# Detailed implementation plan — W1: the fixture's adjacent pairs (Part A)

> - **Wave:** W1 of W1–W3 (`IMPLEMENTATION_PLAN.md` §4 item 1).
> - **Spec basis:** `SPEC.md` v1.16, sha256
>   `0e1e7c415e25b1ef609abed14c094b11be31189a1afa221034b624e85bbb2b16`. Not edited by this wave
>   except by a recorded `fix(spec):` if a pinned number in a row turns out to be stale (§8).
> - **Gate:** the whole suite green with the regenerated fixture goldens, `--self-check` `ok`,
>   and T-76's floors asserted mechanically (≥37 labels, ≥8 adjacent `UNRELATED`).
> - **Budget:** ~90–140 fixture lines (tests + spec rows), 16 junit entries, 16 labels; ~60–120
>   outer-suite lines (the re-derived pinned numbers and the two new assertions).
> - **Depends on:** nothing (the fixture is apparatus). **Unlocks:** W3's T-84/T-49 measurement,
>   which needs the adjacent subset to exist and be labeled.

## 1. Objective and spec obligations

| id | obligation (≤20 words) | how this wave discharges it |
| --- | --- | --- |
| T-76 | the fixture's cross-references and adjacent pairs; ≥37 labels, ≥8 adjacent `UNRELATED`, ≥6 on the long-body contract | fixture rows gain the cross-references and E-03; 8 adjacent + 8 genuine tests; labels regenerated |
| T-46 | the fixture keeps its planted defects and produces byte-identical goldens | the four goldens are regenerated and the planted-defect assertions still hold |
| T-47 | removing a planted defect flips exactly its row and metric | the repair table's counts are re-derived (the fixture gains one id) |
| T-86 | the incidental-citation test's `declared_ratio` reflects the fixture | the ratio is re-derived after the new citations |
| T-88 | `declared_ratio` recomputable under both judge modes | unchanged, re-run |
| T-73 | goldens carry `title`, Markdown renders it, `_selfcheck/` in step | regenerated + `tools/sync_selfcheck.py` |
| T-79/T-80 | the `impact` goldens stay byte-identical to a fresh run | regenerated (new `depends_on` edges change K-02's dependents) |
| T-60 | `_selfcheck/` byte-identical to `fixtures/target/` | synced after every fixture edit |
| T-49 | labels cover exactly the judged edges (half) | the label file is extended; the three runs are W3's |

## 2. Entry preconditions

- `f9d8d6c` (the v1.16 fold) is HEAD; the suite is at 1 failed / 123 passed, the single failure
  being `test_09_self_application`'s `DECLARED_IDS` (W3 fixes it).
- `speccheck --self-check` prints `self-check: ok`; `tools/sync_selfcheck.py --check` is clean.
- `fixtures/target/golden/judge_labels.json` holds 23 entries; the fixture declares 19 in-scope
  ids and 2 retired.

## 3. Deliverables, file by file

### 3.1 `fixtures/target/SPEC.md` — EDIT (~10 lines), fixture v1.2 → v1.3

- Status line: v1.3 adds the adjacent pairs and their labels for T-76/T-84.
- `R-01`: "… the arithmetic sum of `a` and `b`, rounded per K-02." → edge R-01 → K-02.
- `R-02`: "… `a - b`, rounded per K-02." → edge R-02 → K-02.
- `I-001`: "… commutative, per R-01: `add(a, b) == add(b, a)` …; both calls are rounded per K-02."
  → edges I-001 → R-01, I-001 → K-02.
- `I-002`: "`scale` (C-02) preserves the length of its input list." → edge I-002 → C-02.
- `E-02`: "Returns a new empty list, per C-02; the input is not mutated." → edge E-02 → C-02.
- **New `E-03`**: a `ZeroDivisionError` raised by `divide` reached from a caller propagates
  unchanged — same type, C-01's message, nothing wrapped. → edge E-03 → C-01.
- Every added row stays a table row, so `SpecId.text == SpecId.title` (T-01's fixture property).
- The "planted defects" prose is unchanged: E-03 is `PASSING`, not a defect.

### 3.2 `fixtures/target/tests/test_core.py` — EDIT (+11 cases)

Adjacent (`UNRELATED`) — cite X, exercise X's code, assert only Y's fact, Y named by X:

| case | cites | asserts |
| --- | --- | --- |
| `test_add_rounding_fact` | R-01 | `round(0.005 + 0.005, 2) == 0.01` (K-02) |
| `test_subtract_rounding_fact` | R-02 | `round(1.005, 2) == 1.0` (K-02) |
| `test_scale_empty_input_is_not_mutated` | E-02 | the input list is still `[]` (C-02) |
| `test_zero_division_message_names_the_dividend` | E-03 | `"7" in str(exc.value)` (C-01) |
| `test_add_commutes_on_plain_sum` | I-001 | `add(1, 2) == 3` (R-01) |
| `test_add_commutes_rounding_fact` | I-001 | `round(0.005 + 0.005, 2) == 0.01` (K-02) |

Genuine (`ASSERTS`) — same calls, one more assertion, asserting X's own clause:

| case | cites | asserts |
| --- | --- | --- |
| `test_add_result` | R-01 | `add(2, 3) == 5` |
| `test_subtract_result` | R-02 | `subtract(5, 3) == 2` |
| `test_scale_empty_result` | E-02 | `scale([], 3) == []` |
| `test_zero_division_propagates` | E-03 | the type is exactly `ZeroDivisionError` and the raising frame is `divide` |
| `test_add_commutes_on_floats` | I-001 | `add(0.1, 0.2) == add(0.2, 0.1)` |

### 3.3 `fixtures/target/tests/test_summary.py` — EDIT (+5 cases)

| case | kind | cites | asserts |
| --- | --- | --- | --- |
| `test_summary_total_result` | genuine | C-04 | rule 2: `summarize([0.005, 0.005]).total == 0.01` |
| `test_summary_mean_result` | genuine | C-04 | rule 3: `summarize([1, 1, 2]).mean == 1.33` |
| `test_summary_mean_uses_exact_total` | genuine | C-04 | rule 3: `summarize([1, 2]).mean == 1.5` |
| `test_summary_total_rounding_fact` | adjacent | C-04 | `round(0.005 + 0.005, 2) == 0.01` (K-02) |
| `test_summary_mean_rounding_fact` | adjacent | C-04 | `round(1 / 3, 2) == 0.33` (K-02) |

No new test cites `R-03`, `C-02`, `E-01`, `K-01`, `I-002` or `T-03` — each is a planted defect
whose status must not flip (T-46).

### 3.4 `fixtures/target/junit.xml` — EDIT

`tests="18"` → `tests="34"`; the 16 new cases added as passed `<testcase>` elements. The failure,
skip and `tests.test_gone` entries are untouched.

### 3.5 `fixtures/target/golden/judge_labels.json` — EDIT

+16 entries (8 `UNRELATED` adjacent, 8 `ASSERTS`), 23 → 39.

### 3.6 `fixtures/target/golden/{speccheck.json,SPEC_CONFORMANCE_REPORT.md,impact.json,IMPACT_REPORT.md}` — REGENERATED

Regenerate by running the tool, never by hand (§9 of `IMPLEMENTATION_PLAN.md` §6):
`check … --root fixtures/target --out fixtures/target/golden` and
`impact --changed K-02 … --root fixtures/target --out fixtures/target/golden`.

### 3.7 `src/speccheck/_selfcheck/` — SYNCED

`uv run python tools/sync_selfcheck.py` after the last fixture edit.

### 3.8 `tests/test_08_golden.py` — EDIT (~40 lines)

- `test_fixture_long_body_contract_and_labels`: label floor 20 → 37; the six contract edges named
  explicitly (4 `ASSERTS` + 1 `EXECUTES_ONLY` + 1 `UNRELATED`); a new mechanical adjacent floor —
  ≥8 labels whose value is `UNRELATED` and whose id's statement carries a `depends_on` edge.
- `REPAIRS`: `PASSING` counts 14 → 15; `conformance_ratio` denominator 19 → 20.
- `test_fixture_gains_one_incidental_citation`: the re-derived `declared_ratio` (both the fresh
  run and the golden), with the docstring's numbers corrected.

## 4. Work items, in order (red → green → refactor)

- **W1-01** — RED: extend `test_fixture_long_body_contract_and_labels` with the 37/8 floors and
  run it — it fails on `len(labels) >= 37`. Then edit `fixtures/target/SPEC.md` (cross-references
  + E-03) and the two fixture test modules, add the junit entries, and extend the labels. GREEN
  when the T-76 test passes.
- **W1-02** — RED: the regenerated goldens do not exist yet, so `test_golden_fixture_matches_byte_for_byte`
  fails. Regenerate the four goldens, sync `_selfcheck/`, and re-run.
- **W1-03** — RED: `test_removing_each_planted_defect_flips_exactly_its_row` fails on the stale
  `14`/`/19` numbers. Re-derive them from `golden/speccheck.json` and fix the table.
- **W1-04** — RED: `test_fixture_gains_one_incidental_citation` fails on `0.9474`. Re-derive the
  ratio from a `--judge none` run and fix the test; if the SPEC row's parenthetical `(18 of 19
  citations DECLARED)` no longer matches, record `F-1` and apply a `fix(spec):` (Phase 3.3).
- **W1-05** — run the wave gate; commit.

## 5. Test plan

| group | ids | what must be asserted | how it runs |
| --- | --- | --- | --- |
| `tests/test_08_golden.py` | T-46, T-47, T-73, T-76, T-86, T-88, T-79/T-80 | byte-identical goldens; the planted statuses; the label floors; the repair table | `pytest tests/test_08_golden.py tests/test_11_impact.py -q` |
| `tests/test_09_self_application.py` | T-49 (half), T-60 | labels cover exactly the judged edges; `_selfcheck/` in step | `pytest tests/test_09_self_application.py tests/test_07_cli.py -q` |
| whole suite | all | nothing regressed | `pytest tests -q --junitxml=junit.xml` |

## 6. Gate: commands and expected results

```bash
uv run python -m pytest tests -q --junitxml=junit.xml     # expected: 1 failed (test_09 DECLARED_IDS), rest green
uv run ruff check src tests                                # expected: exit 0
uv run speccheck --self-check                              # expected: "self-check: ok", exit 0
uv run python tools/sync_selfcheck.py --check              # expected: exit 0
uv run python -c "import json;print(len(json.load(open('fixtures/target/golden/judge_labels.json'))))"   # expected: 39
```

## 7. Traceability

| id | file.symbol | test | status now → after |
| --- | --- | --- | --- |
| T-76 | `fixtures/target/{SPEC.md,tests/*.py}`, `golden/judge_labels.json` | `test_fixture_long_body_contract_and_labels` | PASSING → PASSING (floors extended) |
| T-46/T-47 | `fixtures/target/golden/*` | `test_golden_fixture_matches_byte_for_byte`, `test_removing_each_planted_defect_flips_exactly_its_row` | PASSING → PASSING |
| T-79/T-80 | `golden/impact.json` | `test_impact_cli_against_golden_fixture` | PASSING → PASSING |
| T-60 | `src/speccheck/_selfcheck/` | `test_selfcheck_fixture_is_byte_identical_to_golden_fixture` | PASSING → PASSING |
| T-84 | `golden/judge_labels.json` (half) | the W3 presence check | UNCITED → UNCITED (W3) |

## 8. Traps

- **Every pinned number this wave moves, enumerated** (grep for each after the edit):
  the fixture's in-scope count `19` (`tests/test_08_golden.py` ×9, `README.md`), `PASSING: 14`
  (×5 in `REPAIRS`), `declared_ratio` `0.9474` (test + golden + the SPEC's T-86 row),
  `len(labels) >= 20` (test + T-49's row is ≥20, still true), `tests="18"` in the fixture's
  `junit.xml`, and `SPEC_BUILD_REPORT.md`'s fixture counts (W3).
- **Do not cite a planted-defect id** from any new test: `R-03` (UNCITED), `C-02` (UNTESTED),
  `E-01` (UNVERIFIED), `K-01` (SKIPPED), `I-002` (WEAKLY_PASSING), `T-03` (FAILING). A new
  `assert`-bearing test citing `I-002` or `C-02` flips a planted status and breaks T-46.
- **A cross-reference is an edge**: any `X-nn` token added to a statement joins the `edges`
  array and moves the `impact` goldens. Add only the seven intended ones.
- **The goldens are regenerated, never hand-edited**; `_selfcheck/` is re-synced after the last
  fixture byte changes (T-60 fails otherwise).
- **A `(18 of 19 citations DECLARED)`-style parenthetical in `SPEC.md` is a pinned number**: if
  Part A moves it, the row is stale — fix the spec with a `fix(spec):` commit and record it, do
  not leave the spec contradicting the fixture.

## 9. Exit criteria and handoff contract

- Gate commands run, with their real exit codes recorded for `SPEC_BUILD_REPORT.md`.
- Frozen for later waves: `fixtures/target/SPEC.md` (E-03 declared; the seven `depends_on`
  edges), `golden/judge_labels.json` (39 entries; the adjacent subset is the 8 keys whose value
  is `UNRELATED` and whose id carries a `depends_on` edge).
- The next wave re-runs `pytest tests -q` and `speccheck --self-check` to confirm W1 is intact.
