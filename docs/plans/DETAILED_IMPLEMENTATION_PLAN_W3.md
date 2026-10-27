# Detailed implementation plan — W3: the citation map

> - **Wave:** W3 of W1–W4 (`IMPLEMENTATION_PLAN.md` §4 item 3).
> - **Spec basis:** `SPEC.md` v1.23.1; not edited by this wave.
> - **Gate:** `tests/test_17_citation_map.py` green; I-019 over every golden; W2 gate intact.
> - **Budget:** 160–240 production lines. **Depends on:** W2 (`Config.namespace` threading). **Unlocks:** W4.

## 1. Objective and spec obligations

| id | obligation | how |
|---|---|---|
| R-103, C-23 | `--citation-map FILE` on check/impact/explain; schema 1.0; entries resolve to a `TestCase` by (file, name), smallest `start` on a tie | `cli._load_citation_map`, `_apply_map` |
| E-70, K-19, K-18 | unreadable/outside root → 2 at validation; shape faults and >2 MiB → 3 in apply-map | split read (validation) / parse (stage) |
| E-71 | unresolved → one Note per entry; counted | `_apply_map` |
| E-72, E-73, D-57 | mapped `Citation(kind test, line=start, declared=True, mapped=True)`; literal duplicate wins | `attribute.Citation.mapped` field |
| C-03 (F-702) | map and `--proof-results` files excluded from every scan | `_excluded_paths`, `_impact_excluded_paths` |
| C-07 (F-703) | `declared_ratio` excludes mapped citations | `graph.build_graph` population |
| C-07, C-23 (F-704) | `mapped` on `tests[]`, `dangling`, `stale` (only with the flag); `citation_map` counts; `lines: []` | `report.to_json` |
| C-08, C-18, §5.1 | `file (map)`; `(mapped)` in explain; `; citations: <M> mapped` | `report.to_markdown`, `explain`, summary line |
| T-110, T-111, T-109 (rest) | the §9.17 rows | `tests/test_17_citation_map.py` |

## 2. Entry preconditions

W2 committed, gate green.

## 3. Deliverables

- **`attribute.py` — EDIT (~3):** `Citation.mapped: bool = False`.
- **`cli.py` — EDIT (~100–140):** flag on three parsers; read bytes in validation (E-70 exit 2); `apply-map` stage after scan-tests: JSON parse, `schema_version == "1.0"`, `citations` array, entries with exactly `id`/`file`/`test` strings, bare TOKEN id, 2 MiB cap (K-19); resolution; `citation_map` counts; exclusion of both files.
- **`graph.py` — EDIT (~10–20):** ratio population skips `mapped`; dangling/stale carry `mapped`.
- **`report.py` — EDIT (~30–50):** conditional keys and orders; Markdown `(map)`; summary suffix.
- **`explain.py` — EDIT (~5–10):** `(mapped)` suffix; E-73 literal wins.
- **`tests/test_17_citation_map.py`, `tests/data/citation_map/` — NEW.** Help goldens regenerated.

## 4. Work items

- **W3-01** T-111 faults (red) → read/validate.
- **W3-02** T-110 Python + file-level + JS resolution and statuses (red) → `_apply_map`.
- **W3-03** T-110 labels: JSON `mapped`, `lines: []`, Markdown `(map)`, summary `; citations: 3 mapped`, explain `(mapped)`, impact re-cite.
- **W3-04** T-110 dangling/stale `mapped: true`, `declared: true` in the judge request, `declared_ratio` unchanged by the map.
- **W3-05** T-110 map and manifest under `--tests` → identical reports (F-702).
- **W3-06** T-109 (rest): absent flag → no new keys; goldens byte-identical. Help goldens.

## 5. Test plan

`uv run python -m pytest tests/test_17_citation_map.py tests/test_13_help.py tests/test_06_reports.py -q`.

## 6. Gate

W2 gate (expected unchanged), plus `uv run python -m pytest tests/test_17_citation_map.py -q` — expected: all pass; and T-44's summary regex test green with and without the suffix.

## 7. Traceability

R-103, C-23, K-19, E-70..E-73, T-110, T-111: UNCITED → PASSING; T-109 complete.

## 8. Traps

- Key order: `citation_map` directly before `foreign`, both after `unattributed_results`; `mapped` after `declared` in `tests[]`, after `line` in dangling/stale. T-34 pins key order.
- E-73 duplicates count as resolved each time, so `resolved + unresolved == entries` must hold with duplicates present.
- A map entry for a test in a file excluded by `speccheck:ignore-file` is unresolved (E-71), not an error.

## 9. Exit and handoff

Frozen: the JSON keys. W4 re-runs W1–W3 gates.
