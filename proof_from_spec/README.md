# speccheck — spec model

Lean 4 formalization of what [`SPEC.md`](../SPEC.md) v1.20 *says* — its normative tables as a pure
total function, with the spec's own claims about itself kernel-checked.

> **There is no implementation.** This certifies the *spec*, not a system. Lean proves the model; it
> cannot read a document, and there is no program here to read either. The spec's §9 tests are
> **planned**, not run — every requirement out of Lean's reach is mapped to the `T-nn` that will
> carry it. Nothing here says anything about any implementation.

## Layout

- `SpeccheckSpec/Speccheck/Spec.lean` — the **spec side**: the pinned constants (exit codes `0..3`,
  the eight status names, the six families, the four verdict tokens, the K-14/K-15/K-07 bounds, the
  K-02/K-03 scan filters, the C-07 quantization, the C-09/C-17 environment names, the C-11 cell
  count), each quoting the spec ID it comes from, plus `section Facts`: the spec's own claims about
  those constants, each closed by `decide`.
- `SpeccheckSpec/Speccheck/Model.lean` — the **model**: the ID grammar and normalization (C-01,
  I-011), the two-step `join_name` and worst-of (C-04), the status algorithm `statusOf` with its
  five steps (C-05), the validation cascade `coerce` (C-06), the ratios and `judge_available`
  (C-07, now total and boolean under `mock`/`llm` — amended v1.20), the exit map `exitOfCheck`
  (§5.4, R-14, R-15, R-28) and the usage-first precedence function `exitPrecedence` (K-18, v1.20),
  the progress arithmetic (C-11), the proof-evidence join `proofStateOf` and the
  proof-never-changes-status wrapper `statusWithProof` (v1.19, C-21, K-17, E-63), and
  `outcome : Input → Option Result` — now **total** over every constructor (v1.20, E-64), where
  `none` still **means the spec states no outcome** for any future input space that grows. The
  correspondence table (spec anchor → model element) is its header — the manual trust boundary,
  including every table deliberately *not* modelled and why.
- `SpeccheckSpec/Speccheck/Theorems.lean` — **the proof**: `section Rows` (transcription of the
  spec's tables — not evidence, and it says so), `section Invariants` (the "for all inputs"
  theorems: the closed exit set, downgrade-only judging, grounded verdicts, `null`-on-zero
  denominators, the bar's bounds, coverage (`noSilence`, v1.20) and usage-fault precedence
  (`k18UsageWinsWhenBoth`, v1.20)), `section Reachability` (all four exit codes reached), the
  findings' witnesses, and the map of every out-of-Lean row to the §9 test that will carry it.

## Commands

    lake build            # checks every proof (Lean v4.34.0, pinned in lean-toolchain)

## What "proven" means here

Lean proves the **model**. It cannot read a document, and there is no program to read either. The
bridge has two legs, and this project is only one of them:

- **Leg A — transcription** (manual): the correspondence table in `Model.lean`, anchor by anchor.
  `section Rows`' theorems exist so the ID-to-declaration join is complete, not because they prove
  anything.
- **Leg B — Lean** (kernel-checked): the claims the spec makes *about itself*, for all inputs —
  coverage, the closed exit set, the diagnostics/verdict contracts, the metrics' zero-denominator
  rules.
- **Leg C — empirical** (does not exist): the system the spec describes. No implementation; the §9
  suite is planned.

Overclaiming leg B as leg C is the one error this project must not make.

## Findings

Four findings, **all resolved** — see
[`docs/reviews/SPEC_MODEL_FINDINGS.md`](../docs/reviews/SPEC_MODEL_FINDINGS.md):

- **F-501 (G-1, P1) — resolved v1.20.** `explain` without `--spec` was an enumerated input with no
  stated outcome (§5.1's synopsis made `--spec` optional for `explain`; its table called it
  required; no default was given). `outcome .explainAbsentSpec = none` no longer typechecks as a
  fact about the resolved model; `f501ResolvedExplainAbsentSpecUsage` proves it now reads E-64's
  outcome, and `noSilence` proves coverage is total over the whole `Input` type.
- **F-502 (G-2, P1) — resolved v1.20.** `judge_available` was undetermined when judge-eligible
  edges existed but no call was issued (K-12/E-35), and the `--strict --judge llm` exit code
  inherited the gap. `judgeAvailable` is now total and boolean under `mock`/`llm`
  (`judgeAvailableNullIffNone`); `f502ResolvedJudgeAvailableBudgetFalse` proves the old silent
  configurations now read `some false`, and `f502ResolvedStrictJudgeFailureUnavailable` proves the
  same exit code now carries the honest `"unavailable"` reason instead of `null`.
- **F-503 (G-2, P2) — resolved v1.20.** §5.4/K-01 gave no precedence when one run carried both a
  usage fault (`2`) and a contract violation (`3`). `exitPrecedence` is now the single, spec-named
  model (K-18, usage-first); `k18UsageWinsWhenBoth` proves it holds for every contract-fault value,
  not just one instance. `f503ExitPrecedenceDiffer` is kept as the historical ambiguity record.
- **F-504 (G-2, P2, v1.19) — resolved v1.19.1, same session.** The top-level `proof` key's
  presence was tied to `--proof` alone (C-07/D-49), so `--proof-results` given without `--proof`
  read a manifest whose `build` result was never written anywhere in the report. D-49 was amended
  before any implementation existed to gate the key on `--proof ∨ --proof-results`; this model was
  resynced to match. Witness: `f504ResolvedManifestAloneWritesKey`.

Every "resolved" theorem above replaces one whose *old* statement no longer typechecks as a fact
about the corrected model — that non-typechecking is the fix's proof, not an assertion of it; each
old witness's name and context are preserved in its replacement's doc comment.

Scope: 267 declared IDs — **60 proven**, **104 deferred-only** (each naming its planned `T-nn`
carriers), **103 `T-nn`** (the test inventory), **9 named exclusions** — its partition checked
mechanically. v1.19 added the proof-evidence join (`proofStateOf`, `statusWithProof`; C-21, K-17,
E-63 proven; R-100, C-20, I-018, E-62, E-65 deferred to T-99/T-100). v1.20 added `judge_available`
totality and usage-fault precedence (E-35 newly dual, K-18 and E-64 proven-and-dual from the
start; T-101..T-103 deferred) over the v1.18 baseline. Findings are reported, not fixed: this
project does not edit `SPEC.md`.