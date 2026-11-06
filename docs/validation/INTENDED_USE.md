# Intended use — speccheck in a quality management system

> **Applies to:** speccheck 1.26.0 and later (`SPEC.md` v1.26, R-110, D-67).
> **Status:** supplier statement. A manufacturer validates speccheck against *its own* intended
> use (ISO 13485:2016 clause 4.1.6); this document is the input to that, not a substitute for it.

## The statement

This block is normative. It is the text of `SPEC.md` §0's *Intended use* block and is packaged byte
for byte as `speccheck/_qualify/intended_use.md`, so every qualification record (`speccheck
qualify`) carries the exact statement the installed copy was built with.

```text
Intended use of speccheck in a quality management system (v1.26)

Validated function: `speccheck check`, `speccheck verify` and `speccheck impact`, each run with
`--judge none` or `--judge mock`, together with `speccheck --self-check` and `speccheck qualify`.
For one specification, one set of source and test trees and one results file, `check` reports
which declared requirements are cited, tested and passing; identical inputs give byte-identical
reports. `verify` reports whether the files a manifest names are unchanged. `impact` lists what a
change to the specification might touch.

Outside validated use: `--judge llm`, `--jev-pre-triage` and `speccheck explain`. They may be
used. The judge can only lower a status, never raise one, but its output is advisory and is not
verification evidence.

speccheck does not run tests, does not decide whether a risk is acceptable, and does not sign or
approve records. The user's quality system owns test execution, risk acceptance, review, approval
and signatures, and the validation of speccheck for the user's own intended use.
```

## Why the boundary sits there

- **Deterministic and reproducible.** `check`, `verify` and `impact` with `--judge none`/`mock`
  produce byte-identical output for byte-identical inputs (I-002, I-020). A validation run can be
  repeated by an auditor and give the same bytes.
- **Offline.** In that mode no socket is opened (I-006); `qualify` checks this for its own run
  (I-022).
- **The LLM judge is advisory by construction.** It can only downgrade a `PASSING` id to
  `WEAKLY_PASSING` (R-11, I-004), so a team may use it to find weak tests. But its verdicts depend on
  a remote model that can change without notice, so they are not reproducible evidence. Bringing it
  into validated use needs a separate decision (`docs/plans/ISO13485_READINESS_PLAN.md` §3.4: a
  pinned model, stored requests and responses, and ongoing performance qualification). Until then,
  a run with `--judge llm` is not verification evidence, whatever it reports.
- **`explain` is a renderer** of facts `check` already computes (I-016). It is useful for review
  and needs no validation of its own.

## What speccheck does not do

- It does not run tests: it reads a JUnit results file produced by the user's test runner.
- It does not perform risk management: hazard ids in a CONTROLS marker or a risk file are labels
  owned by the user's ISO 14971 file (v1.25 non-goal).
- It does not sign, approve or attribute records: the manifest and the qualification record are
  deterministic, hashable files; who ran them and who approved them belongs to the user's
  eQMS (D-62).

## Related documents

- `TOOL_RISK_ASSESSMENT.md` — how the validated function could mislead, and what controls it.
- `IQ_OQ_PROTOCOL.md` — how to qualify an installed copy.
- `CHANGE_CONTROL.md` — what a new release obliges a user to do.
