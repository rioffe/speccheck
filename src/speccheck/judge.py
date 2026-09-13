"""Judge kernel (C-06): request/verdict types, validation of every provider answer, and the
runner that issues at most one call per edge (I-010) under the K-06 / K-12 limits.

The judge may only ever make the news worse: its output is consumed solely by C-05 step 5.

Spec IDs realized here (§11): R-10, R-30, C-06, C-11, I-005, I-010, K-07, K-12, K-13, E-14, E-15,
    E-16, E-17, E-35, E-36, E-40, E-41.
"""

from __future__ import annotations

import json
import logging
import math
import threading
import time
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor, wait
from dataclasses import dataclass
from typing import Protocol, TextIO

from .attribute import TestCase

log = logging.getLogger("speccheck")

VERDICTS = ("ASSERTS", "EXECUTES_ONLY", "UNRELATED", "UNKNOWN")
RATIONALE_MAX = 280  # K-07
POLL_INTERVAL = 0.25  # seconds; timed waits keep the main thread interruptible (E-41)


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


class JudgeInterrupted(Exception):
    """The run was interrupted while this request was in flight (E-41); its verdict is never
    recorded, so the class only needs to unwind the worker promptly."""


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


# --------------------------------------------------------------------------------------------
# progress indicator (R-30, C-11, K-13)
# --------------------------------------------------------------------------------------------

BAR_CELLS = 20  # C-11
DRAW_MIN_INTERVAL = 0.1  # K-13: never more than 10 draws per second; a verdict shows within 100 ms
TICK_INTERVAL = 1.0  # K-13: at least one draw per second while requests are in flight


def _mmss(seconds: float) -> str:
    """C-11: durations floored to whole seconds, rendered M:SS with unbounded minutes."""
    whole = int(math.floor(seconds))
    return f"{whole // 60}:{whole % 60:02d}"


def progress_line(done: int, total: int, elapsed: float) -> str:
    """The C-11 <line> (before padding) for d = done, n = total, t = elapsed seconds."""
    k = BAR_CELLS * done // total
    bar = "#" * k + "-" * (BAR_CELLS - k)
    left = "?:??" if done == 0 else _mmss(elapsed / done * (total - done))
    return f"judge: [{bar}] {done}/{total} edges  {_mmss(elapsed)} elapsed  ~{left} left"


class ProgressLine:
    """One in-place stderr line for the judge stage (C-11), written directly to the stream —
    never through the logger — as single atomic writes serialized by a lock (K-13).

    Draws are padded to the widest line drawn so far and redrawn with a bare "\r", so no
    terminal escape is needed and a shrinking `left` leaves no residue; the erase is "\r",
    W spaces, "\r" (F-205). A background thread provides the 1 s tick and coalesces bursts of
    verdicts into at most one draw per 100 ms. Used as a context manager: the first draw
    (d = 0, 0:00 elapsed) happens on entry, and the erase on exit — on an exception too, without
    the final-state draw, so an interrupt (E-40, E-41) never leaves a partial line behind.
    """

    def __init__(
        self, stream: TextIO, total: int, clock: Callable[[], float] = time.monotonic
    ) -> None:
        self.stream = stream
        self.total = total
        self.clock = clock
        self.done = 0
        self.width = 0
        self.t0 = 0.0
        self.last_draw = -math.inf
        self.drawn_done = -1
        self._lock = threading.Lock()
        self._kick = threading.Event()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="speccheck-progress", daemon=True)

    def __enter__(self) -> ProgressLine:
        self.t0 = self.clock()
        self._draw()
        self._thread.start()
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self._stop.set()
        self._kick.set()
        self._thread.join()
        with self._lock:
            if exc_type is None and self.drawn_done != self.done:
                self._sleep_for_rate_limit()
                self._draw_locked()
            self.stream.write("\r" + " " * self.width + "\r")
            self.stream.flush()

    def advance(self) -> None:
        """One more verdict determined (received, coerced, or budget-skipped)."""
        with self._lock:
            self.done += 1
        self._kick.set()

    def _run(self) -> None:
        while not self._stop.is_set():
            self._kick.wait(TICK_INTERVAL)
            if self._stop.is_set():
                return
            self._kick.clear()
            self._sleep_for_rate_limit()
            if self._stop.is_set():
                return
            self._draw()

    def _sleep_for_rate_limit(self) -> None:
        delay = DRAW_MIN_INTERVAL - (self.clock() - self.last_draw)
        if delay > 0:
            time.sleep(delay)

    def _draw(self) -> None:
        with self._lock:
            self._draw_locked()

    def _draw_locked(self) -> None:
        line = progress_line(self.done, self.total, self.clock() - self.t0)
        self.width = max(self.width, len(line))
        self.stream.write("\r" + line + " " * (self.width - len(line)))
        self.stream.flush()
        self.last_draw = self.clock()
        self.drawn_done = self.done


@dataclass
class JudgeRun:
    verdicts: dict[tuple[TestCase, str], JudgedVerdict]
    available: bool
    budget_unjudged: int

    def notes(self) -> list[str]:
        if self.budget_unjudged:
            return [f"judge budget exhausted: {self.budget_unjudged} edge(s) unjudged"]
        return []


class _NoProgress:
    def __enter__(self) -> None:
        return None

    def __exit__(self, *_exc: object) -> None:
        return None


def run_judge(
    provider: Judge,
    requests: list[JudgeRequest],
    *,
    concurrency: int = 1,
    budget_seconds: int = 0,
    clock: Callable[[], float] = time.monotonic,
    progress: ProgressLine | None = None,
) -> JudgeRun:
    """Judge every request exactly once (I-010). K-06: at most `concurrency` in flight.
    K-12: no request is issued at or after `start + budget`; in-flight requests complete.
    R-30: `progress`, if given, is advanced once per determined verdict; it is entered before
    the first request is issued and exited (erased) when the stage ends, exception or not."""
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
            verdict = _unknown("judge: budget", call_made=False)
        else:
            verdict = judge_edge(provider, req)
        if progress is not None:
            progress.advance()
        return req, verdict

    results: list[tuple[JudgeRequest, JudgedVerdict]]
    abort = getattr(provider, "abort", None)  # E-41: LlmJudge exposes a threading.Event
    with progress if progress is not None else _NoProgress():
        if concurrency <= 1:
            results = [work(r) for r in requests]
        else:
            pool = ThreadPoolExecutor(max_workers=concurrency)
            try:
                # Poll with a timeout rather than block on each result: an untimed lock wait is
                # not interruptible by SIGINT on every platform (macOS CPython), so a bare
                # pool.map() would only notice Ctrl-C once a request happened to finish.
                futures = [pool.submit(work, r) for r in requests]
                pending = set(futures)
                while pending:
                    done, pending = wait(pending, timeout=POLL_INTERVAL)
                    for f in done:
                        exc = f.exception()
                        if exc is not None:
                            raise exc
                results = [f.result() for f in futures]
            except BaseException:
                # E-41: an interrupt (or any failure) in the main thread must not wait for the
                # in-flight requests — tell every waiting worker to give up, drop the queued
                # edges, and only then join the pool, which now returns within one poll.
                if abort is not None:
                    abort.set()
                pool.shutdown(wait=True, cancel_futures=True)
                raise
            pool.shutdown(wait=True)

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
