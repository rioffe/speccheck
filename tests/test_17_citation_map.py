"""§9.17 The citation map (C-23, R-103, K-19, E-70..E-73, I-019; v1.23, v1.23.1).

Ids the self-applied spec does not declare, and `<ns>:ID` forms, are built at runtime so this
file cites none of them (F-713).
"""

from __future__ import annotations

import json

from .conftest import junit, run_cli, spec_table
from .test_07_cli import SUMMARY_RE

UNDECLARED = "R-" + "98"  # not declared in this repository's SPEC.md
SPEC = spec_table(
    [("R-01", "one"), ("R-02", "two"), ("R-03", "three"), ("R-04", "four"), ("R-05", "five")],
    retired={"R-05"},
)
PY = (
    '"""Module docstring."""\n\n\n'
    "def test_a():\n    assert 1 == 1\n\n\n"
    'def test_b():\n    """R-02"""\n    assert 2 == 2\n'
)
JS = "it('adds', () => { expect(1 + 1).toBe(2) })\n"
RESULTS = junit(
    [
        ("tests.test_core", "test_a", "passed"),
        ("tests.test_core", "test_b", "passed"),
        ("tests/calc.test.ts", "adds", "passed"),
    ]
)
ENTRIES = [
    {"id": "R-01", "file": "tests/test_core.py", "test": "test_a"},
    {"id": "R-03", "file": "tests/test_core.py", "test": ""},
    {"id": "R-04", "file": "tests/calc.test.ts", "test": "adds"},
    {"id": "R-02", "file": "tests/test_core.py", "test": "test_b"},  # literal duplicate (E-73)
    {"id": "R-01", "file": "tests/test_core.py", "test": "renamed_away"},  # unresolved (E-71)
]
BASE = ["--spec", "SPEC.md", "--src", "src", "--tests", "tests", "--results", "junit.xml"]


def _map(entries: list[dict], **top: object) -> str:
    return json.dumps({"schema_version": "1.0", "citations": entries, **top})


def _files(map_text: str | None = None, map_name: str = "map.json") -> dict[str, str]:
    files = {
        "SPEC.md": SPEC,
        "src/x.py": "",
        "tests/test_core.py": PY,
        "tests/calc.test.ts": JS,
        "junit.xml": RESULTS,
    }
    if map_text is not None:
        files[map_name] = map_text
    return files


def _check(proj, *extra: str, out: str = "out") -> tuple[int, dict, str, str]:
    run = run_cli(["check", *BASE, "--out", out, *extra], proj.path)
    if run.code not in (0, 1):
        return run.code, {}, "", run.stderr
    doc = json.loads((proj.path / out / "speccheck.json").read_text())
    md = (proj.path / out / "SPEC_CONFORMANCE_REPORT.md").read_text()
    return run.code, doc, md, run.stdout


def _by_id(doc: dict) -> dict[str, dict]:
    return {r["id"]: r for r in doc["ids"]}


def test_t110_map_reproduces_literal_statuses_and_labels(project):
    """T-110: a map resolving a Python case, a file-level case and a JavaScript case reproduces
    the statuses of the same project with literal citations; each mapped `tests[]` entry has
    `mapped: true` and `lines: []`; the summary ends `; citations: 3 mapped`; the Markdown
    renders `<file> (map)`; a literal duplicate stays `mapped: false` and does not raise the
    count; an unresolved entry is one Note; `citation_map` counts R + U == N. (R-103, C-23,
    E-71, E-72, E-73, C-07, C-08, §5.1)"""
    literal_py = PY.replace('"""Module docstring."""', '"""Module docstring. R-03"""').replace(
        "def test_a():\n", 'def test_a():\n    """R-01"""\n'
    )
    literal = project(
        {**_files(), "tests/test_core.py": literal_py, "tests/calc.test.ts": "// R-04\n" + JS}
    )
    lit_code, lit_doc, _, _ = _check(literal)
    mapped = project(_files(_map(ENTRIES)))
    code, doc, md, stdout = _check(mapped, "--citation-map", "map.json")
    ids = ["R-01", "R-02", "R-03", "R-04"]
    assert [_by_id(doc)[i]["status"] for i in ids] == [_by_id(lit_doc)[i]["status"] for i in ids]
    assert [_by_id(doc)[i]["status"] for i in ids] == [
        "PASSING",
        "PASSING",
        "UNVERIFIED",
        "PASSING",
    ]
    r01 = _by_id(doc)["R-01"]["tests"][0]
    assert (r01["mapped"], r01["lines"], r01["declared"]) == (True, [], True)
    assert list(r01)[list(r01).index("declared") + 1] == "mapped"
    assert _by_id(doc)["R-02"]["tests"][0]["mapped"] is False
    assert stdout.rstrip("\n").endswith("; citations: 3 mapped")
    assert SUMMARY_RE.match(stdout.rstrip("\n"))  # T-44's §5.1 regex, suffix included
    assert "tests/test_core.py (map)" in md and "tests/calc.test.ts (map)" in md
    assert doc["citation_map"] == {"file": "map.json", "entries": 5, "resolved": 4, "unresolved": 1}
    keys = list(doc)
    assert keys.index("unattributed_results") + 1 == keys.index("citation_map")
    assert "citation-map entry unresolved: R-01 tests/test_core.py renamed_away" in doc["notes"]
    assert code == lit_code  # the map changes no exit code on its own (R-103)


def test_t110_map_dangling_stale_judge_explain_impact_ratio(project):
    """T-110: an undeclared id is dangling and a retired one stale, at the case's start line,
    each with `mapped: true` (F-704); under `--judge mock` the mapped edge is judged with
    `declared: true` (D-57); `declared_ratio` is the same with and without the map (F-703);
    `explain` renders `(mapped)`; `impact` lists the mapped test case. (R-103, C-23, E-72,
    C-07, C-18, C-13)"""
    extra = [
        {"id": UNDECLARED, "file": "tests/test_core.py", "test": "test_a"},
        {"id": "R-05", "file": "tests/test_core.py", "test": "test_a"},
    ]
    proj = project(_files(_map(ENTRIES + extra)))
    _, doc, md, stdout = _check(proj, "--citation-map", "map.json", "--judge", "mock")
    assert doc["dangling"] == [
        {"id": UNDECLARED, "file": "tests/test_core.py", "line": 4, "mapped": True}
    ]
    assert doc["stale"] == [{"id": "R-05", "file": "tests/test_core.py", "line": 4, "mapped": True}]
    assert stdout.rstrip("\n").endswith("; citations: 5 mapped")
    r01 = _by_id(doc)["R-01"]["tests"][0]
    assert r01["verdict"] is not None and r01["declared"] is True
    _, plain, _, _ = _check(proj, out="plain")
    assert doc["metrics"]["declared_ratio"] == plain["metrics"]["declared_ratio"]
    assert "mapped" not in plain["dangling"][0] if plain["dangling"] else True
    trace = run_cli(["explain", "R-01", *BASE, "--citation-map", "map.json"], proj.path).stdout
    assert "tests/test_core.py::test_a (passed) [not judged] (mapped)" in trace
    imp = [
        "impact",
        "--spec",
        "SPEC.md",
        "--changed",
        "R-01",
        "--tests",
        "tests",
        "--citation-map",
        "map.json",
        "--out",
        "imp",
    ]
    assert run_cli(imp, proj.path).code == 0
    cases = json.loads((proj.path / "imp" / "impact.json").read_text())["test_cases"]
    assert ("tests/test_core.py", "test_a") in {(c["file"], c["name"]) for c in cases}


def test_t110_map_and_manifest_under_tests_are_never_scanned(project):
    """T-110 (v1.23.1, F-702): the map file and a `--proof-results` manifest placed under
    `--tests` produce no citation: the reports equal those of the map kept outside the scan
    roots, apart from the map's own path. (C-03, C-23)"""
    manifest = json.dumps({"build": {"exit": 0}, "theorems": [{"name": "t", "ids": ["R-02"]}]})
    outside = project(_files(_map(ENTRIES)))
    _, ref, _, _ = _check(outside, "--citation-map", "map.json")
    inside = project(
        {**_files(_map(ENTRIES), "tests/citation_map.json"), "tests/proof.json": manifest}
    )
    _, doc, _, _ = _check(
        inside, "--citation-map", "tests/citation_map.json", "--proof-results", "tests/proof.json"
    )
    assert doc["citation_map"]["file"] == "tests/citation_map.json"
    for key in ("ids", "dangling", "stale"):
        assert doc[key] == ref[key], key
    assert not any(t["file"].endswith(".json") for r in doc["ids"] for t in r["tests"])


def test_t111_map_faults(project):
    """T-111: an unresolved entry is a Note with the exit unchanged; malformed JSON, a wrong
    `schema_version`, an entry with a missing or extra key, a `ns:`-prefixed id and a map over
    2 MiB each exit 3 with `citation-map: …`; a map outside `--root` and an unreadable one exit 2
    with `--citation-map: …`; no fault writes a report. (E-70, E-71, K-19, K-18)"""
    ok = {"id": "R-01", "file": "tests/test_core.py", "test": "test_a"}
    contract_faults = {
        "malformed": "{not json",
        "schema": _map([ok]).replace('"1.0"', '"2.0"'),
        "missing": _map([{"id": "R-01", "file": "tests/test_core.py"}]),
        "extra": _map([{**ok, "why": "x"}]),
        "foreign": _map([{**ok, "id": "platform" + ":R-01"}]),
        "not-a-list": json.dumps({"schema_version": "1.0", "citations": {}}),
        "oversize": _map([ok], pad="x" * (2 * 1024 * 1024)),
    }
    for label, text in contract_faults.items():
        proj = project(_files(text))
        run = run_cli(["check", *BASE, "--out", "out", "--citation-map", "map.json"], proj.path)
        assert run.code == 3 and "citation-map: " in run.stderr, (label, run.stderr)
        assert not (proj.path / "out").exists(), label
    proj = project(_files(_map([ok])))
    for arg in ("../elsewhere.json", "tests"):
        run = run_cli(["check", *BASE, "--out", "out", "--citation-map", arg], proj.path)
        assert run.code == 2 and "--citation-map" in run.stderr or "outside --root" in run.stderr
        assert not (proj.path / "out").exists(), arg
    unknown_top = project(_files(_map([ok], note="ignored")))
    code, doc, _, _ = _check(unknown_top, "--citation-map", "map.json")
    assert doc["citation_map"]["resolved"] == 1  # unknown top-level keys are ignored


def test_t109_no_map_flag_means_no_map_keys(project):
    """T-109 (the citation-map half): without `--citation-map` neither `citation_map` nor any
    `mapped` key exists and the summary line has no suffix (I-019). (I-019, C-23)"""
    proj = project(_files())
    _, doc, _, stdout = _check(proj)
    assert "citation_map" not in doc
    assert not any("mapped" in t for r in doc["ids"] for t in r["tests"])
    assert "mapped" not in stdout
