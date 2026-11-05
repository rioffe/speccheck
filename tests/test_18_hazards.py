"""§9.18 Hazards: the CONTROLS marker, the roll-up and the risk file (C-27, C-28, R-108, R-109; v1.25).

Hazard ids (`HAZ-1`) are not spec-id tokens, so naming them here cites nothing.
"""

from __future__ import annotations

import json

import pytest

from speccheck.extract import parse_spec

from .conftest import junit, run_cli
from .test_07_cli import SUMMARY_RE

LONG = "H" + "x" * 64  # 65 characters: one over C-27's HAZID cap (K-20)

MARKED = f"""# Spec

| ID | Statement |
| -- | --------- |
| **R-01** *(controls: HAZ-2, HAZ-1)* | adds |
| **C-01** *(controls: HAZ-2)* | divides |
| ~~**R-02**~~ *(controls: HAZ-5)* | old |
| **R-03** *(recorded)* *(controls: HAZ-4)* | three |
| **T-01** *(controls: HAZ-9)* | add test |
| **K-01** *(controls: )* | bound |
| **K-02** *(controls: {LONG})* | bound two |

### C-02 *(controls: HAZ-3)* Title

Body of C-02.
"""


def unmarked(spec: str) -> str:
    """The same spec with every CONTROLS marker removed (and nothing else)."""
    import re

    return re.sub(r" \*\(controls:[^)]*\)\*", "", spec)


TESTS = (
    "def test_a():\n"
    "    '''R-01 R-03 C-02 K-01 K-02 T-01'''\n"
    "    assert 1 == 1\n\n\n"
    "def test_b():\n"
    "    '''C-01'''\n"
    "    assert 2 == 2\n"
)
RESULTS = junit([("tests.test_h", "test_a", "passed"), ("tests.test_h", "test_b", "failed")])


def files(spec: str) -> dict[str, str]:
    return {"SPEC.md": spec, "src/x.py": "", "tests/test_h.py": TESTS, "junit.xml": RESULTS}


def section(md: str, heading: str) -> str:
    start = md.index(heading)
    nxt = md.find("\n## ", start + 1)
    return md[start : nxt if nxt != -1 else len(md)]


def test_t126_marker_grammar_and_positions():
    """T-126 (grammar half): the marker after the ID form, after RECORDED, and in a heading;
    sorted and de-duplicated; ignored on a T id (E-78); malformed — empty, a 65-character HAZID —
    controls nothing (E-80); it is never part of a statement or title and makes no edge.
    (R-108, C-01, C-02, C-27, E-78, E-80, K-20)"""
    index = parse_spec(MARKED, "SPEC.md")
    by = index.by_id()
    assert by["R-01"].controls == ("HAZ-1", "HAZ-2")
    assert by["R-01"].text == "adds"
    assert by["R-03"].controls == ("HAZ-4",)
    assert by["R-02"].controls == ("HAZ-5",)  # a retired declaration keeps its marker
    assert by["C-02"].controls == ("HAZ-3",) and by["C-02"].title == "Title"
    assert by["T-01"].controls == ()
    assert by["K-01"].controls == () and by["K-02"].controls == ()
    assert index.controls_notes == (
        "controls marker ignored on T-01: not an R/C/I/K/E id",
        "malformed controls marker on K-01",
        "malformed controls marker on K-02",
    )
    twin = parse_spec(unmarked(MARKED), "SPEC.md")
    assert index.edges == twin.edges
    assert [(s.id, s.text, s.title) for s in index.ids] == [
        (s.id, s.text, s.title) for s in twin.ids
    ]
    dup = parse_spec("| ID | S |\n| -- | - |\n| **R-01** *(controls: B,A, B)* | x |\n", "S")
    assert dup.ids[0].controls == ("A", "B")


def test_t126_roll_up_reports_and_inertness(project):
    """T-126 (roll-up half): HAZ-1 and HAZ-3 VERIFIED, HAZ-2 NOT_VERIFIED (C-01 fails), HAZ-4
    VERIFIED through a recorded-marker row, HAZ-5 UNCONTROLLED (retired control only, E-81);
    `controls` only on marked ids; `hazards` after `edges`; `## 10. Hazards`; the summary suffix;
    every id status, metric, edge and the §3 table unchanged by the markers; `explain` prints the
    `controls:` line; `impact` ignores the markers. (R-108, C-07, C-08, C-18, C-27, E-81)"""
    marked = project(files(MARKED))
    plain = project(files(unmarked(MARKED)))
    run, base = marked.check("--judge", "mock"), plain.check("--judge", "mock")
    doc, ref = run.json, base.json
    assert run.code == base.code == 1  # C-01 fails either way

    hazards = {h["id"]: h for h in doc["hazards"]}
    assert list(hazards) == ["HAZ-1", "HAZ-2", "HAZ-3", "HAZ-4", "HAZ-5"]
    assert hazards["HAZ-1"] == {
        "id": "HAZ-1",
        "title": None,
        "controls": ["R-01"],
        "status": "VERIFIED",
    }
    assert hazards["HAZ-2"]["controls"] == ["R-01", "C-01"]
    assert hazards["HAZ-2"]["status"] == "NOT_VERIFIED"
    assert hazards["HAZ-3"]["status"] == "VERIFIED"
    assert hazards["HAZ-4"]["status"] == "VERIFIED"
    assert hazards["HAZ-5"] == {
        "id": "HAZ-5",
        "title": None,
        "controls": [],
        "status": "UNCONTROLLED",
    }
    keys = list(doc)
    assert keys.index("hazards") == keys.index("edges") + 1
    recs = {r["id"]: r for r in doc["ids"]}
    assert recs["R-01"]["controls"] == ["HAZ-1", "HAZ-2"]
    assert list(recs["R-01"]).index("controls") == list(recs["R-01"]).index("recorded") + 1
    assert "controls" not in recs["T-01"] and "controls" not in recs["K-01"]
    assert "1 uncontrolled hazard(s): HAZ-5" in doc["notes"]
    assert "malformed controls marker on K-01" in doc["notes"]  # E-80 reaches check's report

    # nothing else moves (R-108)
    for key in ("metrics", "edges", "dangling", "stale", "exit_code"):
        assert doc[key] == ref[key], key
    strip = [{k: v for k, v in r.items() if k != "controls"} for r in doc["ids"]]
    assert strip == ref["ids"]
    assert section(run.md, "## 3.") == section(base.md, "## 3.")
    assert "hazards" not in ref and "## 10. Hazards" not in base.md

    table = section(run.md, "## 10. Hazards")
    assert "| Hazard | Title | Controls | Status |" in table
    assert "| HAZ-2 | — | R-01 (PASSING); C-01 (FAILING) | NOT_VERIFIED |" in table
    assert "| HAZ-5 | — | — | UNCONTROLLED |" in table
    assert run.stdout.rstrip("\n").endswith("; hazards: 3/5 verified")
    assert SUMMARY_RE.match(run.stdout.rstrip("\n"))
    assert run.stdout.rstrip("\n") in run.md

    exp = run_cli(
        ["explain", "R-01", "--spec", "SPEC.md", "--src", "src", "--tests", "tests",
         "--results", "junit.xml"],
        marked.path,
    )
    lines = exp.stdout.splitlines()
    assert lines[2] == "controls: HAZ-1 (VERIFIED), HAZ-2 (NOT_VERIFIED)"
    assert lines[1].startswith("status: ")
    exp_plain = run_cli(
        ["explain", "K-01", "--spec", "SPEC.md", "--src", "src", "--tests", "tests",
         "--results", "junit.xml"],
        plain.path,
    )
    exp_k = run_cli(
        ["explain", "K-01", "--spec", "SPEC.md", "--src", "src", "--tests", "tests",
         "--results", "junit.xml"],
        marked.path,
    )
    assert exp_k.stdout == exp_plain.stdout  # no marker in effect -> no controls line

    for proj in (marked, plain):
        imp = run_cli(["impact", "--spec", "SPEC.md", "--changed", "R-01", "--out", "imp"], proj.path)
        assert imp.code == 0
    assert (marked.path / "imp" / "impact.json").read_bytes() == (
        plain.path / "imp" / "impact.json"
    ).read_bytes()


def test_t126_weak_control_is_not_verified(project):
    """T-126: a control the mock judge downgrades to WEAKLY_PASSING leaves its hazard
    NOT_VERIFIED — WEAKLY_PASSING is not PASSING (C-27)."""
    spec = "| ID | S |\n| -- | - |\n| **R-01** *(controls: HAZ-1)* | adds |\n"
    tests = "def test_a():\n    '''R-01'''\n    print(1)\n"
    proj = project(
        {
            "SPEC.md": spec,
            "tests/test_w.py": tests,
            "junit.xml": junit([("tests.test_w", "test_a", "passed")]),
        }
    )
    doc = proj.check("--judge", "mock").json
    assert doc["ids"][0]["status"] == "WEAKLY_PASSING"
    assert doc["hazards"][0]["status"] == "NOT_VERIFIED"


RISK_SPEC = """| ID | Statement |
| -- | --------- |
| **R-01** *(controls: HAZ-1)* | one |
| **R-02** *(controls: HAZ-2, HAZ-7)* | two |
| **R-03** | three |
"""
RISK_TESTS = "def test_a():\n    '''R-01 R-02'''\n    assert 1 == 1\n"
RISK = {
    "hazards": [
        {"id": "HAZ-9"},
        {"id": "HAZ-1", "title": "Wrong measurement | shown"},
        {"id": "HAZ-2", "title": "see R-03", "severity": "ignored"},
    ]
}


def risk_project(project, risk: object = RISK, spec: str = RISK_SPEC, path: str = "tests/risk.json"):
    body = risk if isinstance(risk, (str, bytes)) else json.dumps(risk)
    return project(
        {
            "SPEC.md": spec,
            "tests/test_r.py": RISK_TESTS,
            path: body,
            "junit.xml": junit([("tests.test_r", "test_a", "passed")]),
        }
    )


def test_t127_risk_file_uncontrolled_hazard_fails_strict(project):
    """T-127: a listed hazard no id controls is UNCONTROLLED (E-81) and fails --strict even though
    every cited id is PASSING; without --strict the run exits 0 and reads UNPROVEN; titles reach
    both reports; a marker hazard the file does not list is a Note (E-79); the risk file is never
    scanned (its "R-03" cites nothing). (R-109, R-15, R-105, C-28, E-79, E-81, C-03)"""
    proj = risk_project(project)
    strict = proj.check("--risk-file", "tests/risk.json", "--strict", "--out", "s")
    loose = proj.check("--risk-file", "tests/risk.json", "--out", "l")
    doc = strict.json_at(proj.path / "s")
    hazards = {h["id"]: h for h in doc["hazards"]}
    assert list(hazards) == ["HAZ-1", "HAZ-2", "HAZ-7", "HAZ-9"]
    assert hazards["HAZ-9"]["status"] == "UNCONTROLLED"
    assert hazards["HAZ-7"] == {"id": "HAZ-7", "title": None, "controls": ["R-02"], "status": "VERIFIED"}
    assert hazards["HAZ-1"]["title"] == "Wrong measurement | shown"
    assert "1 uncontrolled hazard(s): HAZ-9" in doc["notes"]
    assert "1 hazard(s) not in the risk file: HAZ-7" in doc["notes"]
    assert {r["id"]: r["status"] for r in doc["ids"]}["R-03"] == "UNCITED"
    assert strict.code == 1 and strict.stdout.startswith("speccheck: NOT CONFORMING")
    assert loose.code == 0 and loose.stdout.startswith("speccheck: UNPROVEN")
    assert loose.stdout.rstrip("\n").endswith("; hazards: 3/4 verified")
    md = strict.md_at(proj.path / "s")
    assert "| HAZ-1 | Wrong measurement \\| shown | R-01 (PASSING) | VERIFIED |" in md

    # with HAZ-9 controlled and R-03 cited, --strict passes; HAZ-7 (E-79) never affects the exit
    spec = RISK_SPEC.replace("| **R-03** | three |", "| **R-03** *(controls: HAZ-9)* | three |")
    ok = risk_project(project, spec=spec)
    (ok.path / "tests/test_r.py").write_text(
        "def test_a():\n    '''R-01 R-02 R-03'''\n    assert 1 == 1\n", encoding="utf-8"
    )
    green = ok.check("--risk-file", "tests/risk.json", "--strict")
    assert green.code == 0 and green.stdout.startswith("speccheck: CONFORMING")
    assert green.stdout.rstrip("\n").endswith("; hazards: 4/4 verified")


def test_t127_empty_risk_file_and_marker_free_spec(project):
    """T-127: an empty `hazards` list over a marker-free spec yields `hazards: []` and the suffix
    `; hazards: 0/0 verified`, with nothing UNCONTROLLED. (C-27, C-28)"""
    spec = "| ID | S |\n| -- | - |\n| **R-01** | one |\n| **R-02** | two |\n| **R-03** | three |\n"
    proj = risk_project(project, risk={"hazards": []}, spec=spec)
    (proj.path / "tests/test_r.py").write_text(
        "def test_a():\n    '''R-01 R-02 R-03'''\n    assert 1 == 1\n", encoding="utf-8"
    )
    run = proj.check("--risk-file", "tests/risk.json", "--strict")
    assert run.json["hazards"] == []
    assert run.code == 0 and run.stdout.rstrip("\n").endswith("; hazards: 0/0 verified")
    assert "## 10. Hazards" in run.md


@pytest.mark.parametrize(
    ("risk", "reason"),
    [
        ({"hazards": [{"id": "HAZ-1"}, {"id": "HAZ-1"}]}, "duplicate hazard id HAZ-1"),
        ({"hazards": [{"id": "bad id"}]}, "not a hazard id"),
        ({"hazards": [{"id": "HAZ-1", "title": 3}]}, "title is not a string"),
        ({"items": []}, "no hazards list"),
        ({"hazards": ["HAZ-1"]}, "not an object"),
        ("{not json", "not UTF-8 JSON"),
        (b"x" * (2 * 1024 * 1024 + 1), "over 2 MiB"),
    ],
)
def test_t127_malformed_risk_file_exits_3(project, risk, reason):
    """T-127 / E-84 / K-20: a malformed risk file exits 3 with `--risk-file: <reason>` and writes
    no report. (C-28, E-84, K-20)"""
    proj = risk_project(project, risk=risk)
    run = proj.check("--risk-file", "tests/risk.json", "--out", "o")
    assert run.code == 3
    assert run.stderr.startswith("ERROR --risk-file: ") and reason in run.stderr
    assert not (proj.path / "o").exists() or not any((proj.path / "o").iterdir())


def test_t127_risk_file_usage_faults(project, tmp_path):
    """T-127: an unreadable risk file and one outside --root exit 2 (E-09); `impact` and `explain`
    reject the flag. (R-109, E-09)"""
    proj = risk_project(project)
    missing = proj.check("--risk-file", "nope.json")
    assert missing.code == 2 and "--risk-file: not a readable file: nope.json" in missing.stderr
    outside = tmp_path / "outside.json"
    outside.write_text("{}", encoding="utf-8")
    out = proj.check("--risk-file", str(outside))
    assert out.code == 2 and "outside --root" in out.stderr
    imp = run_cli(
        ["impact", "--spec", "SPEC.md", "--changed", "R-01", "--risk-file", "tests/risk.json"],
        proj.path,
    )
    exp = run_cli(["explain", "R-01", "--spec", "SPEC.md", "--risk-file", "tests/risk.json"], proj.path)
    assert imp.code == 2 and exp.code == 2
