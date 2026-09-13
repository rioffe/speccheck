"""§9.3 Results mapping (C-04)."""

from __future__ import annotations

import pytest

from speccheck.attribute import TestCase as SpecTestCase
from speccheck.results import RawResult, ResultsError, join_results, parse_junit

from .conftest import junit, spec_table

TEST_FILE = "def test_x():\n    '''R-01'''\n    assert True\n\n\ndef test_y():\n    '''C-01'''\n    assert True\n"


def _case(file: str, name: str, classname: str) -> SpecTestCase:
    return SpecTestCase(file, name, classname, 1, 3)


def test_both_roots_parse_and_children_map_to_outcomes(project):
    """T-15: <testsuites> and bare <testsuite> roots both parse; failure/error/skipped children
    map to the correct outcome. (R-05)"""
    cases = [
        ("tests.test_a", "p", "passed"),
        ("tests.test_a", "f", "failed"),
        ("tests.test_a", "e", "error"),
        ("tests.test_a", "s", "skipped"),
    ]
    for root in ("testsuites", "testsuite"):
        results = parse_junit(junit(cases, root=root).encode())
        assert [(r.name, r.outcome) for r in results] == [
            ("p", "passed"),
            ("f", "failed"),
            ("e", "error"),
            ("s", "skipped"),
        ]
    files = {"SPEC.md": spec_table([("R-01", "a"), ("C-01", "b")]), "tests/test_a.py": TEST_FILE}
    for root in ("testsuites", "testsuite"):
        files["junit.xml"] = junit(
            [("tests.test_a", "test_x", "passed"), ("tests.test_a", "test_y", "failed")], root=root
        )
        run = project(files).check()
        assert (run.status("R-01"), run.status("C-01")) == ("PASSING", "FAILING")


def test_classname_join_accepts_suffix_forms_and_rejects_partial_components():
    """T-16: the join accepts both `tests.test_core` and `test_core` for tests/test_core.py and
    rejects `unit_test_core`. (C-04)"""
    case = _case("tests/test_core.py", "test_x", "tests.test_core")
    for classname in ("tests.test_core", "test_core", ""):
        mapping = join_results([RawResult(classname, "test_x", "passed")], [case])
        assert mapping.outcomes[case].outcome == "passed", classname
    mapping = join_results([RawResult("unit_test_core", "test_x", "passed")], [case])
    assert mapping.outcomes == {} and [r.classname for r in mapping.unattributed] == [
        "unit_test_core"
    ]
    mapping = join_results([RawResult("other.tests.test_core", "test_x", "passed")], [case])
    assert mapping.outcomes == {}


def test_longest_suffix_wins_and_ties_are_unattributed(project):
    """T-58: with tests/a/test_core.py and tests/b/test_core.py, classname `tests.a.test_core`
    joins `a` only; classname `test_core` is unattributed with a Note naming both. (E-27, C-04)"""
    a = _case("tests/a/test_core.py", "test_x", "tests.a.test_core")
    b = _case("tests/b/test_core.py", "test_x", "tests.b.test_core")
    mapping = join_results([RawResult("tests.a.test_core", "test_x", "passed")], [a, b])
    assert list(mapping.outcomes) == [a] and mapping.notes == []
    mapping = join_results([RawResult("test_core", "test_x", "failed")], [a, b])
    assert mapping.outcomes == {} and len(mapping.unattributed) == 1
    assert mapping.notes == [
        "ambiguous result test_core::test_x: candidates tests/a/test_core.py::test_x, tests/b/test_core.py::test_x"
    ]
    files = {
        "SPEC.md": spec_table([("R-01", "a")]),
        "tests/a/test_core.py": "def test_x():\n    '''R-01'''\n    assert True\n",
        "tests/b/test_core.py": "def test_x():\n    '''R-01'''\n    assert True\n",
        "junit.xml": junit([("test_core", "test_x", "passed")]),
    }
    run = project(files).check()
    assert run.status("R-01") == "UNVERIFIED"
    assert run.json["unattributed_results"] == [
        {"classname": "test_core", "name": "test_x", "outcome": "passed"}
    ]
    assert run.json["notes"][0].startswith("ambiguous result test_core::test_x: candidates ")


def test_parametrized_names_join_and_empty_classname(project):
    """T-52: parametrized names join their case, `results` lists both with `param`, the outcome
    is the worst; everything from the first `[` is removed; an empty classname joins the unique
    case and is unattributed when two exist. (E-24, C-04, F-105)"""
    assert (
        RawResult("c", "test_x[3-True]", "passed").join_name,
        RawResult("c", "test_x[3-True]", "passed").param,
    ) == ("test_x", "3-True")
    assert (
        RawResult("c", "test_x[list[int]]", "passed").join_name,
        RawResult("c", "test_x[list[int]]", "passed").param,
    ) == ("test_x", "list[int]")
    assert (
        RawResult("c", "test_y[a][b]", "passed").join_name,
        RawResult("c", "test_y[a][b]", "passed").param,
    ) == ("test_y", "a][b")
    assert (
        RawResult("c", "test_plain", "passed").join_name,
        RawResult("c", "test_plain", "passed").param,
    ) == ("test_plain", None)
    assert RawResult("c", "test_open[", "passed").join_name == "test_open["
    files = {
        "SPEC.md": spec_table([("R-01", "a")]),
        "tests/test_p.py": "def test_x(v):\n    '''R-01'''\n    assert v\n",
        "junit.xml": junit(
            [
                ("tests.test_p", "test_x[3-True]", "passed"),
                ("tests.test_p", "test_x[0-False]", "failed"),
            ]
        ),
    }
    run = project(files).check()
    (edge,) = run.ids()["R-01"]["tests"]
    assert edge["outcome"] == "failed"
    assert edge["results"] == [
        {"name": "test_x[0-False]", "param": "0-False", "outcome": "failed"},
        {"name": "test_x[3-True]", "param": "3-True", "outcome": "passed"},
    ]
    files["junit.xml"] = junit([("", "test_x[1]", "passed")])
    assert project(files).check().status("R-01") == "PASSING"
    a = _case("tests/a/test_p.py", "test_x", "tests.a.test_p")
    b = _case("tests/b/test_p.py", "test_x", "tests.b.test_p")
    mapping = join_results([RawResult("", "test_x", "passed")], [a, b])
    assert mapping.outcomes == {} and len(mapping.unattributed) == 1 and len(mapping.notes) == 1


def test_duplicate_results_collapse_to_worst():
    """T-17: duplicate (classname, name) collapses to the worst outcome in the order
    error > failed > skipped > passed. (E-06)"""
    case = _case("tests/test_d.py", "test_x", "tests.test_d")
    for outcomes, expected in [
        (["passed", "skipped"], "skipped"),
        (["skipped", "failed", "passed"], "failed"),
        (["failed", "error", "passed"], "error"),
        (["passed", "passed"], "passed"),
    ]:
        mapping = join_results([RawResult("tests.test_d", "test_x", o) for o in outcomes], [case])
        assert mapping.outcomes[case].outcome == expected
        assert len(mapping.outcomes[case].results) == len(outcomes)
        assert mapping.notes == [
            f"duplicate result tests.test_d::test_x: {len(outcomes)} occurrences"
        ]


def test_unknown_results_are_unattributed_and_change_no_status(project):
    """T-18: results for unknown cases are listed as unattributed and change no status. (E-07)"""
    files = {
        "SPEC.md": spec_table([("R-01", "a")]),
        "tests/test_a.py": "def test_x():\n    '''R-01'''\n    assert True\n",
        "junit.xml": junit(
            [
                ("tests.test_a", "test_x", "passed"),
                ("tests.test_gone", "test_z", "failed"),
                ("tests.test_a", "test_x2", "error"),
            ]
        ),
    }
    run = project(files).check()
    assert run.status("R-01") == "PASSING"
    assert run.json["unattributed_results"] == [
        {"classname": "tests.test_a", "name": "test_x2", "outcome": "error"},
        {"classname": "tests.test_gone", "name": "test_z", "outcome": "failed"},
    ]
    assert run.code == 0
    assert "| tests.test_gone | test_z | failed |" in run.md


def test_malformed_xml_and_nameless_testcase_exit_3(project):
    """T-19: malformed XML and a <testcase> without name each exit 3. (E-05)"""
    with pytest.raises(ResultsError, match="^results: "):
        parse_junit(b"<testsuites><testsuite>")
    with pytest.raises(ResultsError, match="^results: "):
        parse_junit(b'<testsuites><testcase classname="c"/></testsuites>')
    with pytest.raises(ResultsError, match="^results: "):
        parse_junit(b"<report/>")
    for xml in (
        "<testsuites><testsuite>",
        '<testsuites><testcase classname="c"/></testsuites>',
        "<report/>",
    ):
        proj = project(
            {"SPEC.md": spec_table([("R-01", "a")]), "src/a.py": "# R-01\n", "junit.xml": xml}
        )
        run = proj.check()
        assert run.code == 3
        assert run.stderr.startswith("ERROR results: ")
        assert not (proj.path / "speccheck.json").exists()
