# Detailed implementation plan — W2: `speccheck qualify` (R-111..R-113, R-115, C-29, I-022, E-85..E-88)

> - **Gate:** as W1, plus `uv build --wheel`, a fresh `uv venv`, `uv pip install <wheel>`, then `<venv>/bin/speccheck qualify --out q` in an empty directory → `qualify: QUALIFIED - IQ <n> files, tree <hex12>; OQ 5/5 cases`, exit 0.
> - **Budget:** 230–320 production lines: new `qualify.py`; `cli.py`.

## Work items

- **W2-01** T-130 red (wheel in a fresh venv, module-scoped fixture): exit 0, QUALIFIED line, C-29 key order, tree hash equals the R-112 computation over `src/speccheck/` minus caches, every case PASS, the Markdown's seven headings and empty signature table. → `qualify.package_iq`, `render_record`, `cli` subparser.
- **W2-02** T-131: one byte appended to an installed module → `RECORD mismatch`, tree differs; a deleted file → `record_missing`. (Restore the file afterwards.)
- **W2-03** T-132 (in-process, a copied data root): an altered OQ-02 golden fails only OQ-02; a step patched to raise and one opening a socket get E-88's `failure`; no temporary survives. → `run_catalog`, the shared dispatch, the scoped guard.
- **W2-04** T-133: under `uv run`, E-86's line and exit 1 with both records; E-87 for a removed `known_anomalies.json` and an invalid `cases.json`.
- **W2-05** T-134: two runs byte-identical; socket guard restored; `SOURCE_DATE_EPOCH` 1793836800 → `generated_at` in JSON and Markdown §1; `abc` → exit 2, nothing written; unwritable `--out` → exit 3; I-023: the existing golden tests still pass unchanged.
- **W2-06** T-136: `qualify --help` content, `speccheck --help` lists `qualify`, `qualify --root .` exits 2, `tests/data/help/qualify_help.txt`; regenerate `speccheck_help.txt`.
