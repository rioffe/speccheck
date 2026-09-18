"""§9.8 Golden fixture (end to end)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from .conftest import FIXTURE, run_cli

ARGS = [
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
]


def _copy(tmp_path: Path) -> Path:
    dst = tmp_path / "target"
    shutil.copytree(FIXTURE, dst)
    return dst


def test_golden_fixture_matches_byte_for_byte(tmp_path: Path):
    """T-46: fixtures/target/ (>= 12 IDs across all six families, 2 retired, src/, tests/,
    junit.xml) with its planted defects produces reports byte-identical to golden/ and exits 1.
    (all of §2)"""
    target = _copy(tmp_path)
    out = target / "fresh-out"
    run = run_cli(ARGS + ["--root", ".", "--out", str(out)], target)
    assert run.code == 1
    assert (out / "speccheck.json").read_bytes() == (
        FIXTURE / "golden" / "speccheck.json"
    ).read_bytes()
    assert (out / "SPEC_CONFORMANCE_REPORT.md").read_bytes() == (
        FIXTURE / "golden" / "SPEC_CONFORMANCE_REPORT.md"
    ).read_bytes()
    doc = json.loads((out / "speccheck.json").read_text(encoding="utf-8"))
    assert doc["metrics"]["declared"] >= 12 and doc["metrics"]["retired"] == 2
    assert {r["family"] for r in doc["ids"]} == set("RCIKET")
    statuses = {r["id"]: r["status"] for r in doc["ids"]}
    assert (
        statuses["R-03"] == "UNCITED"
        and statuses["C-02"] == "UNTESTED"
        and statuses["E-01"] == "UNVERIFIED"
    )
    assert (
        statuses["T-03"] == "FAILING"
        and statuses["K-01"] == "SKIPPED"
        and statuses["I-002"] == "WEAKLY_PASSING"
    )
    assert doc["dangling"] == [{"id": "R-09", "file": "src/calc/core.py", "line": 30}]
    assert doc["stale"] == [{"id": "R-04", "file": "src/calc/legacy.py", "line": 5}]
    assert doc["unattributed_results"] == [
        {"classname": "tests.test_gone", "name": "test_vanished", "outcome": "passed"}
    ]
    by_id = {r["id"]: r for r in doc["ids"]}
    assert any(t["name"] == "" for t in by_id["E-02"]["tests"])
    assert (FIXTURE / "golden").is_dir() and not (FIXTURE / "out").exists()


def _sub(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert old in text, old
    path.write_text(text.replace(old, new), encoding="utf-8")


REPAIRS = {
    "R-03 UNCITED -> PASSING": (
        lambda t: (
            (t / "src/calc/core.py").write_text(
                (t / "src/calc/core.py").read_text()
                + "\n\ndef multiply(a, b):\n    # R-03\n    return _round(a * b)\n"
            ),
            (t / "tests/test_core.py").write_text(
                (t / "tests/test_core.py").read_text()
                + "\n\ndef test_multiply():\n    '''R-03'''\n    from calc.core import multiply\n\n    assert multiply(2, 3) == 6\n"
            ),
            _sub(
                t / "junit.xml",
                "</testsuite>",
                '<testcase classname="tests.test_core" name="test_multiply" />\n  </testsuite>',
            ),
        ),
        {"R-03": "PASSING"},
        {"UNCITED": 0, "PASSING": 9},
    ),
    "C-02 UNTESTED -> PASSING": (
        lambda t: (
            (t / "tests/test_core.py").write_text(
                (t / "tests/test_core.py").read_text()
                + "\n\ndef test_scale_pure():\n    '''C-02'''\n    values = [1]\n    scale(values, 2)\n    assert values == [1]\n"
            ),
            _sub(
                t / "junit.xml",
                "</testsuite>",
                '<testcase classname="tests.test_core" name="test_scale_pure" />\n  </testsuite>',
            ),
        ),
        {"C-02": "PASSING"},
        {"UNTESTED": 0, "PASSING": 9},
    ),
    "E-01 UNVERIFIED -> PASSING": (
        lambda t: _sub(
            t / "junit.xml",
            "</testsuite>",
            '<testcase classname="tests.test_core" name="test_scale_negative" />\n  </testsuite>',
        ),
        {"E-01": "PASSING"},
        {"UNVERIFIED": 0, "PASSING": 9},
    ),
    "T-03 FAILING -> PASSING": (
        lambda t: _sub(
            t / "junit.xml",
            '<testcase classname="tests.test_core" name="test_subtract_precision">\n      <failure message="assert 1.0 == 1.01">AssertionError</failure>\n    </testcase>',
            '<testcase classname="tests.test_core" name="test_subtract_precision" />',
        ),
        {"T-03": "PASSING"},
        {"FAILING": 0, "PASSING": 9},
    ),
    "K-01 SKIPPED -> PASSING": (
        lambda t: _sub(
            t / "junit.xml",
            '<testcase classname="tests.test_core" name="test_divide_fast">\n      <skipped message="timing test not run in CI" />\n    </testcase>',
            '<testcase classname="tests.test_core" name="test_divide_fast" />',
        ),
        {"K-01": "PASSING"},
        {"SKIPPED": 0, "PASSING": 9},
    ),
    "I-002 WEAKLY_PASSING -> PASSING": (
        lambda t: _sub(
            t / "tests/test_core.py",
            "    scale([1, 2, 3], 2)\n",
            "    assert len(scale([1, 2, 3], 2)) == 3\n",
        ),
        {"I-002": "PASSING"},
        {"WEAKLY_PASSING": 0, "PASSING": 9},
    ),
    "dangling removed": (
        lambda t: _sub(t / "src/calc/core.py", "R-09 territory", "future territory"),
        {},
        {},
    ),
    "stale removed": (
        lambda t: _sub(t / "src/calc/legacy.py", "R-04 (retired)", "modulo (retired)"),
        {},
        {},
    ),
    "unattributed removed": (
        lambda t: _sub(
            t / "junit.xml",
            '    <testcase classname="tests.test_gone" name="test_vanished" />\n',
            "",
        ),
        {},
        {},
    ),
    "file-level citation removed": (
        lambda t: _sub(t / "tests/test_core.py", "E-02 (empty input)", "empty input"),
        {},
        {},
    ),
}


@pytest.mark.parametrize("label", list(REPAIRS))
def test_removing_each_planted_defect_flips_exactly_its_row(tmp_path: Path, label: str):
    """T-47: removing each planted defect in turn flips exactly the expected row and metric
    (one sub-test per defect). (R-06, R-24)"""
    golden = json.loads((FIXTURE / "golden" / "speccheck.json").read_text(encoding="utf-8"))
    target = _copy(tmp_path)
    repair, expected_statuses, expected_counts = REPAIRS[label]
    repair(target)
    run = run_cli(ARGS, target)
    doc = run.json
    golden_statuses = {r["id"]: r["status"] for r in golden["ids"]}
    new_statuses = {r["id"]: r["status"] for r in doc["ids"]}
    changed = {i: s for i, s in new_statuses.items() if golden_statuses[i] != s}
    assert changed == expected_statuses
    for status, count in expected_counts.items():
        assert doc["metrics"]["by_status"][status] == count
    passing = doc["metrics"]["by_status"]["PASSING"]
    assert doc["metrics"]["conformance_ratio"] == f"{passing}/14"
    if label == "dangling removed":
        assert doc["dangling"] == [] and doc["stale"] == golden["stale"]
    elif label == "stale removed":
        assert doc["stale"] == [] and doc["dangling"] == golden["dangling"]
    elif label == "unattributed removed":
        assert doc["unattributed_results"] == [] and doc["dangling"] == golden["dangling"]
    elif label == "file-level citation removed":
        e02 = {r["id"]: r for r in doc["ids"]}["E-02"]
        assert (
            e02["unrun"] == []
            and all(t["name"] != "" for t in e02["tests"])
            and e02["status"] == "PASSING"
        )
    else:
        assert doc["dangling"] == golden["dangling"] and doc["stale"] == golden["stale"]
        assert doc["unattributed_results"] == golden["unattributed_results"]
    assert run.code == 1  # every single repair still leaves other defects


SWIFT_FIXTURE = FIXTURE.parent / "target-swift"
SWIFT_ARGS = [
    "check",
    "--spec",
    "SPEC.md",
    "--src",
    "Sources",
    "--tests",
    "Tests",
    "--results",
    "junit.xml",
    "--judge",
    "mock",
    "--strict",
]


def test_swift_golden_fixture_matches_byte_for_byte(tmp_path: Path):
    """T-71: fixtures/target-swift/ (a SwiftPM-shaped project: Swift Testing file with a nested
    suite, a parameterized and a disabled test, doc-comment citations; an XCTest file; a
    `**[port]**`-decorated declaration; a junit.xml that is SwiftPM's swift-testing output plus
    an XCTest suite) with its planted defects produces reports byte-identical to golden/ and
    exits 1. (R-31, R-32, R-16, R-24)"""
    target = tmp_path / "target-swift"
    shutil.copytree(SWIFT_FIXTURE, target)
    out = target / "fresh-out"
    run = run_cli(SWIFT_ARGS + ["--root", ".", "--out", str(out)], target)
    assert run.code == 1
    assert run.stdout == (SWIFT_FIXTURE / "golden" / "summary.txt").read_text(encoding="utf-8")
    assert (out / "speccheck.json").read_bytes() == (
        SWIFT_FIXTURE / "golden" / "speccheck.json"
    ).read_bytes()
    assert (out / "SPEC_CONFORMANCE_REPORT.md").read_bytes() == (
        SWIFT_FIXTURE / "golden" / "SPEC_CONFORMANCE_REPORT.md"
    ).read_bytes()
    doc = json.loads((out / "speccheck.json").read_text(encoding="utf-8"))
    assert doc["metrics"]["declared"] >= 10 and doc["metrics"]["retired"] == 0
    assert {r["family"] for r in doc["ids"]} == set("RCIKET")
    statuses = {r["id"]: r["status"] for r in doc["ids"]}
    assert statuses == {
        "R-01": "PASSING",
        "R-02": "PASSING",
        "R-03": "UNCITED",
        "C-01": "PASSING",
        "C-02": "UNTESTED",
        "I-001": "PASSING",
        "I-002": "WEAKLY_PASSING",
        "K-01": "SKIPPED",
        "K-02": "FAILING",
        "E-01": "UNVERIFIED",
        "E-02": "PASSING",
        "T-01": "PASSING",
        "T-02": "PASSING",
        "T-03": "FAILING",
    }
    by_id = {r["id"]: r for r in doc["ids"]}
    # the parameterized test joined by identifier; the nested suite and XCTest by dotted chain
    t01 = {(t["name"], t["classname"]) for t in by_id["T-01"]["tests"]}
    assert t01 == {("add", "CalcTests.CalcTests")}
    assert {(t["name"], t["classname"]) for t in by_id["E-02"]["tests"]} == {
        ("scaleEmpty", "CalcTests.CalcTests.Edges")
    }
    assert ("testVersionString", "CalcTests.LegacyTests") in {
        (t["name"], t["classname"]) for t in by_id["R-01"]["tests"]
    }
    assert [t["name"] for t in by_id["E-01"]["tests"]] == [""]  # file-level (E-43)
    assert doc["unattributed_results"] == [
        {"classname": "CalcTests.GoneTests", "name": "testVanished", "outcome": "passed"}
    ]
    assert doc["dangling"] == [] and doc["stale"] == []
    assert any(
        n.startswith(
            "undelimited tests in Tests/CalcTests/CalcTests.swift: CalcTests.testScaleNegative"
        )
        for n in doc["notes"]
    )
    assert (SWIFT_FIXTURE / "golden").is_dir() and not (SWIFT_FIXTURE / "out").exists()
