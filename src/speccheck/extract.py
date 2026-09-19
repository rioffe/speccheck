"""Extractor: SPEC.md -> SpecIndex (C-01, C-02) and file trees -> text files / citations (C-03).

Everything here is deterministic and pattern-based (R-01..R-04, R-27); no semantic analysis.

Spec IDs realized here (§11): R-01, R-02, R-03, R-16, R-20, R-27, R-33, C-01, C-02, C-03, I-002,
    R-35, I-011, K-02, K-03, K-04, K-08, K-14, E-01, E-02, E-03, E-04, E-10, E-11, E-20, E-23,
    E-29, E-30, E-31, E-33, E-34, E-46, E-47, E-50.
"""

from __future__ import annotations

import os
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

# C-01 TOKEN regex; K-04 (1-3 digits, alphanumeric-bounded).
ID_RE = re.compile(r"(?<![A-Za-z0-9])([RCIKET])-([0-9]{1,3})(?![A-Za-z0-9])")

FAMILY_ORDER = "RCIKET"
FAMILIES = frozenset(FAMILY_ORDER)

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


def normalize_id(family: str, number: int) -> str:
    """C-01 normalized form; I-011 (injective within a family)."""
    width = 3 if family == "I" else 2
    return f"{family}-{number:0{width}d}"


def family_rank(family: str) -> int:
    return FAMILY_ORDER.index(family)


def id_sort_key(ident: str) -> tuple[int, int]:
    family, num = ident.split("-", 1)
    return (family_rank(family), int(num))


def tokens_in_line(line: str) -> list[tuple[str, str, int]]:
    """Every ID token on a line as (normalized_id, family, number)."""
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
    recorded: bool = False  # C-01 RECORDED marker (R-35); only ever True for family T

    @property
    def id(self) -> str:
        return normalize_id(self.family, self.number)


@dataclass(frozen=True)
class SpecIndex:
    path: str
    ids: tuple[SpecId, ...]
    notes: tuple[str, ...] = ()  # K-14 / E-46: one Note per truncated statement

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


def parse_spec(text: str, rel_path: str) -> SpecIndex:
    """Build the SpecIndex from the spec text. Raises SpecError for E-01, E-02, E-03."""
    seen: dict[tuple[str, int], SpecId] = {}
    notes: list[str] = []
    for fam, num, title, statement, retired, lineno, recorded in iter_declarations(
        split_spec_lines(text)
    ):
        key = (fam, num)
        if key in seen:
            prior = seen[key]
            ident = normalize_id(fam, num)
            if prior.retired == retired:
                raise SpecError(
                    f"duplicate declaration of {ident} at lines {prior.line} and {lineno}"
                )
            first_kind = "retired" if prior.retired else "non-retired"
            second_kind = "retired" if retired else "non-retired"
            raise SpecError(
                f"{ident} declared {first_kind} at line {prior.line} "
                f"and {second_kind} at line {lineno}"
            )
        statement, truncated = cap_statement(statement)  # K-14
        if truncated:
            notes.append(f"statement truncated at K-14: {normalize_id(fam, num)}")  # E-46
        if recorded and fam != "T":  # E-50: the marker is meaningful for family T only
            notes.append(f"recorded marker ignored on {normalize_id(fam, num)}: not a T id")
            recorded = False
        seen[key] = SpecId(fam, num, title, statement, lineno, retired, recorded)
    ids = tuple(sorted(seen.values(), key=lambda s: (family_rank(s.family), s.number)))
    if not any(not s.retired for s in ids):
        raise SpecError("spec declares no in-scope IDs")
    return SpecIndex(path=rel_path, ids=ids, notes=tuple(sorted(notes)))


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
    """Every text file under the roots that C-03 admits, in deterministic path order."""
    files: list[ScannedFile] = []
    seen: set[Path] = set()
    for scan_root in roots:
        for path in _walk(scan_root, counters):
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


def citations_in_file(scanned: ScannedFile) -> list[RawCitation]:
    """Every TOKEN occurrence on a line not carrying speccheck:ignore (C-01, R-27)."""
    out: list[RawCitation] = []
    for lineno, line in enumerate(scanned.lines, start=1):
        if IGNORE_LINE in line:
            continue
        for ident, _fam, _num in tokens_in_line(line):
            out.append(RawCitation(ident, scanned.path, lineno))
    return out
