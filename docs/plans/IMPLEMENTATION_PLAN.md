# Implementation plan — speccheck v1.25 delta (provenance manifest, hazard traceability)

> - **Target:** the `speccheck` kernel at `SPEC.md` v1.25 (sha256 `14df9d59fa0e…` at `9c27508`):
>   R-106..R-109, R-15 amended, C-01/C-02/C-03/C-07/C-08/C-18/C-19 amended, C-25..C-28, I-001
>   amended, I-020, I-021, K-20, E-09 amended, E-78..E-85, T-122..T-129; D-61..D-65 confirmed.
> - **Size expectation:** a delta on the built v1.24 implementation (4671 production code lines over
>   18 modules by `cloc src/speccheck --exclude-dir=_selfcheck`; 6071 test code lines; 189 tests,
>   187 passing — the 2 failures are the id-count pins, 307 against the 334 the spec now declares).
>   Budget **~330–480 production lines** (one new module, `manifest.py`), **~450–650 test lines**,
>   two new help goldens and two regenerated ones.
> - **Method:** red-green-refactor per §9 row; one commit per wave on branch `spec/v1.25`; `SPEC.md`
>   edited only by a recorded `fix(spec):`.

## 1. Verdict

Three waves, hazards first because the manifest has to list the risk file it reads. **W1** builds
the hazard half in the modules that already own each layer: the CONTROLS marker in
`extract.py` beside RECORDED, the roll-up in `graph.py` after the judge stage, `--risk-file` in
`cli.py`, the keys, `## 10. Hazards`, the summary suffix and the `UNCONTROLLED` strict condition in
`report.py`, and the `controls:` line in `explain.py`. **W2** builds the manifest and `verify` in a
new `manifest.py`, fed by a read log that `scan_roots` and the explicit reads append to, written as
the third file through the existing `write_named_files`. **W3** proves it: the inertness test
against the committed goldens, counts, version 1.25.0, docs, both gates. Nothing is dropped to fit:
the smallest alternative (hashing only the explicitly named files, not the scanned trees) would
miss the very edit that motivated v1.25, a change to a `--src` file.

## 2. What the evidence says

| Measure (at `9c27508`) | Value |
| --- | --- |
| Tests | 189 collected, 187 pass; the 2 failures are `DECLARED_IDS` and the article's `307/307` |
| Production code | 4671 lines; `cli.py` 1245, `extract.py` 614, `report.py` 573, `graph.py` 229, `explain.py` 81 |
| Where files are read | `cli._run_stages` (spec, results, citation map via `load_citation_map`, proof results), `extract.scan_roots` (`--src`, `--tests`), `lean.scan_lean_paths` (`--proof`) |
| Atomic writer | `report.write_named_files(out, [(name, text)…])` already writes N files all-or-none |
| Oversized files | `scan_roots` skips a file over 2 MiB on `stat()` without reading it; C-25 still lists it with the hash of its full bytes |
| Prior build | v1.24 in three waves; its first Phase B failed on HTTP 402 and was re-run after a top-up; its lesson (every Note of the final runs read) stands |

## 3. Shape

One new module, `src/speccheck/manifest.py`: `ReadLog` (append `(path, role, data | None)`),
`render_manifest(...) -> str`, `verify(manifest_path, root) -> (lines, exit)`. It imports only
`hashlib`, `json`, `pathlib` and `report.dumps`; `cli.py` calls it, nothing else does.
Hazard code stays in its layers: `extract` (grammar) → `graph` (`HazardRecord`, `compute_hazards`)
→ `report` (JSON/Markdown/summary/exit) → `explain` (one line). No layer reads a file it did not
read before, except `cli` reading `--risk-file` and `manifest` re-reading an oversized file.

## 4. Order

1. **W1 — hazards.** T-126, T-127, T-129 (summary half) red → marker, `SpecId.controls`, E-78,
   E-80, roll-up, `--risk-file` (C-28, E-84, K-20, E-09, C-03 exclusion), JSON/Markdown keys,
   R-15/R-105 wiring, `controls:` line. Gate: pytest (only the 2 count pins red), ruff,
   `--self-check`, `git diff --exit-code fixtures/` after a golden re-render (I-021's v1.24 bytes).
2. **W2 — manifest and verify.** T-122..T-125, T-129 (help half) red → read log, `--manifest`,
   `SOURCE_DATE_EPOCH` (E-85), the third temp-and-rename file, the `verify` subparser (E-82,
   E-83), help strings and goldens. Gate: as W1, plus `check --manifest` then `verify` on this repo.
3. **W3 — prove it.** T-128, counts (334) and version 1.25.0, README, ARCHITECTURE,
   SPEC_BUILD_REPORT, the article's line; Phase A, Phase B; every Note of both runs read.

## 5. LOC budget

| Slice | LOC |
| --- | --- |
| W1 `extract.py` 25–40, `graph.py` 35–50, `cli.py` 40–60, `report.py` 50–70, `explain.py` 8–12 | 160–230 |
| W2 `manifest.py` 110–150, `cli.py` (flag, env, verify parser, read log) 60–90, `extract.py`/`lean.py` read log 10–15 | 180–255 |
| **Total** | **~330–480** (estimate, not a floor) |
| Tests | 450–650 |

Anchors: v1.23's citation map (a new input file with validation, a conditional JSON key, a
summary suffix and an `explain` marker: about 150 lines in `cli.py`/`report.py`) for W1; v1.19's
proof manifest reader (`proof.py`, 107 lines) for the size of `manifest.py`'s reader half.

## 6. Rules

| Prior failure | Rule |
| --- | --- |
| A K-14 truncation Note shipped unread in v1.23.1 | W3 lists every Note of both final runs and the report says which are expected |
| Goldens changed by a feature and left red | W1 and W2 re-render both fixture goldens and `_selfcheck/` and require `git diff --exit-code` on them: v1.25 adds nothing to a run without its flags (I-021) |
| v1.24's Phase B was first recorded "blocked by HTTP 402" | W3 checks the judge endpoint with one request before the full run; a failed run is not evidence and is re-run, not reported as a gate |
| A manifest can only be as honest as the read log | Every `read_bytes()` on an input in `cli.py`, `extract.py` and `lean.py` goes through the log; T-122 compares `inputs` with an independent walk of the same roots |

## 7. One fork, then action

**Phase B on `openai/gpt-6-luna-pro` through OpenRouter, `--judge-concurrency 16` (recommended:
the v1.24 run's model, so the two `unknown_rate`s compare; the endpoint is configured in this
shell) versus a cheaper model.** About 1,100 judge calls either way. Taking the recommendation
unless told otherwise; the version is `1.25.0`, by the house pattern.

**Next concrete action:** W1-01: T-126 red in a new `tests/test_18_hazards.py`.
