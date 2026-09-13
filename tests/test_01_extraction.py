"""§9.1 Extraction (C-01, C-02)."""

from __future__ import annotations

import pytest

from speccheck.extract import ID_RE, SpecError, normalize_id, parse_spec, split_row, tokens_in_line

from .conftest import spec_table


def test_table_and_heading_declarations_and_utf8_replacement(project):
    """T-01: table-cell and heading declarations are both extracted with correct family, number,
    statement, and line; an invalid-UTF-8 SPEC.md is decoded with replacement, its ASCII
    declarations are still found, and a Note is recorded. (R-01, E-11)"""
    text = "# Spec\n\n| ID | Statement |\n| -- | -- |\n| **R-01** |  adds   two  numbers |\n\n### C-02 divides safely\n"
    index = parse_spec(text, "SPEC.md")
    assert [(s.id, s.family, s.number, s.text, s.line) for s in index.ids] == [
        ("R-01", "R", 1, "adds two numbers", 5),
        ("C-02", "C", 2, "divides safely", 7),
    ]
    bad = text.encode("utf-8") + b"\n| **K-03** | caf\xe9 |\n"
    proj = project({"SPEC.md": bad})
    run = proj.check()
    assert run.code in (0, 1)
    assert {"R-01", "C-02", "K-03"} <= set(run.ids())
    assert "invalid UTF-8 decoded with replacement: SPEC.md" in run.json["notes"]


def test_numbers_normalize_within_family():
    """T-02: R-7, R-07, R-007 are one ID reported as R-07; I-5 is reported as I-005. (I-011, K-04)"""
    assert normalize_id("R", 7) == "R-07"
    assert normalize_id("I", 5) == "I-005"
    assert [t[0] for t in tokens_in_line("R-7 R-07 R-007 I-5")] == ["R-07", "R-07", "R-07", "I-005"]
    with pytest.raises(SpecError, match="R-07"):
        parse_spec(spec_table([("R-7", "a"), ("R-007", "b")]), "SPEC.md")
    index = parse_spec(spec_table([("R-7", "a"), ("I-5", "b")]), "SPEC.md")
    assert [s.id for s in index.ids] == ["R-07", "I-005"]
    assert normalize_id("R", 7) != normalize_id("C", 7)


def test_four_digits_and_adjacent_alphanumerics_are_not_ids():
    """T-03: R-1234, XR-07 and R-07a are not IDs. (K-04, C-01)"""
    assert ID_RE.findall("R-1234 XR-07 R-07a 7R-07 R-070x") == []
    assert [t[0] for t in tokens_in_line("(R-07) R-07, R-07. R-07/ _R-07")] == ["R-07"] * 4 + [
        "R-07"
    ]
    assert [t[0] for t in tokens_in_line("see R-1234 and R-29")] == ["R-29"]


def test_strikethrough_is_retired_and_mixed_redeclaration_exits_3(project):
    """T-04: strikethrough declarations yield retired=True in all three forms; a later plain
    declaration of the same ID exits 3. (R-02, E-03)"""
    text = (
        spec_table([("R-01", "kept")])
        + "| ~~**R-02**~~ | a |\n| **~~R-03~~** | b |\n\n### ~~C-01~~ gone\n"
    )
    index = parse_spec(text, "SPEC.md")
    assert {s.id: s.retired for s in index.ids} == {
        "R-01": False,
        "R-02": True,
        "R-03": True,
        "C-01": True,
    }
    proj = project({"SPEC.md": text + "| **R-02** | again |\n"})
    run = proj.check()
    assert run.code == 3
    assert "R-02" in run.stderr and "6" in run.stderr and "10" in run.stderr
    assert not (proj.path / "speccheck.json").exists()
    proj2 = project(
        {
            "SPEC.md": spec_table([("R-01", "kept")])
            + "| **R-02** | first |\n| ~~**R-02**~~ | later |\n"
        }
    )
    assert proj2.check().code == 3


def test_fenced_code_blocks_are_ignored():
    """T-05: IDs inside fences are ignored for ``` and ~~~ fences, with and without info strings,
    for an unclosed fence, and with the Q-008 closing rules. (E-04, C-01)"""
    text = "\n".join(
        [
            "| **R-01** | real |",
            "```",
            "| **R-02** | fenced |",
            "```",
            "~~~",
            "| **R-03** | fenced |",
            "~~~",
            "```python",
            "| **R-04** | fenced |",
            "~~~",  # a tilde line does not close a backtick fence
            "| **R-05** | still fenced |",
            "```text",  # a closing line with an info string does not close
            "| **R-06** | still fenced |",
            "```",  # bare backtick line closes
            "| **R-07** | real |",
            "~~~info",
            "| **R-08** | fenced |",
            "```",  # backticks never close a tilde fence
            "| **R-09** | still fenced |",
            "~~~",
            "| **R-10** | real |",
            "```",
            "| **R-11** | unclosed to end of file |",
        ]
    )
    index = parse_spec(text, "SPEC.md")
    assert [s.id for s in index.ids] == ["R-01", "R-07", "R-10"]
    indented = "   ```\n| **R-01** | fenced |\n   ```\n| **R-02** | real |\n"
    assert [s.id for s in parse_spec(indented, "SPEC.md").ids] == ["R-02"]


def test_duplicate_declaration_exits_3_naming_both_lines(project):
    """T-06: a duplicate declaration exits 3 and the message names both lines. (E-02)"""
    text = spec_table([("R-01", "one"), ("C-01", "x"), ("R-01", "two")])
    with pytest.raises(SpecError) as excinfo:
        parse_spec(text, "SPEC.md")
    assert "R-01" in str(excinfo.value) and "5" in str(excinfo.value) and "7" in str(excinfo.value)
    run = project({"SPEC.md": text}).check()
    assert run.code == 3
    assert "R-01" in run.stderr and "lines 5 and 7" in run.stderr
    assert run.stdout == ""


def test_row_and_heading_grammar_edge_cases():
    """T-55: a bold ID in a second cell, a heading with the ID after other tokens, a separator
    row, and a row with `\\|` and a backtick-quoted pipe are parsed per C-01: only first-cell /
    first-token forms declare; the statement is the second cell with escapes intact. (E-31, C-01)"""
    text = "\n".join(
        [
            "| ID | Statement |",
            "| -- | :-------: |",
            "| see | **R-01** in a second cell |",
            "### 9.1 Extraction (C-01, C-02)",
            "## C-03 first token declares",
            "| **R-02** | a \\| pipe and a `x | y` span | third |",
            "| **R-03** |",
            "| **R-04** **R-05** | two tokens is not a declaration |",
            "|**R-06**|tight cells|",
            "| R-07 | not bold |",
        ]
    )
    index = parse_spec(text, "SPEC.md")
    assert {s.id: s.text for s in index.ids} == {
        "C-03": "first token declares",
        "R-02": "a \\| pipe and a `x | y` span",
        "R-03": "",
        "R-06": "tight cells",
    }
    assert split_row("| a \\| b | `c | d` | e |") == [" a \\| b ", " `c | d` ", " e "]


def test_no_in_scope_ids_exits_3_and_writes_nothing(project):
    """T-07: a spec with no in-scope IDs exits 3 and writes no files. (E-01, I-001)"""
    for text in ("# nothing here\n", spec_table([("R-01", "gone")], retired={"R-01"})):
        proj = project({"SPEC.md": text, "src/a.py": "# R-01\n"})
        before = sorted(p.name for p in proj.path.iterdir())
        run = proj.check()
        assert run.code == 3
        assert "spec declares no in-scope IDs" in run.stderr
        assert run.stdout == ""
        assert sorted(p.name for p in proj.path.iterdir()) == before
