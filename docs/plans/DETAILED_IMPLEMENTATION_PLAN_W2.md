# Detailed implementation plan — W2: README, the conformance report and both gates

> - **Wave:** W2 of W1–W2 (`docs/plans/IMPLEMENTATION_PLAN.md` §4 item 2).
> - **Spec basis:** `SPEC.md` v1.18; §9.14, §10, §11, §5.1, §5.4, T-48, T-95..T-98.
> - **Gate:** the full Phase 1 exit gate, then Phase A and Phase B, both exit 0.
> - **Budget:** docs and test-side pins only.
> - **Depends on:** W1.

## 1. Objective and spec obligations

| id | obligation (≤20 words) | how this wave discharges it |
| --- | --- | --- |
| §11 | every id traces to component → behaviour → test | `DECLARED_IDS = 252`; the report's §5 rows for R-41/C-19/I-017/T-95..T-98 |
| T-48 | the self-application recorded | the mock gate on this tree, recorded |
| Phase B | `--judge llm --strict` exit 0 | run with `google/gemini-3.8-flash` |

## 2. Entry preconditions

- W1 committed; the suite green apart from `test_09`'s `DECLARED_IDS`.
- The provider reachable.

## 3. Deliverables

- `tests/test_09_self_application.py`: `DECLARED_IDS = 252` with the per-version comment.
- `README.md`: a "the CLI documents itself" note (what `--help` now carries, the environment block,
  the exit codes), the verification commands, the layout (`tests/test_13_help.py`,
  `tests/data/help/`), the version 1.18.0.
- `SPEC_BUILD_REPORT.md`: §0j (why, plan, wave ledger, the four screens quoted at `COLUMNS=80`, the
  T-95 token table, the interpretations), the §5 rows, §6's verdict with both gates verbatim.
- The root `speccheck.json` / `SPEC_CONFORMANCE_REPORT.md` from the final mock run.

## 4. Work items

- **W3-01** — `DECLARED_IDS` 252 (RED first).
- **W3-02** — README; every command in it run as written.
- **W3-03** — the report; both gates; the verdict block; commit.

## 5. Test plan

| group | ids | what must be asserted | how it runs |
| --- | --- | --- | --- |
| whole suite | all | 134 tests green | `pytest tests -q --junitxml=junit.xml` |
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
Expected: 252/252, 0 dangling, 0 stale, exit 0 on both.

## 7. Traceability

| id | file.symbol | test | status now → after |
| --- | --- | --- | --- |
| R-41, C-19, I-017, T-95..T-98 | as W1 | T-95..T-98 | PASSING |
| §11 | every row | the report's §5 walk | complete |

## 8. Traps

- **Phase B is model-sensitive**: record the model, `unknown_rate` and `judge_strength`; a
  `WEAKLY_PASSING` id is a test defect to fix, never a reason to raise `--max-unknown`.
- **The help screens quoted in the report must be the rendered bytes**, not a paraphrase, and at
  the pinned width where the golden is cited.
- **No new §9.8 golden**: `explain`/help change no report; the root reports are gitignored build
  output.

## 9. Exit criteria

- Both gates' summary lines pasted verbatim; the verdict block written; the increment committed.
