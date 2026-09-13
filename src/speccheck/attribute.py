"""Attributor: map test-file citations to the enclosing test case (C-03).

Python files are delimited with `ast` (module-level `test_*` functions; `test*` methods of
recognized classes); everything else, and any `.py` that fails to parse, is one file-level case.

Spec IDs realized here (§11): R-04, R-16, C-03, I-002, K-08, E-12, E-13, E-22, E-28.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass

from .extract import RawCitation, ScannedFile, citations_in_file


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


def _python_cases(scanned: ScannedFile) -> tuple[list[TestCase], list[str]]:
    """Delimit test cases in a Python file. Raises SyntaxError when the file does not parse."""
    tree = ast.parse(scanned.text)
    module = module_classname(scanned.path)
    cases: list[TestCase] = []
    undelimited: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            if node.name.startswith("test_"):
                start, end = _span(node)
                cases.append(TestCase(scanned.path, node.name, module, start, end))
        elif isinstance(node, ast.ClassDef):
            if _recognized_class(node):
                for item in node.body:
                    if isinstance(
                        item, ast.FunctionDef | ast.AsyncFunctionDef
                    ) and item.name.startswith("test"):
                        start, end = _span(item)
                        cases.append(
                            TestCase(scanned.path, item.name, f"{module}.{node.name}", start, end)
                        )
                    elif isinstance(item, ast.ClassDef):
                        undelimited.extend(_nested_test_names(item, f"{node.name}."))
            else:
                undelimited.extend(_nested_test_names(node, ""))
    return cases, undelimited


@dataclass(frozen=True)
class AttributedFile:
    cases: tuple[TestCase, ...]  # delimited cases (file-level case excluded)
    file_case: TestCase
    citations: tuple[Citation, ...]


def attribute_file(scanned: ScannedFile) -> tuple[AttributedFile, list[str]]:
    """Attribute every citation in a test file to its enclosing case, or to the file-level case."""
    notes: list[str] = []
    n_lines = max(1, len(scanned.lines))
    file_case = TestCase(scanned.path, "", module_classname(scanned.path), 1, n_lines)
    cases: list[TestCase] = []
    if scanned.path.endswith(".py"):
        try:
            cases, undelimited = _python_cases(scanned)
        except (SyntaxError, ValueError, RecursionError, MemoryError):
            notes.append(f"parse fallback: {scanned.path}")
            cases = []
        else:
            if undelimited:
                notes.append(f"undelimited tests in {scanned.path}: {', '.join(undelimited)}")
    cases.sort(key=lambda c: (c.start, c.end, c.name))
    citations: list[Citation] = []
    raw: RawCitation
    for raw in citations_in_file(scanned):
        owner = file_case
        for case in cases:
            if case.start <= raw.line <= case.end:
                owner = case
                break
        citations.append(Citation(raw.id, raw.file, raw.line, "test", owner))
    return AttributedFile(tuple(cases), file_case, tuple(citations)), notes
