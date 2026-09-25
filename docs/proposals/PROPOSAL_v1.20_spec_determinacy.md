# Proposal — v1.20: determinacy of three under-specified behaviours (`judge_available`, `explain`'s `--spec`, exit-code precedence)

> - **Status:** proposal, 2026-09-24; for `spec-writing` to turn into `SPEC.md` v1.20 rows after
>   the requester settles D-46, D-47 and D-48 below. Base is the working-tree v1.18.
>   **Numbering:** the pending `docs/proposals/PROPOSAL_v1.19_proof_parameter.md` (2026-09-23)
>   reserves `R-100`, `C-20`, `C-21`, `I-018`, `K-17`, `E-62`, `E-63`, `T-99`, `T-100` and
>   `D-43..D-45`; this proposal numbers past it (`K-18`, `E-64`, `T-101..T-103`, `D-46..D-48`) and
>   claims v1.20, so if v1.19 lands second nothing here renumbers. `PROPOSAL_obligation_census.md`
>   (pending, no version) reserves no ids.
> - **Applies to:** `SPEC.md` v1.18 — §5.1 (the `explain` synopsis line and the `--spec` row),
>   C-07's `judge_available` rule, E-32, §5.4's exit table, and the §9 tests that pin them.
>   Independent of both pending proposals; it touches `§5.1`'s `check` flag table not at all
>   (v1.19 adds two flags there), so neither needs the other and both can land in either order.
> - **Notation:** unprefixed ids are speccheck's own; `F-nnn` are `spec-model` findings in
>   `docs/reviews/SPEC_MODEL_FINDINGS.md`; Lean witness names are the declarations in
>   `proof_from_spec/SpeccheckSpec/Speccheck/Theorems.lean`.
> - **Evidence:** the spec's own formal model — `proof_from_spec/` (Lean 4, `leanprover/lean4:v4.34.0`;
>   `cd proof_from_spec && lake build` from a wiped `.lake`: exit `0`, **zero warnings**, no
>   `sorry`/`admit`), over `SPEC.md` v1.18's **252 declared ids — 54 proven / 100 deferred (each
>   naming its planned §9 `T-nn`) / 98 `T-nn` / 9 named exclusions**, partition checked mechanically.
>   Three gaps found, each with a kernel-checked witness: `f501ExplainAbsentSpecSilent` /
>   `f501NoSilenceFails` (**F-501**), `f502JudgeAvailableBudgetSilent` /
>   `f502JudgeAvailableBudgetSilentMock` / `f502Contrast` / `f502StrictJudgeFailureNull`
>   (**F-502**), `f503ExitPrecedenceDiffer` (**F-503**).

## 1. The problem

The model of the spec could not be made **total over the input space the spec itself enumerates**.
Turning each of the spec's decision tables into a `match` left three cases with no stated outcome —
prose tolerates that gap; a total function does not. Each is quoted below in full, from the
document, and each has a theorem that closes the gap only by returning "the spec says nothing".

**(a) `explain` without `--spec` — one enumerated invocation, two readings.** §5.1's synopsis
(line 1321) brackets the flag:

```text
speccheck explain ID [--spec SPEC.md] [--src PATHS]... [--tests PATHS]... [--results junit.xml]
```

while the same section's flag table (line 1333) states it flatly:

```text
| `--spec FILE` | Required. Path to the specification; decoded as UTF-8 with `errors="replace"`
  (a Note is recorded if any byte was replaced). Missing flag or unreadable file → usage error. | `2` |
```

No default is stated for `explain`: C-19 §3 names the absent-flag-only `src`/`tests` directory
default for `check` and states that `impact`/`explain` have none, and there is no `--spec` analogue.
Read the synopsis literally and `speccheck explain R-01` is a legal invocation whose specification
input is unspecified. The model's `outcome` returns `none` for exactly this input
(`f501ExplainAbsentSpecSilent`), and `f501NoSilenceFails` proves coverage is *not* total — this is
the one enumerated input that falsifies it. Every other enumerated input has a stated outcome.

**(b) `judge_available` when eligible edges were never issued.** C-07 (line 814) defines the field
in two clauses:

```text
`judge_available` is null when judge == none; with mock or llm it is true when at least one
judge call succeeded OR no edge was eligible (vacuously available), and false only when every
call failed (E-14).
```

E-35 and K-12 introduce a third configuration: edges that are **eligible** (I-010) but never
issued — the `N%` budget form with `N = 0`, or the `SECONDS` deadline reached before the first
request. There, no call succeeded, at least one edge *was* eligible, and no call *was made*, so
neither clause applies; "false only when every call failed" is at best a vacuous truth over an
empty set of calls, and structurally distinct from E-14 (a provider that failed). The model returns
`none` (`f502JudgeAvailableBudgetSilent`), while `f502Contrast` pins the two cases C-07 *does*
decide, localizing the hole to exactly the eligible-but-unissued cell.

The consequence is not cosmetic. `judge_available` feeds the `--strict --judge llm` gate (R-28,
§5.4). With every status `PASSING` and `judge_available` unset, the model computes
(`f502StrictJudgeFailureNull`): exit **`1`** — the gate wants `judge_available == true` — while
`strict_judge_failure` is **`null`**, because neither R-28 reason fires. A red run with no recorded
reason is precisely the shape R-28's `unavailable`/`unknown_rate` pair exists to prevent, and
`--strict` is meant to be the operator's audited gate.

**(c) No precedence between a usage fault (`2`) and a contract violation (`3`).** §5.4's table maps
a usage error to `2` and an input-contract violation (`E-01, E-02, E-03, E-05, E-18`) to `3`; K-01
states that both codes exist and no others. Nothing says what a run carrying **both** exits. The
two are checked at different stages (argv and path validation versus spec and results parsing), so a
single invocation satisfies both rows on the document's own terms; §3.1's stage order is prose and
is not stated as a precedence rule. `f503ExitPrecedenceDiffer` exhibits two orderings, each faithful
to §5.4's table, that disagree on the same invocation. On exit 2 or 3 the report is not written, so
the disagreement is not self-correcting — and R-14's promise ("the exit code MUST be a pure function
of the JSON report content plus `--strict`") has no JSON to be a function of.

**A mechanism that did *not* survive checking.** The first draft of (b) blamed the `N%` form alone
and proposed pinning it there. Reading E-35 in full showed the `SECONDS` form reaches the identical
state — the deadline passing before the first request is issued — so the fix has to be stated over
the eligibility/issuance census, not over one budget form. E-35's own Note
(`judge budget exhausted: N edge(s) unjudged`) confirms both forms land in it.

## 2. The change

Three independent parts, cheapest first; each may be accepted or rejected on its own.

**Part A — C-07 states the third `judge_available` case (fixes F-502).** Replace the two-clause
definition with one stated over the census: with `--judge mock|llm`, `judge_available` is `false`
iff at least one judge-eligible edge exists and no judge call succeeded (covering both E-14's "every
call failed" and E-35's "no call issued"), and `true` otherwise; and E-32's reason selection is
extended so an E-35 run that trips R-28 records `unavailable` (the only token C-07/Q-004 already
defines for "there is no usable judge"), not `null`.

**Part B — §5.1 agrees with itself about `explain`'s `--spec` (fixes F-501).** Drop the brackets
and add a new E row naming the invocation, following E-54's pattern of pinning a `check`-only flag
that `explain`'s subparser does not define. (If D-47 takes the other branch, the E row's body
becomes the stated default instead, and the synopsis keeps its brackets.)

**Part C — §5.4 states the precedence (fixes F-503).** One sentence, pinned as a `K` row so it is
checkable: flag, value and path validation precede every read of the spec, the results file and the
output directory, so a usage fault (`2`) is reported when both apply.

No diagram: the three parts touch disjoint rows and feed no shared consumer.

Proposed rows, drafted for `spec-writing`:

| Family | Draft |
| --- | --- |
| **C-07** | (amended, Part A) `judge_available` is `null` under `--judge none`. With `--judge mock` or `--judge llm` it is `true` when at least one judge call succeeded, or when no edge was judge-eligible (I-010; vacuously available), and `false` when at least one edge was judge-eligible and no judge call succeeded — whether because every call failed (E-14) or because no call was issued (E-35). It is never `null` under `mock`/`llm`. Source: F-502, `f502JudgeAvailableBudgetSilent`, `f502Contrast`. |
| **E-32** | (amended, Part A) …`strict_judge_failure` is set to `"unavailable"` when `judge_available == false` — whether the judge failed (E-14) or the eligible edges were never issued (E-35) — else `"unknown_rate"` when `unknown_rate > max_unknown`; when both hold, `"unavailable"` (Q-004). The suffix on the summary line is `(unavailable)` in the first case. Source: F-502, `f502StrictJudgeFailureNull`. |
| **E-64** | (new, Part B) `explain` invoked without `--spec` — the flag is required on this subparser, and its synopsis carries no brackets (E-54's pattern). Exit `2`, message `explain: --spec is required`, and no trace is written; no `explain` stage runs. Source: F-501, `f501ExplainAbsentSpecSilent`. |
| **K-18** | (new, Part C) **Exit-code precedence.** When one invocation carries both a usage fault (§5.4 `2`: an undefined flag, an out-of-range or malformed value, a missing required flag, a path outside `--root`) and an input-contract violation (§5.4 `3`: E-01, E-02, E-03, E-05, E-18), the usage fault is reported: flag, value and `--root`-containment validation are completed before `SPEC.md`, the results file, the output directory or `--against` is read at all, so a run never reaches the contract check that would have failed. No other precedence exists — the two are never both live. Source: F-503, `f503ExitPrecedenceDiffer`. |
| **T-101** | (new, Part A) Over a fixture whose `--judge-budget` is `0%` with `--jev-pre-triage` under `--judge llm` and at least one judge-eligible edge: the run issues no C-06 request, `speccheck.json`'s `judge_available` is `false` (never `null`), and every eligible edge's `verdict` is the E-35 `UNKNOWN` with rationale `judge: budget`; adding `--strict` exits `1` with `strict_judge_failure` `"unavailable"` and the summary-line suffix `(unavailable)`. A second run with the same `N%` but `N` above the eligible count leaves `judge_available` `true`. (C-07, E-32, E-35, R-28) |
| **T-102** | (new, Part B) `speccheck explain R-01` with no `--spec` exits `2` with the E-64 message and writes no trace; `speccheck explain --help`'s synopsis shows `--spec` unbracketed and its entry carries the C-19 §3 `default:`/precondition clause the `check` entry carries; the rendered `explain` help golden is updated for that one entry (T-97). (C-19, E-64, R-41) |
| **T-103** | (new, Part C) A run that carries both fault kinds — a `--src` element that is neither file nor directory (E-52) together with a malformed `--results` (E-05) — exits `2`, not `3`, and writes no report; the same two faults split across separate invocations exit `2` and `3` respectively, so the precedence is observable and not merely asserted. (K-18, §5.4) |

## 3. What it costs

- **Dependencies:** none. Three sentences of `SPEC.md`, one new `K` row, one new `E` row, three `T`
  rows. No new code is implied beyond what a builder already writes; Parts A and C are checks the
  kernel already performs, made normative.
- **Guaranteed (deterministic):** K-18, T-103, E-64 and T-102 are pure functions of argv, the
  filesystem's answers, and the spec text — no model, no timing. Part A's `judge_available` is a
  function of the eligibility/issuance census, which the kernel already computes for K-12/E-35.
- **Not guaranteed:** nothing here depends on a model's compliance, so no `*(recorded)*` test is
  needed. The one behavioural risk is that Part A *changes an exit code* on an existing path (a
  `--strict --judge llm` run whose eligible edges are all budget-skipped goes from
  `1`-with-`null`-reason to `1`-with-`unavailable`); the golden fixtures are unaffected because
  `--self-check` and §9.8 run `--judge mock` with no budget, so both `speccheck.json` goldens are
  byte-identical. Verified from the spec's own §5.1 `--self-check` invocation and §9.8.
- **Fixture churn:** exactly one golden — `tests/data/help/explain_help.txt` (T-97) if D-47 requires
  `--spec`, since the entry gains a precondition clause / loses a default clause. Both §9.8 report
  goldens are untouched.
- **Worth doing alone:** Part B is a one-line correction with zero behaviour change under the
  recommended branch (there is already no defined way to run `explain` without a spec; the change
  only *states* that) and can ship by itself. Part C is one sentence. Part A is the only part that
  moves an exit code and is the one most worth deciding carefully.

## 4. Alternatives considered

| Alternative | Why not |
| --- | --- |
| (Part A) Leave `judge_available` two-clause and state the E-35 case only in E-32 | Fixes the symptom (the `null` reason) but not the field: `speccheck.json` would still carry a `judge_available` value the contract does not determine, and C-07 is the contract the JSON is checked against. |
| (Part A) Add a third value to `judge_available` (`"skipped"`, or `null`) for the E-35 case | A three-valued boolean in the JSON invites every consumer (C-08's header, `--strict`, T-59) to handle a state with no operational meaning: "no call was made" and "the call failed" both mean *no usable judge*, which is what R-28 gates on. The recommendation keeps the field boolean. |
| (Part A) Treat budget-skipped edges as "no eligible edge" (vacuously available, `true`) | Would make a run that judged *nothing* report a usable judge and pass `--strict` — the opposite of what the budget flag is for. |
| (Part B) Fix the table instead: drop `Required.` and let `--spec` be optional for `explain` | That branch is live (D-47's option B) and is the smaller diff, but it needs a default the spec does not have: `explain` runs the `check` stages, and C-13's `--against`-style prior-spec idea was rejected in D-33's neighbourhood for the same reason. If the requester wants optional, D-47 says what the default file is. |
| (Part C) State precedence in §3.1's stage table rather than as a `K` row | §3.1 is a prose pipeline diagram; a `K` row is measurable (T-103 exists to check it) and K-01 already owns the exit-code set, so the rule belongs beside it. |
| (Part C) Do nothing — rely on the stage order being obvious | The stage order is not normative, and the two faults are validated in the same early phase (argv/paths) only if the implementation happens to order it that way; the model's `f503ExitPrecedenceDiffer` shows the table alone admits two orderings. |
| Fold Part B into the pending `PROPOSAL_obligation_census.md` | That proposal reserves no spec ids and is explicitly a tool-and-gate proposal (`Status`: no `SPEC.md` version); it cannot carry a normative `E` row. |

## 5. Decision(s) for the requester (D-46, D-47, D-48, all `confirm`)

| ID | Statement |
| -- | --------- |
| **D-46** | Part A: make `judge_available` boolean and total over the eligible-but-unissued case (recommended: the field is what R-28 gates on, and "no usable judge" is one operational fact however it arose; T-101 measures both budget forms) versus leave C-07's two clauses and patch only E-32's reason (smaller diff, but `speccheck.json` keeps an undetermined field). |
| **D-47** | Part B: require `--spec` on `explain` and drop the brackets in §5.1's synopsis (recommended: it is what the flag table already says, so the change states existing behaviour and T-102 pins it) versus make `--spec` genuinely optional and name the file it falls back to (smaller for a user typing `explain R-01`, but it invents a default the spec has never had and adds a second place the input spec is chosen). |
| **D-48** | Part C: pin usage-first precedence as a `K` row (recommended: one sentence beside K-01's exit set, checkable by T-103) versus leave §5.4 silent and accept that two faithful implementations may exit `2` or `3` on the same invocation. |

## 6. What the change does not do

- **It does not edit `SPEC.md`.** This file is a proposal; the rows above become normative only when
  `spec-writing` folds a confirmed D-46/D-47/D-48 in and bumps the version to v1.20, citing this
  proposal in the revision history.
- **It does not touch the three model findings' wider families.** F-502 asked, and this proposal
  does *not* answer, whether the eligible-but-unissued edges should count in `unknown_rate`
  (C-07 counts `|edges with verdict UNKNOWN|` over `|judged edges|`, and E-35 says budget-skipped
  edges are counted) — the denominator's wording is left as it stands; a follow-up proposal should
  decide whether "judged" means "had a verdict recorded" or "had a call made". Likewise the
  `N%`/`SECONDS` ordering guarantee (K-12, K-16) is untouched.
- **It does not change any status.** C-05 reads citations, tests, results and the judge; none of the
  three parts adds a status, promotes an id, or alters a metric other than the already-defined
  `judge_available`. Every id that is `PASSING` before is `PASSING` after.
- **It does not fix the model's 100 deferrals.** The filesystem, the network, the renderings and the
  process layer remain out of Lean's reach and carried by their §9 tests; this proposal is not a
  step toward proving those, and does not claim to make the spec complete.
- **It does not renumber anything.** `R-100`/`C-20`/`C-21`/`I-018`/`K-17`/`E-62`/`E-63`/`T-99`/
  `T-100` stay reserved for the pending v1.19 proposal; `K-18`/`E-64`/`T-101..T-103` are fresh and
  do not collide with it or with any other pending proposal in `docs/proposals/`.