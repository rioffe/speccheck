"""Judge kernel (C-06): request/verdict types, validation of every provider answer, and the
runner that issues at most one call per edge (I-010) under the K-06 / K-12 limits.

The judge may only ever make the news worse: its output is consumed solely by C-05 step 5.

Spec IDs realized here (§11): R-10, C-06, I-005, I-010, K-07, K-12, E-14, E-15, E-16, E-17, E-35,
    E-36.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Protocol

from .attribute import TestCase

log = logging.getLogger("speccheck")

VERDICTS = ("ASSERTS", "EXECUTES_ONLY", "UNRELATED", "UNKNOWN")
RATIONALE_MAX = 280  # K-07


@dataclass(frozen=True)
class JudgeRequest:
    id: str
    statement: str
    testcase: TestCase
    source: str  # lines start..end, each prefixed "<lineno>\t" (F-109)

    def to_json(self) -> str:
        """The user-message payload (C-06): {id, statement, file, start, end, source}."""
        return json.dumps(
            {
                "id": self.id,
                "statement": self.statement,
                "file": self.testcase.file,
                "start": self.testcase.start,
                "end": self.testcase.end,
                "source": self.source,
            },
            indent=2,
            ensure_ascii=False,
        )


@dataclass(frozen=True)
class Evidence:
    file: str
    line: int


@dataclass(frozen=True)
class Verdict:
    verdict: str
    evidence: tuple[Evidence, ...]
    rationale: str


@dataclass(frozen=True)
class JudgedVerdict:
    """A validated verdict as recorded in the report."""

    verdict: str
    evidence: tuple[Evidence, ...]
    rationale: str
    coerced: bool
    call_failed: bool = False  # E-14 class of failure (feeds judge_available)
    call_made: bool = True


class Judge(Protocol):
    def judge(self, req: JudgeRequest) -> Verdict: ...


class JudgeUnavailable(Exception):
    """Provider unreachable (E-14)."""


class JudgeTimeout(Exception):
    """Provider timed out (K-05, E-14)."""


class JudgeHttpError(Exception):
    """Provider returned HTTP >= 400 (E-14)."""

    def __init__(self, status: int) -> None:
        super().__init__(f"http {status}")
        self.status = status


class JudgeMalformed(Exception):
    """Provider returned non-JSON or JSON lacking `verdict` (E-15)."""


def numbered_source(lines: Iterable[str], start: int, end: int) -> str:
    """The span start..end, each line prefixed by its absolute 1-based number and one TAB."""
    out = []
    for lineno, text in enumerate(lines, start=1):
        if start <= lineno <= end:
            out.append(f"{lineno}\t{text}")
    return "\n".join(out)


def build_request(
    ident: str, statement: str, case: TestCase, file_lines: Iterable[str]
) -> JudgeRequest:
    return JudgeRequest(ident, statement, case, numbered_source(file_lines, case.start, case.end))


def clean_rationale(text: str) -> str:
    """K-07: single line, at most 280 characters (277 + '...')."""
    single = " ".join(str(text).splitlines())
    if len(single) > RATIONALE_MAX:
        return single[: RATIONALE_MAX - 3] + "..."
    return single


def _unknown(rationale: str, *, call_failed: bool = False, call_made: bool = True) -> JudgedVerdict:
    return JudgedVerdict(
        "UNKNOWN", (), rationale, True, call_failed=call_failed, call_made=call_made
    )


def validate(raw: Verdict, req: JudgeRequest) -> JudgedVerdict:
    """The C-06 validation applied to every provider's answer (I-005)."""
    if raw.verdict not in VERDICTS:
        return _unknown("judge: malformed response")
    case = req.testcase
    for ev in raw.evidence:
        if ev.file != case.file or not (case.start <= ev.line <= case.end):
            return _unknown("judge: ungrounded")
    if raw.verdict == "ASSERTS" and not raw.evidence:
        return _unknown("judge: ungrounded")
    evidence = tuple(sorted(set(raw.evidence), key=lambda e: (e.file, e.line)))
    return JudgedVerdict(raw.verdict, evidence, clean_rationale(raw.rationale), False)


def judge_edge(provider: Judge, req: JudgeRequest) -> JudgedVerdict:
    """One provider call, mapped to a validated verdict; never raises."""
    log.debug("judge> %s", req.to_json())
    try:
        raw = provider.judge(req)
    except JudgeTimeout:
        return _unknown("judge: timeout", call_failed=True)
    except JudgeHttpError as exc:
        return _unknown(f"judge: http {exc.status}", call_failed=True)
    except JudgeMalformed:
        return _unknown("judge: malformed response")
    except Exception:  # noqa: BLE001 - E-14: any other failure is "unavailable"
        return _unknown("judge: unavailable", call_failed=True)
    if not isinstance(raw, Verdict):
        return _unknown("judge: malformed response")
    return validate(raw, req)


@dataclass
class JudgeRun:
    verdicts: dict[tuple[TestCase, str], JudgedVerdict]
    available: bool
    budget_unjudged: int

    def notes(self) -> list[str]:
        if self.budget_unjudged:
            return [f"judge budget exhausted: {self.budget_unjudged} edge(s) unjudged"]
        return []


def run_judge(
    provider: Judge,
    requests: list[JudgeRequest],
    *,
    concurrency: int = 1,
    budget_seconds: int = 0,
    clock: Callable[[], float] = time.monotonic,
) -> JudgeRun:
    """Judge every request exactly once (I-010). K-06: at most `concurrency` in flight.
    K-12: no request is issued at or after `start + budget`; in-flight requests complete."""
    verdicts: dict[tuple[TestCase, str], JudgedVerdict] = {}
    if not requests:
        return JudgeRun(verdicts, True, 0)
    lock = threading.Lock()
    state = {"deadline": None}

    def work(req: JudgeRequest) -> tuple[JudgeRequest, JudgedVerdict]:
        with lock:
            if budget_seconds > 0 and state["deadline"] is None:
                state["deadline"] = clock() + budget_seconds
            deadline = state["deadline"]
        if deadline is not None and clock() >= deadline:
            return req, _unknown("judge: budget", call_made=False)
        return req, judge_edge(provider, req)

    results: list[tuple[JudgeRequest, JudgedVerdict]]
    if concurrency <= 1:
        results = [work(r) for r in requests]
    else:
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            results = list(pool.map(work, requests))

    calls_made = 0
    calls_ok = 0
    budget_unjudged = 0
    for req, verdict in results:
        verdicts[(req.testcase, req.id)] = verdict
        if not verdict.call_made:
            budget_unjudged += 1
            continue
        calls_made += 1
        if not verdict.call_failed:
            calls_ok += 1
    available = calls_made == 0 or calls_ok > 0
    return JudgeRun(verdicts, available, budget_unjudged)
