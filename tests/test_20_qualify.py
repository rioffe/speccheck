"""§9.19 The validation pack: intended use, `qualify`, the tool risk file, known anomalies
(R-110..R-115, C-29..C-31, I-022, I-023, E-85..E-88; v1.26).

Tool-hazard (`TH-01`), case (`OQ-01`) and anomaly (`KA-01`) labels are not spec-id tokens, so
naming them here cites nothing.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import socket
import subprocess
import tempfile
from pathlib import Path

import pytest

from speccheck import __version__, cli
from speccheck import qualify as q
from speccheck.extract import parse_spec

from .conftest import FIXTURE, run_cli

ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / "src" / "speccheck"
QDATA = PKG / "_qualify"
SPEC_TEXT = (ROOT / "SPEC.md").read_text(encoding="utf-8")


def _hazard_table() -> dict[str, tuple[str, list[str], list[str]]]:
    """C-30's hazard table: id -> (title, controlled-by ids, OQ cases)."""
    start = SPEC_TEXT.index("| Hazard | Title (as in `tool_risk.json`)")
    out: dict[str, tuple[str, list[str], list[str]]] = {}
    for line in SPEC_TEXT[start:].split("\n")[2:]:
        if not line.startswith("| TH-"):
            break
        cells = [c.strip() for c in line.strip("|").split("|")]
        out[cells[0]] = (cells[1], cells[2].split(", "), cells[3].split(", "))
    return out


def _intended_use_block() -> str:
    i = SPEC_TEXT.index("**Intended use (v1.26; R-110, D-67).**")
    start = SPEC_TEXT.index("```text\n", i) + len("```text\n")
    return SPEC_TEXT[start : SPEC_TEXT.index("\n```\n", start) + 1]


def _tracked(directory: Path) -> dict[str, bytes]:
    return {
        p.relative_to(directory).as_posix(): p.read_bytes()
        for p in sorted(directory.rglob("*"))
        if p.is_file()
        and "__pycache__" not in p.parts
        # dot-paths are never packaged (pyproject.toml `exclude`): an editor's swap file or a
        # SwiftPM .build/ index next to a packaged Package.swift is not part of the fixture
        and not any(part.startswith(".") for part in p.relative_to(directory).parts)
    }


def test_intended_use_block_is_packaged_byte_for_byte():
    """T-130 (the R-110 half that needs no wheel): SPEC.md §0's *Intended use* block — the lines
    between its fence lines, each ending in a newline — equals `_qualify/intended_use.md` byte for
    byte, and it states the validated function and the advisory surfaces. (R-110)"""
    block = _intended_use_block()
    assert (QDATA / "intended_use.md").read_bytes() == block.encode("utf-8")
    assert (
        "Validated function: `speccheck check`, `speccheck verify` and `speccheck impact`" in block
    )
    assert "`--judge none` or `--judge mock`" in block
    assert (
        "Outside validated use: `--judge llm`, `--jev-pre-triage` and `speccheck explain`" in block
    )


def test_tool_risk_file_markers_cases_and_anomalies_agree():
    """T-135: `tool_risk.json` is a C-28 file whose ids and titles equal C-30's hazard table;
    every *Controlled by* id carries exactly the hazards the table gives it in its CONTROLS marker,
    and no other declaration carries a tool hazard; every hazard is challenged by some case and
    the table's OQ column equals the catalog's; every anomaly has C-31's shape and names only
    tool hazards; every case's fixture and goldens exist. (R-114, R-115, C-30, C-31)"""
    table = _hazard_table()
    assert list(table) == [f"TH-{n:02d}" for n in range(1, 11)]
    risk = json.loads((QDATA / "tool_risk.json").read_text(encoding="utf-8"))
    assert risk == {"hazards": [{"id": h, "title": t} for h, (t, _c, _q) in table.items()]}

    expected: dict[str, list[str]] = {}
    for hazard, (_title, controls, _cases) in table.items():
        for ident in controls:
            expected.setdefault(ident, []).append(hazard)
    index = parse_spec(SPEC_TEXT, "SPEC.md")
    marked = {s.id: list(s.controls) for s in index.ids if s.controls}
    assert marked == {k: sorted(v) for k, v in expected.items()}
    assert len(marked) == 31

    cases = json.loads((QDATA / "cases.json").read_text(encoding="utf-8"))["cases"]
    assert [c["id"] for c in cases] == [f"OQ-{n:02d}" for n in range(1, 6)]
    challenged = {h: [c["id"] for c in cases if h in c["hazards"]] for h in table}
    assert challenged == {h: sorted(q) for h, (_t, _c, q) in table.items()}
    for case in cases:
        fixture = PKG / case["fixture"]
        assert fixture.is_dir(), case["fixture"]
        for step in case["steps"]:
            assert set(step) == {"argv", "edit", "exit", "stdout", "goldens"}
            assert step["stdout"].endswith("\n")
            for golden in step["goldens"].values():
                assert (fixture / golden).is_file(), golden
            if step["edit"] is not None:
                assert (fixture / step["edit"]["append"]).is_file()

    anomalies = json.loads((QDATA / "known_anomalies.json").read_text(encoding="utf-8"))
    entries = anomalies["anomalies"]
    assert [a["id"] for a in entries] == [f"KA-{n:02d}" for n in range(1, 6)]
    version = re.compile(r"\d+\.\d+\.\d+")
    for a in entries:
        assert list(a) == ["id", "summary", "hazards", "workaround", "found_in", "fixed_in"]
        assert a["hazards"] and set(a["hazards"]) <= set(table)
        assert a["summary"] and a["workaround"]
        assert version.fullmatch(a["found_in"])
        assert a["fixed_in"] is None or version.fullmatch(a["fixed_in"])


def test_packaged_fixture_copies_do_not_drift():
    """T-135 (drift): `_qualify/swift/` is byte-identical to `fixtures/target-swift/`, and
    `_qualify/hazards/` to the §9.8 fixture except its SPEC.md, `risk.json` and `golden/`; its
    SPEC.md differs from the fixture's only by three CONTROLS markers. (C-30)"""
    assert _tracked(QDATA / "swift") == _tracked(ROOT / "fixtures" / "target-swift")
    target = _tracked(ROOT / "fixtures" / "target")
    hazards = _tracked(QDATA / "hazards")
    own = {"SPEC.md", "risk.json"}
    assert {k: v for k, v in hazards.items() if k not in own and not k.startswith("golden/")} == {
        k: v for k, v in target.items() if k != "SPEC.md" and not k.startswith("golden/")
    }
    stripped = re.sub(r" \*\(controls: [^)]*\)\*", "", hazards["SPEC.md"].decode("utf-8"))
    assert stripped == target["SPEC.md"].decode("utf-8")
    assert hazards["SPEC.md"].decode("utf-8").count("*(controls: ") == 3


def test_self_application_lists_every_tool_hazard_with_its_controls(tmp_path: Path):
    """T-135 (self-application half): `check --risk-file src/speccheck/_qualify/tool_risk.json`
    over this repository lists exactly the ten tool hazards, each with C-30's *Controlled by* ids
    as its `controls` (in C-07 id order). Whether every control is PASSING needs this suite's own
    results and is recorded with T-48 (F-901). (R-114, C-30)"""
    repo = tmp_path / "repo"
    repo.mkdir()
    shutil.copy(ROOT / "SPEC.md", repo / "SPEC.md")
    shutil.copytree(PKG, repo / "src" / "speccheck", ignore=shutil.ignore_patterns("__pycache__"))
    run = run_cli(
        [
            "check",
            "--spec",
            "SPEC.md",
            "--src",
            "src",
            "--judge",
            "mock",
            "--risk-file",
            "src/speccheck/_qualify/tool_risk.json",
            "--out",
            "out",
        ],
        repo,
    )
    assert run.code in (0, 1), run.stderr
    doc = run.json_at(repo / "out")
    order = [r["id"] for r in doc["ids"]]
    table = _hazard_table()
    assert [h["id"] for h in doc["hazards"]] == list(table)
    for h in doc["hazards"]:
        title, controls, _cases = table[h["id"]]
        assert h["title"] == title
        assert h["controls"] == sorted(controls, key=order.index)
    assert re.search(r"; hazards: \d+/10 verified\n$", run.stdout), run.stdout


# ------------------------------------------------------------------- qualify (W2)

C29_KEYS = [
    "qualification_version",
    "tool",
    "intended_use",
    "environment",
    "dependencies",
    "iq",
    "oq",
    "hazards",
    "known_anomalies",
    "verdict",
]
MD_HEADINGS = [
    "## 1. Verdict",
    "## 2. Intended use",
    "## 3. Installation qualification",
    "## 4. Operational qualification",
    "## 5. Tool hazards",
    "## 6. Known anomalies",
    "## 7. Signatures",
]
SIGNATURES = (
    "| Role | Name | Signature | Date |\n| --- | --- | --- | --- |\n"
    "| Executed by |  |  |  |\n| Reviewed by |  |  |  |\n"
)
QUALIFIED_RE = re.compile(
    r"qualify: QUALIFIED - IQ (\d+) files, tree ([0-9a-f]{12}); OQ 5/5 cases\n"
)


def _record(out: Path) -> tuple[dict, str]:
    doc = json.loads((out / "qualification.json").read_text(encoding="utf-8"))
    return doc, (out / "QUALIFICATION_REPORT.md").read_text(encoding="utf-8")


def _copy_package(tmp_path: Path) -> Path:
    """The packaged data a run reads (`_qualify/`, `_selfcheck/`), copied so a test can break it."""
    root = tmp_path / "pkg"
    for name in ("_qualify", "_selfcheck"):
        shutil.copytree(PKG / name, root / name, ignore=shutil.ignore_patterns("__pycache__"))
    return root


def _leftover_copies() -> set[str]:
    return {p.name for p in Path(tempfile.gettempdir()).glob("speccheck-qualify-*")}


def _run_in_process(root: Path, environ: dict | None = None) -> q.Record:
    env = environ or {}
    return q.qualify(
        version=__version__,
        run_step=lambda argv, out: cli.run_argv(argv, env, out),
        epoch=None,
        root=root,
        use_installed=False,
    )


@pytest.fixture(scope="module")
def wheel_venv(tmp_path_factory) -> Path:
    """A wheel built from this tree, installed into a fresh virtual environment (T-130)."""
    uv = shutil.which("uv")
    assert uv, "uv is required to build and install the wheel"
    base = tmp_path_factory.mktemp("wheel")
    env = {k: v for k, v in os.environ.items() if not k.startswith("VIRTUAL_ENV")}
    subprocess.run(
        [uv, "build", "--wheel", "-q", "-o", str(base / "dist")], cwd=ROOT, check=True, env=env
    )
    subprocess.run([uv, "venv", "-q", str(base / "venv"), "--python", "3.12"], check=True, env=env)
    (wheel,) = (base / "dist").glob("*.whl")
    subprocess.run(
        [uv, "pip", "install", "-q", "--python", str(base / "venv" / "bin" / "python"), str(wheel)],
        check=True,
        env=env,
    )
    return base / "venv"


def _qualify_installed(venv: Path, cwd: Path) -> subprocess.CompletedProcess:
    cwd.mkdir(parents=True, exist_ok=True)
    return subprocess.run(
        [str(venv / "bin" / "speccheck"), "qualify", "--out", "q"],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=300,
        env={"PATH": os.environ.get("PATH", "")},
    )


def test_qualify_from_an_installed_wheel(wheel_venv: Path, tmp_path: Path):
    """T-130: from a wheel built from this tree and installed into a fresh virtual environment,
    `speccheck qualify --out q` run in an empty directory exits 0 and prints the QUALIFIED line;
    `qualification.json` has C-29's keys in order; `iq.package_tree_sha256` equals the R-112 (a)
    computation over this tree's `src/speccheck/` minus caches, and `files` its path count;
    every OQ case passes; `intended_use` equals SPEC.md §0's block; the Markdown has C-29's seven
    headings in order, the intended-use text and the empty signature table. (R-110, R-111, R-112,
    C-29)"""
    empty = tmp_path / "empty"
    proc = _qualify_installed(wheel_venv, empty)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    match = QUALIFIED_RE.fullmatch(proc.stdout)
    assert match, proc.stdout
    assert proc.stderr == ""
    doc, md = _record(empty / "q")
    assert list(doc) == C29_KEYS
    tree, files = q.tree_of_directory(PKG)
    assert doc["iq"] == {
        "package_tree_sha256": tree,
        "files": files,
        "record_mismatches": [],
        "record_missing": [],
        "data_faults": [],
    }
    assert (match.group(1), match.group(2)) == (str(files), tree[:12])
    assert doc["tool"] == {"name": "speccheck", "version": __version__}
    assert [(c["id"], c["result"], c["failure"]) for c in doc["oq"]] == [
        (f"OQ-{n:02d}", "PASS", None) for n in range(1, 6)
    ]
    assert doc["verdict"] == "QUALIFIED"
    assert doc["intended_use"] == _intended_use_block()
    assert list(doc["environment"]) == ["implementation", "python", "system", "machine", "source"]
    assert doc["environment"]["source"].endswith(".whl")
    assert [h["id"] for h in doc["hazards"]] == list(_hazard_table())
    assert [a["id"] for a in doc["known_anomalies"]] == [f"KA-{n:02d}" for n in range(1, 6)]
    positions = [md.index(h + "\n") for h in MD_HEADINGS]
    assert positions == sorted(positions)
    assert _intended_use_block() in md
    assert md.endswith("## 7. Signatures\n\n" + SIGNATURES)
    assert sorted(p.name for p in empty.iterdir()) == ["q"]


def test_qualify_names_a_changed_or_missing_installed_file(wheel_venv: Path, tmp_path: Path):
    """T-131: one byte appended to an installed `speccheck/*.py` file makes `qualify` exit 1
    with `RECORD mismatch speccheck/<file>` as its first failure, `record_mismatches` lists exactly
    that path, and the tree hash changes; a deleted installed file is listed in `record_missing`.
    (R-112, C-29)"""
    (site,) = (wheel_venv / "lib").glob("python3*/site-packages")
    target = site / "speccheck" / "graph.py"
    original = target.read_bytes()
    tree, _files = q.tree_of_directory(PKG)
    try:
        target.write_bytes(original + b"\n")
        proc = _qualify_installed(wheel_venv, tmp_path / "a")
        assert proc.returncode == 1
        assert proc.stdout == "qualify: NOT QUALIFIED - RECORD mismatch speccheck/graph.py\n"
        doc, _md = _record(tmp_path / "a" / "q")
        assert doc["iq"]["record_mismatches"] == ["speccheck/graph.py"]
        assert doc["iq"]["package_tree_sha256"] != tree
        assert doc["verdict"] == "NOT QUALIFIED"
    finally:
        target.write_bytes(original)
    # a file the validated function never imports (read only by --judge llm), so the tool still runs
    prompt = site / "speccheck" / "judge_prompt.md"
    kept = prompt.read_bytes()
    try:
        prompt.unlink()
        proc = _qualify_installed(wheel_venv, tmp_path / "b")
        doc, _md = _record(tmp_path / "b" / "q")
        assert proc.stdout == "qualify: NOT QUALIFIED - RECORD missing speccheck/judge_prompt.md\n"
        assert proc.returncode == 1 and doc["iq"]["record_missing"] == ["speccheck/judge_prompt.md"]
    finally:
        prompt.write_bytes(kept)


def test_a_failing_case_never_stops_the_catalog(tmp_path: Path, monkeypatch):
    """T-132: with a packaged golden of OQ-02 altered, OQ-02 fails naming that golden while the
    other cases pass; a step made to raise and one made to open a socket each get E-88's failure
    and later cases still run; no temporary copy survives. (R-113, E-88, I-022)"""
    root = _copy_package(tmp_path)
    golden = root / "_qualify" / "swift" / "golden" / "speccheck.json"
    golden.write_bytes(golden.read_bytes() + b" ")
    before = _leftover_copies()
    record = _run_in_process(root)
    doc = json.loads(record.json_text)
    assert [(c["id"], c["result"], c["failure"]) for c in doc["oq"]] == [
        ("OQ-01", "PASS", None),
        ("OQ-02", "FAIL", "step 1: out/speccheck.json differs from golden/speccheck.json"),
        ("OQ-03", "PASS", None),
        ("OQ-04", "PASS", None),
        ("OQ-05", "PASS", None),
    ]
    assert record.exit_code == 1
    golden.write_bytes((PKG / "_qualify" / "swift" / "golden" / "speccheck.json").read_bytes())

    def opens_a_socket(*_a, **_k):
        socket.socket()
        return 0

    def raises(*_a, **_k):
        raise ValueError("boom")

    monkeypatch.setattr(cli, "execute_verify", opens_a_socket)
    monkeypatch.setattr(cli, "execute_impact", raises)
    doc = json.loads(_run_in_process(root).json_text)
    assert [(c["id"], c["failure"]) for c in doc["oq"]] == [
        ("OQ-01", None),
        ("OQ-02", None),
        ("OQ-03", "step 2: socket"),
        ("OQ-04", None),
        ("OQ-05", "step 1: ValueError"),
    ]
    assert _leftover_copies() == before


def test_editable_install_and_broken_packaged_data(tmp_path: Path):
    """T-133: under `uv run` (an editable install) `qualify` writes both records, every case
    passes, and it exits 1 with E-86's first failure; with `known_anomalies.json` removed, and with
    `cases.json` made invalid JSON, each run lists E-87's data fault and exits 1 without raising.
    (E-86, E-87)"""
    run = run_cli(["qualify", "--out", "q"], tmp_path)
    assert run.code == 1
    assert run.stdout == "qualify: NOT QUALIFIED - not an installed wheel (no hashed RECORD)\n"
    doc, _md = _record(tmp_path / "q")
    assert doc["iq"]["package_tree_sha256"] is None and doc["iq"]["files"] == 0
    assert {c["result"] for c in doc["oq"]} == {"PASS"}

    root = _copy_package(tmp_path / "a")
    (root / "_qualify" / "known_anomalies.json").unlink()
    doc = json.loads(_run_in_process(root).json_text)
    assert doc["iq"]["data_faults"] == ["_qualify/known_anomalies.json: missing"]
    assert doc["known_anomalies"] == [] and doc["verdict"] == "NOT QUALIFIED"

    root = _copy_package(tmp_path / "b")
    (root / "_qualify" / "cases.json").write_text("{not json", encoding="utf-8")
    record = _run_in_process(root)
    doc = json.loads(record.json_text)
    assert doc["iq"]["data_faults"] == ["_qualify/cases.json: not JSON: line 1 column 2"]
    assert doc["oq"] == [] and record.exit_code == 1

    root = _copy_package(tmp_path / "c")
    shutil.rmtree(root / "_qualify" / "hazards" / "golden")
    doc = json.loads(_run_in_process(root).json_text)
    assert [c["id"] for c in doc["oq"] if c["result"] == "FAIL"] == ["OQ-04"]
    assert any(f.startswith("_qualify/cases.json: OQ-04: ") for f in doc["iq"]["data_faults"])


def test_qualify_is_deterministic_offline_and_leaves_the_rest_alone(tmp_path: Path):
    """T-134: two `qualify` runs give byte-identical records; nothing outside `--out` changes and
    the socket guard is restored afterwards; `SOURCE_DATE_EPOCH=1793836800` adds `generated_at`
    to the JSON and the Markdown's §1, `abc` exits 2 writing nothing; an unwritable `--out` exits
    3; `--self-check` and the §9.8 fixture's `check` still reproduce their committed goldens.
    (I-022, I-023, E-85, R-111)"""
    original_init = socket.socket.__init__
    work = tmp_path / "work"
    work.mkdir()
    first = run_cli(["qualify", "--out", "one"], work)
    second = run_cli(["qualify", "--out", "two"], work)
    assert first.stdout == second.stdout
    for name in ("qualification.json", "QUALIFICATION_REPORT.md"):
        assert (work / "one" / name).read_bytes() == (work / "two" / name).read_bytes()
    assert sorted(p.name for p in work.iterdir()) == ["one", "two"]
    assert sorted(p.name for p in (work / "one").iterdir()) == [
        "QUALIFICATION_REPORT.md",
        "qualification.json",
    ]
    assert socket.socket.__init__ is original_init

    dated = run_cli(["qualify", "--out", "d"], work, env={"SOURCE_DATE_EPOCH": "1793836800"})
    doc, md = _record(work / "d")
    assert list(doc)[-1] == "generated_at" and doc["generated_at"] == "2026-11-05T00:00:00Z"
    verdict_section = md.split("## 2. Intended use")[0]
    assert "Generated at: 2026-11-05T00:00:00Z" in verdict_section
    assert dated.code == first.code

    bad = run_cli(["qualify", "--out", "x"], work, env={"SOURCE_DATE_EPOCH": "abc"})
    assert bad.code == 2 and "SOURCE_DATE_EPOCH: not a non-negative integer: abc" in bad.stderr
    assert not (work / "x").exists()

    (work / "blocked").write_text("a file, not a directory", encoding="utf-8")
    unwritable = run_cli(["qualify", "--out", "blocked/sub"], work)
    assert unwritable.code == 3 and unwritable.stdout == ""

    assert run_cli(["--self-check"], work).stdout == "self-check: ok\n"
    target = tmp_path / "target"
    shutil.copytree(FIXTURE, target)
    argv = ["check", "--spec", "SPEC.md", "--src", "src", "--tests", "tests"]
    argv += ["--results", "junit.xml", "--judge", "mock", "--strict", "--out", "out"]
    run_cli(argv, target)
    for name in ("speccheck.json", "SPEC_CONFORMANCE_REPORT.md"):
        assert (target / "out" / name).read_bytes() == (FIXTURE / "golden" / name).read_bytes()


def test_qualify_help_screen(tmp_path: Path):
    """T-136: `speccheck qualify --help` names `--out`, `--verbose`, `SOURCE_DATE_EPOCH`, the four
    exit codes and R-111's line; `speccheck --help` lists `qualify`; `qualify --root .` is a usage
    error. (R-111, C-19, R-41)"""
    screen = run_cli(["qualify", "--help"], tmp_path)
    assert screen.code == 0 and screen.stderr == ""
    text = screen.stdout
    flat = " ".join(text.split())
    for token in ("--out DIR", "--verbose", "SOURCE_DATE_EPOCH", "COLUMNS", "default: ."):
        assert token in flat, token
    assert "0 qualified   1 not qualified   2 usage error   3 --out not writable" in text
    assert "qualify: QUALIFIED - IQ <n> files, tree <first 12 hex digits>; OQ <k>/<k> cases" in text
    assert "qualify: NOT QUALIFIED - <first failure>" in text
    top = run_cli(["--help"], tmp_path)
    assert "qualify" in top.stdout
    assert run_cli(["qualify", "--root", "."], tmp_path).code == 2


def test_t137_the_release_tree_hash_is_recorded():
    """T-137 (recorded; this is its presence check): `SPEC_BUILD_REPORT.md` §0q records the
    package tree hash of this release as `package_tree_sha256 <64 hex>`, and the value equals the
    R-112 (a) computation over this tree's `src/speccheck/`; the run of `qualify` from an install
    of the release, and the release notes, are recorded there too. (R-112)"""
    report = (ROOT / "SPEC_BUILD_REPORT.md").read_text(encoding="utf-8")
    start = report.index("## 0q.")
    section = report[start : report.index("\n## 0p.", start)]
    match = re.search(r"package_tree_sha256 ([0-9a-f]{64})\b", section)
    assert match, "§0q records no package_tree_sha256"
    tree, _files = q.tree_of_directory(PKG)
    assert match.group(1) == tree
    assert f"tree {tree[:12]}; OQ 5/5 cases" in section


def test_t135_record_lists_only_anomalies_not_fixed_in_this_version(tmp_path: Path):
    """T-135 (R-115's selection): with anomalies fixed in an earlier version, in the running
    version, in a later version and in none, the record's `known_anomalies` and the Markdown's §6
    hold exactly the later and the unfixed ones, in file order; with none left §6 reads `None.`.
    (R-115, C-31, C-29)"""
    major, minor, patch = (int(p) for p in __version__.split("."))
    earlier, later = f"{major}.{minor - 1}.0", f"{major}.{minor}.{patch + 1}"

    def entry(ident: str, fixed: str | None) -> dict:
        return {
            "id": ident,
            "summary": f"summary of {ident}",
            "hazards": ["TH-01"],
            "workaround": f"workaround for {ident}",
            "found_in": "1.0.0",
            "fixed_in": fixed,
        }

    root = _copy_package(tmp_path)
    path = root / "_qualify" / "known_anomalies.json"
    entries = [
        entry("KA-91", earlier),
        entry("KA-92", None),
        entry("KA-93", __version__),
        entry("KA-94", later),
    ]
    path.write_text(json.dumps({"anomalies": entries}), encoding="utf-8")
    record = _run_in_process(root)
    doc = json.loads(record.json_text)
    assert [a["id"] for a in doc["known_anomalies"]] == ["KA-92", "KA-94"]
    assert doc["known_anomalies"][1] == entries[3]
    section = record.md_text.split("## 6. Known anomalies")[1].split("## 7.")[0]
    assert "| KA-92 | summary of KA-92 | TH-01 | workaround for KA-92 | 1.0.0 | — |" in section
    assert (
        f"| KA-94 | summary of KA-94 | TH-01 | workaround for KA-94 | 1.0.0 | {later} |" in section
    )
    assert "KA-91" not in section and "KA-93" not in section

    path.write_text(json.dumps({"anomalies": entries[:1] + entries[2:3]}), encoding="utf-8")
    record = _run_in_process(root)
    assert json.loads(record.json_text)["known_anomalies"] == []
    assert "## 6. Known anomalies\n\nNone.\n" in record.md_text
