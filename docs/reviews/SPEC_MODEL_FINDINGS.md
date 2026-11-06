# SPEC_MODEL_FINDINGS — `speccheck` (SPEC.md v1.26)

> - **Produced by:** `spec-model` over `SPEC.md` — the spec's own formal model, before any
>   implementation proof. First run v1.18; extended for v1.19's proof-parameter fold (10 new ids,
>   all `UNCITED`, no implementation), again for v1.20's determinacy fold (5 new ids), and on
>   2026-11-05 brought from v1.20 to v1.26 (55 new requirement-type ids, 19 amended). Output:
>   `proof_from_spec/` (Lean 4, `lake build` exit 0, zero warnings).
> - **What is certified:** the *spec*, not a system. There is no implementation in this bridge: the
>   model is a pure Lean function, `lake build` kernel-checks the claims the spec makes about
>   itself, and every requirement out of Lean's reach is mapped to the §9 test that will carry it
>   (**planned**, not run). See `proof_from_spec/README.md` for the trust boundary.
> - **Numbering:** `F-501..F-504` and `F-904..F-905`, continuing the spec's review sequence (`F-001..F-017`,
>   `F-101..F-110`, `F-201..F-210`, `F-301..F-307`, `F-401..F-407`, `Q-001..Q-011` are all cited
>   inside `SPEC.md`). F-504 was new in the v1.19 extension, resolved v1.19.1; F-501..F-503 were
>   found against v1.18 and are **resolved v1.20** — the proposal that fixed them
>   (`docs/proposals/PROPOSAL_v1.20_spec_determinacy.md`) exists *because* this model found them.
>   F-904 and F-905 are new in the v1.26 update and **open**; they follow F-901..F-903, which the
>   v1.26 build recorded in `SPEC_BUILD_REPORT.md` §0q.
> - **Disposition:** **findings are reported, not fixed.** This project does not edit `SPEC.md`;
>   `spec-proposal` / `spec-writing` decide, and a fix bumps the spec's version.

## Summary

| ID | Class | Severity | Spec anchor | Witness theorem | Status |
| -- | ----- | -------- | ----------- | --------------- | ------ |
| F-501 | G-1 · silent case | P1 | §5.1 (`explain` synopsis vs. flag table), C-18, E-60, E-64 | `f501ResolvedExplainAbsentSpecUsage`, `noSilence` (was `f501ExplainAbsentSpecSilent`, `f501NoSilenceFails`) | **resolved v1.20** |
| F-502 | G-2 · under-determined pin | P1 | C-07 `judge_available`, E-35, R-28 | `f502ResolvedJudgeAvailableBudgetFalse`, `f502ResolvedStrictJudgeFailureUnavailable`, `judgeAvailableNullIffNone`, `f502Contrast` (was `f502JudgeAvailableBudgetSilent`, `f502JudgeAvailableBudgetSilentMock`, `f502StrictJudgeFailureNull`) | **resolved v1.20** |
| F-503 | G-2 · under-specified relation | P2 | §5.4, K-01, K-18 | `k18UsageWinsWhenBoth` (was `f503ExitPrecedenceDiffer`, kept as the historical ambiguity record) | **resolved v1.20** |
| F-504 | G-2 · under-specified interaction (v1.19) | P2 | C-07, D-49 (`proof` key presence) | `f504ManifestReadButKeyAbsent` | **resolved v1.19.1** |
| F-904 | G-2 · two statements disagree | P1 | E-19 vs §5.4, R-15 | `f904E19DisagreesWithExitTable` | **open** |
| F-905 | G-2 · decision row and normative rows disagree | P1 | D-45 vs R-15, §5.4 | `f905D45DisagreesWithR15` | **open** |

No **G-3a** finding: every requirement Lean cannot reach names at least one §9 `T-nn` (§11's
"Verified by" column is total over the 140 deferred-only requirements — checked mechanically).
No **G-1** finding: `noSilence` still closes over every `Input` constructor.

## Scope map (v1.26)

Over the **356 declared conformance IDs** (219 R/C/I/K/E + 137 T): **79 proven**, every one also a
dual-half row; **140 deferred-only**, each naming its §11 `T-nn`; **137 `T-nn`**, the test
inventory; and 12 named exclusions (§0 Non-goals, §5.2), which are not conformance IDs. The v1.26
update proved the deterministic halves of R-102, R-105, R-109, R-111, R-112, R-115, C-26, C-27,
C-29, C-31, E-65, E-70, E-82..E-88, and deferred R-101, R-103, R-104, R-106..R-108, R-110, R-113,
R-114, C-22..C-25, C-28, C-30, I-019..I-023, K-19, K-20 and the remaining E-66..E-81. The partition
was checked mechanically: every spec id is tagged or tabled, and nothing else is.

## Scope map (v1.20, historical)

The full classification is in `proof_from_spec/SpeccheckSpec/Speccheck/Theorems.lean`'s closing
comment. In brief, over the **267 declared conformance IDs** (252 at v1.18, +10 at v1.19, +5 at
v1.20):

- **60 proven** — tagged in bold in `Model.lean`/`Theorems.lean`; the deterministic halves of the
  ID grammar and normalization, the JUnit join, the status algorithm, the judge-validation cascade,
  the metrics and ratios, the exit map, the progress arithmetic, the K-15 matcher, the
  proof-evidence join and its status-invariance (v1.19: C-21, K-17, E-63), and (v1.20) the
  now-total `judge_available` (C-07, and E-35's own eligible-but-unissued case, newly provable),
  usage-fault exit precedence (K-18), and `explain`'s now-total coverage (E-64).
- **104 deferred-only** — the filesystem, the network, renderings, the process layer, timing
  budgets and the §9 tests themselves; each names its `T-nn` carriers (planned). v1.19 added the
  lean adapter's own parsing (R-100, C-20), its file-IO edge cases (E-62, E-65), and the
  byte-identity rendering claim (I-018); v1.20 adds K-18's and E-64's own implementation halves
  (both dual, see below) and drops E-35 from this bucket into the proven-and-dual one (105 → 104).
- **103 `T-nn`** — the §9 acceptance criteria are the test inventory; a T id is carried by itself
  (98 at v1.18, +T-99/T-100 at v1.19, +T-101..T-103 at v1.20).
- **9 named exclusions** — the spec's own §0 Non-goals and §5.2 (`O-2`, `O-3` cited). They are not
  conformance IDs (`O-n` is outside C-01's `FAMILY`), so they consume none of the 267; they are
  listed so the boundary is stated rather than assumed, and are never used to hide a G-3a.

All 60 proven IDs appear a second time in the deferral section as **dual halves** (the theorem
discharges the deterministic half; the §9 test carries the implementation half) — including, new
in v1.20, E-35 (its `judge_available = false` half is now proven; its filesystem/timing half
stays with T-61/T-89), K-18 and E-64 (both freshly proven *and* dual from the start).

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

**Resolved — v1.20 (2026-09-24), `docs/proposals/PROPOSAL_v1.20_spec_determinacy.md`, D-47
confirmed on the recommended branch.** The brackets branch was taken: §5.1's synopsis now reads
`speccheck explain ID --spec SPEC.md …`, and E-64 is the new formal edge case (`explain: --spec is
required`, exit `2`, no trace). `f501ExplainAbsentSpecSilent`'s statement (`= none`) no longer
typechecks as a fact about the resolved model; `f501ResolvedExplainAbsentSpecUsage` proves the
input now reads E-64's outcome instead, and `noSilence` (`section Invariants`) proves coverage is
total over the whole `Input` type — the positive claim `f501NoSilenceFails` used to disprove.

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

**Resolved — v1.20 (2026-09-24), `docs/proposals/PROPOSAL_v1.20_spec_determinacy.md`, D-46
confirmed on the recommended branch.** C-07 (amended) now states exactly this third case; E-32
(amended) extends `strict_judge_failure` to record `"unavailable"` for it too. `judgeAvailable`'s
old `else if 0 < c.issued then some false else none` branch collapsed to `else some false` — the
function is now total (boolean) under `mock`/`llm`. `f502JudgeAvailableBudgetSilent`/
`f502JudgeAvailableBudgetSilentMock`'s `= none` statements no longer typecheck as facts about the
resolved model; `f502ResolvedJudgeAvailableBudgetFalse` proves both configurations now read `some
false`. `judgeAvailableNullIffNone` replaces the old `judgeAvailableNullCases` disjunction with the
tight iff the fix makes available: `judgeAvailable c = none ↔ c.mode = .none`. `f502Contrast`'s two
pre-existing cases were unaffected and still hold.
`f502StrictJudgeFailureNull`'s `ReportFacts` (built with `judgeAvailable := none` under `judgeLlm
:= true`) no longer arises from the real function; `f502ResolvedStrictJudgeFailureUnavailable`
proves the same exit code (`1`, unchanged) now carries the honest reason
(`strict_judge_failure = some "unavailable"`, not `null`) — the fix the finding's "why it matters"
asked for, and the one behavioural change v1.20 makes (a `null` reason becomes `"unavailable"` on
an already-red run; no exit code moves).

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

**Resolved — v1.20 (2026-09-24), `docs/proposals/PROPOSAL_v1.20_spec_determinacy.md`, D-48
confirmed on the recommended branch.** §5.4 gained exactly this sentence, pinned as K-18. The
model gains `exitPrecedence`, the single usage-first function K-18 now names as *the* precedence
rule; `k18UsageWinsWhenBoth` proves it holds for every value of the contract-fault flag, not just
one instance. `f503ExitPrecedenceDiffer` is kept, unmodified, as the historical record of the
ambiguity: read purely as a fact about two *different* functions it is still true (nothing makes
two distinct functions agree), but the spec no longer admits the contract-first one as a valid
reading of `SPEC.md` — only `exitPrecedence`'s usage-first order is.

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
of the two flags; originally witnessed by `f504ManifestReadButKeyAbsent : topLevelProofKeyPresent
false true = false`, exhibiting the case a reader would not expect. After the resolution below,
the model was resynced and that statement no longer typechecks as a fact about it — the resync's
witness, `f504ResolvedManifestAloneWritesKey : topLevelProofKeyPresent false true = true`, proves
the fixed rule instead; both names and the history are in that theorem's doc comment.

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

## F-904 — E-19 states an exit code that §5.4 and R-15 do not give

**Class:** G-2 (two statements of the same spec disagree). **Severity:** P1. **Anchors:** E-19,
§5.4, R-15, R-14.

**Observation.** E-19: "Both `--src` and `--tests` empty/absent — Run proceeds; every in-scope ID
is `UNCITED`; exit `1`". §5.4's table gives exit `0` for "no in-scope ID is `FAILING`; and if
`--strict`, …", and R-15 adds conditions only under `--strict`. A non-strict run whose in-scope
ids are all `UNCITED` has no `FAILING` id, so §5.4 gives `0` and E-19 gives `1` for the same run.
Since v1.24, R-105 would print `UNPROVEN` for the §5.4 reading.

**Witness.** `f904E19DisagreesWithExitTable` (`Theorems.lean`): on the report with every id
uncited, nothing failing and `--strict` off, `exitOfCheck … false = exitConforming` while
`e19Exit … = some exitNotConforming`. The model carries E-19's statement as its own function
(`e19Exit`) beside §5.4's (`exitOfCheck`) rather than choosing between them.

**What the implementation does.** It follows E-19: `report.py` `exit_code_for` returns `1` when
`by_status["UNCITED"] == in_scope` (lines 88–89). `proof/`'s model of the code carries that branch
(`allInScopeUncited`); the spec model does not, because §5.4 does not state it.

**Why it matters.** Two faithful readers of the spec build different exit codes for the first run
most users make (no `--tests` yet). R-14 says the exit code is a pure function of the JSON plus
`--strict`; both readings are, so R-14 does not settle it.

**Proposed resolution (for `spec-proposal`).** Either (a) add E-19's condition to §5.4's exit-`1`
row and to R-15's sibling R-14 text ("an all-`UNCITED` in-scope set exits `1` with or without
`--strict`"), matching the implementation; or (b) drop E-19's "exit `1`" in favour of §5.4, so such
a run exits `0` with `UNPROVEN` (R-105), and change the implementation.

---

## F-905 — D-45 makes a failed proof a strict failure; R-15 says it cannot be

**Class:** G-2 (a confirmed decision row and the normative rows disagree). **Severity:** P1.
**Anchors:** D-45, R-15, §5.4, K-17, E-63.

**Observation.** D-45 (confirmed v1.19): a `failed` proof trips `--strict` "only when
`--proof-results` was given and is readable". R-15: "Status (C-05) and hazard status (C-27) are the
only inputs to this rule". §5.4's exit-`0` row lists its strict conditions and never mentions a
proof. E-63 says a proof state never changes an id's status, which is consistent with both — the
disagreement is about the exit code, not the status.

**Witness.** `f905D45DisagreesWithR15`: on the strict report with every id `PASSING`, nothing
dangling, stale or uncontrolled, and a failed proof under a readable manifest,
`exitOfCheck … true = exitConforming` while `d45StrictFails … true = true`.

**What the implementation does.** It follows D-45: `report.py` `exit_code_for` returns `1` under
`--strict` when `proof.build` is present and `metrics.proof_failed > 0` (lines 99–104).

**Why it matters.** The normative rows are what a second implementation would build, and they
say a failed proof cannot fail the gate; the decision row and the shipped code say it does. A
conformance claim about R-15 is then true of the spec and false of the code, or the reverse.

**Proposed resolution (for `spec-proposal`).** Fold D-45 into R-15 and §5.4 ("and, with a readable
`--proof-results`, no `failed` proof state", with E-63's status clause unchanged), matching the
implementation; or reverse D-45 and change the code.

---

## What was checked mechanically

**v1.26 update.** `lake build`: exit 0, zero warnings. The audit script (spec ids from
`speccheck.extract.parse_spec`, bold-span tags from every `.lean` file, rows of the closing tables)
reports no spec id missing from both, no tag that is not a spec id, and no tabled id that is not a
spec id: 79 proven (all dual), 140 deferred-only, 137 `T-nn`. The anti-tautology audit for the new
theorems: `section Rows` holds the transcriptions (the uncontrolled strict exit, the `UNPROVEN`
row, the unmarked hazard, `verify`'s codes, the new fault rows, the not-a-wheel row); every new
theorem outside it discharges a sentence that is not its subject's definition — R-105's "only
possible without `--strict`", C-27's condition on `CTRL(h)` restated over the controls, C-27's
"`NOT_VERIFIED` adds nothing" (which needs a coherence hypothesis between hazards and the report),
the downgrade-only judge's effect on a hazard, E-83's "no input file is read", C-29's two
statements' agreement, and R-115's order properties.

**v1.20 and earlier:**

- **Tag audit** — `grep -rhoE '\*\*[^*]+\*\*' SpeccheckSpec/ | tr -d '*' | grep -oE '[RCIKE]-[0-9]+' | sort -u`
  yields exactly the 60 proven IDs (57 through v1.19.1, +K-18, +E-64, +E-35 newly dual at v1.20).
  Every ID in that set is discharged by a declaration in `Theorems.lean` and appears in the
  deferral table too (all 60 are dual); every other declared ID is in the deferral table
  deferred-only (with a `T-nn`) or the excluded table. `60 proven` (⊆ `164` total deferral-table
  rows) `+ 104 deferred-only + 103 T-nn = 267`, covering the declared set exactly.
- **Anti-tautology audit** — `section Rows` is transcription and says so; every theorem outside it
  names the spec sentence it discharges (see the header's tautology rule and each doc comment).
  `prefixEq_take`/`infixOf_take` are K-15 support lemmas, tagged as such. v1.19's
  `statusWithProof_ignoresProof` follows the same precedent as `outcomeEnvironmentFree` (I-002): a
  claim about the input space (proof is not a field of `Evidence`), not a definition re-read.
  v1.20's `section Findings` theorems are tagged by finding id (`**F-50N …**`), not by spec id, so
  they do not themselves register in the tag audit's regex; each one's spec-id claim is discharged
  a second time, and tagged, by a real `section Invariants` theorem (`noSilence` for E-64,
  `judgeAvailableAllFailed`/`judgeAvailableNullIffNone` for C-07/E-35, `k18UsageWinsWhenBoth` for
  K-18) — the same "Findings narrates, Invariants discharges" split F-504 already established.
- **Statement audit** — re-read of `SPEC.md` against each theorem's statement: quantifiers,
  hypotheses and goal match the spec's sentences. Two statements were **weakened honestly** during
  the v1.18 build rather than made to fit: `assertGrounded` (I-005's grounding facts, not a clause
  non-emptiness the model does not derive) and `tSrcCitationEvidenceOnly` (a non-retired T id, the
  case C-05 step 1 does not shadow). v1.19's five new theorems were re-read against R-100, C-20,
  C-21, K-17, E-62, E-63, E-65, I-018 with no weakening needed. v1.20's re-sync **strengthened** one
  pre-existing theorem rather than weakening it: `judgeAvailableAllFailed` dropped its
  `0 < c.issued` hypothesis, since the fix makes the conclusion hold for `issued = 0` too (E-35) —
  removing a hypothesis the proof no longer needs is the opposite of the direction Phase 3 warns
  against, so it needed no separate finding.
- **Build** — `cd proof_from_spec && lake build`, `.lake` wiped first: exit 0, **zero warnings**,
  no `sorry`/`admit` (Lean `leanprover/lean4:v4.34.0`, pinned).