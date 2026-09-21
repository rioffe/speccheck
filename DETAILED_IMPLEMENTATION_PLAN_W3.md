# Detailed implementation plan — W3: the recorded measurements, the docs, and both gates

> - **Wave:** W3 of W1–W3 (`IMPLEMENTATION_PLAN.md` §4 item 3).
> - **Spec basis:** `SPEC.md` v1.16 (the digest measured in `IMPLEMENTATION_PLAN.md`); T-48, T-49,
>   T-84, T-87, T-91, T-51, §9.9, §10, §11, §13. `SPEC.md` is edited only by a recorded
>   `fix(spec):` if Phase 3 finds a stale row.
> - **Gate:** the full Phase 1 exit gate — suite green, `ruff` clean, `--self-check` `ok`, Phase A
>   `CONFORMING` with 0 dangling / 0 stale / exit 0, then Phase B (`--judge llm --strict`) exit 0
>   with `google/gemini-3.8-flash`.
> - **Budget:** docs and test-side pins only; ~60–120 lines of suite + report prose.
> - **Depends on:** W1 (the fixture and labels) and W2 (`related` in place).

## 1. Objective and spec obligations

| id | obligation (≤20 words) | how this wave discharges it |
| --- | --- | --- |
| T-84 | the adjacent subset measured; model, date, `judge_prompt_sha256` recorded | both prompt texts, three runs each, `google/gemini-3.8-flash`; recorded in `SPEC_BUILD_REPORT.md`; a presence check in the suite |
| T-49 | three independent runs, ≥0.90 accuracy, ≤0.10 unknown, recorded | `tools/eval_judge.py` against the 39 labels |
| T-48 | the self-application run recorded (all in-scope ids `PASSING`) | the mock gate on this repository, recorded |
| T-51/T-91/T-87 | the recorded rows stay recorded | unchanged; their presence checks re-run |
| §11 | every id traces to component → behaviour → test | `DECLARED_IDS = 237`; the walk filled from `speccheck.json` |
| T-60/T-73 | `_selfcheck/` and the goldens in step | re-checked after every edit |

## 2. Entry preconditions

- W1 and W2 committed; the suite green apart from `test_09_self_application`'s `DECLARED_IDS`.
- `SPECCHECK_JUDGE_{URL,MODEL,KEY}` reachable with `google/gemini-3.8-flash`; the pre-v1.16 C-10
  text recoverable from git (`git show HEAD~1:src/speccheck/judge_prompt.md`).
- The 8 adjacent edges are labeled and judged under `--judge mock`.

## 3. Deliverables, file by file

### 3.1 `tests/test_09_self_application.py` — EDIT

- `DECLARED_IDS = 237` with the per-version comment the file's convention keeps.
- New `test_t84_recorded_adjacent_subset_is_measured_and_recorded`: the report has the T-84
  section, names the model and `judge_prompt_sha256` for both prompt texts, and carries a row per
  adjacent edge (presence check only — the measurement is the evidence).

### 3.2 `tools/adjacent_eval.py` — NEW (~90 lines, not collected by pytest)

The T-84 runner: copies `fixtures/target/`, runs `check --judge llm` three times per prompt text
(shipped, and the pre-v1.16 text injected through `judge_llm.load_prompt`), scores only the eight
adjacent edges against `golden/judge_labels.json`, and prints per-run verdicts, accuracy and
`judge_prompt_sha256`. Never edits a file under `src/`.

### 3.3 `README.md` — EDIT

The fixture's new counts, `related` on the request and in the triage `state`, the recorded
measurements' pointers, and the verification commands. Every command run as written.

### 3.4 `SPEC_BUILD_REPORT.md` — EDIT

A new increment section: the wave ledger (gate command, real exit code, commit sha per wave), the
T-84 measurement (§0h: both prompt texts, model, date, sha, per-edge verdicts), T-49's three runs,
T-48's summary line, the per-id evidence rows for R-38/C-06/C-10/C-17/K-16/E-57/T-83/T-84, the
Phase A/Phase B summary lines verbatim, and the verdict block.

### 3.5 `speccheck.json`, `SPEC_CONFORMANCE_REPORT.md` (root) — REGENERATED

From the final mock run, for the reader who opens them next to the spec.

## 4. Work items, in order (red → green → refactor)

- **W3-01** — `DECLARED_IDS = 237`; RED first (the test fails on 233), then the constant.
- **W3-02** — `tools/adjacent_eval.py`; run it (6 runs); record §0h; write the T-84 presence check.
- **W3-03** — `tools/eval_judge.py` three runs; record T-49.
- **W3-04** — README, `SPEC_BUILD_REPORT.md`, the root reports.
- **W3-05** — the final gates: Phase A (`--judge mock --strict`) and Phase B (`--judge llm
  --strict`, `google/gemini-3.8-flash`); commit.

## 5. Test plan

| group | ids | what must be asserted | how it runs |
| --- | --- | --- | --- |
| `tests/test_09_self_application.py` | T-48, T-49, T-84, T-91 | the declared count; the labels cover the judged edges; the T-84 section exists with both shas | `pytest tests/test_09_self_application.py -q` |
| Phase A | all | `CONFORMING`, 0 dangling, 0 stale, exit 0 | `check --judge mock --strict` |
| Phase B | all | exit 0, judge available, `unknown_rate ≤ max_unknown`, 0 weak | `check --judge llm --strict` |

## 6. Gate: commands and expected results

```bash
uv run python -m pytest tests -q --junitxml=junit.xml
uv run ruff check src tests
uv run speccheck --self-check
uv run speccheck check --spec SPEC.md --src src --tests tests --results junit.xml --judge mock --strict --out build/speccheck
uv run speccheck check --spec SPEC.md --src src --tests tests --results junit.xml --judge llm --strict --out build/speccheck-llm
```
Expected: `237/237 passing`, 0 dangling, 0 stale, exit 0 for Phase A; Phase B exit 0 with
`judge=llm` and no weak id.

## 7. Traceability

| id | file.symbol | test | status now → after |
| --- | --- | --- | --- |
| T-84 | `SPEC_BUILD_REPORT.md` §0h, `tools/adjacent_eval.py` | `test_t84_recorded_adjacent_subset_is_measured_and_recorded` | UNCITED → PASSING |
| T-49 | `SPEC_BUILD_REPORT.md`, `tools/eval_judge.py` | `test_llm_eval_labels_cover_every_judged_edge` | PASSING → PASSING |
| T-48 | `SPEC_BUILD_REPORT.md` | `test_self_application_runs_on_this_repository` | PASSING → PASSING |
| §11 | every row | the walk in §3.1 of the report | — |

## 8. Traps

- **Phase B is model-sensitive** (D-07/D-08): record the model and `unknown_rate`; a
  `WEAKLY_PASSING` id is a test defect to fix, never a reason to raise `--max-unknown`.
- **The two prompt texts must not be confused**: the shipped one is the v1.16 text (sha
  `dbac713c…`); the historical one is `f6b124bd…`. Both go in the report with their own rows.
- **Never paste the API key** into a report, README, commit message or DEBUG output (I-007).
- **The root reports are regenerated from the final run**, after the last code change, so their
  summary line matches the report's.
- **A recorded row is not gating**: the presence checks assert the artifact's shape, not the
  measurement's outcome — but the measurement itself is run, and its honest result is recorded
  even when it is "on none".

## 9. Exit criteria and handoff contract

- Both gates' summary lines pasted verbatim; the verdict block written; the increment committed.
- The wave ledger complete (each wave: gate command, exit code, commit sha).
