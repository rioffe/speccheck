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
            "| **R-10** | real |",  # speccheck:ignore
            "```",
            "| **R-11** | unclosed to end of file |",
        ]
    )
    index = parse_spec(text, "SPEC.md")
    assert [s.id for s in index.ids] == ["R-01", "R-07", "R-10"]  # speccheck:ignore
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
            "| **R-04** **R-05** | a second bold token is decoration (E-44) |",
            "|**R-06**|tight cells|",
            "| R-07 | not bold |",
        ]
    )
    index = parse_spec(text, "SPEC.md")
    assert {s.id: s.title for s in index.ids} == {
        "C-03": "first token declares",
        "R-02": "a \\| pipe and a `x | y` span",
        "R-03": "",
        "R-04": "a second bold token is decoration (E-44)",
        "R-06": "tight cells",
    }
    # v1.8: a table-declared ID's text is its title; the heading's text carries the rows beneath
    # it as its section body while those rows still declare their own IDs (E-47, R-33)
    assert all(s.text == s.title for s in index.ids if s.id != "C-03")
    assert index.by_id()["C-03"].text.startswith("first token declares\n| **R-02** |")
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


def test_first_cell_decoration_after_bold_id():
    """T-70: `| **K-07** **[port]** |` declares K-07 with the second cell as statement;
    `| **R-01** **R-02** |` declares R-01 only; `**K-07**x` and `**K-07**, note` declare
    nothing; retired forms tolerate decoration the same way; headings are unchanged.
    (R-32, C-01, E-44)"""
    text = "\n".join(
        [
            "| ID | Statement |",
            "| -- | --------- |",
            "| **K-07** **[port]** | history bound |",
            "| **R-01** **R-02** | first token only |",
            "| **K-08**x | glued suffix |",
            "| **K-09**, note | comma suffix |",
            "| ~~**E-09**~~ *(retired)* | retired with decoration |",
            "| **~~E-10~~** [port] | retired inner form with decoration |",
            "| **T-01**\t| tab after the form |",
            "### C-03 **[port]** contract heading",
        ]
    )
    index = parse_spec(text, "SPEC.md")
    assert {s.id: (s.text, s.retired) for s in index.ids} == {
        "K-07": ("history bound", False),
        "R-01": ("first token only", False),
        "E-09": ("retired with decoration", True),
        "E-10": ("retired inner form with decoration", True),
        "T-01": ("tab after the form", False),
        "C-03": ("**[port]** contract heading", False),
    }


_T72_SPEC = "\n".join(
    [
        "# Spec",
        "",
        "### C-01 Widget",
        "",
        "```python",
        "| **R-99** | x |",  # speccheck:ignore
        "# comment inside a fence is not a heading",
        "    def pinned(self) -> int: ...",
        "```",
        "",
        "Prose clause with trailing spaces.  ",
        "",
        "#### note",
        "",
        "| ID | Statement |",
        "| -- | --------- |",
        "| **E-09** | inner declaration |",
        "",
        "---",
        "",
        "### C-02 Two",
        "",
        "### C-03",
        "body without a title",
        "### C-04 Empty",
        "",
        "   ",
        "### C-05 Title ###",
        "    ### R-98 indented four spaces: not a heading, not a declaration",  # speccheck:ignore
        "###",
        "###C-06 x",
        "## Section",
        "### C-07 Last",
    ]
)


def test_heading_section_bodies_title_cap_and_line_model():
    """T-72: a heading-declared ID's statement is its title plus its section body — every line
    down to the next heading of the same or a higher level, fenced blocks (and the `#` lines
    inside them), deeper headings, tables and `---` included, indentation and trailing spaces
    intact; `title` is the heading text alone; inner declarations still declare (E-47); an
    empty body gives `text == title` and an empty title gives the body alone (E-46); the K-14 cap
    truncates at a line boundary with the marker line and one Note; CRLF parses as LF; a
    whitespace-only line at the body's edge is dropped and one inside is kept; four-space
    indentation, a bare `###`, closing hashes and `###C-06` follow C-01's HEADING LINE rule;
    and for both fixture specs `title` equals the independently computed cell / heading
    remainder. (R-33, C-01, C-02, K-14, E-46, E-47)"""
    from pathlib import Path

    from speccheck.extract import STATEMENT_CAP_BYTES, TRUNCATION_MARKER

    index = parse_spec(_T72_SPEC, "SPEC.md")
    ids = index.by_id()
    assert set(ids) == {"C-01", "C-02", "C-03", "C-04", "C-05", "C-07", "E-09"}
    body = "\n".join(_T72_SPEC.split("\n")[4:19])  # the fence through the `---`
    assert body.startswith("```python") and body.endswith("---")
    assert ids["C-01"].title == "Widget"
    assert ids["C-01"].text == "Widget\n" + body
    assert "trailing spaces.  \n" in ids["C-01"].text  # whitespace inside preserved
    assert "    def pinned" in ids["C-01"].text  # indentation preserved
    assert ids["E-09"].text == ids["E-09"].title == "inner declaration"
    assert ids["C-02"].text == ids["C-02"].title == "Two"
    assert ids["C-03"].title == "" and ids["C-03"].text == "body without a title"
    assert ids["C-04"].text == ids["C-04"].title == "Empty"  # trailing blank lines dropped
    assert ids["C-05"].title == "Title"
    assert (
        ids["C-05"].text
        == "Title\n    ### R-98 indented four spaces: not a heading, not a declaration"  # speccheck:ignore
    )
    assert ids["C-07"].text == ids["C-07"].title == "Last"
    # v1.13/C-12: the example ids inside C-01's pinned fence and C-05's body are undeclared,
    # so each yields an "edge to undeclared id" Note, not a declaration and not an edge.
    assert index.notes == (
        "edge to undeclared id: C-01 -> R-99",
        "edge to undeclared id: C-05 -> R-98",
    )

    # CRLF twin -> identical index (C-01 Lines rule, I-002)
    assert parse_spec(_T72_SPEC.replace("\n", "\r\n"), "SPEC.md") == index

    # whitespace-only line: dropped at the edge, kept inside
    edge = parse_spec("### C-01 T\nline one\n   \n\n### C-02 U\n", "SPEC.md").by_id()
    assert edge["C-01"].text == "T\nline one"
    inside = parse_spec("### C-01 T\nline one\n   \nline two\n### C-02 U\n", "SPEC.md").by_id()
    assert inside["C-01"].text == "T\nline one\n   \nline two"

    # K-14: cap at a line boundary in UTF-8 bytes, marker appended, one Note
    long_line = "café " * 40  # non-ASCII so bytes != characters
    big = "### C-01 Big\n" + "\n".join(long_line for _ in range(120)) + "\n### C-02 Two\n"
    capped = parse_spec(big, "SPEC.md")
    text = capped.by_id()["C-01"].text
    assert text.endswith("\n" + TRUNCATION_MARKER)
    kept = text[: -len("\n" + TRUNCATION_MARKER)]
    assert len(kept.encode("utf-8")) <= STATEMENT_CAP_BYTES == 16_384
    assert kept.split("\n")[-1] == long_line  # whole lines only
    assert len((kept + "\n" + long_line).encode("utf-8")) > STATEMENT_CAP_BYTES
    # v1.13/C-12: the truncation marker itself contains the literal text "K-14"; scanning
    # SpecId.text (the already-capped statement, marker included, per C-12) for edges finds it
    # as an undeclared token like any other.
    assert capped.notes == (
        "edge to undeclared id: C-01 -> K-14",
        "statement truncated at K-14: C-01",
    )
    assert capped.by_id()["C-01"].title == "Big"

    # property over both fixture specs: title is the cell / remainder, text agrees with it
    import re

    for spec in ("fixtures/target/SPEC.md", "fixtures/target-swift/SPEC.md"):
        raw = Path(__file__).resolve().parent.parent.joinpath(spec).read_text(encoding="utf-8")
        got = parse_spec(raw, spec).by_id()
        for line in raw.split("\n"):
            m = re.match(
                r"^\| (?:\*\*|~~\*\*|\*\*~~)([RCIKET]-\d+)(?:\*\*|\*\*~~|~~\*\*)\s*\|([^|]*)\|",
                line,
            )
            if m:
                sid = got[normalize_id(m.group(1)[0], int(m.group(1)[2:]))]
                assert sid.title == " ".join(m.group(2).split())
                assert sid.text == sid.title  # table-declared
                continue
            m = re.match(r"^### (?:~~)?([RCIKET]-\d+)(?:~~)?\s*(.*)$", line)
            if m:
                sid = got[normalize_id(m.group(1)[0], int(m.group(1)[2:]))]
                assert sid.title == " ".join(m.group(2).split())
                assert sid.text == sid.title or sid.text.startswith(sid.title + "\n")


def test_recorded_marker_declarations():
    """T-77 (extraction half): `| **T-01** *(recorded)* | s |` declares T-01 recorded with
    title `s`; `### T-02 *(recorded)* Title` declares T-02 recorded with title `Title`;
    `*(Recorded)*`, `(recorded)` and a marker after other decoration declare their ids not
    recorded; the marker on a non-T id declares it not recorded with the E-50 Note; a retired
    row may be recorded. (R-35, C-01, C-02, E-50)"""
    text = "\n".join(
        [
            "| ID | Test |",
            "| -- | ---- |",
            "| **T-01** *(recorded)* | s |",
            "| **T-03** *(Recorded)* | wrong case |",
            "| **T-04** (recorded) | not the marker |",
            "| **T-05** **[port]** *(recorded)* | marker not first |",
            "| ~~**T-06**~~ *(recorded)* | retired and recorded |",
            "| **R-01** *(recorded)* | a requirement |",
            "",
            "### T-02 *(recorded)* Title",
            "",
            "body line",
            "",
            "### T-07 Title *(recorded)*",
        ]
    )
    index = parse_spec(text, "SPEC.md")
    ids = index.by_id()
    assert {i: s.recorded for i, s in ids.items()} == {
        "T-01": True,
        "T-02": True,
        "T-03": False,
        "T-04": False,
        "T-05": False,
        "T-06": True,
        "T-07": False,
        "R-01": False,
    }
    assert ids["T-01"].title == ids["T-01"].text == "s"
    assert ids["T-02"].title == "Title" and ids["T-02"].text == "Title\nbody line"
    assert ids["T-06"].retired is True
    assert ids["T-07"].title == "Title *(recorded)*"
    assert index.notes == ("recorded marker ignored on R-01: not a T id",)
