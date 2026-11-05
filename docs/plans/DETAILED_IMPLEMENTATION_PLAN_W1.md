# Detailed implementation plan — W1: hazards (C-27, C-28, R-108, R-109, R-15)

> - **Gate:** pytest red only on the two count pins; ruff 0; `self-check: ok`; both fixture goldens and `_selfcheck/` re-rendered with `git diff --exit-code` clean (I-021).
> - **Budget:** 160–230 production lines: `extract.py`, `graph.py`, `cli.py`, `report.py`, `explain.py`.
> - **Unlocks W2:** `Config.risk_file: Path | None` (the manifest's `risk_file` role) and the read of it in `cli._run_stages`.

## Work items

- **W1-01** T-126 (`tests/test_18_hazards.py`, tmp_path specs): `*(controls: HAZ-2, HAZ-1)*` on a row → `SpecId.controls == ("HAZ-1","HAZ-2")`; after `*(recorded)*` too; heading form strips the marker from the title; on a T id → E-78 Note, `()`; `*(controls: )*` and a 65-char HAZID → E-80 Note, `()`; markers create no edge and leave the statement unchanged. Red → `CONTROLS_RE` and `parse_controls(rest) -> (ids | None, rest)` in `extract.py`, called where RECORDED is; `SpecId.controls` field.
- **W1-02** T-126 continued: statuses VERIFIED / NOT_VERIFIED / UNCONTROLLED (retired-only control) / WEAKLY_PASSING control → NOT_VERIFIED under `--judge mock`; ids, metrics, edges, Markdown §3 byte-equal to the marker-free twin. Red → `graph.HazardRecord`, `compute_hazards(records, risk) -> tuple[HazardRecord, ...] | None`, run in `_run_stages` after `apply_verdicts`; E-81 Note.
- **W1-03** T-126/T-129: JSON `controls` after `recorded` only on marked ids; top-level `hazards` after `edges`; Markdown `## 10. Hazards`; summary `; hazards: V/H verified` after the mapped suffix; `SUMMARY_RE` (T-44) gains the group; `explain` prints `controls: …` after `status:`. Red → `report.build_report`/`render_markdown`/`summary_line`, `explain._controls_line`.
- **W1-04** T-127: `--risk-file` (check only): UNCONTROLLED listed hazard, `--strict` exit 1 with all ids PASSING, non-strict `UNPROVEN`; titles in both reports; E-79 Note; empty list → `hazards: []`, `0/0`; E-84 cases exit 3, no report; unreadable / outside root exit 2; `impact`/`explain` reject the flag; the file is never scanned. Red → `_readable_risk_file`, `load_risk_file` (C-28 shape, HAZID, duplicates, 2 MiB), `_excluded_paths`, `exit_code_for` and `_exit0_word` read `hazards`.
- **W1-05** re-render `fixtures/target/golden/*`, `fixtures/target-swift/golden/*` and `tools/sync_selfcheck.py`; expected: no diff.

## Gate

1. `uv run python -m pytest tests -q --junitxml=junit.xml` — expected: 2 failed (count pins), all else passed.
2. `uv run ruff check src tests` — 0. 3. `uv run speccheck --self-check` — `self-check: ok`.
4. `git diff --exit-code fixtures src/speccheck/_selfcheck` — exit 0.
