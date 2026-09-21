# Impact Report

SPEC.md · changed by `--changed` · depth 1

## 1. Changed

| ID | Line | Reason |
| --- | --- | --- |
| K-02 | 85 | changed |

## 2. Impact

| ID | Depth | Via |
| --- | --- | --- |
| R-01 | 1 | R-01 -depends_on-> K-02 |
| R-02 | 1 | R-02 -depends_on-> K-02 |
| C-04 | 1 | C-04 -depends_on-> K-02 |
| I-001 | 1 | I-001 -depends_on-> K-02 |

## 3. Re-verify

| T id | Verifies |
| --- | --- |
| T-01 | R-01 |
| T-03 | R-02, K-02 |
| T-04 | C-04 |
| T-05 | C-04, K-02 |
| T-06 | C-04 |
| T-07 | C-04 |

| File | Case | IDs |
| --- | --- | --- |
| tests/test_core.py | test_add | R-01, T-01 |
| tests/test_core.py | test_add_commutes | I-001 |
| tests/test_core.py | test_subtract | R-02 |
| tests/test_core.py | test_subtract_precision | T-03 |
| tests/test_core.py | test_version_string | K-02 |
| tests/test_core.py | test_divide_error_names_the_dividend_example | R-02 |
| tests/test_core.py | test_add_result | R-01 |
| tests/test_core.py | test_add_rounding_fact | R-01 |
| tests/test_core.py | test_subtract_result | R-02 |
| tests/test_core.py | test_subtract_rounding_fact | R-02 |
| tests/test_core.py | test_add_rounding_of_a_half_cent | R-01 |
| tests/test_core.py | test_add_commutes_on_floats | I-001 |
| tests/test_core.py | test_add_commutes_on_plain_sum | I-001 |
| tests/test_core.py | test_add_commutes_rounding_fact | I-001 |
| tests/test_summary.py | test_summary_shape | C-04, T-04 |
| tests/test_summary.py | test_summary_rounds_the_exact_sum_once | C-04, K-02, T-05 |
| tests/test_summary.py | test_summary_ordering_is_stable_ascending | C-04, T-06 |
| tests/test_summary.py | test_summary_empty_input | C-04, T-07 |
| tests/test_summary.py | test_summary_runs_on_a_mixed_list | C-04 |
| tests/test_summary.py | test_summary_module_does_not_change_add | R-01, C-04 |
| tests/test_summary.py | test_summary_total_result | C-04 |
| tests/test_summary.py | test_summary_total_rounding_fact | C-04 |
| tests/test_summary.py | test_summary_mean_result | C-04 |
| tests/test_summary.py | test_summary_mean_uses_exact_total | C-04 |
| tests/test_summary.py | test_summary_mean_rounding_fact | C-04 |

## 4. Re-cite

| ID | File | Lines |
| --- | --- | --- |
| R-01 | src/calc/core.py | 10 |
| R-02 | src/calc/core.py | 15 |
| C-04 | src/calc/summary.py | 1, 21 |
| I-001 | src/calc/core.py | 10 |
| K-02 | src/calc/core.py | 1, 5 |
| K-02 | src/calc/summary.py | 29 |

## 5. Notes

- edge to undeclared id: C-04 -> T-49
- edge to undeclared id: C-04 -> T-76
- edge to undeclared id: D-03 -> E-45
