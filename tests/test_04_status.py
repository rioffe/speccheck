"""§9.4 Status algorithm and metrics (C-05, C-07)."""

from __future__ import annotations

import json
import shutil
from decimal import Decimal
from pathlib import Path

from speccheck.graph import ratio

from .conftest import FIXTURE, junit, run_cli, spec_table

SPEC2 = spec_table([("R-01", "a"), ("C-01", "b")])


def _one_test(ident: str, name: str = "test_x") -> str:
    return f"def {name}():\n    '''{ident}'''\n    assert True\n"


def test_one_fixture_per_deterministic_status(project, tmp_path: Path):
    """T-20: one fixture per deterministic status — UNCITED, UNTESTED, UNVERIFIED, FAILING,
    SKIPPED, PASSING, RETIRED — each asserting exactly that status; the UNCITED fixture has
    empty --src and --tests and exits 1. (R-06, E-19)"""
    spec = spec_table([("R-01", "a"), ("C-01", "b")], retired={"C-01"})
    base = {"SPEC.md": spec, "src/.keep": "", "tests/.keep": ""}

    def run_with(extra: dict, results: bool):
        files = dict(base)
        files.update(extra)
        return project(files).check(results=results)

    run = run_with({}, results=False)
    assert run.status("R-01") == "UNCITED" and run.status("C-01") == "RETIRED" and run.code == 1
    run = run_with({"src/a.py": "# R-01\n"}, results=False)
    assert run.status("R-01") == "UNTESTED"
    run = run_with({"tests/test_a.py": _one_test("R-01")}, results=False)
    assert run.status("R-01") == "UNVERIFIED"
    run = run_with(
        {
            "tests/test_a.py": _one_test("R-01"),
            "junit.xml": junit([("tests.test_a", "test_x", "failed")]),
        },
        results=True,
    )
    assert run.status("R-01") == "FAILING"
    run = run_with(
        {
            "tests/test_a.py": _one_test("R-01"),
            "junit.xml": junit([("tests.test_a", "test_x", "skipped")]),
        },
        results=True,
    )
    assert run.status("R-01") == "SKIPPED"
    run = run_with(
        {
            "tests/test_a.py": _one_test("R-01"),
            "junit.xml": junit([("tests.test_a", "test_x", "passed")]),
        },
        results=True,
    )
    assert run.status("R-01") == "PASSING" and run.code == 0
    # E-19: both roots absent -> everything UNCITED, exit 1
    proj = project({"SPEC.md": spec})
    run = run_cli(["check", "--spec", "SPEC.md"], proj.path)
    assert run.code == 1 and run.status("R-01") == "UNCITED"


def test_step_4_mixtures(project):
    """T-21: one failed and three passed citing tests -> FAILING; all skipped -> SKIPPED; some
    skipped and some passed -> PASSING. (C-05 step 4)"""
    tests = "".join(_one_test("R-01", f"test_{i}") for i in range(4))

    def run_with(outcomes: list[str]):
        results = junit([("tests.test_a", f"test_{i}", o) for i, o in enumerate(outcomes)])
        return project({"SPEC.md": SPEC2, "tests/test_a.py": tests, "junit.xml": results}).check()

    assert run_with(["passed", "failed", "passed", "passed"]).status("R-01") == "FAILING"
    assert run_with(["passed", "error", "passed", "passed"]).status("R-01") == "FAILING"
    assert run_with(["skipped"] * 4).status("R-01") == "SKIPPED"
    assert run_with(["skipped", "passed", "skipped", "passed"]).status("R-01") == "PASSING"


def test_unrun_cases_are_listed_and_ignored(project):
    """T-22: citing cases absent from results are listed under `unrun` and do not affect the
    status. (E-08)"""
    tests = _one_test("R-01", "test_ran") + _one_test("R-01", "test_not_run")
    run = project(
        {
            "SPEC.md": SPEC2,
            "tests/test_a.py": tests,
            "junit.xml": junit([("tests.test_a", "test_ran", "passed")]),
        }
    ).check()
    rec = run.ids()["R-01"]
    assert rec["status"] == "PASSING"
    assert rec["unrun"] == [{"file": "tests/test_a.py", "name": "test_not_run"}]
    assert [t["outcome"] for t in rec["tests"]] == ["passed", None]
    run = project(
        {
            "SPEC.md": SPEC2,
            "tests/test_a.py": tests,
            "junit.xml": junit([("tests.test_a", "test_other", "passed")]),
        }
    ).check()
    assert run.status("R-01") == "UNVERIFIED" and len(run.ids()["R-01"]["unrun"]) == 2


def test_dangling_and_stale_citations(project):
    """T-23: dangling and stale citations are listed with file and line; strikethrough in code
    does not retire anything. (R-07, R-08, E-20)"""
    spec = spec_table([("R-01", "a"), ("R-02", "b")], retired={"R-02"})
    files = {
        "SPEC.md": spec,
        "src/a.py": "# R-01 fine\n# R-02 stale\n# ~~R-03~~ looks retired but is dangling\n",
        "tests/test_a.py": "def test_x():\n    '''R-01 and R-02'''\n    assert True  # C-05 dangling\n",
    }
    run = project(files).check(results=False)
    assert run.json["dangling"] == [
        {"id": "R-03", "file": "src/a.py", "line": 3},
        {"id": "C-05", "file": "tests/test_a.py", "line": 3},
    ]
    assert run.json["stale"] == [
        {"id": "R-02", "file": "src/a.py", "line": 2},
        {"id": "R-02", "file": "tests/test_a.py", "line": 2},
    ]
    assert run.status("R-02") == "RETIRED" and "R-03" not in run.ids()
    assert "| R-03 | src/a.py | 3 |" in run.md and "| R-02 | tests/test_a.py | 2 |" in run.md


def test_metrics_match_hand_computed_values_on_golden(tmp_path: Path):
    """T-24: conformance, per-family ratios, and counts match hand-computed values on the golden
    fixture; a family with zero in-scope IDs reports null/n/a, not 0.0, and nothing raises.
    (R-09, I-008)"""
    shutil.copytree(FIXTURE, tmp_path / "t")
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
            "mock",
            "--strict",
        ],
        tmp_path / "t",
    )
    m = run.json["metrics"]
    assert (m["declared"], m["retired"], m["in_scope"]) == (16, 2, 14)
    assert m["by_status"] == {
        "PASSING": 8,
        "WEAKLY_PASSING": 1,
        "FAILING": 1,
        "SKIPPED": 1,
        "UNVERIFIED": 1,
        "UNTESTED": 1,
        "UNCITED": 1,
    }
    assert m["conformance_ratio"] == "8/14" and Decimal(str(m["conformance"])) == Decimal("0.5714")
    assert m["by_family"] == {
        "R": {"in_scope": 3, "passing": 2, "ratio": 0.6667},
        "C": {"in_scope": 2, "passing": 1, "ratio": 0.5},
        "I": {"in_scope": 2, "passing": 1, "ratio": 0.5},
        "K": {"in_scope": 2, "passing": 1, "ratio": 0.5},
        "E": {"in_scope": 2, "passing": 1, "ratio": 0.5},
        "T": {"in_scope": 3, "passing": 2, "ratio": 0.6667},
    }
    assert (
        m["judge_strength_ratio"] == "8/9"
        and m["judge_strength"] == 0.8889
        and m["unknown_rate"] == 0.0
    )
    assert ratio(0, 0) is None and ratio(1, 3) == Decimal("0.3333")
    # a single-family spec: the other five families are null / n/a
    single = write_single_family(tmp_path / "single")
    run = run_cli(["check", "--spec", "SPEC.md", "--src", "src"], single)
    fam = run.json["by_family"] if "by_family" in run.json else run.json["metrics"]["by_family"]
    assert fam["R"] == {"in_scope": 1, "passing": 0, "ratio": 0.0}
    for f in "CIKET":
        assert fam[f] == {"in_scope": 0, "passing": 0, "ratio": None}
    assert "| C | 0 | 0 | n/a |" in run.md
    raw = (single / "speccheck.json").read_text(encoding="utf-8")
    assert '"ratio": 0.0000' in raw and '"ratio": null' in raw


def write_single_family(path: Path) -> Path:
    path.mkdir()
    (path / "SPEC.md").write_text(spec_table([("R-01", "only")]), encoding="utf-8")
    (path / "src").mkdir()
    (path / "src" / "a.py").write_text("# R-01\n", encoding="utf-8")
    return path


def test_retired_ids_excluded_from_denominators_but_listed_once(project):
    """T-25: retired IDs are excluded from every denominator and still appear in `ids` exactly
    once. (R-02, I-003)"""
    spec = spec_table([("R-01", "a"), ("R-02", "b"), ("C-01", "c")], retired={"R-02", "C-01"})
    run = project(
        {
            "SPEC.md": spec,
            "src/a.py": "# R-01\n",
            "tests/test_a.py": _one_test("R-01"),
            "junit.xml": junit([("tests.test_a", "test_x", "passed")]),
        }
    ).check()
    m = run.json["metrics"]
    assert (m["declared"], m["retired"], m["in_scope"], m["conformance_ratio"]) == (3, 2, 1, "1/1")
    assert m["by_family"]["C"] == {"in_scope": 0, "passing": 0, "ratio": None}
    assert [r["id"] for r in run.json["ids"]] == ["R-01", "R-02", "C-01"]
    assert [r["status"] for r in run.json["ids"]].count("RETIRED") == 2
    assert (
        run.md.count("| ~~R-02~~ | RETIRED |") == 1 and run.md.count("| ~~C-01~~ | RETIRED |") == 1
    )
    assert "RETIRED" not in m["by_status"]


def test_family_t_semantics(project):
    """T-53: a T id cited only in a source file is UNCITED; a T id cited by a passing test is
    PASSING; T ids are counted in in_scope, conformance, and by_family.T. (R-25, E-25)"""
    spec = spec_table([("R-01", "a"), ("T-01", "t1"), ("T-02", "t2")])
    files = {
        "SPEC.md": spec,
        "src/a.py": "# R-01 T-01 T-02\n",
        "tests/test_a.py": "def test_x():\n    '''T-02: R-01'''\n    assert True\n",
        "junit.xml": junit([("tests.test_a", "test_x", "passed")]),
    }
    run = project(files).check()
    assert run.status("T-01") == "UNCITED" and run.ids()["T-01"]["src"] == [
        {"file": "src/a.py", "lines": [1]}
    ]
    assert run.status("T-02") == "PASSING" and run.status("R-01") == "PASSING"
    m = run.json["metrics"]
    assert m["in_scope"] == 3 and m["conformance_ratio"] == "2/3"
    assert m["by_family"]["T"] == {"in_scope": 2, "passing": 1, "ratio": 0.5}
    assert json.loads(json.dumps(m["by_status"]))["UNCITED"] == 1
