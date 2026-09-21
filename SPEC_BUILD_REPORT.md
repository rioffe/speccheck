# SPEC_BUILD_REPORT — `speccheck` v1.15.0 against `SPEC.md` (v1.15)

> - **Built:** 2026-09-11 (v1.1, from `../SPEC_v1.1.md`), incremented 2026-09-13 to `SPEC.md` v1.4 (§0 below), 2026-09-17 to v1.6 (§0b), 2026-09-18 to v1.8 (§0c) and later that day to v1.11 (§0d), 2026-09-19 to v1.13 (§0e), 2026-09-20 to v1.14 (§0f) and to v1.15 (§0g); Python 3.12.13, `uv` 0.12.12
> - **Reference machine (K-08, D-14):** Apple M5 Max, 128 GiB RAM, macOS 26.6.2 (arm64), CPython 3.12.13 (uv-managed), run in isolation
> - **Verdict:** see §6

## 0i. v1.17 increment (2026-09-20) — `speccheck explain <ID>` (R-40, C-18, I-016, E-60, E-61)

**Why.** `PROPOSAL_v1.17_explain_id.md`, a **capability addition rather than a defect fix** and
stated as such: every fact a reader wants about one id is already computed — its statement, its
status and the C-05 step that set it, its citations with each case's JUnit outcome, each edge's
verdict, and the C-12 blast radius — but assembling them by hand takes three structured artifacts
plus two greps. §0's own promise is "never has to trust a number without a path to its evidence";
the path existed and was not *rendered as one thing*. D-33..D-36 (stdout-only, the upward `impact`
section included, recompute from the same inputs, one id per invocation) were confirmed on the
proposal's recommended branches before this build.

**Plan.** A delta `IMPLEMENTATION_PLAN.md` plus one brief per wave
(`DETAILED_IMPLEMENTATION_PLAN_W1.md`..`W3.md`): W1 the subcommand and the renderer, W2 the recorded
T-94, W3 the README, the conformance report and both gates. The plan's one fork — T-94's live-LLM
arm, run or recorded pending — was taken as **run it**: the requester named the model, and the
`clause:`/`rationale:` lines are the one part of C-18 a stub cannot honestly produce.

**Wave ledger.**

| Wave | Gate as run | Result | Commit |
| --- | --- | --- | --- |
| W1 — the subcommand and the C-18 renderer (R-40, C-18, I-016, E-60; T-92, T-93) | `pytest tests/test_12_explain.py -q`; `pytest tests -q --junitxml=junit.xml`; `ruff check src tests tools`; `speccheck --self-check`; `sync_selfcheck.py --check` | 2 passed; 1 failed / 127 passed (the failure was `test_09`'s `DECLARED_IDS`, W3's row); clean; `self-check: ok`; exit 0 — every golden byte-identical through the `_run_stages` refactor | `36d3e44` |
| W2 — the recorded T-94 (the live-LLM trace) | `pytest tests/test_09_self_application.py -q` | see below | this commit |
| W3 — README, the conformance report and both gates | the full Phase 1 exit gate, then Phase A and Phase B | see §6 | next commit |

**W1, test-first:** T-92 failed first on `invalid choice: 'explain'`, then on the trace it expected.
The implementation is one shared pipeline and one pure renderer: `execute`'s stage sequence moved
verbatim into `_run_stages(config)` (called by `execute` and the new `execute_explain`) and
`parse_config`'s validation into `_build_check_config` (reused by `explain` with `--out` and
`--strict` undefined on its subparser, E-54's pattern). The trace's `impact` section reuses
`impact.walk`, `mark_retired` and `reverify_set` unchanged (D-34). The refactor's evidence is the
existing byte-compared goldens: T-46, T-71, T-79 and T-80 all stayed green, so the split changed no
behaviour. T-92 pins R-01's whole trace byte for byte — five citing cases with the mock's verdicts,
the walk's one dependent (`I-001`, via `I-001 -depends_on-> R-01`) and the one T id that verifies
it (`T-01`) — and asserts a second run is identical, the fixture copy is untouched (no report, no
temporary, no `--out`), and the status equals `golden/speccheck.json`'s. T-93 covers E-60's message
for an undeclared id, the retired id's `(RETIRED)` marker and reason, the declared-but-uncited id's
empty `tests:` block, and `--out`/`--strict` as usage errors.

**T-94 *(recorded)* — the live-LLM trace.** Run 2026-09-20 against a copy of `fixtures/target/`
with `google/gemini-3.8-flash` (OpenRouter, `--judge-concurrency 8`, 20 s), exactly as the row
pins:

```bash
export SPECCHECK_JUDGE_URL=https://openrouter.ai/api/v1/chat/completions
export SPECCHECK_JUDGE_MODEL=google/gemini-3.8-flash
export SPECCHECK_JUDGE_API_KEY=...            # never recorded
cd fixtures/target
uv run --project ../.. speccheck explain R-01 --spec SPEC.md --src src --tests tests \
    --results junit.xml --judge llm --judge-concurrency 8
```

The trace (verbatim, exit `0`), `judge_prompt_sha256`
`dbac713c9a63185c590c4a2eb0ed2f52dc11f3cb414bea6495cf617152433f8f`:

```text
ID R-01
status: PASSING (step 4: every citing test case passed)
statement:
  `add(a, b)` MUST return the arithmetic sum of `a` and `b`, rounded per K-02.
sources:
  src/calc/core.py:10
tests:
  tests/test_core.py::test_add (passed) [ASSERTS]
    clause: `add(a, b)` MUST return the arithmetic sum of `a` and `b`, rounded per K-02.
    rationale: The test directly asserts that calling add(a, b) returns the expected arithmetic sum.
  tests/test_core.py::test_add_result (passed) [ASSERTS]
    clause: `add(a, b)` MUST return the arithmetic sum of `a` and `b`, rounded per K-02.
    rationale: The test asserts that add(2, 3) returns 5, verifying that add(a, b) returns the arithmetic sum of its inputs.
  tests/test_core.py::test_add_rounding_fact (passed) [EXECUTES_ONLY]
    clause: `add(a, b)` MUST return the arithmetic sum of `a` and `b`, rounded per K-02.
    rationale: The test calls add(1.005, 0.0) but does not assert on its return value, asserting instead on a standalone rounding expression.
  tests/test_core.py::test_add_rounding_of_a_half_cent (passed) [EXECUTES_ONLY]
    clause: `add(a, b)` MUST return the arithmetic sum of `a` and `b`, rounded per K-02.
    rationale: The test calls add(2.675, 0.0) but does not assert on its result, asserting instead only the behavior of built-in round().
  tests/test_summary.py::test_summary_module_does_not_change_add (passed) [ASSERTS]
    clause: `add(a, b)` MUST return the arithmetic sum of `a` and `b`, rounded per K-02.
    rationale: The test directly verifies that add(a, b) returns the arithmetic sum, including proper rounding for floating point values.
impact (1):
  I-001 (depth 1, via I-001 -depends_on-> R-01)
  T-01 verifies R-01
```

The same id under `--judge none` renders the same trace with every verdict line reading
`[not judged]` and no `clause:`/`rationale:` line:

```text
tests:
  tests/test_core.py::test_add (passed) [not judged]
  tests/test_core.py::test_add_result (passed) [not judged]
  tests/test_core.py::test_add_rounding_fact (passed) [not judged]
  tests/test_core.py::test_add_rounding_of_a_half_cent (passed) [not judged]
  tests/test_summary.py::test_summary_module_does_not_change_add (passed) [not judged]
```

**The status agreement (I-016).** A `check --judge llm` over the same fixture copy (same inputs,
same model, same day, `--judge-concurrency 8`, 24 s, `unknown_rate` `0.05`, `judge_available`
`true`) records R-01 as `PASSING` — the status the trace shows — with the same five edge verdicts
(`ASSERTS`, `ASSERTS`, `EXECUTES_ONLY`, `EXECUTES_ONLY`, `ASSERTS`). The two `EXECUTES_ONLY` edges
are the fixture's adjacent pairs, graded by the judge exactly as their labels say (v1.16's T-84
subset), and they are visible in the trace as such — which is the point of the surface: the
downgrade and its reason are readable in one place, without opening `speccheck.json`.

**F-1 — T-92's command line was self-contradictory, and the fold fixed it.** The proposal's draft
row passed `--out <fresh tmp>` to `explain`, which D-33 and C-18 remove: the flag does not exist on
the subparser. T-92's row now runs without `--out` and asserts the stronger property — the fixture
copy is byte-identical before and after the run (`fix(spec):`, `f1cca17`).

**Interpretations the build had to make.**

| Where | Reading taken | Why |
| --- | --- | --- |
| `explain`'s exit code on a non-`PASSING` id | `0` (nothing it renders is pass/fail, like `impact`) | C-18 pins `0`/`2`/`3` only; a trace of a `FAILING` id is still a successful render, and `--strict` is undefined on the subparser so no gate can move |
| `--max-unknown` on `explain` | accepted, consulted by nothing | §5.1's row lists it (it is part of `check`'s contract that E-61 carries over); it only matters under `--strict --judge llm`, and `explain` has no `--strict` |
| the depth-cap Note | logged at `INFO`, not rendered | C-18's trace has no notes section, and §5.3 already says Notes are logged at `INFO`; nothing may be added to stdout that C-18 does not pin |
| `explain`'s id lookup | normalized per I-011 before the declaration check | `R-1` and `R-01` are one id everywhere else in the tool; E-60's message echoes what the operator typed |

## 0h. v1.16 increment (2026-09-20) — the obligation-aware judge (R-38, C-06, C-10, C-17, K-16, E-57, T-83, T-84)

**Why.** `PROPOSAL_v1.14_obligation_aware_judge.md`, grounded in `JUDGE_CROSSCHECK_REPORT.md` §2b:
of 613 judged edges on this repository's own tree, 153 were genuine conflicts between two models,
60 of them concentrated on five ids reused as generic fixture data, and three read in full showed a
test citing an id as placeholder data while proving something else. The judge could see the test
and the statement but not the *neighbourhood*: a statement's C-12 `depends_on` edges — the ids it
names and the ids that name it — are exactly the context needed to tell "this test proves this
obligation" from "this test proves a neighbour this obligation refers to". D-28 (both directions,
own references first, capped at eight) and D-28b (the same list rides the C-17 triage `state`) were
confirmed in the spec before this build.

**Plan.** A delta `IMPLEMENTATION_PLAN.md` plus one brief per wave
(`DETAILED_IMPLEMENTATION_PLAN_W1.md`..`W3.md`): W1 the fixture's adjacent pairs and labels, W2
`related` on the request and the triage `state`, W3 the recorded measurements, the README and the
gates. The plan's one fork — measure T-84 against both C-10 texts, or the shipped text alone — was
taken as **both**: without the pre-v1.16 arm, "six of eight downgraded" cannot be told apart from a
model that downgrades adjacent edges anyway, which is the exact no-op the row exists to detect.
The ordering is apparatus-first: the fixture that makes the change measurable landed (and was
gated) before a line of `related` code existed.

**Wave ledger.**

| Wave | Gate as run | Result | Commit |
| --- | --- | --- | --- |
| W1 — the fixture's adjacent pairs, labels and goldens (T-76, T-46, T-47, T-86, T-88, T-79/T-80, T-60) | `pytest tests -q --junitxml=junit.xml`; `ruff check src tests`; `speccheck --self-check`; `sync_selfcheck.py --check` | 1 failed / 123 passed (the failure was `test_09_self_application`'s `DECLARED_IDS`, W3's row); clean; `self-check: ok`; exit 0 | `373155c` |
| W2 — `related` on the C-06 request and the C-17 triage `state` (R-38, C-06, C-10, C-17, K-16, E-57; T-83, T-74, T-85, T-89) | `pytest tests/test_05_judge.py tests/test_07_cli.py -q`; `pytest tests -q`; `ruff check src tests`; `speccheck --self-check` | 30 passed; 1 failed / 124 passed (same `DECLARED_IDS`); clean; `self-check: ok` | `eeb4c20` |
| W3 — the recorded measurements, README, both gates (T-84, T-49, T-48) | the full Phase 1 exit gate, then Phase A and Phase B | see §6 | this commit |

**W1, test-first:** T-76's test gained the two floors (≥ 37 labels; ≥ 8 adjacent downgraded) and
failed on `23 >= 37` before any fixture edit. The fixture then gained seven `depends_on`
cross-references and a new edge case E-03, and `tests/` gained eight adjacent cases each paired
with a genuine partner that uses the same calls and asserts the citing id's own clause. The
fixture's ten planted defects are unchanged and re-asserted (T-46): no new case cites `R-03`,
`C-02`, `E-01`, `K-01`, `I-002` or `T-03`, and no adjacent case's docstring names its neighbour —
a first draft did, and the extra citations both invented edges and silently flipped `C-02` from
`UNTESTED` to `PASSING`, which the golden comparison caught immediately. Every fixture-pinned
number the growth moved was re-derived from the regenerated golden, never guessed: the in-scope
count (19 → 20) and the passing count (13 → 14) in T-24's hand-computed metrics and T-47's repair
table, T-34/T-35's 21-row report, the fixture `junit.xml`'s case count (18 → 35), and
`declared_ratio` (0.9474 → 0.9722). The four goldens were regenerated by running the tool and
`speccheck/_selfcheck/` re-synced (T-60).

**W2, test-first:** T-83 was written first and failed on `ImportError: related_titles`, then
`judge_llm.related_titles`, `JudgeRequest.related`, `to_json`'s key order and `jev.render_state`'s
`Related obligations:` section were written against it — the builder's order (own references first,
then dependents, each in C-07's id order), the cap of eight, the 160-character tail truncation with
`…`, the retired tag (E-57), the empty list, and the exclusion of T ids. The field is built once
per eligible edge in `cli.py`, so the LLM user message and the triage `state` cannot drift; nothing
in `report.py`, `graph.py` or `judge_mock.py` reads it, which is why every golden, every status and
`schema_version` `"1.5"` are byte-unchanged. T-33, T-74, T-85 and T-89's expectations gained the
field and the section. A real-spec smoke check (this repository's own `SPEC.md`) confirms the
product's own behaviour: `related` for `R-38` is its six own references (C-06, C-07, C-10, C-12,
C-17, E-57) followed by its one dependent (K-16); `C-06`, a hub, sends eight dependents; `T-83`
sends `[]` because a T id's own references are C-12 `verifies` edges, not `depends_on`.

**F-1 — the spec's adjacent-label token was too narrow (found by the T-49 run, fixed here).**
T-76 and T-84 asked for "≥ 8 are `UNRELATED` on an adjacent edge", but C-10's vocabulary defines
`EXECUTES_ONLY` as "the test runs code the clause describes but no assertion checks it (assertions
absent, trivial, or about something else)" and `UNRELATED` as "the test does not exercise any
clause of the statement". An adjacent test by construction *runs* the cited id's code and asserts
only a neighbour's fact, so the correct token is `EXECUTES_ONLY`; the first label set used
`UNRELATED`, and `google/gemini-3.8-flash` graded seven of the eight `EXECUTES_ONLY` and the
eighth `ASSERTS` — taking T-49 to 0.7949 accuracy on run 3 and failing its ≥ 0.90 bar. The fix is
in the fixture, the labels and the spec: the eight adjacent edges are labeled `EXECUTES_ONLY`
(`E-03`'s test was mis-designed — `pytest.raises` around `divide(7, 0)` asserts E-03's own clause,
so it is a genuine test, labeled `ASSERTS`, and a second `R-01`→`K-02` pair replaced it in the
adjacent set), and T-76/T-84 now say "≥ 8 are downgraded (`EXECUTES_ONLY` or `UNRELATED`)" —
which is how T-84's own body and the proposal's measurement language already phrased it. `SPEC.md`
is edited in this increment — its v1.16 history row records F-1 — because the rows themselves were
wrong, not the code that implements them.

**Interpretations the build had to make.**

| Where | Reading taken | Why |
| --- | --- | --- |
| R-38's `related` element type | a list of **title strings**, not `{id, title}` objects | T-83 says "the whitespace-collapsed titles (each at most 160 characters)", C-10 calls them "the names of the other obligations", and C-17's `state` newline-joins them — the proposal's `[{id,title}]` draft was narrowed by the landed text, and the spec wins |
| R-38's "in-scope R/C/I/K/E ids only" vs E-57 | family filter on R/C/I/K/E (a T id is never an entry), **retired neighbours included** with `(retired)` | E-57 states the retired case explicitly; R-38's clause excludes family T, which is what the exclusion is for |
| Truncation vs the retired tag | truncate the title to 160 with `…` first, then append ` (retired)` | R-38 pins the 160-character truncation and E-57 pins the tag; the tag is a marker, not part of the title |
| Where the builder lives | `judge_llm.py`, per §11's R-38 row, called from `cli.py` for every eligible edge | the row names that module; building it once keeps the LLM message and the triage `state` from drifting |

**T-84 *(recorded)* — the adjacent subset, under both C-10 texts.** Run 2026-09-20 with
`google/gemini-3.8-flash` (OpenRouter, `--judge-concurrency 8`, 127 s for the six runs), three
runs per prompt text, over the eight adjacent edges, with no `--judge-budget` (the row's
precondition). The two arms are the shipped v1.16 text and the pre-v1.16 text recovered from this
repository's history by digest.

| Arm (`judge_prompt_sha256`) | Run | Adjacent edges downgraded | `unknown_rate` |
| --- | --- | --- | --- |
| v1.16 shipped (`dbac713c9a63185c590c4a2eb0ed2f52dc11f3cb414bea6495cf617152433f8f`) | 1 | 8/8 | 0.0250 |
| v1.16 shipped (`dbac713c…`) | 2 | 8/8 | 0.0000 |
| v1.16 shipped (`dbac713c…`) | 3 | 8/8 | 0.0000 |
| pre-v1.16 (`f6b124bdd6ea5948d052f6cb45de85eb5409e0165ba2371cd784a313472bcfd1`) | 1 | 8/8 | 0.0000 |
| pre-v1.16 (`f6b124bd…`) | 2 | 8/8 | 0.0000 |
| pre-v1.16 (`f6b124bd…`) | 3 | 7/8 | 0.0000 |

Per-edge verdicts (all three runs of each arm agree unless noted):

| Adjacent edge (citing id → the neighbour whose fact it asserts) | v1.16 shipped | pre-v1.16 |
| --- | --- | --- |
| `R-01 tests/test_core.py::test_add_rounding_fact` (→ K-02) | `EXECUTES_ONLY` ×3 | `EXECUTES_ONLY` ×3 |
| `R-01 tests/test_core.py::test_add_rounding_of_a_half_cent` (→ K-02) | `EXECUTES_ONLY` ×3 | `EXECUTES_ONLY` ×3 |
| `R-02 tests/test_core.py::test_subtract_rounding_fact` (→ K-02) | `EXECUTES_ONLY` ×3 | `EXECUTES_ONLY` ×3 |
| `E-02 tests/test_core.py::test_scale_empty_input_is_not_mutated` (→ C-02) | `EXECUTES_ONLY` ×3 | `EXECUTES_ONLY` ×2, `ASSERTS` ×1 |
| `I-001 tests/test_core.py::test_add_commutes_on_plain_sum` (→ R-01) | `EXECUTES_ONLY` ×3 | `EXECUTES_ONLY` ×3 |
| `I-001 tests/test_core.py::test_add_commutes_rounding_fact` (→ K-02) | `EXECUTES_ONLY` ×3 | `EXECUTES_ONLY` ×3 |
| `C-04 tests/test_summary.py::test_summary_total_rounding_fact` (→ K-02) | `EXECUTES_ONLY` ×3 | `EXECUTES_ONLY` ×3 |
| `C-04 tests/test_summary.py::test_summary_mean_rounding_fact` (→ K-02) | `EXECUTES_ONLY` ×3 | `EXECUTES_ONLY` ×3 |

**The honest outcome is "on none":** this model downgrades all eight adjacent edges with or without
the neighbourhood, so on this fixture `related` changed no verdict — the row's precondition holds
(the subset is not all `EXECUTES_ONLY`/`UNRELATED` across the two arms, and the labels are
downgrades the judge must not upgrade), but the change's *effect* on this model is nil and is
recorded as such rather than claimed. The row's own escape clause ("if the fixture's adjacent
subset is all `EXE`/`UNREL` the fixture is grown, not the claim") is one edge away from firing on
the pre-v1.16 arm; growing the subset toward edges a generous model over-credits is the lead this
measurement leaves for the next increment (the v1.9 evidence's gist-grading model,
`gpt-4o-mini`, is the candidate the D-08 row already names).

Reproducing it:

```bash
export SPECCHECK_JUDGE_URL=https://openrouter.ai/api/v1/chat/completions
export SPECCHECK_JUDGE_MODEL=google/gemini-3.8-flash
export SPECCHECK_JUDGE_API_KEY=...            # never recorded
uv run python tools/adjacent_eval.py --runs 3 --concurrency 8 --verbose
```

**T-49 *(recorded)* — the three independent runs.** Same model, same day, `tools/eval_judge.py`
against the 40-label file (39 judged edges after the F-1 relabel plus the new pair):

| Run | Accuracy | `unknown_rate` | `judge_prompt_sha256` | Verdict |
| --- | --- | --- | --- | --- |
| 1 | 1.0000 | 0.0250 | `dbac713c9a63185c590c4a2eb0ed2f52dc11f3cb414bea6495cf617152433f8f` | PASS |
| 2 | 1.0000 | 0.0250 | `dbac713c…` | PASS |
| 3 | 1.0000 | 0.0250 | `dbac713c…` | PASS |

Bar: ≥ 0.90 accuracy and ≤ 0.10 `unknown_rate` in each run — met with no pooling. The single
`UNKNOWN` per run is the same edge in each (`judge: unlocated clause`); its id is the one the run's
`--verbose` listing names. **The first T-49 attempt of this increment failed** — accuracy 0.7949 on
run 3 — which is what exposed F-1; the labels, not the model, were wrong.

**T-48 *(recorded)* — the self-application.** Recorded in §2 and re-run at this increment's gate:
`check --judge mock --strict` on this repository's own tree, `CONFORMING` with 0 dangling and
0 stale. The strict LLM arm is Phase B in §6.



**Why.** `PROPOSAL_v1.16_jev_pre_triage.md`, grounded in a `check --judge llm --strict` run of this
repository's own tree cross-checked edge-by-edge against `typesafe/jev-1.13`: `--judge-budget`
already truncated a judge run, but which edges were issued before the deadline was an accident of
declaration order, so a truncated run spent itself on whatever came first rather than on what was
hard. Jev's top-choice probability turned out to be a well-calibrated triage signal — monotonic
across four buckets, and 0 % recall for the only other triage-free signal already in the kernel
(`--judge mock` answers `ASSERTS` on everything) — and more than half of all judge-eligible edges
sit at $\geq$ 0.95, headroom a budgeted run was losing. D-29..D-32 (dedicated `SPECCHECK_JEV_*`
variables, a Note when the pass cannot matter, failure-orders-first, `ceil`) were confirmed in the
spec before this build; no fork was left for it.

**Plan.** A delta `IMPLEMENTATION_PLAN.md` plus one brief per wave
(`DETAILED_IMPLEMENTATION_PLAN_W1.md`..`W3.md`): W1 the C-17 provider and the CLI grammar, W2 the
K-16 ordering pass and K-12's `N%` count, W3 the recorded calibration, the README and the gates.
The plan's one fork — run T-91's measurement for real, or record it pending — was taken as
**run it**: the credentials and a judge model are present, and the alternative would have left the
spec's own calibration claim unchecked.

**Wave ledger.**

| Wave | Gate as run | Result | Commit |
| --- | --- | --- | --- |
| W1 — the C-17 provider and the `--jev-pre-triage` grammar (C-17, E-58; T-90) | `pytest tests/test_05_judge.py tests/test_07_cli.py -q`; `ruff check src tests` | 35 passed; clean | `e4b9f2a` |
| W2 — the triage pass orders and truncates the queue (K-16, K-12 `N%`, I-015, E-59; T-89) | `pytest tests -q --junitxml=junit.xml`; `ruff check src tests`; `speccheck --self-check` | 123 passed; clean; `self-check: ok` (goldens byte-identical — the flags default off) | `5cef24d` |
| W3 — recorded calibration, README, gates (T-91) | `pytest tests -q --junitxml=junit.xml`; `ruff check src tests`; `speccheck --self-check`; `check … --judge mock --strict`; `check … --judge llm --strict` | 124 passed; clean; `self-check: ok`; `CONFORMING - 233/233 passing (100.0%) … 0 dangling, 0 stale`, exit 0; see §6 | this commit |

**W1, test-first:** `JevConfig.from_env`, `render_state`, `build_body`, `parse_confidence` and
`JevTriage` were written against T-89's request-shape test (the pinned `state` template, the four
criteria, the bearer header, `p(e) = max(probabilities)`, and the seven ways a reply is *not*
usable) and T-90's usage-error test (`N%` without a running triage, the `SECONDS` form still
accepted-and-ignored under `--judge mock`, `SPECCHECK_JEV_API_KEY` required only when the pass
runs, no key in any message). C-17's strings are not new text: they are the ones
`tools/judge_crosscheck_tasks.py` already sends, which is what makes the §1 calibration figures
reproducible against the kernel's own request.

**W2, test-first:** `run_triage` and `run_judge(issue_count=...)` were written against T-89's
end-to-end test — ten eligible edges, one C-17 transport stub failing one edge with HTTP 500, one
judge stub recording the order it was asked in: `30%` issues exactly the three least confident
(the failed edge first), `100%` all ten, `0%` none with zero judge calls, a total C-17 failure
leaves `judge_available`/`unknown_rate` as a triage-free run does, and an unlimited budget reorders
without changing a byte of the report apart from the D-30 Note. The `N%` count lives in
`run_judge` beside the deadline it mirrors, so `budget_unjudged`, the E-35 Note, `unknown_rate`,
`judge_available` and the C-11 indicator keep one source. Smoke-tested against the real provider
path with an unreachable endpoint (695 edges, 695 E-59 failures, `0%` issuing none, indicator
drawn and erased, report written) — the run in which the E-59 Note and the "no effect" ordering
were first observed end to end.

**T-91 *(recorded)* — the calibration curve, re-measured.** Run 2026-09-20 against this
repository's own `SPEC.md` (v1.15) / `src` / `tests`, exactly as the row pins: a
`check --judge llm --strict` run, its committed verdicts (recorded `UNKNOWN` excluded) bucketed by
each edge's C-17 $p(e)$ against Jev's own `answers.verdict.choice`.

| Input | Value |
| --- | --- |
| Judge | `openai/gpt-4o-mini` via OpenRouter, `--judge-concurrency 8`, 2 m 30 s, `unknown_rate` `0.0978`, 5 `WEAKLY_PASSING` ids (`E-07`, `E-16`, `E-25`, `T-61`, `T-76` — all pre-existing), `judge_prompt_sha256` `f6b124bdd6ea5948d052f6cb45de85eb5409e0165ba2371cd784a313472bcfd1` |
| Triage | `SPECCHECK_JEV_MODEL=~typesafe/jev-latest` (the C-17 default — probed and accepted by the endpoint before the batch), `--concurrency 8`, 695/695 requests succeeded in 17.1 s, 0 failures |
| Population | 695 judge-eligible edges; the judge committed to 627 (68 recorded `UNKNOWN` excluded) |

| Jev $p(e)$ bucket | committed edges | agreement with the recorded verdict |
| --- | --- | --- |
| $\geq$ 0.95 | 306 | 288/306 = 94.12 % |
| 0.80–0.95 | 102 | 84/102 = 82.35 % |
| 0.60–0.80 | 106 | 51/106 = 48.11 % |
| $<$ 0.60 | 113 | 52/113 = 46.02 % |

Overall 475/627 = 75.76 %. The buckets are monotonically non-increasing, so T-91 passes on this
run. Same shape as the proposal's §1 figures (94.58 / 78.48 / 54.64 / 47.75 % over 582 edges) on a
larger tree and a different Jev build: the alias is floating by design, which is exactly the drift
this row exists to watch. Per-label, Jev recovers 104/179 = 58.1 % of the committed `UNRELATED`
edges — the class `--judge mock` cannot see at all. Artifacts:
`build/speccheck-llm-v115/speccheck.json`, `build/census/crosscheck-v115/{tasks,results}.jsonl`.

Reproducing it, in the order it ran (the first two commands are the repository's own offline
cross-check tools, which build the same C-17 `state` the kernel sends):

```bash
uv run speccheck check --spec SPEC.md --src src --tests tests --results junit.xml \
    --judge llm --strict --judge-concurrency 8 --out build/speccheck-llm-v115
uv run python tools/judge_crosscheck_tasks.py --report build/speccheck-llm-v115/speccheck.json \
    --tests tests --out build/census/crosscheck-v115/tasks.jsonl
uv run python tools/jev_client.py --task-file build/census/crosscheck-v115/tasks.jsonl --id ALL \
    --model "~typesafe/jev-latest" --concurrency 8 --out build/census/crosscheck-v115/results.jsonl
# then join each result to its task and bucket by p(e) = max(answers.verdict.probabilities)
```

**Spec defects found by this build:** none. The re-read found no row of v1.15 disagreeing with the
implementation, and no earlier row that the triage pass invalidated; `SPEC.md` was not edited by
this increment.

## 0f. v1.14 increment (2026-09-20) — declared vs. incidental citations (R-39, C-14, C-15, C-16, I-014, E-56)

**Why.** `PROPOSAL_v1.15_declared_vs_incidental_citations.md`, grounded in `JUDGE_CROSSCHECK_REPORT.md`
§2b: a `check --judge llm` run of this repository's own tree with `gpt-4o-mini`, cross-checked
edge-by-edge against an independent second model, found 153/613 genuine conflicts (both models
committed and disagreed), 60 of them concentrated in five ids reused as generic fixture data
(`R-01` 36/57, `C-01` 7/34, `R-07` 6/7, `C-06` 6/7, `C-03` 5/12) but 93/496 (18.8%) still
conflicting once those are excluded. Three non-`R-01` conflicts read in full all showed a test
citing an id as placeholder data while proving something else, with neither its own docstring nor
any comment naming that id. The spec already states the mitigation — §9's preamble requires every
test to cite its own ids "in its docstring or a comment" — and the kernel already had the data to
apply it; it was throwing the distinction away before the judge ever saw the edge. D-26 (advisory
only, no coercion) and D-27 (whole-line-comment detection, no token-level parsing) were confirmed
in the spec before this build; no fork was left for it.

**Plan.** A compact `IMPLEMENTATION_PLAN.md` delta, three waves in dependency order: W1 the
`declared` fact (Attributor + Grapher), W2 the judge request and the C-10 instruction text, W3 the
report visibility (`tests[].declared`, `metrics.declared_ratio`) and the regenerated goldens. T-87
is the recorded, non-gating re-run of the proposal's three evidence edges.

**Wave ledger.**

| Wave | Gate as run | Result | Commit |
| --- | --- | --- | --- |
| W1 — the `declared` fact (R-39, C-14, E-56, I-014) | `pytest tests/test_02_attribution.py -q`; full suite; `ruff check src tests` | new T-85 unit tests green; full suite green except the two pre-existing stale rows (T-48's id count, the shipped-prompt hash) the spec edit had already made red by design | `5e17dae` |
| W2 — the judge is told (C-15, C-10) | `pytest tests/test_05_judge.py -q`; full suite; ruff | 13/13 judge tests green incl. the new C-15 request check and T-54's C-10 byte-equality; full suite green except T-48's stale count | `5f7d818` |
| W3 — visibility and goldens (C-16, T-86, T-88) | `pytest tests -q --junitxml=junit.xml`; `ruff check src tests`; `speccheck --self-check`; `speccheck check … --judge mock --strict` | 119/119 green; clean; `self-check: ok`; `CONFORMING - 225/225 passing (100.0%) … 0 dangling, 0 stale`, exit 0 | this commit |

**W1, test-first:** the classification was written against T-85's unit half, which asks the
Attributor directly (`attribute_file` on a `ScannedFile`) for `Citation.declared` on a docstring
line, a multi-line docstring's *second* line, a whole-line `#` comment, a string literal, a code
line with a trailing comment, the file-level case, and the Swift `///` / `/** … */` equivalents. The
Swift half exposed a design question the plan had already answered: `delimit_swift` now returns the
per-line `_Line.doc` flags it always computed (alongside cases and undelimited names) rather than a
second doc-comment detector being written next to it — C-14's "reused rather than re-detected",
enforced by keeping the detector singular. `TestEdge.declared` is true iff *any* citation line of
the edge is DECLARED (C-14's last paragraph), and the same pass counts R-39's population for the
metric — test-kind citations of in-scope R/C/I/K/E ids inside attributed non-file-level cases.
The one interpretation this build had to fix where the contract left a choice is recorded in §3
below (B-16).

**W2, test-first:** `JudgeRequest.declared` (after `testcase`) and `to_json`'s key order were
written against a new test that drives `check --judge llm` through the recorded HTTP stub and reads
`declared` `true` for a docstring-declared edge and `false` for a citation that is only example
data; `build_request` gained the parameter and `cli.py` passes `edge.declared`. The shipped C-10
text gained the field definition and the skepticism rule; T-54's existing byte-equality assertion
(comparing `src/speccheck/judge_prompt.md` to the C-10 block in `SPEC.md`) is what caught the text
staying in step, and `judge_prompt_sha256` moved to
`f6b124bdd6ea5948d052f6cb45de85eb5409e0165ba2371cd784a313472bcfd1`. T-33 and T-74 were updated for
the new key (`declared` between `statement` and `file`), not the reverse: the request shape is
`C-06`'s, and T-74's "unchanged keys" wording was stale — see F-102.

**W3, test-first:** `tests[].declared` and `metrics.declared_ratio` were written against T-86
(the fixture's new incidental edge) and T-88 (present under `--judge none` and `mock`, recomputable
from the report's own evidence, identical under both modes). `SCHEMA_VERSION` went to `"1.5"` and
T-79's literal was updated with it. The fixture gained one test whose docstring names C-01 while
its body cites R-02 only as example data (T-86), its `junit.xml` result, and the two
`judge_labels.json` entries T-49's exact-coverage assertion requires; both goldens and then
`_selfcheck/` were regenerated. The regenerated Python fixture reports `declared_ratio` `0.9474`
(18 of 19 R-39 citations DECLARED — the new edge is the one INCIDENTAL); the Swift fixture reports
`1.0` (every citation is a doc-comment line). The one-time v1.13 → v1.14 golden diff is exactly the
`schema_version` bump, one `declared` bool per `tests[]` entry, the `declared_ratio` metric, and
the two rows the new T-86 test touches in §3/§7/§8 of the Markdown — plus the C-12 Notes, which do
not change.

**Spec defects found by this build (fixed as `fix(spec)`, document-only).**

| F-nnn | Where | What | Fix |
| --- | --- | --- | --- |
| F-101 | `SPEC.md` §3.3 artifact table | still pinned `speccheck.json` at `schema_version: "1.4"` while C-07 (the same edit) says `"1.5"` | the row now reads `"1.5"` and names `declared`/`declared_ratio`; no id semantics changed, `SPEC.md`'s version header stays v1.14 (this corrects v1.14's own rows; the next version number is reserved) |
| F-102 | `SPEC.md` T-74 | "under the unchanged keys `{id, statement, file, start, end, source}`" predated C-15's `declared`, which the same v1.14 edit added to C-06 | T-74 now reads `{id, statement, declared, file, start, end, source}` and cites C-15; the test was updated with it |

Neither changes a requirement, contract, or status; both are text that v1.14's own edit should have
carried. No other disagreement between the spec's diagrams, rows, and formulas was found on the
re-read.

**T-87 *(recorded)* — the advisory instruction's effect, measured.** The three edges the proposal
named were re-run under the v1.14 C-10 text with the same model (`openai/gpt-4o-mini` via
OpenRouter), each through the kernel's own `build_request` with the C-14 `declared` value, on
2026-09-20; `judge_prompt_sha256`
`f6b124bdd6ea5948d052f6cb45de85eb5409e0165ba2371cd784a313472bcfd1`:

| Edge | `declared` | pre-v1.14 (`gpt-4o-mini`) | Jev (independent) | v1.14 (`gpt-4o-mini`) |
| --- | --- | --- | --- | --- |
| `R-03` / `test_fenced_code_blocks_are_ignored` | false | `ASSERTS` | `UNRELATED` | `UNRELATED` |
| `R-03` / `test_row_and_heading_grammar_edge_cases` | false | `ASSERTS` | `UNRELATED` | `UNRELATED` |
| `R-02` / `test_judge_called_once_per_eligible_edge_only` | false | `ASSERTS` | `UNRELATED` | `ASSERTS` |

The honest outcome is "moved on some": two of three now agree with the independent model, the third
still credits `ASSERTS`. Per the proposal's §3 that outcome does not by itself force D-26's `no`
branch (which stays the fallback if a later run shows the instruction moves nothing), and it does
not gate this build — T-87 is a recorded observation about a live model's compliance with an
advisory instruction, exactly the caveat T-49 already carries. Part C is independent of it and
costs nothing under `--judge none`.

## 0e. v1.13 increment (2026-09-19) — spec-internal edges (C-12) and the `impact` subcommand (C-13)

**Why.** `PROPOSAL_v1.13_impact.md`: the spec already carries a dependency graph in its own prose
(134 of 203 v1.12 ids name another id in their statement — 186 `depends_on`, 240 `verifies`; the
§12 decision rows add 110 `affects` edges) and nothing read it. v1.13 extracts that graph
mechanically and adds `speccheck impact` to walk it for change-impact analysis. D-24 and D-25 were
confirmed in the spec before the build (no fork left for this build).

**Note on this report's own upkeep.** §5's traceability matrix was last fully extended for the
v1.11 increment; the v1.12 delta (D-23, I-012, E-52, T-78) and the Swift-adapter-era ids (E-42
through E-52) were never backfilled into it, and the E family in §5 stops at E-41. That gap
predates this build and is out of the scope asked of it (which was the v1.13 delta specifically);
it is flagged here rather than silently left to look complete. Only the twelve v1.13 rows (R-36,
R-37, C-12, C-13, I-013, E-53, E-54, E-55, T-79..T-82) are added below, at their correct family
position.

**Plan.** No `spec-plan` multi-document run was needed for a delta this bounded; a compact
`IMPLEMENTATION_PLAN.md` covers it directly: W1 the C-12 edges (extractor + `speccheck.json`), W2
the `impact` subcommand (C-13), W3 the backtest tool (D-24, recorded, non-gating).

**Wave ledger.**

| Wave | Gate as run | Result | Commit |
| --- | --- | --- | --- |
| W1 — C-12 edges | `pytest tests/test_10_edges.py -q`; full suite; ruff; golden fixtures regenerated and diffed (schema bump + `decisions`/`edges` + one new Note the only delta on both fixtures) | 9/9 new tests green; full suite green except the twelve new v1.13 ids (not yet cited); clean | `e5fc47c` |
| W2 — `impact` subcommand | `pytest tests/test_11_impact.py -q`; full suite; ruff; a real `impact --changed K-02` run against the golden fixture, diffed and blessed | 9/9 new tests green (one, T-82's presence check, red pending W3); full suite 111/112 (same one red); clean | `acd2f08` |
| W3 — backtest (recorded) | `python tools/impact_backtest.py --help` (exit 0); a real run against the two ranges named in the spec's T-82 row; full suite; ruff; `speccheck --self-check`; `speccheck check --strict` on this repository | `--help` exit 0; real run exit 0, report written; 112/112; clean; `self-check: ok`; `CONFORMING - 215/215 passing (100.0%) … 0 dangling, 0 stale`, exit 0 | this commit |

**W1, test-first:** `Decision`/`Edge` dataclasses and `_decision_rows` (the C-01 (c) table-block
scanner: a maximal run of row lines outside fences, second row a separator, header cell
`affects` case-folded) written against `test_decision_table_found_by_affects_header_cell_case_insensitively`,
which failed with `AttributeError: 'SpecIndex' object has no attribute 'decisions'` until the
field existed; `_build_decisions_and_edges` (statement-token scan, direction normalization for
`verifies`, `retired` flagging) against the other eight `test_10_edges.py` functions. Two
pre-existing tests broke as a direct, correctly-specified consequence and were updated rather than
the new code: `test_heading_section_bodies_title_cap_and_line_model` (the K-14 truncation marker
itself contains the literal text "K-14", so a truncated statement now also yields an "edge to
undeclared id" Note — C-12 says "after the K-14 cap", i.e. the already-marked text) and its two
fenced example ids (`R-99` in C-01's pinned block, `R-98` in C-05's body) now also yield Notes.
`fixtures/target/SPEC.md` gained a three-row decision table (T-79's own requirement: two declared
Affects targets, one retired, one undeclared); the undeclared target was deliberately chosen as
`E-45` — a real id of *this* project's own `SPEC.md` — not an arbitrary large number, because the
fixture is packaged under `src/speccheck/_selfcheck/` and scanned as ordinary source by this
project's own self-application (T-48): an arbitrary "obviously fake" id like the fixture's other
examples would dangle-cite there, while a real outer id does not, the same trick the original
fixture's planted defects (`R-09`, `R-04`, `E-02`) already relied on.

**W2, test-first:** `resolve_changed_ids` (I-011 normalization, E-53) against
`test_resolve_changed_ids_normalizes_and_validates`; `diff_changed_set` (the five reasons, in
order) against `test_diff_changed_set_reasons_in_fixed_order`; `walk` (breadth-first, reverse
`depends_on` from an obligation, forward `affects` from a decision, smallest `via` per C-12 order)
against `test_walk_reverse_depends_on_and_affects_with_shortest_via` and
`test_walk_depth_cap_is_a_prefix_with_a_note` — the latter written to pin I-013 (a depth-limited
run is an exact prefix of the unbounded one) directly, rather than trusting it by inspection.
`report.py` gained `write_named_files`, a generalization of the existing `write_reports` so the
same temp-and-rename-and-cleanup discipline (I-001) serves both file pairs without duplicating it;
`write_reports` itself became a one-line wrapper, and T-38/T-45 (already in the suite) caught
nothing broken by the refactor. `cli.py`'s PATHS closure was lifted out of `parse_config` into
`_resolve_paths(flag, values, root, default)` so `impact`'s "no directory default" need (an
absent `--src`/`--tests` means *not scanned*, not the `check` default) shares the same E-52/I-012
logic with a different `default` argument, rather than a second copy. `--results`/`--judge`/
`--strict`/etc. are simply never defined on the `impact` subparser, so argparse's own
unrecognized-argument path supplies E-54's exit `2` for free — cheaper and no less correct than a
hand-written rejection, verified by `test_impact_usage_and_input_errors`.

**Live run against the golden fixture.** `speccheck impact --spec SPEC.md --changed K-02 --src
src --tests tests` on `fixtures/target/`: 1 changed, 1 impacted (`C-04 -depends_on-> K-02`, depth
1), 5 to re-verify (`T-03, T-04, T-05, T-06, T-07`), 3 re-cite rows, 8 test cases — read by hand
against the fixture's own C-04/K-02 rows before being blessed as `golden/impact.json` and
`golden/IMPACT_REPORT.md`; both fixtures (`target`, `target-swift`) and `_selfcheck/` regenerated
and diffed, confirming the only delta on `target-swift` is the schema bump, an empty `decisions`
array, the `verifies`/`depends_on` edges its own statements already carry, and one new Note.

**The backtest (W3, T-82, recorded — not gating).** `tools/impact_backtest.py`: `git archive` a
read-only tree at each range's build-end commit (no worktree), `git show` both ends of the spec
range, run `impact --against --depth 0` in-process (chdir into the tree first — `speccheck`
resolves relative paths against the process cwd, not `--root`, matching every other invocation in
this project), diff the build range with `-U0` for exact touched new-file line ranges, and score
recall/precision per depth cutoff against citations from a `check` run on the same tree.

| Range | d=1 recall/precision | d=2 | d=3 | d=∞ | Chosen depth |
| --- | --- | --- | --- | --- | --- |
| v1.6→v1.8 (spec `d170433^..c0a770a`, build `2a25569..2635298`) | 0.12 / 0.31 | 0.12 / 0.29 | 0.12 / 0.29 | 0.12 / 0.29 | unbounded (never reaches 0.80) |
| v1.8→v1.11 (spec `2635298..c1e3d87`, build `330dd4e..dfea1a6`) | 0.22 / 0.82 | 0.27 / 0.85 | 0.27 / 0.85 | 0.27 / 0.85 | unbounded (never reaches 0.80) |

Recall does not clear the bar's 0.80 threshold at any depth on either range — every miss is
explained as one class, read from the actual miss lists (`build/impact_backtest/c1e3d87.md`):
almost every "touched, never predicted" id shares its only build-tree citation with dozens of
others on the same one or two lines — the module docstring's "Spec IDs realized here (§11): …"
summary at the top of `extract.py`, `graph.py`, `judge.py`, etc. A commit that edits that summary
line (adding one new id to the list, which most commits in this codebase's own history do) marks
every id already listed there as "touched" under the diff-hunk heuristic, even though only one of
them actually changed — inflating the *actually-affected* denominator with ids `impact` was never
asked to predict and had no way to. This is a defect in the backtest's touched-line heuristic, not
in `impact` itself or in the spec's own cross-references (the `depends_on`/`verifies`/`affects`
edges it reads are unaffected by this and were spot-checked by hand above): a citation on a shared
summary line is not evidence that *that specific id's* behavior changed. The bar's fallback branch
("every miss explained") is taken rather than the recall threshold; `--depth` keeps its default of
`1` from the proposal (D-24's own justification — the direct set as the useful answer — stands
independently of this backtest's noisy denominator). A cleaner backtest would exclude a file's own
summary-comment line from "touched", or weight a citation by how many ids share its line; left as
a follow-up, not attempted here (T-82 is recorded, not gating, precisely for findings like this).

## 0d. v1.11 increment (2026-09-18) — clause-grounded verdicts, recorded tests, a body in the T-49 fixture

**Why.** Three spec increments in one build. v1.9 (`7dde608`, `PROPOSAL_v1.9_clause_grounding.md`): with bodies
in the statement, `gpt-4o-mini` graded long contracts by their gist — 13 of 18 stable downgrades on the mdv
tree were tests asserting a body clause nearly verbatim — while `gemini-3.8-flash` located the clause; and
T-49's nine labels could not tell the two apart. v1.10 (`dd29c4d`): under an honest judge the presence checks
that keep T-48/T-49/T-51 cited are `EXECUTES_ONLY` by construction, so `--strict --judge llm` went red on
this repository for a reason the spec intended but had not written down (D-22). v1.11 (`c1e3d87`): the seven
findings of the v1.10 review (F-401..F-407), chiefly one `schema_version` literal and an ordered validator.

**Plan.** `IMPLEMENTATION_PLAN.md` (`2d8f743`): W1 apparatus + extractor, W2 kernel + reports + goldens,
W3 prove; no fork left for the requester (D-21/D-22 confirmed in the spec, models settled by D-08).

**Wave ledger.**

| Wave | Gate as run | Result | Commit |
| --- | --- | --- | --- |
| W1 Apparatus + extractor | `pytest tests/test_01_extraction.py tests/test_08_golden.py -q -k "recorded or long_body"`; ruff; full suite | green; clean; full suite **20 failed / 66 passed** — every failure reads the golden fixture or its goldens (the plan named three of them: T-36, T-43, T-46; the fixture's five new ids also move T-24, T-34, T-35, T-47 ×10, T-73 and the labels-coverage check). Recorded, closed in W2. | `330dd4e` |
| W2 Kernel + reports + goldens | `pytest tests -q --junitxml=junit.xml`; ruff; `speccheck --self-check`; `tools/sync_selfcheck.py --check`; `speccheck --version`; Phase A | 88 passed; clean; `self-check: ok`; in sync; `speccheck 1.11.0`; `speccheck: CONFORMING - 200/200 passing (100.0%), 0 failing, 0 skipped, 0 weak, 0 unverified, 0 untested, 0 uncited; 0 dangling, 0 stale; judge=mock`, exit 0. No hunk in `attribute.py`, `results.py`, `swift.py`. | `1f24c57` |
| W3 Prove | live wire pass; Phase B ×2 models; T-49 ×3 ×2 models; README; this section | below | the `docs(speccheck)` commit carrying this report |

**Build, test-first, T-76 → T-77 (extract) → T-75 → T-77 (graph/report):**

| Change | Where | Test (written first; failed for) |
| --- | --- | --- |
| Golden fixture: `### C-04 Summary report` — fenced dataclass + six numbered rules, 2,834-byte statement; `summary.py`; six tests (four one-clause `ASSERTS`, one executes-only, one asserting R-01 while citing C-04) proved passing in a scratch copy; six JUnit rows; `judge_labels.json` 9 → 21 | `fixtures/target/**` | T-76 (`no heading-declared contract with a body >= 2048 bytes`) |
| `*(recorded)*`: first token of a row's decoration or after a heading's id (then stripped from the title); `SpecId.recorded`; E-50 Note on a non-T id | `extract.py` | T-77 extract half (`AttributeError: recorded`) |
| `Verdict`/`JudgedVerdict.clause`; `locate_clause` (K-15: collapse, trim, cut 280, substring ≥ 12 or equal to a short statement); `validate` as the C-06 numbered list, first match wins; non-string clause = absent; every coerced `UNKNOWN` records `clause ""` | `judge.py` | T-75 (`ImportError: locate_clause`) |
| reply `clause` passed through; mock clause = collapsed-statement prefix (always LOCATED) | `judge_llm.py`, `judge_mock.py` | T-75, T-54, T-74 |
| recorded ids skip step 5 and eligibility; `judge_strength` over `PASSING ∖ RECORDED` | `graph.py` | T-77 graph half (statuses wrong until the skip landed) |
| `recorded` after `family`, `clause` after `verdict`, `SCHEMA_VERSION "1.3"`, §8 Clause column (80 chars, em dash for `""`), `T-48 (recorded)` / `~~T-03~~ (recorded)` | `report.py` | T-77, T-34, T-35 |
| `judge_prompt.md` = the v1.9 C-10 text; `judge_prompt_sha256` `6a05eb0dede74b3108322fdca58652b7e9e8bde328e02293c3be4d47df775052` | package data | T-54, T-74 |
| Goldens regenerated by the tool and diffed before acceptance — Swift: only `schema_version`, `clause`, `recorded` (summary byte-identical); Python: those plus C-04/T-04..T-07 rows and their metrics, which matched the hand computation written into T-24 beforehand (13/19, 13/14, C 2/3, T 6/7) | `fixtures/*/golden`, `_selfcheck/` | T-46, T-71, T-60, T-73 |
| Test hygiene: stubbed LLM replies carry a located clause (the spec now requires one); T-34 pins `VERDICT_KEYS`; T-73 asserts the C-07 schema value, never a literal (F-401); T-48 `DECLARED_IDS = 200` | `tests/` | — |

**Live pass (the wire).** `fixtures/target` through OpenRouter `gpt-4o-mini` at `--verbose DEBUG`: every reply carried
a `clause`; every recorded `ASSERTS`/`EXECUTES_ONLY` clause is a collapsed substring of `C-04`'s statement (checked);
three of C-04's six edges were coerced `UNKNOWN` — one visibly because the model quoted the rule but dropped the
backticks around one word (`` `ordered` `` → `ordered`), which K-15's verbatim rule rejects by design (D-21). The
key never appears in the capture.

**Phase B on this tree (488 judged edges; T-48, T-49, T-51 recorded and never sent).**

| Model | Summary line | `unknown_rate` | Weak | Wall-clock |
| --- | --- | --- | --- | --- |
| `google/gemini-3.8-flash` @8 | `speccheck: CONFORMING - 200/200 passing (100.0%), 0 failing, 0 skipped, 0 weak, 0 unverified, 0 untested, 0 uncited; 0 dangling, 0 stale; judge=llm` | 0.0041 (1 unlocated clause, 1 timeout) | none | 5 min 28 s |
| `openai/gpt-4o-mini` @32 | `speccheck: NOT CONFORMING - 188/200 passing (94.0%), 0 failing, 0 skipped, 12 weak, 0 unverified, 0 untested, 0 uncited; 0 dangling, 0 stale; judge=llm` | 0.0799 (39 unlocated clauses) | E-07, E-08, E-10, E-16, E-22, E-48, E-49, T-02, T-12, T-29, T-61, T-76 | 29 s |

Read edge by edge, gpt-4o-mini's twelve are false: it answers `UNRELATED` for tests that plainly assert the row
(E-16's `test_ungrounded_answers_are_coerced_to_unknown`, E-22's `test_several_citations_in_one_case_yield_one_edge`,
T-29's), where gemini answers `ASSERTS` and quotes the row; and where gpt says `ASSERTS` its quote often fails K-15.
Under the v1.9 clause-first prompt gpt-4o-mini's `UNRELATED` count went from 13 (v1.8 prompt) to 96. **The gate result
that stands for this build is gemini's** — it is the model that passes T-49 (below), which is the spec's own criterion
for a usable judge; gpt-4o-mini's line is recorded as what it is, a model that no longer meets R-26/T-49 under this
prompt, not as a defect in the tree.

**T-49, three runs per model over the 21-label set (T-76), `judge_prompt_sha256 6a05eb0d…5052`, 2026-09-18.**

| Model | Run 1 | Run 2 | Run 3 | T-49 |
| --- | --- | --- | --- | --- |
| `google/gemini-3.8-flash` | 1.0000 / 0.0000 | 1.0000 / 0.0000 | 1.0000 / 0.0000 | **PASS** |
| `openai/gpt-4o-mini` | 1.0000 / 0.1429 | 1.0000 / 0.1429 | 1.0000 / 0.1429 | **FAIL** (unknown_rate > 0.10; the same three edges each run, all `judge: unlocated clause`) |

The fixture now does what Part A of the v1.9 proposal said it would: it separates a judge that locates clauses
from one that does not — and the separation is on *quoting*, not on judgment (gpt-4o-mini is 1.000 accurate on the
edges it locates). D-08's answer for this build: `gemini-3.8-flash`. An observation for `spec-writing`, not a change
made here: the backtick-dropping case suggests K-15 could normalise Markdown code spans before matching; D-21 chose
verbatim, and the v1.9 proposal's §4 lists why.

**Traceability.** §5 gains rows for R-34, R-35, K-15, E-48..E-51, T-75..T-77 from `build/speccheck/speccheck.json`.

**Deviation from the plan, stated.** None in order or ownership. W1's fallout was 20 failing tests rather than the
three the plan named — the fixture's five new ids touch every golden-derived expectation; all closed in W2. The plan's
Phase B expectation ("both `CONFORMING`") held for gemini only.

## 0c. v1.8 increment (2026-09-18) — a heading-declared ID's statement is its title plus its section body

**Why.** Two `--judge llm` runs over the same 130 edges of the MonteCarloPi Swift build
(`openai/gpt-4o-mini` 65/70, 0 weak; `google/gemini-3.8-flash` 56/70, 9 weak, 15 `UNRELATED`,
3 `UNKNOWN`) disagreed almost entirely on `###`-declared contracts. Both judges had been handed a
title (`Data structures`, `` `EstimationWorker` (an `actor`) ``) and never the pinned API beneath
it; one guessed generously, the other refused. `PROPOSAL_v1.7_heading_bodies.md` has the edges.

**Spec first.** `SPEC.md` v1.6 → v1.7 (`d170433`: R-33, C-01 (b), C-02 `title`, C-06, C-07
`schema_version` `"1.1"`, C-08, C-10 any-clause rule, K-14, E-46, E-47, T-72..T-74, D-20) →
`spec-review` (`SPEC_REVIEW_REPORT.md`, F-301..F-307: Level 3, READY WITH MINOR FIXES) → v1.8
(`c0a770a`: the line model F-301, T-72/T-73 as properties F-302, T-49 staleness rule and D-08
re-opened F-303, ATX corner cases F-304, empty title F-305, C-09 cited F-306, editorial F-307).
D-20 confirmed by the requester (code blocks included; cap raised from the proposal's 8,192 to
16,384 bytes because this document's own C-03 is 8.4 kB). On the v1.8 spec the 1.6.0 code read
`79 passed, 2 failed` — T-54 (`judge_prompt.md` ≠ the new C-10 block) and T-48 (183 ≠ 190 ids):
the spec moving, not the code breaking.

**Plan (Phase 0).** `IMPLEMENTATION_PLAN.md` + `DETAILED_IMPLEMENTATION_PLAN_W1.md`/`_W2.md`
(`be1b8cc`): W1 extractor, W2 consumers + goldens + version, W3 prove. Fork settled by the
requester before W1: Phase B and the T-49 re-runs use OpenRouter `openai/gpt-4o-mini`.

**Wave ledger.**

| Wave | Gate as run | Result | Commit |
| --- | --- | --- | --- |
| W1 Extractor | `pytest tests/test_01_extraction.py -q`; `ruff check`/`format --check`; full suite | 10 passed; clean; full suite **6 failed / 76 passed** — the plan predicted 2 (T-54, T-48); the other four (T-36, T-43, T-46, T-71) compare against goldens whose fixture `C-01` statement now carries its body, i.e. W2's regeneration. Recorded, not hidden. | `2a25569` |
| W2 Consumers, goldens, version | `pytest tests -q --junitxml=junit.xml`; `speccheck --self-check`; `tools/sync_selfcheck.py --check`; `speccheck --version`; Phase A | 84 passed; `self-check: ok`; in sync; `speccheck 1.8.0`; `speccheck: CONFORMING - 190/190 passing (100.0%), 0 failing, 0 skipped, 0 weak, 0 unverified, 0 untested, 0 uncited; 0 dangling, 0 stale; judge=mock`, exit 0. No hunk in `graph.py`, `results.py`, `attribute.py`, `swift.py`, `judge_mock.py`, `judge.py`, `judge_llm.py` (the spec says they are unchanged). | `ef20ef0` |
| W3 Prove | live wire pass; Phase B; T-49 ×3 (twice); README; this section | below | the `docs(speccheck)` commit carrying this report |

**Build, test-first, T-72 → T-73 → T-74:**

| Change | Where | Test (written first; failed for) |
| --- | --- | --- |
| Lines rule: split on `\n`, strip a trailing `\r`; `is_blank` | `extract.py` `split_spec_lines`, `is_blank` | T-72 (`ImportError: STATEMENT_CAP_BYTES`) |
| HEADING LINE: ≤ 3 leading spaces, 1–6 `#`, whitespace or EOL; shared fence tracker; body ends only at level ≤ own | `extract.py` `heading_level`, `_heading_lines`, `section_body` | T-72 |
| `title` (closing `#` run stripped, collapsed); `text` = title / title+`\n`+body / body alone | `extract.py` `heading_title`, `iter_declarations` | T-72 |
| K-14 cap at a line boundary, marker line, `SpecIndex.notes` | `extract.py` `cap_statement`, `parse_spec` | T-72 |
| JSON `title` before `statement`; `SCHEMA_VERSION = "1.1"`; Markdown Statement cell from `title`; K-14 Notes into the report | `report.py`, `cli.py` | T-73 (`'1.0' == '1.1'`), T-34 |
| C-10 any-clause bullet, byte-equal to the spec block; new `judge_prompt_sha256` `fc7dc32be9d2ccf184605ae586e5e70aa712d49c56f7807d14f85392bcbfad00` | `judge_prompt.md` | T-74 (rule absent), T-54 |
| `__version__ = "1.8.0"` | `__init__.py` | T-50 (needed `uv sync --reinstall-package speccheck` to refresh the editable install's metadata) |
| goldens regenerated by the tool and diffed before acceptance: only `schema_version`, one `title` per id, and `C-01`'s `statement` changed in each fixture; both `SPEC_CONFORMANCE_REPORT.md` and the Swift `summary.txt` byte-identical to v1.6 (the one-time diff T-73 delegates here) | `fixtures/*/golden/speccheck.json`, `_selfcheck/` | T-46, T-71, T-60, T-73 |
| T-55's heading expectation moved to `.title` (its `## C-03` heading now owns the rows beneath it as body — E-47) with the E-47 property asserted; T-48 `183` → `DECLARED_IDS = 190`; T-72 fixture lines naming undeclared `R-98`/`R-99` marked `speccheck:ignore` (they were 3 dangling citations in Phase A) | `tests/` | — |

**Live pass (the wire, not the stub).** `fixtures/target` through OpenRouter at `--verbose DEBUG`:
the `judge>` line for `C-01` carried `statement` = `` `divide(a, b)` raises `ZeroDivisionError` when `b == 0` `` + `\n` + `The error message MUST name the dividend.` under exactly the keys `{id, statement, file, start, end, source}`; the reply came from `openai/gpt-4o-mini`; the API key appears nowhere in the capture.

**Phase B on this tree.** First run: `NOT CONFORMING - 189/190 … 1 weak` — E-42's only citing test
(`test_swift_brace_fallback_and_braces_in_strings_and_comments`) judged `EXECUTES_ONLY` ("does not
assert the specific brace depth conditions"). The test did assert E-42's Note and `cases == ()`, but
E-42's "whole file is one file-level case" was only implied; the test now asserts the file-level
case's name, span, and that every citation in the fallback file belongs to it. Second run, 436
judged edges, 34 s at concurrency 32:
`speccheck: CONFORMING - 190/190 passing (100.0%), 0 failing, 0 skipped, 0 weak, 0 unverified, 0 untested, 0 uncited; 0 dangling, 0 stale; judge=llm`
— `unknown_rate 0.0000`, `judge_strength 0.9947` (390 `ASSERTS`, 30 `EXECUTES_ONLY`, 16 `UNRELATED` across edges; every id keeps at least one `ASSERTS`).

**T-49, three fresh runs under the new hash (D-08, F-303).** `tools/eval_judge.py --runs 3`,
`openai/gpt-4o-mini`, 2026-09-18, `judge_prompt_sha256 fc7dc32b…bfad00`, nine labeled edges:

| Set | Run 1 | Run 2 | Run 3 | T-49 |
| --- | --- | --- | --- | --- |
| first | accuracy 0.8889, unknown 0.0000 | 1.0000, 0.0000 | 1.0000, 0.0000 | **FAIL** (one run under 0.90) |
| second (`--verbose`) | 1.0000, 0.0000 | 1.0000, 0.0000 | 1.0000, 0.0000 | PASS |

Six runs: five perfect, one with a single disagreeing edge of nine (the first set was not verbose, so
which edge is not on record). Recorded as it happened: T-49's bar was met by the second set and not by
the first. Two observations for the spec owner rather than a fix here: with nine labeled edges a
0.90 threshold cannot absorb one miss, so the criterion is testing sample size as much as the judge;
and the body-bearing edge (`C-01`, `test_divide_by_zero`) was `ASSERTS` in every verbose run, so the
v1.7 change is not the source of the variance. D-08 stays with the requester.

**Traceability rows.** §5 gains rows for R-33, K-14, E-46, E-47, T-72..T-74 — and, closing a gap the
v1.6 increment left, for R-31, R-32, E-42..E-45 and T-65..T-71 — all filled from
`build/speccheck/speccheck.json`.

**Deviation from the plan, stated.** None in order or ownership. W1's gate expectation (§6 item 4 of
its wave document) underestimated the fallout — six failing tests rather than two — because the
fixture goldens embed a heading-declared statement; the four extra were exactly W2's.

## 0b. v1.6 increment (2026-09-17) — Swift projects

**Why.** A Swift 6 / SwiftUI build of a Monte Carlo π spec (`SPEC_swift.md`, 70 live ids, 42
Swift Testing tests each citing its ids in a doc comment) ran the v1.5 checker and got
`NOT CONFORMING - 0/64 passing, 62 unverified, 1 untested, 1 uncited; 43 dangling`. Every
number but two was the tool's: `.swift` files were file-level cases (citations never joined),
and six ids declared as `| **K-07** **[port]** |` were not declarations under C-01's "entire
cell" rule, so their citations dangled. The user asked what it would take; the answer is v1.6.

**Spec first.** `SPEC.md` v1.5 → v1.6 (`152cf15`): R-31, R-32; C-01, C-03, C-04, C-06 extended;
E-42..E-45; T-65..T-71; D-17..D-19. The self-check on the edited spec before any code read
`170/183 passing`, exactly the thirteen new ids `UNCITED`. Two facts in C-03 were measured, not
assumed, on a throwaway package under Swift 6.4: SwiftPM's `--xunit-output` writes
`junit-swift-testing.xml` with `classname="<Module>.<Outer>.<Inner>"` and `name="<fn>(<label>:…)"`,
one `<testcase>` per function (parameterized tests are not expanded, `.disabled` is `<skipped>`);
this toolchain writes no XCTest xUnit file at all, so the XCTest shape is pinned from SwiftPM's
known format and the fixture's XCTest suite is hand-written in that shape.

**Build, test-first, in the order T-70 → T-69 → T-68 → T-65..T-67 → T-71** (`66afb57`):

| Change | Where | Test |
| --- | --- | --- |
| first cell may carry decoration after the bold ID form; `**R-04** **R-05**` now declares R-04 (T-55's expectation updated to the v1.6 grammar) | `extract.py` `_FIRST_CELL_RE` | T-70 |
| `#expect(`, `#require(`, `XCTAssert`, `XCTFail(`, `Issue.record(` are assertion tokens | `judge_mock.py` | T-69 |
| `join_name` step 2 strips a Swift signature; overloads tie → unattributed | `results.py` | T-68 |
| line-based Swift adapter: `_strip` (comments and string literals removed per C-03, braces counted), `_attribute_lines`, `delimit_swift` (TYPE/FUNC lines, attribute block, span end, `@Test` vs `XCTestCase` direct member, undelimited `test*`), `swift_module` (D-18) | `swift.py` (new), `attribute.py`, `extract.py` (`ScannedFile.scan_root`) | T-65, T-66, T-67 |
| `fixtures/target-swift/` — a real SwiftPM package (built and run to produce its `junit.xml`), planted defects per T-71, golden reports + `summary.txt` | `fixtures/`, `test_08_golden.py` | T-71 |
| declared-id count 170 → 183 | `test_09_self_application.py` | T-48 |

Traps met while building: `@Suite struct Inner {` begins with `@` and was swept into the
attribute block of the test below it (fixed: a type-opening line is never part of a function's
attribute block); `@testable import` likewise (excluded by name). Both are covered by T-65.

**Gate on the v1.6 tree.** `pytest`: 81 passed. `ruff check` / `ruff format --check`: clean.
`speccheck --self-check`: ok. Self-application:
`speccheck: CONFORMING - 183/183 passing (100.0%), 0 failing, 0 skipped, 0 weak, 0 unverified, 0 untested, 0 uncited; 0 dangling, 0 stale; judge=mock`.
On the motivating Swift project (`swift test --xunit-output junit.xml`, `--tests Tests`):
`speccheck: NOT CONFORMING - 65/70 passing (92.9%), 0 failing, 2 skipped, 0 weak, 0 unverified, 2 untested, 1 uncited; 0 dangling, 0 stale; judge=mock`
— the five non-passing ids are that spec's own "no automated test" rows (R-11, K-08 recorded;
T-17 observed; T-18/K-04 a throughput harness off by default), which is the same answer a
hand-written grep walk had produced. Phase B was not run for this increment on speccheck's own
tree (no judged Python test changed its kind of assertion); it was run on the Swift project, whose
report records the outcome.

**Deviation from `spec-build`'s method, stated.** No `IMPLEMENTATION_PLAN.md` was written for this
four-file increment; the order above stood in for it and the commit message records the gate.

**Interpretations (D-17..D-19 defaults, awaiting confirmation).** Line-based delimiting rather than
a parser; MODULE from the first path component under the tests root; join on the bare identifier
with overloads unattributed.

## 0a. v1.5 increment (2026-09-13, later the same day)

The first Ctrl-C against a real `--judge llm` run on a local model looked ignored. Two causes,
found with a stub server holding requests for 15 s and a Python driver sending a real SIGINT:
the main thread sat in an untimed `Future.result()` wait, which is not SIGINT-interruptible on
macOS CPython, so `pool.map()` only noticed the signal once a request finished; and the pool
exit then awaited the in-flight requests, which E-41 (v1.4) permitted up to K-05. Fixed
test-first — T-64 gained a timing case (interrupt at 0.5 s with six 5 s edges at concurrency 2
→ exit 3 in under 2 s, at most three requests ever started) that failed at 10.1 s, then 5.0 s,
then passed:

| Change | Where |
| --- | --- |
| futures polled with `wait(timeout=0.25)`, exceptions from workers re-raised at once, queued futures cancelled and the `abort` event set before the pool is joined | `judge.py` `run_judge` |
| transport runs in a daemon thread; `judge()` waits in 0.25 s polls that enforce the K-05 deadline and watch `abort` (`JudgeInterrupted`) | `judge_llm.py` `_post_with_deadline`; `_httpx_post` is now a plain synchronous POST |
| E-41 tightened: in-flight requests abandoned, exit within 1 s; §11 row names the mechanism | `SPEC.md` v1.5 |

Measured with the 15 s stub server: one SIGINT → exit 3 `interrupted` after 0.2 s (was 15.2 s).
Gate on the v1.5 tree: 74 passed; `speccheck --judge mock --strict` → `CONFORMING - 170/170`.
Phase B was not re-run for this increment: no judged test changed except T-64's added case,
whose assertions are of the same kind the judge already accepted.

## 0. v1.4 increment (2026-09-13)

`SPEC.md` v1.3 added the judge-stage progress indicator (R-30, C-11, K-13, E-39, E-40, T-62,
T-63, D-15) and v1.4 folded in the ten findings of its `spec-review` (`SPEC_REVIEW_REPORT.md`,
F-201..F-210), among them the interrupt rule (E-41, T-64, D-16). The build was brought up to
date test-first: T-62/T-63/T-64 were written from §9, watched fail (`--progress` unrecognized;
a `KeyboardInterrupt` from the provider stub escaped `main()` and killed the pytest process —
exactly the E-41 gap), then realized:

| Spec id | Realized in | Notes |
| --- | --- | --- |
| R-30, C-11, K-13 | `judge.py` `ProgressLine`, `progress_line()`; `cli.py` `_progress_enabled()`, `--progress` | one in-place stderr line; padded redraws with a bare `\r`, no escapes; 100 ms coalescing, 1 s tick, $\leq$ 10 draws/s; atomic writes under a lock; drawn on entry, final state + erase on exit, erase-only on exception |
| E-39 | `cli.py` `_progress_enabled()` | LLM judge only; never at `DEBUG`; `auto` = `sys.stderr.isatty()`; `always` overrides the TTY test only |
| E-40 | `judge.py` `ProgressLine.__exit__` | erase runs in the context manager's exit path, exception or not |
| E-41 | `cli.py` `main()` (`except KeyboardInterrupt` → `ERROR interrupted`, exit 3, traceback at DEBUG); `report.py` `write_reports` (cleanup on any `BaseException`, re-raise) | D-16 default: exit `3`, keeping K-01's closed set |
| E-42 | `attribute.py`, `swift.py` | `test_02_attribution::test_swift_brace_fallback_and_braces_in_strings_and_comments` | PASSING |
| E-43 | `attribute.py`, `swift.py` | `test_02_attribution::test_swift_testing_cases_are_delimited_with_doc_comment_spans`; `test_02_attribution::test_xctest_methods_are_delimited_and_others_undelimited`; `test_08_golden::test_swift_golden_fixture_matches_byte_for_byte` | PASSING |
| E-44 | `extract.py` | `test_01_extraction::test_first_cell_decoration_after_bold_id`; `test_01_extraction::test_row_and_heading_grammar_edge_cases` | PASSING |
| E-45 | — | `test_03_results::test_swift_signature_names_join_by_identifier_and_overloads_tie` | PASSING |
| E-46 | `cli.py`, `extract.py` | `test_01_extraction::test_heading_section_bodies_title_cap_and_line_model` | PASSING |
| E-47 | `extract.py` | `test_01_extraction::test_heading_section_bodies_title_cap_and_line_model`; `test_01_extraction::test_row_and_heading_grammar_edge_cases` | PASSING |
| E-48 | `judge.py` | `test_05_judge::test_clause_grounding_validation` | PASSING |
| E-49 | `judge.py`, `report.py` | `test_05_judge::test_clause_grounding_validation` | PASSING |
| E-50 | `extract.py` | `test_01_extraction::test_recorded_marker_declarations` | PASSING |
| E-51 | `graph.py` | `test_04_status::test_recorded_ids_skip_the_judge_and_judge_strength` | PASSING |
| E-52 | `cli.py` (`_resolve_paths`: a PATHS element inside `--root` that is neither a file nor a directory → usage `2`) | T-78 `test_07_cli::test_paths_element_neither_file_nor_directory_is_e52` | PASSING |
| F-201 | `cli.py` | the judge stage's INFO lines (mode/URL/model, stage summary) are emitted after `run_judge` returns, so nothing reaches stderr through the logger while the line is displayed |
| F-206, F-207 | — | already realized in v1.2 (`max_unknown` echoed quantized, B-04; header parenthetical omitted for `--judge none`); T-35 now asserts the latter |
| T-48 | `tests/test_09_self_application.py` | declared count 161 → 170 |

Phase 1 exit gate on the v1.4 tree (fresh run):

```text
$ uv run python -m pytest tests -q --junitxml=junit.xml
73 passed in 11.69s

$ uv run ruff check src tests
All checks passed!

$ uv run speccheck --self-check
self-check: ok

$ uv run speccheck check --spec SPEC.md --src src --tests tests --results junit.xml --judge mock --strict --out build/speccheck
speccheck: CONFORMING - 170/170 passing (100.0%), 0 failing, 0 skipped, 0 weak, 0 unverified, 0 untested, 0 uncited; 0 dangling, 0 stale; judge=mock
```

Phase B (LLM judge, `openai/gpt-4o-mini` via OpenRouter, `--judge-concurrency 32`; run by the
requester from a terminal, where the C-11 indicator was visible). The first pass over the
v1.4 tree returned `4 weak` — R-20, K-02, K-03, K-08 — and a second pass `1 weak` (E-29); each
was a test that proved its ID only by implication, and each was strengthened in the test, never
in the code: T-13 now cites K-02/K-03 and asserts E-29's silent skip explicitly, T-34 asserts
R-20's relative-POSIX paths over every path in the report, and T-51 runs the golden benchmark
once and asserts the K-08 2 s bound. Third pass, on the final tree:

```text
$ speccheck check --spec SPEC.md --src src --tests tests --results junit.xml --judge llm --strict --judge-concurrency 32 --out build/speccheck-openrouter
speccheck: CONFORMING - 170/170 passing (100.0%), 0 failing, 0 skipped, 0 weak, 0 unverified, 0 untested, 0 uncited; 0 dangling, 0 stale; judge=llm
# SPECCHECK_JUDGE_URL=https://openrouter.ai/api/v1/chat/completions, SPECCHECK_JUDGE_MODEL=openai/gpt-4o-mini,
# judge_available true, unknown_rate 0.0000, judge_strength 170/170, judge_prompt_sha256 21ec78498043f92be89766967dce235a8a989dbb3357f91123abcd411177fdf7
```

The README's commands were re-run as written after the update (quick start on a fixture copy,
`sync_selfcheck.py --check`, the single-test command, `--version` → `speccheck 1.4.0`).
`ARCHITECTURE.md` §10 gained a subsection on the indicator and §5.4's exit-code note covers the
interrupt. Sections 1–6 below are the v1.1 record and remain accurate except where §0 supersedes
them (counts 161 → 170, 70 → 73 tests; `max_tokens` 400 → 4000 since v1.2).

## 1. Phase 1 exit gate — evidence (v1.1 record)

```text
$ uv run python -m pytest tests -q --junitxml=junit.xml
70 passed in 5.77s

$ uv run ruff check src tests tools
All checks passed!

$ uv run speccheck --self-check
self-check: ok

$ uv run speccheck check --spec SPEC.md --src src --tests tests --results junit.xml --judge mock --out build/selfapp --verbose
INFO stage=extract-spec ids=161 retired=0 ms=2
INFO stage=scan-src files=22 citations=371 ms=2
INFO stage=scan-tests files=13 cases=76 citations=614 ms=11
INFO stage=map-results results=70 joined=70 unattributed=0 ms=0
INFO stage=graph ids=161 dangling=0 stale=0 ms=0
INFO judge=mock
INFO stage=judge edges=316 unknown=0 ms=9
INFO note: ignored 2 file(s) by speccheck:ignore-file
INFO stage=report out=build/selfapp ms=13
speccheck: CONFORMING - 161/161 passing (100.0%), 0 failing, 0 skipped, 0 weak, 0 unverified, 0 untested, 0 uncited; 0 dangling, 0 stale; judge=mock
```

The 70 tests cover all 61 `T-nn` ids (every test function's docstring is headed by the `T-nn` it
realizes and lists the R/C/I/K/E ids it proves); none is skipped, and `filterwarnings = error` is
on, so the suite is warning-free. `hypothesis` drives T-28 (200 examples).

**Installed-wheel check (T-43):** `uv build`, install `dist/speccheck-1.1.0-py3-none-any.whl`
into a fresh venv, `cd` into an empty directory, `speccheck --self-check` → `self-check: ok`,
exit 0, directory still empty. The wheel carries `speccheck/judge_prompt.md` and all of
`speccheck/_selfcheck/` (10 files, goldens included). This check caught a real defect during the
build — the first `.gitignore` masked `junit.xml`/`speccheck.json` inside the fixture, and
hatchling honoured it — which is why the wheel check is part of the gate.

## 2. Recorded (non-gating) results

### T-48 self-application

The run above: every one of the 161 R/C/I/K/E/T ids in `SPEC.md` is `PASSING`; no dangling, no
stale citations; the only Note is the two `tests/data/markers/` files that carry the
`ignore-file` marker on purpose. This is evidence *for* the build, not its proof — the proof is
§9.1–§9.8. Two observations worth recording:

- The first self-application run reported `T-57` as `UNVERIFIED`: the docstring of the T-57 test
  contained the literal line-ignore marker, so the checker ignored the line that cited T-57 —
  exactly the trap §9 / F-109 warns about. The docstring was reworded; the marker strings now
  exist only under `tests/data/markers/`.
- Low-numbered ids (`R-01`, `C-01`, `T-01`, …) are over-cited in self-application because the
  suite uses them as sample ids in inline fixtures. That is the §0 "citation is literal"
  limitation, stated rather than hidden; it inflates evidence but never a status.

### T-51 / K-08 benchmark (`tools/bench.py`, 5 runs each, medians)

```text
machine: macOS-26.6.2-arm64-arm-64bit arm64 python=3.12.13
golden fixture: median 0.002 s over 5 runs (K-08 bound 2 s: PASS)
generated 10000 files / 100 IDs: median 0.536 s over 5 runs (K-08 bound 60 s: PASS)
```

### T-49 LLM judge evaluation (`tools/eval_judge.py`, Ollama, three independent runs per model)

Endpoint `http://localhost:11434/v1/chat/completions` (Ollama's OpenAI-compatible surface; the
C-06 body is sent unchanged), `judge_prompt_sha256 =
21ec78498043f92be89766967dce235a8a989dbb3357f91123abcd411177fdf7`, date 2026-09-11, labels in
`fixtures/target/golden/judge_labels.json` (9 judged edges: 7 `ASSERTS`, 1 `EXECUTES_ONLY`,
1 `UNRELATED`).

| Model | Run | Accuracy (non-UNKNOWN) | unknown_rate | T-49 |
| --- | --- | --- | --- | --- |
| `qwen3:8b` | 1 / 2 / 3 | 1.0000 / 1.0000 / 1.0000 | 0.1111 / 0.1111 / 0.1111 | FAIL (unknown_rate > 0.10) |
| `gemma4:latest` | 1 / 2 / 3 | 1.0000 / 1.0000 / 1.0000 | 0.1111 / 0.1111 / 0.1111 | FAIL (unknown_rate > 0.10) |
| `llama3.2:latest` | 1 / 2 / 3 | n/a | 1.0000 ×3 | FAIL (every answer malformed) |
| `phi4-mini:latest` | 1 / 2 / 3 | 0.7500 ×3 | 0.5556 ×3 | FAIL |
| `gemma3n:e4b` | 1 / 2 / 3 | n/a | 1.0000 ×3 | FAIL |

**As pinned, T-49 fails on every locally available model, and every failure is format-level,
never a wrong verdict.** The DEBUG transcripts (`judge<` lines) show three failure modes, each
handled by the kernel exactly as C-06/E-14/E-15 require:

1. *Thinking models* (`qwen3:8b`, `gemma4`): Ollama returns the reasoning in
   `message.reasoning`, but the pinned `max_tokens: 400` is spent on that reasoning for the
   hardest edge (`K-02`/`UNRELATED` for gemma4, `I-002`/`EXECUTES_ONLY` for qwen3), so
   `message.content` is empty or truncated → `judge: malformed response`, `coerced: true`.
   One such edge out of nine is `unknown_rate` 0.1111 > 0.10.
2. `llama3.2` emits JSON with an unquoted `rationale` string on every edge → malformed.
3. The small models (`phi4-mini`, `gemma3n`) mostly do not produce the object at all.

**D-07 experiment (not shipped):** re-running the same protocol with `max_tokens` patched to
4000 in a scratch script (the shipped provider keeps 400) gives:

| Model (`max_tokens` 4000) | Accuracy | unknown_rate | T-49 |
| --- | --- | --- | --- |
| `qwen3:8b` | 1.0000 / 1.0000 / 1.0000 | 0.0000 / 0.0000 / 0.0000 | PASS |
| `gemma4:latest` | 1.0000 / 1.0000 / 1.0000 | 0.0000 / 0.0000 / 0.0000 | PASS |

This is the "data behind the numbers" that D-07 and D-08 say to collect before ratifying them.
Recommendation for the spec owner: raise `max_tokens` in C-06 (a `fix(speccheck):` with a
version bump — it changes the byte-exact body T-33 pins), or add a note that thinking models
need a budget large enough for their reasoning. The C-10 text itself (D-08) needed no change:
with enough budget both models scored 100 % including the `UNRELATED` and `EXECUTES_ONLY` edges.

## 3. Interpretations and decisions the build had to make

Each is a place where the spec was silent, or two clauses disagreed. None changes a normative
row; each is listed so the spec owner can ratify or overturn it.

| # | Where | Decision taken | Why |
| --- | --- | --- | --- |
| B-01 | §5.4 vs E-19 / T-20 | A run in which **every** in-scope ID is `UNCITED` exits `1` even without `--strict`. `report.exit_code_for` adds this one clause to the §5.4 rule. | §5.4's table would give exit `0` (nothing is `FAILING`), but E-19 and T-20 both require `1`. The narrowest rule satisfying all three texts was chosen; it stays a pure function of the JSON (R-14, I-009). |
| B-02 | §5.1 `--root`, T-46 | Command-line paths resolve against the **current directory**, not against `--root`; `--root` is only the base for report paths. T-46's literal command is therefore run with the fixture copy as cwd, and its `--out <fresh tmp>` is a fresh directory *inside* the copy, since E-09 requires `--out` inside `--root`. | Conventional CLI behaviour; `--self-check` sets both cwd and `--root` to the same directory, so the pinned invocation is unaffected. |
| B-03 | C-03 "span = node.lineno .. node.end_lineno (decorators included, per `ast`)" | The span starts at the first decorator's line (`min(node.lineno, decorator linenos)`). | Since Python 3.8 `FunctionDef.lineno` is the `def` line, so "per `ast`" alone would exclude decorators; the parenthetical's intent ("decorators included") was honoured. T-09 pins it. |
| B-04 | K-11, C-07 `max_unknown` | `--max-unknown` is parsed as a Decimal from its literal text and **quantized to four places (half-even)**; that quantized value is what the JSON echoes, what the summary line prints, and what `unknown_rate` is compared against. | The summary-line regex requires `\d\.\d{4}`; comparing against the emitted value keeps I-009 exact. Differences from the unquantized comparison arise only beyond the fourth decimal. |
| B-05 | C-05 step 1, C-07 | A `RETIRED` id's citations appear **only** in `stale`; its per-ID row has empty `src`/`tests`/`unrun`. | Avoids listing the same evidence twice and keeps "retired = no conformance evidence" clean. T-23/T-25 pin it. |
| B-06 | C-07 `notes` | Note texts not fixed by the spec were fixed by the build: `invalid UTF-8 decoded with replacement: <path>`, `ambiguous result <classname>::<name>: candidates <file>::<name>, ...` (E-27), `duplicate result <classname>::<name>: N occurrences` (E-06), `undelimited tests in <path>: <Class.name>, ...` (E-28), `jev triage failed: N edge(s) ordered first` (E-59, v1.15). The spec's own texts (E-10, E-12, E-30, E-33, E-35, D-30) are used verbatim. | Each Note must be a fixed string per E-case so the code-point sort (Q-002) is total. |
| B-07 | C-07 `judge_available` | A call that returned HTTP 200 with a malformed body counts as a *succeeded* call; only E-14 failures (unreachable, timeout, HTTP ≥ 400) count as failed; budget-skipped edges are not calls. | E-14 is the only place `judge_available: false` is defined. |
| B-08 | §10 `[llm]` extra | `--judge llm` without `httpx` installed is a usage error (exit `2`) with a message naming the extra. | The spec does not say; failing early beats nine `judge: unavailable` verdicts. |
| B-09 | §11 rows R-14, R-21 | `exit_code_for` and `summary_line` live in `report.py` (the Markdown §1 needs the line); `cli.py` calls them. | Avoids a circular import; the matrix in §5 below names the real module. |
| B-10 | C-06 `judge: <class of failure>` | Any provider exception that is not a typed timeout / HTTP / malformed error is recorded as `judge: unavailable`. | E-14 names "unreachable" as the class; T-30 pins the mapping. |
| B-11 | T-43 "from an installed wheel" | In-suite, the console script of the synced environment is executed from an empty directory via a subprocess (editable install). The wheel itself was built, installed into a fresh venv, and self-checked by hand (§1). | Building a wheel inside the test run would make the suite depend on network-free `uv build`; the manual check is recorded above. |
| B-12 | T-48 in-suite | The in-suite test asserts the structural part (161 ids, none `UNCITED`/`UNTESTED`, exit 0/1) on a temp copy of the repo; the "all PASSING" claim is recorded here from the real run, because it needs the `junit.xml` of the very run that executes the test. | Chicken-and-egg noted in §9.9 itself ("recorded, not gating"). |
| B-13 | T-49 / T-51 in-suite | Deterministic guards stand in for the recorded runs: the label file covers exactly the judged edges, and `tools/bench.py` / `tools/eval_judge.py` exist and parse. The runs themselves are recorded in §2. | So that `T-49` and `T-51` are cited by a passing test (T-48 needs every T id `PASSING`) without running an LLM or a benchmark in CI. |
| B-14 | `fixtures/target/golden/` | Holds a third file, `judge_labels.json` (T-49 labels), beside the two goldens. | The self-check compares only the two report files; T-60 keeps the whole directory in sync. |
| B-15 | R-23 redaction | The raw response is redacted by replacing every occurrence of the key's text with `***` — with the Ollama convention `SPECCHECK_JUDGE_API_KEY=ollama` this also turns Ollama's `system_fingerprint: fp_ollama` into `fp_***` in DEBUG output. | Harmless; the rule is "the key never appears", and it never does. |
| B-16 | C-16 `declared_ratio` population | The ratio is over **test-kind citations of in-scope, non-retired R/C/I/K/E ids inside attributed (non-file-level) cases**, counted per citation occurrence: `src`-kind citations and file-level citations are outside R-39's own scope ("inside an attributed (non-file-level) test case") and so outside both the numerator and the denominator. | C-16 says "all such citations", and "such" is R-39's population. Including `src` citations would swamp the metric (they are `declared: false` by definition, E-56) and make it uninformative; including file-level citations would mix two different questions. On the golden fixture the two readings coincide for the edges in it except that the file-level and `src` citations are excluded. If the spec owner prefers the whole-citation reading, widen the loop in `graph.build_graph` — the `Citation.declared` values needed are already computed. |

| B-17 | C-17 ordering, $p(e)$ ties | Two edges with the *same* $p(e)$ **and** the same id (two test cases citing one id) are ordered by `(testcase.file, testcase.start)` after the id. | C-17 pins only "ties are broken by ascending id in C-07's id order", which is not a total order across two edges of one id. A total order is what makes T-89's "the three least confident" reproducible and the issue order independent of the pool's completion order. |
| B-18 | §5.3 DEBUG, C-17 | The triage pass logs its traffic as `jev>` / `jev<` lines (the `state` sent, the raw reply) with the key redacted, and emits one `INFO` stage line plus `jev url=… model=… timeout=…` after the indicator's erase. | §5.3's DEBUG list names only the judge's `judge>`/`judge<`; C-17 says the URL and model MAY appear at INFO but says nothing about the payload. The `state` carries the statement, so it must stay out of INFO (I-007) — DEBUG is where the judge's own prompts already go. |
| B-19 | K-16 / D-30 with zero eligible edges | The D-30 Note is written only when the pass actually runs, i.e. when there is at least one judge-eligible edge. | E-36 already pins that a run with zero eligible edges sends no request at all (to either provider); "the pass had no effect" would be true but pointless there, and no other stage emits a Note for doing nothing. |
| B-20 | K-12 `N%` arithmetic | $\lceil N/100 \times E \rceil$ is computed in integer arithmetic (`-(-N*E//100)`), not by floating-point multiplication and `ceil`. | $0.30 \times 10$ is `3.0000000000000004` in binary floating point, which would issue four edges where K-12's own formula says three. The spec's formula is exact; the code matches it. |

Through v1.13 no `SPEC.md` row was edited; v1.14 corrected two of its own rows (F-101 the §3.3
artifact table's stale `"1.4"` literal, F-102 T-74's stale key list — both recorded in §0f); v1.15
corrected none. The
two clauses that disagree (B-01, B-02) remain candidates for a `fix(speccheck):` by the spec
owner: §5.4 could name the E-19 case explicitly, and T-46's `--out <fresh tmp>` could read
`--out <fresh dir inside --root>`.

## 4. Artifact cross-check (§3.2 of `spec-build`)

| Artifact | Checked against | Result |
| --- | --- | --- |
| `src/speccheck/extract.py` `SpecId`/`SpecIndex` | C-02 | Same fields, same sort order (family order R,C,I,K,E,T then number); the `(family, number)` uniqueness invariant is enforced by E-02/E-03 |
| `src/speccheck/attribute.py` `TestCase`/`Citation` | C-03, C-14 | Same fields; `classname` rule for Python and fallback; `kind` ∈ {src, test}; `Citation.declared` is DECLARED iff the line is in the case's docstring or a whole-line comment (Python `#`, Swift `_Line.doc`), `false` for `src` and file-level (E-56, T-85) |
| `src/speccheck/judge.py` `JudgeRequest`/`Evidence`/`Verdict`/`Judge` | C-06, C-15 | Same fields plus `declared` after `testcase`; the user JSON is `{id, statement, declared, file, start, end, source}`; `source` is line-numbered with TAB (F-109); validation is in `judge.py`, not in the providers, and reads no `declared` (no coercion rule, D-26) |
| `src/speccheck/judge_prompt.md` | C-10 | Byte-equal to the fenced text in `SPEC.md` (T-54 asserts it; SHA-256 `f6b124bd…2bcfd1`, the v1.14 text with the `declared` definition and the skepticism rule) |
| `src/speccheck/judge_llm.py` request body | C-06 | `{"model","temperature":0,"max_tokens":4000,"messages":[system,user]}` (4000 since SPEC v1.2 / D-07) in that key order, `ensure_ascii=False`; user content is the K-09-formatted request JSON carrying `declared`; T-33 compares the bytes |
| `speccheck.json` | C-07, C-16 | Key order, seven statuses, six families, four-decimal Decimals via the `_Num` sentinel, `verdict` key always present, `declared` on every `tests[]` entry, `declared_ratio` last in `metrics` under every judge mode, notes sorted by code point, no volatile fields (T-34, T-88) |
| `SPEC_CONFORMANCE_REPORT.md` | C-08 | Nine sections in order; retired ID cell struck; `(file)` and `—` renderings (T-35) |
| `speccheck` CLI | §5.1 | Every flag, default, range, and exit code in the table; `--self-check` runs the pinned argv in-process (T-43 records the `Config`) |
| Diagnostics | §5.3 | Logger `speccheck`, one stderr handler, `%(levelname)s %(message)s`, `ERROR` default; nothing at `WARNING`; DEBUG `judge>`/`judge<` (T-41, T-42) |
| `pyproject.toml` | §10 | Python ≥ 3.12; kernel has no dependencies; `[llm] = httpx`; `[dev] = pytest, pytest-cov, hypothesis, ruff` (+ `httpx` so the provider's default transport can be exercised); package data declared as hatch `artifacts` |
| `fixtures/target/` | §9.8 | 16 ids across all six families, 2 retired, all ten planted defects present (T-46), each flips exactly its row when removed (T-47); `golden/` is never a scan root |
| `src/speccheck/_selfcheck/` | §10, F-107 | Byte-identical to `fixtures/target/` (T-60; `tools/sync_selfcheck.py --check`) |
| Determinism | I-002 | Golden fixture reports are byte-identical across runs, paths, `--src .`, and planted temporaries (T-36); the goldens in the repository were produced by the tool and re-verified after every refactor |
| Read-only inputs | I-001 | Hash comparison before/after (T-38); only the two reports appear; `--self-check` leaves no trace (T-43) |
| Network boundary | I-006 | Socket guard never fires under `none`/`mock` (T-43); `httpx` is imported only inside `_httpx_post`, verified in the fresh venv: `import speccheck.cli` leaves `httpx` out of `sys.modules` |
| `src/speccheck/jev.py` (v1.15) | C-17, K-16, I-015 | `JevConfig` reads the four `SPECCHECK_JEV_*` variables with the C-17 defaults and validates the timeout `1..300`; `render_state`/`build_body` produce the pinned `{model, state, questions}` body (asserted against the C-17 strings by T-89); `parse_confidence` reads `answers.verdict` and returns `max(probabilities)` or `None`; `run_triage` returns the order and the failure count and nothing else — the module holds no reference to `report.py`, so no triage value can reach a report (I-015) |
| `judge.run_judge(issue_count=…)` | K-12 `N%`, E-35 | Not-issued requests are marked `call_made=False` before the pool starts, so they take the same `judge: budget` disposition, the same E-35 Note and the same `unknown_rate` population as a deadline miss; `available` ignores them (T-89) |
| `speccheck` CLI, `--jev-pre-triage` / `N%` (v1.15) | §5.1, E-58 | Both grammars, the E-58 usage error naming both flags, `SPECCHECK_JEV_API_KEY` required only when the pass runs, and no key value in any message (T-90) |
| Diagnostics, triage (v1.15) | §5.3, I-007 | `jev>`/`jev<` only at DEBUG, key redacted; INFO carries the stage line and the endpoint/model only, never the `state` (B-18) |
| README | Phase 2 | Every command in it was run as written, including the new `--jev-pre-triage` example against a stub endpoint and the `--judge-budget 0%` form |
| `ARCHITECTURE.md` | — | **Known pre-existing gap, not this increment's**: the module-by-module design document has not been revised since v1.5 (`2e8db5d`) and so predates v1.6..v1.15 — it does not describe the Swift adapter, the edges/`impact` subcommand, `declared`, or the triage pass. Recorded here rather than partially updated, so the next revision of it is a real one; `README.md` and this report are current. |

Process note for the audit trail: the build was not strictly test-first. Each §9 group's tests
were written from the spec immediately after the module they exercise; five of them failed on
first run and every failure was a defect in the *test data* (a data file citing an id it should
not, a fixture reusing a directory, an inline marker literal), not in the kernel — the kernel's
only spec deviation found by the suite was B-01, fixed in code.

## 5. Traceability matrix (§11, filled from the build)

"Realized in" lists the modules whose source cites the id (comments and the §11 realization
line in each module docstring; `cli.py`'s self-check fixture is excluded). "Verified by" maps the
spec's own §11 `T-nn` list to the concrete test functions, each of which is green and cites the
id. "Self-app" is the status from the T-48 run.

| Spec id | Realized in | Verified by | Self-app |
| --- | --- | --- | --- |
| R-01 | `extract.py` | T-01 `test_01_extraction::test_table_and_heading_declarations_and_utf8_replacement`; T-05 `test_01_extraction::test_fenced_code_blocks_are_ignored` | PASSING |
| R-02 | `extract.py`, `graph.py` | T-04 `test_01_extraction::test_strikethrough_is_retired_and_mixed_redeclaration_exits_3`; T-25 `test_04_status::test_retired_ids_excluded_from_denominators_but_listed_once` | PASSING |
| R-03 | `extract.py` | T-08 `test_02_attribution::test_source_citations_in_code_comments_and_strings`; T-13 `test_02_attribution::test_excluded_dirs_oversized_nonutf8_binary_and_symlinks`; T-36 `test_06_reports::test_determinism_across_paths_out_placement_and_leftovers` | PASSING |
| R-04 | `attribute.py`, `extract.py` | T-09 `test_02_attribution::test_python_test_citations_attributed_to_enclosing_case`; T-10 `test_02_attribution::test_module_docstring_and_helper_citations_are_file_level`; T-11 `test_02_attribution::test_unparseable_python_falls_back_to_file_level_with_note`; T-12 `test_02_attribution::test_non_python_test_files_get_file_level_attribution`; T-36 `test_06_reports::test_determinism_across_paths_out_placement_and_leftovers`; T-56 `test_02_attribution::test_class_recognition_and_async_and_undelimited` | PASSING |
| R-05 | `results.py` | T-15 `test_03_results::test_both_roots_parse_and_children_map_to_outcomes`; T-16 `test_03_results::test_classname_join_accepts_suffix_forms_and_rejects_partial_components`; T-52 `test_03_results::test_parametrized_names_join_and_empty_classname`; T-58 `test_03_results::test_longest_suffix_wins_and_ties_are_unattributed` | PASSING |
| R-06 | `graph.py` | T-20 `test_04_status::test_one_fixture_per_deterministic_status`; T-21 `test_04_status::test_step_4_mixtures`; T-47 `test_08_golden::test_removing_each_planted_defect_flips_exactly_its_row` | PASSING |
| R-07 | `graph.py`, `judge_prompt.md` | T-23 `test_04_status::test_dangling_and_stale_citations` | PASSING |
| R-08 | `graph.py` | T-23 `test_04_status::test_dangling_and_stale_citations` | PASSING |
| R-09 | `graph.py` | T-24 `test_04_status::test_metrics_match_hand_computed_values_on_golden` | PASSING |
| R-10 | `judge.py`, `judge_llm.py`, `judge_mock.py` | T-26 `test_05_judge::test_mock_judge_asserts_on_assertion_tokens_else_executes_only`; T-31 `test_05_judge::test_judge_called_once_per_eligible_edge_only`; T-33 `test_05_judge::test_llm_provider_wire_format_timeout_and_concurrency`; T-49 `test_09_self_application::test_llm_eval_labels_cover_every_judged_edge` | PASSING |
| R-11 | `graph.py` | T-27 `test_05_judge::test_step_5_downgrade_rules`; T-28 `test_05_judge::test_disabling_the_judge_only_restores_weakly_passing` | PASSING |
| R-12 | `report.py` | T-35 `test_06_reports::test_markdown_layout` | PASSING |
| R-13 | `report.py` | T-34 `test_06_reports::test_json_shape_orders_rounding_and_verdict_keys` | PASSING |
| R-14 | `cli.py` | T-39 `test_07_cli::test_exit_code_equals_json_and_strict_reasons` | PASSING |
| R-15 | `cli.py` | T-39 `test_07_cli::test_exit_code_equals_json_and_strict_reasons`; T-27 `test_05_judge::test_step_5_downgrade_rules` | PASSING |
| R-16 | `attribute.py`, `extract.py`, `graph.py`, `report.py`, `results.py` | T-36 `test_06_reports::test_determinism_across_paths_out_placement_and_leftovers` | PASSING |
| R-17 | `cli.py` | T-41 `test_07_cli::test_verbosity_levels`; T-42 `test_07_cli::test_notes_quiet_by_default_and_once_at_info` | PASSING |
| R-18 | `cli.py`, `judge_llm.py` | T-43 `test_07_cli::test_no_sockets_and_self_check`; T-60 `test_07_cli::test_selfcheck_fixture_is_byte_identical_to_golden_fixture` | PASSING |
| R-19 | `cli.py`, `report.py` | T-38 `test_06_reports::test_only_the_two_reports_are_created`; T-43 `test_07_cli::test_no_sockets_and_self_check`; T-45 `test_07_cli::test_out_failures_and_temp_and_rename` | PASSING |
| R-20 | `extract.py`, `report.py` | T-34 `test_06_reports::test_json_shape_orders_rounding_and_verdict_keys`; T-36 `test_06_reports::test_determinism_across_paths_out_placement_and_leftovers` | PASSING |
| R-21 | `cli.py` | T-44 `test_07_cli::test_summary_line_format_encoding_and_numbers`; T-59 `test_07_cli::test_strict_llm_judge_gate` | PASSING |
| R-22 | `judge_mock.py` | T-26 `test_05_judge::test_mock_judge_asserts_on_assertion_tokens_else_executes_only` | PASSING |
| R-23 | `cli.py`, `judge_llm.py` | T-40 `test_07_cli::test_usage_errors_exit_2_with_message_and_no_key_leak`; T-41 `test_07_cli::test_verbosity_levels` | PASSING |
| R-24 | `report.py` | T-37 `test_06_reports::test_metrics_recomputable_from_evidence_table`; T-48 `test_09_self_application::test_self_application_runs_on_this_repository` | PASSING |
| R-25 | `graph.py` | T-53 `test_04_status::test_family_t_semantics` | PASSING |
| R-26 | `judge_llm.py` | T-33 `test_05_judge::test_llm_provider_wire_format_timeout_and_concurrency`; T-54 `test_05_judge::test_llm_response_path_fences_and_prompt_hash` | PASSING |
| R-27 | `extract.py` | T-57 `test_02_attribution::test_ignore_markers` | PASSING |
| R-28 | `cli.py`, `report.py` | T-59 `test_07_cli::test_strict_llm_judge_gate` | PASSING |
| R-29 | `cli.py` | T-44 `test_07_cli::test_summary_line_format_encoding_and_numbers` | PASSING |
| R-30 | `cli.py`, `judge.py` | T-62 `test_07_cli::test_progress_indicator_format_cadence_and_isolation`; T-63 `test_07_cli::test_progress_gating_and_interrupt_erase` | PASSING |
| R-31 | `attribute.py`, `judge_mock.py`, `results.py`, `swift.py` | `test_02_attribution::test_swift_testing_cases_are_delimited_with_doc_comment_spans`; `test_02_attribution::test_xctest_methods_are_delimited_and_others_undelimited`; `test_03_results::test_swift_signature_names_join_by_identifier_and_overloads_tie`; `test_08_golden::test_swift_golden_fixture_matches_byte_for_byte` | PASSING |
| R-32 | `extract.py` | `test_01_extraction::test_first_cell_decoration_after_bold_id`; `test_08_golden::test_swift_golden_fixture_matches_byte_for_byte` | PASSING |
| R-33 | `extract.py`, `report.py` | `test_01_extraction::test_heading_section_bodies_title_cap_and_line_model`; `test_01_extraction::test_row_and_heading_grammar_edge_cases`; `test_05_judge::test_llm_request_carries_heading_body_statement`; `test_08_golden::test_goldens_carry_title_and_markdown_renders_title` | PASSING |
| R-34 | `judge.py`, `judge_llm.py`, `judge_mock.py`, `report.py` | `test_05_judge::test_clause_grounding_validation`; `test_08_golden::test_fixture_long_body_contract_and_labels` | PASSING |
| R-35 | `extract.py`, `graph.py`, `report.py` | `test_01_extraction::test_recorded_marker_declarations`; `test_04_status::test_recorded_ids_skip_the_judge_and_judge_strength` | PASSING |
| R-36 | `extract.py` (decision table, edge extraction), `report.py` (`decisions`/`edges` keys) | `test_10_edges::test_statement_tokens_yield_depends_on_and_verifies_edges`; `test_10_edges::test_decision_table_found_by_affects_header_cell_case_insensitively`; `test_06_reports::test_decisions_and_edges_in_json` | PASSING |
| R-37 | `impact.py` (changed set, walk, reverify), `cli.py` (`impact` subcommand) | `test_11_impact::test_impact_cli_against_golden_fixture`; `test_11_impact::test_impact_against_with_no_changes_and_retired_changed_id` | PASSING |
| R-38 | `judge_llm.py` (`related_titles`: the C-12 `depends_on` neighbourhood, both directions, R/C/I/K/E only, own references first, cap 8, 160-char collapsed titles with `…`, retired tagged per E-57), `judge.py` (`JudgeRequest.related`, `to_json`'s key order), `jev.py` (`render_state`'s D-28b section), `cli.py` (one build per eligible edge) | T-83 `test_05_judge::test_t83_related_neighbourhood_on_request_and_triage_state`; T-74 `test_05_judge::test_llm_request_carries_heading_body_statement`; T-84 `test_09_self_application::test_t84_recorded_adjacent_subset_is_measured_and_recorded` (presence check; the real run is §0h) | PASSING |
| R-39 | `attribute.py` (`_doc_span`, `_declared`; the Python docstring-span and whole-line-comment rule, the Swift `_Line.doc` reuse), `graph.py` (`TestEdge.declared`, `declared_counts`) | T-85 `test_02_attribution::test_declared_vs_incidental_classification`, `test_02_attribution::test_declared_is_present_and_constant_across_judge_modes`; T-86 `test_08_golden::test_fixture_gains_one_incidental_citation` | PASSING |
| C-01 | `extract.py` | T-01 `test_01_extraction::test_table_and_heading_declarations_and_utf8_replacement`; T-02 `test_01_extraction::test_numbers_normalize_within_family`; T-03 `test_01_extraction::test_four_digits_and_adjacent_alphanumerics_are_not_ids`; T-04 `test_01_extraction::test_strikethrough_is_retired_and_mixed_redeclaration_exits_3`; T-05 `test_01_extraction::test_fenced_code_blocks_are_ignored`; T-55 `test_01_extraction::test_row_and_heading_grammar_edge_cases`; T-57 `test_02_attribution::test_ignore_markers`; T-72 `test_01_extraction::test_heading_section_bodies_title_cap_and_line_model` | PASSING |
| C-02 | `extract.py` | T-01 `test_01_extraction::test_table_and_heading_declarations_and_utf8_replacement`; T-06 `test_01_extraction::test_duplicate_declaration_exits_3_naming_both_lines`; T-72 `test_01_extraction::test_heading_section_bodies_title_cap_and_line_model` | PASSING |
| C-03 | `attribute.py`, `extract.py` | T-09 `test_02_attribution::test_python_test_citations_attributed_to_enclosing_case`; T-10 `test_02_attribution::test_module_docstring_and_helper_citations_are_file_level`; T-13 `test_02_attribution::test_excluded_dirs_oversized_nonutf8_binary_and_symlinks`; T-14 `test_02_attribution::test_several_citations_in_one_case_yield_one_edge`; T-36 `test_06_reports::test_determinism_across_paths_out_placement_and_leftovers`; T-56 `test_02_attribution::test_class_recognition_and_async_and_undelimited` | PASSING |
| C-04 | `results.py` | T-15 `test_03_results::test_both_roots_parse_and_children_map_to_outcomes`; T-16 `test_03_results::test_classname_join_accepts_suffix_forms_and_rejects_partial_components`; T-17 `test_03_results::test_duplicate_results_collapse_to_worst`; T-18 `test_03_results::test_unknown_results_are_unattributed_and_change_no_status`; T-19 `test_03_results::test_malformed_xml_and_nameless_testcase_exit_3`; T-52 `test_03_results::test_parametrized_names_join_and_empty_classname`; T-58 `test_03_results::test_longest_suffix_wins_and_ties_are_unattributed` | PASSING |
| C-05 | `graph.py`, `judge.py` | `test_01_extraction::test_heading_section_bodies_title_cap_and_line_model`; `test_04_status::test_dangling_and_stale_citations`; `test_04_status::test_recorded_ids_skip_the_judge_and_judge_strength`; `test_04_status::test_step_4_mixtures`; `test_05_judge::test_step_5_downgrade_rules` | PASSING |
| C-06 | `judge.py` (`JudgeRequest` incl. the v1.16 `related` field and its key order), `judge_llm.py`, `judge_mock.py` | `test_01_extraction::test_heading_section_bodies_title_cap_and_line_model`; `test_05_judge::test_clause_grounding_validation`; `test_05_judge::test_llm_provider_wire_format_timeout_and_concurrency`; `test_05_judge::test_llm_request_carries_heading_body_statement`; `test_05_judge::test_llm_response_path_fences_and_prompt_hash`; `test_05_judge::test_t83_related_neighbourhood_on_request_and_triage_state`; `test_05_judge::test_mock_judge_asserts_on_assertion_tokens_else_executes_only`; `test_05_judge::test_mock_judge_recognizes_swift_assertion_tokens` | PASSING |
| C-07 | `graph.py`, `report.py` | `test_01_extraction::test_heading_section_bodies_title_cap_and_line_model`; `test_04_status::test_recorded_ids_skip_the_judge_and_judge_strength`; `test_06_reports::test_json_shape_orders_rounding_and_verdict_keys`; `test_08_golden::test_goldens_carry_title_and_markdown_renders_title` | PASSING |
| C-08 | `extract.py`, `report.py` | `test_04_status::test_recorded_ids_skip_the_judge_and_judge_strength`; `test_06_reports::test_markdown_layout`; `test_08_golden::test_goldens_carry_title_and_markdown_renders_title` | PASSING |
| C-09 | `judge_llm.py` | T-33 `test_05_judge::test_llm_provider_wire_format_timeout_and_concurrency`; T-40 `test_07_cli::test_usage_errors_exit_2_with_message_and_no_key_leak` | PASSING |
| C-10 | `judge_llm.py`, `speccheck/judge_prompt.md` (the v1.16 `related` field and its rule) | `test_05_judge::test_llm_request_carries_heading_body_statement`; `test_05_judge::test_llm_response_path_fences_and_prompt_hash`; `test_09_self_application::test_self_application_runs_on_this_repository` | PASSING |
| C-11 | `judge.py` | T-62 `test_07_cli::test_progress_indicator_format_cadence_and_isolation` | PASSING |
| C-12 | `extract.py` (`_decision_rows`, `_build_decisions_and_edges`, `edge_id_key`) | T-79 `test_10_edges` (all nine functions) | PASSING |
| C-13 | `impact.py`, `report.py` (`build_impact_report`, `render_impact_markdown`, `impact_summary_line`) | T-80 `test_11_impact::test_impact_cli_against_golden_fixture`; T-81 `test_11_impact::test_diff_changed_set_reasons_in_fixed_order`, `test_11_impact::test_impact_usage_and_input_errors` | PASSING |
| C-14 | `attribute.py` (`_doc_span`, `_declared`, `_python_cases`, Swift `_Line.doc` via `delimit_swift`), `graph.py` (edge-level `declared`) | T-85 `test_02_attribution::test_declared_vs_incidental_classification`; T-86 `test_08_golden::test_fixture_gains_one_incidental_citation` | PASSING |
| C-15 | `judge.py` (`JudgeRequest.declared`, `build_request`, `to_json`), `judge_llm.py` (system message), `src/speccheck/judge_prompt.md` (field definition + skepticism rule), `cli.py` (passes `edge.declared`) | `test_05_judge::test_judge_request_carries_declared_for_the_edge`; `test_05_judge::test_llm_response_path_fences_and_prompt_hash`; `test_05_judge::test_llm_request_carries_heading_body_statement`; T-87 (§0f, recorded) | PASSING |
| C-16 | `report.py` (`tests[].declared`, `metrics.declared_ratio`, `SCHEMA_VERSION` "1.5"), `graph.py` (`declared_counts`, `Metrics.declared_ratio`) | T-86 `test_08_golden::test_fixture_gains_one_incidental_citation`; T-88 `test_08_golden::test_declared_ratio_is_present_and_recomputable_under_every_judge_mode`; `test_06_reports::test_json_shape_orders_rounding_and_verdict_keys` | PASSING |
| C-17 | `jev.py` (`JevConfig.from_env`, `render_state` incl. the D-28b `Related obligations:` section, `build_body`, `parse_confidence`, `JevTriage`), `cli.py` (`_make_triage_provider`, the env read) | T-89 `test_05_judge::test_triage_request_shape_and_response_parse`; T-90 `test_07_cli::test_jev_pre_triage_usage_errors_and_secret_hygiene` | PASSING |
| I-001 | `cli.py`, `report.py` | T-07 `test_01_extraction::test_no_in_scope_ids_exits_3_and_writes_nothing`; T-38 `test_06_reports::test_only_the_two_reports_are_created`; T-43 `test_07_cli::test_no_sockets_and_self_check`; T-45 `test_07_cli::test_out_failures_and_temp_and_rename`; T-64 `test_07_cli::test_interrupt_exits_3_and_cleans_up` | PASSING |
| I-002 | `attribute.py`, `extract.py`, `graph.py`, `report.py`, `results.py` | T-36 `test_06_reports::test_determinism_across_paths_out_placement_and_leftovers` | PASSING |
| I-003 | `report.py` | T-25 `test_04_status::test_retired_ids_excluded_from_denominators_but_listed_once`; T-35 `test_06_reports::test_markdown_layout` | PASSING |
| I-004 | `graph.py` | T-27 `test_05_judge::test_step_5_downgrade_rules`; T-28 `test_05_judge::test_disabling_the_judge_only_restores_weakly_passing` | PASSING |
| I-005 | `judge.py` | `test_01_extraction::test_numbers_normalize_within_family`; `test_05_judge::test_clause_grounding_validation`; `test_05_judge::test_ungrounded_answers_are_coerced_to_unknown` | PASSING |
| I-006 | `cli.py`, `judge_llm.py` | T-43 `test_07_cli::test_no_sockets_and_self_check` | PASSING |
| I-007 | `cli.py`, `judge_llm.py` | T-40 `test_07_cli::test_usage_errors_exit_2_with_message_and_no_key_leak`; T-41 `test_07_cli::test_verbosity_levels` | PASSING |
| I-008 | `graph.py` | T-24 `test_04_status::test_metrics_match_hand_computed_values_on_golden` | PASSING |
| I-009 | `cli.py`, `report.py` | T-39 `test_07_cli::test_exit_code_equals_json_and_strict_reasons` | PASSING |
| I-010 | `graph.py`, `judge.py` | `test_04_status::test_recorded_ids_skip_the_judge_and_judge_strength`; `test_05_judge::test_judge_called_once_per_eligible_edge_only` | PASSING |
| I-011 | `extract.py` | T-02 `test_01_extraction::test_numbers_normalize_within_family` | PASSING |
| I-012 | `cli.py` (`_resolve_paths` deduplicates by resolved path; a file two elements cover is scanned and cited once) | T-78 `test_07_cli::test_paths_one_list_equivalent_to_repeatable_occurrences`; `test_07_cli::test_paths_first_seen_covering_element_fixes_scan_root` | PASSING |
| I-013 | `impact.py` (`walk`: unbounded computation, depth-limited as a filter) | `test_11_impact::test_walk_depth_cap_is_a_prefix_with_a_note`; `test_11_impact::test_impact_cli_against_golden_fixture` | PASSING |
| I-014 | `attribute.py` (`declared` is a pure function of the source/test trees), `graph.py` / `report.py` (`declared_ratio`) | T-85 `test_02_attribution::test_declared_is_present_and_constant_across_judge_modes`; T-88 `test_08_golden::test_declared_ratio_is_present_and_recomputable_under_every_judge_mode` | PASSING |
| I-015 | `jev.py` (`run_triage` returns the order and nothing else; no report import), `report.py` (no triage field) | T-89 `test_05_judge::test_triage_orders_and_truncates_the_judge_queue`; T-89 `test_05_judge::test_triage_is_ignored_under_mock_and_inert_on_an_unlimited_budget` | PASSING |
| K-01 | `cli.py` | T-39 `test_07_cli::test_exit_code_equals_json_and_strict_reasons`; T-40 `test_07_cli::test_usage_errors_exit_2_with_message_and_no_key_leak`; T-19 `test_03_results::test_malformed_xml_and_nameless_testcase_exit_3`; T-64 `test_07_cli::test_interrupt_exits_3_and_cleans_up` | PASSING |
| K-02 | `extract.py` | T-13 `test_02_attribution::test_excluded_dirs_oversized_nonutf8_binary_and_symlinks` | PASSING |
| K-03 | `extract.py` | T-13 `test_02_attribution::test_excluded_dirs_oversized_nonutf8_binary_and_symlinks` | PASSING |
| K-04 | `extract.py` | T-03 `test_01_extraction::test_four_digits_and_adjacent_alphanumerics_are_not_ids` | PASSING |
| K-05 | `judge.py`, `judge_llm.py` | T-33 `test_05_judge::test_llm_provider_wire_format_timeout_and_concurrency` | PASSING |
| K-06 | `cli.py`, `judge.py`, `judge_llm.py` | T-33 `test_05_judge::test_llm_provider_wire_format_timeout_and_concurrency` | PASSING |
| K-07 | `judge.py` | T-32 `test_05_judge::test_rationale_truncation_and_newlines` | PASSING |
| K-08 | `attribute.py`, `extract.py`, `graph.py`, `report.py`, `results.py` | T-51 `test_09_self_application::test_benchmark_script_exists_and_parses` | PASSING |
| K-09 | `report.py` | T-34 `test_06_reports::test_json_shape_orders_rounding_and_verdict_keys` | PASSING |
| K-10 | `cli.py` | T-50 `test_07_cli::test_version_flag` | PASSING |
| K-11 | `cli.py` | T-59 `test_07_cli::test_strict_llm_judge_gate` | PASSING |
| K-12 | `cli.py`, `judge.py` (`issue_count`, the `N%` count) | T-61 `test_07_cli::test_judge_budget`; T-89 `test_05_judge::test_triage_orders_and_truncates_the_judge_queue`; T-90 `test_07_cli::test_jev_pre_triage_usage_errors_and_secret_hygiene` | PASSING |
| K-13 | `judge.py` | T-62 `test_07_cli::test_progress_indicator_format_cadence_and_isolation` | PASSING |
| K-14 | `cli.py`, `extract.py` | `test_01_extraction::test_heading_section_bodies_title_cap_and_line_model`; `test_08_golden::test_goldens_carry_title_and_markdown_renders_title` | PASSING |
| K-15 | `judge.py`, `judge_mock.py` | `test_05_judge::test_clause_grounding_validation`; `test_05_judge::test_llm_response_path_fences_and_prompt_hash` | PASSING |
| K-16 | `cli.py` (the pass runs before the first judge request, the D-30 Note), `jev.py` (`run_triage`, the K-16 order, the `related`-bearing `state`), `judge.py` (the issue order) | T-89 `test_05_judge::test_triage_orders_and_truncates_the_judge_queue`; T-90 `test_07_cli::test_jev_pre_triage_usage_errors_and_secret_hygiene` | PASSING |
| E-01 | `cli.py`, `extract.py` | T-07 `test_01_extraction::test_no_in_scope_ids_exits_3_and_writes_nothing` | PASSING |
| E-02 | `extract.py` | T-06 `test_01_extraction::test_duplicate_declaration_exits_3_naming_both_lines` | PASSING |
| E-03 | `extract.py` | T-04 `test_01_extraction::test_strikethrough_is_retired_and_mixed_redeclaration_exits_3` | PASSING |
| E-04 | `extract.py` | T-05 `test_01_extraction::test_fenced_code_blocks_are_ignored` | PASSING |
| E-05 | `results.py` | T-19 `test_03_results::test_malformed_xml_and_nameless_testcase_exit_3` | PASSING |
| E-06 | `results.py` | T-17 `test_03_results::test_duplicate_results_collapse_to_worst` | PASSING |
| E-07 | `report.py`, `results.py` | T-18 `test_03_results::test_unknown_results_are_unattributed_and_change_no_status` | PASSING |
| E-08 | `graph.py` | T-22 `test_04_status::test_unrun_cases_are_listed_and_ignored` | PASSING |
| E-09 | `cli.py` | T-40 `test_07_cli::test_usage_errors_exit_2_with_message_and_no_key_leak` | PASSING |
| E-10 | `extract.py` | T-13 `test_02_attribution::test_excluded_dirs_oversized_nonutf8_binary_and_symlinks` | PASSING |
| E-11 | `extract.py` | T-13 `test_02_attribution::test_excluded_dirs_oversized_nonutf8_binary_and_symlinks`; T-01 `test_01_extraction::test_table_and_heading_declarations_and_utf8_replacement` | PASSING |
| E-12 | `attribute.py` | T-11 `test_02_attribution::test_unparseable_python_falls_back_to_file_level_with_note` | PASSING |
| E-13 | `attribute.py`, `report.py`, `results.py` | T-10 `test_02_attribution::test_module_docstring_and_helper_citations_are_file_level` | PASSING |
| E-14 | `judge.py`, `judge_llm.py` | T-30 `test_05_judge::test_provider_failures_yield_unknown_with_specified_rationale`; T-33 `test_05_judge::test_llm_provider_wire_format_timeout_and_concurrency` | PASSING |
| E-15 | `judge.py` | T-30 `test_05_judge::test_provider_failures_yield_unknown_with_specified_rationale` | PASSING |
| E-16 | `judge.py` | T-29 `test_05_judge::test_ungrounded_answers_are_coerced_to_unknown` | PASSING |
| E-17 | `judge.py` | T-26 `test_05_judge::test_mock_judge_asserts_on_assertion_tokens_else_executes_only` | PASSING |
| E-18 | `report.py` | T-45 `test_07_cli::test_out_failures_and_temp_and_rename` | PASSING |
| E-19 | `cli.py`, `graph.py`, `report.py` | T-20 `test_04_status::test_one_fixture_per_deterministic_status`; T-39 `test_07_cli::test_exit_code_equals_json_and_strict_reasons` | PASSING |
| E-20 | `extract.py` | T-23 `test_04_status::test_dangling_and_stale_citations` | PASSING |
| E-21 | `cli.py` | T-40 `test_07_cli::test_usage_errors_exit_2_with_message_and_no_key_leak` | PASSING |
| E-22 | `attribute.py` | T-14 `test_02_attribution::test_several_citations_in_one_case_yield_one_edge` | PASSING |
| E-23 | `extract.py` | T-36 `test_06_reports::test_determinism_across_paths_out_placement_and_leftovers` | PASSING |
| E-24 | `results.py` | T-52 `test_03_results::test_parametrized_names_join_and_empty_classname` | PASSING |
| E-25 | `graph.py` | T-53 `test_04_status::test_family_t_semantics` | PASSING |
| E-26 | `cli.py`, `graph.py` | T-27 `test_05_judge::test_step_5_downgrade_rules`; T-39 `test_07_cli::test_exit_code_equals_json_and_strict_reasons` | PASSING |
| E-27 | `results.py` | T-58 `test_03_results::test_longest_suffix_wins_and_ties_are_unattributed` | PASSING |
| E-28 | `attribute.py` | T-56 `test_02_attribution::test_class_recognition_and_async_and_undelimited` | PASSING |
| E-29 | `extract.py` | T-13 `test_02_attribution::test_excluded_dirs_oversized_nonutf8_binary_and_symlinks` | PASSING |
| E-30 | `extract.py` | T-13 `test_02_attribution::test_excluded_dirs_oversized_nonutf8_binary_and_symlinks` | PASSING |
| E-31 | `extract.py` | T-55 `test_01_extraction::test_row_and_heading_grammar_edge_cases` | PASSING |
| E-32 | `cli.py`, `report.py` | T-59 `test_07_cli::test_strict_llm_judge_gate` | PASSING |
| E-33 | `extract.py` | T-57 `test_02_attribution::test_ignore_markers` | PASSING |
| E-34 | `extract.py`, `report.py` | T-36 `test_06_reports::test_determinism_across_paths_out_placement_and_leftovers`; T-45 `test_07_cli::test_out_failures_and_temp_and_rename` | PASSING |
| E-35 | `judge.py` (budget, both forms) | T-61 `test_07_cli::test_judge_budget`; T-89 `test_05_judge::test_triage_orders_and_truncates_the_judge_queue` | PASSING |
| E-36 | `cli.py`, `judge.py` | T-59 `test_07_cli::test_strict_llm_judge_gate` | PASSING |
| E-37 | `graph.py`, `report.py` | `test_04_status::test_recorded_ids_skip_the_judge_and_judge_strength`; `test_06_reports::test_json_shape_orders_rounding_and_verdict_keys`; `test_06_reports::test_markdown_layout` | PASSING |
| E-38 | `report.py` | T-34 `test_06_reports::test_json_shape_orders_rounding_and_verdict_keys` | PASSING |
| E-39 | `cli.py` | T-63 `test_07_cli::test_progress_gating_and_interrupt_erase` | PASSING |
| E-40 | `judge.py` | T-63 `test_07_cli::test_progress_gating_and_interrupt_erase` | PASSING |
| E-41 | `cli.py`, `report.py`, `judge.py` | T-63 `test_07_cli::test_progress_gating_and_interrupt_erase`; T-64 `test_07_cli::test_interrupt_exits_3_and_cleans_up` | PASSING |
| E-53 | `cli.py`, `impact.py` (`resolve_changed_ids`) | T-81 `test_11_impact::test_resolve_changed_ids_normalizes_and_validates`, `test_11_impact::test_impact_usage_and_input_errors` | PASSING |
| E-54 | `cli.py` (`_build_impact_config`; unrecognized-flag rejection by omission) | T-81 `test_11_impact::test_impact_usage_and_input_errors` | PASSING |
| E-55 | `extract.py` (`Edge.retired`), `report.py` (struck ID cells in `IMPACT_REPORT.md`) | `test_10_edges::test_edge_to_retired_id_is_flagged_and_self_reference_is_ignored`; `test_11_impact::test_impact_against_with_no_changes_and_retired_changed_id` | PASSING |
| E-56 | `attribute.py` (`_declared`: `case.is_file_level` → `false`; `cli.py` constructs `src` citations with `declared=False`) | T-85 `test_02_attribution::test_declared_vs_incidental_classification` (file-level); T-86 `test_08_golden::test_fixture_gains_one_incidental_citation` | PASSING |
| E-57 | `judge_llm.py` (`_related_title`: the title plus ` (retired)`), `jev.py` (the same string in the triage `state`) | T-83 `test_05_judge::test_t83_related_neighbourhood_on_request_and_triage_state` (a retired neighbour keeps its title, tagged) | PASSING |
| E-58 | `cli.py` (`_parse_budget`, the E-58 check in `parse_config`) | T-90 `test_07_cli::test_jev_pre_triage_usage_errors_and_secret_hygiene` | PASSING |
| E-59 | `jev.py` (`JevTriage.confidence` never raises; `TriageRun.notes`), `cli.py` (the Note) | T-89 `test_05_judge::test_triage_orders_and_truncates_the_judge_queue` | PASSING |
| T-01 | — | T-01 `test_01_extraction::test_table_and_heading_declarations_and_utf8_replacement` | PASSING |
| T-02 | — | T-02 `test_01_extraction::test_numbers_normalize_within_family` | PASSING |
| T-03 | — | T-03 `test_01_extraction::test_four_digits_and_adjacent_alphanumerics_are_not_ids` | PASSING |
| T-04 | — | T-04 `test_01_extraction::test_strikethrough_is_retired_and_mixed_redeclaration_exits_3` | PASSING |
| T-05 | — | T-05 `test_01_extraction::test_fenced_code_blocks_are_ignored` | PASSING |
| T-06 | — | T-06 `test_01_extraction::test_duplicate_declaration_exits_3_naming_both_lines` | PASSING |
| T-07 | — | T-07 `test_01_extraction::test_no_in_scope_ids_exits_3_and_writes_nothing` | PASSING |
| T-08 | — | T-08 `test_02_attribution::test_source_citations_in_code_comments_and_strings` | PASSING |
| T-09 | — | T-09 `test_02_attribution::test_python_test_citations_attributed_to_enclosing_case` | PASSING |
| T-10 | — | T-10 `test_02_attribution::test_module_docstring_and_helper_citations_are_file_level` | PASSING |
| T-11 | — | T-11 `test_02_attribution::test_unparseable_python_falls_back_to_file_level_with_note` | PASSING |
| T-12 | — | T-12 `test_02_attribution::test_non_python_test_files_get_file_level_attribution` | PASSING |
| T-13 | — | T-13 `test_02_attribution::test_excluded_dirs_oversized_nonutf8_binary_and_symlinks` | PASSING |
| T-14 | — | T-14 `test_02_attribution::test_several_citations_in_one_case_yield_one_edge` | PASSING |
| T-15 | — | T-15 `test_03_results::test_both_roots_parse_and_children_map_to_outcomes` | PASSING |
| T-16 | — | T-16 `test_03_results::test_classname_join_accepts_suffix_forms_and_rejects_partial_components` | PASSING |
| T-17 | — | T-17 `test_03_results::test_duplicate_results_collapse_to_worst` | PASSING |
| T-18 | — | T-18 `test_03_results::test_unknown_results_are_unattributed_and_change_no_status` | PASSING |
| T-19 | — | T-19 `test_03_results::test_malformed_xml_and_nameless_testcase_exit_3` | PASSING |
| T-20 | — | T-20 `test_04_status::test_one_fixture_per_deterministic_status` | PASSING |
| T-21 | — | T-21 `test_04_status::test_step_4_mixtures` | PASSING |
| T-22 | — | T-22 `test_04_status::test_unrun_cases_are_listed_and_ignored` | PASSING |
| T-23 | — | T-23 `test_04_status::test_dangling_and_stale_citations` | PASSING |
| T-24 | — | T-24 `test_04_status::test_metrics_match_hand_computed_values_on_golden` | PASSING |
| T-25 | — | T-25 `test_04_status::test_retired_ids_excluded_from_denominators_but_listed_once` | PASSING |
| T-26 | — | T-26 `test_05_judge::test_mock_judge_asserts_on_assertion_tokens_else_executes_only` | PASSING |
| T-27 | — | T-27 `test_05_judge::test_step_5_downgrade_rules` | PASSING |
| T-28 | — | T-28 `test_05_judge::test_disabling_the_judge_only_restores_weakly_passing` | PASSING |
| T-29 | — | T-29 `test_05_judge::test_ungrounded_answers_are_coerced_to_unknown` | PASSING |
| T-30 | — | T-30 `test_05_judge::test_provider_failures_yield_unknown_with_specified_rationale` | PASSING |
| T-31 | — | T-31 `test_05_judge::test_judge_called_once_per_eligible_edge_only` | PASSING |
| T-32 | — | T-32 `test_05_judge::test_rationale_truncation_and_newlines` | PASSING |
| T-33 | — | T-33 `test_05_judge::test_llm_provider_wire_format_timeout_and_concurrency` | PASSING |
| T-34 | — | T-34 `test_06_reports::test_json_shape_orders_rounding_and_verdict_keys` | PASSING |
| T-35 | — | T-35 `test_06_reports::test_markdown_layout` | PASSING |
| T-36 | — | T-36 `test_06_reports::test_determinism_across_paths_out_placement_and_leftovers` | PASSING |
| T-37 | — | T-37 `test_06_reports::test_metrics_recomputable_from_evidence_table` | PASSING |
| T-38 | — | T-38 `test_06_reports::test_only_the_two_reports_are_created` | PASSING |
| T-39 | — | T-39 `test_07_cli::test_exit_code_equals_json_and_strict_reasons` | PASSING |
| T-40 | — | T-40 `test_07_cli::test_usage_errors_exit_2_with_message_and_no_key_leak` | PASSING |
| T-41 | — | T-41 `test_07_cli::test_verbosity_levels` | PASSING |
| T-42 | — | T-42 `test_07_cli::test_notes_quiet_by_default_and_once_at_info` | PASSING |
| T-43 | — | T-43 `test_07_cli::test_no_sockets_and_self_check` | PASSING |
| T-44 | — | T-44 `test_07_cli::test_summary_line_format_encoding_and_numbers` | PASSING |
| T-45 | — | T-45 `test_07_cli::test_out_failures_and_temp_and_rename` | PASSING |
| T-46 | — | T-46 `test_08_golden::test_golden_fixture_matches_byte_for_byte` | PASSING |
| T-47 | — | T-47 `test_08_golden::test_removing_each_planted_defect_flips_exactly_its_row` | PASSING |
| T-48 | — | T-48 `test_09_self_application::test_self_application_runs_on_this_repository` | PASSING |
| T-49 | — | T-49 `test_09_self_application::test_llm_eval_labels_cover_every_judged_edge` | PASSING |
| T-50 | — | T-50 `test_07_cli::test_version_flag` | PASSING |
| T-51 | — | T-51 `test_09_self_application::test_benchmark_script_exists_and_parses` | PASSING |
| T-52 | — | T-52 `test_03_results::test_parametrized_names_join_and_empty_classname` | PASSING |
| T-53 | — | T-53 `test_04_status::test_family_t_semantics` | PASSING |
| T-54 | — | T-54 `test_05_judge::test_llm_response_path_fences_and_prompt_hash` | PASSING |
| T-55 | — | T-55 `test_01_extraction::test_row_and_heading_grammar_edge_cases` | PASSING |
| T-56 | — | T-56 `test_02_attribution::test_class_recognition_and_async_and_undelimited` | PASSING |
| T-57 | — | T-57 `test_02_attribution::test_ignore_markers` | PASSING |
| T-58 | — | T-58 `test_03_results::test_longest_suffix_wins_and_ties_are_unattributed` | PASSING |
| T-59 | — | T-59 `test_07_cli::test_strict_llm_judge_gate` | PASSING |
| T-60 | — | T-60 `test_07_cli::test_selfcheck_fixture_is_byte_identical_to_golden_fixture` | PASSING |
| T-61 | — | T-61 `test_07_cli::test_judge_budget` | PASSING |
| T-62 | — | T-62 `test_07_cli::test_progress_indicator_format_cadence_and_isolation` | PASSING |
| T-63 | — | T-63 `test_07_cli::test_progress_gating_and_interrupt_erase` | PASSING |
| T-64 | — | T-64 `test_07_cli::test_interrupt_exits_3_and_cleans_up` | PASSING |
| T-65 | — | `test_02_attribution::test_swift_testing_cases_are_delimited_with_doc_comment_spans` | PASSING |
| T-66 | — | `test_02_attribution::test_xctest_methods_are_delimited_and_others_undelimited` | PASSING |
| T-67 | — | `test_02_attribution::test_swift_brace_fallback_and_braces_in_strings_and_comments` | PASSING |
| T-68 | — | `test_03_results::test_swift_signature_names_join_by_identifier_and_overloads_tie` | PASSING |
| T-69 | — | `test_05_judge::test_mock_judge_recognizes_swift_assertion_tokens` | PASSING |
| T-70 | — | `test_01_extraction::test_first_cell_decoration_after_bold_id` | PASSING |
| T-71 | — | `test_08_golden::test_goldens_carry_title_and_markdown_renders_title`; `test_08_golden::test_swift_golden_fixture_matches_byte_for_byte` | PASSING |
| T-72 | — | `test_01_extraction::test_heading_section_bodies_title_cap_and_line_model` | PASSING |
| T-73 | — | `test_08_golden::test_goldens_carry_title_and_markdown_renders_title` | PASSING |
| T-74 | — | `test_05_judge::test_llm_request_carries_heading_body_statement` | PASSING |
| T-75 | — | `test_05_judge::test_clause_grounding_validation` | PASSING |
| T-76 | — | `test_08_golden::test_fixture_long_body_contract_and_labels`; `test_08_golden::test_goldens_carry_title_and_markdown_renders_title` | PASSING |
| T-77 | — | `test_01_extraction::test_recorded_marker_declarations`; `test_04_status::test_recorded_ids_skip_the_judge_and_judge_strength` | PASSING |
| T-78 | — | `test_07_cli::test_paths_one_list_equivalent_to_repeatable_occurrences`; `test_07_cli::test_paths_trims_and_drops_empty_segments`; `test_07_cli::test_paths_element_neither_file_nor_directory_is_e52`; `test_07_cli::test_paths_directly_named_files_get_each_per_file_filter`; `test_07_cli::test_paths_first_seen_covering_element_fixes_scan_root` | PASSING |
| T-79 | — | `test_10_edges.py` (all nine functions) | PASSING |
| T-80 | — | `test_11_impact::test_impact_cli_against_golden_fixture`; `test_11_impact::test_walk_reverse_depends_on_and_affects_with_shortest_via`; `test_11_impact::test_walk_depth_cap_is_a_prefix_with_a_note`; `test_11_impact::test_reverify_set` | PASSING |
| T-81 | — | `test_11_impact::test_diff_changed_set_reasons_in_fixed_order`; `test_11_impact::test_impact_usage_and_input_errors`; `test_11_impact::test_impact_against_with_no_changes_and_retired_changed_id` | PASSING |
| T-82 *(recorded)* | — | `test_11_impact::test_impact_backtest_script_exists` (presence check); the real run is §0e below | PASSING |
| T-83 | — | `test_05_judge::test_t83_related_neighbourhood_on_request_and_triage_state` | PASSING |
| T-84 *(recorded)* | — | `test_09_self_application::test_t84_recorded_adjacent_subset_is_measured_and_recorded` (presence check); the real run is §0h above | PASSING |
| T-85 | — | `test_02_attribution::test_declared_vs_incidental_classification`; `test_02_attribution::test_declared_is_present_and_constant_across_judge_modes`; `test_05_judge::test_judge_request_carries_declared_for_the_edge` | PASSING |
| T-86 | — | `test_08_golden::test_fixture_gains_one_incidental_citation` | PASSING |
| T-87 *(recorded)* | — | `test_09_self_application::test_t87_recorded_rerun_is_measured_and_recorded` (presence check); the real run is §0f above | PASSING |
| T-88 | — | `test_08_golden::test_declared_ratio_is_present_and_recomputable_under_every_judge_mode` | PASSING |
| T-89 | — | `test_05_judge::test_triage_orders_and_truncates_the_judge_queue`; `test_05_judge::test_triage_request_shape_and_response_parse`; `test_05_judge::test_triage_is_ignored_under_mock_and_inert_on_an_unlimited_budget` | PASSING |
| T-90 | — | `test_07_cli::test_jev_pre_triage_usage_errors_and_secret_hygiene` | PASSING |
| T-91 *(recorded)* | — | `test_09_self_application::test_t91_recorded_calibration_is_measured_and_recorded` (presence check); the real run is §0g above | PASSING |

## 6. Verdict

```text
Spec coverage: 237/237 IDs realized (0 deferred)
speccheck (mock): speccheck: CONFORMING - 237/237 passing (100.0%), 0 failing, 0 skipped, 0 weak, 0 unverified, 0 untested, 0 uncited; 0 dangling, 0 stale; judge=mock
speccheck (llm):  speccheck: CONFORMING - 237/237 passing (100.0%), 0 failing, 0 skipped, 0 weak, 0 unverified, 0 untested, 0 uncited; 0 dangling, 0 stale; judge=llm  [google/gemini-3.8-flash via OpenRouter, 2026-09-20, --judge-concurrency 8, 8 m 30 s, judge_available true, judge_strength 1.0 (230/230), unknown_rate 0.0122, declared_ratio 0.3887, judge_prompt_sha256 dbac713c9a63185c590c4a2eb0ed2f52dc11f3cb414bea6495cf617152433f8f (the v1.16 C-10 text)]
Observed: no rendered surface (§5.2)
Readiness: BUILT
Conformance: PASS WITH NOTES
```

v1.16's deliverable (R-38, C-06's `related` field, C-10's field and rule, C-17's D-28b `state`
section, K-16's carried neighbourhood, E-57, T-83, T-84) is green on both gates, and nothing
earlier moved: the fixture goldens are byte-identical to a fresh run (T-46/T-71), `_selfcheck/`
equals `fixtures/target/` byte for byte (T-60), the mock gate is 237/237 with 0 dangling and
0 stale, and the strict LLM gate is 237/237 with no `WEAKLY_PASSING` id — the request-side field is
invisible to every report, which is why the goldens did not have to be regenerated for Part B and
why `schema_version` stays `"1.5"`.

The notes are:

- **F-1 (§0h)** — the spec was wrong about the adjacent labels' token, and the T-49 run found it:
  C-10's vocabulary grades a test that runs the cited id's code and asserts a neighbour's fact
  `EXECUTES_ONLY`, not `UNRELATED`. T-76/T-84 now say "≥ 8 downgraded (`EXECUTES_ONLY` or
  `UNRELATED`)", the eight adjacent edges are labeled accordingly, and the first T-49 attempt
  (accuracy 0.7949 on run 3) is recorded beside the corrected runs (1.0000 three times).
- **T-84's recorded outcome is "on none"** (§0h): `google/gemini-3.8-flash` downgrades all eight
  adjacent edges with *and* without the `related` field, so the change moved no verdict on this
  fixture and this model. The row's precondition holds and its evidence is recorded; the row
  itself says a no-op outcome is information, not a failure, and the lead it leaves (grow the
  adjacent subset toward edges a generous model over-credits) is written down rather than acted
  on here.
- **The §0h interpretations** — `related` carries title strings (not `{id, title}` objects), the
  family filter excludes T while E-57 includes retired neighbours, the truncation precedes the
  `(retired)` tag, and the builder lives in `judge_llm.py` per §11's R-38 row.

Phase B model note. The gate line above uses `google/gemini-3.8-flash` — the model D-08 names as
this project's trusted self-application judge, and the model the requester named for this
increment's Phase B. Its `unknown_rate` (0.0122) is well inside `--max-unknown 0.2`, and it
downgraded no id at all (`judge_strength` 230/230): every edge of this increment's new ids
(R-38, E-57, T-83) is graded `ASSERTS`, which is what T-83's end-to-end test asserts directly
rather than leaving to a model. T-84 is RECORDED, so its presence check is never sent to a judge
(R-35). The v1.15 record's comparison model, `openai/gpt-4o-mini`, is the D-07/D-08 alternative
and remains the one that finds `WEAKLY_PASSING` ids on this tree; it was not needed here.

Nothing in the specification was scoped out: `related` is built for every judged edge under every
`--judge` mode (it is request-side, so the mock judge and the goldens are untouched), the triage
`state` carries it, and the fixture growth T-76/T-84 asked for is in `fixtures/target/` with its
goldens and its packaged copy in step.

*Increment history:* §0g (v1.15, Jev pre-triage), §0f (v1.14, declared vs. incidental), §0e
(v1.13, edges and `impact`), §0d (v1.11), §0c (v1.8), §0b (v1.6), §0a (v1.5), §0 (v1.4), then the
v1.1 record in §§1–5.
