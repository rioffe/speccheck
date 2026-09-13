"""Results Mapper: JUnit XML -> outcomes per attributed test case (C-04).

Spec IDs realized here (§11): R-05, R-16, C-04, I-002, K-08, E-05, E-06, E-07, E-24, E-27.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

from .attribute import TestCase

OUTCOMES = ("passed", "failed", "error", "skipped")
_WORST_ORDER = {"error": 3, "failed": 2, "skipped": 1, "passed": 0}


class ResultsError(Exception):
    """E-05 -> exit 3; the message is `results: <reason>`."""


@dataclass(frozen=True)
class RawResult:
    classname: str
    name: str
    outcome: str

    @property
    def join_name(self) -> str:
        if self.name.endswith("]") and "[" in self.name:
            return self.name[: self.name.index("[")]
        return self.name

    @property
    def param(self) -> str | None:
        if self.name.endswith("]") and "[" in self.name:
            return self.name[self.name.index("[") + 1 : -1]
        return None


@dataclass
class CaseOutcome:
    outcome: str
    results: list[RawResult] = field(default_factory=list)


@dataclass
class ResultsMap:
    outcomes: dict[TestCase, CaseOutcome]
    unattributed: list[RawResult]
    notes: list[str]
    joined: int


def worst(outcomes: list[str]) -> str:
    return max(outcomes, key=lambda o: _WORST_ORDER[o])


def parse_junit(data: bytes) -> list[RawResult]:
    """Every <testcase> below a <testsuites>/<testsuite> root. Raises ResultsError (E-05)."""
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise ResultsError(f"results: malformed XML ({exc})") from None
    tag = root.tag.rsplit("}", 1)[-1]
    if tag not in ("testsuites", "testsuite"):
        raise ResultsError(
            f"results: root element is <{tag}>, expected <testsuites> or <testsuite>"
        )
    results: list[RawResult] = []
    for node in root.iter():
        if node is root or node.tag.rsplit("}", 1)[-1] != "testcase":
            continue
        name = node.attrib.get("name")
        if name is None:
            raise ResultsError("results: <testcase> without name")
        classname = node.attrib.get("classname", "")
        child_tags = {c.tag.rsplit("}", 1)[-1] for c in node}
        if "failure" in child_tags:
            outcome = "failed"
        elif "error" in child_tags:
            outcome = "error"
        elif "skipped" in child_tags:
            outcome = "skipped"
        else:
            outcome = "passed"
        results.append(RawResult(classname, name, outcome))
    return results


def _suffix_matches(case_classname: str, result_classname: str) -> bool:
    if result_classname == "":
        return True
    return case_classname == result_classname or case_classname.endswith("." + result_classname)


def _common_suffix_len(a: str, b: str) -> int:
    pa, pb = a.split("."), b.split(".")
    n = 0
    while n < len(pa) and n < len(pb) and pa[-1 - n] == pb[-1 - n]:
        n += 1
    return n


def join_results(results: list[RawResult], cases: list[TestCase]) -> ResultsMap:
    """Join each result to a TestCase per C-04 (longest common dotted suffix; ties unattributed)."""
    by_name: dict[str, list[TestCase]] = {}
    for case in cases:
        if case.is_file_level:
            continue  # E-13: a file-level case has no outcome by construction
        by_name.setdefault(case.name, []).append(case)

    outcomes: dict[TestCase, CaseOutcome] = {}
    unattributed: list[RawResult] = []
    notes: list[str] = []
    seen_keys: dict[tuple[str, str], int] = {}
    joined = 0
    for result in results:
        key = (result.classname, result.name)
        seen_keys[key] = seen_keys.get(key, 0) + 1
        candidates = [
            c
            for c in by_name.get(result.join_name, [])
            if _suffix_matches(c.classname, result.classname)
        ]
        if not candidates:
            unattributed.append(result)
            continue
        if result.classname == "":
            best = candidates
        else:
            scored = [(_common_suffix_len(c.classname, result.classname), c) for c in candidates]
            top = max(s for s, _ in scored)
            best = [c for s, c in scored if s == top]
        if len(best) > 1:
            unattributed.append(result)
            names = ", ".join(
                f"{c.file}::{c.name}" for c in sorted(best, key=lambda c: (c.file, c.name))
            )
            notes.append(f"ambiguous result {result.classname}::{result.name}: candidates {names}")
            continue
        case = best[0]
        entry = outcomes.setdefault(case, CaseOutcome(result.outcome))
        entry.results.append(result)
        entry.outcome = worst([r.outcome for r in entry.results])
        joined += 1
    for (classname, name), count in sorted(seen_keys.items()):
        if count > 1:
            notes.append(f"duplicate result {classname}::{name}: {count} occurrences")
    for entry in outcomes.values():
        entry.results.sort(key=lambda r: r.name)
    unattributed.sort(key=lambda r: (r.classname, r.name))
    return ResultsMap(outcomes, unattributed, notes, joined)
