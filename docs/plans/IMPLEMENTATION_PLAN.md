# Implementation plan — speccheck v1.26 delta (validation pack: intended use, `qualify`, tool risk file, known anomalies)

> - **Target:** `SPEC.md` v1.26 (sha256 `75791efd4b03…` at `d132a87`): R-110..R-115, C-29..C-31,
>   I-022, I-023, E-85 amended, E-86..E-88, T-130..T-137, the 31 CONTROLS markers of C-30's hazard
>   table; D-66..D-71 confirmed.
> - **Size expectation:** a delta on the built v1.25 implementation (5157 production code lines over
>   20 files by `cloc src/speccheck --exclude-dir=_selfcheck`; 6525 test code lines; 213 tests, 211
>   passing — the 2 failures are the id-count pin, 334 against 356, and the article's verbatim
>   quote of R-11, which now carries its marker). Budget **~240–340 production lines** (one new
>   module, `qualify.py`, plus `cli.py` wiring), **~400–550 test lines**, packaged data (five JSON or
>   text files and two fixture copies), one new help golden, four validation documents and one tool.
> - **Method:** red-green-refactor per §9.19 row; one commit per wave on branch `spec/v1.26`;
>   `SPEC.md` edited only by a recorded `fix(spec):`.

## 1. Verdict

Three waves, data first, because `qualify` is a reader of the packaged data and every OQ case is
judged against a packaged golden. **W1** writes `src/speccheck/_qualify/` — the intended-use text,
the tool risk file, the known anomalies, the case catalog and the two fixture copies with their
goldens — packages it, and turns on the self-applied risk file, so the build gate itself checks the
31 markers before any code reads them. **W2** builds `qualify.py` (IQ, OQ, the two records) and its
`cli.py` subparser, help and exit wiring. **W3** proves it: counts, version 1.26.0, the validation
documents, `tools/validation_impact.py`, README, ARCHITECTURE, the article, `SPEC_BUILD_REPORT.md`
§0q with the package tree hash (T-137), both gates. Nothing is dropped to fit: the smallest
alternative (running `--self-check` as the only OQ case) would leave TH-02, TH-03, TH-08 and TH-10
unchallenged on a customer's machine.

## 2. What the evidence says

| Measure (at `d132a87`) | Value |
| --- | --- |
| Tests | 213 collected, 211 pass; the 2 failures are `DECLARED_IDS` and the article's R-11 quote |
| Production code | 5157 lines; `cli.py` 1775 physical lines, `manifest.py` 189 |
| Reusable parts | `cli.self_check` (copies a packaged fixture, runs `check` in-process, compares goldens); `cli.install_socket_guard` (patches `socket.socket.__init__` for the process lifetime); `report.write_named_files` (N files, all or none); `manifest.tree_sha256` (the `shasum` line format); `cli._source_date_epoch` (E-85) |
| Installed tree = tag | measured for 1.24.0 (35 files) and 1.25.0 (36 files): the installed `speccheck/` files hash to the same tree digest as `git archive <tag> src/speccheck` |
| Editable install | `uv run` installs `speccheck` editable: its `RECORD` holds no hashed `speccheck/` entry, so in-process tests see E-86 by construction; T-130/T-131 need a wheel in a fresh environment |
| Prior build | v1.25 in three waves, both gates clean (Phase B `unknown_rate` 0.0117 over 1,110 edges after a probe-first rule caught a rejected key) |

## 3. Shape

One new module, `src/speccheck/qualify.py`: `package_iq(dist) -> IQ`, `run_catalog(data_root, run_step) -> list[CaseResult]`, `render_record(...) -> (json_text, md_text)`, `first_failure(...)`. It takes the package data directory and the distribution as parameters, so tests run it on a modified copy without touching the install. `cli.py` gains the `qualify` subparser, `QualifyConfig`, `execute_qualify`, and one dispatch function shared by `main` and the OQ runner, so a step's exceptions are mapped the same way `main` maps them — except that a blocked socket is reported as E-88, not swallowed as exit `3`. The socket guard becomes scoped (installed for the `qualify` run, restored after), raising its own exception class. Package data under `src/speccheck/_qualify/`, added to `pyproject.toml`'s `artifacts` and to ruff's exclusions like `_selfcheck/`.

## 4. Order

1. **W1 — packaged data and the self-applied risk file.** T-135 red in `tests/test_20_qualify.py`
   (hazard file = C-30 table, markers, case coverage, anomaly shape, fixture drift) and the R-110
   block-equality half of T-130 → `_qualify/{intended_use.md, tool_risk.json,
   known_anomalies.json, cases.json, swift/, hazards/}`, the hazards fixture's goldens rendered from
   the v1.25 kernel and checked against C-27 by hand, `pyproject.toml` artifacts. Gate: pytest
   (only the 2 pins red), ruff, `--self-check`, `git diff --exit-code fixtures/`, and the
   self-application `check --strict --risk-file src/speccheck/_qualify/tool_risk.json` showing the
   ten hazards with the C-30 controls.
2. **W2 — `qualify`.** T-130..T-134, T-136 red → `qualify.py`, the subparser and its help (golden
   `qualify_help.txt`), E-85 for `qualify`, E-86..E-88, the scoped socket guard. Gate: as W1, plus
   a wheel built from the tree, installed into a fresh environment, `speccheck qualify --out q`
   printing `QUALIFIED`.
3. **W3 — prove it.** Counts (356) and version 1.26.0, the article's quote and numbers,
   `docs/validation/*.md`, `tools/validation_impact.py`, README, ARCHITECTURE, `SPEC_BUILD_REPORT.md`
   §0q with `package_tree_sha256` and the T-137 presence test; Phase A with `--risk-file`, Phase B;
   every Note of both runs read.

## 5. LOC budget

| Slice | LOC |
| --- | --- |
| W1 data only (JSON, text, fixture copies) | 0 production code |
| W2 `qualify.py` 170–230, `cli.py` (subparser, config, dispatch, scoped guard) 60–90 | 230–320 |
| W3 `tools/validation_impact.py` (not in the wheel) | 40–70 |
| **Total (wheel)** | **~240–340** (estimate, not a floor) |
| Tests | 400–550 |

Anchors: `manifest.py` (189 physical lines: hashing, a deterministic record, a loader with
validation) for `qualify.py`'s IQ and record halves; `cli.self_check` (60 lines) for one OQ case.

## 6. Rules

| Prior failure | Rule |
| --- | --- |
| A golden produced by the code it certifies is only a regression guard | The hazards fixture's goldens are rendered by the v1.25 kernel, and W1 checks their `hazards` block by hand against C-27 (one each of `VERIFIED`, `NOT_VERIFIED`, `UNCONTROLLED`) before committing them; the report says which oracle each OQ golden rests on |
| A permanent socket patch leaked across in-process tests (T-43 restores it by hand) | The `qualify` guard is scoped and restored in a `finally`; T-134 asserts `socket.socket.__init__` is the original after a run |
| Tests that assume a checkout cannot be OQ | Every OQ case runs from packaged data in a temporary copy; T-130 runs `qualify` from a wheel in an empty directory |
| v1.24/v1.25 Phase B were first blocked by 402/401 | One probe request before the full run; a failed run is not evidence |
| A Note shipped unread | W3 lists every Note of both final runs |

## 7. One fork, then action

**Phase B on `openai/gpt-6-luna-pro` through OpenRouter at `--judge-concurrency 16`, key from
`switch_to_openrouter.sh` with the model overridden** — settled by the requester for v1.25 and
restated for this build. The version is `1.26.0`, by the house pattern.

**Next concrete action:** W1-01: T-135 red in a new `tests/test_20_qualify.py`.
