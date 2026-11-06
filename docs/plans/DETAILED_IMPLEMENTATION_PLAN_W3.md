# Detailed implementation plan — W3: prove it

> - **Gate:** pytest 0 failed; ruff 0; self-check ok; Phase A (`--risk-file src/speccheck/_qualify/tool_risk.json`) and Phase B `CONFORMING` with `; hazards: 10/10 verified`; every Note of both runs read and listed in the report.

## Work items

W3-01 `DECLARED_IDS = 356`, the article's R-11 quote and numbers, `__version__ = "1.26.0"`, SPEC status line to v1.26 (built). W3-02 `docs/validation/{INTENDED_USE,TOOL_RISK_ASSESSMENT,IQ_OQ_PROTOCOL,CHANGE_CONTROL}.md`; `tools/validation_impact.py` (run against v1.25.0 as its example). W3-03 README (`qualify`, the self-application gate's `--risk-file`), ARCHITECTURE (`qualify.py`, `_qualify/`), `SPEC_BUILD_REPORT.md` §0q with `package_tree_sha256` and the §5 rows for the 22 new ids; T-137 presence test. W3-04 Phase A. W3-05 one-request endpoint probe, then Phase B with `openai/gpt-6-luna-pro`, `--judge-concurrency 16`. W3-06 merge `spec/v1.26` into `main` only when the user asks.
