"""§9.12 Edges and decisions (C-12; v1.13)."""

from __future__ import annotations

import pytest

from speccheck.extract import SpecError, edge_id_key, parse_spec

from .conftest import spec_table


def _spec_with_decisions(extra_decisions: str = "") -> str:
    base = spec_table(
        [
            ("R-01", "obeys the grammar in C-01."),
            ("C-01", "the interface."),
            ("T-01", "proves R-01."),
            ("T-02", "proves T-01 too."),
        ],
        retired={"C-01"},
    )
    table = (
        "\n\n## 12. Decisions\n\n"
        "| ID | Decision | Default | Alternatives | Affects | Owner |\n"
        "| -- | -------- | ------- | ------------- | ------- | ----- |\n"
        "| D-01 | first | x | y | R-01, C-01 | me |\n"
        "| D-02 | second | x | y | R-99 | me |\n"  # speccheck:ignore
    )
    return base + table + extra_decisions


def test_statement_tokens_yield_depends_on_and_verifies_edges():
    """T-79: an obligation naming another obligation is `depends_on`; an obligation naming a T
    id (or a T naming an obligation) is one `verifies` edge with the T as src, emitted once even
    when both sides name each other; a T naming a T is `depends_on`; a self-reference and a
    repeated token add nothing; an edge to an undeclared id is a Note, not an edge. (R-36, C-12)"""
    index = parse_spec(_spec_with_decisions(), "SPEC.md")
    edges = {(e.src, e.kind, e.dst) for e in index.edges}
    assert ("R-01", "depends_on", "C-01") in edges
    assert ("T-01", "verifies", "R-01") in edges
    assert ("T-02", "depends_on", "T-01") in edges
    assert sum(1 for e in index.edges if e.kind == "verifies" and e.dst == "R-01") == 1
    assert "edge to undeclared id: D-02 -> R-99" in index.notes  # speccheck:ignore


def test_verifies_direction_normalized_regardless_of_which_side_is_named_first():
    """T-79: T-01 naming R-01 and R-01 naming T-01 (mutual reference) produce exactly one
    `verifies` edge, T-01 as src. (R-36, C-12)"""
    text = spec_table(
        [("R-01", "proved by T-01."), ("T-01", "proves R-01.")],
    )
    index = parse_spec(text, "SPEC.md")
    verifies = [(e.src, e.kind, e.dst) for e in index.edges if e.kind == "verifies"]
    assert verifies == [("T-01", "verifies", "R-01")]


def test_edge_to_retired_id_is_flagged_and_self_reference_is_ignored():
    """T-79: an edge whose target is RETIRED is recorded with retired=True; R-01 naming itself
    (repeated) adds no edge. (E-55, C-12)"""
    text = spec_table(
        [("R-01", "see R-01 and C-01."), ("C-01", "the interface.")],
        retired={"C-01"},
    )
    index = parse_spec(text, "SPEC.md")
    edges = [(e.src, e.kind, e.dst, e.retired) for e in index.edges]
    assert edges == [("R-01", "depends_on", "C-01", True)]


def test_edges_are_sorted_affects_before_depends_on_before_verifies():
    """T-79: edges sorted by (id_key(src), kind, id_key(dst)); "affects" < "depends_on" <
    "verifies". (C-12)"""
    index = parse_spec(_spec_with_decisions(), "SPEC.md")
    keys = [(e.src, e.kind, e.dst) for e in index.edges]
    expected = sorted(keys, key=lambda k: (edge_id_key(k[0]), k[1], edge_id_key(k[2])))
    assert keys == expected


def test_decision_table_found_by_affects_header_cell_case_insensitively():
    """T-79: the decision table is the first table whose header has a cell "affects" (trimmed,
    case-folded); D-01's Affects cell names R-01 and the retired C-01 (both declared, so both
    are in `affects` and each yields an edge); D-02's Affects cell names the undeclared R-99 (a  # speccheck:ignore
    Note, not an edge, and not in `affects`). (R-36, C-01 (c), C-02)"""
    index = parse_spec(_spec_with_decisions(), "SPEC.md")
    decisions = {d.id: d for d in index.decisions}
    assert decisions["D-01"].affects == ("R-01", "C-01")  # C-12 id order: R before C
    assert decisions["D-02"].affects == ()
    assert {(e.src, e.kind, e.dst) for e in index.edges if e.src == "D-01"} == {
        ("D-01", "affects", "R-01"),
        ("D-01", "affects", "C-01"),
    }


def test_decision_row_outside_the_table_and_bold_decoration_declare_nothing():
    """T-79: a `D-nn` row outside the decision table, and a bold `**D-09**` row inside it,
    declare nothing. (C-01 (c))"""
    extra = "\n\nSome other table:\n\n| D-03 | x |\n| - | - |\n"
    text = _spec_with_decisions(extra) + "\n| **D-09** | bold | x | y | R-01 | me |\n"
    index = parse_spec(text, "SPEC.md")
    assert {d.id for d in index.decisions} == {"D-01", "D-02"}


def test_second_affects_table_is_not_the_decision_table():
    """T-79: only the first table whose header has an "affects" cell is the decision table; a
    D-nn row in a second such table declares nothing. (C-01 (c))"""
    text = _spec_with_decisions(
        "\n\n## Another table\n\n| ID | Affects |\n| -- | ------- |\n| D-03 | R-01 |\n"
    )
    index = parse_spec(text, "SPEC.md")
    assert {d.id for d in index.decisions} == {"D-01", "D-02"}


def test_duplicate_decision_declaration_exits_3_naming_both_lines():
    """T-79: a second D-01 row in the decision table exits 3 naming both lines. (E-02)"""
    base = spec_table([("R-01", "x")])
    table = (
        "\n\n| ID | Affects |\n| -- | ------- |\n| D-01 | R-01 |\n| D-01 | R-01 |\n"
    )
    with pytest.raises(SpecError, match="D-01"):
        parse_spec(base + table, "SPEC.md")


def test_decision_numbers_are_normalized_and_no_decision_table_yields_empty():
    """T-79: `D-8` normalizes to `D-08` (I-011); a spec with no decision table has
    `decisions == ()` and `edges == ()`."""
    text = spec_table([("R-01", "x")]) + "\n\n| ID | Affects |\n| -- | ------- |\n| D-8 | R-01 |\n"
    index = parse_spec(text, "SPEC.md")
    assert [d.id for d in index.decisions] == ["D-08"]

    plain = spec_table([("R-01", "x")])
    index2 = parse_spec(plain, "SPEC.md")
    assert index2.decisions == ()
    assert index2.edges == ()
