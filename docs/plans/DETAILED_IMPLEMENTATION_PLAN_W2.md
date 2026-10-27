# Detailed implementation plan — W2: foreign references and `--namespace`

> - **Wave:** W2 of W1–W4 (`IMPLEMENTATION_PLAN.md` §4 item 2).
> - **Spec basis:** `SPEC.md` v1.23.1; not edited by this wave.
> - **Gate:** `tests/test_16_namespaces.py` green; every golden byte-identical (I-019, half).
> - **Budget:** 80–140 production lines. **Depends on:** W1 gate. **Unlocks:** W3 (`namespace` threaded through `Config`/`ImpactConfig`/`ExplainConfig`).

## 1. Objective and spec obligations

| id | obligation | how |
|---|---|---|
| R-101, C-22, E-67 | `<ns>:ID` (ns uncapped, not ID-shaped, ≠ `--namespace`) is no citation; listed in `foreign`; one Note naming the first three | `extract.FOREIGN_RE`, `citations_in_file(scanned, namespace)` returns citations + foreign |
| E-69, C-12, F-716 (b) | in a statement or Affects cell: no edge, no Note; not a range endpoint | `targets_of` skips FOREIGN spans before ID_RE and RANGE_RE |
| R-102, E-68 | `--namespace NS` on check/impact/explain, at most once, `{0,31}` grammar; `NS:ID` local | `cli.build_parser`, validation, config field |
| C-07 | `foreign` key after `unattributed_results`, only when non-empty | `report.to_json` |
| T-107, T-108, T-109 (half) | the §9.17 rows | `tests/test_16_namespaces.py` |

## 2. Entry preconditions

W1 committed; gate 1 shows only the `DECLARED_IDS` failures.

## 3. Deliverables

- **`extract.py` — EDIT (~40–60):** `FOREIGN_RE = (?<![A-Za-z0-9])(?P<ns>[A-Za-z][A-Za-z0-9_-]*):(?P<id>[RCIKET]-[0-9]{1,3})(?![A-Za-z0-9])`, ID-shaped ns rejected; `foreign_spans(line, namespace) -> list[(start, end, ns, id)]`; `citations_in_file` skips tokens inside a foreign span and returns `RawForeign` entries; `parse_spec(text, rel, namespace=None)` passes it to `targets_of`, which blanks foreign spans before both regexes (no Note, no range).
- **`cli.py` — EDIT (~30–50):** `--namespace` on three subparsers (C-19 help, metavar `NS`), `action` that rejects a second occurrence with `--namespace: given more than once`; `--namespace: invalid namespace: <value>`; thread into `_run_stages` and `execute_impact`; collect `foreign`, sort `(file, line, namespace, id)`, add the E-67 Note.
- **`report.py` — EDIT (~10–20):** `foreign` key, conditional.
- **`tests/test_16_namespaces.py` — NEW; `tests/data/namespaces/` — NEW** fixture files carrying `platform:R-99` (F-713).
- **`tests/data/help/{check,impact,explain}_help.txt` — REGENERATE** at `COLUMNS=80`.

## 4. Work items

- **W2-01** T-107 core (R-99 UNCITED with `platform:R-99`; `foreign` entry; Note) red → FOREIGN in `citations_in_file` → green.
- **W2-02** T-107 `--namespace platform` → PASSING, no `foreign`, no Note; second `--namespace` and a 33-char value exit 2; 41-char ns foreign.
- **W2-03** T-107 `R-01:R-02` both local; four tokens → ` and 1 more`; impact and explain agree.
- **W2-04** T-108 statement/Affects edges, range `platform:R-01..R-05` → one edge to R-05.
- **W2-05** T-109 (half): goldens and `--self-check` unchanged (already covered by gate; add the explicit test with the summary line and exit code).
- **W2-06** help goldens regenerated; T-95..T-97 green.

## 5. Test plan

`uv run python -m pytest tests/test_16_namespaces.py tests/test_13_help.py tests/test_10_edges.py -q`.

## 6. Gate

W1 gate items 1–4 (same expected results), plus `uv run python -m pytest tests/test_16_namespaces.py -q` — expected: all pass.

## 7. Traceability

R-101, R-102, C-22, E-67, E-68, E-69, T-107, T-108: UNCITED → PASSING. T-109: UNCITED → PASSING (half; W3 extends to `--citation-map` absent).

## 8. Traps

- This `SPEC.md` contains `platform:R-99` in statements: after W2 the C-07/C-23/R-101/T-107/T-108 `-> R-99` undeclared-target Notes lose the foreign ones. Expected, since E-69 says so, but it changes this repo's own `speccheck.json` notes; check `edge to undeclared id` Notes before and after.
- argparse `append`-free single flag: a second occurrence silently overwrites unless the action counts. Use a custom action.

## 9. Exit and handoff

Frozen: `extract.FOREIGN_RE`, `citations_in_file(scanned, namespace=None)`, `Config.namespace`. W3 re-runs this gate.
