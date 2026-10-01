"""Extractor: SPEC.md -> SpecIndex (C-01, C-02) and file trees -> text files / citations (C-03).

Everything here is deterministic and pattern-based (R-01..R-04, R-27); no semantic analysis.

Spec IDs realized here (§11): R-01, R-02, R-03, R-16, R-20, R-27, R-33, C-01, C-02, C-03, I-002,
    R-35, I-011, K-02, K-03, K-04, K-08, K-14, E-01, E-02, E-03, E-04, E-10, E-11, E-20, E-23,
    E-29, E-30, E-31, E-33, E-34, E-46, E-47, E-50, E-52, I-012.
"""

from __future__ import annotations

import os
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

# C-01 TOKEN regex; K-04 (1-3 digits, alphanumeric-bounded); R-44 (v1.19): a token immediately
# preceded by an uppercase-alphanumeric character and a hyphen is no token at all, so `IR-C-001`
# never yields a `C-001` citation in either dialect.
ID_RE = re.compile(r"(?<![A-Z0-9]-)(?<![A-Za-z0-9])([RCIKET])-([0-9]{1,3})(?![A-Za-z0-9])")

# C-20 TERSE-ID (v1.19): PREFIX "-" FAMILY "-" DIGITS, bounds per K-17, boundary per R-44.
TERSE_ID_RE = re.compile(
    r"(?<![A-Z0-9]-)(?<![A-Za-z0-9])"
    r"([A-Z][A-Z0-9]{0,3})-([A-Z]{1,2})-([0-9]{1,3})"
    r"(?![A-Za-z0-9])"
)

DIALECTS = ("house", "terse")  # C-21 (v1.19); "auto" is CLI-only and resolves before parsing

FAMILY_ORDER = "RCIKET"
FAMILIES = frozenset(FAMILY_ORDER)
EDGE_FAMILY_ORDER = FAMILY_ORDER + "D"  # C-12 sort order: decisions (D) sort last

MAX_FILE_BYTES = 2 * 1024 * 1024  # K-02
BINARY_PROBE_BYTES = 8192  # K-02 / E-29
SKIP_DIR_NAMES = frozenset({".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv", "venv"})

IGNORE_LINE = "speccheck:ignore"  # C-01 / E-33
IGNORE_FILE = "speccheck:ignore-file"

STATEMENT_CAP_BYTES = 16_384  # K-14: a statement is at most this many bytes of UTF-8
TRUNCATION_MARKER = "\u2026 (statement truncated by speccheck at K-14)"  # K-14 marker line
RECORDED_MARKER = (
    "*(recorded)*"  # C-01 / R-35: the first token after the ID form marks a recorded T id
)


class SpecError(Exception):
    """An input-contract violation in SPEC.md (E-01, E-02, E-03) -> exit 3."""


class DialectError(Exception):
    """A C-21/C-20 dialect-selection violation (E-62, E-64) -> exit 2."""


def normalize_id(family: str, number: int) -> str:
    """C-01 normalized form; I-011 (injective within a family)."""
    width = 3 if family == "I" else 2
    return f"{family}-{number:0{width}d}"


def normalize_terse_id(prefix: str, family: str, number: int) -> str:
    """C-20 normalized form: digits zero-padded to three, as the house of record (`ir-control`)
    writes them, so `IR-RX-1` and `IR-RX-001` are one id."""
    return f"{prefix}-{family}-{number:03d}"


def family_rank(family: str) -> int:
    return FAMILY_ORDER.index(family)


def id_sort_key(ident: str) -> tuple[str, int, int]:
    """House: FAMILY_ORDER rank then number. Terse (C-20): lexicographic family then number.
    The two never co-occur in one run (C-21)."""
    parts = ident.split("-")
    if len(parts) == 3:
        return (parts[1], 0, int(parts[2]))
    return ("", family_rank(parts[0]), int(parts[1]))


def edge_id_key(ident: str) -> tuple[int, str, int, int]:
    """C-12 order: like id_sort_key, but the family alphabet includes "D" (decisions), which
    sorts last in both dialects."""
    parts = ident.split("-")
    if len(parts) == 3:
        return (0, parts[1], 0, int(parts[2]))
    family, num = parts
    if family == "D":
        return (1, "", 0, int(num))
    return (0, "", family_rank(family), int(num))


def spec_sort_key(spec: SpecId) -> tuple[str, int, int]:
    if spec.prefix:
        return (spec.family, 0, spec.number)
    return ("", family_rank(spec.family), spec.number)


def is_test_family(spec: SpecId) -> bool:
    """C-05/R-25 family-T semantics apply to house T ids only; no terse family receives them
    (R-43, D-45)."""
    return spec.family == "T" and not spec.prefix


def tokens_in_line(line: str, dialect: str = "house") -> list[tuple[str, str, int]]:
    """Every ID token on a line as (normalized_id, family, number), per the run's dialect
    (R-43: terse citation is full-token only)."""
    if dialect == "terse":
        return [
            (normalize_terse_id(m[1], m[2], int(m[3])), m[2], int(m[3]))
            for m in TERSE_ID_RE.finditer(line)
        ]
    return [
        (normalize_id(m.group(1), int(m.group(2))), m.group(1), int(m.group(2)))
        for m in ID_RE.finditer(line)
    ]


# --------------------------------------------------------------------------------------------
# C-02
# --------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class SpecId:
    family: str
    number: int
    title: str  # C-02: table cell / heading remainder, whitespace-collapsed (what C-08 renders)
    text: str  # C-02: the statement; == title for a row, title + "\n" + SECTION BODY for a heading
    line: int
    retired: bool
    recorded: bool = False  # C-01 RECORDED marker (R-35); only ever True for house family T
    prefix: str = ""  # C-20 (v1.19): the terse PREFIX; "" for a house id

    @property
    def id(self) -> str:
        if self.prefix:
            return normalize_terse_id(self.prefix, self.family, self.number)
        return normalize_id(self.family, self.number)


@dataclass(frozen=True)
class Decision:
    """C-01 (c) / v1.13: a decision-table row. Never a SpecId; never in `ids`; never a citation
    target (the TOKEN regex does not match "D-"); never in any metric (D-25)."""

    id: str  # normalized "D-nn"
    line: int
    affects: tuple[str, ...]  # DECLARED ids named in the AFFECTS CELL, normalized, unique, sorted


@dataclass(frozen=True)
class Edge:
    """C-12 / v1.13: a spec-internal edge. Not a citation, not a status or metric input — it
    records only that `src`'s statement (or Affects cell) names `dst`."""

    src: str  # normalized id: a D id for "affects", the T id for "verifies"
    kind: str  # "affects" | "depends_on" | "verifies"
    dst: str  # normalized; always a declared R/C/I/K/E/T id
    retired: bool  # dst is RETIRED (E-55)


@dataclass(frozen=True)
class SpecIndex:
    path: str
    ids: tuple[SpecId, ...]
    notes: tuple[str, ...] = ()  # K-14 / E-46: one Note per truncated statement
    decisions: tuple[Decision, ...] = ()  # C-01 (c) / v1.13, sorted by number
    edges: tuple[Edge, ...] = ()  # C-12 / v1.13, sorted per the C-12 order

    def by_id(self) -> dict[str, SpecId]:
        return {s.id: s for s in self.ids}


# --------------------------------------------------------------------------------------------
# C-01 declaration grammar
# --------------------------------------------------------------------------------------------

_WS_RE = re.compile(r"\s+")
# C-01 (a): the bold form must BEGIN the trimmed first cell; whatever follows is decoration and
# must be empty or start with whitespace (R-32, E-44: `**K-07** **[port]**` declares K-07,
# `**K-07**x` declares nothing).
_FIRST_CELL_RE = re.compile(
    r"^(?:\*\*(?P<a>[RCIKET]-[0-9]{1,3})\*\*"
    r"|~~\*\*(?P<b>[RCIKET]-[0-9]{1,3})\*\*~~"
    r"|\*\*~~(?P<c>[RCIKET]-[0-9]{1,3})~~\*\*)(?:$|\s)"
)
# C-01 (b) HEADING LINE: at most three leading spaces, one to six "#", then whitespace or end of
# line (ATX only; F-304). A declaring heading is a HEADING LINE whose first token is the ID.
_HEADING_LINE_RE = re.compile(r"^ {0,3}(?P<hashes>#{1,6})(?:\s|$)")
_HEADING_RE = re.compile(
    r"^ {0,3}#{1,6}\s+(?P<tok>~~[RCIKET]-[0-9]{1,3}~~|[RCIKET]-[0-9]{1,3})"
    r"(?![A-Za-z0-9])(?P<rest>.*)$"
)
_CLOSING_HASHES_RE = re.compile(r"(?:^|\s)#+\s*$")  # C-01 (b): "### C-03 Title ###" -> "Title"
_SEPARATOR_CELL_RE = re.compile(r"^[-:\s]+$")


def collapse_ws(text: str) -> str:
    return _WS_RE.sub(" ", text).strip()


def split_row(line: str) -> list[str]:
    """Split a table row on every '|' not preceded by '\\' and not inside a backtick span;
    drop the leading and trailing empty cells (C-01 (a))."""
    cells: list[str] = []
    buf: list[str] = []
    in_span = False
    prev = ""
    for ch in line:
        if ch == "`":
            in_span = not in_span
            buf.append(ch)
        elif ch == "|" and not in_span and prev != "\\":
            cells.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
        prev = ch
    cells.append("".join(buf))
    if cells and cells[0].strip() == "":
        cells = cells[1:]
    if cells and cells[-1].strip() == "":
        cells = cells[:-1]
    return cells


def _fence_marker(line: str) -> str | None:
    s = line.lstrip()
    if s.startswith("```"):
        return "```"
    if s.startswith("~~~"):
        return "~~~"
    return None


def split_spec_lines(text: str) -> list[str]:
    """C-01 Lines rule (F-301): split on "\n"; a trailing "\r" is removed from every line, so a
    CRLF spec parses as its LF twin (I-002)."""
    return [ln[:-1] if ln.endswith("\r") else ln for ln in text.split("\n")]


def is_blank(line: str) -> bool:
    """C-01 BLANK: empty, or spaces and tabs only."""
    return line.strip(" \t") == ""


def heading_level(line: str) -> int | None:
    """C-01 (b) HEADING LINE -> its LEVEL, else None. Fence state is the caller's concern."""
    m = _HEADING_LINE_RE.match(line)
    return len(m.group("hashes")) if m else None


def _heading_lines(lines: list[str]) -> list[tuple[int, int]]:
    """(0-based index, LEVEL) of every HEADING LINE outside fenced code blocks."""
    out: list[tuple[int, int]] = []
    fence: str | None = None
    for i, line in enumerate(lines):
        marker = _fence_marker(line)
        if fence is not None:
            if marker == fence and line.strip() == fence:
                fence = None
            continue
        if marker is not None:
            fence = marker
            continue
        level = heading_level(line)
        if level is not None:
            out.append((i, level))
    return out


def section_body(lines: list[str], start: int, level: int, headings: list[tuple[int, int]]) -> str:
    """C-01 (b) SECTION BODY: the lines after HEADING LINE `start` up to the next HEADING LINE of
    LEVEL <= `level` (or end of file), leading/trailing BLANK lines dropped, joined with "\n",
    everything else preserved (fenced blocks, deeper headings, tables, `---`; E-47)."""
    end = len(lines)
    for i, lvl in headings:
        if i > start and lvl <= level:
            end = i
            break
    body = lines[start + 1 : end]
    while body and is_blank(body[0]):
        body = body[1:]
    while body and is_blank(body[-1]):
        body = body[:-1]
    return "\n".join(body)


def cap_statement(statement: str) -> tuple[str, bool]:
    """K-14: keep the longest prefix of whole lines (the first line always) whose UTF-8 length,
    joined by "\n", is <= STATEMENT_CAP_BYTES; when anything was cut, append the marker line,
    which does not count toward the cap. Returns (text, truncated)."""
    if len(statement.encode("utf-8")) <= STATEMENT_CAP_BYTES:
        return statement, False
    kept: list[str] = []
    size = 0
    for line in statement.split("\n"):
        add = len(line.encode("utf-8")) + (1 if kept else 0)
        if kept and size + add > STATEMENT_CAP_BYTES:
            break
        kept.append(line)
        size += add
    return "\n".join(kept) + "\n" + TRUNCATION_MARKER, True


def heading_title(rest: str) -> str:
    """C-01 (b) title: the remainder after the ID token, closing "#" run removed, collapsed."""
    return collapse_ws(_CLOSING_HASHES_RE.sub("", rest))


def iter_declarations(lines: list[str]) -> Iterable[tuple[str, int, str, str, bool, int, bool]]:
    """Yield (family, number, title, statement, retired, lineno, recorded) for every declaration
    outside fences (C-01). The statement is capped per K-14 by the caller."""
    headings = _heading_lines(lines)
    fence: str | None = None
    for lineno, line in enumerate(lines, start=1):
        marker = _fence_marker(line)
        if fence is not None:
            # closes only on the same marker followed by nothing but whitespace (Q-008)
            if marker == fence and line.strip() == fence:
                fence = None
            continue
        if marker is not None:
            fence = marker
            continue
        stripped = line.lstrip()
        if stripped.startswith("|"):
            cells = split_row(line)
            if not cells:
                continue
            if all(_SEPARATOR_CELL_RE.match(c) for c in cells):
                continue
            first = cells[0].strip()
            m = _FIRST_CELL_RE.match(first)
            if not m:
                continue
            tok = m.group("a") or m.group("b") or m.group("c")
            retired = m.group("a") is None
            decoration = first[m.end() :].split()
            recorded = bool(decoration) and decoration[0] == RECORDED_MARKER  # R-35
            statement = collapse_ws(cells[1]) if len(cells) > 1 else ""
            fam, num = tok.split("-")
            # C-01 (a): a table declaration's title is its statement
            yield fam, int(num), statement, statement, retired, lineno, recorded
            continue
        if stripped.startswith("#"):
            m = _HEADING_RE.match(line)
            if not m:
                continue
            tok = m.group("tok")
            retired = tok.startswith("~~")
            tok = tok.strip("~")
            fam, num = tok.split("-")
            rest = m.group("rest")
            recorded = rest.split()[:1] == [RECORDED_MARKER]  # R-35: first token after the ID
            if recorded:
                rest = rest.lstrip()[len(RECORDED_MARKER) :]  # the marker is not part of the title
            title = heading_title(rest)
            level = heading_level(line)
            assert level is not None  # _HEADING_RE is a subset of _HEADING_LINE_RE
            body = section_body(lines, lineno - 1, level, headings)
            # C-01 (b) / R-33: title, newline, body; body alone when the title is empty (E-46)
            if not body:
                statement = title
            elif not title:
                statement = body
            else:
                statement = title + "\n" + body
            yield fam, int(num), title, statement, retired, lineno, recorded


# --------------------------------------------------------------------------------------------
# C-20 terse-IEEE declaration grammar (v1.19)
# --------------------------------------------------------------------------------------------

_TERSE_TOK = r"[A-Z][A-Z0-9]{0,3}-[A-Z]{1,2}-[0-9]{1,3}"
# C-20 (d): a list item whose first token after the bullet marker is **TERSE-ID — Title:** or
# **TERSE-ID:** (the em-dash and title are optional; the title is then empty);
# retirement by strike-through, either nesting.
_TERSE_BULLET_RE = re.compile(
    r"^(?P<indent>[ \t]*)[-*+][ \t]+"
    r"(?P<open>~~\*\*|\*\*~~|\*\*)"
    r"(?P<tok>" + _TERSE_TOK + r")"
    r"(?:[ \t]+—[ \t]+(?P<title>.*))?:"
    r"(?P<close>~~\*\*|\*\*~~|\*\*)"
    r"(?P<rest>.*)$"
)
# C-20 (a)/(b): C-01's forms accepting a TERSE-ID where C-01 accepts an ID.
_TERSE_FIRST_CELL_RE = re.compile(
    r"^(?:\*\*(?P<a>" + _TERSE_TOK + r")\*\*"
    r"|~~\*\*(?P<b>" + _TERSE_TOK + r")\*\*~~"
    r"|\*\*~~(?P<c>" + _TERSE_TOK + r")~~\*\*)(?:$|\s)"
)
_TERSE_HEADING_RE = re.compile(
    r"^ {0,3}#{1,6}\s+(?P<tok>~~" + _TERSE_TOK + r"~~|" + _TERSE_TOK + r")"
    r"(?![A-Za-z0-9])(?P<rest>.*)$"
)
_BULLET_LINE_RE = re.compile(r"^[ \t]*[-*+][ \t]")


def _split_terse(tok: str) -> tuple[str, str, int]:
    prefix, family, num = tok.rsplit("-", 2)
    return prefix, family, int(num)


def _bullet_item_body(lines: list[str], start: int, indent: str) -> list[str]:
    """C-20 (d): the continuation lines of the list item declared at 0-based `start` — up to the
    next list item at the same or shallower indentation, a blank line followed by
    non-continuation text, a HEADING LINE, or end of file; fenced code blocks inside the item
    included."""
    body: list[str] = []
    fence: str | None = None
    i = start + 1
    while i < len(lines):
        line = lines[i]
        marker = _fence_marker(line)
        if fence is not None:
            body.append(line)
            if marker == fence and line.strip() == fence:
                fence = None
            i += 1
            continue
        if is_blank(line):
            # a blank line ends the item unless the next non-blank line is a continuation
            j = i + 1
            while j < len(lines) and is_blank(lines[j]):
                j += 1
            if j >= len(lines):
                break
            nxt = lines[j]
            leading = len(nxt) - len(nxt.lstrip(" \t"))
            if leading <= len(indent):
                break
            body.extend(lines[i:j])
            i = j
            continue
        if heading_level(line) is not None:
            break
        if _BULLET_LINE_RE.match(line):
            leading = len(line) - len(line.lstrip(" \t"))
            if leading <= len(indent):
                break
        if marker is not None:
            fence = marker
        body.append(line)
        i += 1
    while body and is_blank(body[-1]):
        body = body[:-1]
    return body


def iter_terse_declarations(
    lines: list[str],
) -> Iterable[tuple[str, str, int, str, str, bool, int, bool]]:
    """Yield (prefix, family, number, title, statement, retired, lineno, recorded) for every
    C-20 declaration outside fences. The statement is capped per K-14 by the caller."""
    headings = _heading_lines(lines)
    fence: str | None = None
    for lineno, line in enumerate(lines, start=1):
        marker = _fence_marker(line)
        if fence is not None:
            if marker == fence and line.strip() == fence:
                fence = None
            continue
        if marker is not None:
            fence = marker
            continue
        stripped = line.lstrip()
        if stripped.startswith("|"):
            cells = split_row(line)
            if not cells:
                continue
            if all(_SEPARATOR_CELL_RE.match(c) for c in cells):
                continue
            first = cells[0].strip()
            m = _TERSE_FIRST_CELL_RE.match(first)
            if not m:
                continue
            tok = m.group("a") or m.group("b") or m.group("c")
            retired = m.group("a") is None
            decoration = first[m.end() :].split()
            recorded = bool(decoration) and decoration[0] == RECORDED_MARKER
            statement = collapse_ws(cells[1]) if len(cells) > 1 else ""
            prefix, fam, num = _split_terse(tok)
            yield prefix, fam, num, statement, statement, retired, lineno, recorded
            continue
        if stripped.startswith("#"):
            m = _TERSE_HEADING_RE.match(line)
            if not m:
                continue
            tok = m.group("tok")
            retired = tok.startswith("~~")
            tok = tok.strip("~")
            rest = m.group("rest")
            recorded = rest.split()[:1] == [RECORDED_MARKER]
            if recorded:
                rest = rest.lstrip()[len(RECORDED_MARKER) :]
            title = heading_title(rest)
            level = heading_level(line)
            assert level is not None
            body = section_body(lines, lineno - 1, level, headings)
            if not body:
                statement = title
            elif not title:
                statement = body
            else:
                statement = title + "\n" + body
            prefix, fam, num = _split_terse(tok)
            yield prefix, fam, num, title, statement, retired, lineno, recorded
            continue
        m = _TERSE_BULLET_RE.match(line)
        if m is None:
            continue
        retired = "~~" in m.group("open")
        title = collapse_ws(m.group("title") or "")
        body = _bullet_item_body(lines, lineno - 1, m.group("indent"))
        first_rest = m.group("rest").strip()
        item = ([first_rest] if first_rest else []) + body
        item_text = "\n".join(item)
        if not item:
            statement = title
        elif not title:
            statement = item_text  # title-less form: the item alone (as house F-305)
        else:
            statement = title + "\n" + item_text
        prefix, fam, num = _split_terse(m.group("tok"))
        yield prefix, fam, num, title, statement, retired, lineno, False
        # the RECORDED marker is meaningful for no terse family (D-45); bullets never carry it


def detect_dialect(text: str) -> str:
    """C-21 census under --dialect auto: terse>0 and house=0 -> terse; terse=0 -> house;
    both>0 -> DialectError (E-62). D rows (C-01 (c)) are counted in neither census."""
    lines = split_spec_lines(text)
    n_house = sum(1 for _ in iter_declarations(lines))
    n_terse = sum(1 for _ in iter_terse_declarations(lines))
    if n_terse and n_house:
        raise DialectError(
            f"dialect: ambiguous spec: {n_house} house declarations, "
            f"{n_terse} terse declarations"
        )
    return "terse" if n_terse else "house"


def count_foreign_house_tokens(lines: Iterable[str]) -> int:
    """E-63: bare house-form tokens in a terse run — never citations, never dangling; the caller
    folds the total into one Note. The R-27 ignore-line rule applies as it does to citations."""
    count = 0
    for line in lines:
        if IGNORE_LINE in line:
            continue
        count += sum(1 for _ in ID_RE.finditer(line))
    return count


# --------------------------------------------------------------------------------------------
# C-01 (c) decision table (v1.13)
# --------------------------------------------------------------------------------------------

_DECISION_ID_RE = re.compile(r"^D-[0-9]{1,3}$")


def _is_row_line(line: str) -> bool:
    return line.lstrip().startswith("|")


def _all_separator(cells: list[str]) -> bool:
    return bool(cells) and all(_SEPARATOR_CELL_RE.match(c) for c in cells)


def _decision_rows(lines: list[str]) -> list[tuple[int, str, str]]:
    """C-01 (c): (lineno, "D-nn" token, raw AFFECTS CELL text) for every decision row of the
    DECISION TABLE -- the first TABLE (a maximal run of consecutive row lines outside fenced
    code blocks, with no BLANK line between them, whose second row is a separator row) whose
    HEADER ROW has a cell equal to "affects" once trimmed and case-folded. A D-nn row outside
    that table, or in a second such table, declares nothing (Q-008-style: only the first
    match counts). Duplicate D ids are the caller's concern."""
    fence: str | None = None
    block: list[tuple[int, str]] = []
    decision_table: list[tuple[int, str]] | None = None
    affects_col: int | None = None

    def flush() -> None:
        nonlocal block, decision_table, affects_col
        if decision_table is None and len(block) >= 2:
            header_cells = split_row(block[0][1])
            sep_cells = split_row(block[1][1])
            if _all_separator(sep_cells):
                for i, cell in enumerate(header_cells):
                    if cell.strip().casefold() == "affects":
                        affects_col = i
                        decision_table = block[2:]
                        break
        block = []

    for lineno, line in enumerate(lines, start=1):
        if decision_table is not None:
            break
        marker = _fence_marker(line)
        if fence is not None:
            if marker == fence and line.strip() == fence:
                fence = None
            flush()
            continue
        if marker is not None:
            fence = marker
            flush()
            continue
        if is_blank(line):
            flush()
            continue
        if _is_row_line(line):
            block.append((lineno, line))
        else:
            flush()
    flush()

    out: list[tuple[int, str, str]] = []
    if decision_table is not None and affects_col is not None:
        for lineno, line in decision_table:
            cells = split_row(line)
            first = cells[0].strip() if cells else ""
            if _DECISION_ID_RE.match(first):
                affects_raw = cells[affects_col] if affects_col < len(cells) else ""
                out.append((lineno, first, affects_raw))
    return out


def _build_decisions_and_edges(
    ids: tuple[SpecId, ...],
    decision_rows: list[tuple[int, str, str]],
    dialect: str = "house",
) -> tuple[tuple[Decision, ...], tuple[Edge, ...], list[str]]:
    """C-12: statement-token edges among the declared ids, plus decision rows and their
    `affects` edges. Returns (decisions, edges, notes) with everything in C-12 order."""
    by_id = {s.id: s for s in ids}
    notes: set[str] = set()
    edge_retired: dict[tuple[str, str, str], bool] = {}

    def targets_of(text: str, self_id: str) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for y, _fam, _num in tokens_in_line(text, dialect):
            if y == self_id or y in seen:
                continue
            seen.add(y)
            out.append(y)
        return out

    def record(src: str, kind: str, dst: str, *, dst_retired: bool) -> None:
        key = (src, kind, dst)
        edge_retired[key] = edge_retired.get(key, False) or dst_retired

    for s in ids:  # retired included (E-55)
        for y in targets_of(s.text, s.id):
            target = by_id.get(y)
            if target is None:
                notes.add(f"edge to undeclared id: {s.id} -> {y}")
                continue
            # R-43/D-45: "verifies" is a house family-T notion; every terse edge is depends_on
            if is_test_family(s) and not is_test_family(target):
                record(s.id, "verifies", y, dst_retired=target.retired)
            elif is_test_family(target) and not is_test_family(s):
                record(y, "verifies", s.id, dst_retired=s.retired)
            else:
                record(s.id, "depends_on", y, dst_retired=target.retired)

    decisions: list[Decision] = []
    for lineno, token, affects_raw in decision_rows:
        fam, num = token.split("-")
        d_id = normalize_id(fam, int(num))
        declared_targets: list[str] = []
        for y in targets_of(affects_raw, d_id):
            target = by_id.get(y)
            if target is None:
                notes.add(f"edge to undeclared id: {d_id} -> {y}")
                continue
            declared_targets.append(y)
            record(d_id, "affects", y, dst_retired=target.retired)
        affects = tuple(sorted(set(declared_targets), key=id_sort_key))
        decisions.append(Decision(id=d_id, line=lineno, affects=affects))

    def _edge_sort_key(item: tuple[tuple[str, str, str], bool]) -> tuple[object, ...]:
        (src, kind, dst), _retired = item
        return (edge_id_key(src), kind, edge_id_key(dst))

    edges = tuple(
        Edge(src=src, kind=kind, dst=dst, retired=retired)
        for (src, kind, dst), retired in sorted(edge_retired.items(), key=_edge_sort_key)
    )
    decisions_sorted = tuple(sorted(decisions, key=lambda d: int(d.id.split("-")[1])))
    return decisions_sorted, edges, sorted(notes)


def _check_duplicate(
    seen: dict[tuple[str, int], SpecId],
    key: tuple[str, int],
    ident: str,
    retired: bool,
    lineno: int,
) -> None:
    """E-02/E-03: a second declaration of one id is an error, worded by the retired flags."""
    prior = seen.get(key)
    if prior is None:
        return
    if prior.retired == retired:
        raise SpecError(f"duplicate declaration of {ident} at lines {prior.line} and {lineno}")
    first_kind = "retired" if prior.retired else "non-retired"
    second_kind = "retired" if retired else "non-retired"
    raise SpecError(
        f"{ident} declared {first_kind} at line {prior.line} and {second_kind} at line {lineno}"
    )


def parse_spec(text: str, rel_path: str, dialect: str = "house") -> SpecIndex:
    """Build the SpecIndex from the spec text. Raises SpecError for E-01, E-02, E-03, and
    DialectError for E-64 (terse prefix mismatch)."""
    seen: dict[tuple[str, int], SpecId] = {}
    notes: list[str] = []
    if dialect == "terse":
        spec_prefix: str | None = None
        for prefix, fam, num, title, statement, retired, lineno, recorded in (
            iter_terse_declarations(split_spec_lines(text))
        ):
            if spec_prefix is None:
                spec_prefix = prefix  # C-20: fixed by the first declaration in document order
            elif prefix != spec_prefix:
                raise DialectError(  # E-64
                    f"dialect: prefix mismatch: {prefix} differs from {spec_prefix} "
                    f"at line {lineno}"
                )
            key = (fam, num)
            ident = normalize_terse_id(prefix, fam, num)
            _check_duplicate(seen, key, ident, retired, lineno)
            statement, truncated = cap_statement(statement)  # K-14
            if truncated:
                notes.append(f"statement truncated at K-14: {ident}")  # E-46
            if recorded:  # C-20/D-45: meaningful for no terse family; ignored with a Note
                notes.append(f"recorded marker ignored on {ident}: no terse family is a T family")
                recorded = False
            seen[key] = SpecId(fam, num, title, statement, lineno, retired, recorded, prefix)
    else:
        for fam, num, title, statement, retired, lineno, recorded in iter_declarations(
            split_spec_lines(text)
        ):
            key = (fam, num)
            _check_duplicate(seen, key, normalize_id(fam, num), retired, lineno)
            statement, truncated = cap_statement(statement)  # K-14
            if truncated:
                notes.append(f"statement truncated at K-14: {normalize_id(fam, num)}")  # E-46
            if recorded and fam != "T":  # E-50: the marker is meaningful for family T only
                notes.append(f"recorded marker ignored on {normalize_id(fam, num)}: not a T id")
                recorded = False
            seen[key] = SpecId(fam, num, title, statement, lineno, retired, recorded)
    ids = tuple(sorted(seen.values(), key=spec_sort_key))
    if not any(not s.retired for s in ids):
        raise SpecError("spec declares no in-scope IDs")

    decision_rows = _decision_rows(split_spec_lines(text))
    seen_decisions: dict[int, int] = {}  # number -> lineno, for E-02-style duplicate detection
    for lineno, token, _affects_raw in decision_rows:
        num = int(token.split("-")[1])
        if num in seen_decisions:
            ident = normalize_id("D", num)
            raise SpecError(
                f"duplicate declaration of {ident} at lines {seen_decisions[num]} and {lineno}"
            )
        seen_decisions[num] = lineno
    decisions, edges, edge_notes = _build_decisions_and_edges(ids, decision_rows, dialect)
    notes.extend(edge_notes)

    return SpecIndex(
        path=rel_path,
        ids=ids,
        notes=tuple(sorted(notes)),
        decisions=decisions,
        edges=edges,
    )


def decode_text(data: bytes) -> tuple[str, bool]:
    """Decode as UTF-8 with replacement; the flag says whether any byte was replaced (E-11)."""
    try:
        return data.decode("utf-8"), False
    except UnicodeDecodeError:
        return data.decode("utf-8", errors="replace"), True


# --------------------------------------------------------------------------------------------
# C-03 file scanning
# --------------------------------------------------------------------------------------------


def to_posix_relative(path: Path, root: Path) -> str:
    """R-20: paths relative to --root with '/' separators."""
    return PurePosixPath(*path.relative_to(root).parts).as_posix()


@dataclass(frozen=True)
class ScannedFile:
    path: str  # relative, POSIX
    text: str
    lines: tuple[str, ...]
    scan_root: str = (
        ""  # the --src/--tests root this file was found under, relative, POSIX (C-03 MODULE)
    )


@dataclass
class ScanCounters:
    symlinks: int = 0
    ignored_files: int = 0
    oversized: list[str] | None = None
    replaced: list[str] | None = None

    def __post_init__(self) -> None:
        self.oversized = self.oversized or []
        self.replaced = self.replaced or []

    def notes(self) -> list[str]:
        out = [f"skipped 1 file over 2 MiB: {p}" for p in self.oversized]
        out += [f"invalid UTF-8 decoded with replacement: {p}" for p in self.replaced]
        if self.symlinks:
            out.append(f"skipped {self.symlinks} symlink(s)")
        if self.ignored_files:
            out.append(f"ignored {self.ignored_files} file(s) by speccheck:ignore-file")
        return out


def _walk(root_dir: Path, counters: ScanCounters) -> Iterable[Path]:
    """Deterministic descent (sorted by name); K-03 directory skips; symlinks never followed."""
    stack = [root_dir]
    while stack:
        current = stack.pop()
        try:
            entries = sorted(os.scandir(current), key=lambda e: e.name)
        except OSError:
            continue
        subdirs: list[Path] = []
        for entry in entries:
            if entry.is_symlink():
                counters.symlinks += 1
                continue
            if entry.is_dir(follow_symlinks=False):
                if entry.name in SKIP_DIR_NAMES or entry.name.startswith("."):
                    continue
                subdirs.append(Path(entry.path))
            elif entry.is_file(follow_symlinks=False):
                yield Path(entry.path)
        # push in reverse so that pop() visits in sorted order
        stack.extend(reversed(subdirs))


def is_excluded(path: Path, excluded: frozenset[Path], out_dir: Path | None) -> bool:
    """C-03 exclusions by resolved path: spec, results, both reports, §3.1 temporaries."""
    # scan roots are resolved and descent never follows symlinks, so `path` is canonical
    resolved = path
    if resolved in excluded:
        return True
    if out_dir is not None and resolved.parent == out_dir:
        name = resolved.name
        if name.endswith(".tmp") and (
            name.startswith(".speccheck.json.") or name.startswith(".SPEC_CONFORMANCE_REPORT.md.")
        ):
            return True
    return False


def scan_roots(
    roots: Iterable[Path],
    root: Path,
    excluded: frozenset[Path],
    out_dir: Path | None,
    counters: ScanCounters,
) -> list[ScannedFile]:
    """C-03 PATHS (D-23): every admitted file, ascending by resolved path.
    A directory element is descended; a file element is scanned under its parent
    directory (D-18). Resolved-path deduplication: a directly-named file also
    covered by a directory is scanned and cited exactly once (I-012)."""
    files: list[ScannedFile] = []
    seen: set[Path] = set()
    for entry in roots:  # C-03 PATHS (D-23): a directory element is descended; a file element
        # is scanned as that one file under its parent directory (D-18, fixes its MODULE).
        if entry.is_dir():  # entry is a resolved (canonical) path, so never a symlink
            candidates = ((p, entry) for p in _walk(entry, counters))
        elif entry.is_file():
            candidates = [(entry, entry.parent)]
        else:
            continue  # E-52 (cli.py) excludes any element that is neither a dir nor a file
        for path, scan_root in candidates:
            if path in seen:
                continue
            seen.add(path)
            if is_excluded(path, excluded, out_dir):
                continue
            try:
                size = path.stat().st_size
            except OSError:
                continue
            rel = to_posix_relative(path, root)
            rel_root = to_posix_relative(scan_root, root)
            if size > MAX_FILE_BYTES:
                counters.oversized.append(rel)
                continue
            try:
                data = path.read_bytes()
            except OSError:
                continue
            if b"\x00" in data[:BINARY_PROBE_BYTES]:
                continue  # E-29: silent
            text, replaced = decode_text(data)
            if replaced:
                counters.replaced.append(rel)
            lines = text.split("\n")
            if any(IGNORE_FILE in ln for ln in lines[:3]):
                counters.ignored_files += 1
                continue
            files.append(ScannedFile(path=rel, text=text, lines=tuple(lines), scan_root=rel_root))
    files.sort(key=lambda f: f.path)
    return files


@dataclass(frozen=True)
class RawCitation:
    id: str
    file: str
    line: int


def citations_in_file(scanned: ScannedFile, dialect: str = "house") -> list[RawCitation]:
    """Every TOKEN occurrence on a line not carrying speccheck:ignore (C-01, C-20, R-27)."""
    out: list[RawCitation] = []
    for lineno, line in enumerate(scanned.lines, start=1):
        if IGNORE_LINE in line:
            continue
        for ident, _fam, _num in tokens_in_line(line, dialect):
            out.append(RawCitation(ident, scanned.path, lineno))
    return out
