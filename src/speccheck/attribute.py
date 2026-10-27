"""Attributor: map test-file citations to the enclosing test case (C-03).

Python files are delimited with `ast` (module-level `test_*` functions; `test*` methods of
recognized classes); Swift files by the line-based adapter in `swift.py` (R-31); JavaScript
and TypeScript files by the token adapter in `jsts.py` (R-104); everything else, and any file
that fails to delimit, is one file-level case.

Spec IDs realized here (§11): R-04, R-16, R-31, R-39, R-104, C-03, C-14, I-002, I-014, K-08,
E-12, E-13, E-22, E-28, E-42, E-43, E-56, E-74, E-75.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass

from .extract import RawCitation, ScannedFile, citations_in_file
from .jsts import EXTENSIONS as JS_EXTENSIONS
from .jsts import JsParseError, delimit_js
from .swift import SwiftParseError, delimit_swift, swift_module


@dataclass(frozen=True)
class TestCase:
    file: str  # relative, POSIX
    name: str  # "" for file-level
    classname: str  # dotted module path (+ ".ClassName" for methods)
    start: int  # 1-based
    end: int  # inclusive

    @property
    def is_file_level(self) -> bool:
        return self.name == ""


@dataclass(frozen=True)
class Citation:
    id: str
    file: str
    line: int
    kind: str  # "src" | "test"
    testcase: TestCase | None
    declared: bool = False  # C-14/R-39 (v1.14): DECLARED vs INCIDENTAL; always False for "src"
    mapped: bool = False  # v1.23 (R-103, C-23): made by a --citation-map entry, not by a token


def module_classname(rel_path: str) -> str:
    """'tests/test_core.py' -> 'tests.test_core'; final extension dropped (also for fallback)."""
    parts = rel_path.split("/")
    last = parts[-1]
    dot = last.rfind(".")
    if dot > 0:
        last = last[:dot]
    return ".".join(parts[:-1] + [last])


def _recognized_class(node: ast.ClassDef) -> bool:
    if node.name.startswith("Test"):
        return True
    for base in node.bases:
        if isinstance(base, ast.Name) and base.id.endswith("TestCase"):
            return True
        if isinstance(base, ast.Attribute) and base.attr.endswith("TestCase"):
            return True
    return False


def _span(node: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[int, int]:
    start = node.lineno
    for dec in node.decorator_list:
        start = min(start, dec.lineno)
    return start, node.end_lineno or node.lineno


def _doc_span(node: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[int, int] | None:
    """C-14: the line range of the `Expr` node `ast.get_docstring` reads, or None.

    The node (not the text `get_docstring` returns), so a multi-line docstring's second and
    later lines count."""
    if not node.body:
        return None
    first = node.body[0]
    if (
        isinstance(first, ast.Expr)
        and isinstance(first.value, ast.Constant)
        and isinstance(first.value.value, str)
    ):
        return (first.lineno, first.value.end_lineno or first.lineno)
    return None


def _nested_test_names(cls: ast.ClassDef, prefix: str) -> list[str]:
    """`test*` methods of an unrecognized or nested class (E-28): names for the Note."""
    names: list[str] = []
    for item in cls.body:
        if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef) and item.name.startswith(
            "test"
        ):
            names.append(f"{prefix}{cls.name}.{item.name}")
        elif isinstance(item, ast.ClassDef):
            names.extend(_nested_test_names(item, f"{prefix}{cls.name}."))
    return names


def _python_cases(
    scanned: ScannedFile,
) -> tuple[list[TestCase], list[str], dict[TestCase, tuple[int, int]]]:
    """Delimit test cases in a Python file. Raises SyntaxError when the file does not parse.

    The third element is each case's docstring line range (C-14), for the DECLARED test."""
    tree = ast.parse(scanned.text)
    module = module_classname(scanned.path)
    cases: list[TestCase] = []
    undelimited: list[str] = []
    doc_spans: dict[TestCase, tuple[int, int]] = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            if node.name.startswith("test_"):
                start, end = _span(node)
                case = TestCase(scanned.path, node.name, module, start, end)
                cases.append(case)
                if (span := _doc_span(node)) is not None:
                    doc_spans[case] = span
        elif isinstance(node, ast.ClassDef):
            if _recognized_class(node):
                for item in node.body:
                    if isinstance(
                        item, ast.FunctionDef | ast.AsyncFunctionDef
                    ) and item.name.startswith("test"):
                        start, end = _span(item)
                        case = TestCase(
                            scanned.path, item.name, f"{module}.{node.name}", start, end
                        )
                        cases.append(case)
                        if (span := _doc_span(item)) is not None:
                            doc_spans[case] = span
                    elif isinstance(item, ast.ClassDef):
                        undelimited.extend(_nested_test_names(item, f"{node.name}."))
            else:
                undelimited.extend(_nested_test_names(node, ""))
    return cases, undelimited, doc_spans


def _declared(
    line: int,
    case: TestCase,
    lines: tuple[str, ...],
    doc_spans: dict[TestCase, tuple[int, int]],
    doc_lines: list[bool],
) -> bool:
    """C-14: is this citation DECLARED in `case`?

    A "test"-kind citation is DECLARED when its line is inside the case's own docstring (Python:
    the `_doc_span` node range) or is a whole-line comment (`#` for Python; a `_Line.doc` line
    for Swift — `///` or inside `/** ... */`). A file-level case, and any other adapter (E-56),
    is always INCIDENTAL."""
    if case.is_file_level:
        return False  # E-56
    if doc_lines:  # Swift: the R-31 line model, reused rather than re-detected
        return 1 <= line <= len(doc_lines) and doc_lines[line - 1]
    span = doc_spans.get(case)
    if span is not None and span[0] <= line <= span[1]:
        return True
    text = lines[line - 1] if 1 <= line <= len(lines) else ""
    return text.lstrip().startswith("#")


@dataclass(frozen=True)
class AttributedFile:
    cases: tuple[TestCase, ...]  # delimited cases (file-level case excluded)
    file_case: TestCase
    citations: tuple[Citation, ...]


def attribute_file(
    scanned: ScannedFile, namespace: str | None = None
) -> tuple[AttributedFile, list[str]]:
    """Attribute every citation in a test file to its enclosing case, or to the file-level case."""
    notes: list[str] = []
    n_lines = max(1, len(scanned.lines))
    file_case = TestCase(scanned.path, "", module_classname(scanned.path), 1, n_lines)
    cases: list[TestCase] = []
    doc_spans: dict[TestCase, tuple[int, int]] = {}  # C-14: Python docstring line ranges
    doc_lines: list[bool] = []  # C-14: Swift `_Line.doc` per line (R-31)
    if scanned.path.endswith(".py"):
        try:
            cases, undelimited, doc_spans = _python_cases(scanned)
        except (SyntaxError, ValueError, RecursionError, MemoryError):
            notes.append(f"parse fallback: {scanned.path}")
            cases = []
        else:
            if undelimited:
                notes.append(f"undelimited tests in {scanned.path}: {', '.join(undelimited)}")
    elif scanned.path.endswith(".swift"):
        try:
            swift_cases, undelimited, doc_lines = delimit_swift(scanned.lines)
        except SwiftParseError:
            notes.append(f"parse fallback: {scanned.path}")  # E-42
            cases = []
        else:
            module = swift_module(scanned.path, scanned.scan_root)
            for sc in swift_cases:
                classname = ".".join((module, *sc.chain))
                cases.append(TestCase(scanned.path, sc.name, classname, sc.start, sc.end))
            if undelimited:  # E-43
                notes.append(f"undelimited tests in {scanned.path}: {', '.join(undelimited)}")
    elif scanned.path.endswith(JS_EXTENSIONS):
        try:
            js_cases, undelimited, doc_lines = delimit_js(scanned.lines)
        except JsParseError:
            notes.append(f"parse fallback: {scanned.path}")  # E-74
            cases = []
        else:
            classname = scanned.path.replace("/", ".")  # the extension is kept (C-04, R-104)
            cases = [
                TestCase(scanned.path, jc.name, classname, jc.start, jc.end) for jc in js_cases
            ]
            if undelimited:  # E-75
                notes.append(f"undelimited tests in {scanned.path}: {', '.join(undelimited)}")
    cases.sort(key=lambda c: (c.start, c.end, c.name))
    citations: list[Citation] = []
    raw: RawCitation
    for raw in citations_in_file(scanned, namespace):
        owner = file_case
        for case in cases:
            if case.start <= raw.line <= case.end:
                owner = case
                break
        declared = _declared(raw.line, owner, scanned.lines, doc_spans, doc_lines)
        citations.append(Citation(raw.id, raw.file, raw.line, "test", owner, declared))
    return AttributedFile(tuple(cases), file_case, tuple(citations)), notes
