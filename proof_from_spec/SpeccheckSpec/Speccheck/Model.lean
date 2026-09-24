/-
# `SpeccheckSpec.Speccheck.Model` — the transcription

The normative tables of `SPEC.md` v1.18 (Specification Conformance Checker, `speccheck`) as pure,
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
| C-07 `judge_available` (E-14, E-36) | `JudgeMode`, `JudgeCalls`, `judgeAvailable` | partial in one configuration — finding F-502 |
| §5.4 exit map, R-14, R-15 | `ReportFacts`, `exitOfCheck`, `strictJudgeHolds` | pure function of report content + `--strict` |
| R-28, E-32, Q-004 | `strictJudgeFailure` | `unavailable` takes precedence |
| C-11 | `barCells`, `bar`, `remainingSeconds` | `k = ⌊20d/n⌋`; `left = t(n−d)/d` |
| §5.1 CLI surface, §5.4 | `Subcommand`, `Fault`, `Input`, `Result`, `outcome` | one `Fault` constructor per usage/contract row, one `Input` constructor per decision case |
| E-41 | `Input.interrupt` | exit 3, no report survives |
| E-01/E-02/E-03/E-05/E-18 | `Fault.specZeroIds` … `Fault.outNotWritable` | the exit-3 set of §5.4 |
| E-09/E-21/E-52/E-53/E-54/E-58/E-60; §5.1 bad values | the usage `Fault` constructors | the exit-2 set |
| C-21, K-17 (v1.19) | `ProofState`, `ProofJoin`, `proofStateOf` | manifest-to-citation join: `checked`/`failed`/`unknown`/`stale`, `none` for no citation (D-49) |
| E-63 (v1.19) | `statusWithProof`, `statusWithProof_ignoresProof` | proof is not a field of `Evidence`, so a wrapper that accepts it provably returns `statusOf`'s answer unchanged |
| C-07, D-49 (v1.19) | `topLevelProofKeyPresent` | finding F-504 |

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

/-- C-07, E-14, E-36 — `judge_available`: null when `--judge none`; otherwise "true when at
least one judge call succeeded OR no edge was eligible (vacuously available), and false only when
every call failed". Partial: the configuration `eligible > 0`, `issued = 0` — every eligible
edge budget-skipped by K-12/E-35, so no call was made and none failed — is covered by neither
clause; see finding F-502. -/
def judgeAvailable (c : JudgeCalls) : Option Bool :=
  match c.mode with
  | .none => none
  | .mock | .llm =>
    if decide (1 ≤ c.succeeded) ∨ c.eligible = 0 then some true
    else if 0 < c.issued then some false
    else none

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
  deriving DecidableEq, Repr

/-- R-15, R-28, §5.4 — the strict judge gate: with `--judge llm` the judge must be available and
`unknown_rate` must not exceed `--max-unknown`; otherwise no judge condition applies. -/
def strictJudgeHolds (f : ReportFacts) : Bool :=
  !f.judgeLlm ∨ (f.judgeAvailable = some true ∧ !f.unknownRateExceeds)

/-- §5.4, R-14, R-15 — the exit code of a `check` run: `0` iff no in-scope ID is `FAILING` and,
under `--strict`, every in-scope ID is `PASSING`, `dangling` and `stale` are empty, and the R-28
judge gate holds; else `1`. -/
def exitOfCheck (f : ReportFacts) (strict : Bool) : Nat :=
  if !f.anyInScopeFailing ∧
     (!strict ∨ (f.allInScopePassing ∧ !f.anyDangling ∧ !f.anyStale ∧ strictJudgeHolds f))
  then exitConforming else exitNotConforming

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
  | check | impact | explain | selfCheck | version | help
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
default. -/
def outcome : Input → Option Result
  | .check f strict => some { exit := exitOfCheck f strict, reports := true }
  | .impactEmptyChanged => some { exit := exitConforming, reports := true }
  | .explainDeclared => some { exit := exitConforming, reports := false }
  | .explainUndeclared => some { exit := exitUsage, reports := false }
  | .fault x => some { exit := if x.isUsage then exitUsage else exitContract, reports := false }
  | .explainAbsentSpec => none
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

/-- C-07, D-49 — whether the top-level `proof` key (and therefore its `build` echo) is written:
the pinned rule ties it to `--proof` alone, not to `--proof-results` — see finding F-504. -/
def topLevelProofKeyPresent (proofGiven _proofResultsGiven : Bool) : Bool := proofGiven

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
  proofStateOf statusWithProof topLevelProofKeyPresent

end SpeccheckSpec.Speccheck.Model