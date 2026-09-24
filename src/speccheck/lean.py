"""Lean adapter: split Lean 4 source on declaration heads and read the spec ids each declaration
discharges from its doc comment (C-20; v1.19). The line-based pattern `swift.py` established for
a second language, extended to a third: no parser, no Lean toolchain, standard library only.

Spec IDs realized here (§11): R-100, C-20, E-62.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .extract import normalize_id

# C-20: declaration heads. Each optionally `public`/`protected`-prefixed, one per head.
_DECL_RE = re.compile(
    r"^\s*(?:public\s+|protected\s+)*(?:theorem|lemma|def|abbrev|instance)\s+"
    r"([A-Za-z_][A-Za-z0-9_']*)"
)
# Doc comments: `/-- ... -/` (declaration doc); section headers `/-! ... -/` are not declaration
# docs and are skipped by the "one block, ending <=1 line above the head" rule naturally, since
# they rarely sit directly above a declaration head.
_DOC_OPEN_RE = re.compile(r"^\s*/--")
_DOC_CLOSE_RE = re.compile(r"-/\s*$")
_BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
_ID_IN_RE = re.compile(r"\b([RCIKE])-([0-9]{1,3})(?:\s*\([^)]*\))?")


@dataclass(frozen=True)
class ProofCitation:
    """One (declaration, id) pair discharged by a Lean declaration (C-20)."""

    id: str
    file: str  # posix-relative to --root
    name: str
    line: int  # 1-based, the declaration head's line


@dataclass
class LeanScanResult:
    citations: list[ProofCitation] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)  # E-62: unreadable / no parseable declaration


def _doc_blocks(lines: list[str]) -> list[tuple[int, list[str]]]:
    """(1-indexed end line, body lines) of every `/-- ... -/` doc-comment block."""
    blocks: list[tuple[int, list[str]]] = []
    i = 0
    n = len(lines)
    while i < n:
        if _DOC_OPEN_RE.match(lines[i]):
            start = i
            if _DOC_CLOSE_RE.search(lines[i]) and lines[i].strip() != "/--":
                blocks.append((start + 1, [lines[i]]))
                i += 1
                continue
            j = i + 1
            while j < n and not _DOC_CLOSE_RE.search(lines[j]):
                j += 1
            blocks.append((j + 1, lines[start : j + 1]))
            i = j + 1
            continue
        i += 1
    return blocks


def _tags(body: list[str]) -> list[str]:
    """Every RCIKE id inside a bold span; `(a)`-style parentheticals stripped; T/D tokens and any
    other family dropped (C-20)."""
    ids: list[str] = []
    for line in body:
        for span in _BOLD_RE.findall(line):
            for family, number in _ID_IN_RE.findall(span):
                ids.append(normalize_id(family, int(number)))
    # de-duplicate, keep first-seen order
    seen: set[str] = set()
    out = []
    for i in ids:
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out


def parse_lean_text(text: str, rel_path: str) -> tuple[list[ProofCitation], bool]:
    """One file's declarations and their tags. Returns (citations, had_any_declaration) — the
    caller uses the second value for the E-62 "no parseable declaration head" case."""
    lines = text.splitlines()
    blocks = _doc_blocks(lines)
    citations: list[ProofCitation] = []
    found_decl = False
    for k, line in enumerate(lines, 1):
        m = _DECL_RE.match(line)
        if not m:
            continue
        found_decl = True
        name = m.group(1)
        tags: list[str] = []
        for end, body in blocks:
            # C-20: the doc-comment block ending at most one line above the head.
            if 0 < k - end <= 2:
                tags = _tags(body)
        for ident in tags:
            citations.append(ProofCitation(ident, rel_path, name, k))
    return citations, found_decl


def collect_lean_files(paths: tuple[Path, ...]) -> list[Path]:
    """Directory elements recursively scanned for `*.lean` (C-20); file elements used as given.
    Deduplicated by resolved path (I-012's pattern), in ascending path order."""
    seen: set[Path] = set()
    out: list[Path] = []
    for p in paths:
        candidates = sorted(p.rglob("*.lean")) if p.is_dir() else [p]
        for f in candidates:
            if f not in seen:
                seen.add(f)
                out.append(f)
    return out


def scan_lean_paths(paths: tuple[Path, ...], root: Path) -> LeanScanResult:
    """Scan every `--proof` path (C-20) and return the proof citations plus E-62 notes for any
    file that could not be read or yielded no parseable declaration head."""
    result = LeanScanResult()
    for f in collect_lean_files(paths):
        rel = f.resolve().relative_to(root).as_posix()
        try:
            text = f.read_bytes().decode("utf-8")
        except (OSError, UnicodeDecodeError):
            result.notes.append(f"unreadable or non-Lean file, skipped: {rel}")
            continue
        citations, found_decl = parse_lean_text(text, rel)
        if not found_decl:
            result.notes.append(f"no parseable Lean declaration, skipped: {rel}")
            continue
        result.citations.extend(citations)
    return result
