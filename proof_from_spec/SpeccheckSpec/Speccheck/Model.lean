/-
# `SpeccheckSpec.Speccheck.Model` — the transcription

The normative tables of `SPEC.md` v1.26 (Specification Conformance Checker, `speccheck`) as pure,
total functions. This file is leg A of the trust boundary and the correspondence table below is
manual: Lean cannot read the document, so the claim "the model is a faithful transcription of
the spec's normative tables" is checked here row by row, and made *checkable* — not proven — by the
`section Rows` theorems in `Theorems.lean`.

## Correspondence table (spec anchor → model element)

| Spec anchor | Model element | Note |
| --- | --- | --- |
| C-01 `ID`/`FAMILY`/`DIGITS` | `Family`, `letterFamily`, `Family.letter` | six families; `D` separate (`decisionFamilyLetter`) |
| C-01 normalized form, I-011 | `IdKey`, `Family.order`, `normalizeDisplay` | the model's identity *is* the normalized key, so injectivity is the typing fact |
| K-04 | `Family.padWidth`, `k04MaxDigits` | a 4+ digit token is not an ID (modelled as `Family` never containing one) |
| C-04 `join_name` step 1 | `stripFromFirst '[' ']'` | everything from the first `[` |
| C-04 `join_name` step 2 (R-31, D-19) | `stripFromFirst '(' ')'` | everything from the first `(` |
| C-04 worst-of (E-06, E-24) | `Outcome`, `Outcome.rank`, `worst` | `error > failed > skipped > passed` |
| C-04 root elements | `junitRoots` | accepted `<testsuites>`/`<testsuite>` |
| C-05 steps 1–5 | `Status`, `Evidence`, `statusOf`, `step4`, `step5` | the whole algorithm; `Evidence` carries exactly the evidence facts the steps read |
| C-05 family-T rule (F-001, E-25) | `statusOf`'s `.T` branch | source citations are evidence only |
| C-05 recorded skip (R-35, E-51) | `step5`'s `!recorded` conjunct | a recorded id is exempt from the judge and nothing else |
| C-06 validation rules 1–8 (F-402) | `RawAnswer`, `coerce` | ordered cascade; the first rule that fires decides |
| C-06 rule 8 / K-07 | `truncateRationale` | truncate to 277 + `...` |
| K-15 located clause | `locatedL`, `locatedN`, `k15Normalize`, `infixOf`, `prefixEq` | collapse, trim, cut 280; ≥ 12 or the short-statement rule |
| C-07 ratios (Q-009) | `ratioUnits`, `roundHalfEven`, `ratioScale` | fixed point, 4 places, half-even |
| C-07 metrics | `judgeStrengthUnits`, `declaredRatioUnits`, `conformanceUnits` | populations per C-07/F-405 |
| C-07 zero denominators (F-405, E-19) | `ratioUnits`'s `den = 0 → none` | I-008 |
| C-07 `judge_available` (E-14, E-35, E-36; amended v1.20) | `JudgeMode`, `JudgeCalls`, `judgeAvailable` | total, boolean under `mock`/`llm` — finding F-502, resolved v1.20 |
| §5.4 exit map, R-14, R-15 | `ReportFacts`, `exitOfCheck`, `strictJudgeHolds` | pure function of report content + `--strict` |
| R-28, E-32 (amended v1.20), Q-004 | `strictJudgeFailure` | `unavailable` takes precedence, now covering the E-35 case too |
| K-18 (v1.20) | `exitPrecedence` | usage-fault precedence over a contract violation — finding F-503, resolved v1.20 |
| E-64 (v1.20) | `outcome`'s `.explainAbsentSpec` case | now a stated outcome (exit 2) — finding F-501, resolved v1.20 |
| C-11 | `barCells`, `bar`, `remainingSeconds` | `k = ⌊20d/n⌋`; `left = t(n−d)/d` |
| §5.1 CLI surface, §5.4 | `Subcommand`, `Fault`, `Input`, `Result`, `outcome` | one `Fault` constructor per usage/contract row, one `Input` constructor per decision case |
| E-41 | `Input.interrupt` | exit 3, no report survives |
| E-01/E-02/E-03/E-05/E-18 | `Fault.specZeroIds` … `Fault.outNotWritable` | the exit-3 set of §5.4 |
| E-09/E-21/E-52/E-53/E-54/E-58/E-60; §5.1 bad values | the usage `Fault` constructors | the exit-2 set |
| C-21, K-17 (v1.19) | `ProofState`, `ProofJoin`, `proofStateOf` | manifest-to-citation join: `checked`/`failed`/`unknown`/`stale`, `none` for no citation (D-49) |
| E-63 (v1.19) | `statusWithProof`, `statusWithProof_ignoresProof` | proof is not a field of `Evidence`, so a wrapper that accepts it provably returns `statusOf`'s answer unchanged |
| C-07, D-49 (v1.19, amended v1.19.1) | `topLevelProofKeyPresent` | finding F-504, resolved v1.19.1 |
| R-15 amended, C-27, D-64 (v1.25) | `ReportFacts.anyUncontrolled`, `exitOfCheck`'s strict conjunct | an `UNCONTROLLED` hazard fails `--strict` |
| R-105 (v1.24) | `SummaryWord`, `r15Holds`, `summaryWord` | `CONFORMING` / `UNPROVEN` / `NOT CONFORMING` from the exit and R-15's conditions |
| E-19 | `ReportFacts.allInScopeUncited`, `e19Exit` | E-19's own stated exit, carried beside §5.4's — finding F-904 |
| D-45 (v1.19) | `ReportFacts.proofFailedWithManifest`, `d45StrictFails` | D-45's strict rule, carried beside R-15's — finding F-905 |
| C-27, R-108, R-109 (v1.25) | `HazardStatus`, `Control`, `liveControls`, `hazardStatus` | the roll-up over a hazard's controlling ids; a risk-file hazard nobody marks is the empty list |
| R-107, C-26, E-82, E-83 (v1.25) | `VerifyInput`, `verifyExit`, `verifyReadsInputs` | the four exit codes and E-83's "no input file is read" |
| R-111, C-29, E-86, E-87, E-88 (v1.26) | `IQFacts`, `QualFailure`, `firstFailure`, `verdictQualified`, `qualifyExit` | C-29's verdict sentence and its first-failure order, both transcribed, so their agreement is a theorem |
| R-115, C-31 (v1.26) | `Version`, `verLt`, `Anomaly`, `openAnomalies` | entries not fixed in or before the running version, file order |
| E-65, E-70, E-84, E-85, R-102 (v1.19..v1.25) | the new `Fault` constructors | each in the 2/3 class its row states |

Deliberately not modelled, with the reason. The spec is a program that reads a tree of files;
Lean operates on pure values, so nothing that *is* the filesystem, the network, or a clock is a
parameter of the model:

| Spec anchor | Why not modelled here |
| --- | --- |
| §3.1 lifecycle, §3.3 durable artifacts, I-001 | the write/rename/cleanup ordering is process-level; carried by T-38/T-45 |
| C-01 declaration parsing, fences, SECTION BODY, K-14 cap | a text transformer over a document; the *bounds* are `k14Cap` and the facts in `Spec.lean`, the parser is carried by T-01…T-07, T-72 |
| C-02 `SpecIndex` | a container of the above; carried by T-01/T-06 |
| C-03 scanning, adapters, PATHS list, exclusions, binary/symlink | filesystem traversal; the *filters* are pinned as constants (`k02*`, `k03*`), the walk is carried by T-08…T-14, T-78 |
| C-04 XML parsing & join | XML is not a Lean value; `joinName` and `worst` *are* modelled, the reader is carried by T-15…T-19, T-52, T-58, T-68 |
| C-06/C-09/C-10 provider wire format, HTTP, prompt hash | network + bytes; carried by T-30, T-33, T-40, T-54, T-74 |
| C-12 edge extraction, C-13 walk/reports | the edge *kinds* and their order are constants here; the token pass and the BFS are carried by T-79, T-80…T-82 |
| C-08/C-16/C-19 rendered bytes, help screens | rendering; carried by T-35, T-73, T-77, T-86, T-88, T-95…T-98 |
| C-17, K-16 ordering | advisory network pass; carried by T-89, T-90 |
| C-18 trace rendering | rendering from modelled facts; carried by T-92…T-94 |
| §9 tests, K-08 performance, K-05/K-06/K-12 timing | empirical / timing budgets; the §9 test ids carry them (see the deferral table) |
| R-100, C-20 (v1.19) | the lean adapter — declaration-head split, bold-span doc-comment tag extraction | a text transformer over Lean source, the same class as C-01/C-03; carried by T-99 |
| E-62, E-65 (v1.19) | an unreadable/non-Lean `--proof` file, or an unreadable/malformed `--proof-results` file | filesystem/IO, the same class as E-10/E-11/E-29/E-05; carried by T-99 |
| I-018 (v1.19) | byte-identity of `speccheck.json`/`SPEC_CONFORMANCE_REPORT.md` under flag absence | rendering, the same class as C-08; carried by T-100 |
| R-101..R-104, C-22..C-24 (v1.21..v1.23) | namespaces, the citation map's resolution, the JS/TS adapter | text transformers over files and a JSON map, the same class as C-01/C-03; carried by T-104..T-117 |
| R-106, R-112, C-25, I-020 (v1.25, v1.26) | manifest and package-tree hashing | SHA-256 over bytes; the exit consequences (`verifyExit`, `firstFailure`) are modelled, the hashing is carried by T-122..T-125, T-130, T-131 |
| R-113, R-114, C-28, C-30, I-019, I-021..I-023, K-19, K-20 | the OQ catalog runner, packaged data, risk-file parsing, inertness, size caps | process- and file-level; carried by the §9.17..§9.19 tests (deferral table) |
| E-66..E-69, E-71..E-81 | Notes, marker grammar, adapter edge cases | rendering and parsing; carried by their §9 tests (deferral table) |
-/
import SpeccheckSpec.Speccheck.Spec

namespace SpeccheckSpec.Speccheck.Model

open SpeccheckSpec.Speccheck.Spec

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
for R/C/K/E/T, 3 digits for I`. -/
def normalizeDisplay (k : IdKey) : String :=
  String.singleton k.family.letter ++ "-" ++ padLeft k.family.padWidth (toString k.number)

/-- C-12 — the C-12 total order key: family order then number. -/
def IdKey.orderKey (k : IdKey) : Nat × Nat := (k.family.order, k.number)

/-! ## C-04 — the JUnit join -/

/-- C-04 — `join_name` step 1 and step 2 share one rule: "if it ends with `<close>` and contains
`<open>`, everything from the FIRST `<open>` to the end is removed, whatever it contains". -/
def stripFromFirst (op cl : Char) (cs : List Char) : List Char :=
  if cs.getLast? = some cl ∧ cs.any (· = op) then cs.takeWhile (· ≠ op) else cs

/-- C-04 (F-005, F-101, R-31, D-19) — the two-step `join_name`: strip from the first `[`, then
from the first `(`. -/
def joinNameL (cs : List Char) : List Char :=
  stripFromFirst '(' ')' (stripFromFirst '[' ']' cs)

/-- C-04 — `join_name` on the `String` a `<testcase name>` carries. -/
def joinName (s : String) : String := String.ofList (joinNameL s.toList)

/-- C-04, E-06, E-24 — the four JUnit outcomes. -/
inductive Outcome where
  | passed | skipped | failed | error
  deriving DecidableEq, Repr

/-- C-04 — the worst-first rank `error > failed > skipped > passed`. -/
def Outcome.rank : Outcome → Nat
  | .passed => 0 | .skipped => 1 | .failed => 2 | .error => 3

/-- C-04 (E-06, E-24) — the case's single outcome is the worst of its results. -/
def worst (a b : Outcome) : Outcome := if a.rank ≤ b.rank then b else a

/-- C-04 (E-06, E-24) — worst-of a list; `passed` is the identity of `worst`. -/
def worstOf (l : List Outcome) : Outcome := l.foldl (fun acc o => worst acc o) .passed

/-! ## K-15 — the located-clause matcher -/

/-- K-15 — whitespace, per the spec's "every run of whitespace". -/
def isWs (c : Char) : Bool := c = ' ' ∨ c = '\t' ∨ c = '\n' ∨ c = '\r'

/-- K-15 — collapse every run of whitespace to one space. -/
def collapseWs (cs : List Char) : List Char := go false cs
where
  go (prevWs : Bool) : List Char → List Char
    | [] => []
    | c :: cs =>
      if isWs c then (if prevWs then go true cs else ' ' :: go true cs) else c :: go false cs

/-- K-15 — the clause's normalization: collapse, trim, then cut to the first `k15Cut`
characters. -/
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

/-- K-15 — `a` occurs as a (case-sensitive) contiguous substring of `b`. -/
def infixOf (a b : List Char) : Bool := (suffixes b).any (prefixEq a)

/-- K-15 — the matcher, given the clause already normalized by `k15Normalize`: it is located
when it is at least `k15Min` characters and a substring of the statement, or the statement is
shorter than `k15Min` and the clause equals it (an empty statement is matched by an empty clause). -/
def locatedN (nc statement : List Char) : Bool :=
  (decide (k15Min ≤ nc.length) && infixOf nc (collapseWs statement)) ||
    (decide ((collapseWs statement).length < k15Min) && decide (nc = collapseWs statement))

/-- K-15 — the full located check on a raw clause and a raw statement. -/
def locatedL (clause statement : List Char) : Bool := locatedN (k15Normalize clause) statement

/-- C-06 — the mock provider's clause: "the whitespace-collapsed statement cut to its first 280
characters — a prefix, so it is always LOCATED under K-15". -/
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

/-- C-05 — the evidence facts the five steps read, and nothing else. Field-per-step:
`retired` (§1); `family`/`hasTestCitation`/`hasSrcCitation` (§2, F-001); `resultsGiven`/
`anyTestHasOutcome`/`anyFailedOrError`/`allOutcomesSkipped` (§3–§4); `judgeEnabled`/`recorded`/
`verdicts` (§5, R-35). `anyFailedOrError` and `allOutcomesSkipped` are stated directly, as the spec
reduces `O` before reading it. -/
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
`v` in `V` is `ASSERTS`, and some `v` is `EXECUTES_ONLY` or `UNRELATED`. -/
def step5 (e : Evidence) : Status :=
  if e.judgeEnabled ∧ !e.recorded ∧ !e.verdicts.isEmpty
     ∧ e.verdicts.all (fun v => v ≠ .asserts)
     ∧ e.verdicts.any (fun v => v = .executesOnly ∨ v = .unrelated)
  then .weaklyPassing else .passing

/-- C-05 steps 4–5 — worst outcome then the judge step. -/
def step4 (e : Evidence) : Status :=
  if e.anyFailedOrError then .failing
  else if e.allOutcomesSkipped then .skipped
  else step5 e

/-- C-05 — the whole deterministic algorithm, steps 1–5. -/
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

/-- C-06 — a provider's raw answer, abstracted to exactly the fields the eight rules inspect:
`failure` (rule 1: raised / timed out / non-JSON; the tag is the class of failure); `verdict`
(rule 2); `clause` (rule 3: `none` when absent or present-but-not-a-JSON-string); `evidenceCount`
and `evidenceInSpan` (rules 6–7); `rationale` (rule 8); `clauseLocated` (rule 5, from K-15). -/
structure RawAnswer where
  failure : Option String
  verdict : Option String
  clause : Option String
  evidenceCount : Nat
  evidenceInSpan : Bool
  rationale : List Char
  clauseLocated : Bool
  deriving DecidableEq, Repr

/-- C-06 rule 8, K-07 — `rationale ≤ 280`; a longer one is truncated to 277 + `...`. -/
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

/-- C-06 — rule 1's rationale: `judge: <class of failure>`. -/
def failureRationale (tag : String) : List Char := "judge: ".toList ++ tag.toList

/-- C-06 (F-402) — the validation cascade, in the spec's order. The first rule that fires
determines the verdict and the rationale; no later rule is evaluated. -/
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

/-- C-07 (Q-009) — `ROUND_HALF_EVEN` of `num/den` at `ratioScale` resolution, for `den > 0`. -/
def roundHalfEven (num den : Nat) : Nat :=
  let q := num * ratioScale
  let quo := q / den
  let rem := q % den
  if 2 * rem > den then quo + 1
  else if 2 * rem < den then quo
  else if quo % 2 = 0 then quo else quo + 1

/-- C-07, I-008 — a ratio as fixed-point units, or `none` on a zero denominator ("ratio = null
(JSON) / n/a (Markdown)"). -/
def ratioUnits (num den : Nat) : Option Nat :=
  if den = 0 then none else some (roundHalfEven num den)

/-- C-07 — `conformance = |PASSING| / in_scope` (`WEAKLY_PASSING` is NOT passing). -/
def conformanceUnits (passing inScope : Nat) : Option Nat := ratioUnits passing inScope

/-- C-07 (F-405) — `judge_strength = |PASSING \ RECORDED| / (|PASSING \ RECORDED| +
|WEAKLY_PASSING|)`: recorded ids are outside this population. -/
def judgeStrengthUnits (passingNotRecorded weaklyPassing : Nat) : Option Nat :=
  ratioUnits passingNotRecorded (passingNotRecorded + weaklyPassing)

/-- C-07, C-16 — `declared_ratio = |DECLARED citations of in-scope R/C/I/K/E ids| / |all such
citations|`. -/
def declaredRatioUnits (declaredCitations allCitations : Nat) : Option Nat :=
  ratioUnits declaredCitations allCitations

/-- C-07, K-11 — `unknown_rate = |edges with verdict UNKNOWN| / |judged edges|`. -/
def unknownRateUnits (unknownEdges judgedEdges : Nat) : Option Nat :=
  ratioUnits unknownEdges judgedEdges

/-! ## C-07, E-14, E-36 — `judge_available` -/

/-- §5.1 — the three judge modes. -/
inductive JudgeMode where
  | none | mock | llm
  deriving DecidableEq, Repr

/-- C-07, E-14, E-35, E-36 — the C-06 call census for one run: the mode, the number of
judge-eligible edges (`eligible`, I-010), the number of C-06 calls actually issued (`issued`), and
how many of those succeeded (`succeeded`). -/
structure JudgeCalls where
  mode : JudgeMode
  eligible : Nat
  issued : Nat
  succeeded : Nat
  deriving DecidableEq, Repr

/-- C-07 (amended v1.20), E-14, E-35, E-36 — `judge_available`: `none` when `--judge none`;
otherwise total and boolean — `true` when at least one judge call succeeded or no edge was
eligible (vacuously available), and `false` whenever at least one edge was eligible and no call
succeeded, whatever the reason: every call failed (E-14), or no call was issued at all (E-35 —
every eligible edge budget-skipped by K-12). Originally partial in the eligible-but-unissued
configuration (finding F-502, resolved v1.20): see `judgeAvailableNullIffNone` below. -/
def judgeAvailable (c : JudgeCalls) : Option Bool :=
  match c.mode with
  | .none => none
  | .mock | .llm =>
    if decide (1 ≤ c.succeeded) ∨ c.eligible = 0 then some true
    else some false

/-! ## §5.4, R-14, R-15, R-28 — the exit-code function -/

/-- §5.4, I-009 — the report facts the exit code is a pure function of: the status facts R-15
gates on, the two citation lists, and the R-28 judge facts. -/
structure ReportFacts where
  anyInScopeFailing : Bool
  allInScopePassing : Bool
  anyDangling : Bool
  anyStale : Bool
  judgeLlm : Bool
  judgeAvailable : Option Bool
  unknownRateExceeds : Bool
  /-- R-15 amended (v1.25), C-27: some hazard is `UNCONTROLLED`. -/
  anyUncontrolled : Bool := false
  /-- E-19: every in-scope id is `UNCITED` (no `--src`/`--tests` citation at all). Read by
  `e19Exit`, not by `exitOfCheck`: §5.4 and R-15 do not mention it (finding F-904). -/
  allInScopeUncited : Bool := false
  /-- D-45 (v1.19): a proof state is `failed` and `--proof-results` was given and readable. Read
  by `d45StrictFails`, not by `exitOfCheck`: R-15 names status and hazard status as its only
  inputs (finding F-905). -/
  proofFailedWithManifest : Bool := false
  deriving DecidableEq, Repr

/-- R-15, R-28, §5.4 — the strict judge gate: with `--judge llm` the judge must be available and
`unknown_rate` must not exceed `--max-unknown`; otherwise no judge condition applies. -/
def strictJudgeHolds (f : ReportFacts) : Bool :=
  !f.judgeLlm ∨ (f.judgeAvailable = some true ∧ !f.unknownRateExceeds)

/-- §5.4, R-14, R-15 — the exit code of a `check` run: `0` iff no in-scope ID is `FAILING` and,
under `--strict`, every in-scope ID is `PASSING`, `dangling` and `stale` are empty, no hazard is
`UNCONTROLLED` (v1.25), and the R-28 judge gate holds; else `1`. -/
def exitOfCheck (f : ReportFacts) (strict : Bool) : Nat :=
  if !f.anyInScopeFailing ∧
     (!strict ∨ (f.allInScopePassing ∧ !f.anyDangling ∧ !f.anyStale ∧ !f.anyUncontrolled ∧
       strictJudgeHolds f))
  then exitConforming else exitNotConforming

/-- §5.4, K-18 (v1.20) — the precedence the spec now pins between the two fault classes: when one
invocation carries both a usage fault (`usage`) and an input-contract violation (`contract`), the
usage fault is reported (`exitUsage`) — flag/value/`--root`-containment validation completes
before any spec/results/output read, so a run carrying a contract violation too never reaches the
check that would have found it. Before this, `SPEC.md` admitted the usage-first reading and its
contract-first twin as equally faithful to §5.4's table (finding F-503); K-18 states this is *the*
function, not one of two candidates — see `k18UsageWinsWhenBoth` in `Theorems.lean`. -/
def exitPrecedence (usage contract : Bool) : Nat :=
  if usage then exitUsage else if contract then exitContract else exitConforming

/-- C-07, R-28, E-32, Q-004 — `strict_judge_failure`: non-null only when R-28 forced exit 1;
`unavailable` takes precedence when both reasons hold. -/
def strictJudgeFailure (f : ReportFacts) (strict : Bool) : Option String :=
  if strict ∧ f.judgeLlm ∧ (f.judgeAvailable = some false ∨ f.unknownRateExceeds) then
    (if f.judgeAvailable = some false then some "unavailable" else some "unknown_rate")
  else none

/-! ## C-11 — the progress indicator -/

/-- C-11 — the filled cell count `k = ⌊20·d/n⌋`. -/
def barCells (done total : Nat) : Nat :=
  if total = 0 then 0 else progressCells * done / total

/-- C-11, K-13 — the bar: `k` `#` cells then `20 − k` `-` cells. -/
def bar (done total : Nat) : List Char :=
  List.replicate (barCells done total) progressFull ++
    List.replicate (progressCells - barCells done total) progressEmpty

/-- C-11 — the estimate of time remaining, `⌊t(n−d)/d⌋` seconds for `d > 0`; `none` (rendered
`?:??`) while `d = 0`. -/
def remainingSeconds (t done n : Nat) : Option Nat :=
  if done = 0 then none else some (t * (n - done) / done)

/-! ## §5.1, §5.4, §8 — the invocation decision surface -/

/-- §5.1, §5.4 — the six surfaces of the CLI, plus the two inert ones. -/
inductive Subcommand where
  | check | impact | explain | verify | qualify | selfCheck | version | help
  deriving DecidableEq, Repr

/-- §5.1, §5.4, §8 — one constructor per *usage-error* (exit 2) and *input-contract-violation*
(exit 3) row of the spec: the validation rows of §5.1, and E-01, E-02, E-03, E-05, E-09, E-18, E-21,
E-52, E-53, E-54, E-58, E-60. -/
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
  | namespaceInvalid
  | citationMapUnreadable
  | riskFileUnreadable
  | proofResultsUnreadable
  | sourceDateEpochInvalid
  | verifyManifestUsage
  | specZeroIds
  | specDuplicateId
  | specRetireConflict
  | resultsMalformed
  | outNotWritable
  | proofResultsMalformed
  | citationMapMalformed
  | riskFileMalformed
  | verifyManifestMalformed
  deriving DecidableEq, Repr

/-- §5.4, K-01 — the usage-error (exit 2) faults. -/
def Fault.isUsage : Fault → Bool
  | .specZeroIds | .specDuplicateId | .specRetireConflict | .resultsMalformed | .outNotWritable
  | .proofResultsMalformed | .citationMapMalformed | .riskFileMalformed
  | .verifyManifestMalformed => false
  | _ => true

/-- §5.4, K-01 — the input-contract-violation (exit 3) faults: "E-01, E-02, E-03, E-05, E-18,
E-65 (malformed manifest), E-70 (map shape faults), E-84 (malformed risk file)", and `verify`'s
E-83. -/
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

/-- §5.4, §5.1, C-13, E-41, E-60, E-64 — the stated outcome of each enumerated input. `none` means
the spec states no outcome for this input — the representation of a silent case, never a default.
Every constructor now maps to `some _` (`.explainAbsentSpec`'s case was resolved v1.20, E-64,
finding F-501): see `noSilence` in `Theorems.lean`. -/
def outcome : Input → Option Result
  | .check f strict => some { exit := exitOfCheck f strict, reports := true }
  | .impactEmptyChanged => some { exit := exitConforming, reports := true }
  | .explainDeclared => some { exit := exitConforming, reports := false }
  | .explainUndeclared => some { exit := exitUsage, reports := false }
  | .fault x => some { exit := if x.isUsage then exitUsage else exitContract, reports := false }
  | .explainAbsentSpec => some { exit := exitUsage, reports := false }
  | .interrupt => some { exit := exitContract, reports := false }

/-! ## C-21, K-17 — the proof-evidence join (v1.19) -/

/-- C-21, K-17 — the four states a cited declaration's manifest join can produce. -/
inductive ProofState where
  | checked | failed | unknown | stale
  deriving DecidableEq, Repr

/-- C-20, C-21, K-17 — the facts the join reads for one (declaration, id) citation: whether the
lean adapter (C-20) attributed a citation at all (`cited`); among the manifest's `theorems[]`,
whether one shares the declaration's name (`nameMatch`); among those, whether one also matches
its file (and line, where present — K-17's "in a different file or line"; `locationMatch`); and,
when matched, whether that entry's own `status` is `"checked"` rather than `"failed"`
(`manifestChecked`). `locationMatch`/`manifestChecked` are read only when the fields before them
hold — the join never inspects them otherwise, matching `proofStateOf`'s short-circuit order. -/
structure ProofJoin where
  cited : Bool
  nameMatch : Bool
  locationMatch : Bool
  manifestChecked : Bool
  deriving DecidableEq, Repr

/-- C-21, K-17, D-49 — the join: no citation → `none` (the id's `proof` array is empty, C-07); a
citation with no name-matching manifest entry → `unknown` (K-17: "never `failed`"); a name match
whose file/line differ → `stale`; a full match → the manifest's own `checked`/`failed`. -/
def proofStateOf (j : ProofJoin) : Option ProofState :=
  if !j.cited then none
  else if !j.nameMatch then some .unknown
  else if !j.locationMatch then some .stale
  else if j.manifestChecked then some .checked
  else some .failed

/-! ## E-63 — proof never changes status or the exit map -/

/-- E-63 — a wrapper taking a proof state alongside the evidence `statusOf` already reads, to
state "a proof state never changes status" as a real equality rather than an absent parameter.
`_p` is unused by construction: `Evidence` (C-05) carries no proof field, so there is nothing for
a proof state to reach. -/
def statusWithProof (e : Evidence) (_p : Option ProofState) : Status := statusOf e

/-- C-07, D-49 (amended v1.19.1) — whether the top-level `proof` key (and therefore its `build`
echo) is written: present whenever `--proof` **or** `--proof-results` was given. Originally tied
to `--proof` alone (finding F-504: a `--proof-results`-only run read the manifest but wrote no
trace of it); D-49 was amended same-session, before any implementation existed, and this
definition now matches the corrected rule — see `f504ResolvedManifestAloneWritesKey` below. -/
def topLevelProofKeyPresent (proofGiven proofResultsGiven : Bool) : Bool :=
  proofGiven || proofResultsGiven


/-! ## R-105 (v1.24) — the summary line's status word -/

/-- §5.1, R-105 — the three `<STATUS>` words. -/
inductive SummaryWord where
  | conforming | unproven | notConforming
  deriving DecidableEq, Repr

/-- R-15, R-105 — R-15's conditions (everything but the R-28 judge gate): every in-scope id
`PASSING`, no dangling or stale citation, and (v1.25) no `UNCONTROLLED` hazard. -/
def r15Holds (f : ReportFacts) : Bool :=
  f.allInScopePassing ∧ !f.anyDangling ∧ !f.anyStale ∧ !f.anyUncontrolled

/-- R-105, §5.1 — `NOT CONFORMING` on exit `1`; on exit `0`, `CONFORMING` only when R-15's
conditions hold, else `UNPROVEN`. -/
def summaryWord (f : ReportFacts) (strict : Bool) : SummaryWord :=
  if exitOfCheck f strict = exitConforming then
    (if r15Holds f then .conforming else .unproven)
  else .notConforming

/-! ## E-19 and D-45 — two exit statements outside §5.4 (findings F-904, F-905) -/

/-- E-19 — the exit E-19 states for a run whose in-scope ids are all `UNCITED`: `1`; `none` when
E-19 does not apply. -/
def e19Exit (f : ReportFacts) : Option Nat :=
  if f.allInScopeUncited then some exitNotConforming else none

/-- D-45 (v1.19, confirmed) — "a `failed` proof trips `--strict` only when `--proof-results` was
given and is readable". -/
def d45StrictFails (f : ReportFacts) (strict : Bool) : Bool :=
  strict && f.proofFailedWithManifest

/-! ## C-27 (v1.25) — the hazard roll-up -/

/-- C-27 — the three hazard statuses. -/
inductive HazardStatus where
  | verified | notVerified | uncontrolled
  deriving DecidableEq, Repr

/-- C-27 — one declared id whose CONTROLS marker names the hazard: whether it is retired, and its
final C-05 status (after step 5). -/
structure Control where
  retired : Bool
  status : Status
  deriving DecidableEq, Repr

/-- C-27 — `CTRL(h)`: the non-retired controlling ids. -/
def liveControls (cs : List Control) : List Control := cs.filter (fun c => !c.retired)

/-- C-27 — `UNCONTROLLED` if `CTRL(h)` is empty; `VERIFIED` if every id in it is `PASSING`
(`WEAKLY_PASSING` is not); else `NOT_VERIFIED`. A risk-file hazard no marker names is the empty
list. -/
def hazardStatus (cs : List Control) : HazardStatus :=
  match liveControls cs with
  | [] => .uncontrolled
  | live => if live.all (fun c => c.status == .passing) then .verified else .notVerified

/-! ## C-26 (v1.25) — `verify`'s exit codes -/

/-- C-26, E-82, E-83 — what a `verify` run meets: a usage fault (E-82), a malformed manifest
(E-83), or a well-formed manifest whose files were re-hashed, `differing` of them missing or
changed. -/
inductive VerifyInput where
  | usageFault
  | malformedManifest
  | checked (differing : Nat)
  deriving DecidableEq, Repr

/-- §5.4, C-26 — `0` every file matches, `1` one or more is missing or differs, `2` usage, `3`
malformed manifest. -/
def verifyExit : VerifyInput → Nat
  | .usageFault => exitUsage
  | .malformedManifest => exitContract
  | .checked 0 => exitConforming
  | .checked (_ + 1) => exitNotConforming

/-- E-82, E-83 — whether any file the manifest names is read: only once the manifest is
well-formed ("no input file is read (a manifest cannot direct a read outside the tree)"). -/
def verifyReadsInputs : VerifyInput → Bool
  | .checked _ => true
  | _ => false

/-! ## C-29, R-111 (v1.26) — the qualification verdict and its first failure -/

/-- C-29, R-112 — the facts the verdict reads: whether `package_tree_sha256` is non-null, the
sizes of the three IQ lists, and the catalog's results in order (`true` = `PASS`). -/
structure IQFacts where
  treePresent : Bool
  dataFaults : Nat
  mismatches : Nat
  missing : Nat
  casesPass : List Bool
  deriving DecidableEq, Repr

/-- C-29 — the failure kinds, one per clause of the first-failure order. -/
inductive QualFailure where
  | notWheel | dataFault | recordMismatch | recordMissing | caseFail
  deriving DecidableEq, Repr

/-- C-29 — "first failure (R-111's stdout line), the first that applies, in this order": E-86,
the first data fault (E-87), the first RECORD mismatch, the first RECORD missing, the first failing
case (E-88). `none` = nothing failed. -/
def firstFailure (q : IQFacts) : Option QualFailure :=
  if !q.treePresent then some .notWheel
  else if q.dataFaults ≠ 0 then some .dataFault
  else if q.mismatches ≠ 0 then some .recordMismatch
  else if q.missing ≠ 0 then some .recordMissing
  else if q.casesPass.all id then none
  else some .caseFail

/-- C-29 — the verdict sentence, transcribed separately from the order above: "`QUALIFIED` iff
package_tree_sha256 is non-null, all three IQ lists are empty, and every `oq` result is `PASS`". -/
def verdictQualified (q : IQFacts) : Bool :=
  q.treePresent && q.dataFaults == 0 && q.mismatches == 0 && q.missing == 0 && q.casesPass.all id

/-- R-111 — exit `0` when every IQ check and OQ case passed, else `1` (the usage and `--out`
faults are `Fault` rows). -/
def qualifyExit (q : IQFacts) : Nat :=
  if verdictQualified q then exitConforming else exitNotConforming

/-! ## R-115, C-31 (v1.26) — which known anomalies a record lists -/

/-- C-31 — `X.Y.Z`. -/
structure Version where
  major : Nat
  minor : Nat
  patch : Nat
  deriving DecidableEq, Repr

/-- R-115 — "a version later than the running one (compared as three integers)". -/
def verLt (a b : Version) : Bool :=
  a.major < b.major || (a.major == b.major &&
    (a.minor < b.minor || (a.minor == b.minor && a.patch < b.patch)))

/-- C-31 — the field the selection reads. -/
structure Anomaly where
  fixedIn : Option Version
  deriving DecidableEq, Repr

/-- R-115 — "every entry whose `fixed_in` is `null` or a version later than the running one",
in file order. -/
def openAnomalies (running : Version) (as : List Anomaly) : List Anomaly :=
  as.filter (fun a => match a.fixedIn with
    | none => true
    | some f => verLt running f)

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
  strictJudgeHolds exitOfCheck strictJudgeFailure exitPrecedence
  barCells bar remainingSeconds
  Fault.isUsage Fault.isContract
  outcome
  proofStateOf statusWithProof topLevelProofKeyPresent
  r15Holds summaryWord e19Exit d45StrictFails
  liveControls hazardStatus
  verifyExit verifyReadsInputs
  firstFailure verdictQualified qualifyExit
  verLt openAnomalies

end SpeccheckSpec.Speccheck.Model