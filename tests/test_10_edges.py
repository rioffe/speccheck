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
    table = "\n\n| ID | Affects |\n| -- | ------- |\n| D-01 | R-01 |\n| D-01 | R-01 |\n"
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


def _edges(text: str) -> set[tuple[str, str, str]]:
    return {(e.src, e.kind, e.dst) for e in parse_spec(text, "SPEC.md").edges}


@pytest.mark.parametrize(
    "phrase", ["R-01..R-03", "R-01 to R-03", "R-01 through R-03", "R-01–R-03", "R-01..03"]
)
def test_range_names_the_declared_ids_between_its_endpoints(phrase):
    """T-104: a range in a statement names every declared id of the family between its
    endpoints; an undeclared id inside it is silently skipped; a reversed, cross-family or
    over-wide range names only its endpoints. (R-36, C-12)"""
    rows = [("R-01", "a."), ("R-02", "b."), ("R-03", "c."), ("R-04", f"spans {phrase}.")]
    got = {d for s, k, d in _edges(spec_table(rows)) if s == "R-04"}
    assert got == {"R-01", "R-02", "R-03"}, phrase

    without_middle = [r for r in rows if r[0] != "R-02"]
    index = parse_spec(spec_table(without_middle), "SPEC.md")
    assert {e.dst for e in index.edges if e.src == "R-04"} == {"R-01", "R-03"}
    assert not any("R-02" in n for n in index.notes)

    for odd, expected in (("R-03..R-01", {"R-01", "R-03"}), ("R-01..E-03", {"R-01", "E-03"})):
        rows = [("R-01", "a."), ("R-02", "b."), ("R-03", "c."), ("E-03", "d."), ("R-04", odd)]
        assert {d for s, k, d in _edges(spec_table(rows)) if s == "R-04"} == expected, odd
    wide = [("R-01", "a."), ("R-02", "b."), ("R-102", "c."), ("R-04", "spans R-01..R-102.")]
    assert {d for s, k, d in _edges(spec_table(wide)) if s == "R-04"} == {"R-01", "R-102"}


def test_non_statement_cells_feed_edges_but_not_the_statement():
    """T-105: an edge-case row's outcome column is read for edges; `text` and `title` stay the
    statement cell alone. (R-36, C-12)"""
    text = (
        "# S\n\n| ID | Condition | Outcome |\n| -- | --------- | ------- |\n"
        "| **R-02** | base | x |\n| **E-01** | condition | outcome naming R-02 |\n"
    )
    index = parse_spec(text, "SPEC.md")
    assert ("E-01", "depends_on", "R-02") in {(e.src, e.kind, e.dst) for e in index.edges}
    e01 = index.by_id()["E-01"]
    assert e01.text == "condition" and e01.title == "condition"


def test_odd_math_delimiters_note_and_symlink_hint(tmp_path):
    """T-106: a row cut at an unescaped `|` inside `$..$` gets one Note; escaped, backticked and
    balanced rows get none; a symlinked --out that escapes --root names its target. (E-66, E-09)"""

    def notes(cell: str) -> tuple[str, ...]:
        text = f"# S\n\n| ID | Statement | More |\n| -- | -- | -- |\n| **R-05** | {cell} |\n"
        return parse_spec(text, "SPEC.md").notes

    assert notes("value $a | b$ holds") == ("statement may be cut at an unescaped '|': R-05",)
    assert notes(r"value $a \| b$ holds | x") == ()
    assert notes("value `$a | b$` holds | x") == ()
    assert notes("value $a$ and $b$ | x") == ()

    from .conftest import run_cli

    outside = tmp_path / "outside"
    outside.mkdir()
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "SPEC.md").write_text(spec_table([("R-01", "x.")]))
    (proj / "link").symlink_to(outside)
    run = run_cli(["check", "--spec", "SPEC.md", "--out", "link"], proj)
    assert run.code == 2 and run.stderr.startswith("ERROR path outside --root: link")
    assert run.stderr.rstrip().endswith(f"(resolves to {outside.resolve()})")
    plain = run_cli(["check", "--spec", "SPEC.md", "--out", ".."], proj)
    assert plain.stderr == "ERROR path outside --root: ..\n"


def test_t121_isolated_ids_are_named_in_one_note(project):
    """T-121 (v1.24): the declared, non-retired ids that no C-12 edge touches are named in one
    Note, in C-07 order; a retired one is uncounted; naming an id removes it; five list three and
    end ` and 2 more`; the golden fixture carries its three; `impact` emits no such Note.
    (E-77, C-12, R-36, D-60)"""
    import json

    from speccheck.extract import isolated_note

    from .conftest import FIXTURE, run_cli

    rows = [
        ("R-01", "alone"),
        ("R-02", "names E-01"),
        ("C-01", "old"),
        ("E-01", "x"),
        ("E-02", "alone"),
    ]
    spec = spec_table(rows, retired={"C-01"})
    index = parse_spec(spec, "SPEC.md")
    assert index.isolated == ("R-01", "E-02")
    assert isolated_note(index) == "2 declared id(s) touch no edge: R-01, E-02"
    named = parse_spec(spec_table(rows + [("K-01", "bounds R-01")], retired={"C-01"}), "SPEC.md")
    assert named.isolated == ("E-02",)
    five = parse_spec(spec_table([("R-" + f"0{n}", "alone") for n in range(1, 6)]), "SPEC.md")
    assert isolated_note(five) == "5 declared id(s) touch no edge: R-01, R-02, R-03 and 2 more"
    assert (
        isolated_note(parse_spec(spec_table([("R-01", "names R-02"), ("R-02", "x")]), "S")) is None
    )
    golden = json.loads((FIXTURE / "golden" / "speccheck.json").read_text(encoding="utf-8"))
    assert "3 declared id(s) touch no edge: R-03, K-01, E-01" in golden["notes"]
    proj = project({"SPEC.md": spec, "src/x.py": "", "tests/t.py": ""})
    assert "2 declared id(s) touch no edge: R-01, E-02" in proj.check().json["notes"]
    imp = run_cli(["impact", "--spec", "SPEC.md", "--changed", "R-02", "--out", "imp"], proj.path)
    assert imp.code == 0
    notes = json.loads((proj.path / "imp" / "impact.json").read_text())["notes"]
    assert not any("touch no edge" in n for n in notes)
