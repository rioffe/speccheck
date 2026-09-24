/-
# `SpeccheckProof.Speccheck.Theorems` — the proof

## What this proves

For the deterministic, enumerable part of `src/speccheck/*.py` (SPEC.md v1.18), for **all inputs**,
kernel-checked:

- **The status algorithm** (C-05, `graph.deterministic_status`/`graph.apply_verdicts`):
  `statusOf` returns `RETIRED` for retired ids, `UNCITED` for a T id with source citations only
  (F-001/E-25), and only `PASSING`/`WEAKLY_PASSING` from the judge step; the judge step never
  fires for a RECORDED id (R-35/E-51), and it can only downgrade (I-004).
- **The validation cascade** (C-06, `judge.validate`): rules fire in the spec's order; a verdict
  coerced to `UNKNOWN` is recorded with an empty clause (E-49); `ASSERTS` requires an in-span
  evidence line and a located clause (E-16, E-48, I-005); every rationale is ≤ 280 characters
  (C-06 rule 8 / K-07, `judge.clean_rationale`).
- **The metrics** (C-07, `graph.compute_metrics`): every ratio is `null`-on-zero-denominator
  (I-008, R-09); `judge_strength` excludes RECORDED ids from its population (F-405).
- **The exit map** (§5.4, R-14, R-15, R-28, E-19, `report.exit_code_for`/`report.strict_judge_failure`):
  the exit code is a pure function of the report facts plus `--strict`, **including the E-19
  all-`UNCITED` branch** that fires even without `--strict` — the one place this project's model
  corrects `proof_from_spec`'s spec-only version, after reading `report.py:82-97` directly; the
  closed set is `{0,1,2,3}` (K-01); a usage fault exits `2` and a contract fault exits `3`, neither
  writing a report; `strict_judge_failure` is `unavailable`-first (Q-004); all four codes are
  reachable.
- **The progress arithmetic** (C-11, `judge.progress_line`): the bar is 20 cells with
  `k = ⌊20d/n⌋`, and `left` is undefined exactly while `d = 0`.
- **The K-15 matcher** (`judge.locate_clause`): the prefix/infix facts, and the mock provider's
  clause is always located (R-22, `judge_mock.py:40`).

## What this does not prove

Lean proves **the model in `Model.lean`**, transcribed from `src/speccheck/*.py` by manual re-read
(the correspondence table in `Model.lean`'s header). Every requirement whose realization is the
filesystem, a network call, a clock, or a rendering step is out of Lean's reach and appears in the
deferral table at the foot of this file, against the `tests/test_NN_*.py` file that actually
exercises it — those tests exist and run today (`uv run python -m pytest tests -q`), unlike the
"planned" carriers this project's predecessor (`proof_from_spec/`, written before any
implementation existed) had to cite.

## The trust boundary

Lean proves **the model** — the pure functions in `Model.lean`. It cannot read a `.py` file, and
the correspondence between `src/speccheck/*.py` and those functions is **manual**: the
correspondence table in `Model.lean`'s header, function by function. The row theorems in
`section Rows` exist so that the source-to-model join is complete (every branch the model covers
has a checkable example), *not* because they prove anything.

## The tautology rule

`section Rows` is **transcription**: each theorem re-states the model's own definition for one
input, and its doc comment says so. Every theorem *outside* `section Rows` discharges a spec
sentence that is not the definition of the thing it is about — a claim quantified over the whole
input space, a cross-constant relation, or a reachability claim — and its doc comment names that
sentence.
-/
import SpeccheckProof.Speccheck.Spec
import SpeccheckProof.Speccheck.Model

namespace SpeccheckProof.Speccheck.Theorems

open SpeccheckProof.Speccheck.Spec
open SpeccheckProof.Speccheck.Model

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

/-- A baseline conforming report: no failing id, not all-`UNCITED`, everything passing, no
dangling/stale, judge off. -/
def factConforming : ReportFacts :=
  { anyInScopeFailing := false, allInScopeUncited := false, allInScopePassing := true,
    anyDangling := false, anyStale := false, judgeLlm := false, judgeAvailable := none,
    unknownRateExceeds := false }

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

/-! ## Rows — transcription of the source's branches (not evidence; see the tautology rule) -/

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

/-- **E-19** (transcription): every in-scope id `UNCITED` exits `1` even without `--strict` —
`report.exit_code_for`'s `by_status["UNCITED"] == in_scope` branch (`report.py:88-89`), the
branch this project's model adds over `proof_from_spec`'s spec-only version. -/
theorem row_exit_allUncited :
    exitOfCheck { factConforming with allInScopeUncited := true } false = exitNotConforming := by
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
configuration this spec-level statement leaves under-determined (see `Model.lean`'s note: the
actual `run_judge`/`available` computation resolves this same configuration to `true`, since a
budget-skipped edge is never counted in `calls_made`). -/
theorem judgeAvailableNullCases (c : JudgeCalls) :
    judgeAvailable c = none →
      c.mode = .none ∨ (c.succeeded = 0 ∧ c.issued = 0 ∧ 0 < c.eligible) := by
  grind

/-- **R-15, R-28, E-19** — with `--strict`, exit `0` implies no in-scope id is `FAILING`, not every
in-scope id is `UNCITED`, every in-scope id is `PASSING`, `dangling` and `stale` are empty, and the
R-28 judge gate holds. -/
theorem strictExitZeroImpliesAll (f : ReportFacts) (h : exitOfCheck f true = exitConforming) :
    f.anyInScopeFailing = false ∧ f.allInScopeUncited = false ∧
    f.allInScopePassing = true ∧ f.anyDangling = false ∧ f.anyStale = false ∧
      strictJudgeHolds f = true := by
  grind

/-- **E-19** — every in-scope id `UNCITED` exits `1` regardless of `--strict`: the branch fires
before the strict-only checks and is not gated on `strict`. -/
theorem allUncitedAlwaysExitOne (f : ReportFacts) (h : f.allInScopeUncited = true)
    (hf : f.anyInScopeFailing = false) (s : Bool) :
    exitOfCheck f s = exitNotConforming := by
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
not the definition of `mockClause`. Matches `judge_mock.py:40`. -/
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
There is nothing to prove and nothing that *could* differ — this is the typing fact behind R-16's
determinism claim for the modelled functions; §3.1's file-write ordering (the rest of I-002) is
process-level and deferred (`tests/test_08_golden.py`, T-36). -/
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

-- ## Closing: the deferral table
--
-- ### Deferred — out of Lean's reach, carried by the actual test suite
--
-- This repository has an implementation and a green acceptance suite (`uv run python -m pytest
-- tests -q`). The carrier column names the `tests/test_NN_*.py` file that exercises each
-- requirement's T id (every test cites its own T id in a docstring or comment, R-39/§9's own
-- rule; T-48 records that a `check --judge mock` run over this repository reports every
-- R/C/I/K/E/T id `PASSING`). Unlike `proof_from_spec`'s deferral table, nothing here is
-- "planned": these tests run in CI today. A requirement whose Lean half is proven *and* whose
-- process half is deferred appears twice — as a bold tag above and as a row here; that dual
-- state is the normal shape, not a conflict.
--
-- | Spec ID | Content (out of Lean's reach) | Carried by |
-- | --- | --- | --- |
-- | C-02 | SpecIndex | tests/test_01_extraction.py (T-01, T-06, T-72, T-77, T-79) |
-- | C-03 | Citation, TestCase, attribution | tests/test_02_attribution.py (T-09, T-10, T-13, T-14, T-56, T-65, T-66, T-67, T-78, T-85); tests/test_08_golden.py (T-36) |
-- | C-08 | Markdown report layout (SPEC_CONFORMANCE_REPORT.md) | tests/test_06_reports.py (T-35, T-73, T-75, T-77) |
-- | C-09 | LLM provider configuration | tests/test_05_judge.py (T-33); tests/test_07_cli.py (T-40) |
-- | C-10 | Judge instruction text (normative; F-004) | tests/test_05_judge.py (T-33, T-54, T-74, T-75, T-83); tests/test_09_self_application.py (T-87, recorded) |
-- | C-12 | Spec-internal edges (v1.13; R-36) | tests/test_10_edges.py (T-79) |
-- | C-14 | Declared vs. incidental citations (v1.14; R-39) | tests/test_02_attribution.py (T-85); tests/test_06_reports.py (T-86) |
-- | C-15 | declared in the judge request; the instruction text is advisory (v1.14; R-39) | tests/test_09_self_application.py (T-87, recorded) |
-- | C-16 | declared and declared_ratio in the JSON report (v1.14; R-39) | tests/test_06_reports.py (T-86, T-88) |
-- | C-17 | Jev triage provider (v1.15; K-16, I-015) | tests/test_05_judge.py (T-89, T-90) |
-- | C-19 | Help contract (v1.18; R-41) | tests/test_13_help.py (T-95, T-96, T-97, T-98) |
-- | E-04 | ID inside a fenced code block in SPEC.md is not a declaration | tests/test_01_extraction.py (T-05) |
-- | E-07 | Result <testcase> joins no attributed test case | tests/test_03_results.py (T-18) |
-- | E-08 | Test case cites an ID but has no result | tests/test_04_status.py (T-22) |
-- | E-10 | File > 2 MiB under a scan root | tests/test_02_attribution.py (T-13) |
-- | E-11 | A scanned file (or SPEC.md) is not valid UTF-8 | tests/test_02_attribution.py (T-13); tests/test_01_extraction.py (T-01) |
-- | E-12 | .py test file fails to parse | tests/test_02_attribution.py (T-11) |
-- | E-13 | Test citation lands in a file-level case | tests/test_02_attribution.py (T-10) |
-- | E-20 | Dangling citation that looks retired in code | tests/test_04_status.py (T-23) |
-- | E-22 | Test file cites the same ID on several lines of one case | tests/test_02_attribution.py (T-14) |
-- | E-23 | --spec/--results/report path lies under a scan root | tests/test_08_golden.py (T-36) |
-- | E-27 | A result's classname suffix-matches two test cases equally | tests/test_03_results.py (T-58) |
-- | E-28 | A test* method of an unrecognized class | tests/test_02_attribution.py (T-56) |
-- | E-29 | A file with a 0x00 byte in its first 8192 bytes | tests/test_02_attribution.py (T-13) |
-- | E-30 | A symlink encountered during descent | tests/test_02_attribution.py (T-13) |
-- | E-31 | A bold ID token outside the first-cell/first-token form | tests/test_01_extraction.py (T-55) |
-- | E-33 | speccheck:ignore / speccheck:ignore-file | tests/test_01_extraction.py (T-57) |
-- | E-34 | A leftover .tmp file under --out | tests/test_08_golden.py (T-36, T-45) |
-- | E-35 | The --judge-budget deadline passes with edges not yet started | tests/test_07_cli.py (T-61); tests/test_05_judge.py (T-89) |
-- | E-37 | A tests[] entry whose case was not judged | tests/test_06_reports.py (T-34, T-35, T-77) |
-- | E-38 | Two or more Notes in one run | tests/test_06_reports.py (T-34) |
-- | E-39 | No progress bytes under a suppression condition | tests/test_07_cli.py (T-63) |
-- | E-40 | The judge stage cut short while the indicator is displayed | tests/test_07_cli.py (T-63) |
-- | E-42 | A .swift file whose brace depth is unbalanced | tests/test_02_attribution.py (T-67) |
-- | E-43 | A .swift test* function neither @Test nor a direct XCTestCase method | tests/test_02_attribution.py (T-65, T-66) |
-- | E-44 | A declaring row with whitespace-separated decoration | tests/test_01_extraction.py (T-70) |
-- | E-45 | Two Swift test cases with the same identifier and classname | tests/test_03_results.py (T-68) |
-- | E-46 | A heading-declared ID's statement exceeds K-14, or has an empty body | tests/test_01_extraction.py (T-72) |
-- | E-47 | A heading-declared ID whose body contains a deeper declaring heading | tests/test_01_extraction.py (T-72) |
-- | E-50 | The *(recorded)* marker on a non-T declaration | tests/test_04_status.py (T-77) |
-- | E-55 | A statement or Affects cell names a retired id | tests/test_10_edges.py (T-79); tests/test_11_impact.py (T-80) |
-- | E-56 | A citation with no test-case span to check for declaration | tests/test_02_attribution.py (T-85); tests/test_06_reports.py (T-86) |
-- | E-57 | A related edge names a retired id | tests/test_05_judge.py (T-83) |
-- | E-59 | A C-17 triage request fails during --jev-pre-triage | tests/test_05_judge.py (T-89) |
-- | E-61 | --judge on explain | tests/test_12_explain.py (T-94, recorded) |
-- | I-003 | Exactly-once reporting | tests/test_04_status.py (T-25); tests/test_06_reports.py (T-35) |
-- | I-006 | Network boundary (no socket under --judge none/mock) | tests/test_07_cli.py (T-43) |
-- | I-007 | Secret and payload hygiene | tests/test_07_cli.py (T-40, T-41) |
-- | I-009 | Exit ≡ report | tests/test_07_cli.py (T-39) |
-- | I-010 | One judge call per edge | tests/test_05_judge.py (T-31); tests/test_04_status.py (T-77) |
-- | I-012 | One scan per physical file (D-23) | tests/test_07_cli.py (T-78) |
-- | I-013 | The direct set is exact; depth is a prefix | tests/test_11_impact.py (T-80) |
-- | I-014 | declared is a pure function of the source/test trees | tests/test_02_attribution.py (T-85); tests/test_06_reports.py (T-88) |
-- | I-015 | Jev stays advisory | tests/test_05_judge.py (T-89) |
-- | I-016 | explain is additive and read-only | tests/test_12_explain.py (T-92, T-94) |
-- | I-017 | --help is inert | tests/test_13_help.py (T-96) |
-- | K-02 | 2 MiB / binary file filters | tests/test_02_attribution.py (T-13) |
-- | K-03 | Never-descend directories, symlinks | tests/test_02_attribution.py (T-13) |
-- | K-04 | ID numbers are 1-3 digits | tests/test_01_extraction.py (T-03) |
-- | K-05 | LLM judge timeout | tests/test_05_judge.py (T-33) |
-- | K-06 | One HTTP request per judged edge; concurrency | tests/test_05_judge.py (T-33) |
-- | K-08 | Kernel performance | tests/test_09_self_application.py (T-51, recorded) |
-- | K-09 | JSON/Markdown output formatting | tests/test_06_reports.py (T-34) |
-- | K-10 | --version | tests/test_07_cli.py (T-50) |
-- | K-11 | --max-unknown default and comparison | tests/test_07_cli.py (T-59) |
-- | K-12 | --judge-budget SECONDS/N% forms | tests/test_07_cli.py (T-61); tests/test_05_judge.py (T-89, T-90) |
-- | K-14 | Statement byte cap and truncation marker | tests/test_01_extraction.py (T-72) |
-- | K-16 | --jev-pre-triage ordering | tests/test_05_judge.py (T-89, T-90) |
-- | R-01 | Declaration extraction | tests/test_01_extraction.py (T-01, T-05, T-72); tests/test_08_golden.py (T-46) |
-- | R-02 | Retired flag, denominator exclusion | tests/test_01_extraction.py (T-04); tests/test_04_status.py (T-25) |
-- | R-03 | Source scan, PATHS parsing, exclusions | tests/test_02_attribution.py (T-08, T-13); tests/test_07_cli.py (T-78) |
-- | R-04 | Test scan, attribution, adapters | tests/test_02_attribution.py (T-09, T-10, T-11, T-12, T-56, T-65, T-66, T-67); tests/test_07_cli.py (T-78) |
-- | R-05 | JUnit XML read and join | tests/test_03_results.py (T-15, T-16, T-52, T-58, T-68) |
-- | R-06 | C-05 steps 1-4 | tests/test_04_status.py (T-20, T-21, T-47) |
-- | R-07 | Dangling citations | tests/test_04_status.py (T-23) |
-- | R-08 | Stale citations | tests/test_04_status.py (T-23) |
-- | R-10 | Judge obtained for PASSING+passed edges | tests/test_05_judge.py (T-26, T-31, T-33); tests/test_09_self_application.py (T-49, recorded) |
-- | R-12 | Markdown report written | tests/test_06_reports.py (T-35) |
-- | R-13 | JSON report written | tests/test_06_reports.py (T-34) |
-- | R-16 | Byte-identical reports (the file-write half) | tests/test_08_golden.py (T-36) |
-- | R-17 | Diagnostics contract | tests/test_07_cli.py (T-41, T-42) |
-- | R-18 | No network I/O under --judge none/mock | tests/test_07_cli.py (T-43); tests/test_09_self_application.py (T-60) |
-- | R-19 | Read-only inputs | tests/test_07_cli.py (T-38, T-43, T-45) |
-- | R-20 | Relative, /-separated report paths | tests/test_06_reports.py (T-34); tests/test_08_golden.py (T-36) |
-- | R-21 | One summary line on stdout | tests/test_07_cli.py (T-44, T-59) |
-- | R-23 | LLM judge reads env vars; key redacted | tests/test_07_cli.py (T-40, T-41) |
-- | R-24 | Every metric reproducible from the report's own evidence | tests/test_07_cli.py (T-37); tests/test_09_self_application.py (T-48, recorded) |
-- | R-26 | LLM request body / instruction text / hash | tests/test_05_judge.py (T-33, T-54, T-74) |
-- | R-27 | speccheck:ignore markers | tests/test_01_extraction.py (T-57) |
-- | R-29 | ASCII summary line | tests/test_07_cli.py (T-44) |
-- | R-30 | Judge progress indicator | tests/test_07_cli.py (T-62, T-63) |
-- | R-32 | Decorated table-row declarations | tests/test_01_extraction.py (T-70) |
-- | R-33 | Heading-declared statement (title + body) | tests/test_01_extraction.py (T-72, T-73); tests/test_05_judge.py (T-74) |
-- | R-34 | Clause grounding | tests/test_05_judge.py (T-75); tests/test_09_self_application.py (T-49, recorded) |
-- | R-36 | Edge extraction | tests/test_10_edges.py (T-79) |
-- | R-37 | impact subcommand | tests/test_11_impact.py (T-80, T-81) |
-- | R-38 | related neighbourhood in the judge request | tests/test_05_judge.py (T-83) |
-- | R-39 | DECLARED/INCIDENTAL computation | tests/test_02_attribution.py (T-85); tests/test_06_reports.py (T-86, T-88) |
-- | R-40 | explain subcommand | tests/test_12_explain.py (T-92, T-93, T-94) |
-- | R-41 | --help documents the interface | tests/test_13_help.py (T-95, T-96, T-97, T-98) |
-- | T-01 … T-98 | the §9 acceptance tests (98 rows, per tests/test_01..13_*.py) | themselves — `uv run python -m pytest tests -q` |
--
-- The 98 `T-nn` acceptance tests are the §9 inventory; each is its own carrier — a T id is never
-- proven here, since a T id's proof is a run, not a theorem.
--
-- ### Dual halves — proven in Lean, implementation half carried by a real test
--
-- Each ID below is **also** a bold tag above: the theorem discharges its deterministic half, and
-- the test named here witnesses its implementation half (already run, not planned).
--
-- | Spec ID | Implementation half carried by |
-- | --- | --- |
-- | C-01 | tests/test_01_extraction.py (T-01, T-02, T-03, T-04, T-05, T-55, T-57, T-70, T-72, T-77, T-79) |
-- | C-04 | tests/test_03_results.py (T-15, T-16, T-17, T-18, T-19, T-52, T-58, T-68) |
-- | C-05 | tests/test_04_status.py (T-20, T-21, T-27, T-53, T-77) |
-- | C-06 | tests/test_05_judge.py (T-26, T-29, T-30, T-32, T-33, T-54, T-69, T-74, T-75, T-83, T-87) |
-- | C-07 | tests/test_06_reports.py (T-34, T-37, T-59, T-73, T-75, T-77, T-79, T-86, T-88) |
-- | C-11 | tests/test_07_cli.py (T-62) |
-- | C-13 | tests/test_11_impact.py (T-80, T-81) |
-- | C-18 | tests/test_12_explain.py (T-92, T-93, T-94) |
-- | E-01 | tests/test_01_extraction.py (T-07) |
-- | E-02 | tests/test_01_extraction.py (T-06) |
-- | E-03 | tests/test_01_extraction.py (T-04) |
-- | E-05 | tests/test_03_results.py (T-19) |
-- | E-06 | tests/test_03_results.py (T-17) |
-- | E-09 | tests/test_07_cli.py (T-40, T-78) |
-- | E-14 | tests/test_05_judge.py (T-30, T-33) |
-- | E-15 | tests/test_05_judge.py (T-30) |
-- | E-16 | tests/test_05_judge.py (T-29) |
-- | E-17 | tests/test_05_judge.py (T-26) |
-- | E-18 | tests/test_07_cli.py (T-45) |
-- | E-19 | tests/test_04_status.py (T-20); tests/test_07_cli.py (T-39) |
-- | E-21 | tests/test_07_cli.py (T-40) |
-- | E-24 | tests/test_03_results.py (T-52) |
-- | E-25 | tests/test_04_status.py (T-53) |
-- | E-26 | tests/test_05_judge.py (T-27); tests/test_07_cli.py (T-39) |
-- | E-32 | tests/test_07_cli.py (T-59) |
-- | E-36 | tests/test_07_cli.py (T-59) |
-- | E-41 | tests/test_07_cli.py (T-63, T-64) |
-- | E-48 | tests/test_05_judge.py (T-75) |
-- | E-49 | tests/test_05_judge.py (T-75) |
-- | E-51 | tests/test_04_status.py (T-77) |
-- | E-52 | tests/test_07_cli.py (T-78) |
-- | E-53 | tests/test_11_impact.py (T-81) |
-- | E-54 | tests/test_11_impact.py (T-81) |
-- | E-58 | tests/test_07_cli.py (T-90) |
-- | E-60 | tests/test_12_explain.py (T-93) |
-- | I-001 | tests/test_01_extraction.py (T-07); tests/test_07_cli.py (T-38, T-43, T-45); tests/test_09_self_application.py (T-60) |
-- | I-002 | tests/test_08_golden.py (T-36) |
-- | I-004 | tests/test_05_judge.py (T-27, T-28) |
-- | I-005 | tests/test_05_judge.py (T-29, T-75) |
-- | I-008 | tests/test_04_status.py (T-24) |
-- | I-011 | tests/test_01_extraction.py (T-02) |
-- | K-01 | tests/test_07_cli.py (T-39, T-40, T-64); tests/test_03_results.py (T-19) |
-- | K-07 | tests/test_05_judge.py (T-32) |
-- | K-13 | tests/test_07_cli.py (T-62) |
-- | K-15 | tests/test_05_judge.py (T-75) |
-- | R-09 | tests/test_04_status.py (T-24); tests/test_08_golden.py (T-46) |
-- | R-11 | tests/test_05_judge.py (T-27, T-28); tests/test_08_golden.py (T-46) |
-- | R-14 | tests/test_07_cli.py (T-39); tests/test_08_golden.py (T-46) |
-- | R-15 | tests/test_07_cli.py (T-39); tests/test_05_judge.py (T-27); tests/test_08_golden.py (T-46) |
-- | R-22 | tests/test_05_judge.py (T-26, T-69, T-75) |
-- | R-25 | tests/test_04_status.py (T-53) |
-- | R-28 | tests/test_07_cli.py (T-59) |
-- | R-31 | tests/test_02_attribution.py (T-65, T-66, T-67); tests/test_03_results.py (T-68); tests/test_05_judge.py (T-69) |
-- | R-35 | tests/test_04_status.py (T-77) |
--
-- ### Excluded — the spec puts these out of scope by name
--
-- Neither proven nor deferred: the spec's own stated boundary (§0 Non-goals, §5.2).
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

end SpeccheckProof.Speccheck.Theorems
