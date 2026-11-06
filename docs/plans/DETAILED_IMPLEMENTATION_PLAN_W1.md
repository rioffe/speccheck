# Detailed implementation plan — W1: packaged data and the self-applied risk file

> - **Gate:** pytest (only the 2 count pins red); ruff 0; `--self-check` ok; `git diff --exit-code fixtures/ src/speccheck/_selfcheck/`; the self-application `check --strict --risk-file src/speccheck/_qualify/tool_risk.json` lists TH-01..TH-10 with C-30's controls.
> - **Budget:** no production code; data files and two fixture copies.

## Work items

- **W1-01** T-135 red (`tests/test_20_qualify.py`): `tool_risk.json` ids and titles equal C-30's table (parsed from SPEC.md); every *Controlled by* id carries exactly its hazards in its CONTROLS marker (from `extract`'s `SpecId.controls`); every hazard is in some case's `hazards`; every anomaly has C-31's shape and names only C-30 hazards; every case's fixture and goldens exist; `_qualify/swift/` byte-equals `fixtures/target-swift/`; `_qualify/hazards/` byte-equals `fixtures/target/` except `SPEC.md`, `risk.json`, `golden/`. A run of `check --risk-file` over this repository lists the ten hazards with those controls.
- **W1-02** R-110 half of T-130: the §0 *Intended use* block's content equals `_qualify/intended_use.md`.
- **W1-03** Data: write the five files and copy the two fixtures; mark three ids of the hazards fixture's SPEC.md; render its goldens with the v1.25 kernel and check the `hazards` block against C-27 by hand; add `src/speccheck/_qualify/**` to `pyproject.toml` artifacts and ruff exclusions.
