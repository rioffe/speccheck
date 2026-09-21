# Detailed implementation plan — W2: the recorded T-94 (the live-LLM trace)

> - **Wave:** W2 of W1–W3 (`IMPLEMENTATION_PLAN.md` §4 item 2).
> - **Spec basis:** `SPEC.md` v1.17: T-94 *(recorded)*, E-61, C-18's verdict/clause/rationale rules.
> - **Gate:** the T-94 measurement run and recorded; the presence check green; the suite green.
> - **Budget:** ~40–60 test/report lines, no production change.
> - **Depends on:** W1 (`explain.render_trace`, `cli.execute_explain`). **Unlocks:** W3.

## 1. Objective and spec obligations

| id | obligation (≤20 words) | how this wave discharges it |
| --- | --- | --- |
| T-94 *(recorded)* | under `--judge llm` the trace shows the verdict with `clause:` and `rationale:`; under `--judge none` it reads `not judged`; statuses agree | the live run on the fixture with the requester's model, recorded in `SPEC_BUILD_REPORT.md` §0i; a presence check in the suite |
| E-61 | `--judge` carries `check`'s contract verbatim | the recorded run is the evidence that the verdict rendering matches the JSON's |

## 2. Entry preconditions

- W1 committed; `pytest tests -q` green except `test_09`'s `DECLARED_IDS`.
- `SPECCHECK_JUDGE_URL`/`_MODEL`/`_API_KEY` reachable with `google/gemini-3.8-flash`.

## 3. Deliverables

- `tests/test_09_self_application.py::test_t94_recorded_explain_trace_is_measured_and_recorded` —
  the report has the T-94 section, names the model, the date and `judge_prompt_sha256`, quotes both
  forms (`clause:`/`rationale:` and `not judged`), and `tests/test_12_explain.py` exists.
- `SPEC_BUILD_REPORT.md` §0i — the recorded trace: the exact command, the model, the date, the
  `judge_prompt_sha256`, the status agreement with `speccheck.json`, and the `--judge none` form.

## 4. Work items

- **W2-01** — RED: the presence check fails (no §0i).
- **W2-02** — run `explain` under `--judge llm` on the fixture copy (gemini-3.8-flash) and under
  `--judge none`; capture both traces; assert by hand that the status equals the JSON's.
- **W2-03** — record §0i; GREEN; gate; commit.

## 5. Test plan

| group | ids | what must be asserted | how it runs |
| --- | --- | --- | --- |
| `tests/test_09_self_application.py` | T-94 | the §0i artifact's shape only (non-gating row) | `pytest tests/test_09_self_application.py -q` |

## 6. Gate

```bash
uv run python -m pytest tests/test_09_self_application.py -q     # expected: all green
uv run python -m pytest tests -q --junitxml=junit.xml            # expected: 1 failed (DECLARED_IDS), rest green
uv run ruff check src tests tools                                # expected: exit 0
```

## 7. Traceability

| id | file.symbol | test | status now → after |
| --- | --- | --- | --- |
| T-94 *(recorded)* | `SPEC_BUILD_REPORT.md` §0i | `test_t94_recorded_explain_trace_is_measured_and_recorded` | UNCITED → PASSING |
| E-61 | `cli.py`, `explain.py` | the recorded run | UNCITED → PASSING (its edge is judged by the live run) |

## 8. Traps

- **Never paste the API key** into the report or the trace (I-007).
- **The trace must be quoted verbatim**, not paraphrased: it is the evidence.
- **`--judge llm` on the fixture needs `--results junit.xml`** for edges to be eligible (I-010).
- A `WEAKLY_PASSING` or `UNKNOWN` verdict is recorded as it renders — the row measures the
  *rendering*, not the model's agreement.

## 9. Exit criteria and handoff contract

- §0i written with the model, date, sha and both forms; the presence check green; committed.
- W3 re-runs the suite and both gates.
