# W2 — K-16: the triage pass, and K-12's `N%` count

## 1. Ids discharged

K-16 (the pass itself: one task per eligible edge, `--judge-concurrency`, ascending $p(e)$, ties
by C-07's id order, failures first, the D-30 Note), I-015 (the answer is discarded after the
order), E-59 (per-edge failure → first + one Note, `judge_available`/`unknown_rate` untouched),
and the amended K-12 (`N%` issues $\lceil N/100 \times E \rceil$ edges), E-35/E-36, C-11.

## 2. Entry preconditions

W1 committed: `jev.py` with `JevTriage.confidence`, `Config.jev/triage/budget_percent`,
`_make_triage_provider`.

## 3. Deliverables

`src/speccheck/jev.py`

```python
@dataclass class TriageRun:
    order: list[JudgeRequest]      # the issue order (K-16)
    failures: int                  # E-59
    def notes(self) -> list[str]   # one Note naming the count, or []
def run_triage(provider, requests, *, concurrency=1, progress=None) -> TriageRun
```

`src/speccheck/judge.py`

```python
def run_judge(..., issue_count: int | None = None) -> JudgeRun
    # issue_count is not None -> requests[issue_count:] are K-12 budget-skipped
    # (UNKNOWN, "judge: budget", coerced, call_made=False) before the pool starts; they still
    # count in budget_unjudged, in the Note, in unknown_rate, and advance the indicator.
```

`src/speccheck/cli.py`

```python
# after eligible_edges -> requests:
#   if config.triage: run_triage -> requests = run.order (I-015: nothing else is kept)
#   notes.extend(triage.notes()); D-30 Note when budget is the SECONDS 0 form
#   issue_count = ceil(percent/100 * len(requests)) when budget_percent is not None
```

## 4. Work items

- **W2-01** — RED: `tests/test_05_judge.py::test_triage_orders_and_truncates_the_judge_queue`
  (T-89, K-16, K-12, I-015, E-35, E-59, D-30, D-32): 10 eligible edges, a stub triage provider
  with fixed confidences (one edge raising), a stub judge recording the order it was asked in —
  `30%` issues exactly 3 (the lowest $p(e)$, the failing edge first), the other 7 are `UNKNOWN`
  with `judge: budget`/`coerced`, Notes report 7 and 1; `100%` issues 10; `0%` issues none with
  0 judge calls; `--judge mock` makes no Jev call; `--judge-budget 0` adds the D-30 Note and
  changes no report content; a total Jev failure leaves `judge_available`/`unknown_rate` as a
  triage-free run.
- **W2-02** — the triage pass's concurrency and interrupt path (same poll/abort shape as
  `run_judge`; `JevTriage.abort` is set on the way out of a `BaseException`, so E-41 holds).
- **W2-03** — the stage/INFO lines (`stage=triage edges=N failed=N ms=…`, then
  `jev url=… model=… timeout=…` with the key redacted) emitted after the indicator's erase, as
  K-13/F-201 require for the judge stage.

## 5. Test plan

`test_triage_orders_and_truncates_the_judge_queue` is one function with sub-cases (the T-61
pattern). A second function, `test_triage_concurrency_and_interrupt`, may be added if the abort
path needs it; both cite T-89.

## 6. Gate

```bash
uv run python -m pytest tests -q --junitxml=junit.xml
uv run ruff check src tests
uv run speccheck --self-check
```

Expected: green, `self-check: ok`, and the T-46/T-71 goldens byte-identical (the flags default
off, so no golden moves).

## 7. Traceability

§11 rows: K-16, I-015, E-59 (`jev.py`, `judge.py`, `cli.py`); K-12 and E-35 rows gain T-89.

## 8. Traps

- Ordering must be total: `p(e)`, then C-07's id order, then (file, start) for two edges of the
  same id — otherwise T-89's "the 3 lowest" is not reproducible. Record the third key as a report
  note: C-17 pins only the id tiebreak.
- A triage failure must not touch `judge_available` (E-14 owns that flag) or `unknown_rate`.
- The D-30 Note is about the `SECONDS 0` form only; `0%` is a real, requested truncation and
  gets no such Note.
- `budget_unjudged` already drives the Note and `unknown_rate`; do not add a second counter.

## 9. Exit criteria and handoff

Gate green, one commit (`feat(speccheck): W2 — the triage pass orders and truncates the judge
queue (K-16, K-12 N%, I-015, E-59; T-89)`), and W3 can assume: `check --jev-pre-triage` works
end to end against a stub and against the real endpoint.
