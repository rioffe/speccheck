# Detailed implementation plan — W2: manifest and verify (C-25, C-26, R-106, R-107, I-020)

> - **Gate:** as W1, plus `check --manifest` then `verify` on this repository → `verify: ok`.
> - **Budget:** 180–255 production lines: new `manifest.py`; `cli.py`; read-log hooks in `extract.py` and `lean.py`.
> - **Depends on W1:** `Config.risk_file`.

## Work items

- **W2-01** T-122 (`tests/test_19_manifest.py`, on a copy of `fixtures/target`): key order; `inputs` equal an independent walk (spec, every scanned file with role, results); hashes/lengths equal disk; `tree_sha256` from the `shasum` line format; `reports` equal the written files, Markdown first; `tool.version`; reports byte-equal to a run without the flag; with `--out` inside `--tests` the manifest is never scanned. Red → `manifest.ReadLog`, `render_manifest`; `scan_roots(..., log=None)` logs every selected file (oversized and binary included, symlinks not); `scan_lean_paths(..., log=None)`; explicit reads in `_run_stages` and `load_citation_map`/risk file logged; `write_named_files` gets three files; C-03 exclusions for the manifest and its temporaries.
- **W2-02** T-123: deterministic twice; `SOURCE_DATE_EPOCH=1793836800` → `generated_at` `2026-11-05T00:00:00Z`; `abc` and empty → exit 2 E-85 before any read; ignored without `--manifest`; CRLF twin → same reports, different spec hash; an injected failure before the third rename leaves none of the three.
- **W2-03** T-124 and T-125: `verify` ok line; one-byte change → `mismatch` + `FAILED - 1 of N`; deleted report → `missing`; E-82 (no flag, outside root) exit 2; E-83 (not JSON, version, missing key, `../x`, bad hex) exit 3 with no input read; nothing written; socket guard. T-125: append to a `--src` file after a manifest run → reports unchanged, `verify` names it. Red → `verify` subparser in `build_parser`, `manifest.verify`, `execute_verify`.
- **W2-04** T-129 help half: `check --help` names `--manifest`, `--risk-file`, `SOURCE_DATE_EPOCH`; `verify --help` names `--manifest FILE` and its four codes; regenerate `tests/data/help/{speccheck,check}_help.txt`, add `verify_help.txt`; T-95/T-98 still green.

## Gate

1–4 as W1. 5. `uv run speccheck check --spec SPEC.md --src src --tests tests --results junit.xml --judge mock --manifest --out build/rec` then `uv run speccheck verify --manifest build/rec/speccheck.manifest.json` — expected `verify: ok - …`, exit 0.
