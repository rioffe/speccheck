"""§9.6 Reports and determinism (C-07, C-08)."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
from decimal import Decimal
from pathlib import Path

from speccheck import judge_llm, report
from speccheck.graph import ratio
from speccheck.report import dumps

from .conftest import FIXTURE, SIMPLE_PROJECT, run_cli, spec_table, write_tree

LLM_ENV = {
    "SPECCHECK_JUDGE_URL": "http://localhost:11434/v1/chat/completions",
    "SPECCHECK_JUDGE_MODEL": "m",
    "SPECCHECK_JUDGE_API_KEY": "k",
}
TOP_KEYS = [
    "schema_version",
    "spec",
    "judge",
    "judge_available",
    "strict",
    "max_unknown",
    "strict_judge_failure",
    "ids",
    "dangling",
    "stale",
    "unattributed_results",
    "notes",
    "metrics",
    "exit_code",
]
ID_KEYS = ["id", "family", "statement", "line", "status", "src", "tests", "unrun"]
TEST_KEYS = ["file", "name", "classname", "lines", "outcome", "results", "verdict"]
METRIC_KEYS = [
    "declared",
    "retired",
    "in_scope",
    "by_status",
    "conformance_ratio",
    "conformance",
    "by_family",
]


def _golden_copy(tmp_path: Path) -> Path:
    dst = tmp_path / "target"
    shutil.copytree(FIXTURE, dst)
    return dst


def _golden_args(*extra: str) -> list[str]:
    return [
        "check",
        "--spec",
        "SPEC.md",
        "--src",
        "src",
        "--tests",
        "tests",
        "--results",
        "junit.xml",
        *extra,
    ]


def test_json_shape_orders_rounding_and_verdict_keys(tmp_path: Path, monkeypatch):
    """T-34: speccheck.json validates against the C-07 shape: key order, sort orders, rounding,
    no absolute paths, no timestamps; by_family has all six keys and by_status all seven on every
    fixture including single-family ones; judge_available is null/true/true/false per mode; every
    tests[] entry carries `verdict` (null on a FAILING ID, on a skipped edge, and under --judge
    none); tests[].name is "" for a file-level case; five Notes come out in code-point order in
    both reports; every ratio has exactly four decimals and ties round half-even.
    (R-13, R-20, K-09, C-07, E-37, E-38)"""
    target = _golden_copy(tmp_path)
    assert run_cli(_golden_args("--judge", "mock", "--strict"), target).code == 1
    raw = (target / "speccheck.json").read_text(encoding="utf-8")
    doc = json.loads(raw)
    assert list(doc) == TOP_KEYS
    assert all(list(rec) == ID_KEYS for rec in doc["ids"])
    assert all(list(t) == TEST_KEYS for rec in doc["ids"] for t in rec["tests"])
    assert list(doc["metrics"]) == METRIC_KEYS + [
        "judge_strength_ratio",
        "judge_strength",
        "unknown_rate",
    ]
    assert list(doc["metrics"]["by_family"]) == ["R", "C", "I", "K", "E", "T"]
    assert list(doc["metrics"]["by_status"]) == [
        "PASSING",
        "WEAKLY_PASSING",
        "FAILING",
        "SKIPPED",
        "UNVERIFIED",
        "UNTESTED",
        "UNCITED",
    ]
    ids = [r["id"] for r in doc["ids"]]
    assert ids == [
        "R-01",
        "R-02",
        "R-03",
        "R-04",
        "C-01",
        "C-02",
        "C-03",
        "I-001",
        "I-002",
        "K-01",
        "K-02",
        "E-01",
        "E-02",
        "T-01",
        "T-02",
        "T-03",
    ]
    assert raw.endswith("}\n") and raw.startswith('{\n  "schema_version": "1.0",\n')
    assert str(target) not in raw and "\\" not in raw.replace("\\n", "").replace('\\"', "")
    # R-20: every path in the report is relative to --root and uses "/" regardless of host OS
    paths = [rec["spec"] for rec in [doc]]
    for rec in doc["ids"]:
        paths += [s["file"] for s in rec["src"]] + [t["file"] for t in rec["tests"]]
        paths += [u["file"] for u in rec["unrun"]]
    paths += [e["file"] for e in doc["dangling"] + doc["stale"]]
    assert paths and all(
        not p.startswith(("/", "\\")) and "\\" not in p and not re.match(r"^[A-Za-z]:", p)
        for p in paths
    ), paths
    assert (
        "src/calc/core.py" in paths and "tests/test_core.py" in paths and doc["spec"] == "SPEC.md"
    )
    assert not re.search(r"20\d\d-\d\d-\d\d", raw)
    assert re.findall(
        r'"(?:conformance|ratio|judge_strength|unknown_rate|max_unknown)": (\S+?),?\n', raw
    )
    for num in re.findall(
        r'"(?:conformance|ratio|judge_strength|unknown_rate|max_unknown)": ([0-9.]+)', raw
    ):
        assert re.fullmatch(r"[01]\.[0-9]{4}", num), num
    by_id = {r["id"]: r for r in doc["ids"]}
    assert by_id["T-03"]["tests"][0]["verdict"] is None  # FAILING ID
    assert by_id["K-01"]["tests"][0]["verdict"] is None  # skipped outcome
    assert by_id["E-02"]["tests"][0]["name"] == "" and by_id["E-02"]["tests"][0]["verdict"] is None
    for rec in doc["ids"]:
        for t in rec["tests"]:
            assert "verdict" in t
            assert t["results"] == sorted(t["results"], key=lambda r: r["name"])
            assert t["lines"] == sorted(set(t["lines"]))
    assert doc["judge_available"] is True
    # judge none: verdict null everywhere, judge_available null, no judge metrics
    run_none = run_cli(_golden_args(), target)
    doc_none = run_none.json
    assert (
        doc_none["judge_available"] is None
        and "judge_strength" not in doc_none["metrics"]
        and "judge_prompt_sha256" not in doc_none
    )
    assert all(t["verdict"] is None for rec in doc_none["ids"] for t in rec["tests"])
    # llm with zero eligible edges -> true, no request; llm with every call failing -> false
    write_tree(tmp_path / "zero", {"SPEC.md": spec_table([("R-01", "a")]), "src/a.py": "# R-01\n"})
    calls = []
    monkeypatch.setattr(judge_llm, "_httpx_post", lambda *a: calls.append(a) or (500, ""))
    run_zero = run_cli(
        ["check", "--spec", "SPEC.md", "--src", "src", "--judge", "llm"],
        tmp_path / "zero",
        env=LLM_ENV,
    )
    assert (
        run_zero.json["judge_available"] is True
        and calls == []
        and run_zero.json["metrics"]["unknown_rate"] is None
    )
    write_tree(tmp_path / "fail", SIMPLE_PROJECT)
    run_fail = run_cli(_golden_args("--judge", "llm"), tmp_path / "fail", env=LLM_ENV)
    assert run_fail.json["judge_available"] is False and len(calls) == 3
    # single-family fixture: still six families and seven statuses
    fam = run_zero.json["metrics"]["by_family"]
    assert list(fam) == ["R", "C", "I", "K", "E", "T"] and fam["C"] == {
        "in_scope": 0,
        "passing": 0,
        "ratio": None,
    }
    assert list(run_zero.json["metrics"]["by_status"]) == list(doc["metrics"]["by_status"])
    # five Notes in code-point order in both reports
    five = {
        "SPEC.md": spec_table([("R-01", "a")]),
        "src/big.txt": b"x" * (2 * 1024 * 1024 + 1),
        "src/latin.py": b"# \xff R-01\n",
        "tests/test_bad.py": "def broken(:\n",
        "tests/test_z.py": "class Plain:\n    def test_x(self):\n        pass\n",
    }
    write_tree(tmp_path / "five", five)
    shutil.copy(
        Path(__file__).parent / "data" / "markers" / "ignore_file_line2.py",
        tmp_path / "five" / "tests" / "test_q.py",
    )
    os.symlink(tmp_path / "five" / "src" / "latin.py", tmp_path / "five" / "src" / "link.py")
    run_five = run_cli(
        ["check", "--spec", "SPEC.md", "--src", "src", "--tests", "tests"], tmp_path / "five"
    )
    notes = run_five.json["notes"]
    assert len(notes) == 6 and notes == sorted(notes)
    md_notes = [
        ln[2:]
        for ln in run_five.md.split("## 9. Notes\n\n", 1)[1].splitlines()
        if ln.startswith("- ")
    ]
    assert md_notes == notes
    # rounding: quantized Decimal, half-even, not round()'s binary result
    assert ratio(1, 8) == Decimal("0.1250")
    assert ratio(1, 32) == Decimal(
        "0.0312"
    )  # 0.03125 -> half-even -> 0.0312 (round() gives 0.0312 too)
    assert ratio(3, 32) == Decimal("0.0938")  # 0.09375 -> half-even -> 0.0938
    assert ratio(5, 32) == Decimal(
        "0.1562"
    )  # 0.15625 -> half-even -> 0.1562; float round(0.15625, 4) == 0.1562
    assert ratio(7, 32) == Decimal("0.2188")  # 0.21875 -> half-even -> 0.2188
    assert ratio(2, 3) == Decimal("0.6667") and ratio(1, 1) == Decimal("1.0000")
    assert (
        dumps({"a": report._Num(Decimal("0.9000")), "b": None})
        == '{\n  "a": 0.9000,\n  "b": null\n}\n'
    )


def test_markdown_layout(tmp_path: Path):
    """T-35: the Markdown report has the nine C-08 sections in order, one per-ID row per
    declared ID, retired rows with exactly the ID cell struck, an em dash for every unjudged
    case and `(file)` for every file-level case, and every file:line also present in the JSON.
    (R-12, I-003, E-37, Q-011)"""
    target = _golden_copy(tmp_path)
    run = run_cli(_golden_args("--judge", "mock", "--strict"), target)
    md, doc = run.md, run.json
    headings = [ln for ln in md.splitlines() if ln.startswith("## ")]
    assert headings == [
        "## 1. Verdict",
        "## 2. Metrics",
        "## 3. Per-ID evidence",
        "## 4. Dangling citations",
        "## 5. Stale citations",
        "## 6. Unattributed results",
        "## 7. Unrun test citations",
        "## 8. Judge details",
        "## 9. Notes",
    ]
    assert md.startswith(
        "# Specification Conformance Report\n\n**Spec:** `SPEC.md` · **Judge:** mock (available) · **Strict:** on\n"
    )
    # F-207: the parenthetical is absent when judge_available is null (--judge none)
    none_run = run_cli(_golden_args("--judge", "none"), target)
    assert "**Judge:** none · **Strict:** off" in none_run.md.splitlines()[2]
    assert run.stdout.strip() in md
    per_id = md.split("## 3. Per-ID evidence\n\n", 1)[1].split("\n## 4.", 1)[0].splitlines()[2:]
    assert len(per_id) == len(doc["ids"]) == 16
    id_cells = [row.split(" | ")[0][2:] for row in per_id]
    assert id_cells == [
        f"~~{r['id']}~~" if r["status"] == "RETIRED" else r["id"] for r in doc["ids"]
    ]
    for row in per_id:
        if row.startswith("| ~~"):
            assert row.count("~~") == 2
    unjudged = sum(1 for rec in doc["ids"] for t in rec["tests"] if t["verdict"] is None)
    assert "\n".join(per_id).count("· —)") == unjudged == 4
    file_level = sum(1 for rec in doc["ids"] for t in rec["tests"] if t["name"] == "")
    assert "\n".join(per_id).count("`(file)`") == file_level == 1
    assert "| E-02 | tests/test_core.py | (file) |" in md
    json_locations = set()
    for rec in doc["ids"]:
        json_locations.update(f"{s['file']}:{ln}" for s in rec["src"] for ln in s["lines"])
        json_locations.update(f"{t['file']}:{ln}" for t in rec["tests"] for ln in t["lines"])
        json_locations.update(
            f"{e['file']}:{e['line']}"
            for t in rec["tests"]
            if t["verdict"]
            for e in t["verdict"]["evidence"]
        )
    json_locations.update(f"{d['file']}:{d['line']}" for d in doc["dangling"] + doc["stale"])
    md_locations = set(re.findall(r"((?:src|tests)/[\w./-]+\.py):(\d+)", md))
    assert {f"{f}:{ln}" for f, ln in md_locations} <= json_locations
    assert '"name": ""' in (target / "speccheck.json").read_text(
        encoding="utf-8"
    ) and "(file)" not in (target / "speccheck.json").read_text(encoding="utf-8")
    # judge none: no §8, em dashes everywhere
    run_none = run_cli(_golden_args(), target)
    assert "## 8. Judge details" not in run_none.md and "## 9. Notes" in run_none.md


def test_determinism_across_paths_out_placement_and_leftovers(tmp_path: Path):
    """T-36: two runs on the golden fixture with --judge mock are byte-identical; so after
    copying the fixture elsewhere; so with --src . and --out inside the source root; so with
    planted .tmp leftovers under --out (never scanned, deleted by the run). (R-16, I-002, E-23, E-34)"""
    a = _golden_copy(tmp_path / "one")
    first = run_cli(_golden_args("--judge", "mock", "--strict"), a)
    second = run_cli(_golden_args("--judge", "mock", "--strict"), a)
    assert first.stdout == second.stdout
    assert (a / "speccheck.json").read_bytes() == (
        FIXTURE / "golden" / "speccheck.json"
    ).read_bytes()
    assert (a / "SPEC_CONFORMANCE_REPORT.md").read_bytes() == (
        FIXTURE / "golden" / "SPEC_CONFORMANCE_REPORT.md"
    ).read_bytes()
    b = _golden_copy(tmp_path / "two" / "deeper")
    run_cli(_golden_args("--judge", "mock", "--strict"), b)
    assert (b / "speccheck.json").read_bytes() == (a / "speccheck.json").read_bytes()
    # --src . with --out inside the source root: reports and spec produce no citations
    c = _golden_copy(tmp_path / "three")
    args = [
        "check",
        "--spec",
        "SPEC.md",
        "--src",
        ".",
        "--tests",
        "tests",
        "--results",
        "junit.xml",
        "--judge",
        "mock",
        "--out",
        "src/out",
    ]
    r1 = run_cli(args, c)
    j1 = (c / "src" / "out" / "speccheck.json").read_bytes()
    m1 = (c / "src" / "out" / "SPEC_CONFORMANCE_REPORT.md").read_bytes()
    (c / "src" / "out" / ".speccheck.json.deadbeef.tmp").write_text("R-01 R-02 R-03 planted\n")
    (c / "src" / "out" / ".SPEC_CONFORMANCE_REPORT.md.deadbeef.tmp").write_text("R-01 planted\n")
    r2 = run_cli(args, c)
    assert r1.stdout == r2.stdout
    assert (c / "src" / "out" / "speccheck.json").read_bytes() == j1
    assert (c / "src" / "out" / "SPEC_CONFORMANCE_REPORT.md").read_bytes() == m1
    assert not list((c / "src" / "out").glob(".*.tmp"))
    doc = json.loads(j1)
    cited_files = {s["file"] for rec in doc["ids"] for s in rec["src"]} | {
        d["file"] for d in doc["dangling"] + doc["stale"]
    }
    assert not any(f.startswith("src/out/") or f in ("SPEC.md", "junit.xml") for f in cited_files)
    assert any(
        f.startswith("tests/") for f in cited_files
    )  # `--src .` did scan the tests tree as source


def test_metrics_recomputable_from_evidence_table(tmp_path: Path):
    """T-37: every metric in the report is recomputable from the report's own evidence table plus
    the results file (this test recomputes them independently). (R-24)"""
    target = _golden_copy(tmp_path)
    run = run_cli(_golden_args("--judge", "mock", "--strict"), target)
    doc = run.json
    import xml.etree.ElementTree as ET

    outcomes = {}
    for tc in ET.fromstring((target / "junit.xml").read_bytes()).iter("testcase"):
        kids = {c.tag for c in tc}
        o = (
            "failed"
            if "failure" in kids
            else "error"
            if "error" in kids
            else "skipped"
            if "skipped" in kids
            else "passed"
        )
        name = tc.get("name")
        name = name[: name.index("[")] if name.endswith("]") and "[" in name else name
        key = (tc.get("classname"), name)
        rank = {"passed": 0, "skipped": 1, "failed": 2, "error": 3}
        outcomes[key] = max([outcomes.get(key, "passed"), o], key=rank.get)
    recomputed = {}
    for rec in doc["ids"]:
        if rec["status"] == "RETIRED":
            continue
        tests = rec["tests"]
        if not tests:
            recomputed[rec["id"]] = (
                "UNCITED" if (rec["family"] == "T" or not rec["src"]) else "UNTESTED"
            )
            continue
        outs = [
            outcomes[(t["classname"], t["name"])]
            for t in tests
            if (t["classname"], t["name"]) in outcomes
        ]
        if not outs:
            recomputed[rec["id"]] = "UNVERIFIED"
        elif any(o in ("failed", "error") for o in outs):
            recomputed[rec["id"]] = "FAILING"
        elif all(o == "skipped" for o in outs):
            recomputed[rec["id"]] = "SKIPPED"
        else:
            verdicts = [t["verdict"]["verdict"] for t in tests if t["verdict"]]
            weak = (
                verdicts
                and "ASSERTS" not in verdicts
                and any(v in ("EXECUTES_ONLY", "UNRELATED") for v in verdicts)
            )
            recomputed[rec["id"]] = "WEAKLY_PASSING" if weak else "PASSING"
    assert recomputed == {
        rec["id"]: rec["status"] for rec in doc["ids"] if rec["status"] != "RETIRED"
    }
    m = doc["metrics"]
    in_scope = len(recomputed)
    passing = sum(1 for s in recomputed.values() if s == "PASSING")
    assert m["in_scope"] == in_scope and m["conformance_ratio"] == f"{passing}/{in_scope}"
    assert Decimal(str(m["conformance"])) == ratio(passing, in_scope)
    for s in m["by_status"]:
        assert m["by_status"][s] == sum(1 for v in recomputed.values() if v == s)
    for fam, entry in m["by_family"].items():
        fam_ids = [i for i in recomputed if i.startswith(fam + "-")]
        fam_passing = sum(1 for i in fam_ids if recomputed[i] == "PASSING")
        assert entry == {
            "in_scope": len(fam_ids),
            "passing": fam_passing,
            "ratio": None if not fam_ids else float(ratio(fam_passing, len(fam_ids))),
        }
    weak = sum(1 for s in recomputed.values() if s == "WEAKLY_PASSING")
    judged = [t["verdict"] for rec in doc["ids"] for t in rec["tests"] if t["verdict"]]
    assert m["judge_strength_ratio"] == f"{passing}/{passing + weak}"
    assert Decimal(str(m["unknown_rate"])) == ratio(
        sum(1 for v in judged if v["verdict"] == "UNKNOWN"), len(judged)
    )
    assert m["declared"] == len(doc["ids"]) and m["retired"] == sum(
        1 for r in doc["ids"] if r["status"] == "RETIRED"
    )


def _tree_hash(root: Path, skip: set[str]) -> dict[str, str]:
    out = {}
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.name not in skip:
            out[str(p.relative_to(root))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def test_only_the_two_reports_are_created(tmp_path: Path):
    """T-38: only the two report files are created; input trees are byte-identical before and
    after (hash comparison). (R-19, I-001)"""
    target = _golden_copy(tmp_path)
    before = _tree_hash(target, set())
    run = run_cli(_golden_args("--judge", "mock", "--out", "reports"), target)
    assert run.code == 1
    after = _tree_hash(target, set())
    new = set(after) - set(before)
    assert new == {"reports/speccheck.json", "reports/SPEC_CONFORMANCE_REPORT.md"}
    assert {k: v for k, v in after.items() if k not in new} == before
    outside = _tree_hash(tmp_path, set())
    assert all(k.startswith("target/") for k in outside)
