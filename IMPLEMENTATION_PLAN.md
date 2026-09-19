# Implementation plan — SPEC.md v1.13 delta (C-12 edges, C-13 `impact`)

> Scope: this is a **delta plan** on top of the working v1.12 implementation (203 ids, `speccheck
> check` CONFORMING). It covers only the ids v1.13 added: R-36, R-37, C-12, C-13, I-013, E-53,
> E-54, E-55, T-79..T-82, D-24, D-25. Not a greenfield plan; no target-shape or LOC-budget section
> is needed because the shape (Extractor / Grapher / Reporter / CLI, deterministic kernel) is
> already built and unchanged.

## Verdict

Two waves, in dependency order, each gated by the existing `speccheck check --judge mock
--strict` self-check plus the new ids' own tests. `impact` (C-13) reads the edges C-12 produces,
so C-12 must exist and be tested first. The recorded backtest (T-82, D-24) is a third, non-gating
wave since it needs `git` history and touches nothing already-built.

- **W1 — C-12 spec-internal edges.** `extract.py`: `Decision`, `Edge` dataclasses; the C-01 (c)
  decision-table grammar; the edge-extraction pass (statement tokens → `depends_on`/`verifies`,
  *Affects* cells → `affects`); `SpecIndex.decisions`/`edges`. `report.py`: `decisions` and
  `edges` keys in `speccheck.json` after `ids`, `schema_version` → `"1.4"`. Fixture: extend
  `fixtures/target/SPEC.md` with a decision table (T-79's three rows). No change to any existing
  status, metric, or the Markdown report.
- **W2 — C-13 `impact` subcommand.** New `impact.py`: changed-set resolution (`--changed`,
  `--against` diff with its six reasons), the breadth-first reverse walk with `--depth` and
  `via`, REVERIFY, RECITE, TEST_CASES. `cli.py`: the `impact` subparser, E-53/E-54 validation,
  wiring into `main`. `report.py`: `impact.json` / `IMPACT_REPORT.md` renderers and the summary
  line. Golden fixtures: `fixtures/target/golden/{impact.json,IMPACT_REPORT.md}` (T-80), the
  `--against` fixture pair (T-81).
- **W3 — the backtest (recorded, non-gating).** `tools/impact_backtest.py` (D-24): git plumbing
  outside the kernel, run once against `main`'s own history for T-82. Does not block W1/W2's
  gate.

## Gates

```bash
uv run python -m pytest tests -q --junitxml=junit.xml
uv run ruff check src tests
uv run speccheck check --spec SPEC.md --src src --tests tests --results junit.xml --judge mock --strict --out build/speccheck
```

W2 additionally exercises `speccheck impact` against the golden fixture and against this
repository's own `SPEC.md` (a real `--changed`/`--against` run, by hand, as evidence for
`SPEC_BUILD_REPORT.md`).

## The one fork

None open. D-24 and D-25 are already confirmed in `SPEC.md` §12; there is no remaining decision
for the user to make before implementing.

## Next action

Execute W1 test-first, gate, commit; then W2; then W3.
