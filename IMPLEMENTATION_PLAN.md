# Implementation plan — SPEC.md v1.15 delta (Jev pre-triage)

> Scope: a **delta plan** on top of the working v1.14 implementation (225 ids, `speccheck check
> --judge mock --strict` CONFORMING). It covers only the ids v1.15 added: K-16, C-17, I-015,
> E-58, E-59, T-89, T-90, T-91, and the two amended rows K-12 (`N%`) and E-35/E-36. Not a
> greenfield plan; the target shape (Extractor / Attributor / Grapher / Judge / Reporter / CLI)
> is already built, and this change adds one provider beside the judge plus one ordering stage.

## Verdict

Three waves, in dependency order. The ordering fact (K-16) has exactly one source (C-17's
per-edge confidence) and exactly one consumer (`run_judge`'s issue order and K-12's `N%` count),
so the provider contract must exist and be tested before anything is wired to it, and the
truncation must be expressed where the budget already lives (`run_judge`) rather than in a second
place that could drift from K-12's bookkeeping.

- **W1 — C-17, the provider.** New `jev.py`: `JevConfig.from_env` (four variables, E-21-style
  message, key never echoed), `render_state` (the C-17 template, byte-identical to
  `tools/judge_crosscheck_tasks.py`'s), `build_body` (model/state/questions with the four pinned
  criteria), `parse_confidence` (`answers.verdict` → $p(e)$, or "unusable"), and `JevTriage`
  (bearer header, K-05-shaped timeout, abortable transport, `judge>`/`judge<`-style DEBUG lines).
  `cli.py`: `--jev-pre-triage`, the `SECONDS|N%` grammar, E-58's usage error, `Config.jev`,
  `_make_triage_provider`. Closes C-17, E-58; T-90, and T-89's request-shape half.
- **W2 — K-16 + K-12 `N%`.** `jev.py`: `run_triage` (one request per eligible edge at
  `--judge-concurrency`, ascending $p(e)$, ties by C-07's id order, failures first, one Note).
  `judge.py`: `run_judge(issue_count=...)` so the not-issued edges take today's exact K-12
  disposition and count as budget-skipped. `cli.py`: order the requests, the D-30 Note, the
  triage stage line and INFO line, E-59's Note. Closes K-16, I-015, E-59; extends K-12, E-35,
  E-36, C-11; T-89.
- **W3 — evidence and docs.** README (the flag, the two grammars, C-17's variables, what triage
  does not do), the T-91 presence check in the suite, the recorded T-91 measurement on this
  repository's own tree, the final gates, and `SPEC_BUILD_REPORT.md`. Closes T-91.

## Evidence (measured, not assumed)

- Starting tree: v1.14 is green — `check --judge mock --strict` exits 0 with 233/233 once this
  change's ids are cited; before it, 225/225, `build/speccheck/`.
- The eight new ids are `UNCITED` today (the spec change landed without code): confirmed by
  running the v1.15 spec against the v1.14 tree (`8 uncited`, 0 dangling, 0 stale).
- `tools/judge_crosscheck_tasks.py` + `tools/jev_client.py` already implement the request shape
  and the `answers.verdict` path C-17 pins, and the v1.16 proposal's calibration was measured
  with them — so C-17's strings are copied from working code, not invented.
- The environment has `OPENROUTER_API_KEY` and `SPECCHECK_JUDGE_{URL,MODEL,KEY,TIMEOUT}`
  (`openai/gpt-4o-mini`), so T-91's recorded run and the Phase B gate can both be executed.

**Systemic failure modes this delta must not repeat** (both were found in the v1.14 build):

| Failure | Structural rule that makes it impossible here |
| --- | --- |
| A pinned string (the C-10 text) drifting from the code that ships it | C-17's `state` template, `instructions` and four `criteria` strings live in **one** module constant each, and T-89 asserts the wire body against them |
| A second bookkeeping path for the same number (budget-skipped edges) | the `N%` count is a parameter of the one function that already counts budget-skipped edges (`run_judge`), so `budget_unjudged`, the Note, `unknown_rate` and `available` stay single-sourced |

## Target shape

```
src/speccheck/jev.py     C-17 provider + K-16 ordering pass   (new)
src/speccheck/judge.py   run_judge gains issue_count          (K-12 N%)
src/speccheck/cli.py     flags, grammar, wiring, notes        (E-58, K-16)
tests/test_05_judge.py   T-89 (ordering, truncation, request shape)
tests/test_07_cli.py     T-90 (usage errors, secret hygiene)
tests/test_09_self_application.py  T-91 presence check
```

One-way direction: `cli.py` → `jev.py` → `judge.py`'s `JudgeRequest`/`TestCase` types. `jev.py`
never imports `cli.py`, `report.py`, or `graph.py`; nothing in the report path imports `jev.py`
(I-015: no triage field can reach a report because the reporter cannot see the module).

## Order, gates, budgets

| Wave | Gate (all commands, real exit codes recorded in `SPEC_BUILD_REPORT.md`) | Budget |
| --- | --- | --- |
| W1 | `pytest tests/test_05_judge.py tests/test_07_cli.py -q`; `ruff check src tests` | ~170 LOC `jev.py`, ~40 LOC `cli.py` |
| W2 | the same two files, then the whole suite + `speccheck --self-check` | ~90 LOC `jev.py`, ~50 LOC `cli.py`, ~15 LOC `judge.py` |
| W3 | the full Phase 1 exit gate: `pytest tests -q --junitxml=junit.xml`; `ruff check src tests`; `speccheck --self-check`; `check --judge mock --strict`; `check --judge llm --strict` | docs only |

Anchors: the smallest complete build of this delta is ~300 LOC of production code (one provider
module, one parameter, one wiring block). Anything above that is structure named in the report.

## The one fork

**T-91's recorded measurement: run it for real, or record it pending?** Recommendation, taken:
**run it** — the credentials and a judge model are present, the measurement is the spec's own
evidence for the calibration claim, and it is the only way T-91 is more than a presence check.
The alternative (record "pending: no reachable judge") would be honest but weaker; the run is
re-runnable, so the choice is reversible. Recorded in `SPEC_BUILD_REPORT.md` §0g with the model,
the date and the bucket figures.

## Spec defects found while planning

None. v1.15's own rows are consistent with the implementation shape above; the two v1.14
document corrections (F-101/F-102) were already applied in the previous increment.

## Next action

Execute W1 test-first (`test_jev_pre_triage_usage_errors_and_secret_hygiene`, then
`test_triage_request_shape_and_response_parse`), gate, commit; then W2, then W3.
