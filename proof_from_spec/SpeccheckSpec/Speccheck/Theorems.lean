/-
# `SpeccheckSpec.Speccheck.Theorems` — the proof

## What this proves

For the deterministic, enumerable part of `SPEC.md` v1.26, for **all inputs**, kernel-checked:

- **The status algorithm** (C-05): `statusOf` returns `RETIRED` for retired ids, `UNCITED` for a
  T id with source citations only (F-001/E-25), and only `PASSING`/`WEAKLY_PASSING` from the judge
  step; the judge step never fires for a RECORDED id (R-35/E-51), and it can only downgrade (I-004).
- **The validation cascade** (C-06): rules fire in the spec's order; a verdict coerced to `UNKNOWN`
  is recorded with an empty clause (E-49); `ASSERTS` requires an in-span evidence line and a
  located clause (E-16, E-48, I-005); every rationale is ≤ 280 characters (C-06 rule 8 / K-07).
- **The metrics** (C-07): every ratio is `null`-on-zero-denominator (I-008, R-09);
  `judge_strength` excludes RECORDED ids from its population (F-405); `judge_available` is
  total and boolean under `mock`/`llm` (amended v1.20) — vacuously `true` when no edge was
  eligible (E-36), and `false` whenever an edge was eligible and no call succeeded, whether every
  call failed (E-14) or none was issued at all (E-35, F-502, resolved v1.20).
- **The exit map** (§5.4, R-14, R-15, R-28): the exit code is a pure function of the report facts
  plus `--strict`; the closed set is `{0,1,2,3}` (K-01); a usage fault exits `2` and a contract
  fault exits `3`, neither writing a report; `strict_judge_failure` is `unavailable`-first
  (Q-004) and now also covers the E-35 case (E-32, amended v1.20); all four codes are reachable;
  when one invocation carries both fault classes, usage wins (K-18, v1.20, F-503 resolved).
- **The progress arithmetic** (C-11): the bar is 20 cells with `k = ⌊20d/n⌋`, and `left` is
  undefined exactly while `d = 0`.
- **The K-15 matcher**: the prefix/infix facts, and the mock provider's clause is always located
  (R-22).
- **Coverage**: `outcome` is now total over the entire enumerated input space — `noSilence`
  (`section Invariants`) proves it directly. The one case that was silent, `explain` without
  `--spec`, now has E-64's stated outcome (F-501, resolved v1.20).
- **The proof-evidence join** (C-21, K-17, v1.19): `proofStateOf` is total over its four boolean
  facts (no case is under-determined — a citation is always `checked`, `failed`, `unknown`, or
  `stale`); an absent citation always joins to `none`; a name-matched, location-mismatched entry is
  always `stale`, never `failed`, and a name-unmatched one is always `unknown`, never `failed`
  (K-17's own emphasis). Proof never changes status (E-63): `statusWithProof` provably ignores its
  proof-state argument, for every evidence record and every proof state.
- **The status word** (R-105, v1.24): `UNPROVEN` never appears under `--strict`, and the word is
  `NOT CONFORMING` exactly on exit `1`.
- **The hazard roll-up** (C-27, R-109, D-64, v1.25): `UNCONTROLLED` exactly when every
  controlling id is retired (or none exists); `VERIFIED` implies every live control `PASSING`, so a
  `WEAKLY_PASSING` control never verifies; the downgrade-only judge can never turn a hazard
  `VERIFIED`; an `UNCONTROLLED` hazard fails `--strict`; and C-27's claim that `NOT_VERIFIED` adds
  nothing to `--strict` holds for every coherent report.
- **`verify`** (C-26, E-82, E-83, v1.25): the closed exit set; a run exiting `2` or `3` read no
  file the manifest names; exit `0` exactly when nothing differs.
- **`qualify`** (C-29, R-111, E-86..E-88, v1.26): C-29's verdict sentence and its first-failure
  order agree on every input; the `QUALIFIED` line always has a tree; "not an installed wheel"
  outranks every other failure; a failing case or a data fault can never be masked.
- **The anomaly selection** (R-115, C-31, v1.26): the version order is strict; an unfixed anomaly
  is always listed, one fixed in or before the running version never is, and file order is kept.
- **Two findings** (F-904, F-905): E-19 and D-45 each state an exit outcome that §5.4/R-15 do not,
  witnessed by one report each.

## What this does not prove

**There is no program.** This file certifies the *spec*, not any system: no line of
`src/speccheck/*.py` was read to write it. Every requirement whose realization is the filesystem,
the network, a clock, a rendering, or the process layer is out of Lean's reach and appears in the
deferral table at the foot of this file, each against the §9 test that will carry it — those tests
are **planned**, because the spec's §9 suite is what a build would run, not something this project
runs. Nothing here says anything about an implementation.

## The trust boundary

Lean proves **the model** — the pure functions in `Model.lean`. It cannot read a document, and the
correspondence between `SPEC.md`'s tables and those functions is **manual**: the correspondence
table in `Model.lean`'s header, anchor by anchor. The row theorems in `section Rows` exist so that
the ID-to-declaration join is complete (every spec row the model covers has a declaration a reader
can check), *not* because they prove anything.

## The tautology rule

`section Rows` is **transcription**: each theorem re-states the model's own definition for one
input, and its doc comment says so. Every theorem *outside* `section Rows` discharges a spec
sentence that is not the definition of the thing it is about — a claim quantified over the whole
input space, a cross-constant relation, a reachability or coverage claim, or a claim about the
input space itself — and its doc comment names that sentence.
-/
import SpeccheckSpec.Speccheck.Spec
import SpeccheckSpec.Speccheck.Model

namespace SpeccheckSpec.Speccheck.Theorems

open SpeccheckSpec.Speccheck.Spec
open SpeccheckSpec.Speccheck.Model

/-! ### Fixtures used by the row theorems (model values, not spec constants) -/

/-- A baseline evidence record: a cited, run, passing `R` id, judge off, not recorded. -/
def evBase : Evidence :=
  { retired := false, family := .R, hasTestCitation := true, hasSrcCitation := true,
    resultsGiven := true, anyTestHasOutcome := true, anyFailedOrError := false,
    allOutcomesSkipped := false, judgeEnabled := false, recorded := false, verdicts := [] }

/-- A baseline raw provider answer: nothing yet filled in. -/
def aBase : RawAnswer :=
  { failure := none, verdict := none, clause := none, evidenceCount := 0, evidenceInSpan := true,
    rationale := [], clauseLocated := false }

/-- A baseline conforming report: no failing id, everything passing, no dangling/stale, judge off. -/
def factConforming : ReportFacts :=
  { anyInScopeFailing := false, allInScopePassing := true, anyDangling := false, anyStale := false,
    judgeLlm := false, judgeAvailable := none, unknownRateExceeds := false }

/-! ### K-15 support lemmas (used by `mockClauseLocated`) -/

/-- **K-15** — a list is one of its own suffixes. -/
theorem mem_suffixes (l : List Char) : l ∈ suffixes l := by
  induction l with
  | nil => simp [suffixes]
  | cons c cs _ => simp [suffixes]

/-- **K-15** — `prefixEq` is reflexive. -/
theorem prefixEq_refl (l : List Char) : prefixEq l l = true := by
  induction l with
  | nil => rfl
  | cons c cs ih => simp [prefixEq, ih]

/-- **K-15** — any prefix of a list is a `prefixEq` prefix of it. -/
theorem prefixEq_take : ∀ (l : List Char) (n : Nat), prefixEq (l.take n) l = true
  | [], _ => by simp [prefixEq]
  | _ :: _, 0 => rfl
  | x :: xs, n + 1 => by
      simp only [List.take_succ_cons, prefixEq, decide_true, Bool.true_and]
      exact prefixEq_take xs n

/-- **K-15** — any prefix of a list occurs in it as an infix. -/
theorem infixOf_take (l : List Char) (n : Nat) : infixOf (l.take n) l = true := by
  unfold infixOf
  exact List.any_eq_true.mpr ⟨l, mem_suffixes l, prefixEq_take l n⟩

/-! ## Rows — transcription of the spec's tables (not evidence; see the tautology rule) -/

section Rows

/-- **C-01, I-011** (transcription): the normalized display form pads `R-7` to `R-07`. -/
theorem row_normalize_R7 : normalizeDisplay ⟨.R, 7⟩ = "R-07" := by decide

/-- **C-01, I-011** (transcription): `I` numbers pad to three digits, so `I-5` is `I-005`. -/
theorem row_normalize_I5 : normalizeDisplay ⟨.I, 5⟩ = "I-005" := by decide

/-- **I-011** (transcription): the spellings `R-7` and `R-007` share one normalized form. -/
theorem row_normalize_idempotent :
    normalizeDisplay ⟨.R, 7⟩ = normalizeDisplay ⟨.R, 007⟩ := by decide

/-- **C-01** (transcription): a two-digit family pads to width 2, `I` to width 3. -/
theorem row_padWidths : (Family.K.padWidth, Family.I.padWidth) = (2, 3) := by decide

/-- **C-04, F-005** (transcription): `join_name` step 1 strips from the first `[`. -/
theorem row_join_param : joinName "test_x[3-True]" = "test_x" := by decide

/-- **C-04, F-101** (transcription): a nested `[` is removed with everything after it. -/
theorem row_join_nested : joinName "test_x[list[int]]" = "test_x" := by decide

/-- **C-04** (transcription): two bracket groups still strip to the first. -/
theorem row_join_two_brackets : joinName "test_y[a][b]" = "test_y" := by decide

/-- **C-04, R-31, D-19** (transcription): step 2 strips a Swift signature from the first `(`. -/
theorem row_join_signature : joinName "twoArgs(a:b:)" = "twoArgs" := by decide

/-- **C-04, R-31** (transcription): a bracket group then a signature still strips both. -/
theorem row_join_both : joinName "test_x[f(1)]" = "test_x" := by decide

/-- **C-04, F-102** (transcription): a plain identifier is unchanged (`testAddition`). -/
theorem row_join_plain : joinName "testAddition" = "testAddition" := by decide

/-- **C-04, E-06** (transcription): `error` is the worst outcome. -/
theorem row_worst_error : worst .error .failed = .error := by decide

/-- **C-04, E-24** (transcription): `failed` beats `skipped`. -/
theorem row_worst_failed : worst .failed .skipped = .failed := by decide

/-- **C-04** (transcription): `skipped` beats `passed`, and `passed` is `worst`'s unit. -/
theorem row_worst_skipped : worst .skipped .passed = .skipped ∧ worst .passed .passed = .passed := by
  decide

/-- **C-05 step 1** (transcription): a retired id is `RETIRED`. -/
theorem row_status_retired : statusOf { evBase with retired := true } = .retired := by decide

/-- **C-05 step 2a** (transcription): no citation at all is `UNCITED`. -/
theorem row_status_uncited :
    statusOf { evBase with hasTestCitation := false, hasSrcCitation := false } = .uncited := by
  decide

/-- **C-05 step 2a** (transcription): source citations but no test citation is `UNTESTED`. -/
theorem row_status_untested : statusOf { evBase with hasTestCitation := false } = .untested := by
  decide

/-- **C-05 step 2b, F-001, E-25** (transcription): a T id cited in source only is `UNCITED`. -/
theorem row_status_T_src_only :
    statusOf { evBase with family := .T, hasTestCitation := false } = .uncited := by decide

/-- **C-05 step 3** (transcription): a citing case without an outcome is `UNVERIFIED`. -/
theorem row_status_unverified :
    statusOf { evBase with anyTestHasOutcome := false } = .unverified := by decide

/-- **C-05 step 4** (transcription): a failed or error outcome is `FAILING`. -/
theorem row_status_failing : statusOf { evBase with anyFailedOrError := true } = .failing := by decide

/-- **C-05 step 4** (transcription): all outcomes skipped is `SKIPPED`. -/
theorem row_status_skipped : statusOf { evBase with allOutcomesSkipped := true } = .skipped := by decide

/-- **C-05 step 4** (transcription): otherwise `PASSING`. -/
theorem row_status_passing : statusOf evBase = .passing := by decide

/-- **C-05 step 5, R-11** (transcription): verdicts `{EXECUTES_ONLY}` downgrade `PASSING`. -/
theorem row_status_weakly :
    statusOf { evBase with judgeEnabled := true, verdicts := [.executesOnly] } = .weaklyPassing := by
  decide

/-- **C-05 step 5, E-26** (transcription): `{ASSERTS, EXECUTES_ONLY}` stays `PASSING`. -/
theorem row_status_asserts_wins :
    statusOf { evBase with judgeEnabled := true, verdicts := [.asserts, .executesOnly] } = .passing := by
  decide

/-- **C-05 step 5, R-35, E-51** (transcription): a RECORDED id never reaches step 5. -/
theorem row_status_recorded :
    statusOf { evBase with judgeEnabled := true, recorded := true, verdicts := [.executesOnly] } = .passing := by
  decide

/-- **C-05 step 5** (transcription): `{UNKNOWN}` alone leaves the id `PASSING`. -/
theorem row_status_unknown_only :
    statusOf { evBase with judgeEnabled := true, verdicts := [.unknown] } = .passing := by decide

/-- **C-06 rule 1** (transcription): a provider failure coerces to `UNKNOWN`, clause `""`. -/
theorem row_coerce_rule1 :
    coerce { aBase with failure := some "timeout" } =
      { verdict := .unknown, clause := [], coerced := true, rationale := failureRationale "timeout" } := by
  decide

/-- **C-06 rule 2, E-15** (transcription): a verdict outside the four-value set is `UNKNOWN`. -/
theorem row_coerce_rule2 :
    coerce { aBase with verdict := some "MAYBE" } =
      { verdict := .unknown, clause := [], coerced := true, rationale := rationaleMalformed.toList } := by
  decide

/-- **C-06 rule 4, E-49** (transcription): `UNRELATED` keeps its token and blanks the clause. -/
theorem row_coerce_rule4 :
    (coerce { aBase with verdict := some "UNRELATED", clause := some "returns the sum" }).clause = [] := by
  decide

/-- **C-06 rule 5, E-48** (transcription): an unlocated clause on `ASSERTS` is `UNKNOWN`. -/
theorem row_coerce_rule5 :
    coerce { aBase with verdict := some "ASSERTS", clause := some "x", clauseLocated := false } =
      { verdict := .unknown, clause := [], coerced := true, rationale := rationaleUnlocated.toList } := by
  decide

/-- **C-06 rule 6, E-16** (transcription): `ASSERTS` without evidence is `UNKNOWN`. -/
theorem row_coerce_rule6 :
    coerce { aBase with verdict := some "ASSERTS", clause := some "returns the sum", clauseLocated := true, evidenceCount := 0 } =
      { verdict := .unknown, clause := [], coerced := true, rationale := rationaleUngrounded.toList } := by
  decide

/-- **C-06 rule 7, E-16** (transcription): evidence outside the span is `UNKNOWN`. -/
theorem row_coerce_rule7 :
    coerce { aBase with verdict := some "ASSERTS", clause := some "returns the sum", clauseLocated := true, evidenceCount := 1, evidenceInSpan := false } =
      { verdict := .unknown, clause := [], coerced := true, rationale := rationaleUngrounded.toList } := by
  decide

/-- **C-06, E-17** (transcription): a well-formed reply is recorded as returned. -/
theorem row_coerce_ok :
    (coerce { aBase with verdict := some "ASSERTS", clause := some "returns the sum", clauseLocated := true, evidenceCount := 2 }).verdict = .asserts := by
  decide

/-- **§5.4, R-14** (transcription): conforming, non-strict, exits `0`. -/
theorem row_exit_conforming : exitOfCheck factConforming false = exitConforming := by decide

/-- **§5.4, R-15** (transcription): a `FAILING` in-scope id exits `1`. -/
theorem row_exit_failing :
    exitOfCheck { factConforming with anyInScopeFailing := true } false = exitNotConforming := by
  decide

/-- **R-15** (transcription): a strict run needs every in-scope id `PASSING`. -/
theorem row_exit_strict :
    exitOfCheck { factConforming with allInScopePassing := false } true = exitNotConforming := by
  decide

/-- **§5.4, K-01, E-01** (transcription): a spec with no in-scope ids exits `3`, no reports. -/
theorem row_fault_E01 :
    outcome (.fault .specZeroIds) = some { exit := exitContract, reports := false } := by decide

/-- **§5.4, K-01, E-02** (transcription): a duplicate declaration exits `3`, no reports. -/
theorem row_fault_E02 :
    outcome (.fault .specDuplicateId) = some { exit := exitContract, reports := false } := by decide

/-- **§5.4, K-01, E-03** (transcription): a retire/keep conflict exits `3`, no reports. -/
theorem row_fault_E03 :
    outcome (.fault .specRetireConflict) = some { exit := exitContract, reports := false } := by decide

/-- **§5.4, K-01, E-05** (transcription): malformed results exits `3`, no reports. -/
theorem row_fault_E05 :
    outcome (.fault .resultsMalformed) = some { exit := exitContract, reports := false } := by decide

/-- **§5.4, K-01, E-09** (transcription): a path outside `--root` exits `2`, no reports. -/
theorem row_fault_E09 :
    outcome (.fault .pathOutsideRoot) = some { exit := exitUsage, reports := false } := by decide

/-- **§5.4, K-01, E-18** (transcription): an unwritable `--out` exits `3`, no reports. -/
theorem row_fault_E18 :
    outcome (.fault .outNotWritable) = some { exit := exitContract, reports := false } := by decide

/-- **§5.4, K-01, E-21** (transcription): a missing judge env var exits `2`, no reports. -/
theorem row_fault_E21 :
    outcome (.fault .judgeEnvMissing) = some { exit := exitUsage, reports := false } := by decide

/-- **§5.4, K-01, E-52** (transcription): a `--src`/`--tests` element that is neither file nor
directory exits `2`, no reports. -/
theorem row_fault_E52 :
    outcome (.fault .pathsElementMissing) = some { exit := exitUsage, reports := false } := by decide

/-- **§5.4, K-01, E-53** (transcription): an undeclared `--changed` id exits `2`, no reports. -/
theorem row_fault_E53 :
    outcome (.fault .changedUndeclared) = some { exit := exitUsage, reports := false } := by decide

/-- **§5.4, K-01, E-54** (transcription): `impact`'s flag exclusivity exits `2`, no reports. -/
theorem row_fault_E54 :
    outcome (.fault .impactBothOrNeither) = some { exit := exitUsage, reports := false } := by decide

/-- **§5.4, K-01, E-58** (transcription): `--judge-budget N%` without triage exits `2`, no reports. -/
theorem row_fault_E58 :
    outcome (.fault .budgetPercentWithoutTriage) = some { exit := exitUsage, reports := false } := by decide

/-- **§5.4, K-01, E-60** (transcription): `explain` on an undeclared id exits `2`, no trace. -/
theorem row_fault_E60 :
    outcome (.fault .explainUndeclaredId) = some { exit := exitUsage, reports := false } := by decide

/-- **§5.4, K-01, §5.1** (transcription): a bad flag value (judge mode, `--max-unknown`,
`--judge-concurrency`, `--judge-budget`, `--progress`, `--verbose`, `--depth`) exits `2`. -/
theorem row_fault_badValue :
    outcome (.fault .judgeModeInvalid) = some { exit := exitUsage, reports := false } ∧
    outcome (.fault .maxUnknownInvalid) = some { exit := exitUsage, reports := false } ∧
    outcome (.fault .judgeConcurrencyInvalid) = some { exit := exitUsage, reports := false } ∧
    outcome (.fault .judgeBudgetInvalid) = some { exit := exitUsage, reports := false } ∧
    outcome (.fault .progressInvalid) = some { exit := exitUsage, reports := false } ∧
    outcome (.fault .verboseInvalid) = some { exit := exitUsage, reports := false } ∧
    outcome (.fault .depthInvalid) = some { exit := exitUsage, reports := false } := by
  decide

/-- **E-41, K-01** (transcription): an interrupt exits `3` with no surviving report. -/
theorem row_interrupt :
    outcome .interrupt = some { exit := exitContract, reports := false } := by decide

/-- **C-13** (transcription): an `impact` run whose changed set came out empty exits `0`. -/
theorem row_impact_empty :
    outcome .impactEmptyChanged = some { exit := exitConforming, reports := true } := by decide

/-- **C-18** (transcription): an `explain` on a declared id writes no file and exits `0`. -/
theorem row_explain_declared :
    outcome .explainDeclared = some { exit := exitConforming, reports := false } := by decide

/-- **C-11** (transcription): half the edges fill half the bar. -/
theorem row_bar_half : barCells 5 10 = 10 := by decide

/-- **C-11** (transcription): a determined edge count equal to the total fills all 20 cells. -/
theorem row_bar_full : barCells 10 10 = 20 := by decide

/-- **C-21, D-49** (transcription): no citation at all joins to `none` (the id's `proof` array is
empty). -/
theorem row_proof_absent :
    proofStateOf { cited := false, nameMatch := false, locationMatch := false, manifestChecked := false } = none := by
  decide

/-- **K-17** (transcription): a citation with no name-matching manifest entry is `unknown`. -/
theorem row_proof_unknown :
    proofStateOf { cited := true, nameMatch := false, locationMatch := false, manifestChecked := false } = some .unknown := by
  decide

/-- **K-17** (transcription): a name match at a different file/line is `stale`. -/
theorem row_proof_stale :
    proofStateOf { cited := true, nameMatch := true, locationMatch := false, manifestChecked := true } = some .stale := by
  decide

/-- **C-21** (transcription): a full match whose manifest entry is `checked` joins `checked`. -/
theorem row_proof_checked :
    proofStateOf { cited := true, nameMatch := true, locationMatch := true, manifestChecked := true } = some .checked := by
  decide

/-- **C-21** (transcription): a full match whose manifest entry is `failed` joins `failed`, with
the build error line carried at the `theorems[]` level, not modelled here (deferred to T-99). -/
theorem row_proof_failed :
    proofStateOf { cited := true, nameMatch := true, locationMatch := true, manifestChecked := false } = some .failed := by
  decide

/-- **R-15, D-64** (transcription, v1.25): under `--strict`, an `UNCONTROLLED` hazard exits `1`
although every in-scope id is `PASSING`. -/
theorem row_exit_uncontrolled_strict :
    exitOfCheck { factConforming with anyUncontrolled := true } true = exitNotConforming := by
  decide

/-- **R-105** (transcription, v1.24): a non-strict run exiting `0` with an id not `PASSING` prints
`UNPROVEN`. -/
theorem row_summary_unproven :
    summaryWord { factConforming with allInScopePassing := false } false = .unproven := by decide

/-- **R-109** (transcription, v1.25): a risk-file hazard that no marker names has no controls and
is `UNCONTROLLED`. -/
theorem row_hazard_unmarked_uncontrolled : hazardStatus [] = .uncontrolled := rfl

/-- **C-26, E-82, E-83** (transcription, v1.25): `verify`'s four exit codes. -/
theorem row_verify_codes :
    verifyExit .usageFault = exitUsage ∧ verifyExit .malformedManifest = exitContract ∧
    verifyExit (.checked 0) = exitConforming ∧ verifyExit (.checked 1) = exitNotConforming := by
  decide

/-- **E-65, E-70, E-84, E-85** (transcription): the unreadable halves exit `2`, the malformed
halves exit `3`, no report either way; `SOURCE_DATE_EPOCH` malformed is a usage fault. -/
theorem row_fault_v119_v125 :
    outcome (.fault .proofResultsUnreadable) = some { exit := exitUsage, reports := false } ∧
    outcome (.fault .proofResultsMalformed) = some { exit := exitContract, reports := false } ∧
    outcome (.fault .citationMapUnreadable) = some { exit := exitUsage, reports := false } ∧
    outcome (.fault .citationMapMalformed) = some { exit := exitContract, reports := false } ∧
    outcome (.fault .riskFileMalformed) = some { exit := exitContract, reports := false } ∧
    outcome (.fault .sourceDateEpochInvalid) = some { exit := exitUsage, reports := false } := by
  decide

/-- **R-102** (transcription, v1.23): an invalid or repeated `--namespace` is a usage error. -/
theorem row_fault_namespace :
    outcome (.fault .namespaceInvalid) = some { exit := exitUsage, reports := false } := by decide

/-- **E-86** (transcription, v1.26): an install with no hashed `RECORD` fails first as
`not an installed wheel`, and exits `1`. -/
theorem row_qualify_not_wheel :
    firstFailure { treePresent := false, dataFaults := 0, mismatches := 0, missing := 0,
                   casesPass := [true, true] } = some .notWheel ∧
    qualifyExit { treePresent := false, dataFaults := 0, mismatches := 0, missing := 0,
                  casesPass := [true, true] } = exitNotConforming := by
  decide

end Rows

/-! ## Invariants — the "for all inputs" theorems -/

section Invariants

/-- **C-01, I-011** — the family letters are injective, so two ids of different families never
normalize to one another (`R-07` and `C-07` never collide). -/
theorem letters_inj (a b : Family) (h : a.letter = b.letter) : a = b := by
  cases a <;> cases b <;> simp_all [Family.letter]

/-- **C-01, I-011** — an id is its family and number: two keys that agree on both are the same id,
so the three spellings `R-7`/`R-07`/`R-007` cannot be made to differ. -/
theorem keys_inj (a b : IdKey) (h : a.number = b.number) (hf : a.family = b.family) : a = b := by
  cases a; cases b; simp_all

/-- **C-01** — `letterFamily` is the inverse of `Family.letter`. -/
theorem letterFamily_roundtrip (f : Family) : letterFamily f.letter = some f := by
  cases f <;> rfl

/-- **K-01** — the closed exit set: every stated outcome's exit code is one of `0,1,2,3`. This is a
claim over the whole input space, not a re-read of `outcome`. -/
theorem exitClosed (i : Input) (r : Result) (h : outcome i = some r) : r.exit ∈ k01ExitSet := by
  grind

/-- **I-001** — "no file outside the report pair is written": a usage or contract fault, and the
interrupt, write no report file. -/
theorem faultWritesNoReports (x : Fault) : ∃ r, outcome (.fault x) = some r ∧ r.reports = false :=
  ⟨_, rfl, rfl⟩

/-- **I-001** — the interrupt writes no report file. -/
theorem interruptWritesNoReports : ∃ r, outcome .interrupt = some r ∧ r.reports = false :=
  ⟨_, rfl, rfl⟩

/-- **I-001** — a `check` run always writes both reports, whatever its exit code. -/
theorem checkWritesReports (f : ReportFacts) (s : Bool) :
    ∃ r, outcome (.check f s) = some r ∧ r.reports = true := ⟨_, rfl, rfl⟩

/-- **I-001, C-18** — an `explain` run writes no report file. -/
theorem explainWritesNoReport :
    (∃ r, outcome .explainDeclared = some r ∧ r.reports = false) ∧
    (∃ r, outcome .explainUndeclared = some r ∧ r.reports = false) :=
  ⟨⟨_, rfl, rfl⟩, ⟨_, rfl, rfl⟩⟩

/-- **C-13** — `impact` never exits `1`: "there is no `1`: nothing it reports is pass/fail". -/
theorem impactNeverExitOne (r : Result) (h : outcome .impactEmptyChanged = some r) :
    r.exit ≠ exitNotConforming := by
  grind

/-- **I-004** — the downgrade-only judge, quantified over *all* evidence records: enabling the
judge never changes a status except `PASSING → WEAKLY_PASSING`. This is not a definition re-read —
it ranges over the whole input space and exhibits the only difference between the two
configurations. -/
theorem downgradeOnly (e : Evidence) :
    statusOf { e with judgeEnabled := true } = statusOf { e with judgeEnabled := false } ∨
    (statusOf { e with judgeEnabled := false } = .passing ∧
      statusOf { e with judgeEnabled := true } = .weaklyPassing) := by
  grind

/-- **R-11, I-004** — the judge step produces only `PASSING` or `WEAKLY_PASSING`; it can never mint
a failure, a silence, or any other status. -/
theorem step5OnlyPassingOrWeak (e : Evidence) :
    step5 e = .passing ∨ step5 e = .weaklyPassing := by
  grind

/-- **R-35, E-51** — a RECORDED id is exempt from step 5 and from nothing else: with the judge on,
a recorded id's status is its non-judge status, whatever its verdicts are. -/
theorem recordedSkipsJudge (e : Evidence) :
    statusOf { e with recorded := true } =
      statusOf { e with recorded := true, judgeEnabled := false } := by
  grind

/-- **R-25, E-25, F-001** — a T id's source citations are evidence only: adding one to a non-retired
T id with no test citation does not move it off `UNCITED`. -/
theorem tSrcCitationEvidenceOnly (e : Evidence) (hr : e.retired = false) (h : e.family = .T)
    (h2 : e.hasTestCitation = false) :
    statusOf { e with hasSrcCitation := true } = .uncited := by
  grind

/-- **E-19** — with no `--src` and no `--tests` citations, a non-retired non-T id is `UNCITED`. -/
theorem e19NoCitations (e : Evidence) (h : e.retired = false) (hf : e.family ≠ .T)
    (ht : e.hasTestCitation = false) (hs : e.hasSrcCitation = false) : statusOf e = .uncited := by
  grind

/-- **C-06 rule 8, K-07** — every recorded rationale is at most 280 characters, whatever the
provider returned. -/
theorem rationaleBounded (r : List Char) : (truncateRationale r).length ≤ rationaleMax := by
  unfold truncateRationale rationaleMax rationaleKeep
  split
  · omega
  · simp only [List.length_append, List.length_take, List.length_cons, List.length_nil]
    have : min 277 r.length ≤ 277 := Nat.min_le_left _ _
    omega

/-- **K-07** — a rationale already within the bound is passed through untouched. -/
theorem rationaleUntouched (r : List Char) (h : r.length ≤ rationaleMax) : truncateRationale r = r := by
  grind

/-- **E-49** — a verdict coerced to `UNKNOWN` by any validation rule is recorded with an empty
clause, for *every* raw answer — not just the ones the row theorems cover. -/
theorem coercedClauseBlank (a : RawAnswer) (h : (coerce a).coerced = true) : (coerce a).clause = [] := by
  grind

/-- **E-49, C-06** — `UNRELATED` and `UNKNOWN` are recorded with an empty clause whether or not the
provider quoted one. -/
theorem unrelatedUnknownClauseBlank (a : RawAnswer)
    (h : (coerce a).verdict = .unrelated ∨ (coerce a).verdict = .unknown) :
    (coerce a).clause = [] := by
  grind

/-- **I-005, E-16, E-48** — a recorded `ASSERTS` is grounded on both sides: it was not coerced, it
carried at least one in-span evidence line, and its clause was located under K-15. (The clause's
non-emptiness follows from `k15Min` for a long statement; the model carries `clauseLocated` as the
matcher's verdict, so the fact recorded here is the grounding one.) -/
theorem assertGrounded (a : RawAnswer) (h : (coerce a).verdict = .asserts) :
    (coerce a).coerced = false ∧ 0 < a.evidenceCount ∧ a.clauseLocated = true ∧
      a.evidenceInSpan = true := by
  grind

/-- **I-008** — a ratio is `none` exactly on a zero denominator; no run raises on `0/0`. -/
theorem ratioNoneIff (num den : Nat) : ratioUnits num den = none ↔ den = 0 := by
  grind

/-- **I-008, R-09** — the conformance ratio is `null` exactly when `in_scope = 0` (the E-01 case),
and never `0.0` for an undefined ratio. -/
theorem conformanceNoneIff (passing inScope : Nat) :
    conformanceUnits passing inScope = none ↔ inScope = 0 := by
  grind

/-- **C-07, F-405** — `judge_strength` is `none` exactly when both of its populations are empty:
every `PASSING` id is RECORDED and nothing is `WEAKLY_PASSING`. -/
theorem judgeStrengthNoneIff (p w : Nat) : judgeStrengthUnits p w = none ↔ p + w = 0 := by
  grind

/-- **C-07, E-14, E-35 (strengthened v1.20)** — whenever no call succeeded and an edge was
eligible, `judge_available` is `false` — whether every call failed (E-14, `issued > 0`) or none
was issued at all (E-35, `issued = 0`). Originally stated only for `issued > 0`; the
eligible-but-unissued case was F-502's own gap, so this theorem could not cover it either until
the fix — the hypothesis is now dropped rather than kept redundant. -/
theorem judgeAvailableAllFailed (c : JudgeCalls) (hm : c.mode ≠ .none)
    (hs : c.succeeded = 0) (he : 0 < c.eligible) :
    judgeAvailable c = some false := by
  grind

/-- **C-07, E-36** — with no eligible edge, `judge_available` is vacuously `true`. -/
theorem judgeAvailableVacuous (c : JudgeCalls) (hm : c.mode ≠ .none) (he : c.eligible = 0) :
    judgeAvailable c = some true := by
  grind

/-- **C-07** — `judge_available` is `none` if and only if `--judge none`: with `mock`/`llm` it is
always `some _`, including the eligible-but-unissued configuration finding F-502 left
under-determined before v1.20's fix. This is the totality claim F-502 asked for, stated directly
rather than as a disjunction of the cases that are *not* `none` — see F-502's finding entry for
the resolved witnesses at the point that used to fail. -/
theorem judgeAvailableNullIffNone (c : JudgeCalls) :
    judgeAvailable c = none ↔ c.mode = .none := by
  grind

/-- **R-15, R-28** — with `--strict`, exit `0` implies every in-scope id is `PASSING`, `dangling`
and `stale` are empty, and the R-28 judge gate holds. -/
theorem strictExitZeroImpliesAll (f : ReportFacts) (h : exitOfCheck f true = exitConforming) :
    f.allInScopePassing = true ∧ f.anyDangling = false ∧ f.anyStale = false ∧
      strictJudgeHolds f = true := by
  grind

/-- **R-28, E-32, Q-004** — `strict_judge_failure` is non-null only when `--strict` and `--judge llm`
hold, and takes `unavailable` for preference when both reasons hold. -/
theorem strictJudgeFailureUnavailableFirst (f : ReportFacts) (s : Bool) :
    strictJudgeFailure f s = some "unavailable" →
      f.judgeAvailable = some false ∧ s = true ∧ f.judgeLlm = true := by
  grind

/-- **C-11, K-13** — the bar never has more than 20 filled cells: for `d ≤ n` the count is in
range. -/
theorem barCellsBounded (d n : Nat) (h : d ≤ n) (hn : 0 < n) : barCells d n ≤ progressCells := by
  unfold barCells progressCells
  simp only [Nat.pos_iff_ne_zero.mp hn, ite_false]
  exact Nat.div_le_of_le_mul (show 20 * d ≤ n * 20 by
    rw [Nat.mul_comm n 20]; exact Nat.mul_le_mul_left 20 h)

/-- **C-11, K-13** — for `d ≤ n` the drawn bar is exactly 20 cells wide. -/
theorem barLength (d n : Nat) (h : d ≤ n) (hn : 0 < n) : (bar d n).length = progressCells := by
  unfold bar progressCells
  rw [List.length_append, List.length_replicate, List.length_replicate]
  have hb : barCells d n ≤ 20 := by
    have := barCellsBounded d n h hn
    simpa [progressCells] using this
  omega

/-- **C-11** — `left` is `?:??` exactly while `d = 0`. -/
theorem remainingNoneIffZero (t d n : Nat) : remainingSeconds t d n = none ↔ d = 0 := by
  unfold remainingSeconds
  by_cases h : d = 0 <;> simp [h]

/-- **C-11** — the final state `d = n > 0` estimates zero remaining seconds. -/
theorem remainingAtEnd (t n : Nat) (hn : 0 < n) : remainingSeconds t n n = some 0 := by
  unfold remainingSeconds
  simp [Nat.pos_iff_ne_zero.mp hn]

/-- **K-15** — the clause is at least 12 characters unless the statement is shorter than 12, so a
short clause cannot be located against a long statement. -/
theorem locatedNeedsTwelve (nc s : List Char) (h : locatedN nc s = true) :
    k15Min ≤ nc.length ∨ (collapseWs s).length < k15Min := by
  unfold locatedN k15Min at h
  by_cases h1 : 12 ≤ nc.length
  · exact Or.inl h1
  · right
    by_cases h2 : (collapseWs s).length < 12
    · exact h2
    · exfalso
      simp only [Bool.or_eq_true, Bool.and_eq_true, decide_eq_true_eq] at h
      rcases h with ⟨h, _⟩ | ⟨h, _⟩
      · exact absurd h h1
      · exact absurd h h2

/-- **R-22, C-06** — the mock provider's clause is always LOCATED under K-15 when the statement is
long enough to be judged. This discharges the mock's "a prefix, so it is always LOCATED" sentence,
not the definition of `mockClause`. -/
theorem mockClauseLocated (s : List Char) (h : k15Min ≤ (collapseWs s).length) :
    locatedN (mockClause s) s = true := by
  unfold locatedN mockClause k15Min k15Cut
  have hlen : 12 ≤ ((collapseWs s).take 280).length := by
    rw [List.length_take]; exact Nat.le_min.mpr ⟨by omega, h⟩
  have hinf : infixOf ((collapseWs s).take 280) (collapseWs s) = true := infixOf_take _ _
  have hdec : decide (12 ≤ ((collapseWs s).take 280).length) = true := by simpa using hlen
  rw [hdec, hinf]
  simp

/-- **I-002** — the model's entry points are pure functions with **no environment parameter**, so
a run outcome cannot depend on the environment: two evaluations on the same input agree by `rfl`.
There is nothing to prove and nothing that *could* differ. -/
theorem outcomeEnvironmentFree (i : Input) (e₁ e₂ : Unit) :
    (fun (_ : Unit) => outcome i) e₁ = (fun (_ : Unit) => outcome i) e₂ := rfl

/-- **E-63** — a proof state never changes an id's status, for *every* evidence record and *every*
proof state: `statusWithProof` accepts one and provably returns exactly what `statusOf` already
returns. This is the "for all inputs" content of E-63's status half — `Evidence` (C-05) has no
proof field, so there is structurally nothing a proof state could move. -/
theorem statusWithProof_ignoresProof (e : Evidence) (p : Option ProofState) :
    statusWithProof e p = statusOf e := rfl

/-- **K-17** — the "never `failed`" clause, quantified over every join: a citation with no
name-matching manifest entry is `unknown` and never anything else, in particular never `failed`. -/
theorem proofUnmatchedNeverFailed (j : ProofJoin) (h : j.cited = true) (hn : j.nameMatch = false) :
    proofStateOf j = some .unknown ∧ proofStateOf j ≠ some .failed := by
  grind

/-- **K-17** — a name-matched but location-mismatched join is always `stale`, whatever the
manifest's own build status was — a `checked` build at the wrong file/line is still stale, not
silently promoted to `checked`. -/
theorem proofStaleRegardlessOfManifestStatus (j : ProofJoin) (h : j.cited = true)
    (hn : j.nameMatch = true) (hl : j.locationMatch = false) :
    proofStateOf j = some .stale := by
  grind

/-- **E-64** (v1.20) — coverage: every enumerated input now has a stated outcome. `outcome` was
partial (F-501: `.explainAbsentSpec` returned `none`) before E-64 gave that configuration its own
exit-`2` outcome; this theorem is the positive claim the old `f501NoSilenceFails` disproved, now
true by construction over every constructor of `Input`. -/
theorem noSilence : ∀ i : Input, (outcome i).isSome := by
  intro i; cases i <;> rfl

/-- **K-18** — usage-fault precedence, quantified over the contract-fault flag: whenever a usage
fault is live, the resolved exit is `exitUsage`, whether or not an input-contract violation is
*also* live (`contract` ranges over both). This is the "for all inputs" content of K-18, not a
re-read of `exitPrecedence`'s own `if`: it discharges the spec's claim that usage-fault precedence
holds *unconditionally* on `contract`, not merely at one instance of it. See F-503's finding entry
for why this closes the gap `f503ExitPrecedenceDiffer` exhibited. -/
theorem k18UsageWinsWhenBoth (contract : Bool) : exitPrecedence true contract = exitUsage := rfl

/-- **R-105** (v1.24) — `UNPROVEN` never appears under `--strict`: for every report, a strict run
that exits `0` has R-15's conditions holding, so its word is `CONFORMING`. Not a re-read of
`summaryWord`: it discharges R-105's "only possible without `--strict`", which needs the strict
exit rule to imply R-15's conditions. -/
theorem unprovenNeverStrict (f : ReportFacts) : summaryWord f true ≠ .unproven := by
  unfold summaryWord r15Holds exitOfCheck
  cases f with
  | mk a b c d e g h u x y =>
    cases a <;> cases b <;> cases c <;> cases d <;> cases u <;> simp [strictJudgeHolds] <;> grind

/-- **R-105, R-14** (v1.24) — the word follows the exit code, for every report and both modes:
`NOT CONFORMING` exactly on exit `1`, and the exit code itself never depends on the word ("the
exit code, every status and `speccheck.json` are unchanged"). -/
theorem summaryWordTracksExit (f : ReportFacts) (s : Bool) :
    (summaryWord f s = .notConforming ↔ exitOfCheck f s ≠ exitConforming) := by
  unfold summaryWord
  split <;> simp_all <;> split <;> simp

/-- **R-15, D-64** (v1.25) — for every report: an `UNCONTROLLED` hazard makes a strict run exit
`1`, whatever else holds. -/
theorem strictUncontrolledFails (f : ReportFacts) (h : f.anyUncontrolled = true) :
    exitOfCheck f true = exitNotConforming := by
  simp [exitOfCheck, h]

/-- **C-27** (v1.25) — support: the roll-up read as three cases of `CTRL(h)`. -/
theorem hazardStatus_cases (cs : List Control) :
    hazardStatus cs = if liveControls cs = [] then .uncontrolled
      else if (liveControls cs).all (fun c => c.status == .passing) then .verified
      else .notVerified := by
  unfold hazardStatus
  split <;> simp_all

/-- **C-27** (v1.25) — support: `CTRL(h)` is exactly the non-retired controlling ids. -/
theorem mem_liveControls (cs : List Control) (c : Control) :
    c ∈ liveControls cs ↔ c ∈ cs ∧ c.retired = false := by
  simp [liveControls]

/-- **C-27** (v1.25) — `UNCONTROLLED` exactly when no non-retired id controls the hazard: "no
marker names h, or every id naming it is retired". The spec states the condition on `CTRL(h)`;
this proves it in terms of the controls themselves, for every list. -/
theorem uncontrolledIffAllRetired (cs : List Control) :
    hazardStatus cs = .uncontrolled ↔ ∀ c ∈ cs, c.retired = true := by
  rw [hazardStatus_cases]
  have hnil : liveControls cs = [] ↔ ∀ c ∈ cs, c.retired = true := by
    simp [liveControls, List.filter_eq_nil_iff]
  by_cases h : liveControls cs = []
  · simp only [h, ite_true, true_iff]; exact hnil.mp h
  · have : ¬ ∀ c ∈ cs, c.retired = true := fun hall => h (hnil.mpr hall)
    simp only [h, ite_false, this, iff_false]
    split <;> simp

/-- **C-27** (v1.25) — `VERIFIED` means every non-retired control is `PASSING`, for every list. -/
theorem verifiedImpliesLivePassing (cs : List Control) (h : hazardStatus cs = .verified) :
    ∀ c ∈ cs, c.retired = false → c.status = .passing := by
  intro c hc hr
  rw [hazardStatus_cases] at h
  have hm : c ∈ liveControls cs := (mem_liveControls cs c).mpr ⟨hc, hr⟩
  by_cases hn : liveControls cs = []
  · rw [hn] at hm; simp at hm
  · simp only [hn, ite_false] at h
    by_cases hall : (liveControls cs).all (fun c => c.status == .passing) = true
    · have := List.all_eq_true.mp hall c hm
      simpa using this
    · simp [hall] at h

/-- **C-27** (v1.25) — "`WEAKLY_PASSING` is not `PASSING`": a hazard with a live
`WEAKLY_PASSING` control is never `VERIFIED`, for every list. -/
theorem weaklyControlNeverVerifies (cs : List Control)
    (h : ∃ c ∈ cs, c.retired = false ∧ c.status = .weaklyPassing) :
    hazardStatus cs ≠ .verified := by
  intro hv
  obtain ⟨c, hc, hr, hs⟩ := h
  have := verifiedImpliesLivePassing cs hv c hc hr
  rw [hs] at this; cases this

/-- **C-27** (v1.25) — support: a hazard with a live control, all of whose live controls are
`PASSING`, is `VERIFIED`. -/
theorem verifiedOfLivePassing (cs : List Control) (hne : ¬ ∀ c ∈ cs, c.retired = true)
    (hp : ∀ c ∈ cs, c.retired = false → c.status = .passing) : hazardStatus cs = .verified := by
  rw [hazardStatus_cases]
  have hn : liveControls cs ≠ [] := fun h =>
    hne ((uncontrolledIffAllRetired cs).mp (by rw [hazardStatus_cases, h]; rfl))
  have hall : (liveControls cs).all (fun c => c.status == .passing) = true := by
    apply List.all_eq_true.mpr
    intro c hc
    have := (mem_liveControls cs c).mp hc
    simp [hp c this.1 this.2]
  simp [hn, hall]

/-- **C-27, R-11, I-004** — the downgrade-only judge cannot verify a hazard: for every list and
every status map `g` that creates no `PASSING` (R-11: a verdict only ever lowers `PASSING` to
`WEAKLY_PASSING`), if the hazard is `VERIFIED` after `g`, it was `VERIFIED` before. The roll-up runs
"after C-05 step 5, from the final statuses; nothing flows back" — so the judge can only lower it. -/
theorem judgeNeverVerifiesAHazard (cs : List Control) (g : Status → Status)
    (hg : ∀ s, g s = .passing → s = .passing)
    (h : hazardStatus (cs.map (fun c => { c with status := g c.status })) = .verified) :
    hazardStatus cs = .verified := by
  have hall := verifiedImpliesLivePassing _ h
  apply verifiedOfLivePassing
  · intro hret
    have hu : hazardStatus (cs.map (fun c => { c with status := g c.status })) = .uncontrolled :=
      (uncontrolledIffAllRetired _).mpr (by
        intro c hc
        obtain ⟨d, hd, rfl⟩ := List.mem_map.mp hc
        exact hret d hd)
    rw [h] at hu; cases hu
  · intro c hc hr
    exact hg _ (hall { c with status := g c.status } (List.mem_map_of_mem hc) hr)

/-- **C-27, R-15** (v1.25) — C-27's claim that `NOT_VERIFIED` "adds nothing" to `--strict`: for
every hazard and every report in which a non-retired, non-`PASSING` control is an in-scope id that
is not `PASSING` (the coherence hypothesis — a control is a declared R/C/I/K/E id, so in scope), a
`NOT_VERIFIED` hazard already makes the strict run exit `1` through R-15's status condition. -/
theorem notVerifiedAddsNothingToStrict (cs : List Control) (f : ReportFacts)
    (hcoh : ∀ c ∈ cs, c.retired = false → c.status ≠ .passing → f.allInScopePassing = false)
    (h : hazardStatus cs = .notVerified) :
    exitOfCheck f true = exitNotConforming := by
  have hne : ¬ ∀ c ∈ cs, c.retired = true := by
    intro hret; rw [(uncontrolledIffAllRetired cs).mpr hret] at h; cases h
  have hex : ∃ c ∈ cs, c.retired = false ∧ c.status ≠ .passing := by
    apply Classical.byContradiction
    intro hno
    have hp : ∀ c ∈ cs, c.retired = false → c.status = .passing := by
      intro c hc hr
      apply Classical.byContradiction
      intro hs
      exact hno ⟨c, hc, hr, hs⟩
    rw [verifiedOfLivePassing cs hne hp] at h; cases h
  obtain ⟨c, hc, hr, hs⟩ := hex
  have := hcoh c hc hr hs
  simp [exitOfCheck, this]

/-- **C-26, K-01** (v1.25) — `verify` exits only within the closed set, for every input. -/
theorem verifyExitClosed (v : VerifyInput) : verifyExit v ∈ k01ExitSet := by
  cases v with
  | usageFault => decide
  | malformedManifest => decide
  | checked n => cases n <;> simp [verifyExit, k01ExitSet, exitNotConforming, exitConforming]

/-- **E-83, E-82** (v1.25) — a `verify` run that exits `2` or `3` read no file the manifest names
("no input file is read (a manifest cannot direct a read outside the tree)"), for every input. -/
theorem verifyFaultReadsNothing (v : VerifyInput)
    (h : verifyExit v = exitUsage ∨ verifyExit v = exitContract) :
    verifyReadsInputs v = false := by
  cases v with
  | usageFault => rfl
  | malformedManifest => rfl
  | checked n =>
    cases n <;> simp [verifyExit, exitConforming, exitNotConforming, exitUsage, exitContract] at h

/-- **C-26** (v1.25) — `verify` exits `0` exactly when the manifest was well-formed and no file
differs: for every input. -/
theorem verifyOkIffNothingDiffers (v : VerifyInput) :
    verifyExit v = exitConforming ↔ v = .checked 0 := by
  cases v with
  | usageFault => decide
  | malformedManifest => decide
  | checked n => cases n <;> simp [verifyExit, exitConforming, exitNotConforming]

/-- **C-29, R-111** (v1.26) — C-29's two statements agree: the verdict sentence ("`QUALIFIED`
iff …") and the first-failure order ("the first that applies, in this order") are transcribed
separately, and for every set of facts the verdict is `QUALIFIED` exactly when no failure applies.
A spec that let these disagree would print `QUALIFIED` with a failure, or a failure line under
`QUALIFIED`. -/
theorem verdictAgreesWithFirstFailure (q : IQFacts) :
    verdictQualified q = true ↔ firstFailure q = none := by
  unfold verdictQualified firstFailure
  cases q with
  | mk t d m k c =>
    cases t <;> simp <;> by_cases hd : d = 0 <;> by_cases hm : m = 0 <;> by_cases hk : k = 0 <;>
      simp [hd, hm, hk] <;> split <;> simp_all

/-- **R-111, R-112, E-86** (v1.26) — the `QUALIFIED` line always has a tree to print: for every set
of facts, exit `0` implies `package_tree_sha256` is non-null. -/
theorem qualifiedHasTree (q : IQFacts) (h : qualifyExit q = exitConforming) :
    q.treePresent = true := by
  unfold qualifyExit verdictQualified at h
  cases ht : q.treePresent <;> simp_all [exitConforming, exitNotConforming]

/-- **E-86** (v1.26) — "not an installed wheel" outranks every other failure: for every set of
facts with no tree, the first failure is `notWheel`, whatever the lists and cases hold. -/
theorem notWheelOutranksAll (q : IQFacts) (h : q.treePresent = false) :
    firstFailure q = some .notWheel := by
  simp [firstFailure, h]

/-- **E-88** (v1.26) — a failing OQ case can never be masked: for every set of facts in
which some case failed, the run is not qualified. -/
theorem caseFailureNeverQualifies (q : IQFacts) (h : q.casesPass.all id = false) :
    qualifyExit q = exitNotConforming := by
  simp [qualifyExit, verdictQualified, h]

/-- **E-87** (v1.26) — a packaged-data fault can never be masked either. -/
theorem dataFaultNeverQualifies (q : IQFacts) (h : q.dataFaults ≠ 0) :
    qualifyExit q = exitNotConforming := by
  simp [qualifyExit, verdictQualified, h]

/-- **R-115** (v1.26) — the version order is strict: no version is later than itself. -/
theorem verLtIrrefl (v : Version) : verLt v v = false := by
  simp [verLt]

/-- **R-115** (v1.26) — and asymmetric: if `a` is later than `b`, `b` is not later than `a`. -/
theorem verLtAsymm (a b : Version) (h : verLt a b = true) : verLt b a = false := by
  cases a; cases b; simp [verLt] at *; omega

/-- **R-115, C-31** (v1.26) — an unfixed anomaly is always listed, for every file and version. -/
theorem unfixedAlwaysListed (v : Version) (as : List Anomaly) (a : Anomaly) (ha : a ∈ as)
    (hf : a.fixedIn = none) : a ∈ openAnomalies v as := by
  simp [openAnomalies, ha, hf]

/-- **R-115, C-31** (v1.26) — an anomaly fixed in the running version, or in an earlier one, is
never listed, for every file. -/
theorem fixedNotLaterNeverListed (v f : Version) (as : List Anomaly) (a : Anomaly)
    (hf : a.fixedIn = some f) (hle : verLt v f = false) : a ∉ openAnomalies v as := by
  simp [openAnomalies, hf, hle]

/-- **R-115** (v1.26) — the fixed-in-this-version case, from the order's irreflexivity: an anomaly
fixed in the running version is not listed. -/
theorem fixedInRunningNeverListed (v : Version) (as : List Anomaly) (a : Anomaly)
    (hf : a.fixedIn = some v) : a ∉ openAnomalies v as :=
  fixedNotLaterNeverListed v v as a hf (verLtIrrefl v)

/-- **R-115** (v1.26) — "in file order": the listed anomalies are a sublist of the file. -/
theorem openAnomaliesKeepFileOrder (v : Version) (as : List Anomaly) :
    (openAnomalies v as).Sublist as := List.filter_sublist

end Invariants

/-! ## Reachability — the spec claims each exit code is reachable -/

section Reachability

/-- **K-01, R-14** — exit `0` is reached (a conforming `check`, or an empty-changed `impact`). -/
theorem exit0Reachable : ∃ i, ∃ r, outcome i = some r ∧ r.exit = exitConforming :=
  ⟨.check factConforming false, _, rfl, rfl⟩

/-- **K-01, R-14** — exit `1` is reached (a `FAILING` in-scope id). -/
theorem exit1Reachable : ∃ i, ∃ r, outcome i = some r ∧ r.exit = exitNotConforming :=
  ⟨.check { factConforming with anyInScopeFailing := true } false, _, rfl, rfl⟩

/-- **K-01, R-14** — exit `2` is reached (a usage fault). -/
theorem exit2Reachable : ∃ i, ∃ r, outcome i = some r ∧ r.exit = exitUsage :=
  ⟨.fault .pathOutsideRoot, _, rfl, rfl⟩

/-- **K-01, R-14** — exit `3` is reached (a contract fault, and an interrupt). -/
theorem exit3Reachable : ∃ i, ∃ r, outcome i = some r ∧ r.exit = exitContract :=
  ⟨.fault .specZeroIds, _, rfl, rfl⟩

end Reachability

/-! ## Findings — witnesses for the spec-precision gaps -/

section Findings

/-- **F-501 (G-1, silent case) — resolved v1.20, E-64.** The `explain` configuration with no
`--spec`: the synopsis made `--spec` optional for `explain` (`speccheck explain ID [--spec
SPEC.md]`) while the §5.1 flag table marked it `Required.`. Originally witnessed by
`outcome .explainAbsentSpec = none` (`f501ExplainAbsentSpecSilent`); under the resolved model that
statement no longer typechecks as a fact about it — the theorem below proves the input now has
E-64's stated outcome (exit `2`, no report) instead. `f501NoSilenceFails` (`¬ (∀ i,
(outcome i).isSome)`) likewise no longer holds; `noSilence` in `section Invariants` proves the
positive claim it used to disprove. See `docs/reviews/SPEC_MODEL_FINDINGS.md` F-501. -/
theorem f501ResolvedExplainAbsentSpecUsage :
    outcome .explainAbsentSpec = some { exit := exitUsage, reports := false } := rfl

/-- **F-502 (G-2, under-determined pin) — resolved v1.20.** `judge_available` on a run where
eligible edges exist but no C-06 call was issued: every edge budget-skipped by K-12 (`N%` with
`N = 0`, or the `SECONDS` deadline reached before the first request, E-35). Originally witnessed
by `judgeAvailable { mode := .llm, eligible := 3, issued := 0, succeeded := 0 } = none`
(`f502JudgeAvailableBudgetSilent`) and its `--judge mock` twin
(`f502JudgeAvailableBudgetSilentMock`); under the resolved model both configurations now compute
`some false`, not `none` — the theorem below proves it at the exact points that used to be silent.
`f502Contrast`'s two cases (every call failed → `false`; no eligible edge → `true`) were already
true and remain so, now joined by the third case the gap used to leave out. -/
theorem f502ResolvedJudgeAvailableBudgetFalse :
    judgeAvailable { mode := .llm, eligible := 3, issued := 0, succeeded := 0 } = some false ∧
    judgeAvailable { mode := .mock, eligible := 1, issued := 0, succeeded := 0 } = some false := by
  decide

/-- **F-502 (G-2)** — the contrast cases C-07 already pinned: every call failed gives `false`, and
no eligible edge gives `true`. Unaffected by the fix; kept as a sanity check that the boundary
cases the spec already determined still hold under the corrected, now-total function. -/
theorem f502Contrast :
    judgeAvailable { mode := .llm, eligible := 3, issued := 3, succeeded := 0 } = some false ∧
    judgeAvailable { mode := .llm, eligible := 0, issued := 0, succeeded := 0 } = some true := by
  decide

/-- **F-502 (G-2) — resolved v1.20, E-32.** The consequence: a `--strict --judge llm` run whose
eligible edges were all budget-skipped and every status is `PASSING` still exits `1` (unchanged —
the R-28 gate still wants `judge_available = true`), but `strict_judge_failure` is now
`"unavailable"`, not `null` (originally witnessed by `f502StrictJudgeFailureNull`, which no longer
holds: `judge_available` is never `none` under `llm`, so the `ReportFacts` that theorem
constructed no longer arises from `judgeAvailable`). This is the same exit code with an honest
reason, exactly the fix the finding's "why it matters" asked for. -/
theorem f502ResolvedStrictJudgeFailureUnavailable :
    exitOfCheck { factConforming with judgeLlm := true, judgeAvailable := some false } true
      = exitNotConforming ∧
    strictJudgeFailure { factConforming with judgeLlm := true, judgeAvailable := some false } true
      = some "unavailable" := by
  decide

/- **F-503 (G-2, under-specified relation) — resolved v1.20, K-18.** When one run carries both a
usage fault (exit `2`) and an input-contract violation (exit `3`), §5.4's table and K-01 gave no
precedence: `f503ExitPrecedenceDiffer` exhibited two orderings, each faithful to the table, that
disagree on the same abstract inputs — and, read purely as a fact about two *different* functions,
that disagreement is still true (nothing makes two distinct functions agree). What closes the gap
is that the spec now names *one* of them, `exitPrecedence`, as *the* model (K-18): the
contrast-first ordering `f503ExitPrecedenceDiffer` exhibited is no longer a candidate reading of
`SPEC.md`, only `exitPrecedence`'s usage-first order is — see `k18UsageWinsWhenBoth` in
`section Invariants`. -/

/-- **F-504 (G-2, under-specified interaction, v1.19) — resolved v1.19.1.** C-07/D-49 originally
tied the top-level `proof` key's presence (and therefore its `build` echo) to `--proof` alone:
"omitted entirely — on the top-level object and on every id — when `--proof` was not given." But
C-21 states the checker *reads* `--proof-results` independently — a manifest given without
`--proof` still has its `build` block parsed (there is simply nothing to join it to, since no
citation exists). That wording meant a `--proof-results`-only run wrote **no `proof` key at
all**, silently discarding the manifest's own build result (exit code, declaration counts) that
was in fact read. Originally witnessed by `topLevelProofKeyPresent false true = false`
(`f504ManifestReadButKeyAbsent`, now false under the corrected model, since `false || true` is
`true` — that non-typechecking IS the fix's proof: the buggy behavior the finding named is no
longer a fact about this model). D-49 was amended same-session (before any implementation
existed) to gate the key on `--proof ∨ --proof-results`; `topLevelProofKeyPresent` now computes
that rule, and the witness below proves the gap is closed. -/
theorem f504ResolvedManifestAloneWritesKey : topLevelProofKeyPresent false true = true := rfl

/-- **F-904 (G-2, two statements disagree) — open.** E-19 states that a run whose in-scope ids
are all `UNCITED` (no `--src`/`--tests` citation at all) exits `1`. §5.4's table and R-15 give exit
`0` to every non-strict run with no `FAILING` in-scope id, and an all-`UNCITED` run has none. The
witness is one report — all ids uncited, nothing failing, `--strict` off — on which §5.4's exit map
gives `0` while E-19's stated exit is `1`. The implementation follows E-19 (`report.py`
`exit_code_for`); `proof/`'s model carries that branch. See `docs/reviews/SPEC_MODEL_FINDINGS.md`
F-904. -/
theorem f904E19DisagreesWithExitTable :
    exitOfCheck { factConforming with allInScopePassing := false, allInScopeUncited := true } false
      = exitConforming ∧
    e19Exit { factConforming with allInScopePassing := false, allInScopeUncited := true }
      = some exitNotConforming := by
  decide

/-- **F-905 (G-2, decision row and normative rows disagree) — open.** D-45 (confirmed v1.19)
states that a `failed` proof trips `--strict` when `--proof-results` was given and is readable;
R-15 states that status and hazard status are "the only inputs to this rule", and §5.4 never
mentions a proof. The witness is one strict report — everything `PASSING`, no dangling, stale or
uncontrolled hazard, a failed proof with a readable manifest — on which R-15/§5.4 exit `0` while
D-45 says the strict gate fails. The implementation follows D-45 (`report.py` `exit_code_for`). See
`docs/reviews/SPEC_MODEL_FINDINGS.md` F-905. -/
theorem f905D45DisagreesWithR15 :
    exitOfCheck { factConforming with proofFailedWithManifest := true } true = exitConforming ∧
    d45StrictFails { factConforming with proofFailedWithManifest := true } true = true := by
  decide

end Findings

-- ## Closing: the deferral table and the excluded table
--
-- ### Deferred — out of Lean's reach, carried by a §9 test (planned)
--
-- **There is no implementation.** The carrier column names the §9 test IDs that will witness each
-- requirement when a build runs them; every one is **planned**. A requirement whose Lean half is
-- proven *and* whose process half is deferred appears twice — as a bold tag above and as a row here;
-- that dual state is the normal shape, not a conflict.
--
-- | Spec ID | Content (out of Lean's reach) | Carried by (planned) |
-- | --- | --- | --- |
-- | C-02 | SpecIndex | T-01, T-06, T-72, T-77, T-79 (planned) |
-- | C-03 | Citation, TestCase, attribution | T-09, T-10, T-13, T-14, T-36, T-56, T-65, T-66, T-67, T-78, T-85 (planned) |
-- | C-08 | Markdown report layout (SPEC_CONFORMANCE_REPORT.md) | T-35, T-73, T-75, T-77 (planned) |
-- | C-09 | LLM provider configuration | T-33, T-40 (planned) |
-- | C-10 | Judge instruction text (normative; F-004) | T-33, T-54, T-74, T-75, T-83, T-84, T-87 (planned) |
-- | C-12 | Spec-internal edges (v1.13; R-36) | T-79 (planned) |
-- | C-14 | Declared vs. incidental citations (v1.14; R-39) | T-85, T-86 (planned) |
-- | C-15 | declared in the judge request; the instruction text is advisory (v1.14; R-39) | T-87 (planned) |
-- | C-16 | declared and declared_ratio in the JSON report (v1.14; R-39) | T-86, T-88 (planned) |
-- | C-17 | Jev triage provider (v1.15; K-16, I-015) | T-89, T-90 (planned) |
-- | C-19 | Help contract (v1.18; R-41) | T-95, T-96, T-97, T-98 (planned) |
-- | E-04 | ID declared inside a fenced code block in SPEC.md — Not a declaration; ignored silently (spec templates contain exa… | T-05 (planned) |
-- | E-07 | Result <testcase> joins no attributed test case — Listed under unattributed_results; not counted for any ID; exit u… | T-18 (planned) |
-- | E-08 | Test case cites an ID but has no result (results absent, or case not run) — Case listed under that ID's unrun; igno… | T-22 (planned) |
-- | E-10 | File > 2 MiB under a scan root — Skipped; Note skipped 1 file over 2 MiB: <path>. | T-13 (planned) |
-- | E-11 | A scanned file — or SPEC.md itself — is not valid UTF-8 — Decoded with replacement; Note; citations on replaced byt… | T-13, T-01 (planned) |
-- | E-12 | .py test file fails to parse — Whole file is one file-level case; Note parse fallback: <path>. | T-11 (planned) |
-- | E-13 | Test citation lands in a file-level case (module docstring, helper, fixture) — Attributed to the file-level case; t… | T-10 (planned) |
-- | E-20 | Dangling citation of a token that looks retired in code (R-99 in a comment) — Strikethrough is only meaningful in S… | T-23 (planned) |
-- | E-22 | Test file cites the same ID on several lines of one case — One edge; lines lists every line. | T-14 (planned) |
-- | E-23 | --spec, --results, or a report path lies under a --src/--tests root (e.g. --src ., or --out inside src/) — Those fi… | T-36 (planned) |
-- | E-27 | A result's classname suffix-matches two test cases equally (tests/a/test_core.py and tests/b/test_core.py, result c… | T-58 (planned) |
-- | E-28 | A test function (underscore or not) is a method of a class that is neither Test-named nor a TestCase subclass, or o… | T-56 (planned) |
-- | E-29 | A file under a scan root contains a 0x00 byte in its first 8192 bytes — Skipped silently: no citations, no test cas… | T-13 (planned) |
-- | E-30 | A symbolic link (file or directory) is encountered during descent under a --src/--tests directory element — Not fol… | T-13 (planned) |
-- | E-31 | A bold ID token appears in a table cell other than the first, or in a heading after other tokens — Not a declaratio… | T-55 (planned) |
-- | E-33 | A line contains speccheck:ignore, or a file's first three lines contain speccheck:ignore-file — The line yields no… | T-57 (planned) |
-- | E-34 | A .speccheck.json..tmp or .SPEC_CONFORMANCE_REPORT.md..tmp from a killed run exists under --out, which lies under a… | T-36, T-45 (planned) |
-- | E-35 | --judge llm and the --judge-budget deadline passes with edges not yet started, or the N% form's issued count is rea… | T-61, T-89 (planned) |
-- | E-37 | A tests[] entry whose case was not judged: judge disabled, or the ID not PASSING after C-05 step 4, or the ID RECOR… | T-34, T-35, T-77 (planned) |
-- | E-38 | Two or more Notes are produced in one run — Emitted in ascending Unicode code-point order of their full text, in bo… | T-34 (planned) |
-- | E-39 | --judge llm with stderr not a TTY (CI log, redirected file, pipe) under --progress auto; or --verbose DEBUG under a… | T-63 (planned) |
-- | E-40 | The judge stage is cut short while the indicator is displayed: a provider raises out of the stage (should not happe… | T-63 (planned) |
-- | E-42 | A .swift test file whose brace depth goes negative on some line or is non-zero at end of file (counted per C-03, ou… | T-67 (planned) |
-- | E-43 | A .swift function named test that is neither @Test-attributed nor a direct test method of an XCTestCase class (a me… | T-65, T-66, T-71 (planned) |
-- | E-44 | A declaring table row whose first cell begins with a bold ID form and continues with whitespace-separated decoratio… | T-70, T-71 (planned) |
-- | E-45 | Two Swift test cases with the same identifier and classname (overloads by parameter label) — A result with that joi… | T-68 (planned) |
-- | E-46 | A heading-declared ID whose statement (title plus section body) exceeds K-14; or whose section body is empty — the… | T-72 (planned) |
-- | E-47 | A heading-declared ID whose section body contains a deeper heading that itself declares an ID (#### E-09 … under ##… | T-72 (planned) |
-- | E-50 | The (recorded) marker on a declaration whose family is not T ( — R-07 (recorded) | T-77 (planned) |
-- | E-55 | A statement or an Affects cell names a retired id — The edge is recorded with retired: true (C-12); impact walks it… | T-79, T-80 (planned) |
-- | E-56 | A citation of family R/C/I/K/E has no test-case span to check for declaration — a "src"-kind citation, or a "test"-… | T-85, T-86 (planned) |
-- | E-57 | A related edge — a C-12 depends_on, both directions (R-38, D-28) — names a retired id, and a related field is built… | T-83 (planned) |
-- | E-59 | A C-17 triage request fails during --jev-pre-triage: non-200 status, transport error, timeout (SPECCHECK_JEV_TIMEOU… | T-89 (planned) |
-- | E-61 | --judge on explain — Carries check's contract exactly: the same provider, the same I-010 eligibility, the same C-06… | T-94 (planned) |
-- | I-003 | Exactly-once reporting. Every declared ID (retired included) appears exactly once in ids and exactly once in the Ma… | T-25, T-35 (planned) |
-- | I-006 | Network boundary. With --judge none/mock, no socket is opened for the lifetime of the process. | T-43 (planned) |
-- | I-007 | Secret and payload hygiene. The API key never appears in stdout, stderr, or either report. INFO never contains file… | T-40, T-41 (planned) |
-- | I-009 | Exit $\equiv$ report. exit_code in speccheck.json equals the process exit status, and both are computable from the… | T-39 (planned) |
-- | I-010 | One judge call per edge. The judge is invoked at most once per (test case, ID) edge per run, and only for edges who… | T-31, T-77 (planned) |
-- | I-012 | One scan per physical file (D-23). For the --src list, and separately for the --tests list, every physical file rea… | T-78 (planned) |
-- | I-013 | The direct set is exact; depth is a prefix (v1.13). In every impact report, an id is at depth 1 if and only if it i… | T-80 (planned) |
-- | I-014 | declared is a pure function of the source and test trees (v1.14). Citation.declared and every value derived from it… | T-85, T-88 (planned) |
-- | I-015 | Jev stays advisory (v1.15). For every edge, and under every combination of --jev-pre-triage and --judge-budget, the… | T-89 (planned) |
-- | I-016 | explain is additive and read-only (v1.17). explain writes no report file, changes no status, verdict, citation, met… | T-92, T-94 (planned) |
-- | I-017 | --help is inert (v1.18). speccheck --help, speccheck check --help, speccheck impact --help and speccheck explain --… | T-96 (planned) |
-- | K-02 | Files larger than 2 MiB (2,097,152 bytes) under --src/--tests are skipped with a Note (E-10); binary files (a 0x00… | T-13 (planned) |
-- | K-03 | Directories named .git, .hg, .svn, node_modules, __pycache__, .venv, venv, and any directory whose name starts with… | T-13 (planned) |
-- | K-04 | ID numbers are 1–3 digits; a token with 4+ digits is not an ID. | T-03 (planned) |
-- | K-05 | LLM judge timeout is SPECCHECK_JUDGE_TIMEOUT seconds (default 30) per edge, wall-clock, measured from the moment th… | T-33 (planned) |
-- | K-06 | Exactly one HTTP request per judged edge; no retries, no batching. Requests MAY be issued concurrently, at most --j… | T-33 (planned) |
-- | K-08 | Kernel performance, measured on the reference machine named in SPEC_BUILD_REPORT.md (CPU model, RAM, OS, Python bui… | T-51 (planned) |
-- | K-09 | JSON output is UTF-8, indent=2, ensure_ascii=False, sorted per C-07 (not alphabetically), trailing newline; Markdow… | T-34 (planned) |
-- | K-10 | --version prints a PEP 440 version equal to the package metadata version. | T-50 (planned) |
-- | K-11 | --max-unknown defaults to 0.2, accepts a decimal in [0, 1] (parsed as a Decimal from its literal text), and is comp… | T-59 (planned) |
-- | K-12 | --judge-budget has two forms (v1.15). SECONDS (default 0 = unlimited; integer 0..86400): bounds the wall-clock spen… | T-61, T-89, T-90 (planned) |
-- | K-14 | A statement (C-01: title, newline, section body) is at most 16,384 bytes of UTF-8. A longer statement is truncated… | T-72 (planned) |
-- | K-16 | --jev-pre-triage (boolean, default off; ignored unless --judge llm — under --judge none/mock no C-17 request is mad… | T-89, T-90 (planned) |
-- | R-01 | The checker MUST read a Markdown specification and extract every declared spec ID together with its family and stat… | T-01, T-05, T-46, T-72 (planned) |
-- | R-02 | The checker MUST recognize a declared ID as retired when its declaration is struck through (R-07), and MUST exclude… | T-04, T-25, T-46 (planned) |
-- | R-03 | The checker MUST scan every text file under each directory — and every file named directly — in the --src list, exc… | T-08, T-13, T-36, T-46, T-78 (planned) |
-- | R-04 | The checker MUST scan every text file under each directory — and every file named directly — in the --tests list, e… | T-09, T-10, T-11, T-12, T-36, T-56, T-46, T-65, T-66, T-67, T-78 (planned) |
-- | R-05 | When --results is given, the checker MUST read a JUnit XML file and join each <testcase> to an attributed test case… | T-15, T-16, T-52, T-58, T-46, T-68 (planned) |
-- | R-06 | The checker MUST assign every declared, non-retired ID exactly one deterministic status from the set in C-05, compu… | T-20, T-21, T-47, T-46 (planned) |
-- | R-07 | The checker MUST list every dangling citation: an ID token cited in a source or test file that is not declared in t… | T-23, T-46 (planned) |
-- | R-08 | The checker MUST list every stale citation: a citation of a retired ID. | T-23, T-46 (planned) |
-- | R-10 | When --judge is mock or llm, the checker MUST obtain, for each (test case, ID) edge whose ID is PASSING and whose t… | T-26, T-31, T-33, T-49, T-46 (planned) |
-- | R-12 | The checker MUST write a Markdown report (SPEC_CONFORMANCE_REPORT.md) laid out per C-08 in which every declared ID… | T-35, T-46 (planned) |
-- | R-13 | The checker MUST write a JSON report (speccheck.json) conforming to C-07 that contains everything the Markdown repo… | T-34, T-46 (planned) |
-- | R-16 | With --judge none or --judge mock, two runs over byte-identical inputs MUST produce byte-identical SPEC_CONFORMANCE… | T-36 (planned) |
-- | R-17 | The checker MUST implement the diagnostics contract in §5.3: silent by default; --verbose/--verbose INFO emit metad… | T-41, T-42 (planned) |
-- | R-18 | With --judge none or --judge mock, the process MUST perform no network I/O, and speccheck --self-check MUST verify… | T-43, T-60 (planned) |
-- | R-19 | The checker MUST treat all inputs as read-only; it MUST NOT create, modify, or delete any file outside --out, excep… | T-38, T-43, T-45 (planned) |
-- | R-20 | All paths in reports MUST be relative to --root (default: current directory) and use / as separator regardless of h… | T-34, T-36 (planned) |
-- | R-21 | On completion (exit 0 or 1) the checker MUST print exactly one summary line to stdout in the format of §5.1 and not… | T-44, T-59 (planned) |
-- | R-23 | The LLM judge MUST read its endpoint, model name, and API key from environment variables per C-09; a missing variab… | T-40, T-41 (planned) |
-- | R-24 | Every deterministic status (C-05 steps 1–4), every count, and every metric in the report MUST be reproducible by an… | T-37, T-48 (planned) |
-- | R-26 | The LLM judge MUST use exactly the request body, response path, and instruction text pinned in C-06 and C-10, and t… | T-33, T-54, T-74 (planned) |
-- | R-27 | The checker MUST honor the ignore markers in C-01: a line containing speccheck:ignore yields no citations, and a fi… | T-57 (planned) |
-- | R-29 | The summary line MUST be a single line of ASCII text written to stdout as UTF-8 regardless of locale, in the exact… | T-44 (planned) |
-- | R-30 | With --judge llm, the checker MUST display a progress indicator for the judge stage on stderr, in the format of C-1… | T-62, T-63 (planned) |
-- | R-32 | The declaration parser MUST declare an ID whose bold form is the beginning of a table row's first cell and is follo… | T-70, T-71 (planned) |
-- | R-33 | For an ID declared by a heading (C-01 (b)), the checker MUST use the heading text followed by the section body bene… | T-72, T-73, T-74 (planned) |
-- | R-34 | For every ASSERTS or EXECUTES_ONLY verdict the judge MUST name the clause of the statement it judged against, as a… | T-75, T-76, T-49 (planned) |
-- | R-36 | The checker MUST extract, from every declared id's statement, the ids it names, and record them as typed edges — de… | T-79 (planned) |
-- | R-37 | The checker MUST provide an impact subcommand that, given a changed set — the ids of --changed, or the ids whose de… | T-80, T-81, T-82 (planned) |
-- | R-38 | For every judged edge the checker MUST send the judge, with the statement, the related titles of the obligations th… | T-83, T-84 (planned) |
-- | R-39 | The checker MUST compute, for every citation of an in-scope R/C/I/K/E id inside an attributed (non-file-level) test… | T-85, T-86, T-88 (planned) |
-- | R-40 | The checker MUST accept a third subcommand, speccheck explain <ID>, that runs the same extract / attribute / map-re… | T-92, T-93, T-94 (planned) |
-- | R-41 | The checker MUST document its own interface: for every flag the parser defines on speccheck, speccheck check, specc… | T-95, T-96, T-97, T-98 (planned) |
-- | R-100 (v1.19) | With --proof PATHS, the checker MUST scan the named Lean files or directories with the lean adapter (C-20) and attr… | T-99 (planned) |
-- | C-20 (v1.19) | The lean adapter: declaration-head split, bold-span doc-comment tag extraction, directory recursion, unparseable/un… | T-99 (planned) |
-- | E-62 (v1.19) | An unreadable or non-Lean file in a --proof path — Recorded as a notes entry; MUST NOT be a usage error or change the… | T-99 (planned) |
-- | I-018 (v1.19) | Proof-input inertness: a check run without --proof/--proof-results writes speccheck.json and SPEC_CONFORMANCE_REPOR… | T-100 (planned) |
-- | R-101 (v1.23) | The checker MUST treat a TOKEN immediately preceded by <ns>: — where <ns> matches [A-Za-z][A-Za-z0-9_-] (no le… | T-107, T-108, T-112 (planned) |
-- | R-103 (v1.23) | check, impact and explain MUST accept --citation-map FILE; each resolving entry MUST yield one mapped test cit… | T-110, T-111 (planned) |
-- | R-104 (v1.22) | For every .ts, .tsx, .mts, .cts, .js, .jsx, .mjs and .cjs file in the --tests list the checker MUST delimit te… | T-113, T-114, T-115, T-116, T-117 (planned) |
-- | R-106 (v1.25) | check MUST accept a boolean --manifest flag (v1.25). With it, after both reports are written, check MUST write… | T-122, T-123, T-125 (planned) |
-- | R-107 (v1.25) | The checker MUST accept a fourth subcommand, speccheck verify --manifest FILE [--root DIR] [--verbose [LEVEL]]… | T-124, T-125 (planned) |
-- | R-108 (v1.25) | A declaring row or heading of an R, C, I, K or E id MAY carry the CONTROLS marker (C-01, C-27; v1.25). The che… | T-126 (planned) |
-- | R-110 (v1.26) | SPEC.md §0 MUST contain the Intended use block (v1.26), stating that the validated function is check, verify a… | T-130 (planned) |
-- | R-113 (v1.26) | qualify's operational qualification MUST run every case of the packaged catalog speccheck/_qualify/cases.json … | T-132 (planned) |
-- | R-114 (v1.26) | This repository MUST ship speccheck/_qualify/tool_risk.json, a C-28 risk file listing exactly the tool hazards… | T-135, T-48 (planned) |
-- | C-22 (v1.23) | Foreign reference and namespace (v1.23; R-101, R-102) | T-107, T-108, T-111 (planned) |
-- | C-23 (v1.23) | The citation map (v1.23; R-103) | T-110, T-111 (planned) |
-- | C-24 (v1.24) | The JavaScript/TypeScript adapter (v1.22; R-104; moved from C-03 in v1.24) | T-113, T-114, T-115, T-116, T-117 (planned) |
-- | C-25 (v1.25) | The provenance manifest (v1.25; R-106) | T-122, T-123 (planned) |
-- | C-28 (v1.25) | The risk file (v1.25; R-109) | T-127 (planned) |
-- | C-30 (v1.26) | The OQ case catalog and the tool hazards (v1.26; R-113, R-114) | T-132, T-135 (planned) |
-- | I-019 (v1.23) | Namespace and map inertness (v1.23). A check run given neither --namespace nor --citation-map, over inputs in … | T-109 (planned) |
-- | I-020 (v1.25) | Manifest determinism (v1.25). I-002 extends to speccheck.manifest.json: for --judge none and --judge mock, ide… | T-123 (planned) |
-- | I-021 (v1.25) | Provenance and hazard inertness (v1.25). A check run given neither --manifest nor --risk-file, over a specific… | T-128 (planned) |
-- | I-022 (v1.26) | qualify is read-only and offline (v1.26). A qualify run opens no socket, modifies no file of the installed pac… | T-132, T-134 (planned) |
-- | I-023 (v1.26) | Validation-pack inertness (v1.26). check, impact, explain, verify and --self-check write and print output byte… | T-134 (planned) |
-- | K-19 (v1.23) | Citation-map size (v1.23). A citation map (C-23) is at most 2 MiB, the K-02 file cap. Over it, E-70 (exit 3), … | T-111 (planned) |
-- | K-20 (v1.25) | Risk-file and hazard-id size (v1.25). A risk file (C-28) is at most 2 MiB, the K-02 cap; over it, E-84 (exit 3… | T-124, T-126, T-127 (planned) |
-- | E-66 (v1.21) | A table-declared row whose statement cell contains an odd number of unescaped $ outside backtick spans and whi… | T-106, T-120 (planned) |
-- | E-67 (v1.23) | A scanned --src/--tests file contains a foreign reference (C-22) — a TOKEN preceded by <ns>:, <ns> not the --n… | T-107 (planned) |
-- | E-68 (v1.23) | --namespace NS is given and a scanned file or a declared statement contains NS:ID | T-107, T-111 (planned) |
-- | E-69 (v1.23) | A declared statement or an Affects cell contains a foreign reference | T-108 (planned) |
-- | E-71 (v1.23) | A map entry's file and test match no scanned TestCase (the file was not scanned, or its test was renamed) | T-110, T-111 (planned) |
-- | E-72 (v1.23) | A map entry resolves (C-23) and no literal citation of the same (id, testcase) exists | T-110 (planned) |
-- | E-73 (v1.23) | A map entry resolves to a (id, testcase) already cited literally, or two entries name the same (id, testcase) | T-110 (planned) |
-- | E-74 (v1.22) | A JavaScript/TypeScript test file whose parentheses do not balance, or with an unterminated block comment, str… | T-114 (planned) |
-- | E-75 (v1.22) | An it/test call whose first argument is not a literal title (a variable, an interpolated template), or a descr… | T-114 (planned) |
-- | E-76 (v1.22) | A JavaScript/TypeScript case whose title carries each placeholders, and several results that fill them | T-116 (planned) |
-- | E-77 (v1.24) | A declared, non-retired id is the src or dst of no C-12 edge: no statement, row cell or Affects cell names it,… | T-121 (planned) |
-- | E-78 (v1.25) | A CONTROLS marker (C-27) on the declaration of a T id | T-126 (planned) |
-- | E-79 (v1.25) | With --risk-file, a CONTROLS marker names a hazard the file does not list | T-127 (planned) |
-- | E-80 (v1.25) | The text in the CONTROLS position (C-01) begins (controls: but does not match C-27's grammar: an empty list, a… | T-126 (planned) |
-- | E-81 (v1.25) | A hazard in C-27's set H has no non-retired control: it is listed in --risk-file and no marker names it, or ev… | T-126, T-127 (planned) |
-- | T-01 … T-137 | the §9 acceptance tests (137 rows, +T-104..T-137 v1.21..v1.26); each is the test that carries its own row | themselves (planned) |
--
-- The 137 `T-nn` acceptance tests themselves are the §9 inventory; each is its own carrier
-- (planned). A T id is never proven here: a T id's proof is a run, not a theorem.
--
-- ### Dual halves — proven in Lean, implementation half deferred
--
-- Each ID below is **also** a bold tag above: the theorem discharges its deterministic half, and
-- the §9 test named here is what will witness its implementation half when a build runs it
-- (planned). This is the spec-review-sanctioned dual state, not a re-classification.
--
-- | Spec ID | Implementation half carried by (planned) |
-- | --- | --- |
-- | C-01 | T-01, T-02, T-03, T-04, T-05, T-55, T-57, T-70, T-72, T-77, T-79 (planned) |
-- | C-04 | T-15, T-16, T-17, T-18, T-19, T-52, T-58, T-68 (planned) |
-- | C-05 | T-20, T-21, T-27, T-53, T-77 (planned) |
-- | C-06 | T-26, T-29, T-30, T-32, T-33, T-54, T-69, T-74, T-75, T-83, T-87 (planned) |
-- | C-07 | T-34, T-37, T-59, T-73, T-75, T-77, T-79, T-86, T-88, T-101 (planned) |
-- | C-11 | T-62 (planned) |
-- | C-13 | T-80, T-81 (planned) |
-- | C-18 | T-92, T-93, T-94 (planned) |
-- | E-01 | T-07 (planned) |
-- | E-02 | T-06 (planned) |
-- | E-03 | T-04 (planned) |
-- | E-05 | T-19 (planned) |
-- | E-06 | T-17 (planned) |
-- | E-09 | T-40, T-78 (planned) |
-- | E-14 | T-30, T-33 (planned) |
-- | E-15 | T-30 (planned) |
-- | E-16 | T-29 (planned) |
-- | E-17 | T-26 (planned) |
-- | E-18 | T-45 (planned) |
-- | E-19 | T-20, T-39 (planned) |
-- | E-21 | T-40 (planned) |
-- | E-24 | T-52 (planned) |
-- | E-25 | T-53 (planned) |
-- | E-26 | T-27, T-39 (planned) |
-- | E-32 | T-59, T-101 (planned) |
-- | E-36 | T-59 (planned) |
-- | E-41 | T-63, T-64 (planned) |
-- | E-48 | T-75 (planned) |
-- | E-49 | T-75 (planned) |
-- | E-51 | T-77 (planned) |
-- | E-52 | T-78 (planned) |
-- | E-53 | T-81 (planned) |
-- | E-54 | T-81 (planned) |
-- | E-58 | T-90 (planned) |
-- | E-60 | T-93 (planned) |
-- | I-001 | T-07, T-38, T-43, T-45, T-60, T-64 (planned) |
-- | I-002 | T-36 (planned) |
-- | I-004 | T-27, T-28 (planned) |
-- | I-005 | T-29, T-75 (planned) |
-- | I-008 | T-24 (planned) |
-- | I-011 | T-02 (planned) |
-- | K-01 | T-39, T-40, T-19, T-64 (planned) |
-- | K-07 | T-32 (planned) |
-- | K-13 | T-62 (planned) |
-- | K-15 | T-75 (planned) |
-- | R-09 | T-24, T-46 (planned) |
-- | R-11 | T-27, T-28, T-46 (planned) |
-- | R-14 | T-39, T-46 (planned) |
-- | R-15 | T-39, T-27, T-46, T-127 (planned) |
-- | R-22 | T-26, T-69, T-75 (planned) |
-- | R-25 | T-53 (planned) |
-- | R-28 | T-59, T-101 (planned) |
-- | R-31 | T-65, T-66, T-67, T-68, T-69, T-71 (planned) |
-- | R-35 | T-77 (planned) |
-- | C-21 (v1.19) | T-99 (planned) |
-- | K-17 (v1.19) | T-99 (planned) |
-- | E-63 (v1.19) | T-99 (planned) |
-- | K-18 (v1.20) | T-103 (planned) |
-- | E-64 (v1.20) | T-102 (planned) |
-- | R-102 (v1.23) | T-107, T-111 (planned) |
-- | R-105 (v1.24) | T-118 (planned) |
-- | R-109 (v1.25) | T-127 (planned) |
-- | R-111 (v1.26) | T-130, T-134, T-136 (planned) |
-- | R-112 (v1.26) | T-130, T-131, T-137 (planned) |
-- | R-115 (v1.26) | T-135 (planned) |
-- | C-26 (v1.25) | T-124 (planned) |
-- | C-27 (v1.25) | T-126, T-127, T-129 (planned) |
-- | C-29 (v1.26) | T-130, T-131 (planned) |
-- | C-31 (v1.26) | T-135 (planned) |
-- | E-65 (v1.19) | T-99 (planned) |
-- | E-70 (v1.23) | T-111 (planned) |
-- | E-82 (v1.25) | T-124 (planned) |
-- | E-83 (v1.25) | T-124 (planned) |
-- | E-84 (v1.25) | T-127 (planned) |
-- | E-85 (v1.25) | T-123, T-134 (planned) |
-- | E-86 (v1.26) | T-133 (planned) |
-- | E-87 (v1.26) | T-133 (planned) |
-- | E-88 (v1.26) | T-132 (planned) |
--
-- ### Excluded — the spec puts these out of scope by name
--
-- Neither proven nor deferred: the spec's own stated boundary (§0 Non-goals, §5.2). Not a missing
-- witness, and never a place to hide a `G-3a`.
--
-- | Out of scope | Where stated |
-- | --- | --- |
-- | No semantic analysis of source code (type inference, control flow, "does this function implement R-07") — by the kernel *or* the judge | §0 Non-goals |
-- | No test execution: the checker consumes a results file, never runs `pytest`/`go test` | §0 Non-goals |
-- | No spec-quality review (ambiguity, contradictions, missing sections) — that is `spec-review` | §0 Non-goals |
-- | No remediation: the checker reports, never edits the spec, code, or tests | §0 Non-goals |
-- | No multi-repository or multi-spec runs; `--against` reads a prior version of the same spec only | §0 Non-goals |
-- | No change semantics: an edge records that a statement names another id, nothing more | §0 Non-goals |
-- | No IDE integration, daemon mode, watch mode, or web UI | §0 Non-goals |
-- | No adapters other than Python, Swift and JavaScript/TypeScript (v1.22); other languages get file-level attribution | §0 Non-goals, O-2 |
-- | No risk management: hazard ids are labels owned by the user's ISO 14971 file; acceptability is never evaluated (v1.25) | §0 Non-goals |
-- | No signatures or attribution of records (v1.25) | §0 Non-goals |
-- | No validation on the user's behalf (v1.26) | §0 Non-goals |
-- | No graphical surface at all | §5.2, O-3 |

end SpeccheckSpec.Speccheck.Theorems