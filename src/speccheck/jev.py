"""Jev triage provider (C-17) and the triage pass (K-16), v1.15.

One task per judge-eligible edge, sent to the C-17 endpoint before any real-judge request is
issued; the answer is read once, for ordering, and then discarded. Nothing here produces a
`Verdict`, writes a report field, or affects a status (I-015): the module exposes a confidence
per edge and an issue order, and the reporter cannot see it.

The request is the one `tools/judge_crosscheck_tasks.py` already builds — the C-06 request object
for the edge rendered by C-17's `state` template — so the calibration figures the spec's v1.15
rows cite were measured on the same input this module sends.

Spec IDs realized here (§11): C-17, K-16, I-015, E-59 (v1.15).
"""

from __future__ import annotations

import json
import logging
import queue
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor, wait
from dataclasses import dataclass
from typing import Protocol

from .judge import VERDICTS, JudgeRequest

log = logging.getLogger("speccheck")

ENV_URL = "SPECCHECK_JEV_URL"
ENV_MODEL = "SPECCHECK_JEV_MODEL"
ENV_KEY = "SPECCHECK_JEV_API_KEY"
ENV_TIMEOUT = "SPECCHECK_JEV_TIMEOUT"
DEFAULT_URL = "https://openrouter.ai/api/alpha/decisions"
# C-17: OpenRouter's floating alias, not the pinned typesafe/jev-1.13 the proposal's §1
# calibration was measured against; SPECCHECK_JEV_MODEL pins it when the measured behaviour
# must be held fixed.
DEFAULT_MODEL = "~typesafe/jev-latest"
REDACTED = "***"
POLL_INTERVAL = 0.25  # seconds between checks of the deadline and the abort flag (E-41)

# post(url, headers, body_bytes, timeout_seconds) -> (status_code, response_text)
PostFn = Callable[[str, Mapping[str, str], bytes, float], tuple[int, str]]

# C-17's pinned question. `state` is the only place the statement and the test span appear.
INSTRUCTIONS = (
    "Does any assertion in this test case check any clause of the statement? "
    "Choose exactly one option."
)
CRITERIA = {
    "ASSERTS": (
        "The test contains at least one assertion whose expected value or condition "
        "corresponds to a clause of the statement."
    ),
    "EXECUTES_ONLY": (
        "The test runs code the statement describes, but no assertion checks it "
        "(assertions absent, trivial, or about something else)."
    ),
    "UNRELATED": "The test does not exercise any clause of the statement.",
    "UNKNOWN": "Cannot decide from the source given. Prefer this over guessing.",
}
assert set(CRITERIA) == set(VERDICTS)  # stay in lockstep with the C-06 vocabulary (C-17)


class JevConfigError(Exception):
    """C-17 violation -> usage error (exit 2). The message never carries the key (I-007)."""


@dataclass(frozen=True)
class JevConfig:
    url: str
    model: str
    api_key: str
    timeout: int = 30

    @classmethod
    def from_env(cls, environ: Mapping[str, str]) -> JevConfig:
        """C-17: URL and MODEL optional with defaults, API_KEY required, TIMEOUT 1..300."""
        if not environ.get(ENV_KEY):
            raise JevConfigError(f"--jev-pre-triage requires environment variable {ENV_KEY}")
        timeout_text = environ.get(ENV_TIMEOUT, "30")
        try:
            timeout = int(timeout_text)
        except ValueError:
            raise JevConfigError(f"{ENV_TIMEOUT} must be an integer in 1..300") from None
        if not 1 <= timeout <= 300:
            raise JevConfigError(f"{ENV_TIMEOUT} must be an integer in 1..300")
        return cls(
            environ.get(ENV_URL) or DEFAULT_URL,
            environ.get(ENV_MODEL) or DEFAULT_MODEL,
            environ[ENV_KEY],
            timeout,
        )

    def redacted(self) -> str:
        return f"url={self.url} model={self.model} api_key={REDACTED} timeout={self.timeout}"


def render_state(req: JudgeRequest) -> str:
    """C-17's `state` template, applied to the C-06 request object for this edge."""
    payload = json.loads(req.to_json())
    return (
        f"Specification obligation {payload['id']}.\n\n"
        f"Statement:\n{payload['statement']}\n\n"
        f"Test file {payload['file']}, lines {payload['start']}-{payload['end']}:\n"
        f"{payload['source']}"
    )


def build_body(req: JudgeRequest, model: str) -> bytes:
    """C-17's request body: exactly `{model, state, questions}` — no clause, no evidence."""
    payload = {
        "model": model,
        "state": render_state(req),
        "questions": {
            "verdict": {"type": "choice", "instructions": INSTRUCTIONS, "criteria": CRITERIA}
        },
    }
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def parse_confidence(text: str) -> float | None:
    """`answers.verdict` -> $p(e) = \\max \\mathrm{probabilities}$, or None when the reply is not
    USABLE (C-17) — the per-edge failure E-59 records, never an exception."""
    try:
        envelope = json.loads(text)
        answer = envelope["answers"]["verdict"]
        choice = answer["choice"]
        probabilities = answer["probabilities"]
    except (ValueError, TypeError, KeyError):
        return None
    if choice not in VERDICTS or not isinstance(probabilities, dict) or not probabilities:
        return None
    values = list(probabilities.values())
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in values):
        return None
    return float(max(values))


def _httpx_post(
    url: str, headers: Mapping[str, str], body: bytes, timeout: float
) -> tuple[int, str]:
    """Default transport: one synchronous POST, run in a daemon thread by `confidence` so the
    timeout is a wall-clock bound the calling thread can poll (K-05's shape, C-17's TIMEOUT)."""
    import httpx  # [llm] extra; lazy so the kernel never imports it

    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, content=body, headers=dict(headers))
    except httpx.TimeoutException:
        raise TimeoutError("jev: timeout") from None
    return resp.status_code, resp.text


class JevTriage:
    """The C-17 provider: one confidence per edge, or None when the edge's request failed."""

    def __init__(self, config: JevConfig, post: PostFn | None = None) -> None:
        self.config = config
        self._post = post or _httpx_post
        # E-41: set by run_triage when the run is interrupted, so a waiting call returns at the
        # next poll instead of sitting out the rest of its request.
        self.abort = threading.Event()

    def headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
        }

    def _post_with_deadline(self, req: JudgeRequest) -> tuple[int, str]:
        timeout = float(self.config.timeout)
        out: queue.Queue[tuple[str, object]] = queue.Queue(maxsize=1)
        args = (self.config.url, self.headers(), build_body(req, self.config.model), timeout)

        def run() -> None:
            try:
                out.put(("ok", self._post(*args)))
            except BaseException as exc:  # noqa: BLE001 - re-raised in the calling thread
                out.put(("exc", exc))

        threading.Thread(target=run, daemon=True).start()
        deadline = time.monotonic() + timeout
        while True:
            if self.abort.is_set():
                raise InterruptedError("jev: interrupted")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("jev: timeout")
            try:
                kind, payload = out.get(timeout=min(POLL_INTERVAL, remaining))
                break
            except queue.Empty:
                continue
        if kind == "exc":
            raise payload  # type: ignore[misc]
        return payload  # type: ignore[return-value]

    def confidence(self, req: JudgeRequest) -> float | None:
        """Never raises (E-59): any failure of any kind is "this edge has no usable answer"."""
        log.debug("jev> %s", render_state(req))
        try:
            status, text = self._post_with_deadline(req)
        except BaseException as exc:  # noqa: BLE001
            log.debug("jev< failed: %s", exc.__class__.__name__)
            return None
        log.debug("jev< status=%s %s", status, text.replace(self.config.api_key, REDACTED))
        if status != 200:
            return None
        return parse_confidence(text)


class TriageProvider(Protocol):
    def confidence(self, req: JudgeRequest) -> float | None: ...


# --------------------------------------------------------------------------------------------
# the triage pass (K-16)
# --------------------------------------------------------------------------------------------

FAMILY_ORDER = {family: i for i, family in enumerate("RCIKET")}  # C-07's id order


def order_key(req: JudgeRequest, confidence: float | None) -> tuple:
    """K-16: ascending $p(e)$, ties by ascending id in C-07's id order, then by (file, start) so
    the order is total even when two edges share an id; a failure sorts first."""
    family, _, number = req.id.partition("-")
    return (
        -1.0 if confidence is None else confidence,
        FAMILY_ORDER.get(family, len(FAMILY_ORDER)),
        int(number) if number.isdigit() else 0,
        req.testcase.file,
        req.testcase.start,
    )


@dataclass
class TriageRun:
    order: list[JudgeRequest]
    failures: int

    def notes(self) -> list[str]:
        """E-59: one Note naming how many edges had no usable Jev answer."""
        if self.failures:
            return [f"jev triage failed: {self.failures} edge(s) ordered first"]
        return []


def run_triage(
    provider: TriageProvider,
    requests: Sequence[JudgeRequest],
    *,
    concurrency: int = 1,
) -> TriageRun:
    """K-16: one request per eligible edge, at most `concurrency` in flight, then the ascending
    order. The answers are dropped here — only the order leaves this function (I-015)."""
    if not requests:
        return TriageRun([], 0)
    results: list[float | None]
    if concurrency <= 1:
        results = [provider.confidence(r) for r in requests]
    else:
        pool = ThreadPoolExecutor(max_workers=concurrency)
        try:
            futures = [pool.submit(provider.confidence, r) for r in requests]
            pending = set(futures)
            while pending:
                done, pending = wait(pending, timeout=POLL_INTERVAL)
                for f in done:
                    exc = f.exception()
                    if exc is not None:
                        raise exc
            results = [f.result() for f in futures]
        except BaseException:
            # E-41: an interrupt must not wait for the in-flight requests; tell every waiting
            # worker to give up, drop the queued edges, then join (now within one poll).
            abort = getattr(provider, "abort", None)
            if abort is not None:
                abort.set()
            pool.shutdown(wait=True, cancel_futures=True)
            raise
        pool.shutdown(wait=True)
    failures = sum(1 for value in results if value is None)
    paired = list(zip(requests, results, strict=True))
    paired.sort(key=lambda pair: order_key(pair[0], pair[1]))
    return TriageRun([req for req, _ in paired], failures)
