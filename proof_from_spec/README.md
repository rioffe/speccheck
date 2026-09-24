# speccheck — spec model

Lean 4 formalization of what [`SPEC.md`](../SPEC.md) v1.19 *says* — its normative tables as a pure
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
  (C-07), the exit map `exitOfCheck` (§5.4, R-14, R-15, R-28), the progress arithmetic (C-11), the
  proof-evidence join `proofStateOf` and the proof-never-changes-status wrapper `statusWithProof`
  (v1.19, C-21, K-17, E-63), and `outcome : Input → Option Result`, where `none` **means the spec
  states no outcome**. The correspondence table (spec anchor → model element) is its header — the
  manual trust boundary, including every table deliberately *not* modelled and why.
- `SpeccheckSpec/Speccheck/Theorems.lean` — **the proof**: `section Rows` (transcription of the
  spec's tables — not evidence, and it says so), `section Invariants` (the "for all inputs"
  theorems: the closed exit set, downgrade-only judging, grounded verdicts, `null`-on-zero
  denominators, the bar's bounds), `section Reachability` (all four exit codes reached), the
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

Three open spec-precision gaps and one resolved one, each with a kernel-checked witness — see
[`docs/reviews/SPEC_MODEL_FINDINGS.md`](../docs/reviews/SPEC_MODEL_FINDINGS.md):

- **F-501 (G-1, P1, open)** — `explain` without `--spec` is an enumerated input with no stated
  outcome (§5.1's synopsis makes `--spec` optional for `explain`; its table calls it required; no
  default is given). Witness: `f501ExplainAbsentSpecSilent`, `f501NoSilenceFails`.
- **F-502 (G-2, P1, open)** — `judge_available` is undetermined when judge-eligible edges exist but
  no call was issued (K-12/E-35), and the `--strict --judge llm` exit code inherits the gap.
  Witness: `f502JudgeAvailableBudgetSilent`, `f502Contrast`, `f502StrictJudgeFailureNull`.
- **F-503 (G-2, P2, open)** — §5.4/K-01 give no precedence when one run carries both a usage fault
  (`2`) and a contract violation (`3`). Witness: `f503ExitPrecedenceDiffer`.
- **F-504 (G-2, P2, v1.19) — resolved v1.19.1, same session.** The top-level `proof` key's
  presence was tied to `--proof` alone (C-07/D-49), so `--proof-results` given without `--proof`
  read a manifest whose `build` result was never written anywhere in the report. D-49 was amended
  before any implementation existed to gate the key on `--proof ∨ --proof-results`; this model was
  resynced to match. The old buggy behavior no longer typechecks as a fact about this model
  (`topLevelProofKeyPresent false true` is `true`, not `false`) — that non-typechecking *is* the
  fix's proof. Witness: `f504ResolvedManifestAloneWritesKey` (the original
  `f504ManifestReadButKeyAbsent` witness and its context are preserved in the theorem's doc
  comment). F-501–503 remain open, unrelated to this fold.

Scope: 262 declared IDs — **57 proven**, **105 deferred** (each naming its planned `T-nn`
carriers), **100 `T-nn`** (the test inventory), **9 named exclusions** — its partition checked
mechanically. v1.19 added the proof-evidence join (`proofStateOf`, `statusWithProof`; C-21, K-17,
E-63 proven; R-100, C-20, I-018, E-62, E-65 deferred to T-99/T-100) over the v1.18 baseline.
Findings are reported, not fixed: this project does not edit `SPEC.md`.