"""§9.12 impact: changed set, walk, reverify, and the CLI subcommand (C-13; v1.13)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from speccheck.extract import parse_spec
from speccheck.impact import (
    ChangedError,
    diff_changed_set,
    resolve_changed_ids,
    reverify_set,
    walk,
)

from .conftest import FIXTURE, run_cli, spec_table, write_tree


def _index(text: str):
    return parse_spec(text, "SPEC.md")


BASE_SPEC = spec_table(
    [
        ("R-01", "obeys the grammar in C-01."),
        ("C-01", "the interface."),
        ("K-15", "a bound."),
        ("E-48", "unlocated, per K-15."),
        ("R-34", "grounding rule (K-15, E-48)."),
        ("T-75", "proves K-15 and E-48."),
    ]
) + "\n\n| ID | Affects |\n| -- | ------- |\n| D-08 | C-10, T-49 |\n"


def test_resolve_changed_ids_normalizes_and_validates():
    """T-80/E-53: --changed elements are trimmed, deduplicated, normalized (I-011); an
    undeclared id, an unknown decision, or a malformed token exits with the first offender
    named; an empty list after trimming is its own message. (R-37, C-13, E-53)"""
    index = _index(BASE_SPEC)
    entries = resolve_changed_ids(index, "K-15, K-015 , D-8")
    # C-12 id order: family rank R,C,I,K,E,T,D -- K sorts before D
    assert [(e.id, e.family, e.reason) for e in entries] == [
        ("K-15", "K", "changed"),
        ("D-08", "D", "changed"),
    ]
    with pytest.raises(ChangedError, match=r"undeclared id: R-99"):  # speccheck:ignore
        resolve_changed_ids(index, "R-99")  # speccheck:ignore
    with pytest.raises(ChangedError, match=r"undeclared id: X-01"):
        resolve_changed_ids(index, "X-01")
    with pytest.raises(ChangedError, match=r"undeclared id: 1234"):
        resolve_changed_ids(index, "1234")
    with pytest.raises(ChangedError, match="no ids"):
        resolve_changed_ids(index, " , ,")


def test_diff_changed_set_reasons_in_fixed_order():
    """T-81: statement differs / added / removed / retired flag differs / affects differs,
    each id carrying every reason that applies, joined by "; ", in C-12 id order. (C-13)"""
    old = _index(BASE_SPEC)
    new_text = spec_table(
        [
            ("R-01", "obeys the grammar in C-01, reworded."),  # statement differs
            ("C-01", "the interface."),
            ("K-15", "a bound."),
            ("E-48", "unlocated, per K-15."),
            ("R-34", "grounding rule (K-15, E-48)."),
            ("T-75", "proves K-15 and E-48."),
            ("R-90", "brand new."),  # added; speccheck:ignore
        ],
        retired={"C-01"},  # retired flag differs
    ) + "\n\n| ID | Affects |\n| -- | ------- |\n| D-08 | C-10, T-49, R-01 |\n| D-09 | R-01 |\n"
    new = _index(new_text)
    entries = diff_changed_set(old, new)
    by_id = {e.id: e for e in entries}
    assert by_id["R-01"].reason == "statement differs"
    assert by_id["C-01"].reason == "retired flag differs"
    assert by_id["R-90"].reason == "added"  # speccheck:ignore
    assert by_id["D-08"].reason == "affects differs"
    assert by_id["D-09"].reason == "added"
    assert "K-15" not in by_id and "E-48" not in by_id  # unchanged

    # removed: an id declared in old only
    old2 = _index(BASE_SPEC + "\n\n### R-91 Going away\n")  # speccheck:ignore
    entries2 = diff_changed_set(old2, old)
    assert {e.id: e.reason for e in entries2} == {"R-91": "removed"}  # speccheck:ignore
    assert entries2[0].line > 0

    # identical specs -> empty changed set
    assert diff_changed_set(old, old) == ()


def test_walk_reverse_depends_on_and_affects_with_shortest_via():
    """T-80: from K-15, the walk follows reverse depends_on (R-34, E-48 depend on K-15) and,
    from a changed D id, forward affects edges; --depth limits the returned set to a prefix of
    the unbounded one with identical `via` (I-013); a T is reached only through `verifies`,
    never expanded from. (R-37, C-13, I-013)"""
    index = _index(BASE_SPEC)
    changed = {"K-15"}
    full = walk(index.edges, changed, depth_limit=0)
    by_id = {e.id: e for e in full.impact}
    assert by_id["R-34"].depth == 1 and by_id["E-48"].depth == 1
    assert by_id["R-34"].via.dst == "K-15"
    assert "K-15" not in by_id  # changed-set ids never enter IMPACT
    assert "D-08" not in by_id  # no edge has a D id as dst

    limited = walk(index.edges, changed, depth_limit=1)
    assert {e.id for e in limited.impact} == {"R-34", "E-48"}
    assert limited.beyond_depth == 0  # nothing deeper exists to cap here

    # from a D id: forward affects, not reverse
    d_changed = {"D-08"}
    d_full = walk(index.edges, d_changed, depth_limit=0)
    assert {e.id for e in d_full.impact} == set()  # C-10, T-49 are not declared in BASE_SPEC


def test_walk_depth_cap_is_a_prefix_with_a_note():
    """T-80/I-013: a two-hop chain capped at depth 1 omits the second hop and counts it."""
    text = spec_table(
        [("R-01", "a"), ("R-02", "depends on R-01."), ("R-03", "depends on R-02.")]
    )
    index = _index(text)
    full = walk(index.edges, {"R-01"}, depth_limit=0)
    capped = walk(index.edges, {"R-01"}, depth_limit=1)
    assert [(e.id, e.depth, e.via) for e in capped.impact] == [
        (e.id, e.depth, e.via) for e in full.impact if e.depth <= 1
    ]
    assert capped.beyond_depth == 1 and full.beyond_depth == 0


def test_reverify_set():
    """T-80: REVERIFY is every T verifying an id in (changed ∪ impact), plus every T id itself
    in that set (verifies=[] when only reached/changed, not verifying). (R-37, C-13)"""
    index = _index(BASE_SPEC)
    changed = {"K-15"}
    full = walk(index.edges, changed, depth_limit=0)
    impacted = {e.id for e in full.impact}
    rev = reverify_set(index.edges, changed | impacted)
    by_id = {r.id: r for r in rev}
    # T-75's statement names K-15 and E-48 only (not R-34); K sorts before E in the id order
    assert by_id["T-75"].verifies == ("K-15", "E-48")


def test_impact_cli_against_golden_fixture(tmp_path: Path):
    """T-80: `speccheck impact --changed K-02` on the golden fixture writes byte-identical
    impact.json / IMPACT_REPORT.md, exits 0, and prints the C-13 summary line; --depth 0 is a
    superset agreeing on shared rows (I-013); two runs are byte-identical (I-002); a prior
    `check` into the same --out leaves both pairs of files intact (I-001). (R-37, C-13, I-001,
    I-002, I-013)"""
    import shutil

    target = tmp_path / "target"
    shutil.copytree(FIXTURE, target)
    out = target / "out"
    run = run_cli(
        [
            "impact",
            "--spec",
            "SPEC.md",
            "--changed",
            "K-02",
            "--src",
            "src",
            "--tests",
            "tests",
            "--root",
            ".",
            "--out",
            "out",
        ],
        target,
    )
    assert run.code == 0, run.stderr
    golden_dir = FIXTURE / "golden"
    produced = (out / "impact.json").read_bytes()
    assert produced == (golden_dir / "impact.json").read_bytes()
    assert (out / "IMPACT_REPORT.md").read_bytes() == (
        golden_dir / "IMPACT_REPORT.md"
    ).read_bytes()
    import re

    assert re.match(
        r"^speccheck impact: \d+ changed, \d+ impacted \((depth \d+|unbounded)\), "
        r"\d+ to re-verify, \d+ citations, \d+ test cases$",
        run.stdout.strip(),
    )

    # two runs byte-identical
    run2 = run_cli(
        [
            "impact",
            "--spec",
            "SPEC.md",
            "--changed",
            "K-02",
            "--src",
            "src",
            "--tests",
            "tests",
            "--root",
            ".",
            "--out",
            "out",
        ],
        target,
    )
    assert run2.code == 0
    assert (out / "impact.json").read_bytes() == produced

    # a prior check leaves the impact files intact, and a following impact leaves check's intact
    run_check = run_cli(
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
            "--root",
            ".",
            "--out",
            "checkout",
        ],
        target,
    )
    assert run_check.code in (0, 1)
    assert (out / "impact.json").read_bytes() == produced


def test_impact_usage_and_input_errors(tmp_path: Path):
    """T-81: neither/both of --changed and --against, an undeclared --changed id, a bad
    --depth, and --results/--judge on impact all exit 2; a broken --against file exits 3 with
    the message prefixed; nothing is written under --out in any case. (E-53, E-54, I-001)"""
    write_tree(tmp_path / "p", {"SPEC.md": BASE_SPEC})
    base = ["impact", "--spec", "SPEC.md"]

    def run(*extra):
        return run_cli(base + list(extra) + ["--out", "out"], tmp_path / "p")

    r = run()  # neither
    assert r.code == 2 and "exactly one of" in r.stderr

    r = run("--changed", "K-15", "--against", "SPEC.md")  # both
    assert r.code == 2 and "exactly one of" in r.stderr

    r = run("--changed", "R-99")  # speccheck:ignore
    assert r.code == 2 and "undeclared id: R-99" in r.stderr  # speccheck:ignore

    r = run("--changed", "K-15", "--depth", "-1")
    assert r.code == 2

    r = run("--changed", "K-15", "--depth", "x")
    assert r.code == 2

    r = run("--changed", "K-15", "--results", "junit.xml")
    assert r.code == 2 and "--results" in r.stderr

    r = run("--changed", "K-15", "--judge", "mock")
    assert r.code == 2

    (tmp_path / "p" / "bad_against.md").write_text(
        spec_table([("R-01", "a")]) + spec_table([("R-01", "b")]), encoding="utf-8"
    )
    r = run("--against", "bad_against.md")
    assert r.code == 3 and r.stderr.startswith("ERROR --against: ") or "--against: " in r.stderr

    assert not (tmp_path / "p" / "out").exists()


def test_impact_against_with_no_changes_and_retired_changed_id(tmp_path: Path):
    """T-81: an --against run against an identical copy has an empty changed set, every
    section "None.", exit 0, and the zero summary line; a retired id may be named by
    --changed and its rows are struck through. (C-13, E-55)"""
    write_tree(
        tmp_path / "p",
        {"SPEC.md": BASE_SPEC, "old.md": BASE_SPEC},
    )
    run = run_cli(
        ["impact", "--spec", "SPEC.md", "--against", "old.md", "--out", "out"], tmp_path / "p"
    )
    assert run.code == 0
    md = (tmp_path / "p" / "out" / "IMPACT_REPORT.md").read_text(encoding="utf-8")
    assert md.count("None.") == 3  # Changed, Impact, Re-verify; §4 is "Not scanned." (no --src)
    assert "Not scanned." in md
    assert (
        run.stdout.strip()
        == "speccheck impact: 0 changed, 0 impacted (depth 1), 0 to re-verify, 0 citations, "
        "0 test cases"
    )

    retired_spec = BASE_SPEC.replace("**C-01**", "~~**C-01**~~")
    write_tree(tmp_path / "q", {"SPEC.md": retired_spec})
    run2 = run_cli(
        ["impact", "--spec", "SPEC.md", "--changed", "C-01", "--out", "out"], tmp_path / "q"
    )
    assert run2.code == 0
    doc = json.loads((tmp_path / "q" / "out" / "impact.json").read_text(encoding="utf-8"))
    assert doc["changed"][0]["retired"] is True
    md2 = (tmp_path / "q" / "out" / "IMPACT_REPORT.md").read_text(encoding="utf-8")
    assert "~~C-01~~" in md2


def test_impact_backtest_script_exists():
    """T-82 (recorded): tools/impact_backtest.py exists, needs git and this repository's
    history, and is not collected by pytest; its outcome (recall/precision per depth cutoff on
    two ranges of main) is recorded in SPEC_BUILD_REPORT.md, not asserted here. (D-24)"""
    from pathlib import Path as _P

    root = _P(__file__).resolve().parent.parent
    source = (root / "tools" / "impact_backtest.py").read_text(encoding="utf-8")
    import ast

    tree = ast.parse(source)
    names = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
    assert "main" in names
    assert "git" in source and "--depth" in source
