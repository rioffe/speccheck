/-
# `SpeccheckSpec.Speccheck.Theorems` — the proof

## What this proves

For the deterministic, enumerable part of `SPEC.md` v1.18, for **all inputs**, kernel-checked:

- **The status algorithm** (C-05): `statusOf` returns `RETIRED` for retired ids, `UNCITED` for a
  T id with source citations only (F-001/E-25), and only `PASSING`/`WEAKLY_PASSING` from the judge
  step; the judge step never fires for a RECORDED id (R-35/E-51), and it can only downgrade (I-004).
- **The validation cascade** (C-06): rules fire in the spec's order; a verdict coerced to `UNKNOWN`
  is recorded with an empty clause (E-49); `ASSERTS` requires an in-span evidence line and a
  located clause (E-16, E-48, I-005); every rationale is ≤ 280 characters (C-06 rule 8 / K-07).
- **The metrics** (C-07): every ratio is `null`-on-zero-denominator (I-008, R-09);
  `judge_strength` excludes RECORDED ids from its population (F-405); `judge_available` is
  vacuously true when no edge was eligible (E-36) and false when every call failed (E-14).
- **The exit map** (§5.4, R-14, R-15, R-28): the exit code is a pure function of the report facts
  plus `--strict`; the closed set is `{0,1,2,3}` (K-01); a usage fault exits `2` and a contract
  fault exits `3`, neither writing a report; `strict_judge_failure` is `unavailable`-first
  (Q-004); all four codes are reachable.
- **The progress arithmetic** (C-11): the bar is 20 cells with `k = ⌊20d/n⌋`, and `left` is
  undefined exactly while `d = 0`.
- **The K-15 matcher**: the prefix/infix facts, and the mock provider's clause is always located
  (R-22).
- **Coverage**: `outcome` is total over the enumerated input space *except* for the one silent case
  proved by `silentCaseExists` (finding F-501).

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

/-- **C-07, E-14** — when every C-06 call failed, `judge_available` is `false`. -/
theorem judgeAvailableAllFailed (c : JudgeCalls) (hm : c.mode ≠ .none)
    (hs : c.succeeded = 0) (hi : 0 < c.issued) (he : 0 < c.eligible) :
    judgeAvailable c = some false := by
  grind

/-- **C-07, E-36** — with no eligible edge, `judge_available` is vacuously `true`. -/
theorem judgeAvailableVacuous (c : JudgeCalls) (hm : c.mode ≠ .none) (he : c.eligible = 0) :
    judgeAvailable c = some true := by
  grind

/-- **C-07** — `judge_available` is `null` under `--judge none`, or in the eligible-but-unissued
configuration that finding F-502 records as under-determined. -/
theorem judgeAvailableNullCases (c : JudgeCalls) :
    judgeAvailable c = none →
      c.mode = .none ∨ (c.succeeded = 0 ∧ c.issued = 0 ∧ 0 < c.eligible) := by
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

/-- **F-501 (G-1, silent case)** — the `explain` configuration with no `--spec`: the synopsis makes
`--spec` optional for `explain` (`speccheck explain ID [--spec SPEC.md]`), the §5.1 flag table marks
`--spec` `Required.` for every subcommand, and no default is stated for `explain`. Read as optional,
the input has no stated outcome — the model returns `none`, and this theorem is the kernel-checked
witness. See `docs/reviews/SPEC_MODEL_FINDINGS.md` F-501. -/
theorem f501ExplainAbsentSpecSilent : outcome .explainAbsentSpec = none := rfl

/-- **F-501 (G-1)** — coverage is *not* total: `noSilence` is false, and
`f501ExplainAbsentSpecSilent` exhibits the one enumerated input that falsifies it. -/
theorem f501NoSilenceFails : ¬ (∀ i, (outcome i).isSome) := by
  intro h
  have := h .explainAbsentSpec
  simp [outcome] at this

/-- **F-502 (G-2, under-determined pin)** — `judge_available` on a run where eligible edges exist
but no C-06 call was issued: every edge budget-skipped by K-12 (`N%` with `N = 0`, or the `SECONDS`
deadline reached before the first request, E-35). C-07's "true when at least one judge call
succeeded OR no edge was eligible" does not apply, and "false only when every call failed" does not
either, because no call *was* made. The model returns `none`; this theorem is the witness. -/
theorem f502JudgeAvailableBudgetSilent :
    judgeAvailable { mode := .llm, eligible := 3, issued := 0, succeeded := 0 } = none := by
  decide

/-- **F-502 (G-2)** — the same gap is reachable from `--judge mock`. -/
theorem f502JudgeAvailableBudgetSilentMock :
    judgeAvailable { mode := .mock, eligible := 1, issued := 0, succeeded := 0 } = none := by
  decide

/-- **F-502 (G-2)** — the contrast cases C-07 *does* pin: every call failed gives `false`, and no
eligible edge gives `true`. The pair shows the gap is exactly the eligible-but-unissued cell. -/
theorem f502Contrast :
    judgeAvailable { mode := .llm, eligible := 3, issued := 3, succeeded := 0 } = some false ∧
    judgeAvailable { mode := .llm, eligible := 0, issued := 0, succeeded := 0 } = some true := by
  decide

/-- **F-502 (G-2)** — the consequence: a `--strict --judge llm` run whose eligible edges were all
budget-skipped and every status is `PASSING` exits `1` (the R-28 gate wants `judge_available =
true`), yet `strict_judge_failure` is `null` because neither R-28 reason fires. -/
theorem f502StrictJudgeFailureNull :
    exitOfCheck { factConforming with judgeLlm := true, judgeAvailable := none } true = exitNotConforming ∧
    strictJudgeFailure { factConforming with judgeLlm := true, judgeAvailable := none } true = none := by
  decide

/-- **F-503 (G-2, under-specified relation)** — when one run carries both a usage fault (exit `2`)
and an input-contract violation (exit `3`), §5.4's table and K-01 give no precedence. These two
orderings are both faithful to the table and disagree, which is the kernel-checked separating
witness; §3.1's process order supplies the answer only by narrative. -/
theorem f503ExitPrecedenceDiffer :
    ∃ usage contract : Bool,
      (if usage then exitUsage else if contract then exitContract else exitConforming) ≠
      (if contract then exitContract else if usage then exitUsage else exitConforming) :=
  ⟨true, true, by decide⟩

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
-- | T-01 … T-98 | the §9 acceptance tests (98 rows); each is the test that carries its own row | themselves (planned) |
--
-- The 98 `T-nn` acceptance tests themselves are the §9 inventory; each is its own carrier
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
-- | C-07 | T-34, T-37, T-59, T-73, T-75, T-77, T-79, T-86, T-88 (planned) |
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
-- | E-32 | T-59 (planned) |
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
-- | R-15 | T-39, T-27, T-46 (planned) |
-- | R-22 | T-26, T-69, T-75 (planned) |
-- | R-25 | T-53 (planned) |
-- | R-28 | T-59 (planned) |
-- | R-31 | T-65, T-66, T-67, T-68, T-69, T-71 (planned) |
-- | R-35 | T-77 (planned) |
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
-- | No adapters other than Python and Swift; other languages get file-level attribution | §0 Non-goals, O-2 |
-- | No graphical surface at all | §5.2, O-3 |

end SpeccheckSpec.Speccheck.Theorems