# Detailed implementation plan — W1: v1.23.1 corrections to existing behaviour

> - **Wave:** W1 of W1–W4 (`IMPLEMENTATION_PLAN.md` §4 item 1).
> - **Spec basis:** `SPEC.md` v1.23.1 (re-measure the sha256 at wave start); not edited by this wave.
> - **Gate:** the full suite red only on the two `DECLARED_IDS` tests; goldens and `--self-check` unchanged.
> - **Budget:** 15–40 production lines. **Depends on:** v1.22 build. **Unlocks:** W2 (a baseline where every failure is new).

## 1. Objective and spec obligations

| id | obligation | how |
|---|---|---|
| R-22, C-06 (F-706) | mock: a JS/TS line with `expect(`/`expect.` is an assertion token | `judge_mock.is_assertion_line` |
| C-03 (F-708) | `/` is a regex iff the previous token is absent, punctuation other than `) ] }`, or a listed keyword | `jsts._starts_regex`, `_REGEX_PRECEDERS` |
| C-18, R-40 (F-711) | reason strings name C-05's steps; `<outcome>` includes `error` | `explain._REASONS`, outcome rendering |
| C-10, R-26 (F-703) | `judge_prompt.md` equals the C-10 block | copy the block |
| C-06 (F-701) | request `messages` = [system, user] | test only (code already right) |
| C-14 (F-705) | a JS `/* … */` second line is DECLARED | test only (T-115 extension) |
| K-18 (F-709) | unreadable `--results` + E-01 → exit 2 | test only (T-103 extension) |

## 2. Entry preconditions

`spec/v1.23.1` at or after `50b723d`; `uv sync --extra dev`; the 161/164 baseline of plan §2.

## 3. Deliverables

- **`src/speccheck/judge_mock.py` — EDIT (~3 lines):** add `"expect(", "expect."` to the token check (C-06).
- **`src/speccheck/jsts.py` — EDIT (~10 lines):** `_REGEX_PRECEDERS` = every one-char punctuation except `)`, `]`, `}`, plus `return typeof instanceof in of new delete void throw case do else yield await` (C-03 F-708). Regex flags already consumed; verify the class `[ … ]` rule.
- **`src/speccheck/explain.py` — EDIT (~12 lines):** `_REASONS` per C-18 (RETIRED `step 1: struck through in the specification`; UNCITED `step 2a: …`, a T id `step 2b: no test citation`; UNTESTED `step 2a: no test citation`; UNVERIFIED `step 3: …`; FAILING/SKIPPED/PASSING `step 4: …`; WEAKLY_PASSING `step 5: no judged edge asserts the statement`); `error` rendered as an outcome.
- **`src/speccheck/judge_prompt.md` — EDIT:** the C-10 fenced block, byte for byte.
- **Tests — EDIT:** `test_05_judge.py` (T-69 JS sub-test; T-33 two-message assertion), `test_15_jsts.py` (T-113 regex cases, T-115 `/* */` line), `test_12_explain.py` (T-92/T-93 strings, UNVERIFIED step 3, `(error)`), `test_07_cli.py` (T-103 pair).

## 4. Work items

- **W1-01** T-69 JS sub-test (red: `EXECUTES_ONLY`) → mock tokens → green.
- **W1-02** T-113 cases `return /c)/`, `x = /d[/)]/g`, file-start `/e)/`, and `a } /x)/` behaviour (red on `}` and missing keywords) → `_REGEX_PRECEDERS` → green.
- **W1-03** T-92/T-93 new strings, UNVERIFIED/`error` cases (red) → `explain.py` → green.
- **W1-04** sync `judge_prompt.md` → `test_llm_response_path_fences_and_prompt_hash` green.
- **W1-05** characterization tests T-33 (two messages), T-115 (`/* */`), T-103 pair: written to
  pin behaviour the spec now states and the code already has. They are expected to pass at once;
  the commit body says so rather than claiming a red phase.

## 5. Test plan

`uv run python -m pytest tests/test_05_judge.py tests/test_15_jsts.py tests/test_12_explain.py tests/test_07_cli.py -q`.

## 6. Gate

1. `uv run python -m pytest tests -q --junitxml=junit.xml` — expected: exactly 4 failures, all in `test_09_self_application.py`: the two `DECLARED_IDS` tests, and T-84 and T-94, whose recorded runs pin the old `judge_prompt_sha256` and are voided by the C-10 change (F-303); W4 re-records them. *(Amended during W1: the plan first expected 2.)*
2. `uv run ruff check src tests` — expected: exit 0.
3. `uv run speccheck --self-check` — expected: `self-check: ok` (the T-46 goldens unchanged; no golden contains `expect(` outside `#expect(`).
4. `uv run python -m pytest tests/test_08_golden.py -q` — expected: all pass (T-46, T-71 byte-identical).

## 7. Traceability

R-22, C-06, C-03, C-18, R-40, C-10, R-26, C-14, K-18 stay PASSING; their tests gain the v1.23.1 clauses.

## 8. Traps

- T-62/T-92-style pinned strings elsewhere (`README.md`, `docs/introducing-speccheck.md`) quoting the old `step 4` line: grep for `step 2b:` and `step 3: a citing` and update them in W4, not here (docs last).
- `expect(` also occurs in `#expect(`; the evidence list must not double-count a line (one entry per line).

## 9. Exit and handoff

Frozen: `judge_mock.is_assertion_line`, `explain.render_trace` signature. Next wave re-runs gate items 1–4.
