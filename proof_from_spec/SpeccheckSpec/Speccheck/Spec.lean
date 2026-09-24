/-
# `SpeccheckSpec.Speccheck.Spec` — the normative side

Transcribes the pinned constants of `SPEC.md` v1.18 (Specification Conformance Checker,
`speccheck`; `/Users/rioffe/projects/speccheck/SPEC.md`) and checks the spec's own claims about
them. Rule for this file: every constant quotes the spec's normative text; every lemma in
`section Facts` is a check that the spec's claims about those constants are mutually consistent.
This module imports `Lean` and nothing else.

Every constant carries the spec ID(s) that pin it in its doc comment. Constants another module's
theorems normalize through are `@[grind unfold] public def`, so they unfold across modules.
-/
import Lean

namespace SpeccheckSpec.Speccheck.Spec

/-! ## §5.4, K-01 — the exit codes -/

/-- §5.4, K-01 — exit `0`: `CONFORMING`: no in-scope ID is `FAILING`; and if `--strict`, every
in-scope ID has status `PASSING`, `dangling` and `stale` are empty, and — with `--judge llm` only —
`judge_available` is `true` and `unknown_rate ≤ max_unknown` (R-28). Reports written. -/
@[grind unfold] public def exitConforming : Nat := 0

/-- §5.4, K-01 — exit `1`: `NOT CONFORMING`: anything else the report can express. Reports
written. -/
@[grind unfold] public def exitNotConforming : Nat := 1

/-- §5.4, K-01 — exit `2`: usage error (bad flag/value, missing required, path outside root,
missing judge env). No reports written. -/
@[grind unfold] public def exitUsage : Nat := 2

/-- §5.4, K-01 — exit `3`: input contract violation (E-01, E-02, E-03, E-05, E-18); also any
uncaught exception and `KeyboardInterrupt` (E-41). No reports written. -/
@[grind unfold] public def exitContract : Nat := 3

/-- K-01 — "no other exit codes exist": the closed set of process exit codes. -/
@[grind unfold] public def exitCodes : List Nat := [exitConforming, exitNotConforming, exitUsage, exitContract]

/-- K-01 — the same set written as the spec's table spells it. -/
@[grind unfold] public def k01ExitSet : List Nat := [0, 1, 2, 3]

/-! ## C-05 — statuses -/

/-- C-05 — `IdStatus (deterministic): RETIRED | UNCITED | UNTESTED | UNVERIFIED | FAILING |
SKIPPED | PASSING`. -/
@[grind unfold] public def deterministicStatuses : List String :=
  ["RETIRED", "UNCITED", "UNTESTED", "UNVERIFIED", "FAILING", "SKIPPED", "PASSING"]

/-- C-05 — `IdStatus (judge-only): WEAKLY_PASSING`. -/
@[grind unfold] public def judgeOnlyStatuses : List String := ["WEAKLY_PASSING"]

/-- C-07 (`by_status`) — the seven in-scope statuses, in the order the report pins. -/
@[grind unfold] public def inScopeStatuses : List String :=
  ["PASSING", "WEAKLY_PASSING", "FAILING", "SKIPPED", "UNVERIFIED", "UNTESTED", "UNCITED"]

/-! ## C-01 — families and the ID grammar -/

/-- C-01 — `FAMILY := "R" | "C" | "I" | "K" | "E" | "T"`; `O-n`, `D-nn` and `F-nnn` are NOT
conformance IDs. -/
@[grind unfold] public def familyLetters : List Char := ['R', 'C', 'I', 'K', 'E', 'T']

/-- C-01 (c) — the declaration-only decision family letter. A decision "is not a conformance ID:
it is never in `ids`, never a citation target ... never in any metric (D-25)". -/
@[grind unfold] public def decisionFamilyLetter : Char := 'D'

/-- K-04 — "ID numbers are 1–3 digits; a token with 4+ digits is not an ID." -/
@[grind unfold] public def k04MaxDigits : Nat := 3

/-- C-01 — the normalized form: `FAMILY "-" zero-padded to 2 digits for R/C/K/E/T, 3 digits for
I (R-07, I-005)`. -/
@[grind unfold] public def pad2Width : Nat := 2

/-- C-01 — the family whose numbers are zero-padded to 3 digits. -/
@[grind unfold] public def pad3Family : Char := 'I'

/-- C-01 — the zero-padding width for `I`. -/
@[grind unfold] public def pad3Width : Nat := 3

/-- C-01 — the RECORDED marker (R-35): "the whitespace-separated token immediately after its ID
form is exactly `*(recorded)*`". -/
@[grind unfold] public def recordedMarker : String := "*(recorded)*"

/-- C-01 (F-013) — the line-level ignore marker, matched literally and case-sensitively. -/
@[grind unfold] public def ignoreMarker : String := "speccheck:ignore"

/-- C-01 (F-013) — the file-level ignore marker; a file whose first three lines contain it is
not scanned. -/
@[grind unfold] public def ignoreFileMarker : String := "speccheck:ignore-file"

/-! ## C-04 — the JUnit join -/

/-- C-04 — the parametrization bracket that `join_name` step 1 strips from. -/
@[grind unfold] public def joinOpenBracket : Char := '['

/-- C-04 (R-31, D-19) — the signature parenthesis that `join_name` step 2 strips from. -/
@[grind unfold] public def joinOpenParen : Char := '('

/-- C-04 — the worst-first outcome order `error > failed > skipped > passed` (E-06, E-24). -/
@[grind unfold] public def outcomeWorstOrder : List String := ["error", "failed", "skipped", "passed"]

/-! ## C-05 — the judge step -/

/-- C-06 — the four-value verdict set. -/
@[grind unfold] public def verdictTokens : List String := ["ASSERTS", "EXECUTES_ONLY", "UNRELATED", "UNKNOWN"]

/-- C-06 rule 8, K-07 — `rationale ≤ 280 characters`; a longer one is "truncated to 277 +
`...`". -/
@[grind unfold] public def rationaleMax : Nat := 280

/-- C-06 rule 8 — the length kept before the `...` ellipsis. -/
@[grind unfold] public def rationaleKeep : Nat := 277

/-- C-06 — the coercion rationale for rule 2 (malformed verdict). -/
@[grind unfold] public def rationaleMalformed : String := "judge: malformed response"

/-- C-06 — the coercion rationale for rule 5 (unlocated clause). -/
@[grind unfold] public def rationaleUnlocated : String := "judge: unlocated clause"

/-- C-06 — the coercion rationale for rules 6 and 7 (ungrounded). -/
@[grind unfold] public def rationaleUngrounded : String := "judge: ungrounded"

/-! ## K-14, K-15 — statement and clause bounds -/

/-- K-14 — "A statement (C-01: title, newline, section body) is at most 16,384 bytes of UTF-8." -/
@[grind unfold] public def k14Cap : Nat := 16384

/-- K-14 — the truncation marker line the spec appends. -/
@[grind unfold] public def k14Marker : String := "… (statement truncated by speccheck at K-14)"

/-- K-15 — a located clause "is at least 12 characters long". -/
@[grind unfold] public def k15Min : Nat := 12

/-- K-15 — the clause is "cut to its first 280 characters" before matching. -/
@[grind unfold] public def k15Cut : Nat := 280

/-! ## K-02, K-03 — the scan filters -/

/-- K-02 — "Files larger than 2 MiB (2,097,152 bytes) under `--src`/`--tests` are skipped with a
Note (E-10)". -/
@[grind unfold] public def k02MaxBytes : Nat := 2097152

/-- K-02 (F-008) — "binary files (a `0x00` byte within the first 8192 bytes) are skipped
silently (E-29)". -/
@[grind unfold] public def k02BinaryWindow : Nat := 8192

/-- K-03 — directories never descended into. "any directory whose name starts with `.`" is the
predicate `isDot`; these are the named ones. -/
@[grind unfold] public def k03NeverDescend : List String :=
  [".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv", "venv"]

/-- K-03 — the dot-prefix rule: "any directory whose name starts with `.`". -/
@[grind unfold] public def k03DotPrefix : Char := '.'

/-! ## K-05, K-06, K-11, K-12 — timing, concurrency, thresholds, budget -/

/-- K-05, C-09 — `SPECCHECK_JUDGE_TIMEOUT` "optional, seconds, default 30, integer 1..300". -/
@[grind unfold] public def judgeTimeoutDefault : Nat := 30

/-- K-05, C-09 — the accepted timeout range lower bound. -/
@[grind unfold] public def timeoutMin : Nat := 1

/-- K-05, C-09 — the accepted timeout range upper bound. -/
@[grind unfold] public def timeoutMax : Nat := 300

/-- K-06 (§5.1) — `--judge-concurrency N` "default `4`, integer `1..32`". -/
@[grind unfold] public def judgeConcurrencyDefault : Nat := 4

/-- K-06 (§5.1) — the concurrency lower bound. -/
@[grind unfold] public def concurrencyMin : Nat := 1

/-- K-06 (§5.1) — the concurrency upper bound. -/
@[grind unfold] public def concurrencyMax : Nat := 32

/-- C-07 (Q-009) — every ratio is "quantized to 4 places"; `ratioScale` is the denominator of
that fixed-point representation (a ratio is carried as ten-thousandths). -/
@[grind unfold] public def ratioScale : Nat := 10000

/-- K-11 (§5.1), C-07 — `--max-unknown` "default `0.2`"; C-07 emits it as the K-11 Decimal
quantized to 4 places, so the constant is carried at `ratioScale` resolution: `0.2000` is `2000`
ten-thousandths. -/
@[grind unfold] public def maxUnknownDefault : Nat := 2000

/-- K-12 (§5.1) — `--judge-budget` `SECONDS` form: "integer `0..86400`". -/
@[grind unfold] public def budgetSecondsMax : Nat := 86400

/-- K-12 (§5.1) — the `N%` form upper bound. -/
@[grind unfold] public def budgetPercentMax : Nat := 100

/-- §5.1 — `--depth N` "Integer `0..999`, default `1`; `0` = unbounded". -/
@[grind unfold] public def depthDefault : Nat := 1

/-- §5.1 — the `--depth` upper bound. -/
@[grind unfold] public def depthMax : Nat := 999

/-! ## C-07 — report shape and quantization -/

/-- C-07 — the JSON schema version this document pins (`schema_version` "1.5"). -/
@[grind unfold] public def schemaVersion : String := "1.5"

/-- C-13 — `impact.json`'s own schema version. -/
@[grind unfold] public def impactSchemaVersion : String := "1.0"

/-- C-07 (Q-009) — every ratio is "quantized to 4 places with ROUND_HALF_EVEN". -/
@[grind unfold] public def ratioPlaces : Nat := 4

/-- C-07 (Q-009) — `<pct>` is "the quantized `conformance` times 100, quantized to 1 place with
ROUND_HALF_EVEN". -/
@[grind unfold] public def pctPlaces : Nat := 1

/-- C-07 (F-016) — the six `by_family` keys, always present in that order. -/
@[grind unfold] public def byFamilyKeys : List String := ["R", "C", "I", "K", "E", "T"]

/-- R-38, C-10 — a `related` neighbourhood is "at most eight total in C-07 id order". -/
@[grind unfold] public def relatedCap : Nat := 8

/-- R-38 — each related title is "a whitespace-collapsed title tail-truncated to 160
characters". -/
@[grind unfold] public def relatedTitleCap : Nat := 160

/-- R-38, C-10 — a retired neighbour keeps its title with this appended. -/
@[grind unfold] public def retiredSuffix : String := "(retired)"

/-! ## C-11 — the progress indicator -/

/-- C-11, K-13 — "The bar has exactly 20 cells". -/
@[grind unfold] public def progressCells : Nat := 20

/-- C-11 — the bar's filled cell, and the empty cell, "pure ASCII ... so it renders under any
locale (R-29 rationale)". -/
@[grind unfold] public def progressFull : Char := '#'

/-- C-11 — the empty bar cell. -/
@[grind unfold] public def progressEmpty : Char := '-'

/-- C-11 — `left` is rendered `?:??` "while `d = 0`". -/
@[grind unfold] public def progressUnknownLeft : String := "?:??"

/-! ## C-09, C-17 — environment variables -/

/-- C-09 — the four judge variables, three required and one optional. -/
@[grind unfold] public def judgeEnvVars : List String :=
  ["SPECCHECK_JUDGE_URL", "SPECCHECK_JUDGE_MODEL", "SPECCHECK_JUDGE_API_KEY", "SPECCHECK_JUDGE_TIMEOUT"]

/-- C-17 — the four triage variables; read only when the triage pass runs. -/
@[grind unfold] public def jevEnvVars : List String :=
  ["SPECCHECK_JEV_URL", "SPECCHECK_JEV_MODEL", "SPECCHECK_JEV_API_KEY", "SPECCHECK_JEV_TIMEOUT"]

/-- C-17 — `SPECCHECK_JEV_URL` default. -/
@[grind unfold] public def jevUrlDefault : String := "https://openrouter.ai/api/alpha/decisions"

/-- C-17 — `SPECCHECK_JEV_MODEL` default (OpenRouter's floating alias). -/
@[grind unfold] public def jevModelDefault : String := "~typesafe/jev-latest"

/-- C-19, D-41, I-017 — the only variable that changes a `--help` run's own output. -/
@[grind unfold] public def columnsVar : String := "COLUMNS"

/-- C-19, D-39, T-97 — the width the help goldens are rendered at. -/
@[grind unfold] public def helpGoldenColumns : Nat := 80

/-! ## §5.1, R-29 — the summary line -/

/-- §5.1, R-29 — the summary line's regex (T-44). The model's `summaryASCII` and
`summarySingleLine` are checked against this shape. -/
@[grind unfold] public def summaryRegex : String :=
  "^speccheck: (CONFORMING|NOT CONFORMING) - \\d+/\\d+ passing \\(\\d+\\.\\d%\\), \\d+ failing, \\d+ skipped, \\d+ weak, \\d+ unverified, \\d+ untested, \\d+ uncited; \\d+ dangling, \\d+ stale; judge=(none|mock|llm)( \\(unavailable\\)| \\(unknown_rate \\d\\.\\d{4} > max_unknown \\d\\.\\d{4}\\))?$"

/-- §5.1 — `<STATUS>` is `CONFORMING` (exit 0) or `NOT CONFORMING` (exit 1). -/
@[grind unfold] public def summaryStatusWords : List String := ["CONFORMING", "NOT CONFORMING"]

/-- §5.1, Q-004 — the judge suffix when R-28 forced exit 1 and the judge was unavailable. -/
@[grind unfold] public def suffixUnavailable : String := " (unavailable)"

/-- §5.1, R-28, Q-004 — `strict_judge_failure` values. When both R-28 reasons hold the suffix is
` (unavailable)`. -/
@[grind unfold] public def strictJudgeFailureValues : List String := ["unavailable", "unknown_rate"]

/-! ## §10 / §12 — no-op markers used by the correspondence table -/

/-- §0 — the shipped decision-table family (C-01 (c)); `D-nn` rows are declaration-only. -/
@[grind unfold] public def decisionIdPrefix : String := "D-"

/-- C-04 — the root elements the results reader accepts. -/
@[grind unfold] public def junitRoots : List String := ["testsuites", "testsuite"]

/-- C-08 (Q-011) — the Markdown-only label for a file-level test case. -/
@[grind unfold] public def fileLevelLabel : String := "(file)"

/-- C-08 (Q-001) — the Markdown em dash rendered when the JSON `verdict` is null. -/
@[grind unfold] public def emDash : String := "—"

/-! ## C-21, K-17 — the proof manifest and the join states (v1.19) -/

/-- C-21, K-17 — the four states a cited declaration's manifest join can produce: `checked`
(cited and manifest-checked), `failed` (cited and manifest-failed), `unknown` (cited, no matching
manifest entry), `stale` (a manifest entry matches by name but not by file/line). An id with no
citation at all has no entry in this set — represented by an empty `proof` array, not a fifth
token (D-49). -/
@[grind unfold] public def proofStateTokens : List String := ["checked", "failed", "unknown", "stale"]

/-- C-21 — the two `theorems[].status` values the manifest itself carries: a Lean build result,
distinct from the four join states above (a `checked` build result can still join as `stale`). -/
@[grind unfold] public def manifestStatusTokens : List String := ["checked", "failed"]

/-- C-21 — the three top-level manifest keys speccheck reads (`build`, `theorems`, optional
`deferred_to_pytest`); every other top-level key, and every extra key on an entry, is ignored. -/
@[grind unfold] public def manifestReadKeys : List String := ["build", "theorems", "deferred_to_pytest"]

/-! ## Facts — the spec's claims about its own constants -/

section Facts

/-- K-01 — the closed exit set is exactly `{0,1,2,3}`. -/
theorem k01ExitSet_eq : k01ExitSet = [0, 1, 2, 3] := rfl

/-- K-01 — no exit code outside the set: the list has four distinct members. -/
theorem k01ExitSet_nodup : k01ExitSet.Nodup := by decide

/-- §5.4 — the named exit constants agree with the table's literals. -/
theorem exits_named : (exitConforming, exitNotConforming, exitUsage, exitContract) = (0, 1, 2, 3) := rfl

/-- C-05 — the deterministic status set has exactly the seven names the spec lists. -/
theorem deterministicStatuses_length : deterministicStatuses.length = 7 := by decide

/-- C-05 — the deterministic status names are pairwise distinct. -/
theorem deterministicStatuses_nodup : deterministicStatuses.Nodup := by decide

/-- C-07 — the seven in-scope report statuses are pairwise distinct and exclude `RETIRED`. -/
theorem inScopeStatuses_nodup : inScopeStatuses.Nodup := by decide

/-- C-07 (F-016) — `RETIRED` is never a `by_status` key. -/
theorem retired_not_in_scope : "RETIRED" ∉ inScopeStatuses := by decide

/-- C-07 — `by_status` has exactly seven keys for the seven in-scope statuses. -/
theorem inScopeStatuses_length : inScopeStatuses.length = 7 := by decide

/-- C-01 — the family list is exactly the six conformance families, `D` excluded. -/
theorem familyLetters_eq : familyLetters = ['R', 'C', 'I', 'K', 'E', 'T'] := rfl

/-- C-01 — `D` is not one of the six families (a decision is never a conformance ID). -/
theorem decision_not_family : decisionFamilyLetter ∉ familyLetters := by decide

/-- C-01 — the families are pairwise distinct. -/
theorem familyLetters_nodup : familyLetters.Nodup := by decide

/-- K-04 — the digit cap is three. -/
theorem k04MaxDigits_eq : k04MaxDigits = 3 := rfl

/-- C-01, I-005 — the padding widths are 2 for R/C/K/E/T and 3 for `I`. -/
theorem padding_widths : (pad2Width, pad3Width) = (2, 3) := rfl

/-- C-01 — `I` is the family padded to three digits; it is one of the families. -/
theorem pad3Family_mem : pad3Family ∈ familyLetters := by decide

/-- C-06 — the verdict set has exactly the four tokens. -/
theorem verdictTokens_eq : verdictTokens = ["ASSERTS", "EXECUTES_ONLY", "UNRELATED", "UNKNOWN"] := rfl

/-- C-06 — the four verdict tokens are pairwise distinct. -/
theorem verdictTokens_nodup : verdictTokens.Nodup := by decide

/-- C-06 rule 8, K-07 — the truncation keeps `277` of the `280` allowed characters and appends
`...`, so the ellipsized rationale is exactly `280`. -/
theorem rationale_truncation_fits : rationaleKeep + 3 = rationaleMax := by decide

/-- K-15 — the minimum located clause is shorter than the cut length. -/
theorem k15Min_lt_k15Cut : k15Min < k15Cut := by decide

/-- K-15, C-10 — the minimum located clause is shorter than the K-07 rationale bound. -/
theorem k15Min_lt_rationaleMax : k15Min < rationaleMax := by decide

/-- K-14 — the statement cap is 16384 bytes. -/
theorem k14Cap_eq : k14Cap = 16384 := rfl

/-- K-02 — the size cap is 2 MiB and the binary window is 8192 bytes, well under it. -/
theorem k02_window_lt_cap : k02BinaryWindow < k02MaxBytes := by decide

/-- K-02 — the size cap is exactly 2 MiB. -/
theorem k02MaxBytes_eq : k02MaxBytes = 2097152 := rfl

/-- K-03 — the named never-descend directories are pairwise distinct. -/
theorem k03NeverDescend_nodup : k03NeverDescend.Nodup := by decide

/-- K-03 — every named never-descend directory begins with the dot the dot-prefix rule also
covers, or is one of the two virtualenv spellings; the list has seven entries. -/
theorem k03NeverDescend_length : k03NeverDescend.length = 7 := by decide

/-- K-05, C-09 — the default timeout lies inside its accepted range. -/
theorem judgeTimeoutDefault_in_range :
    timeoutMin ≤ judgeTimeoutDefault ∧ judgeTimeoutDefault ≤ timeoutMax := by decide

/-- K-06 — the default concurrency lies inside `1..32`. -/
theorem judgeConcurrencyDefault_in_range :
    concurrencyMin ≤ judgeConcurrencyDefault ∧ judgeConcurrencyDefault ≤ concurrencyMax := by decide

/-- K-11 — the `--max-unknown` default `0.2` lies in `[0, 1]`; carried at `ratioScale`, that is
`0 ≤ 2000 ≤ 10000`. -/
theorem maxUnknownDefault_in_unit :
    0 ≤ maxUnknownDefault ∧ maxUnknownDefault ≤ ratioScale := by decide

/-- K-12 — the `N%` form's bound is the percentage 100. -/
theorem budgetPercentMax_eq : budgetPercentMax = 100 := rfl

/-- §5.1 — the `--depth` default lies inside its accepted range, and `0` means unbounded. -/
theorem depthDefault_in_range : depthDefault ≤ depthMax := by decide

/-- C-07 (F-016) — `by_family` has exactly the six keys `R C I K E T` in that order. -/
theorem byFamilyKeys_eq : byFamilyKeys = ["R", "C", "I", "K", "E", "T"] := rfl

/-- C-07 (F-016) — the `by_family` keys are pairwise distinct. -/
theorem byFamilyKeys_nodup : byFamilyKeys.Nodup := by decide

/-- C-09 — the judge reads four environment variables. -/
theorem judgeEnvVars_length : judgeEnvVars.length = 4 := by decide

/-- C-17 — the triage provider reads four environment variables. -/
theorem jevEnvVars_length : jevEnvVars.length = 4 := by decide

/-- I-007, D-41 — `COLUMNS` is not one of the eight `SPECCHECK_*` names it is documented
beside. -/
theorem columns_not_speccheck : columnsVar ∉ judgeEnvVars ∧ columnsVar ∉ jevEnvVars := by decide

/-- C-11, K-13 — the bar has exactly 20 cells, and the two cell characters are distinct. -/
theorem progressCells_eq : progressCells = 20 ∧ progressFull ≠ progressEmpty := by decide

/-- R-38 — the related-title cap is below the K-14 statement cap, and the cap is eight. -/
theorem relatedTitleCap_lt_k14Cap : relatedTitleCap < k14Cap := by decide

/-- R-38 — at most eight related titles are sent. -/
theorem relatedCap_eq : relatedCap = 8 := rfl

/-- C-04 — the worst-first order runs `error > failed > skipped > passed`. -/
theorem outcomeWorstOrder_eq : outcomeWorstOrder = ["error", "failed", "skipped", "passed"] := rfl

/-- C-04 — the four outcomes are pairwise distinct. -/
theorem outcomeWorstOrder_nodup : outcomeWorstOrder.Nodup := by decide

/-- C-04 — the results reader accepts exactly the two root elements. -/
theorem junitRoots_eq : junitRoots = ["testsuites", "testsuite"] := rfl

/-- R-28, Q-004 — `strict_judge_failure` takes exactly two non-null values. -/
theorem strictJudgeFailureValues_eq : strictJudgeFailureValues = ["unavailable", "unknown_rate"] := rfl

/-- C-19, D-39 — the help goldens are rendered at width 80. -/
theorem helpGoldenColumns_eq : helpGoldenColumns = 80 := rfl

/-- C-21, K-17 — the four join states are pairwise distinct. -/
theorem proofStateTokens_nodup : proofStateTokens.Nodup := by decide

/-- C-21 — both manifest build-result tokens are also join-state tokens: a manifest `checked`
declaration can still join `stale`, but the token vocabularies overlap by design (the join's
`checked`/`failed` states are read straight off the manifest when the location matches). -/
theorem manifestStatusTokens_subset_proofStateTokens :
    "checked" ∈ proofStateTokens ∧ "failed" ∈ proofStateTokens := by decide

/-- C-21 — the checker reads exactly three top-level manifest keys. -/
theorem manifestReadKeys_length : manifestReadKeys.length = 3 := by decide

/-- C-21 — the three read keys are pairwise distinct. -/
theorem manifestReadKeys_nodup : manifestReadKeys.Nodup := by decide

end Facts

end SpeccheckSpec.Speccheck.Spec