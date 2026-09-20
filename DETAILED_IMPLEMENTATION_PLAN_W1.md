# W1 — C-17: the Jev provider contract, and the CLI grammar it is gated by

## 1. Ids discharged

C-17 (the four variables, the request body and `state` template, the `answers.verdict` parse and
$p(e)$, the USABLE rule), E-58 (`--judge-budget N%` without a running triage is a usage error),
plus the request-shape half of T-89 and all of T-90. Amends §5.1's rows only.

## 2. Entry preconditions

- `SPEC.md` v1.15 is on disk and `check --judge mock` on the v1.14 tree reports exactly 8
  `UNCITED` ids (the new ones) — verified before this wave started.
- `judge.py` exposes `JudgeRequest` (`id`, `statement`, `testcase`, `declared`, `source`) and
  `numbered_source`; `judge_llm.py`'s `LlmConfig`/`LlmJudge` are the pattern to mirror (env
  validation message shape, `_httpx_post`, `PostFn`, the abortable `_post_with_deadline`).
- `cli.py` has `_int_in_range`, `UsageError`, `JUDGE_MODES`, `Config`, `_make_provider`.

## 3. Deliverables

`src/speccheck/jev.py` (new)

```python
ENV_URL, ENV_MODEL, ENV_KEY, ENV_TIMEOUT   # SPECCHECK_JEV_*
DEFAULT_URL = "https://openrouter.ai/api/alpha/decisions"
DEFAULT_MODEL = "~typesafe/jev-latest"
REDACTED = "***"
INSTRUCTIONS: str                          # C-17's pinned instructions line
CRITERIA: dict[str, str]                   # the four C-06 tokens -> C-17's pinned criteria

class JevConfigError(Exception)            # -> exit 2; message never carries the key
@dataclass(frozen=True) class JevConfig:   # url, model, api_key, timeout
    @classmethod from_env(environ) -> JevConfig
    def redacted() -> str

def render_state(req: JudgeRequest) -> str           # C-17's state template
def build_body(req: JudgeRequest, model: str) -> bytes
def parse_confidence(text: str) -> float | None      # answers.verdict -> p(e), or None (unusable)
class JevTriage:
    config: JevConfig; abort: threading.Event
    def __init__(config, post: PostFn | None = None)
    def confidence(req: JudgeRequest) -> float | None # never raises (E-59)
```

`src/speccheck/cli.py`

```python
Config.jev: JevConfig | None
Config.triage: bool
Config.judge_budget: int          # the SECONDS form (unchanged meaning)
Config.budget_percent: int | None # the N% form
def _parse_budget(text: str) -> tuple[int, int | None]     # grammar + E-58
def _make_triage_provider(config: Config) -> JevTriage     # tests monkeypatch this
```

## 4. Work items

- **W1-01** — RED: `tests/test_07_cli.py::test_jev_pre_triage_usage_errors_and_secret_hygiene`
  (T-90, E-58, E-21, I-007): `--judge-budget 30%` alone exits 2 naming both flags with no report
  written; `--judge-budget 30% --jev-pre-triage --judge mock` exits 2 the same way;
  `--judge-budget 30` under `--judge mock` is still accepted and ignored; `--judge-budget 30%
  --jev-pre-triage --judge llm` with `SPECCHECK_JEV_API_KEY` unset exits 2 naming that variable;
  `101%` and `%` exit 2; no key value appears in any message. GREEN: `_parse_budget` + the E-58
  check + `JevConfig.from_env` in `parse_config`.
- **W1-02** — RED: `tests/test_05_judge.py::test_triage_request_shape_and_response_parse`
  (T-89, C-17): the body is exactly `{model, state, questions}` with the pinned `state` template
  and the four criteria; the headers carry the bearer key; a 200 with a choice answer yields
  `p(e) = max(probabilities)`; a non-200, a non-JSON body, a missing `answers.verdict`, a
  non-token `choice`, and empty/non-numeric `probabilities` each yield `None`; the config's
  `redacted()` and every error message never carry the key. GREEN: `jev.py`.
- **W1-03** — `Config` plumbing (`jev`, `triage`, `budget_percent`), `_make_triage_provider`, and
  the `[llm]`-extra check for the triage path.

## 5. Test plan

One test function per work item, ids cited literally in the docstring. No timing assertions in
this wave (no concurrency yet); `_httpx_post` is monkeypatched or a `post=` stub is injected.

## 6. Gate

```bash
uv run python -m pytest tests/test_05_judge.py tests/test_07_cli.py -q
uv run ruff check src tests
```

Expected: green; no change to any existing test's outcome (the flags default off).

## 7. Traceability

§11 rows this wave closes: C-17 (`jev.py`, `cli.py`), E-58 (`cli.py`). T-90 PASSING; T-89 still
needs W2 for its end-to-end half, so its §11 "verified by" stays incomplete until then.

## 8. Traps

- `~typesafe/jev-latest` is a floating alias; the default in `DEFAULT_MODEL` must be the alias,
  not the pinned `typesafe/jev-1.13` the calibration was measured against (C-17 says so).
- The `%` form must be rejected under `--judge mock` even though the `SECONDS` form is ignored
  there (E-58's second clause) — two rules that look asymmetric on purpose.
- `parse_config` resolves `--judge` before the budget grammar; keep E-58's message independent of
  the C-09 variables (it must not need a judge config to be built).
- Never log the state or the answer at INFO (I-007): the state contains the statement.

## 9. Exit criteria and handoff

Both gate commands green, one commit (`feat(speccheck): W1 — the C-17 Jev provider and the
--jev-pre-triage grammar (C-17, E-58; T-90)`), and W2 can assume: `JevConfig`/`JevTriage` exist,
`Config` carries `jev`/`triage`/`budget_percent`, and `_make_triage_provider` is the seam the
tests patch.
