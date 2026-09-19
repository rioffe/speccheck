# Impact Report

SPEC.md · changed by `--changed` · depth 1

## 1. Changed

| ID | Line | Reason |
| --- | --- | --- |
| K-02 | 85 | changed |

## 2. Impact

| ID | Depth | Via |
| --- | --- | --- |
| C-04 | 1 | C-04 -depends_on-> K-02 |

## 3. Re-verify

| T id | Verifies |
| --- | --- |
| T-03 | K-02 |
| T-04 | C-04 |
| T-05 | C-04, K-02 |
| T-06 | C-04 |
| T-07 | C-04 |

| File | Case | IDs |
| --- | --- | --- |
| tests/test_core.py | test_subtract_precision | T-03 |
| tests/test_core.py | test_version_string | K-02 |
| tests/test_summary.py | test_summary_shape | C-04, T-04 |
| tests/test_summary.py | test_summary_rounds_the_exact_sum_once | C-04, K-02, T-05 |
| tests/test_summary.py | test_summary_ordering_is_stable_ascending | C-04, T-06 |
| tests/test_summary.py | test_summary_empty_input | C-04, T-07 |
| tests/test_summary.py | test_summary_runs_on_a_mixed_list | C-04 |
| tests/test_summary.py | test_summary_module_does_not_change_add | C-04 |

## 4. Re-cite

| ID | File | Lines |
| --- | --- | --- |
| C-04 | src/calc/summary.py | 1, 21 |
| K-02 | src/calc/core.py | 1, 5 |
| K-02 | src/calc/summary.py | 29 |

## 5. Notes

- edge to undeclared id: C-04 -> T-49
- edge to undeclared id: C-04 -> T-76
- edge to undeclared id: D-03 -> E-99
