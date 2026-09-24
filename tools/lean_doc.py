#!/usr/bin/env python3
"""Extract the first comment of a Lean file as Markdown.

The files under `proof/` open with a block comment whose body *is* a Markdown document — the module
header: a `# ` title naming the module and the source file it transcribes, the line-by-line
correspondence table, the recorded limits. This tool pulls that body out of the Lean syntax around
it, so it can be read, rendered, diffed or handed to something else.

Usage
-----
    python3 tools/lean_doc.py proof/LinregProof/Linreg/Model.lean             # to stdout
    python3 tools/lean_doc.py proof/LinregProof/Linreg/Model.lean -o /tmp/model.md
    python3 tools/lean_doc.py - < proof/LinregProof/Linreg/Model.lean         # from stdin

Exit codes: `0` extracted; `1` no comment found, or the comment never closes, or the file is
unreadable (message on stderr); `2` usage (argparse).

What "first comment" means — the scan follows Lean's own rules, not a regex:

* `/- … -/` opens a block comment, and block comments **nest**: `/- a /- b -/ c -/` is one comment
  whose body is ` a /- b -/ c `, and the body ends where the nesting depth returns to zero.
* `/-! … -/` (module doc) and `/-- … -/` (declaration doc) are block comments too; the marker
  character after `/-` belongs to the opener and is not part of the body.
* `-- …` runs to the end of the line, so a `/-` inside one opens nothing.
* `"…"` string literals — including the `s!`/`f!`/`m!` interpolated forms, whose `{ … }` holes may
  themselves contain strings, chars, comments and further braces — and `'x'` char literals are
  skipped, so the `/-` of `s!"/-"` opens nothing.
* a `'` with no closing quote within a few characters on the same line is an identifier prime
  (`f'`), not a char literal.

The body is emitted verbatim apart from blank lines trimmed at both ends and line endings
normalised to `\\n`. Interior blank lines, indentation, and the spaces a one-line `/- x -/` carries
are preserved (` x `, not `x`): trailing spaces are a hard break in Markdown, so the body's
whitespace is the document's business and not this tool's.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

# The one-character markers that may follow `/-`: `/-!` module docs and `/--` declaration docs.
MARKERS = ("!", "-")

# A char literal is short (`'a'`, `'\n'`, `'\u{1F600}'`); a `'` further away is an identifier prime.
CHAR_LITERAL_MAX = 12


def _block_body(text: str, i: int) -> tuple[int, int]:
    """The body span of the block comment opening at `i` (which points at `/-`).

    Raises ValueError if the comment never closes.
    """
    start = i + 2
    if text[start : start + 1] in MARKERS:
        start += 1
    depth, j, n = 1, start, len(text)
    while j < n:
        if text.startswith("/-", j):
            depth, j = depth + 1, j + 2
        elif text.startswith("-/", j):
            depth, j = depth - 1, j + 2
            if depth == 0:
                return start, j - 2
        else:
            j += 1
    raise ValueError(f"block comment at offset {i} never closes")


def _skip_string(text: str, i: int) -> int:
    """The index just past the string literal opening at `i` (a `"`), interpolations included."""
    interpolated = text[max(i - 2, 0) : i] in ("s!", "f!", "m!")
    j, n = i + 1, len(text)
    while j < n:
        c = text[j]
        if c == "\\":
            j += 2
        elif c == '"':
            return j + 1
        elif interpolated and c == "{":
            j = _skip_interpolation(text, j)
        else:
            j += 1
    return n  # unterminated string: everything left is string


def _skip_interpolation(text: str, i: int) -> int:
    """The index just past the `{ … }` hole of an interpolated string, braces balanced."""
    depth, j, n = 1, i + 1, len(text)
    while j < n and depth:
        c = text[j]
        if c == '"':
            j = _skip_string(text, j)
        elif c == "'":
            j = _skip_char(text, j)
        elif text.startswith("--", j):
            k = text.find("\n", j)
            j = n if k < 0 else k + 1
        elif text.startswith("/-", j):
            j = _block_body(text, j)[1] + 2
        elif c == "{":
            depth, j = depth + 1, j + 1
        elif c == "}":
            depth, j = depth - 1, j + 1
        else:
            j += 1
    return j


def _skip_char(text: str, i: int) -> int:
    """The index just past the char literal at `i`, or past this `'` when it is an identifier prime."""
    j, n = i + 1, len(text)
    while j < n and j - i <= CHAR_LITERAL_MAX and text[j] != "\n":
        if text[j] == "\\":
            j += 2
        elif text[j] == "'":
            return j + 1
        else:
            j += 1
    return i + 1


def first_comment(text: str) -> str | None:
    """The body of the first comment in `text`, markers stripped, or None if there is none."""
    i, n = 0, len(text)
    while i < n:
        if text[i] == '"':
            i = _skip_string(text, i)
        elif text[i] == "'":
            i = _skip_char(text, i)
        elif text.startswith("--", i):
            k = text.find("\n", i)
            if k < 0:
                return None
            i = k + 1
        elif text.startswith("/-", i):
            start, end = _block_body(text, i)
            lines = text[start:end].splitlines()
            while lines and not lines[0].strip():
                lines.pop(0)
            while lines and not lines[-1].strip():
                lines.pop()
            return "\n".join(lines)
        else:
            i += 1
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Extract the first comment of a Lean file as Markdown.")
    parser.add_argument("path", help="a Lean file, or - to read from stdin")
    parser.add_argument("-o", "--out", metavar="PATH",
                        help="write the Markdown here instead of stdout")
    args = parser.parse_args(argv)

    try:
        text = sys.stdin.read() if args.path == "-" else \
            pathlib.Path(args.path).read_text(encoding="utf-8")
    except OSError as exc:
        print(f"lean_doc: {args.path}: {exc.strerror or exc}", file=sys.stderr)
        return 1

    try:
        body = first_comment(text)
    except ValueError as exc:
        print(f"lean_doc: {args.path}: {exc}", file=sys.stderr)
        return 1
    if body is None:
        print(f"lean_doc: {args.path}: no comment found", file=sys.stderr)
        return 1

    if args.out:
        pathlib.Path(args.out).write_text(body + "\n", encoding="utf-8")
        first = body.splitlines()[0] if body else ""
        print(f"lean_doc: wrote {args.out} ({len(body.splitlines())} lines; {first[:70]!r})")
    else:
        sys.stdout.write(body + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())