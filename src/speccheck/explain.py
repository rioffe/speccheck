"""`explain` trace renderer (C-18; v1.17).

One id's evidence trail, rendered from the facts a `check` run already holds: the `IdRecord`
(status, source citations, test edges with their outcomes and verdicts), the statement, and the
`impact` walk's own results. Pure: no clock, no filesystem, no environment, no network — the trace
is a function of its arguments, which is what makes two runs byte-identical (I-002, I-016) and what
keeps `explain` additive and read-only (it writes nothing, R-40/D-33).
"""

from __future__ import annotations

from .graph import IdRecord
from .impact import ReverifyEntry, WalkResult
from .judge import JudgedVerdict

NO_RESULT = "\u2014"  # C-18: no result joined (the C-08 report's em dash)
NOT_JUDGED = "not judged"  # C-18: no verdict recorded for this edge
FILE_LEVEL = "(file-level)"  # C-18: a case with no name (E-13)
INDENT = "  "

# C-18: the C-05 step that set each status, in C-05's own words.
REASON = {
    "UNCITED": "step 1: no source or test citation",
    "UNTESTED": "step 2: no test citation",
    "UNVERIFIED": "step 2b: no citing test case has a result",
    "FAILING": "step 3: a citing test case failed",
    "SKIPPED": "step 3: a citing test case was skipped",
    "PASSING": "step 4: every citing test case passed",
    "WEAKLY_PASSING": "step 5: the judge downgraded every judged edge",
    "RETIRED": "retired: struck through in the specification",
}


def _id_line(rec: IdRecord) -> str:
    """C-18 section 1: the id with its `RETIRED` / `recorded` markers."""
    markers = ""
    if rec.spec.retired:
        markers += " (RETIRED)"
    if rec.spec.recorded:
        markers += " (recorded)"
    return f"ID {rec.spec.id}{markers}"


def _status_line(rec: IdRecord) -> str:
    """C-18 section 2: the status and the C-05 step that set it."""
    return f"status: {rec.status} ({REASON[rec.status]})"


def _statement_lines(rec: IdRecord) -> list[str]:
    """C-18 section 3: `SpecId.text` (C-10), every line indented by two spaces."""
    return ["statement:"] + [INDENT + line for line in rec.spec.text.split("\n")]


def _source_lines(rec: IdRecord) -> list[str]:
    """C-18 section 4: one `file:line` per source citation, ascending."""
    out = ["sources:"]
    for file, lines in rec.src:  # IdRecord.src: [(file, [line, ...])] in ascending order
        for line in lines:
            out.append(f"{INDENT}{file}:{line}")
    return out


def _verdict_marker(verdict: JudgedVerdict | None) -> str:
    """C-18: the C-06 token, ` (coerced)` when it was coerced, or `not judged` when absent."""
    if verdict is None:
        return NOT_JUDGED
    token = verdict.verdict
    if verdict.coerced:
        token += " (coerced)"
    return token


def _test_lines(rec: IdRecord) -> list[str]:
    """C-18 section 5: one line per citing test case, ascending by (file, start), plus the
    `clause:`/`rationale:` lines a recorded verdict carries."""
    out = ["tests:"]
    for edge in rec.tests:
        case = edge.case
        label = f"{case.file}::{case.name}" if case.name else f"{case.file} {FILE_LEVEL}"
        out.append(
            f"{INDENT}{label} ({edge.outcome or NO_RESULT}) [{_verdict_marker(edge.verdict)}]"
        )
        if edge.verdict is not None:
            if edge.verdict.clause:
                out.append(f"{INDENT}{INDENT}clause: {edge.verdict.clause}")
            out.append(f"{INDENT}{INDENT}rationale: {edge.verdict.rationale}")
    return out


def _impact_lines(
    walk: WalkResult, reverify: tuple[ReverifyEntry, ...], depth: int
) -> list[str]:
    """C-18 section 6: the C-12 walk from this id and the C-13 reverify set, in their own order."""
    out = [f"impact ({depth}):"]
    for entry in walk.impact:
        via = entry.via
        out.append(
            f"{INDENT}{entry.id} (depth {entry.depth}, "
            f"via {via.src} -{via.kind}-> {via.dst})"
        )
    for entry in reverify:
        out.append(f"{INDENT}{entry.id} verifies {', '.join(entry.verifies)}")
    return out


def render_trace(
    rec: IdRecord,
    walk: WalkResult,
    reverify: tuple[ReverifyEntry, ...],
    depth: int,
) -> str:
    """C-18: the whole trace for one id, ending in exactly one `\\n`."""
    lines = [_id_line(rec), _status_line(rec)]
    lines += _statement_lines(rec)
    lines += _source_lines(rec)
    lines += _test_lines(rec)
    lines += _impact_lines(walk, reverify, depth)
    return "\n".join(lines) + "\n"
