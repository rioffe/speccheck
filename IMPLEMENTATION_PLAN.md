# Implementation plan — SPEC.md v1.14 delta (declared vs. incidental citations)

> Scope: a **delta plan** on top of the working v1.13 implementation (215 ids, `speccheck check
> --judge mock --strict` CONFORMING). It covers only the ids v1.14 added: R-39, C-14, C-15, C-16,
> I-014, E-56, T-85, T-86, T-87, T-88, D-26, D-27. Not a greenfield plan; the target shape
> (Extractor / Attributor / Grapher / Judge / Reporter / CLI) is already built and unchanged.

## Verdict

Three waves, in dependency order, each gated by the existing `speccheck check --judge mock
--strict` self-check plus the new ids' own tests. The fact (Part A) is computed in the
Attributor and is the only input the judge (Part B) and the report (Part C) consume, so Part A
must exist and be tested first. T-87 is a recorded, non-gating LLM re-run of three real edges
(the proposal's own falsifiable claim); it needs no kernel change and is measured with the
existing `check --judge llm` path.

- **W1 — Part A: the `declared` fact.** `attribute.py`: `Citation.declared` (C-03/C-14), the
  Python docstring-span (`ast.get_docstring`'s `Expr` node) and whole-line-comment rule, the
  Swift reuse of `_Line.doc` (R-31); `swift.py`: expose the per-line doc flags `delimit_swift`
  already computes; `graph.py`: `TestEdge.declared` (true iff any citation line of the edge is
  DECLARED) and the per-citation declared counters for `declared_ratio`; `cli.py`: the `"src"`
  citation constructor (always `false`, E-56). New edge semantics only — no status changes
  (I-014). Closes R-39, C-14, E-56, I-014; T-85.
- **W2 — Part B: the judge is told.** `judge.py`: `JudgeRequest.declared` after `testcase`
  (C-06/C-15), `build_request` gaining the parameter, `to_json` gaining the key after
  `statement`; `cli.py`: pass `edge.declared`; `judge_prompt.md`: the field's definition and the
  skepticism rule, byte-for-byte the C-10 text (whose `judge_prompt_sha256` changes). Advisory
  only — no coercion rule, K-15/E-48/E-49/I-004/I-005 untouched (D-26). Closes C-15; extends
  T-33/T-54/T-74; T-87 recorded.
- **W3 — Part C: visibility.** `report.py`: `SDHEMA`-version → `"1.5"`, `tests[].declared` after
  `lines`, `metrics.declared_ratio` last (C-07/C-16); `fixtures/target/`: one new test whose
  docstring declares one id while its body reuses an existing id as example data (T-86) plus its
  `junit.xml` result and `judge_labels.json` labels; regenerate `fixtures/target/golden/`,
  `fixtures/target-swift/golden/`, then `src/speccheck/_selfcheck/` via `tools/sync_selfcheck.py`
  (T-60/T-73). Closes C-16; T-86, T-88.

## Gates

```bash
uv run python -m pytest tests -q --junitxml=junit.xml
uv run ruff check src tests
uv run speccheck check --spec SPEC.md --src src --tests tests --results junit.xml --judge mock --strict --out build/speccheck
```

W3 additionally pins the fixture goldens byte-for-byte and runs `speccheck --self-check`
(`self-check: ok`). T-87 is run by hand against the three named edges with the configured LLM
judge and recorded in `SPEC_BUILD_REPORT.md`; it does not block any gate (advisory instruction,
falsifiable claim — T-49's caveat applies).

## The one fork

None open. D-26 (advisory only, not coercion) and D-27 (whole-line-comment detection, not
token-level) are already confirmed in `SPEC.md` §12; there is no remaining decision for the user
to make before implementing.

## Spec defects found while planning (fixed under `fix(spec)` in Phase 3)

Two stale spots the v1.15 edit left behind; both are document-only, no id semantics:
`§3.3`'s artifact table still pins `schema_version: "1.4"` for `speccheck.json` (C-07 says
`"1.5"`), and T-74's "unchanged keys `{id, statement, file, start, end, source}`" predates
C-06's `declared`. Recorded as F-101/F-102 in `SPEC_BUILD_REPORT.md` and corrected in
`SPEC.md` (version header unchanged; these are corrections to v1.14's own rows).

## Next action

Execute W1 test-first, gate, commit; then W2; then W3.