# Detailed implementation plan — W1: extraction (C-01 spans, E-66 cell count, E-77 isolated ids)

> - **Gate:** pytest red only on the two count pins; ruff 0; `self-check: ok`; T-46/T-71 against regenerated goldens.
> - **Budget:** 45–80 production lines in `extract.py`, 3 in `cli.py`.

## Work items

- **W1-01** T-119 (`test_01_extraction.py`): the mdv R-24 shape stays two cells; no trailing `|`; an unmatched backtick does not protect a later `|`; `` `a\|b` `` one cell. Red → `_code_spans(line)` (CommonMark runs) used by `split_row`.
- **W1-02** T-120: two-column TABLE `| **R-01** | a | b |` → Note and statement `a`; `$..$` case one Note; three-column TABLE three cells none; no TABLE none. Red → `_table_header_widths(lines)` (C-01 (c)'s TABLE, fences respected) and the widened E-66 condition; `_odd_math_delimiters` strips spans with the same scanner.
- **W1-03** T-121: isolated R and E counted, retired not; naming removes; five → ` and 2 more`; `impact.json` has no such Note. Red → `SpecIndex.isolated` from the C-12 edges, `isolated_note()`, appended in `cli._run_stages` only.
- **W1-04** regenerate `fixtures/target/golden/*`, `fixtures/target-swift/golden/*` (expected: one added Note line each, nothing else), `tools/sync_selfcheck.py`; read the diffs.

## Gate

1. `uv run python -m pytest tests -q --junitxml=junit.xml` — expected: 2 failed (count pins).
2. `uv run ruff check src tests` — 0. 3. `uv run speccheck --self-check` — `self-check: ok`.
