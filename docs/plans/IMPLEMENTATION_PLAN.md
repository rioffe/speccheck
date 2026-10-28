# Implementation plan — speccheck v1.24 delta (UNPROVEN, CommonMark spans, cut rows, isolated ids)

> - **Target:** the `speccheck` kernel at `SPEC.md` v1.24 (sha256 `97b3c4e26ceb…` at `51073a2`): R-105,
>   C-01 (a) amended, C-24 (moved, no behaviour), E-66 amended, E-77, T-118..T-121.
> - **Size expectation:** a delta on the built v1.23.1 implementation (4557 production code lines,
>   18 modules; 185 tests, 183 passing — the two id-count pins read 300, the spec now declares 307).
>   Budget **~60–110 production lines** (`extract.py`, `report.py`, `cli.py`), **~150–250 test
>   lines**, two regenerated fixture goldens and `_selfcheck/`.
> - **Method:** red-green-refactor per §9 row; one commit per wave on `spec/v1.24`; `SPEC.md` edited
>   only by a recorded `fix(spec):`.

## 1. Verdict

Three waves. **W1** is everything in `extract.py`: the CommonMark span scanner shared by the row
splitter and E-66's `$` count (D-59), the header cell-count condition (E-66), and the isolated-id
set (E-77), carried on `SpecIndex` but *not* in `index.notes`, because `impact` copies those and
E-77 says `impact` does not emit it. W1 regenerates the two fixture goldens for the one new Note.
**W2** is the `UNPROVEN` word in `report.summary_line` (R-105), derived from the JSON so R-14 holds.
**W3** proves it: counts, version 1.24.0, README/ARCHITECTURE/build report, both gates.

## 2. What the evidence says

| Measure (at `51073a2`) | Value |
| --- | --- |
| Tests | 185 collected, 183 pass; the 2 failures are the `DECLARED_IDS`/article count pins (300 → 307) |
| Splitter vs CommonMark spans | 43 of 5,869 rows differ over 14 specs (proposal §1 B); 0 in the fixtures |
| Isolated ids | `fixtures/target` 3 (R-03, K-01, E-01), `fixtures/target-swift` 7, this spec 0 after T-42's fix |
| Prior build | v1.23.1 in four waves; its lesson: a K-14 Note sat unread for a release — W3 reads every Note of the final runs |

## 3. Shape

No new module. `extract.py` owns spans, cell counts and isolated ids; `report.py` owns the word;
`cli.py` appends the E-77 Note in `_run_stages` only.

## 4. Order

1. **W1 — extraction.** T-119, T-120, T-121 red → spans, header counts, isolated ids → goldens
   regenerated and read. Gate: pytest (only the 2 count pins red), ruff, `--self-check`, T-46/T-71.
2. **W2 — UNPROVEN.** T-118 red → `summary_line`; T-44 regex gains `UNPROVEN`. Gate: as W1.
3. **W3 — prove it.** Counts and version, docs, Phase A, Phase B (`openai/gpt-6-luna-pro`,
   `--judge-concurrency 16`), every Note of both runs read.

## 5. LOC budget

| Slice | LOC |
| --- | --- |
| W1 `extract.py` (+ `cli.py` 3) | 45–80 |
| W2 `report.py` | 8–20 |
| **Total** | **~60–110** |

Anchor: v1.21's E-66 and range edges (about 40 lines in `extract.py`).

## 6. Rules

| Prior failure | Rule |
| --- | --- |
| A K-14 truncation Note shipped unread in v1.23.1 | W3's gate lists every Note of the self-application run and the report says which are expected |
| Goldens changed by a feature and left red | W1 regenerates both fixture goldens and `_selfcheck/` in the same commit, and the diff is read |

## 7. One fork, then action

**The release number: `1.24.0` (recommended: the house's minor-version pattern, `v1.20.0`) versus
`1.24`.** The version guard needs only the prefix `1.24`; either works. Taking `1.24.0` unless told
otherwise.

**Next concrete action:** W1-01: T-119 red in `tests/test_01_extraction.py`.
