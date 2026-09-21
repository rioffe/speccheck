# Detailed implementation plan — W3: README, the conformance report, and both gates

> - **Wave:** W3 of W1–W3 (`IMPLEMENTATION_PLAN.md` §4 item 3).
> - **Spec basis:** `SPEC.md` v1.17; §9.13, §10, §11, §5.1, §5.4, T-48, T-92..T-94.
> - **Gate:** the full Phase 1 exit gate, then Phase A and Phase B, both exit 0.
> - **Budget:** docs and test-side pins only.
> - **Depends on:** W1 and W2.

## 1. Objective and spec obligations

| id | obligation (≤20 words) | how this wave discharges it |
| --- | --- | --- |
| §11 | every id traces to component → behaviour → test | `DECLARED_IDS = 245`; the report's §5 rows for R-40/C-18/I-016/E-60/E-61; the walk shows no gap |
| T-48 | the self-application recorded | the mock gate on this tree, recorded |
| T-92..T-94 | the new surface's rows | README + report carry their evidence |
| Phase B | `--judge llm --strict` exit 0 | run with `google/gemini-3.8-flash` |

## 2. Entry preconditions

- W1 and W2 committed; the suite green apart from `test_09`'s `DECLARED_IDS`.
- The provider reachable (same as W2).

## 3. Deliverables

- `tests/test_09_self_application.py`: `DECLARED_IDS = 245` with the per-version comment.
- `README.md`: the `explain` section (what it prints, the six sections, `--depth`, stdout-only,
  exit codes), the synopsis block, the layout (`explain.py`, `tests/test_12_explain.py`), the
  verification commands, the version 1.17.0, and the fixture/scope notes.
- `SPEC_BUILD_REPORT.md`: §0i's increment narrative, the wave ledger, the §4/§5 rows, the §6 verdict
  with both gates' summary lines verbatim.
- The root `speccheck.json` / `SPEC_CONFORMANCE_REPORT.md` from the final mock run.

## 4. Work items

- **W3-01** — `DECLARED_IDS` 245 (RED first).
- **W3-02** — README; every command in it run as written.
- **W3-03** — the report; both gates; the verdict block; commit.

## 5. Test plan

| group | ids | what must be asserted | how it runs |
| --- | --- | --- | --- |
| whole suite | all | 127 tests green | `pytest tests -q --junitxml=junit.xml` |
| Phase A | all | `CONFORMING`, 0 dangling, 0 stale, exit 0 | `check --judge mock --strict` |
| Phase B | all | exit 0, judge available, `unknown_rate` within bound, 0 weak | `check --judge llm --strict` |

## 6. Gate

```bash
uv run python -m pytest tests -q --junitxml=junit.xml
uv run ruff check src tests tools
uv run speccheck --self-check
uv run speccheck check --spec SPEC.md --src src --tests tests --results junit.xml --judge mock --strict --out build/speccheck
uv run speccheck check --spec SPEC.md --src src --tests tests --results junit.xml --judge llm --strict --out build/speccheck-llm
```
Expected: 245/245, 0 dangling, 0 stale, exit 0 on both.

## 7. Traceability

| id | file.symbol | test | status now → after |
| --- | --- | --- | --- |
| R-40, C-18, I-016, E-60, E-61, T-92, T-93, T-94 | as W1/W2 | T-92..T-94 | PASSING |
| §11 | every row | the report's §5 walk | complete |

## 8. Traps

- **Phase B is model-sensitive**: record the model, `unknown_rate` and `judge_strength`; a
  `WEAKLY_PASSING` id is a test defect to fix, never a reason to raise `--max-unknown`.
- **The README's `explain` example must be run as written** on the fixture (its trace is long:
  quote the command, not the whole trace).
- **No new golden**: the root reports are gitignored build output, regenerated for the reader.

## 9. Exit criteria

- Both gates' summary lines pasted verbatim; the verdict block written; the increment committed.
