"""Swift adapter: delimit Swift Testing `@Test` functions and XCTest `test*` methods by lines
(C-03 Swift adapter; R-31, D-17, D-18, D-19). No parser: the kernel stays standard-library.

Spec IDs realized here (§11): R-31, C-03, E-42, E-43.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_MODIFIERS = (
    "public|package|internal|private|fileprivate|open|static|class|final|override|mutating|"
    "nonmutating|nonisolated|isolated|consuming|borrowing|indirect"
)
_TYPE_RE = re.compile(
    r"^\s*(?:@\S+\s+|(?:public|package|internal|private|fileprivate|open|final|indirect)\s+)*"
    r"(?P<kind>struct|class|actor|enum|extension)\s+(?!func\b)(?P<name>[A-Za-z_][A-Za-z0-9_]*)"
)
_FUNC_RE = re.compile(
    r"^\s*(?:@[A-Za-z_][A-Za-z0-9_]*(?:\([^)]*\))?\s+|(?:" + _MODIFIERS + r")\s+)*"
    r"func\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*[<(]"
)
_TEST_ATTR_RE = re.compile(r"@Test(?=[(\s]|$)")
_XCTESTCASE_RE = re.compile(r"\bXCTestCase\b")


@dataclass(frozen=True)
class SwiftCase:
    name: str  # the function identifier (D-19)
    chain: tuple[str, ...]  # enclosing type identifiers, outermost first
    start: int  # 1-based, first line of the attribute block
    end: int  # inclusive, the closing-brace line


class SwiftParseError(Exception):
    """E-42: brace depth went negative or did not return to zero."""


@dataclass
class _Line:
    code: str  # comments removed, string literals blanked (C-03)
    doc: bool  # a doc-comment line: `///` or inside `/** ... */`
    attr_start: bool  # first non-space character is `@`
    open_before: int
    open_after: int
    first_brace_depth: int | None  # depth in force before this line's first `{`, or None


def _strip(lines: tuple[str, ...]) -> list[_Line]:
    """Apply the C-03 stripping rules line by line and count braces."""
    out: list[_Line] = []
    depth = 0
    in_block = False  # inside /* ... */
    in_doc_block = False  # the block comment opened with /**
    in_multi = False  # inside a """ ... """ literal
    for raw in lines:
        stripped = raw.lstrip()
        doc = in_block and in_doc_block
        if stripped.startswith("///"):
            doc = True
        # C-03 (D-17): a `//` anywhere starts a comment, string literal or not.
        text = raw
        if not in_block and not in_multi and "//" in text:
            text = text[: text.index("//")]
        code: list[str] = []
        i = 0
        n = len(text)
        while i < n:
            ch = text[i]
            if in_block:
                end = text.find("*/", i)
                if end < 0:
                    i = n
                else:
                    in_block = False
                    in_doc_block = False
                    i = end + 2
                continue
            if in_multi:
                end = text.find('"""', i)
                if end < 0:
                    i = n
                else:
                    in_multi = False
                    i = end + 3
                continue
            if text.startswith("/*", i):
                in_block = True
                in_doc_block = text.startswith("/**", i)
                doc = doc or in_doc_block
                i += 2
                continue
            if text.startswith('"""', i):
                in_multi = True
                i += 3
                continue
            if ch == '"':
                j = i + 1
                while j < n and text[j] != '"':
                    j += 2 if text[j] == "\\" else 1
                i = j + 1
                continue
            code.append(ch)
            i += 1
        code_text = "".join(code)
        before = depth
        first_brace_depth: int | None = None
        for ch in code_text:
            if ch == "{":
                if first_brace_depth is None:
                    first_brace_depth = depth
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth < 0:
                    raise SwiftParseError("negative brace depth")
        out.append(
            _Line(code_text, doc, stripped.startswith("@"), before, depth, first_brace_depth)
        )
    if depth != 0:
        raise SwiftParseError("unbalanced braces at end of file")
    return out


def _attribute_lines(lines: list[_Line]) -> list[bool]:
    """Lines that belong to an attribute: a `@` line and the continuation lines until its
    parentheses balance (C-03 ATTRIBUTE BLOCK (ii))."""
    flags = [False] * len(lines)
    i = 0
    while i < len(lines):
        opens_type = _TYPE_RE.match(lines[i].code) and lines[i].open_after > lines[i].open_before
        is_import = lines[i].code.lstrip().startswith("@testable")
        if lines[i].attr_start and not opens_type and not is_import:
            balance = 0
            j = i
            while j < len(lines):
                flags[j] = True
                balance += lines[j].code.count("(") - lines[j].code.count(")")
                if balance <= 0 or _FUNC_RE.match(lines[j].code):
                    break
                j += 1
            i = j + 1
        else:
            i += 1
    return flags


def delimit_swift(
    lines: tuple[str, ...],
) -> tuple[list[SwiftCase], list[str], list[bool]]:
    """Return (cases, undelimited `Chain.name` list, per-line doc-comment flags). Raises
    SwiftParseError (E-42). The flags are `_Line.doc` for every line (R-31) — the C-14 DECLARED
    test reuses this line model rather than re-detecting doc comments."""
    parsed = _strip(lines)
    doc_lines = [line.doc for line in parsed]
    attr = _attribute_lines(parsed)
    cases: list[SwiftCase] = []
    undelimited: list[str] = []
    # Open types: (depth the type body lives at, name, is_xctest_class)
    stack: list[tuple[int, str, bool]] = []
    for idx, line in enumerate(parsed):
        while stack and line.open_before < stack[-1][0]:
            stack.pop()
        m_type = _TYPE_RE.match(line.code)
        if m_type and line.open_after > line.open_before and line.first_brace_depth is not None:
            rest = line.code[m_type.end() :]
            is_xc = m_type.group("kind") == "class" and bool(_XCTESTCASE_RE.search(rest))
            stack.append((line.first_brace_depth + 1, m_type.group("name"), is_xc))
            continue
        m_func = _FUNC_RE.match(line.code)
        if not m_func:
            continue
        name = m_func.group("name")
        # Attribute block: contiguous doc / attribute lines above, blanks only between them.
        start = idx
        k = idx - 1
        while k >= 0:
            if parsed[k].doc or attr[k]:
                start = k
                k -= 1
            elif parsed[k].code.strip() == "" and not lines[k].strip():
                k -= 1
            else:
                break
        block = "\n".join(parsed[j].code for j in range(start, idx))
        block += "\n" + line.code[: m_func.start("name")]
        is_swift_testing = bool(_TEST_ATTR_RE.search(block))
        chain = tuple(entry[1] for entry in stack)
        direct = stack[-1] if stack and stack[-1][0] == line.open_before else None
        is_xctest = name.startswith("test") and direct is not None and direct[2]
        if not is_swift_testing and not is_xctest:
            if name.startswith("test"):
                undelimited.append(".".join(chain + (name,)))
            continue
        # Span end: the line where depth returns to what it was before the body's `{`.
        body_depth: int | None = None
        end = None
        for j in range(idx, len(parsed)):
            if body_depth is None:
                if parsed[j].first_brace_depth is not None:
                    body_depth = parsed[j].first_brace_depth
                elif j > idx and (
                    parsed[j].open_after < parsed[j].open_before or _FUNC_RE.match(parsed[j].code)
                ):
                    break  # a declaration without a body (protocol requirement)
                else:
                    continue
            if parsed[j].open_after <= body_depth:
                end = j
                break
        if end is None:
            continue
        cases.append(SwiftCase(name, chain, start + 1, end + 1))
    return cases, undelimited, doc_lines


def swift_module(path: str, scan_root: str) -> str:
    """MODULE (C-03, D-18): the first path component under the tests root, or the root's own
    last component for a file directly under it."""
    root = scan_root.strip("/")
    rel = path
    if root and root != "." and (path == root or path.startswith(root + "/")):
        rel = path[len(root) + 1 :]
    parts = rel.split("/")
    if len(parts) > 1:
        return parts[0]
    if root and root != ".":
        return root.split("/")[-1]
    return parts[0].rsplit(".", 1)[0]
