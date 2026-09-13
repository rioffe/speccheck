"""§9.7 CLI, exit codes, diagnostics, boundary (§5)."""

from __future__ import annotations

import filecmp
import importlib.metadata
import io
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from speccheck import cli, judge_llm, report

from .conftest import FIXTURE, SIMPLE_PROJECT, junit, run_cli, spec_table

SUMMARY_RE = re.compile(
    r"^speccheck: (CONFORMING|NOT CONFORMING) - \d+/\d+ passing \(\d+\.\d%\), \d+ failing, \d+ skipped, "
    r"\d+ weak, \d+ unverified, \d+ untested, \d+ uncited; \d+ dangling, \d+ stale; "
    r"judge=(none|mock|llm)( \(unavailable\)| \(unknown_rate \d\.\d{4} > max_unknown \d\.\d{4}\))?$"
)
LLM_ENV = {
    "SPECCHECK_JUDGE_URL": "http://localhost:11434/v1/chat/completions",
    "SPECCHECK_JUDGE_MODEL": "m",
    "SPECCHECK_JUDGE_API_KEY": "sk-very-secret",
}
ROOT = Path(__file__).resolve().parent.parent


def _ok_reply(line: int = 3) -> str:
    content = json.dumps(
        {
            "verdict": "ASSERTS",
            "evidence": [{"file": "tests/test_a.py", "line": line}],
            "rationale": "ok",
        }
    )
    return json.dumps({"choices": [{"message": {"content": content}}]})


def test_exit_code_equals_json_and_strict_reasons(project, tmp_path: Path):
    """T-39: exit_code in JSON equals the process exit status for fixtures exercising 0, 1
    (non-strict), 1 (each strict-only reason), and 0 under --strict for a mixed
    ASSERTS/EXECUTES_ONLY ID. (R-14, R-15, I-009, E-26)"""
    run = project(SIMPLE_PROJECT).check()
    assert run.code == 0 == run.json["exit_code"]
    failing = dict(
        SIMPLE_PROJECT,
        **{
            "junit.xml": junit(
                [
                    ("tests.test_calc", "test_add", "failed"),
                    ("tests.test_calc", "test_div", "passed"),
                ]
            )
        },
    )
    run = project(failing).check()
    assert run.code == 1 == run.json["exit_code"]
    strict_only = {
        "UNVERIFIED": {"junit.xml": junit([("tests.test_calc", "test_add", "passed")])},
        "UNTESTED": {
            "tests/test_calc.py": "def test_add():\n    '''T-01: R-01'''\n    assert True\n"
        },
        "UNCITED": {
            "src/calc.py": "def add(a, b):\n    # R-01\n    return a + b\n",
            "tests/test_calc.py": "def test_add():\n    '''T-01: R-01'''\n    assert True\n",
        },
        "SKIPPED": {
            "junit.xml": junit(
                [
                    ("tests.test_calc", "test_add", "passed"),
                    ("tests.test_calc", "test_div", "skipped"),
                ]
            )
        },
        "dangling": {"src/calc.py": SIMPLE_PROJECT["src/calc.py"] + "# K-09 dangling\n"},
        "stale": {
            "SPEC.md": spec_table(
                [("R-01", "adds"), ("C-01", "divides"), ("T-01", "t")], retired={"R-01"}
            )
        },
    }
    for reason, overrides in strict_only.items():
        files = dict(SIMPLE_PROJECT, **overrides)
        lenient = project(files).check()
        strict = project(files).check("--strict")
        assert lenient.code == 0 == lenient.json["exit_code"], reason
        assert strict.code == 1 == strict.json["exit_code"], reason
        if reason == "stale":
            assert strict.json["stale"] and lenient.json["stale"]
    weak_files = dict(
        SIMPLE_PROJECT,
        **{
            "tests/test_calc.py": "def test_add():\n    '''T-01: R-01'''\n    add(1, 2)\n\n\ndef test_div():\n    '''C-01'''\n    assert True\n"
        },
    )
    assert project(weak_files).check("--judge", "mock").code == 0
    strict_weak = project(weak_files).check("--judge", "mock", "--strict")
    assert (
        strict_weak.code == 1 == strict_weak.json["exit_code"]
        and strict_weak.status("R-01") == "WEAKLY_PASSING"
    )
    mixed = dict(SIMPLE_PROJECT)
    mixed["tests/test_calc.py"] = (
        SIMPLE_PROJECT["tests/test_calc.py"]
        + "\n\ndef test_add_weak():\n    '''R-01'''\n    add(1, 1)\n"
    )
    mixed["junit.xml"] = junit(
        [
            ("tests.test_calc", "test_add", "passed"),
            ("tests.test_calc", "test_div", "passed"),
            ("tests.test_calc", "test_add_weak", "passed"),
        ]
    )
    run = project(mixed).check("--judge", "mock", "--strict")
    assert run.code == 0 == run.json["exit_code"] and run.status("R-01") == "PASSING"
    # the exit code is a pure function of the JSON: recompute from the file
    doc = run.json
    assert report.exit_code_for(_renum(doc)) == doc["exit_code"]


def _renum(doc: dict) -> dict:
    """Rebuild a parsed JSON report into the `_Num`-bearing shape exit_code_for/summary_line read."""
    from decimal import Decimal

    from speccheck.report import _Num

    d = json.loads(json.dumps(doc))
    d["max_unknown"] = _Num(Decimal(str(doc["max_unknown"])))
    m = d["metrics"]
    m["conformance"] = _Num(Decimal(str(doc["metrics"]["conformance"])))
    if "unknown_rate" in m and m["unknown_rate"] is not None:
        m["unknown_rate"] = _Num(Decimal(str(doc["metrics"]["unknown_rate"])))
    return d


def test_usage_errors_exit_2_with_message_and_no_key_leak(project, tmp_path: Path):
    """T-40: missing --spec, bad --judge, bad --verbose value, any input or --out path outside
    --root, and missing judge env each exit 2 with the specified message; the API key value never
    appears in the message. (K-01, E-09, E-21, R-23, C-09)"""
    proj = project(SIMPLE_PROJECT)
    run = run_cli(["check", "--src", "src"], proj.path)
    assert run.code == 2 and "--spec" in run.stderr and run.stdout == ""
    run = proj.check("--judge", "gpt")
    assert run.code == 2 and "--judge" in run.stderr and "gpt" in run.stderr
    run = proj.check("--verbose", "TRACE")
    assert run.code == 2 and "--verbose" in run.stderr and "TRACE" in run.stderr
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "SPEC.md").write_text(SIMPLE_PROJECT["SPEC.md"])
    (outside / "junit.xml").write_text(SIMPLE_PROJECT["junit.xml"])
    for argv in (
        ["check", "--spec", str(outside / "SPEC.md")],
        ["check", "--spec", "SPEC.md", "--src", str(outside)],
        ["check", "--spec", "SPEC.md", "--tests", str(outside)],
        ["check", "--spec", "SPEC.md", "--results", str(outside / "junit.xml")],
        ["check", "--spec", "SPEC.md", "--out", str(outside / "reports")],
        ["check", "--spec", "SPEC.md", "--out", ".."],
    ):
        run = run_cli(argv, proj.path)
        assert run.code == 2 and run.stderr.startswith("ERROR path outside --root: "), argv
    for missing in ("SPECCHECK_JUDGE_URL", "SPECCHECK_JUDGE_MODEL", "SPECCHECK_JUDGE_API_KEY"):
        env = {k: v for k, v in LLM_ENV.items() if k != missing}
        run = proj.check("--judge", "llm", env=env)
        assert run.code == 2 and missing in run.stderr, missing
        assert "sk-very-secret" not in run.stderr and "sk-very-secret" not in run.stdout
    run = proj.check("--judge", "llm", env={**LLM_ENV, "SPECCHECK_JUDGE_TIMEOUT": "0"})
    assert (
        run.code == 2
        and "SPECCHECK_JUDGE_TIMEOUT" in run.stderr
        and "sk-very-secret" not in run.stderr
    )
    for flag, value in (
        ("--max-unknown", "1.5"),
        ("--max-unknown", "abc"),
        ("--judge-concurrency", "0"),
        ("--judge-concurrency", "33"),
        ("--judge-budget", "-1"),
        ("--judge-budget", "x"),
    ):
        run = proj.check(flag, value)
        assert run.code == 2 and flag in run.stderr, (flag, value)
    assert run_cli(["check", "--spec", "SPEC.md", "--src", "nope"], proj.path).code == 2
    assert run_cli(["check", "--spec", "missing.md"], proj.path).code == 2
    assert run_cli([], proj.path).code == 2
    assert run_cli(["--bogus"], proj.path).code == 2
    # a symlinked root/path inside --root is resolved and used (Q-007), not rejected
    os.symlink(proj.path / "src", proj.path / "srclink")
    run = run_cli(
        [
            "check",
            "--spec",
            "SPEC.md",
            "--src",
            "srclink",
            "--tests",
            "tests",
            "--results",
            "junit.xml",
        ],
        proj.path,
    )
    assert run.code == 0 and "skipped" not in " ".join(run.json["notes"])


def test_verbosity_levels(project, monkeypatch):
    """T-41: bare --verbose == --verbose INFO; INFO emits stage lines with counts and no
    statement text, file contents, or prompts; DEBUG emits judge>/judge< lines with the key
    redacted; stdout is the single summary line in all cases. (R-17, I-007)"""
    proj = project(SIMPLE_PROJECT)
    quiet = proj.check("--judge", "mock")
    bare = proj.check("--judge", "mock", "--verbose")
    info = proj.check("--judge", "mock", "--verbose", "INFO")
    assert quiet.stderr == ""
    assert bare.stderr == info.stderr and bare.stderr != ""
    for line in info.stderr.splitlines():
        assert line.startswith("INFO "), line
    assert (
        "stage=extract-spec ids=3" in info.stderr
        and "stage=scan-src files=1 citations=2" in info.stderr
    )
    assert "stage=judge edges=" in info.stderr and re.search(r"ms=\d+", info.stderr)
    assert "adds" not in info.stderr and "divides" not in info.stderr  # statement text
    assert (
        "return a + b" not in info.stderr
        and "judge>" not in info.stderr
        and "test-strength judge" not in info.stderr
    )
    debug = proj.check("--judge", "mock", "--verbose", "DEBUG")
    assert "DEBUG judge> " in debug.stderr and "DEBUG judge< " in debug.stderr
    assert '"source": "' in debug.stderr
    for run in (quiet, bare, info, debug):
        assert run.stdout.count("\n") == 1 and SUMMARY_RE.match(run.stdout.rstrip("\n"))
    assert quiet.stdout == debug.stdout
    assert (proj.path / "speccheck.json").read_bytes() == (
        proj.path / "speccheck.json"
    ).read_bytes()
    monkeypatch.setattr(judge_llm, "_httpx_post", lambda *a: (200, _ok_reply()))
    llm_info = proj.check("--judge", "llm", "--verbose", env=LLM_ENV)
    assert "url=http://localhost:11434/v1/chat/completions model=m" in llm_info.stderr
    assert "sk-very-secret" not in llm_info.stderr
    monkeypatch.setattr(
        judge_llm,
        "_httpx_post",
        lambda *a: (200, _ok_reply().replace("ok", "key sk-very-secret leaked")),
    )
    llm_debug = proj.check("--judge", "llm", "--verbose", "DEBUG", env=LLM_ENV)
    assert (
        "judge< " in llm_debug.stderr
        and "sk-very-secret" not in llm_debug.stderr
        and "***" in llm_debug.stderr
    )
    assert "sk-very-secret" not in llm_debug.md and "sk-very-secret" not in llm_debug.stdout
    assert "Bearer" not in llm_debug.stderr or "Bearer ***" in llm_debug.stderr


def test_notes_quiet_by_default_and_once_at_info(project):
    """T-42: with no --verbose, stderr is empty on exit 0/1 even when the run produced Notes;
    with --verbose, each Note appears once at INFO. (§5.3)"""
    files = dict(SIMPLE_PROJECT, **{"tests/test_bad.py": "def broken(:\n"})
    quiet = project(files).check()
    assert (
        quiet.code in (0, 1)
        and quiet.stderr == ""
        and quiet.json["notes"] == ["parse fallback: tests/test_bad.py"]
    )
    loud = project(files).check("--verbose")
    assert loud.stderr.count("INFO note: parse fallback: tests/test_bad.py") == 1
    assert "WARNING" not in loud.stderr


def test_no_sockets_and_self_check(tmp_path: Path, monkeypatch):
    """T-43: with --judge none and --judge mock a socket-creation guard is never triggered;
    speccheck --self-check passes from an installed console script in an empty working
    directory, invokes the inner check in-process with exactly the §5.1 argument list (recorded
    Config), prints `self-check: ok` although its inner check exits 1, leaves no files behind,
    and writes nothing outside its temporary directory. (R-18, I-006, I-001, Q-003)"""
    target = tmp_path / "target"
    shutil.copytree(FIXTURE, target)
    triggered = []
    original_init = socket.socket.__init__

    def guard(self, *a, **k):
        triggered.append(a)
        raise RuntimeError("socket blocked")

    monkeypatch.setattr(socket.socket, "__init__", guard)
    for mode in ("none", "mock"):
        run = run_cli(
            [
                "check",
                "--spec",
                "SPEC.md",
                "--src",
                "src",
                "--tests",
                "tests",
                "--results",
                "junit.xml",
                "--judge",
                mode,
            ],
            target,
        )
        assert run.code == 1
    assert triggered == []
    monkeypatch.setattr(socket.socket, "__init__", original_init)
    # self-check in-process with a recorded Config
    recorded = []
    real_parse = cli.parse_config

    def recording_parse(argv, environ):
        action = real_parse(argv, environ)
        recorded.append((list(argv), action.config))
        return action

    monkeypatch.setattr(cli, "parse_config", recording_parse)
    empty = tmp_path / "empty"
    empty.mkdir()
    before = sorted(p.name for p in tmp_path.iterdir())
    run = run_cli(["--self-check"], empty)
    assert run.code == 0 and run.stdout == "self-check: ok\n" and run.stderr == ""
    ((argv, config),) = [(a, c) for a, c in recorded if c is not None]
    tmp_root = config.root
    assert argv == [
        "check",
        "--spec",
        "SPEC.md",
        "--src",
        "src",
        "--tests",
        "tests",
        "--results",
        "junit.xml",
        "--judge",
        "mock",
        "--strict",
        "--root",
        str(tmp_root),
        "--out",
        str(tmp_root / "out"),
    ]
    assert config.judge == "mock" and config.strict is True and config.out == tmp_root / "out"
    assert not tmp_root.exists()
    assert (
        sorted(p.name for p in empty.iterdir()) == []
        and sorted(p.name for p in tmp_path.iterdir()) == before
    )
    # from the installed console script, in an empty directory, via a subprocess
    exe = Path(sys.executable).parent / "speccheck"
    assert exe.exists(), exe
    proc = subprocess.run(
        [str(exe), "--self-check"], cwd=empty, capture_output=True, text=True, timeout=120
    )
    assert proc.returncode == 0 and proc.stdout == "self-check: ok\n" and proc.stderr == ""
    assert sorted(p.name for p in empty.iterdir()) == []


def test_selfcheck_fixture_is_byte_identical_to_golden_fixture():
    """T-60: speccheck/_selfcheck/ is byte-identical to fixtures/target/ (recursive file-by-file
    comparison, golden/ included). (F-107, §10)"""
    packaged = ROOT / "src" / "speccheck" / "_selfcheck"

    def compare(a: Path, b: Path) -> list[str]:
        cmp = filecmp.dircmp(a, b, ignore=["__pycache__", ".pytest_cache"])
        hidden = lambda n: n.startswith(".")  # noqa: E731 - editor swap files
        problems = [f"only in fixture: {n}" for n in cmp.left_only if not hidden(n)]
        problems += [f"only in package: {n}" for n in cmp.right_only if not hidden(n)]
        for name in cmp.common_files:
            if (a / name).read_bytes() != (b / name).read_bytes():
                problems.append(f"differs: {a / name}")
        for sub in cmp.common_dirs:
            problems.extend(compare(a / sub, b / sub))
        return problems

    assert compare(FIXTURE, packaged) == []
    assert (packaged / "golden" / "speccheck.json").is_file()


def test_summary_line_format_encoding_and_numbers(project, tmp_path: Path, monkeypatch):
    """T-44: the summary line matches the §5.1 regex exactly, is pure ASCII, ends in a single
    newline, is emitted correctly under a C/POSIX locale and a cp1252 stdout, carries all seven
    status counts including skipped, and its numbers equal the JSON metrics. (R-21, R-29, Q-005)"""
    files = dict(
        SIMPLE_PROJECT,
        **{
            "junit.xml": junit(
                [
                    ("tests.test_calc", "test_add", "passed"),
                    ("tests.test_calc", "test_div", "skipped"),
                ]
            )
        },
    )
    proj = project(files)
    run = proj.check("--judge", "mock")
    line = run.stdout
    assert line.endswith("\n") and line.count("\n") == 1 and line.isascii()
    assert SUMMARY_RE.match(line[:-1])
    m = run.json["metrics"]
    s = m["by_status"]
    expected = (
        f"speccheck: CONFORMING - {s['PASSING']}/{m['in_scope']} passing (66.7%), {s['FAILING']} failing, {s['SKIPPED']} skipped, "
        f"{s['WEAKLY_PASSING']} weak, {s['UNVERIFIED']} unverified, {s['UNTESTED']} untested, {s['UNCITED']} uncited; 0 dangling, 0 stale; judge=mock\n"
    )
    assert line == expected and s["SKIPPED"] == 1
    # cp1252 stdout and a C locale: the bytes are still the ASCII line
    raw = io.BytesIO()
    cp1252 = io.TextIOWrapper(raw, encoding="cp1252", write_through=True)
    monkeypatch.setattr(sys, "stdout", cp1252)
    monkeypatch.setenv("LC_ALL", "C")
    monkeypatch.setenv("LANG", "C")
    monkeypatch.chdir(proj.path)
    code = cli.main(
        [
            "check",
            "--spec",
            "SPEC.md",
            "--src",
            "src",
            "--tests",
            "tests",
            "--results",
            "junit.xml",
            "--judge",
            "mock",
        ],
        environ={},
    )
    assert code == 0 and raw.getvalue() == expected.encode("ascii")
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "speccheck",
            "check",
            "--spec",
            "SPEC.md",
            "--src",
            "src",
            "--tests",
            "tests",
            "--results",
            "junit.xml",
            "--judge",
            "mock",
        ],
        cwd=proj.path,
        capture_output=True,
        env={**os.environ, "LC_ALL": "C", "LANG": "C", "PYTHONIOENCODING": "ascii"},
        timeout=60,
    )
    assert proc.returncode == 0 and proc.stdout == expected.encode("ascii") and proc.stderr == b""
    # the summary line is byte-identical in the Markdown §1
    assert expected.strip() in run.md
    assert report.summary_line(_renum(run.json)) + "\n" == expected


def test_strict_llm_judge_gate(project, tmp_path: Path, monkeypatch):
    """T-59: under --strict --judge llm with every call failing, exit 1 with
    strict_judge_failure "unavailable" and the `judge=llm (unavailable)` suffix; with 3 UNKNOWN
    of 10 edges and --max-unknown 0.2 exit 1 with "unknown_rate" and the numeric suffix; with
    --max-unknown 0.3 exit 0; without --strict neither affects exit; with zero eligible edges no
    request is sent, unknown_rate is null, and --strict exits 0. (R-28, K-11, E-32, E-36)"""
    proj = project(SIMPLE_PROJECT)
    monkeypatch.setattr(judge_llm, "_httpx_post", lambda *a: (503, "down"))
    run = proj.check("--judge", "llm", "--strict", env=LLM_ENV)
    assert (
        run.code == 1
        and run.json["strict_judge_failure"] == "unavailable"
        and run.json["judge_available"] is False
    )
    assert run.json["metrics"]["unknown_rate"] == 1.0 and run.stdout.rstrip("\n").endswith(
        "judge=llm (unavailable)"
    )
    assert SUMMARY_RE.match(run.stdout.rstrip("\n"))
    lenient = proj.check("--judge", "llm", env=LLM_ENV)
    assert (
        lenient.code == 0
        and lenient.json["strict_judge_failure"] is None
        and lenient.stdout.rstrip("\n").endswith("judge=llm")
    )
    # ten edges, three UNKNOWN
    tests = "".join(f"def test_{i}():\n    '''R-01'''\n    assert True\n\n" for i in range(10))
    ten = project(
        {
            "SPEC.md": spec_table([("R-01", "a")]),
            "tests/test_a.py": tests,
            "junit.xml": junit([("tests.test_a", f"test_{i}", "passed") for i in range(10)]),
        }
    )
    calls = {"n": 0}

    def three_unknown(url, headers, body, timeout):
        calls["n"] += 1
        req = json.loads(json.loads(body)["messages"][1]["content"])
        unknown = req["start"] in (1, 5, 9)
        content = json.dumps(
            {
                "verdict": "UNKNOWN" if unknown else "ASSERTS",
                "evidence": [] if unknown else [{"file": req["file"], "line": req["start"] + 2}],
                "rationale": "r",
            }
        )
        return 200, json.dumps({"choices": [{"message": {"content": content}}]})

    monkeypatch.setattr(judge_llm, "_httpx_post", three_unknown)
    run = ten.check("--judge", "llm", "--strict", env=LLM_ENV)
    assert (
        run.code == 1
        and run.json["strict_judge_failure"] == "unknown_rate"
        and run.json["metrics"]["unknown_rate"] == 0.3
    )
    assert run.stdout.rstrip("\n").endswith("judge=llm (unknown_rate 0.3000 > max_unknown 0.2000)")
    assert SUMMARY_RE.match(run.stdout.rstrip("\n")) and run.json["judge_available"] is True
    run = ten.check("--judge", "llm", "--strict", "--max-unknown", "0.3", env=LLM_ENV)
    assert (
        run.code == 0
        and run.json["strict_judge_failure"] is None
        and run.json["max_unknown"] == 0.3
    )
    run = ten.check("--judge", "llm", env=LLM_ENV)
    assert run.code == 0 and run.json["strict_judge_failure"] is None
    # zero eligible edges
    zero = project(
        {
            "SPEC.md": spec_table([("R-01", "a")]),
            "src/a.py": "# R-01\n",
            "tests/test_a.py": "def test_a():\n    '''R-01'''\n    assert True\n",
            "junit.xml": junit([("tests.test_a", "test_a", "failed")]),
        }
    )
    calls["n"] = 0
    run = zero.check("--judge", "llm", "--strict", env=LLM_ENV)
    assert (
        calls["n"] == 0
        and run.json["metrics"]["unknown_rate"] is None
        and run.json["judge_available"] is True
    )
    assert run.json["strict_judge_failure"] is None and run.code == 1  # FAILING, not the judge gate
    zero_pass = project(
        {
            "SPEC.md": spec_table([("R-01", "a")]),
            "src/a.py": "# R-01\n",
            "tests/test_a.py": "def test_a():\n    '''R-01'''\n    assert True\n",
            "junit.xml": junit([("tests.test_a", "test_a", "skipped")]),
        }
    )
    run = zero_pass.check("--judge", "llm", env=LLM_ENV)
    assert calls["n"] == 0 and run.code == 0 and run.json["metrics"]["unknown_rate"] is None


def test_judge_budget(project, monkeypatch):
    """T-61: with --judge-budget 1, --judge-concurrency 2, and a provider stub that sleeps 2 s
    per call over six edges, exactly the two requests issued before the deadline complete and
    are judged; the remaining four are UNKNOWN with rationale `judge: budget` and coerced: true;
    the Note reports 4; unknown_rate includes them; with --judge-budget 0 all six are judged.
    (K-12, E-35, Q-010)"""
    tests = "".join(f"def test_{i}():\n    '''R-01'''\n    assert True\n\n" for i in range(6))
    six = project(
        {
            "SPEC.md": spec_table([("R-01", "a")]),
            "tests/test_a.py": tests,
            "junit.xml": junit([("tests.test_a", f"test_{i}", "passed") for i in range(6)]),
        }
    )
    issued = []
    lock = threading.Lock()

    def slow(url, headers, body, timeout):
        with lock:
            issued.append(time.monotonic())
        time.sleep(2.0)
        req = json.loads(json.loads(body)["messages"][1]["content"])
        content = json.dumps(
            {
                "verdict": "ASSERTS",
                "evidence": [{"file": req["file"], "line": req["start"] + 2}],
                "rationale": "r",
            }
        )
        return 200, json.dumps({"choices": [{"message": {"content": content}}]})

    monkeypatch.setattr(judge_llm, "_httpx_post", slow)
    t0 = time.monotonic()
    run = six.check(
        "--judge", "llm", "--judge-budget", "1", "--judge-concurrency", "2", env=LLM_ENV
    )
    assert time.monotonic() - t0 < 5.0
    assert len(issued) == 2
    verdicts = [t["verdict"] for t in run.ids()["R-01"]["tests"]]
    judged = [v for v in verdicts if v["verdict"] == "ASSERTS"]
    budget = [v for v in verdicts if v["rationale"] == "judge: budget"]
    assert len(judged) == 2 and len(budget) == 4
    assert all(
        v["verdict"] == "UNKNOWN" and v["coerced"] is True and v["evidence"] == [] for v in budget
    )
    assert run.json["notes"] == ["judge budget exhausted: 4 edge(s) unjudged"]
    assert run.json["metrics"]["unknown_rate"] == 0.6667 and run.json["judge_available"] is True
    assert run.status("R-01") == "PASSING"
    issued.clear()
    run = six.check(
        "--judge", "llm", "--judge-budget", "0", "--judge-concurrency", "6", env=LLM_ENV
    )
    assert (
        len(issued) == 6 and run.json["notes"] == [] and run.json["metrics"]["unknown_rate"] == 0.0
    )


def test_out_failures_and_temp_and_rename(project, monkeypatch):
    """T-45: an unwritable --out exits 3 with nothing written; a failure injected after the JSON
    rename and before the Markdown rename exits 3 with no .tmp left, no speccheck.json, and the
    previous run's SPEC_CONFORMANCE_REPORT.md intact; leftover temporaries are deleted first; on
    success no .tmp remains and the two temporaries carried the same 8-hex-digit nonce.
    (E-18, I-001, §3.1)"""
    proj = project(SIMPLE_PROJECT)
    (proj.path / "blocked").write_text("a file, not a directory")
    run = proj.check("--out", "blocked")
    assert run.code == 3 and run.stderr.startswith("ERROR out: ") and run.stdout == ""
    assert not (proj.path / "speccheck.json").exists() and not list(proj.path.glob("**/.*.tmp"))
    if os.name != "nt" and os.geteuid() != 0:
        ro = proj.path / "ro"
        ro.mkdir()
        ro.chmod(0o500)
        try:
            run = proj.check("--out", "ro")
            assert run.code == 3 and run.stderr.startswith("ERROR out: ")
            assert sorted(p.name for p in ro.iterdir()) == []
        finally:
            ro.chmod(0o700)
    # a first successful run, then an injected failure between the two renames
    first = proj.check("--out", "reports")
    assert first.code == 0
    old_md = (proj.path / "reports" / "SPEC_CONFORMANCE_REPORT.md").read_bytes()
    (proj.path / "reports" / ".speccheck.json.00000000.tmp").write_text("leftover")
    (proj.path / "reports" / ".SPEC_CONFORMANCE_REPORT.md.00000000.tmp").write_text("leftover")
    renames = []
    real_replace = report._replace

    def failing_replace(src, dst):
        renames.append((src.name, dst.name))
        if dst.name == "SPEC_CONFORMANCE_REPORT.md":
            raise OSError(28, "No space left on device")
        real_replace(src, dst)

    monkeypatch.setattr(report, "_replace", failing_replace)
    run = proj.check("--out", "reports")
    assert run.code == 3 and run.stderr.startswith("ERROR out: ") and run.stdout == ""
    names = sorted(p.name for p in (proj.path / "reports").iterdir())
    assert names == ["SPEC_CONFORMANCE_REPORT.md"], names
    assert (proj.path / "reports" / "SPEC_CONFORMANCE_REPORT.md").read_bytes() == old_md
    assert renames[0][1] == "speccheck.json" and renames[1][1] == "SPEC_CONFORMANCE_REPORT.md"
    monkeypatch.setattr(report, "_replace", real_replace)
    renames.clear()

    def recording_replace(src, dst):
        renames.append(src.name)
        real_replace(src, dst)

    monkeypatch.setattr(report, "_replace", recording_replace)
    run = proj.check("--out", "reports")
    assert run.code == 0
    assert sorted(p.name for p in (proj.path / "reports").iterdir()) == [
        "SPEC_CONFORMANCE_REPORT.md",
        "speccheck.json",
    ]
    nonces = [
        re.fullmatch(
            r"\.(?:speccheck\.json|SPEC_CONFORMANCE_REPORT\.md)\.([0-9a-f]{8})\.tmp", n
        ).group(1)
        for n in renames
    ]
    assert len(nonces) == 2 and nonces[0] == nonces[1]


def test_version_flag():
    """T-50: speccheck --version prints `speccheck <version>` where <version> is PEP 440 and
    equals importlib.metadata.version("speccheck"). (K-10)"""
    proc = subprocess.run(
        [sys.executable, "-m", "speccheck", "--version"], capture_output=True, text=True, timeout=60
    )
    assert proc.returncode == 0
    prefix, version = proc.stdout.strip().split(" ")
    assert prefix == "speccheck"
    assert version == importlib.metadata.version("speccheck")
    assert re.fullmatch(
        r"([1-9][0-9]*!)?(0|[1-9][0-9]*)(\.(0|[1-9][0-9]*))*((a|b|rc)(0|[1-9][0-9]*))?(\.post(0|[1-9][0-9]*))?(\.dev(0|[1-9][0-9]*))?",
        version,
    )
    buf = io.StringIO()
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(sys, "stdout", buf)
        assert cli.main(["--version"], environ={}) == 0
    assert buf.getvalue() == f"speccheck {version}\n"


# ------------------------------------------------------------------------------------------
# progress indicator (R-30, C-11, K-13, E-39, E-40) and interrupts (E-41)
# ------------------------------------------------------------------------------------------

PROGRESS_LINE_RE = re.compile(
    r"^judge: \[[#-]{20}\] \d+/\d+ edges  \d+:\d{2} elapsed  ~(\d+:\d{2}|\?:\?\?) left$"
)


def _edges_project(project, n: int):
    tests = "".join(f"def test_{i}():\n    '''R-01'''\n    assert True\n\n" for i in range(n))
    return project(
        {
            "SPEC.md": spec_table([("R-01", "a")]),
            "tests/test_a.py": tests,
            "junit.xml": junit([("tests.test_a", f"test_{i}", "passed") for i in range(n)]),
        }
    )


def _asserting_stub(delay: float):
    def post(url, headers, body, timeout):
        if delay:
            time.sleep(delay)
        req = json.loads(json.loads(body)["messages"][1]["content"])
        content = json.dumps(
            {
                "verdict": "ASSERTS",
                "evidence": [{"file": req["file"], "line": req["start"] + 2}],
                "rationale": "r",
            }
        )
        return 200, json.dumps({"choices": [{"message": {"content": content}}]})

    return post


def _segments(stderr: str) -> tuple[list[str], str]:
    """Split a stderr capture on \\r into (draws, erase): every draw is a padded C-11 line;
    the erase is the final `\\r` + W spaces + `\\r` (so the capture ends with an empty segment)."""
    assert "\x1b" not in stderr
    parts = stderr.split("\r")
    assert parts[0] == "" and parts[-1] == "", parts
    erase = parts[-2]
    draws = parts[1:-2]
    return draws, erase


def test_progress_indicator_format_cadence_and_isolation(project, monkeypatch):
    """T-62: with --judge llm, --progress always, a six-edge stub sleeping 0.3 s per call and
    --judge-concurrency 2, the stderr capture splits on \\r into C-11 draws only: the first
    reads 0/6, 0:00 elapsed, ?:??; <done> is non-decreasing; the last draw is 6/6 with a full
    bar; the capture ends with the erase; no \\x1b byte; every draw padded to the widest so far;
    # cells == floor(20 d / 6); a 2.5 s single edge shows >= 2 draws at 0/1 with distinct
    elapsed (the 1 s tick); 32 instant edges at concurrency 32 draw <= 10 times per second and
    end at 32/32 (coalescing); with --verbose INFO no INFO line sits between the first draw and
    the erase; stdout is the summary line and the reports equal a --progress never run.
    (R-30, C-11, K-13)"""
    six = _edges_project(project, 6)
    monkeypatch.setattr(judge_llm, "_httpx_post", _asserting_stub(0.3))
    run = six.check(
        "--judge", "llm", "--judge-concurrency", "2", "--progress", "always", env=LLM_ENV
    )
    assert (
        run.code == 0 and SUMMARY_RE.match(run.stdout.rstrip("\n")) and run.stdout.count("\n") == 1
    )
    draws, erase = _segments(run.stderr)
    assert len(draws) >= 2
    width = 0
    dones = []
    for padded in draws:
        line = padded.rstrip(" ")
        assert PROGRESS_LINE_RE.match(line), line
        width = max(width, len(line))
        assert len(padded) == width, (padded, width)
        m = re.match(r"^judge: \[([#-]{20})\] (\d+)/6 edges", line)
        bar, done = m.group(1), int(m.group(2))
        assert bar == "#" * (20 * done // 6) + "-" * (20 - 20 * done // 6)
        dones.append(done)
    assert dones == sorted(dones) and dones[-1] == 6
    assert draws[0].startswith("judge: [--------------------] 0/6 edges  0:00 elapsed  ~?:?? left")
    assert erase == " " * width
    reference = six.check(
        "--judge", "llm", "--judge-concurrency", "2", "--progress", "never", env=LLM_ENV
    )
    assert reference.stderr == "" and reference.json == run.json and reference.md == run.md

    one = _edges_project(project, 1)
    monkeypatch.setattr(judge_llm, "_httpx_post", _asserting_stub(2.5))
    run = one.check("--judge", "llm", "--progress", "always", env=LLM_ENV)
    draws, _ = _segments(run.stderr)
    idle = {re.search(r"(\d+:\d{2}) elapsed", d).group(1) for d in draws if " 0/1 edges" in d}
    assert len(idle) >= 2, draws

    many = _edges_project(project, 32)
    monkeypatch.setattr(judge_llm, "_httpx_post", _asserting_stub(0.0))
    t0 = time.monotonic()
    run = many.check(
        "--judge", "llm", "--judge-concurrency", "32", "--progress", "always", env=LLM_ENV
    )
    elapsed = time.monotonic() - t0
    draws, _ = _segments(run.stderr)
    assert draws[-1].startswith("judge: [####################] 32/32 edges")
    assert len(draws) <= 10 * max(1.0, elapsed) + 1, (len(draws), elapsed)

    monkeypatch.setattr(judge_llm, "_httpx_post", _asserting_stub(0.3))
    run = six.check(
        "--judge",
        "llm",
        "--judge-concurrency",
        "2",
        "--progress",
        "always",
        "--verbose",
        "INFO",
        env=LLM_ENV,
    )
    assert run.code == 0
    first_draw = run.stderr.index("\rjudge: [")
    erase_end = run.stderr.rindex("\r") + 1
    assert "INFO" not in run.stderr[first_draw:erase_end]
    after = run.stderr[erase_end:]
    assert "INFO judge=llm url=" in after and "INFO stage=judge " in after
    assert "INFO stage=judge " not in run.stderr[:first_draw]


def test_progress_gating_and_interrupt_erase(project, monkeypatch):
    """T-63: no progress bytes when stderr is not a TTY under --progress auto, under --progress
    never, under --verbose DEBUG with --progress always, or with --judge mock/none and
    --progress always; drawn under auto when stderr.isatty() is True; a bad --progress value
    exits 2; a stub raising KeyboardInterrupt mid-stage leaves the erase as the last stderr
    bytes before the `interrupted` message (E-41). (R-30, E-39, E-40, K-01)"""
    six = _edges_project(project, 6)
    monkeypatch.setattr(judge_llm, "_httpx_post", _asserting_stub(0.0))
    for flags, env in [
        (("--judge", "llm"), LLM_ENV),
        (("--judge", "llm", "--progress", "auto"), LLM_ENV),
        (("--judge", "llm", "--progress", "never"), LLM_ENV),
        (("--judge", "mock", "--progress", "always"), None),
        (("--judge", "none", "--progress", "always"), None),
    ]:
        run = six.check(*flags, env=env)
        assert run.code == 0 and run.stderr == "", (flags, run.stderr)
    run = six.check("--judge", "llm", "--progress", "always", "--verbose", "DEBUG", env=LLM_ENV)
    assert run.code == 0 and "\r" not in run.stderr and "judge>" in run.stderr
    run = six.check("--judge", "llm", "--progress", "sometimes", env=LLM_ENV)
    assert run.code == 2 and "--progress" in run.stderr and run.stdout == ""

    run = six.check("--judge", "llm", env=LLM_ENV, tty=True)
    assert run.code == 0 and run.stderr.startswith("\rjudge: [")
    run = six.check("--judge", "llm", "--verbose", "DEBUG", env=LLM_ENV, tty=True)
    assert run.code == 0 and "\r" not in run.stderr

    calls = []

    def interrupting(url, headers, body, timeout):
        calls.append(1)
        if len(calls) == 3:
            raise KeyboardInterrupt
        time.sleep(0.05)
        return _asserting_stub(0.0)(url, headers, body, timeout)

    monkeypatch.setattr(judge_llm, "_httpx_post", interrupting)
    run = six.check(
        "--judge", "llm", "--judge-concurrency", "1", "--progress", "always", env=LLM_ENV
    )
    assert run.code == 3 and run.stdout == ""
    body, _, tail = run.stderr.rpartition("\r")
    assert tail == "ERROR interrupted\n"
    draws, erase = _segments(body + "\r")
    assert erase == " " * len(erase) and len(erase) == len(draws[0]) and draws


def test_interrupt_exits_3_and_cleans_up(project, monkeypatch):
    """T-64: a KeyboardInterrupt from a provider stub mid-judge, and one injected between the
    JSON rename and the Markdown rename, each exit 3 with stderr exactly `ERROR interrupted`,
    write nothing to stdout, leave no .tmp and no speccheck.json from this run under --out,
    and leave a previous run's reports intact. (E-41, K-01, I-001, §3.1)"""
    six = _edges_project(project, 6)
    first = six.check("--judge", "none", "--out", "reports")
    assert first.code == 0
    old_md = (six.path / "reports" / "SPEC_CONFORMANCE_REPORT.md").read_bytes()
    old_json = (six.path / "reports" / "speccheck.json").read_bytes()

    def interrupting(url, headers, body, timeout):
        raise KeyboardInterrupt

    monkeypatch.setattr(judge_llm, "_httpx_post", interrupting)
    run = six.check("--judge", "llm", "--out", "reports", env=LLM_ENV)
    assert run.code == 3 and run.stdout == "" and run.stderr == "ERROR interrupted\n"
    assert sorted(p.name for p in (six.path / "reports").iterdir()) == [
        "SPEC_CONFORMANCE_REPORT.md",
        "speccheck.json",
    ]
    assert (six.path / "reports" / "SPEC_CONFORMANCE_REPORT.md").read_bytes() == old_md
    assert (six.path / "reports" / "speccheck.json").read_bytes() == old_json

    real_replace = report._replace

    def interrupting_replace(src, dst):
        if dst.name == "SPEC_CONFORMANCE_REPORT.md":
            raise KeyboardInterrupt
        real_replace(src, dst)

    monkeypatch.setattr(report, "_replace", interrupting_replace)
    run = six.check("--judge", "none", "--out", "reports")
    assert run.code == 3 and run.stdout == "" and run.stderr == "ERROR interrupted\n"
    names = sorted(p.name for p in (six.path / "reports").iterdir())
    assert names == ["SPEC_CONFORMANCE_REPORT.md"], names
    assert (six.path / "reports" / "SPEC_CONFORMANCE_REPORT.md").read_bytes() == old_md
    run = six.check("--judge", "none", "--out", "reports", "--verbose", "DEBUG")
    assert run.code == 3 and "\nERROR interrupted\n" in run.stderr and "Traceback" in run.stderr


def test_interrupt_abandons_in_flight_requests(project, monkeypatch):
    """T-64 (E-41, in-flight requests): a SIGINT delivered to the main thread while several
    slow LLM requests are in flight ends the run promptly — queued edges are never started,
    in-flight ones are abandoned rather than awaited — with exit 3, `ERROR interrupted`, the
    progress line erased, and no report written. (E-41, E-40, K-05)"""
    import _thread

    six = _edges_project(project, 6)
    started = []
    lock = threading.Lock()

    def slow(url, headers, body, timeout):
        with lock:
            started.append(1)
        time.sleep(5.0)
        return _asserting_stub(0.0)(url, headers, body, timeout)

    monkeypatch.setattr(judge_llm, "_httpx_post", slow)
    threading.Timer(0.5, _thread.interrupt_main).start()
    t0 = time.monotonic()
    run = six.check(
        "--judge", "llm", "--judge-concurrency", "2", "--progress", "always", env=LLM_ENV
    )
    elapsed = time.monotonic() - t0
    assert run.code == 3 and run.stdout == "", run.stderr
    assert elapsed < 2.0, elapsed  # not the 5 s the in-flight stubs would take
    assert len(started) <= 3
    assert run.stderr.endswith("\rERROR interrupted\n") or run.stderr.endswith(
        "\r" + " " * (len(run.stderr.split("\r")[-2])) + "\rERROR interrupted\n"
    )
    assert not (six.path / "speccheck.json").exists()
