# SPEC_MODEL_FINDINGS — `speccheck` (SPEC.md v1.19)

> - **Produced by:** `spec-model` over `SPEC.md` — the spec's own formal model, before any
>   implementation proof. First run v1.18; extended for v1.19's proof-parameter fold (10 new ids,
>   all `UNCITED`, no implementation). Output: `proof_from_spec/` (Lean 4, `lake build` exit 0, zero
>   warnings).
> - **What is certified:** the *spec*, not a system. There is no implementation in this bridge: the
>   model is a pure Lean function, `lake build` kernel-checks the claims the spec makes about
>   itself, and every requirement out of Lean's reach is mapped to the §9 test that will carry it
>   (**planned**, not run). See `proof_from_spec/README.md` for the trust boundary.
> - **Numbering:** `F-501..F-504`, continuing the spec's review sequence (`F-001..F-017`,
>   `F-101..F-110`, `F-201..F-210`, `F-301..F-307`, `F-401..F-407`, `Q-001..Q-011` are all cited
>   inside `SPEC.md`). F-504 is new in the v1.19 extension; F-501..F-503 are unchanged from the
>   v1.18 run.
> - **Disposition:** **findings are reported, not fixed.** This project does not edit `SPEC.md`;
>   `spec-proposal` / `spec-writing` decide, and a fix bumps the spec's version.

## Summary

| ID | Class | Severity | Spec anchor | Witness theorem | Status |
| -- | ----- | -------- | ----------- | --------------- | ------ |
| F-501 | G-1 · silent case | P1 | §5.1 (`explain` synopsis vs. flag table), C-18, E-60 | `f501ExplainAbsentSpecSilent`, `f501NoSilenceFails` | open |
| F-502 | G-2 · under-determined pin | P1 | C-07 `judge_available`, E-35, R-28 | `f502JudgeAvailableBudgetSilent`, `f502JudgeAvailableBudgetSilentMock`, `f502Contrast`, `f502StrictJudgeFailureNull` | open |
| F-503 | G-2 · under-specified relation | P2 | §5.4, K-01 | `f503ExitPrecedenceDiffer` | open |
| F-504 | G-2 · under-specified interaction (v1.19) | P2 | C-07, D-49 (`proof` key presence) | `f504ManifestReadButKeyAbsent` | **resolved v1.19.1** |

No **G-3a** finding: every requirement Lean cannot reach names at least one §9 `T-nn` (§11's
"Verified by" column is total over the 105 deferred requirements — checked mechanically).

## Scope map

The full classification is in `proof_from_spec/SpeccheckSpec/Speccheck/Theorems.lean`'s closing
comment. In brief, over the **262 declared conformance IDs** (252 at v1.18, +10 at v1.19):

- **57 proven** — tagged in bold in `Model.lean`/`Theorems.lean`; the deterministic halves of the
  ID grammar and normalization, the JUnit join, the status algorithm, the judge-validation cascade,
  the metrics and ratios, the exit map, the progress arithmetic, the K-15 matcher, and (v1.19) the
  proof-evidence join and its status-invariance (C-21, K-17, E-63).
- **105 deferred** — the filesystem, the network, renderings, the process layer, timing budgets and
  the §9 tests themselves; each names its `T-nn` carriers (planned). v1.19 adds the lean adapter's
  own parsing (R-100, C-20), its file-IO edge cases (E-62, E-65), and the byte-identity rendering
  claim (I-018).
- **100 `T-nn`** — the §9 acceptance criteria are the test inventory; a T id is carried by itself
  (98 at v1.18, +T-99/T-100 at v1.19).
- **9 named exclusions** — the spec's own §0 Non-goals and §5.2 (`O-2`, `O-3` cited). They are not
  conformance IDs (`O-n` is outside C-01's `FAMILY`), so they consume none of the 262; they are
  listed so the boundary is stated rather than assumed, and are never used to hide a G-3a.

The 57 proven IDs appear a second time in the deferral section as **dual halves** (the theorem
discharges the deterministic half; the §9 test carries the implementation half).

---

## F-501 — `explain` without `--spec`: an enumerated input with no stated outcome

**Class:** G-1 (silent case). **Severity:** P1. **Anchors:** §5.1 synopsis, §5.1 flag table
(`--spec`), C-18, E-60.

**Observation.** §5.1's synopsis puts `--spec` in brackets for `explain`
(`speccheck explain ID [--spec SPEC.md] …`) — optional — while the same section's flag table states
`--spec FILE` as `Required.` and the `explain` row says it "Accepts `--spec` … with the meanings
above". No default for `explain`'s `--spec` is stated anywhere: the `src`/`tests` directory default
is explicitly *absent* for `explain` (C-19 §3), and there is no `--spec` analogue.

**Why it matters.** Read the synopsis literally and `explain ID` with no `--spec` is a legal
invocation whose spec input is unspecified. A builder must guess (reject with the E-60 usage error?
require it, contradicting the synopsis? invent a default file?), and the guess is not checkable
against the document. It is exactly the class of hole this skill exists to find: the `match` has no
case for it.

**Witness.** `f501ExplainAbsentSpecSilent : outcome .explainAbsentSpec = none` — the model returns
`none` (the representation of "the spec states no outcome") for exactly this input. Consequently
`f501NoSilenceFails : ¬ (∀ i, (outcome i).isSome)`: coverage is *not* total over the enumerated
input space, and this is the one input that falsifies it. Every other enumerated input has a stated
outcome (`section Rows`, `exitClosed`, `exit0Reachable`…`exit3Reachable`).

**Proposed resolution (for `spec-proposal`).** Make §5.1's synopsis agree with its table: either
drop the brackets (`speccheck explain ID --spec SPEC.md`), or state the absent-flag default for
`explain` in the `--spec` row and C-19 §3, in the same words the `src`/`tests` rows use.

---

## F-502 — `judge_available` is undetermined when eligible edges were never issued

**Class:** G-2 (pin narrower than the mechanism). **Severity:** P1. **Anchors:** C-07
(`judge_available`), E-35 (budget), E-14, E-36, R-28, K-12.

**Observation.** C-07 defines the field in two clauses: "it is true when at least one judge call
succeeded OR no edge was eligible (vacuously available), and false only when every call failed
(E-14)". K-12/E-35 introduce a third configuration: edges that are **eligible** but never issued —
the `N%` budget form with `N = 0`, or the `SECONDS` deadline reached before the first request. In
that configuration no call succeeded, at least one edge *was* eligible, and no call *was made*, so
neither clause applies. "False only when every call failed" is at best a vacuous truth over an
empty set of calls, and structurally distinct from the E-14 case (a provider that failed).

**Why it matters.** `judge_available` is left undefined — not `true`, not `false` — for a
reachable, deterministic configuration. The `--strict --judge llm` gate reads it (R-28, §5.4), so
the spec's *exit code* for that run is a consequence of the gap, not of the rules.

**Witnesses.**
- `f502JudgeAvailableBudgetSilent : judgeAvailable { mode := .llm, eligible := 3, issued := 0, succeeded := 0 } = none`
  and its `--judge mock` twin `f502JudgeAvailableBudgetSilentMock`.
- `f502Contrast` pins the two cases C-07 *does* determine (`false` when every call failed, `true`
  when no edge was eligible), localizing the gap to exactly the eligible-but-unissued cell.
- `f502StrictJudgeFailureNull` shows the downstream consequence the model computes: with every
  status `PASSING` and `judge_available` unset, a `--strict --judge llm` run exits `1` (the R-28
  gate wants `judge_available = true`) while `strict_judge_failure` is `null` — a red run with no
  recorded reason, the shape R-28's `unavailable`/`unknown_rate` pair exists to prevent.

**Proposed resolution.** Extend C-07's definition with the third case explicitly, e.g.: with
`--judge llm`, `judge_available` is `false` iff at least one judge-eligible edge (I-010) exists and
no judge call succeeded — covering both "every call failed" (E-14) and "no call was issued"
(E-35) — and `true` otherwise; and state which R-28 reason a `judge_available == false` run records
under E-35 (today E-32's precedence rule presumes only the E-14 shape).

---

## F-503 — no precedence between a usage fault (`2`) and a contract violation (`3`) in one run

**Class:** G-2 (relation under-specified). **Severity:** P2. **Anchors:** §5.4, K-01.

**Observation.** §5.4's table maps a usage error to `2` and an input-contract violation
(`E-01, E-02, E-03, E-05, E-18`) to `3`; K-01 states that both codes exist and no others. Neither
says what a run that carries **both** kinds of fault exits, and the two are checked at different
stages (argv/path validation vs. spec and results parsing), so a single invocation can, on the
document's own terms, satisfy both rows. §3.1's stage order is prose and is not stated as a
precedence rule; nothing in §5.4/K-01 makes it normative.

**Why it matters.** Two faithful implementations can differ on the exit code of the same
invocation — the one observable R-14 promises is a pure function of the report. The report itself
is not written on exit 2 or 3, so the disagreement is not self-correcting.

**Witness.** `f503ExitPrecedenceDiffer : ∃ usage contract : Bool, (usage-first) ≠ (contract-first)`
— two orderings, each faithful to §5.4's table, exhibited by a kernel-checked separating witness.

**Proposed resolution.** Add one sentence to §5.4: "When a run carries both a usage fault and an
input-contract violation, the usage fault (exit `2`) is reported: flag, value and path validation
precede every read of the spec, the results file and the output directory." (§3.1's order already
implies it; the table should say it.)

---

## F-504 — the top-level `proof` key's presence is tied to `--proof` alone, dropping a read manifest

**Class:** G-2 (under-specified interaction). **Severity:** P2. **Anchors:** C-07, D-49 (v1.19).

**Observation.** C-07's v1.19 addition states: "the key is omitted entirely — on the top-level
object and on every id — when `--proof` was not given." D-49 separately pins the top-level shape,
`{"build": {…} | null}`, echoing C-21's `build` "when `--proof-results` was also given." Read
together, a run given `--proof-results` **without** `--proof` has its manifest read (C-21 states
the checker reads it unconditionally) but writes **no `proof` key anywhere** — the manifest's own
`build` result (exit code, declaration counts) is silently discarded, because the presence gate is
tied to `--proof` alone rather than to "was any proof input given."

**Why it matters.** `--proof-results` is documented (§5.1) as independently accepted — nothing in
its own row says it is inert without `--proof`. An operator who passes only `--proof-results` (to
report a Lean build's aggregate health with no per-id citations, say) gets a run that read the file
and silently produced no trace of having done so.

**Witness.** `topLevelProofKeyPresent` (`Model.lean`) models the pinned rule exactly as a function
of the two flags; `f504ManifestReadButKeyAbsent : topLevelProofKeyPresent false true = false`
exhibits the case a reader would not expect.

**Proposed resolution (for `spec-proposal`).** Either (a) gate the top-level key on
`--proof ∨ --proof-results` instead of `--proof` alone (per-id `proof` stays gated on `--proof`,
since there is nothing to attribute without a citation), or (b) state explicitly that
`--proof-results` without `--proof` is accepted but produces no report trace, so the current
behavior is a documented no-op rather than a silent one.

**Resolved — v1.19.1 (2026-09-24), same session, before any implementation existed.** Branch (a)
taken: C-07's proof-field rules and the JSON comment reworded, D-49 amended with the corrected
condition and branch (b) recorded as the rejected alternative. See `SPEC.md`'s v1.19.1 status
paragraph and revision-history row.

---

## What was checked mechanically

- **Tag audit** — `grep -rhoE '\*\*[^*]+\*\*' SpeccheckSpec/ | tr -d '*' | grep -oE '[RCIKE]-[0-9]+' | sort -u`
  yields exactly the 57 proven IDs. Every ID in that set is discharged by a declaration in
  `Theorems.lean`; every other declared ID is in the deferral table (with a `T-nn`) or the excluded
  table. `57 + 105 + 100 = 262`, disjoint, covering the declared set exactly.
- **Anti-tautology audit** — `section Rows` is transcription and says so; every theorem outside it
  names the spec sentence it discharges (see the header's tautology rule and each doc comment).
  `prefixEq_take`/`infixOf_take` are K-15 support lemmas, tagged as such. v1.19's
  `statusWithProof_ignoresProof` follows the same precedent as `outcomeEnvironmentFree` (I-002): a
  claim about the input space (proof is not a field of `Evidence`), not a definition re-read.
- **Statement audit** — re-read of `SPEC.md` against each theorem's statement: quantifiers,
  hypotheses and goal match the spec's sentences. Two statements were **weakened honestly** during
  the v1.18 build rather than made to fit: `assertGrounded` (I-005's grounding facts, not a clause
  non-emptiness the model does not derive) and `tSrcCitationEvidenceOnly` (a non-retired T id, the
  case C-05 step 1 does not shadow). v1.19's five new theorems were re-read against R-100, C-20,
  C-21, K-17, E-62, E-63, E-65, I-018 with no weakening needed.
- **Build** — `cd proof_from_spec && lake build`, `.lake` wiped first: exit 0, **zero warnings**,
  no `sorry`/`admit` (Lean `leanprover/lean4:v4.34.0`, pinned).