"""Grapher: ID -> source-file / ID -> test-case edges, the C-05 status algorithm, C-07 metrics.

Spec IDs realized here (§11): R-02, R-06, R-07, R-08, R-09, R-11, R-16, R-25, R-35, C-05, I-002,
    I-004, I-008, I-010, K-08, E-08, E-19, E-25, E-26, E-37, E-51.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_EVEN, Context, Decimal

from .attribute import Citation, TestCase
from .extract import FAMILY_ORDER, SpecId, SpecIndex, family_rank
from .judge import JudgedVerdict
from .results import CaseOutcome, RawResult

IN_SCOPE_STATUSES = (
    "PASSING",
    "WEAKLY_PASSING",
    "FAILING",
    "SKIPPED",
    "UNVERIFIED",
    "UNTESTED",
    "UNCITED",
)
STATUSES = ("RETIRED",) + IN_SCOPE_STATUSES

_QUANT = Decimal("0.0001")
_CTX = Context(prec=28, rounding=ROUND_HALF_EVEN)


def ratio(numerator: int, denominator: int) -> Decimal | None:
    """C-07 Numbers (Q-009): Decimal division at 28 digits, quantized to 4 places, half-even;
    None when the denominator is zero (I-008)."""
    if denominator == 0:
        return None
    value = _CTX.divide(Decimal(numerator), Decimal(denominator))
    return value.quantize(_QUANT, rounding=ROUND_HALF_EVEN, context=_CTX)


@dataclass
class TestEdge:
    case: TestCase
    lines: list[int]
    outcome: str | None  # None -> unrun (E-08)
    results: list[RawResult]
    verdict: JudgedVerdict | None = None  # None -> not judged (Q-001)


@dataclass
class IdRecord:
    spec: SpecId
    status: str
    src: list[tuple[str, list[int]]] = field(default_factory=list)
    tests: list[TestEdge] = field(default_factory=list)

    @property
    def id(self) -> str:
        return self.spec.id

    @property
    def unrun(self) -> list[TestEdge]:
        return [t for t in self.tests if t.outcome is None]


@dataclass
class Graph:
    records: list[IdRecord]
    dangling: list[Citation]
    stale: list[Citation]
    judge_enabled: bool = False


def deterministic_status(
    spec: SpecId, src: list, tests: list[TestEdge], results_given: bool
) -> str:
    """C-05 steps 1-4."""
    if spec.retired:
        return "RETIRED"
    if not tests:
        if spec.family != "T" and not src:
            return "UNCITED"
        if spec.family == "T":
            return "UNCITED"  # F-001: source citations are evidence only
        return "UNTESTED"
    outcomes = [t.outcome for t in tests if t.outcome is not None]
    if not results_given or not outcomes:
        return "UNVERIFIED"
    if any(o in ("failed", "error") for o in outcomes):
        return "FAILING"
    if all(o == "skipped" for o in outcomes):
        return "SKIPPED"
    return "PASSING"


def build_graph(
    index: SpecIndex,
    src_citations: list[Citation],
    test_citations: list[Citation],
    outcomes: dict[TestCase, CaseOutcome],
    results_given: bool,
) -> Graph:
    declared = index.by_id()
    dangling: list[Citation] = []
    stale: list[Citation] = []
    src_by_id: dict[str, dict[str, list[int]]] = {}
    tests_by_id: dict[str, dict[TestCase, list[int]]] = {}
    for cit in list(src_citations) + list(test_citations):
        spec = declared.get(cit.id)
        if spec is None:
            dangling.append(cit)
            continue
        if spec.retired:
            stale.append(cit)
            continue
        if cit.kind == "src":
            src_by_id.setdefault(cit.id, {}).setdefault(cit.file, []).append(cit.line)
        else:
            assert cit.testcase is not None
            tests_by_id.setdefault(cit.id, {}).setdefault(cit.testcase, []).append(cit.line)

    records: list[IdRecord] = []
    for spec in index.ids:
        src = [(f, sorted(set(lines))) for f, lines in sorted(src_by_id.get(spec.id, {}).items())]
        tests: list[TestEdge] = []
        for case, lines in tests_by_id.get(spec.id, {}).items():
            outcome = outcomes.get(case)
            tests.append(
                TestEdge(
                    case,
                    sorted(set(lines)),
                    outcome.outcome if outcome else None,
                    list(outcome.results) if outcome else [],
                )
            )
        tests.sort(key=lambda t: (t.case.file, t.case.start, t.case.name))
        status = deterministic_status(spec, src, tests, results_given)
        records.append(IdRecord(spec, status, src, tests))

    def cit_key(c: Citation) -> tuple[str, int, str]:
        return (c.file, c.line, c.testcase.name if c.testcase else "")

    dangling.sort(key=cit_key)
    stale.sort(key=cit_key)
    return Graph(records, dangling, stale)


def eligible_edges(graph: Graph) -> list[tuple[IdRecord, TestEdge]]:
    """I-010: edges of PASSING IDs (after step 4) whose test outcome is `passed` — never an edge
    of a RECORDED id (R-35)."""
    out: list[tuple[IdRecord, TestEdge]] = []
    for rec in graph.records:
        if rec.status != "PASSING" or rec.spec.recorded:
            continue
        for edge in rec.tests:
            if edge.outcome == "passed":
                out.append((rec, edge))
    return out


def apply_verdicts(graph: Graph, verdicts: dict[tuple[TestCase, str], JudgedVerdict]) -> None:
    """C-05 step 5: the only place verdicts influence anything (R-11, I-004)."""
    graph.judge_enabled = True
    for rec in graph.records:
        if rec.status != "PASSING" or rec.spec.recorded:  # R-35: recorded ids skip step 5
            continue
        collected: list[str] = []
        for edge in rec.tests:
            if edge.outcome != "passed":
                continue
            verdict = verdicts.get((edge.case, rec.id))
            if verdict is None:
                continue
            edge.verdict = verdict
            collected.append(verdict.verdict)
        if (
            collected
            and "ASSERTS" not in collected
            and any(v in ("EXECUTES_ONLY", "UNRELATED") for v in collected)
        ):
            rec.status = "WEAKLY_PASSING"


@dataclass
class Metrics:
    declared: int
    retired: int
    in_scope: int
    by_status: dict[str, int]
    passing: int
    conformance: Decimal | None
    by_family: dict[str, dict]
    judge_strength_ratio: str | None
    judge_strength: Decimal | None
    unknown_rate: Decimal | None
    judged_edges: int
    unknown_edges: int


def compute_metrics(graph: Graph) -> Metrics:
    """C-07 metrics with the zero-denominator rules (R-09, I-008)."""
    records = graph.records
    declared = len(records)
    retired = sum(1 for r in records if r.status == "RETIRED")
    in_scope = declared - retired
    by_status = {s: sum(1 for r in records if r.status == s) for s in IN_SCOPE_STATUSES}
    passing = by_status["PASSING"]
    by_family: dict[str, dict] = {}
    for fam in FAMILY_ORDER:
        fam_records = [r for r in records if r.spec.family == fam and r.status != "RETIRED"]
        fam_passing = sum(1 for r in fam_records if r.status == "PASSING")
        by_family[fam] = {
            "in_scope": len(fam_records),
            "passing": fam_passing,
            "ratio": ratio(fam_passing, len(fam_records)),
        }
    judged = 0
    unknown = 0
    strength_ratio = None
    strength = None
    unknown_rate = None
    if graph.judge_enabled:
        for rec in records:
            for edge in rec.tests:
                if edge.verdict is not None:
                    judged += 1
                    if edge.verdict.verdict == "UNKNOWN":
                        unknown += 1
        weak = by_status["WEAKLY_PASSING"]
        # C-07: judge_strength is over PASSING \ RECORDED — a recorded id is PASSING without a
        # judged edge and is outside the population (F-405); conformance keeps it
        judged_passing = sum(1 for r in records if r.status == "PASSING" and not r.spec.recorded)
        strength_ratio = f"{judged_passing}/{judged_passing + weak}"
        strength = ratio(judged_passing, judged_passing + weak)
        unknown_rate = ratio(unknown, judged)
    return Metrics(
        declared,
        retired,
        in_scope,
        by_status,
        passing,
        ratio(passing, in_scope),
        by_family,
        strength_ratio,
        strength,
        unknown_rate,
        judged,
        unknown,
    )


def sort_records(records: list[IdRecord]) -> list[IdRecord]:
    return sorted(records, key=lambda r: (family_rank(r.spec.family), r.spec.number))
