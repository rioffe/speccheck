"""LLM judge provider (C-06 wire format, C-09 configuration, C-10 instruction text).

The endpoint is an OpenAI-compatible chat-completions URL. The reference deployment is a local
Ollama server, which serves exactly this shape at http://localhost:11434/v1/chat/completions
(Ollama ignores the bearer token, but C-09 still requires one to be set).

`httpx` is imported lazily inside `_httpx_post` so that `--judge none|mock` never loads an HTTP
client (R-18, I-006).

Spec IDs realized here (§11): R-10, R-18, R-23, R-26, C-06, C-09, C-10, I-007, K-05, K-06, E-14.
"""

from __future__ import annotations

import hashlib
import json
import logging
import queue
import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from importlib import resources

from .judge import (
    Evidence,
    JudgeHttpError,
    JudgeMalformed,
    JudgeRequest,
    JudgeTimeout,
    JudgeUnavailable,
    Verdict,
)

log = logging.getLogger("speccheck")

ENV_URL = "SPECCHECK_JUDGE_URL"
ENV_MODEL = "SPECCHECK_JUDGE_MODEL"
ENV_KEY = "SPECCHECK_JUDGE_API_KEY"
ENV_TIMEOUT = "SPECCHECK_JUDGE_TIMEOUT"
REDACTED = "***"
MAX_TOKENS = 4000

# post(url, headers, body_bytes, timeout_seconds) -> (status_code, response_text)
PostFn = Callable[[str, Mapping[str, str], bytes, float], tuple[int, str]]


class LlmConfigError(Exception):
    """C-09 violation -> usage error (exit 2). The message never carries the key (R-23)."""


@dataclass(frozen=True)
class LlmConfig:
    url: str
    model: str
    api_key: str
    timeout: int = 30

    @classmethod
    def from_env(cls, environ: Mapping[str, str]) -> LlmConfig:
        missing = [name for name in (ENV_URL, ENV_MODEL, ENV_KEY) if not environ.get(name)]
        if missing:
            raise LlmConfigError(f"--judge llm requires environment variable {missing[0]}")
        timeout_text = environ.get(ENV_TIMEOUT, "30")
        try:
            timeout = int(timeout_text)
        except ValueError:
            raise LlmConfigError(f"{ENV_TIMEOUT} must be an integer in 1..300") from None
        if not 1 <= timeout <= 300:
            raise LlmConfigError(f"{ENV_TIMEOUT} must be an integer in 1..300")
        return cls(environ[ENV_URL], environ[ENV_MODEL], environ[ENV_KEY], timeout)

    def redacted(self) -> str:
        return f"url={self.url} model={self.model} api_key={REDACTED} timeout={self.timeout}"


def load_prompt() -> str:
    """The C-10 text, shipped as package data."""
    return resources.files("speccheck").joinpath("judge_prompt.md").read_text(encoding="utf-8")


def prompt_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _httpx_post(
    url: str, headers: Mapping[str, str], body: bytes, timeout: float
) -> tuple[int, str]:
    """Default transport. K-05: one wall-clock deadline from issue to full body received."""
    import httpx  # [llm] extra; lazy so the kernel never imports it

    out: queue.Queue[tuple[str, object]] = queue.Queue(maxsize=1)

    def run() -> None:
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(url, content=body, headers=dict(headers))
            out.put(("ok", (resp.status_code, resp.text)))
        except httpx.TimeoutException as exc:
            out.put(("timeout", exc))
        except Exception as exc:  # noqa: BLE001
            out.put(("error", exc))

    threading.Thread(target=run, daemon=True).start()
    try:
        kind, payload = out.get(timeout=timeout)
    except queue.Empty:
        raise JudgeTimeout() from None
    if kind == "timeout":
        raise JudgeTimeout()
    if kind == "error":
        raise JudgeUnavailable(str(payload.__class__.__name__))
    return payload  # type: ignore[return-value]


def strip_fence(text: str) -> str:
    """Strip surrounding whitespace and ONE enclosing ``` / ```json fence, if present."""
    text = text.strip()
    if text.startswith("```") and text.endswith("```") and len(text) >= 6:
        inner = text[3:-3]
        first_nl = inner.find("\n")
        if first_nl >= 0:
            info = inner[:first_nl].strip()
            if info == "" or info.isalnum():
                inner = inner[first_nl + 1 :]
        return inner.strip()
    return text


def parse_answer(text: str) -> Verdict:
    """The model's text -> Verdict; anything that is not the C-06 object is JudgeMalformed."""
    try:
        obj = json.loads(strip_fence(text))
    except (ValueError, TypeError):
        raise JudgeMalformed("non-JSON") from None
    if not isinstance(obj, dict) or "verdict" not in obj:
        raise JudgeMalformed("missing verdict")
    verdict = obj.get("verdict")
    if not isinstance(verdict, str):
        raise JudgeMalformed("verdict is not a string")
    evidence: list[Evidence] = []
    raw_evidence = obj.get("evidence") or []
    if not isinstance(raw_evidence, list):
        raise JudgeMalformed("evidence is not a list")
    for item in raw_evidence:
        if not isinstance(item, dict):
            raise JudgeMalformed("evidence item is not an object")
        line = item.get("line")
        if isinstance(line, bool) or not isinstance(line, int):
            raise JudgeMalformed("evidence line is not an integer")
        evidence.append(Evidence(str(item.get("file", "")), line))
    rationale = obj.get("rationale", "")
    return Verdict(verdict, tuple(evidence), str(rationale))


class LlmJudge:
    def __init__(
        self, config: LlmConfig, prompt: str | None = None, post: PostFn | None = None
    ) -> None:
        self.config = config
        self.prompt = prompt if prompt is not None else load_prompt()
        self.prompt_sha256 = prompt_sha256(self.prompt)
        self._post = post or _httpx_post

    def body(self, req: JudgeRequest) -> bytes:
        payload = {
            "model": self.config.model,
            "temperature": 0,
            "max_tokens": MAX_TOKENS,
            "messages": [
                {"role": "system", "content": self.prompt},
                {"role": "user", "content": req.to_json()},
            ],
        }
        return json.dumps(payload, ensure_ascii=False).encode("utf-8")

    def headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
        }

    def judge(self, req: JudgeRequest) -> Verdict:
        status, text = self._post(
            self.config.url, self.headers(), self.body(req), float(self.config.timeout)
        )
        log.debug("judge< status=%s %s", status, text.replace(self.config.api_key, REDACTED))
        if status != 200:
            raise JudgeHttpError(status)
        try:
            envelope = json.loads(text)
            content = envelope["choices"][0]["message"]["content"]
        except (ValueError, TypeError, KeyError, IndexError):
            raise JudgeMalformed("missing choices[0].message.content") from None
        if not isinstance(content, str):
            raise JudgeMalformed("content is not text")
        return parse_answer(content)
