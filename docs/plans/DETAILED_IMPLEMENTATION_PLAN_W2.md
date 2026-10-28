# Detailed implementation plan — W2: the UNPROVEN word (R-105)

> - **Gate:** as W1. **Budget:** 8–20 lines in `report.py`.

## Work items

- **W2-01** T-118 (`test_07_cli.py`): fixture without `--results` → `UNPROVEN - 0/20`, exit 0; `--strict` → `NOT CONFORMING`, 1; all-PASSING project → `CONFORMING` both modes; plus one dangling → `UNPROVEN`; Markdown §1 equals stdout; `exit_code` equals the process status. Red → `summary_line` chooses the word from `exit_code`, `by_status`, `in_scope`, `dangling`, `stale`.
- **W2-02** `SUMMARY_RE` gains `UNPROVEN`; T-44 still green.
