/-
# `SpeccheckProof.Speccheck.Model` — the transcription

The deterministic core of `src/speccheck/*.py` (the built `speccheck` CLI, `SPEC.md` v1.18) as
pure, total Lean functions. This file is leg 1 of the trust boundary (see the project README) and
the correspondence table below is **manual**: Lean cannot read a `.py` file, so the claim "the
model is a faithful transcription of the source" is checked here, function by function, by a human
re-read — not proven by `lake build`. The `section Rows` theorems in `Theorems.lean` make that
re-read *checkable* (they pin one input/output pair per branch), not proof of correspondence.

This project descends from `../proof_from_spec/`, which modelled `SPEC.md`'s own claims about
itself before any implementation existed. Cross-checking that model against the actual source
below found it matches almost line for line — with one real discrepancy, fixed here: the spec's
general §5.4 prose for exit `0` ("no in-scope ID is `FAILING`; and if `--strict`, ...") does not
mention the all-`UNCITED` case, but `report.exit_code_for` has an explicit extra branch for it
(sourced from the E-19 edge-case row, not the general rule), and `ReportFacts`/`exitOfCheck` below
now carry that branch. The spec-model project's `exitOfCheck` did not have it.

## Correspondence table (model element → source)

| Model element | Source | Note |
| --- | --- | --- |
| `Family`, `letterFamily`, `Family.letter/order/padWidth` | `extract.py:21-50` (`FAMILY_ORDER`, `normalize_id`, `family_rank`) | six families; `D` handled separately |
| `IdKey`, `normalizeDisplay`, I-011 | `extract.py:43-46` (`normalize_id`) | the model's identity *is* the normalized key |
| `stripFromFirst`, `joinNameL`/`joinName` | `results.py:28-36` (`RawResult.join_name`) | two-step `[`/`(` strip, transcribed verbatim |
| `Outcome`, `Outcome.rank`, `worst`, `worstOf` | `results.py:14,59-60` (`_WORST_ORDER`, `worst`) | `error > failed > skipped > passed` |
| `Status`, `Evidence`, `statusOf`, `step4`, `step5` | `graph.py:78-97` (`deterministic_status`) and `graph.py:178-198` (`apply_verdicts`) | the whole C-05 algorithm; `Evidence` is the exact set of facts those two functions read |
| `statusOf`'s `.T` branch (F-001, E-25) | `graph.py:85-89` (`if spec.family == "T": return "UNCITED"`) | source citations are evidence only for family T |
| `step5`'s `!recorded` conjunct (R-35, E-51) | `graph.py:182` (`if rec.status != "PASSING" or rec.spec.recorded: continue`) | a recorded id is exempt from the judge and nothing else |
| `RawAnswer`, `coerce` | `judge.py:187-214` (`validate`) | rule 1 (provider failure) lives one level up at `judge.py:217-232` (`judge_edge`)'s `except` clauses; `coerce` starts at rule 2, exactly as `validate`'s own doc comment says |
| `truncateRationale` | `judge.py:147-152` (`clean_rationale`) | truncate to 277 + `...` |
| `locatedL`/`locatedN`, `k15Normalize`, `infixOf`, `prefixEq` | `judge.py:162-184` (`locate_clause`) | collapse, trim, cut 280; ≥ 12 or the short-statement rule |
| `mockClause` | `judge_mock.py:40` (`" ".join(req.statement.split())[:280]`) | byte-for-byte the same expression as `mockClause` |
| `ratioUnits`, `roundHalfEven` | `graph.py:28-38` (`ratio`) | `Decimal` division at 28-digit precision, quantized 4 places half-even; the Lean version is the same rounding at fixed-point scale `10000` |
| `conformanceUnits`, `judgeStrengthUnits`, `declaredRatioUnits`, `unknownRateUnits` | `graph.py:218-268` (`compute_metrics`) | one `ratio(...)` call per metric, same numerator/denominator pairs |
| `ratioUnits`'s `den = 0 → none` (I-008) | `graph.py:35-36` (`if denominator == 0: return None`) | |
| `judgeAvailable` | not yet in `graph.py`/`report.py`: no `judge_available` computation was found in the read source (this repository's `judge.py`/`graph.py` compute `JudgeRun.available` at `judge.py:444` — `calls_made == 0 or calls_ok > 0` — a **different** but equivalent shape). See the note below the table. | |
| `ReportFacts`, `exitOfCheck` (fixed) | `report.py:82-97` (`exit_code_for`) | now includes the E-19 all-`UNCITED` branch (`report.py:88-89`), absent from the spec-model project's version |
| `strictJudgeFailure` | `report.py:70-79` (`strict_judge_failure`) | `unavailable` takes precedence (Q-004) |
| `barCells`, `bar`, `remainingSeconds` | `judge.py:244-255` (`_mmss`, `progress_line`) | `k = ⌊20d/n⌋`; `left = t(n−d)/d` |
| `Subcommand`, `Fault`, `Input`, `Result`, `outcome` | `cli.py` (argument parsing and exit dispatch — not individually line-mapped; the exit/usage split is `report.py:5.4`'s table, realized across `cli.py`'s per-flag validation) | one `Fault` constructor per usage/contract row |
| `Input.interrupt` (E-41) | `judge.py:115-118` (`JudgeInterrupted`), `cli.py`'s top-level exception handling | exit 3, no report survives |

**`judge_available` — a genuine model/source gap, recorded rather than papered over.** The read
source computes `JudgeRun.available` in `run_judge` (`judge.py:433-444`) as `calls_made == 0 or
calls_ok > 0` over *issued* calls, budget-skips excluded (`verdict.call_made` is `false` for a
K-12-skipped edge, `judge.py:389,397`). `graph.eligible_edges` (`graph.py:165-175`) separately
computes the *eligible* count. The two are joined by `report.build_report`'s caller, not by a
single function this project read in full — `report.py:129-234` takes `judge_available` as an
already-computed `ReportInputs` field rather than deriving it. `judgeAvailable`/`JudgeCalls` below
transcribe the *spec's* E-14/E-36 statement (the same shape `proof_from_spec` used), not a
specific source function; this is why the `judgeAvailable` theorems below are tagged as proving
the spec's rule over the `JudgeCalls` abstraction, and the join to `JudgeRun.available` is left in
the deferral table (T-59, T-89) rather than claimed as a transcription.

Deliberately not modelled, with the reason — the parts of `src/speccheck/*.py` that are a text
transformer, a filesystem walk, XML/network I/O, or a renderer; Lean operates on pure values:

| Source area | Why not modelled here |
| --- | --- |
| `extract.py`'s declaration scan (`SpecId`/`SpecIndex` construction, fence/heading/table parsing, K-14 truncation) | a text transformer over a document; the *bounds* are `k14Cap` and the facts in `Spec.lean`; the parser is carried by `tests/test_01_extraction.py` |
| `attribute.py`, `swift.py` (Python/Swift test-case delimiting, PATHS scanning, K-02/K-03 filters, binary/symlink handling) | filesystem traversal and language-specific line scanning; the *filters* are pinned as constants (`k02*`, `k03*`); carried by `tests/test_02_attribution.py` |
| `results.py`'s `parse_junit`, `join_results` (beyond `join_name`/`worst`, which *are* modelled) | XML parsing and the suffix-match/tie-break search are not Lean values in this project; carried by `tests/test_03_results.py` |
| `judge_llm.py`, `jev.py`, C-09/C-10/C-17 wire format, HTTP | network + bytes; carried by `tests/test_05_judge.py`, `tests/test_13_help.py` |
| `impact.py` (C-12 edge extraction, C-13 BFS walk) | the edge *kinds* and their order are constants here; the walk is carried by `tests/test_10_edges.py`, `tests/test_11_impact.py` |
| `report.py`'s Markdown/JSON rendering (C-08, C-16, C-19 byte-exact output), `explain.py` (C-18) | rendering from modelled facts; carried by `tests/test_06_reports.py`, `tests/test_12_explain.py` |
| `cli.py`'s argument parsing and `--help` text (C-19) | argparse configuration and string rendering; carried by `tests/test_07_cli.py`, `tests/test_13_help.py` |
| §3.1 lifecycle (write/rename/cleanup ordering), I-001 | process-level file I/O; carried by `tests/test_07_cli.py`, `tests/test_08_golden.py` |
| §9 tests, K-08 performance, K-05/K-06/K-12 timing | empirical / timing budgets; `tests/test_09_self_application.py` (recorded, non-gating) and the deferral table below |
-/
import SpeccheckProof.Speccheck.Spec

namespace SpeccheckProof.Speccheck.Model

open SpeccheckProof.Speccheck.Spec

/-! ## C-01 — families and normalized identity -/

/-- C-01 — `FAMILY := "R" | "C" | "I" | "K" | "E" | "T"`. The six conformance families; `D-nn`
is declaration-only and is not a member. -/
inductive Family where
  | R | C | I | K | E | T
  deriving DecidableEq, Repr

/-- C-01 — the family letter. -/
def Family.letter : Family → Char
  | .R => 'R' | .C => 'C' | .I => 'I' | .K => 'K' | .E => 'E' | .T => 'T'

/-- C-01 — the zero-padding width: "zero-padded to 2 digits for R/C/K/E/T, 3 digits for I". -/
def Family.padWidth : Family → Nat
  | .I => 3 | _ => 2

/-- C-12, C-07 — the total id order `R, C, I, K, E, T, D` (family order, then number). -/
def Family.order : Family → Nat
  | .R => 0 | .C => 1 | .I => 2 | .K => 3 | .E => 4 | .T => 5

/-- C-01 — the inverse of `Family.letter`. -/
def letterFamily : Char → Option Family
  | 'R' => some .R | 'C' => some .C | 'I' => some .I
  | 'K' => some .K | 'E' => some .E | 'T' => some .T
  | _ => none

/-- C-01, I-011 — the normalized identity of an ID: family plus number. "ID numbers are compared
numerically: R-7 and R-07 and R-007 are the same ID." The model's identity *is* this key, so
normalization is injective by construction. -/
structure IdKey where
  family : Family
  number : Nat
  deriving DecidableEq, Repr

/-- C-01 — zero-pad a decimal string on the left to `w` characters. -/
def padLeft (w : Nat) (s : String) : String :=
  if s.length < w then String.ofList (List.replicate (w - s.length) '0') ++ s else s

/-- C-01 — the normalized form used everywhere in output: `FAMILY "-" zero-padded to 2 digits
for R/C/K/E/T, 3 digits for I`. Transcribes `extract.normalize_id` (`extract.py:43-46`). -/
def normalizeDisplay (k : IdKey) : String :=
  String.singleton k.family.letter ++ "-" ++ padLeft k.family.padWidth (toString k.number)

/-- C-12 — the C-12 total order key: family order then number. -/
def IdKey.orderKey (k : IdKey) : Nat × Nat := (k.family.order, k.number)

/-! ## C-04 — the JUnit join -/

/-- C-04 — `join_name` step 1 and step 2 share one rule: "if it ends with `<close>` and contains
`<open>`, everything from the FIRST `<open>` to the end is removed, whatever it contains".
Transcribes `RawResult.join_name`'s two `if name.endswith(...) and "..." in name:` checks
(`results.py:32-35`). -/
def stripFromFirst (op cl : Char) (cs : List Char) : List Char :=
  if cs.getLast? = some cl ∧ cs.any (· = op) then cs.takeWhile (· ≠ op) else cs

/-- C-04 (F-005, F-101, R-31, D-19) — the two-step `join_name`: strip from the first `[`, then
from the first `(`. Transcribes `results.py:28-36` in order (bracket strip first, paren strip
on the result). -/
def joinNameL (cs : List Char) : List Char :=
  stripFromFirst '(' ')' (stripFromFirst '[' ']' cs)

/-- C-04 — `join_name` on the `String` a `<testcase name>` carries. -/
def joinName (s : String) : String := String.ofList (joinNameL s.toList)

/-- C-04, E-06, E-24 — the four JUnit outcomes. -/
inductive Outcome where
  | passed | skipped | failed | error
  deriving DecidableEq, Repr

/-- C-04 — the worst-first rank `error > failed > skipped > passed`. Transcribes
`results._WORST_ORDER` (`results.py:14`). -/
def Outcome.rank : Outcome → Nat
  | .passed => 0 | .skipped => 1 | .failed => 2 | .error => 3

/-- C-04 (E-06, E-24) — the case's single outcome is the worst of them. Transcribes
`results.worst` (`results.py:59-60`: `max(outcomes, key=lambda o: _WORST_ORDER[o])`). -/
def worst (a b : Outcome) : Outcome := if a.rank ≤ b.rank then b else a

/-- C-04 (E-06, E-24) — worst-of a list; `passed` is the identity of `worst`. Transcribes
`join_results`'s fold `entry.outcome = worst([r.outcome for r in entry.results])`
(`results.py:149`). -/
def worstOf (l : List Outcome) : Outcome := l.foldl (fun acc o => worst acc o) .passed

/-! ## K-15 — the located-clause matcher -/

/-- K-15 — whitespace, per the spec's "every run of whitespace". -/
def isWs (c : Char) : Bool := c = ' ' ∨ c = '\t' ∨ c = '\n' ∨ c = '\r'

/-- K-15 — collapse every run of whitespace to one space. Transcribes `judge.collapse_ws`
(`judge.py:166-167`: `" ".join(text.split())`). -/
def collapseWs (cs : List Char) : List Char := go false cs
where
  go (prevWs : Bool) : List Char → List Char
    | [] => []
    | c :: cs =>
      if isWs c then (if prevWs then go true cs else ' ' :: go true cs) else c :: go false cs

/-- K-15 — the clause's normalization: collapse, trim, then cut to the first `k15Cut`
characters. Transcribes `judge.locate_clause`'s `collapse_ws(clause)[:CLAUSE_MAX]`
(`judge.py:179`) — Python's `str.split()`/`" ".join()` already trims, matched here by the
`collapseWs` pass alone (no separate trim is needed once whitespace runs are collapsed to
single interior spaces and leading/trailing runs collapse to nothing under `split`). -/
def k15Normalize (clause : List Char) : List Char :=
  ((collapseWs clause).reverse.dropWhile isWs).reverse.take k15Cut

/-- K-15 — `a` is a prefix of `b`, decidable. -/
def prefixEq : List Char → List Char → Bool
  | [], _ => true
  | _ :: _, [] => false
  | x :: xs, y :: ys => decide (x = y) && prefixEq xs ys

/-- K-15 — the suffixes of a list, `b` itself first (Lean core has no `List.tails`). -/
def suffixes : List Char → List (List Char)
  | [] => [[]]
  | c :: cs => (c :: cs) :: suffixes cs

/-- K-15 — `a` occurs as a (case-sensitive) contiguous substring of `b`. Transcribes Python's
`in` operator as used at `judge.py:182` (`cut in stmt`). -/
def infixOf (a b : List Char) : Bool := (suffixes b).any (prefixEq a)

/-- K-15 — the matcher, given the clause already normalized by `k15Normalize`: it is located
when it is at least `k15Min` characters and a substring of the statement, or the statement is
shorter than `k15Min` and the clause equals it. Transcribes `judge.locate_clause`
(`judge.py:170-184`) exactly: `stmt = collapse_ws(statement)`, `cut = collapse_ws(clause)[:280]`,
then the two branches at `judge.py:180-183`. -/
def locatedN (nc statement : List Char) : Bool :=
  (decide (k15Min ≤ nc.length) && infixOf nc (collapseWs statement)) ||
    (decide ((collapseWs statement).length < k15Min) && decide (nc = collapseWs statement))

/-- K-15 — the full located check on a raw clause and a raw statement. -/
def locatedL (clause statement : List Char) : Bool := locatedN (k15Normalize clause) statement

/-- C-06, R-22 — the mock provider's clause: "the whitespace-collapsed statement cut to its
first 280 characters — a prefix, so it is always LOCATED under K-15". Transcribes
`judge_mock.py:40` (`" ".join(req.statement.split())[:280]`) byte for byte. -/
def mockClause (statement : List Char) : List Char := (collapseWs statement).take k15Cut

/-! ## C-05 — the status algorithm -/

/-- C-05 — `IdStatus (deterministic): RETIRED | UNCITED | UNTESTED | UNVERIFIED | FAILING |
SKIPPED | PASSING` plus `IdStatus (judge-only): WEAKLY_PASSING`. -/
inductive Status where
  | retired | uncited | untested | unverified | failing | skipped | passing | weaklyPassing
  deriving DecidableEq, Repr

/-- C-06 — the four-value verdict set. -/
inductive VerdictToken where
  | asserts | executesOnly | unrelated | unknown
  deriving DecidableEq, Repr

/-- C-06 — parse a raw verdict string against the four-value set (rule 2). -/
def VerdictToken.parse : String → Option VerdictToken
  | "ASSERTS" => some .asserts
  | "EXECUTES_ONLY" => some .executesOnly
  | "UNRELATED" => some .unrelated
  | "UNKNOWN" => some .unknown
  | _ => none

/-- C-05 — the evidence facts `graph.deterministic_status` (`graph.py:78-97`) and
`graph.apply_verdicts` (`graph.py:178-198`) read, and nothing else. Field-per-step:
`retired` (§1, `spec.retired`); `family`/`hasTestCitation`/`hasSrcCitation` (§2, `not tests`/
`not src`, F-001); `resultsGiven`/`anyTestHasOutcome`/`anyFailedOrError`/`allOutcomesSkipped`
(§3–§4, `results_given`/`outcomes`); `judgeEnabled`/`recorded`/`verdicts` (§5, R-35,
`apply_verdicts`'s `rec.spec.recorded` guard and `collected` list). -/
structure Evidence where
  retired : Bool
  family : Family
  hasTestCitation : Bool
  hasSrcCitation : Bool
  resultsGiven : Bool
  anyTestHasOutcome : Bool
  anyFailedOrError : Bool
  allOutcomesSkipped : Bool
  judgeEnabled : Bool
  recorded : Bool
  verdicts : List VerdictToken
  deriving DecidableEq, Repr

/-- C-05 step 5 — the judge-only downgrade: `PASSING → WEAKLY_PASSING` iff `V` is non-empty, no
`v` in `V` is `ASSERTS`, and some `v` is `EXECUTES_ONLY` or `UNRELATED`. Transcribes
`apply_verdicts`'s final `if` (`graph.py:193-198`). -/
def step5 (e : Evidence) : Status :=
  if e.judgeEnabled ∧ !e.recorded ∧ !e.verdicts.isEmpty
     ∧ e.verdicts.all (fun v => v ≠ .asserts)
     ∧ e.verdicts.any (fun v => v = .executesOnly ∨ v = .unrelated)
  then .weaklyPassing else .passing

/-- C-05 steps 4–5 — worst outcome then the judge step. Transcribes
`deterministic_status`'s last three lines (`graph.py:93-97`); `step5` stands in for the status
`apply_verdicts` later assigns when `status == PASSING` (`graph.py:180-198`). -/
def step4 (e : Evidence) : Status :=
  if e.anyFailedOrError then .failing
  else if e.allOutcomesSkipped then .skipped
  else step5 e

/-- C-05 — the whole deterministic algorithm, steps 1–5. Transcribes
`graph.deterministic_status` (`graph.py:78-97`) verbatim: the T-family branch
(`graph.py:85-89`) and the non-T branch (`graph.py:84,90`) share the same tail
(`graph.py:90-97`), reproduced here as `step4`. -/
def statusOf (e : Evidence) : Status :=
  if e.retired then .retired
  else if e.family = .T then
    (if !e.hasTestCitation then .uncited
     else if !e.resultsGiven ∨ !e.anyTestHasOutcome then .unverified
     else step4 e)
  else
    (if !e.hasTestCitation ∧ !e.hasSrcCitation then .uncited
     else if !e.hasTestCitation then .untested
     else if !e.resultsGiven ∨ !e.anyTestHasOutcome then .unverified
     else step4 e)

/-! ## C-06 — validation and coercion -/

/-- C-06 — a provider's raw answer, abstracted to exactly the fields `judge.validate`
(`judge.py:187-214`) inspects: `failure` (rule 1, handled one level up in `judge_edge`'s
`except` clauses, `judge.py:217-232`; the tag is the class of failure); `verdict` (rule 2,
`raw.verdict not in VERDICTS`); `clause` (rule 3: `none` when `isinstance(raw.clause, str)` is
false); `evidenceCount` and `evidenceInSpan` (rules 6–7, the `evidence` loop at `judge.py:208-211`);
`rationale` (rule 8, `clean_rationale`); `clauseLocated` (rule 5, `locate_clause(...) is not
None`). -/
structure RawAnswer where
  failure : Option String
  verdict : Option String
  clause : Option String
  evidenceCount : Nat
  evidenceInSpan : Bool
  rationale : List Char
  clauseLocated : Bool
  deriving DecidableEq, Repr

/-- C-06 rule 8, K-07 — `rationale ≤ 280`; a longer one is truncated to 277 + `...`.
Transcribes `judge.clean_rationale` (`judge.py:147-152`). -/
def truncateRationale (r : List Char) : List Char :=
  if r.length ≤ rationaleMax then r else r.take rationaleKeep ++ ['.', '.', '.']

/-- C-06 — a recorded verdict: the token, the clause (`""` whenever the token is `UNRELATED`,
`UNKNOWN`, or the verdict was coerced per E-49), the coercion flag, and the rationale. -/
structure Judged where
  verdict : VerdictToken
  clause : List Char
  coerced : Bool
  rationale : List Char
  deriving DecidableEq, Repr

/-- C-06 — rule 1's rationale: `judge: <class of failure>`. Transcribes `_unknown`'s callers in
`judge_edge` (`judge.py:222-229`: `"judge: timeout"`, `f"judge: http {exc.status}"`,
`"judge: unavailable"`). -/
def failureRationale (tag : String) : List Char := "judge: ".toList ++ tag.toList

/-- C-06 (F-402) — the validation cascade, in the spec's order. The first rule that fires
determines the verdict and the rationale; no later rule is evaluated. Transcribes
`judge.validate` (`judge.py:187-214`) line for line: rule 2 (`judge.py:192-193`), rule 3
(`judge.py:195`), rule 4 (`judge.py:197-199`), rule 5 (`judge.py:200-203`), rule 6
(`judge.py:204-206`), rule 7 (`judge.py:207-211`), rule 8 (`judge.py:212-214`, folded into every
branch's `clean_rationale`/`truncateRationale` call). -/
def coerce (a : RawAnswer) : Judged :=
  if a.failure.isSome then
    { verdict := .unknown, clause := [], coerced := true
      rationale := truncateRationale (failureRationale (a.failure.getD "")) }
  else
    match a.verdict with
    | none =>
      { verdict := .unknown, clause := [], coerced := true
        rationale := truncateRationale rationaleMalformed.toList }
    | some v =>
      match VerdictToken.parse v with
      | none =>
        { verdict := .unknown, clause := [], coerced := true
          rationale := truncateRationale rationaleMalformed.toList }
      | some tok =>
        let cl := (a.clause.getD "").toList
        match tok with
        | .unrelated | .unknown =>
          { verdict := tok, clause := [], coerced := false
            rationale := truncateRationale a.rationale }
        | .asserts | .executesOnly =>
          if !a.clauseLocated then
            { verdict := .unknown, clause := [], coerced := true
              rationale := truncateRationale rationaleUnlocated.toList }
          else if tok = .asserts ∧ a.evidenceCount = 0 then
            { verdict := .unknown, clause := [], coerced := true
              rationale := truncateRationale rationaleUngrounded.toList }
          else if !a.evidenceInSpan then
            { verdict := .unknown, clause := [], coerced := true
              rationale := truncateRationale rationaleUngrounded.toList }
          else
            { verdict := tok, clause := cl, coerced := false
              rationale := truncateRationale a.rationale }

/-! ## C-07 — metrics -/

/-- C-07 (Q-009) — `ROUND_HALF_EVEN` of `num/den` at `ratioScale` resolution, for `den > 0`.
The Lean fixed-point reimplementation of `graph.ratio`'s `Decimal` arithmetic
(`graph.py:32-38`); both round half-to-even at four decimal places, and for the counts a
conformance run produces (well under the 28-digit `Decimal` context), the two agree exactly. -/
def roundHalfEven (num den : Nat) : Nat :=
  let q := num * ratioScale
  let quo := q / den
  let rem := q % den
  if 2 * rem > den then quo + 1
  else if 2 * rem < den then quo
  else if quo % 2 = 0 then quo else quo + 1

/-- C-07, I-008 — a ratio as fixed-point units, or `none` on a zero denominator. Transcribes
`graph.ratio`'s `if denominator == 0: return None` (`graph.py:35-36`). -/
def ratioUnits (num den : Nat) : Option Nat :=
  if den = 0 then none else some (roundHalfEven num den)

/-- C-07 — `conformance = |PASSING| / in_scope`. Transcribes `compute_metrics`'s
`ratio(passing, in_scope)` (`graph.py:260`). -/
def conformanceUnits (passing inScope : Nat) : Option Nat := ratioUnits passing inScope

/-- C-07 (F-405) — `judge_strength = |PASSING \ RECORDED| / (|PASSING \ RECORDED| +
|WEAKLY_PASSING|)`. Transcribes `compute_metrics`'s `ratio(judged_passing, judged_passing +
weak)` (`graph.py:252`), where `judged_passing` excludes RECORDED ids (`graph.py:250`). -/
def judgeStrengthUnits (passingNotRecorded weaklyPassing : Nat) : Option Nat :=
  ratioUnits passingNotRecorded (passingNotRecorded + weaklyPassing)

/-- C-07, C-16 — `declared_ratio = |DECLARED citations of in-scope R/C/I/K/E ids| / |all such
citations|`. Transcribes `compute_metrics`'s `ratio(*graph.declared_counts)` (`graph.py:267`),
fed by `build_graph`'s `(declared_hits, population)` accumulation (`graph.py:153-162`). -/
def declaredRatioUnits (declaredCitations allCitations : Nat) : Option Nat :=
  ratioUnits declaredCitations allCitations

/-- C-07, K-11 — `unknown_rate = |edges with verdict UNKNOWN| / |judged edges|`. Transcribes
`compute_metrics`'s `ratio(unknown, judged)` (`graph.py:253`). -/
def unknownRateUnits (unknownEdges judgedEdges : Nat) : Option Nat :=
  ratioUnits unknownEdges judgedEdges

/-! ## C-07, E-14, E-36 — `judge_available` -/

/-- §5.1 — the three judge modes. -/
inductive JudgeMode where
  | none | mock | llm
  deriving DecidableEq, Repr

/-- C-07, E-14, E-35, E-36 — the C-06 call census for one run: the mode, the number of
judge-eligible edges (`eligible`, from `graph.eligible_edges`, `graph.py:165-175`), the number of
C-06 calls actually issued (`issued`), and how many of those succeeded (`succeeded`) — the
`calls_made`/`calls_ok` counters `run_judge` accumulates over non-budget-skipped verdicts
(`judge.py:433-444`). -/
structure JudgeCalls where
  mode : JudgeMode
  eligible : Nat
  issued : Nat
  succeeded : Nat
  deriving DecidableEq, Repr

/-- C-07, E-14, E-36 — `judge_available`: null when `--judge none`; otherwise "true when at
least one judge call succeeded OR no edge was eligible (vacuously available), and false only when
every call failed". The source computes an equivalent but differently-shaped fact directly —
`run_judge`'s `available = calls_made == 0 or calls_ok > 0` (`judge.py:444`), where `calls_made`
already excludes budget-skipped edges — rather than branching on `eligible`/`issued`/`succeeded`
the way this spec-level statement does; see the correspondence table's note on this gap. Partial:
the configuration `eligible > 0`, `issued = 0` — every eligible edge budget-skipped, so no call
was made and none failed — is covered by neither of the spec's two clauses. -/
def judgeAvailable (c : JudgeCalls) : Option Bool :=
  match c.mode with
  | .none => none
  | .mock | .llm =>
    if decide (1 ≤ c.succeeded) ∨ c.eligible = 0 then some true
    else if 0 < c.issued then some false
    else none

/-! ## §5.4, R-14, R-15, R-28, E-19 — the exit-code function -/

/-- §5.4, R-14, R-15, E-19, I-009 — the report facts `report.exit_code_for` (`report.py:82-97`)
reads: the status facts R-15 gates on, `allInScopeUncited` (E-19: every in-scope id is
`UNCITED`, `report.py:88-89`), the two citation lists, and the R-28 judge facts. -/
structure ReportFacts where
  anyInScopeFailing : Bool
  allInScopeUncited : Bool
  allInScopePassing : Bool
  anyDangling : Bool
  anyStale : Bool
  judgeLlm : Bool
  judgeAvailable : Option Bool
  unknownRateExceeds : Bool
  deriving DecidableEq, Repr

/-- R-15, R-28, §5.4 — the strict judge gate: with `--judge llm` the judge must be available and
`unknown_rate` must not exceed `--max-unknown`; otherwise no judge condition applies. Transcribes
the third `if report["strict_judge_failure"] is not None` branch's precondition
(`report.py:95-96`, via `strict_judge_failure`, `report.py:70-79`). -/
def strictJudgeHolds (f : ReportFacts) : Bool :=
  !f.judgeLlm ∨ (f.judgeAvailable = some true ∧ !f.unknownRateExceeds)

/-- §5.4, R-14, R-15, E-19 — the exit code of a `check` run. Transcribes `report.exit_code_for`
(`report.py:82-97`) as its own `if`-chain, in order: a `FAILING` in-scope id exits `1`
(`report.py:86-87`); every in-scope id `UNCITED` exits `1` even without `--strict` (E-19,
`report.py:88-89` — the branch the spec-model project's version of this function omitted); under
`--strict`, not every in-scope id `PASSING`, or a dangling/stale citation, or a failed R-28 gate
each exit `1` (`report.py:90-96`); otherwise `0` (`report.py:97`). -/
def exitOfCheck (f : ReportFacts) (strict : Bool) : Nat :=
  if f.anyInScopeFailing then exitNotConforming
  else if f.allInScopeUncited then exitNotConforming
  else if strict ∧ !(f.allInScopePassing ∧ !f.anyDangling ∧ !f.anyStale ∧ strictJudgeHolds f) then
    exitNotConforming
  else exitConforming

/-- C-07, R-28, E-32, Q-004 — `strict_judge_failure`: non-null only when `--strict` and
`--judge llm` both hold, and `unavailable` takes precedence when both R-28 reasons hold.
Transcribes `report.strict_judge_failure` (`report.py:70-79`) exactly: the two early returns at
`report.py:72-73` become the `strict ∧ judgeLlm` guard, and `report.py:74-75`'s `if
judge_available is False` is checked before `report.py:76-78`'s rate comparison. -/
def strictJudgeFailure (f : ReportFacts) (strict : Bool) : Option String :=
  if strict ∧ f.judgeLlm ∧ (f.judgeAvailable = some false ∨ f.unknownRateExceeds) then
    (if f.judgeAvailable = some false then some "unavailable" else some "unknown_rate")
  else none

/-! ## C-11 — the progress indicator -/

/-- C-11 — the filled cell count `k = ⌊20·d/n⌋`. Transcribes `progress_line`'s
`k = BAR_CELLS * done // total` (`judge.py:252`). -/
def barCells (done total : Nat) : Nat :=
  if total = 0 then 0 else progressCells * done / total

/-- C-11, K-13 — the bar: `k` `#` cells then `20 − k` `-` cells. Transcribes `progress_line`'s
`bar = "#" * k + "-" * (BAR_CELLS - k)` (`judge.py:253`). -/
def bar (done total : Nat) : List Char :=
  List.replicate (barCells done total) progressFull ++
    List.replicate (progressCells - barCells done total) progressEmpty

/-- C-11 — the estimate of time remaining, `⌊t(n−d)/d⌋` seconds for `d > 0`; `none` (rendered
`?:??`) while `d = 0`. Transcribes `progress_line`'s `left = "?:??" if done == 0 else
_mmss(elapsed / done * (total - done))` (`judge.py:254`), the `_mmss` rendering itself deferred
(string formatting, carried by T-62). -/
def remainingSeconds (t done n : Nat) : Option Nat :=
  if done = 0 then none else some (t * (n - done) / done)

/-! ## §5.1, §5.4, §8 — the invocation decision surface -/

/-- §5.1, §5.4 — the six surfaces of the CLI, plus the two inert ones. -/
inductive Subcommand where
  | check | impact | explain | selfCheck | version | help
  deriving DecidableEq, Repr

/-- §5.1, §5.4, §8 — one constructor per *usage-error* (exit 2) and *input-contract-violation*
(exit 3) row of the spec, realized by `cli.py`'s per-flag validation and by `extract.py`'s
`SpecError` (E-01, E-02, E-03) and `results.ResultsError` (E-05): the validation rows of §5.1,
and E-01, E-02, E-03, E-05, E-09, E-18, E-21, E-52, E-53, E-54, E-58, E-60. -/
inductive Fault where
  | missingSpec
  | pathOutsideRoot
  | pathsElementMissing
  | judgeModeInvalid
  | maxUnknownInvalid
  | judgeConcurrencyInvalid
  | judgeBudgetInvalid
  | budgetPercentWithoutTriage
  | progressInvalid
  | verboseInvalid
  | depthInvalid
  | judgeEnvMissing
  | changedUndeclared
  | impactBothOrNeither
  | impactRejectedFlag
  | explainUndeclaredId
  | specZeroIds
  | specDuplicateId
  | specRetireConflict
  | resultsMalformed
  | outNotWritable
  deriving DecidableEq, Repr

/-- §5.4, K-01 — the usage-error (exit 2) faults. -/
def Fault.isUsage : Fault → Bool
  | .specZeroIds | .specDuplicateId | .specRetireConflict | .resultsMalformed | .outNotWritable => false
  | _ => true

/-- §5.4, K-01 — the input-contract-violation (exit 3) faults: "E-01, E-02, E-03, E-05, E-18". -/
def Fault.isContract (x : Fault) : Bool := !x.isUsage

/-- §5.4, I-001 — the observable result of a run: the exit code and whether report files are
written (the `Reports written?` column). -/
structure Result where
  exit : Nat
  reports : Bool
  deriving DecidableEq, Repr

/-- §5.1, §5.4, §8 — the enumeration of run outcomes: one constructor per decision case of the
spec — a `check` run (keyed by report facts and `--strict`), an `impact` run whose changed set came
out empty (C-13), an `explain` run on a declared or undeclared id (E-60), one per `Fault` row, the
`explain`-without-`--spec` configuration, and an interrupt (E-41). -/
inductive Input where
  | check (f : ReportFacts) (strict : Bool)
  | impactEmptyChanged
  | explainDeclared
  | explainUndeclared
  | fault (x : Fault)
  | explainAbsentSpec
  | interrupt
  deriving DecidableEq, Repr

/-- §5.4, §5.1, C-13, E-41, E-60 — the stated outcome of each enumerated input. `none` means
the spec states no outcome for this input — the representation of a silent case, never a
default (see `docs/reviews/SPEC_MODEL_FINDINGS.md` F-501, inherited unchanged from
`proof_from_spec`: nothing in `cli.py`'s handling of `explain` resolves the `--spec`-optional vs.
`--spec`-required disagreement between §5.1's synopsis and its flag table). -/
def outcome : Input → Option Result
  | .check f strict => some { exit := exitOfCheck f strict, reports := true }
  | .impactEmptyChanged => some { exit := exitConforming, reports := true }
  | .explainDeclared => some { exit := exitConforming, reports := false }
  | .explainUndeclared => some { exit := exitUsage, reports := false }
  | .fault x => some { exit := if x.isUsage then exitUsage else exitContract, reports := false }
  | .explainAbsentSpec => none
  | .interrupt => some { exit := exitContract, reports := false }

-- Cross-module normalization: every definition `Theorems.lean` reasons through is `grind unfold`
-- (and `public`), so it unfolds in the proof module.
attribute [grind unfold]
  Family.letter Family.padWidth Family.order letterFamily
  padLeft normalizeDisplay IdKey.orderKey
  stripFromFirst joinNameL
  Outcome.rank worst worstOf
  isWs collapseWs k15Normalize prefixEq infixOf suffixes locatedN locatedL mockClause
  VerdictToken.parse
  step5 step4 statusOf
  truncateRationale coerce
  roundHalfEven ratioUnits conformanceUnits judgeStrengthUnits declaredRatioUnits unknownRateUnits
  judgeAvailable
  strictJudgeHolds exitOfCheck strictJudgeFailure
  barCells bar remainingSeconds
  Fault.isUsage Fault.isContract
  outcome

end SpeccheckProof.Speccheck.Model
