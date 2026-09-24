# speccheck proof

Lean 4 formalization of the **deterministic core** of [`src/speccheck/`](../src/speccheck/) —
the implementation of [`SPEC.md`](../SPEC.md) v1.18 — with a green acceptance suite
(`uv run python -m pytest tests -q`) carrying the rest.

> **The trust boundary, up front.** Lean proves the **model** in `Model.lean` — a pure Lean
> transcription of `graph.py`, `judge.py`, `results.py`, `report.py`, `extract.py` and
> `judge_mock.py` — never the `.py` files themselves. The bridge has three legs:
>
> | Leg | Claims | Evidence |
> | --- | --- | --- |
> | 1. Transcription | the model is a faithful transcription of the source file | **manual** — the correspondence table in `Model.lean`'s header, function by function |
> | 2. **Lean (this project)** | the model satisfies the spec's module-level contract, for all inputs | `lake build` — kernel-checked theorems |
> | 3. Empirical | the *file* satisfies the process-level contract | `tests/test_01_extraction.py` … `tests/test_13_help.py` (the §9 acceptance suite) |
>
> Overclaiming leg 2 as leg 1 or leg 3 is the one sin of proof work. This README, and every file
> in this project, keeps the three separate.

## Relationship to `proof_from_spec/`

[`../proof_from_spec/`](../proof_from_spec/) modelled `SPEC.md`'s own claims about itself, before
any implementation existed (`spec-model`). This project (`spec-proof`) was built after the fact,
by reading `src/speccheck/*.py` directly and checking that earlier model against the real code.
It matched almost line for line, with **one real discrepancy, fixed here**: `report.py`'s
`exit_code_for` (`report.py:82-97`) has an extra branch — every in-scope id `UNCITED` exits `1`
even without `--strict` (E-19) — that the general §5.4 prose doesn't mention and that
`proof_from_spec`'s `exitOfCheck` therefore omitted. `Model.lean`'s `ReportFacts`/`exitOfCheck`
here carry that branch (`allInScopeUncited`); `Theorems.lean` adds `row_exit_allUncited` and
`allUncitedAlwaysExitOne` for it.

## Layout

- `SpeccheckProof/Speccheck/Spec.lean` — the **spec side**: the pinned constants (exit codes
  `0..3`, the eight status names, the six families, the four verdict tokens, the K-14/K-15/K-07
  bounds, the K-02/K-03 scan filters, the C-07 quantization, the C-09/C-17 environment names, the
  C-11 cell count), each quoting the spec ID it comes from and, where it corresponds to one, the
  source constant it matches (e.g. `judge.RATIONALE_MAX`). `section Facts` checks the spec's own
  claims about those constants, each closed by `decide`.
- `SpeccheckProof/Speccheck/Model.lean` — the **model**: the ID grammar and normalization
  (`extract.normalize_id`), the two-step `join_name` and worst-of (`results.py`), the status
  algorithm `statusOf` (`graph.deterministic_status`/`graph.apply_verdicts`), the validation
  cascade `coerce` (`judge.validate`), the ratios and metrics (`graph.compute_metrics`), the exit
  map `exitOfCheck` (`report.exit_code_for`, `report.strict_judge_failure`), the progress
  arithmetic (`judge.progress_line`), and `outcome : Input → Option Result`, where `none` means
  the spec states no outcome for that input. The correspondence table is its header — the manual
  trust boundary, including every part of the source deliberately *not* modelled and why.
- `SpeccheckProof/Speccheck/Theorems.lean` — **the proof**: `section Rows` (one theorem per
  branch of the modelled functions — transcription, not evidence, and it says so),
  `section Invariants` (the "for all inputs" theorems: downgrade-only judging, grounded verdicts,
  `null`-on-zero denominators, the E-19 all-`UNCITED` exit rule, the bar's bounds),
  `section Reachability` (all four exit codes reached), and the closing deferral table mapping
  every out-of-Lean spec ID to the `tests/test_NN_*.py` file that actually exercises it today.

## Commands

    lake build            # checks every proof (Lean v4.34.0, pinned in lean-toolchain)

From the project root, the empirical leg:

    uv run python -m pytest tests -q --junitxml=junit.xml
    uv run speccheck check --spec SPEC.md --src src --tests tests --results junit.xml --judge mock

## What "proven" means here

Lean proves the **model** — a pure Lean function. It cannot execute or inspect
`src/speccheck/*.py`. The bridge is two-way: the model is a line-by-line transcription
(correspondence table in `Model.lean` — the manual trust boundary, re-read against the real
source rather than assumed), and the file is empirically verified by its test suite. Lean side:
module-level contract, all inputs, for the deterministic core — the C-05 status algorithm, the
C-06 validation cascade, the C-07 metrics and their zero-denominator rules, the §5.4 exit map
(including E-19), the C-11 progress-bar arithmetic, and C-01 ID normalization. Test side:
everything that is a text parser, a filesystem walk, network/XML I/O, or a renderer — SPEC.md's
own declaration grammar, source/test scanning and attribution, JUnit XML parsing, the LLM/Jev
wire formats, both report renderers, `explain`'s trace, and the CLI's argument parsing and help
text.

## Scope

252 declared conformance ids — 41 R, 19 C, 17 I, 16 K, 61 E, 98 T — the Phase 1 classification,
checked mechanically against `Theorems.lean`'s bold ID tags and closing tables:

- **54 proven** (kernel-checked, tagged above a theorem): C-01, C-04, C-05, C-06, C-07, C-11,
  C-13, C-18, most of the E-nn edge cases that are pure decision logic (E-01…E-06, E-09, E-14…E-19,
  E-21, E-24…E-26, E-32, E-36, E-41, E-48, E-49, E-51…E-54, E-58, E-60), I-001, I-002, I-004, I-005,
  I-008, I-011, K-01, K-07, K-13, K-15, R-09, R-11, R-14, R-15, R-22, R-25, R-28, R-31, R-35.
- **98 T-nn** — the §9 acceptance-test inventory; a T id is a run, never a theorem.
- **The rest deferred**, each naming the real `tests/test_NN_*.py` file that carries it: SPEC.md's
  own declaration/citation grammar (C-01's parser, C-02, C-03), the Python/Swift attribution
  adapters, JUnit XML reading, the LLM/Jev network wire formats (C-09's HTTP shape, C-10, C-17),
  the C-12/C-13 edge extraction and impact walk, every rendered byte (C-08, C-16, C-18, C-19), and
  the process layer (§3.1 file I/O, K-02/K-03/K-05/K-06/K-08 filters and timing).
- **9 named exclusions** — the spec's own stated non-goals (§0, §5.2): no semantic analysis, no
  test execution, no spec-quality review, no remediation, no multi-spec runs, no change semantics,
  no IDE/daemon/web surface, no adapters beyond Python/Swift, no GUI.

Its partition is checked mechanically: every bold-tagged id in `Theorems.lean` appears in the
closing "Dual halves" table (and vice versa), and every declared R/C/I/K/E id in `SPEC.md`
appears in exactly one of the proven-tag set, the deferred table, or the dual-halves table (the
same holds for the 98 T ids, each covered by the closing table's blanket row).
