# Detailed implementation plan — W3: prove it

> - **Gate:** pytest 0 failed; ruff 0; self-check ok; Phase A and Phase B `CONFORMING`; every Note of both runs read and listed in the report.

## Work items

W3-01 T-128 (`tests/test_19_manifest.py`): the golden fixture, the Swift fixture and the T-109 fixtures under v1.25 without new flags reproduce the committed goldens, no third file. W3-02 `DECLARED_IDS = 334`, the article's line and count, `__version__ = "1.25.0"`, SPEC status line to v1.25 (built). W3-03 README (`--manifest`, `verify`, `--risk-file`, the marker), ARCHITECTURE (`manifest.py`, the hazard stage), `SPEC_BUILD_REPORT.md` §0p and the §5 rows for the 27 new ids. W3-04 Phase A. W3-05 one-request endpoint probe, then Phase B with `openai/gpt-6-luna-pro`, `--judge-concurrency 16`. W3-06 merge `spec/v1.25` into `main` only when the user asks.
