# Specification Conformance Report

**Spec:** `SPEC.md` · **Judge:** mock (available) · **Strict:** on

## 1. Verdict

speccheck: NOT CONFORMING - 14/20 passing (70.0%), 1 failing, 1 skipped, 1 weak, 1 unverified, 1 untested, 1 uncited; 1 dangling, 1 stale; judge=mock

## 2. Metrics

| Metric | Value |
| --- | --- |
| Declared | 22 |
| Retired | 2 |
| In scope | 20 |
| Conformance | 14/20 (0.7000) |
| PASSING | 14 |
| WEAKLY_PASSING | 1 |
| FAILING | 1 |
| SKIPPED | 1 |
| UNVERIFIED | 1 |
| UNTESTED | 1 |
| UNCITED | 1 |
| Judge strength | 14/15 (0.9333) |
| Unknown rate | 0.0000 |

| Family | In scope | Passing | Ratio |
| --- | --- | --- | --- |
| R | 3 | 2 | 0.6667 |
| C | 3 | 2 | 0.6667 |
| I | 2 | 1 | 0.5000 |
| K | 2 | 1 | 0.5000 |
| E | 3 | 2 | 0.6667 |
| T | 7 | 6 | 0.8571 |

## 3. Per-ID evidence

| ID | Status | Statement | Source citations | Test citations (outcome · verdict) |
| --- | --- | --- | --- | --- |
| R-01 | PASSING | `add(a, b)` MUST return the arithmetic sum of `a` and `b`, rounded per K-02. | src/calc/core.py:10 | `test_add` tests/test_core.py:15 (passed · ASSERTS); `test_add_result` tests/test_core.py:77 (passed · ASSERTS); `test_add_rounding_fact` tests/test_core.py:82 (passed · ASSERTS); `test_summary_module_does_not_change_add` tests/test_summary.py:52 (passed · ASSERTS) |
| R-02 | PASSING | `subtract(a, b)` MUST return `a - b`, rounded per K-02. | src/calc/core.py:15 | `test_subtract` tests/test_core.py:25 (passed · ASSERTS); `test_divide_error_names_the_dividend_example` tests/test_core.py:70 (passed · ASSERTS); `test_subtract_result` tests/test_core.py:88 (passed · ASSERTS); `test_subtract_rounding_fact` tests/test_core.py:93 (passed · ASSERTS) |
| R-03 | UNCITED | `multiply(a, b)` MUST return the product of `a` and `b`. | — | — |
| ~~R-04~~ | RETIRED | `modulo(a, b)` MUST return `a % b`. (retired: dropped from the brief) | — | — |
| C-01 | PASSING | `divide(a, b)` raises `ZeroDivisionError` when `b == 0` | src/calc/core.py:20 | `test_divide_by_zero` tests/test_core.py:35 (passed · ASSERTS); `test_divide_error_names_the_dividend_example` tests/test_core.py:69 (passed · ASSERTS) |
| C-02 | UNTESTED | `scale(values, factor)` returns a new list and never mutates its input | src/calc/core.py:27 | — |
| ~~C-03~~ | RETIRED | `average(values)` returns the arithmetic mean (retired) | — | — |
| C-04 | PASSING | Summary report: `summarize(values)` and the `Summary` shape | src/calc/summary.py:1, src/calc/summary.py:21 | `test_summary_shape` tests/test_summary.py:11 (passed · ASSERTS); `test_summary_rounds_the_exact_sum_once` tests/test_summary.py:22 (passed · ASSERTS); `test_summary_ordering_is_stable_ascending` tests/test_summary.py:28 (passed · ASSERTS); `test_summary_empty_input` tests/test_summary.py:39 (passed · ASSERTS); `test_summary_runs_on_a_mixed_list` tests/test_summary.py:46 (passed · EXECUTES_ONLY); `test_summary_module_does_not_change_add` tests/test_summary.py:52 (passed · ASSERTS); `test_summary_total_result` tests/test_summary.py:58 (passed · ASSERTS); `test_summary_total_rounding_fact` tests/test_summary.py:63 (passed · ASSERTS); `test_summary_mean_result` tests/test_summary.py:69 (passed · ASSERTS); `test_summary_mean_uses_exact_total` tests/test_summary.py:74 (passed · ASSERTS); `test_summary_mean_rounding_fact` tests/test_summary.py:79 (passed · ASSERTS) |
| I-001 | PASSING | `add` is commutative, per R-01: `add(a, b) == add(b, a)` for all finite inputs; both calls are rounded per K-02. | src/calc/core.py:10 | `test_add_commutes` tests/test_core.py:20 (passed · ASSERTS); `test_add_commutes_on_floats` tests/test_core.py:126 (passed · ASSERTS); `test_add_commutes_on_plain_sum` tests/test_core.py:131 (passed · ASSERTS); `test_add_commutes_rounding_fact` tests/test_core.py:138 (passed · ASSERTS) |
| I-002 | WEAKLY_PASSING | `scale` (C-02) preserves the length of its input list. | src/calc/core.py:27 | `test_scale_runs` tests/test_core.py:47 (passed · EXECUTES_ONLY) |
| K-01 | SKIPPED | `divide` completes in under 1 ms for inputs below 10^6. | src/calc/core.py:20 | `test_divide_fast` tests/test_core.py:42 (skipped · —) |
| K-02 | PASSING | Every result is rounded to two decimal places with `round(x, 2)`. | src/calc/core.py:1, src/calc/core.py:5, src/calc/summary.py:29 | `test_version_string` tests/test_core.py:62 (passed · ASSERTS); `test_summary_rounds_the_exact_sum_once` tests/test_summary.py:22 (passed · ASSERTS) |
| E-01 | UNVERIFIED | Negative inputs to `scale` | src/calc/core.py:29 | `test_scale_negative` tests/test_core.py:52 (unrun · —) |
| E-02 | PASSING | Empty list passed to `scale` (per C-02) | src/calc/core.py:29 | `(file)` tests/test_core.py:1 (unrun · —); `test_scale_empty` tests/test_core.py:57 (passed · ASSERTS); `test_scale_empty_result` tests/test_core.py:99 (passed · ASSERTS); `test_scale_empty_input_is_not_mutated` tests/test_core.py:104 (passed · ASSERTS) |
| E-03 | PASSING | A `ZeroDivisionError` raised by `divide`, per C-01, reached from a caller | — | `test_zero_division_propagates` tests/test_core.py:111 (passed · ASSERTS); `test_zero_division_message_names_the_dividend` tests/test_core.py:119 (passed · ASSERTS) |
| T-01 | PASSING | `add` returns the sum for integers and floats. (R-01) | — | `test_add` tests/test_core.py:15 (passed · ASSERTS) |
| T-02 | PASSING | `divide` by zero raises with the dividend in the message. (C-01) | — | `test_divide_by_zero` tests/test_core.py:35 (passed · ASSERTS) |
| T-03 | FAILING | `subtract` of floats keeps two-decimal precision. (R-02, K-02) | — | `test_subtract_precision` tests/test_core.py:30 (failed · —) |
| T-04 | PASSING | `summarize` returns the pinned `Summary` shape: field names, order, types, `count` including duplicates, frozen. (C-04 rule 1) | — | `test_summary_shape` tests/test_summary.py:11 (passed · ASSERTS) |
| T-05 | PASSING | `summarize` rounds the exact sum once: `[0.005, 0.005]` totals `0.01`. (C-04 rule 2, K-02) | — | `test_summary_rounds_the_exact_sum_once` tests/test_summary.py:22 (passed · ASSERTS) |
| T-06 | PASSING | `summarize` orders ascending with a stable sort and reports `smallest`/`largest`. (C-04 rule 4) | — | `test_summary_ordering_is_stable_ascending` tests/test_summary.py:28 (passed · ASSERTS) |
| T-07 | PASSING | `summarize([])` is the all-empty `Summary` with `mean` `None` and `total` `0.0`. (C-04 rule 6) | — | `test_summary_empty_input` tests/test_summary.py:39 (passed · ASSERTS) |

## 4. Dangling citations

| ID | File | Line |
| --- | --- | --- |
| R-09 | src/calc/core.py | 30 |

## 5. Stale citations

| ID | File | Line |
| --- | --- | --- |
| R-04 | src/calc/legacy.py | 5 |

## 6. Unattributed results

| Classname | Name | Outcome |
| --- | --- | --- |
| tests.test_gone | test_vanished | passed |

## 7. Unrun test citations

| ID | File | Name |
| --- | --- | --- |
| E-01 | tests/test_core.py | test_scale_negative |
| E-02 | tests/test_core.py | (file) |

## 8. Judge details

| ID | Test | Verdict | Clause | Evidence | Rationale |
| --- | --- | --- | --- | --- | --- |
| R-01 | tests/test_core.py `test_add` | ASSERTS | `add(a, b)` MUST return the arithmetic sum of `a` and `b`, rounded per K-02. | tests/test_core.py:16 | mock: assertion token on 1 line(s) |
| R-01 | tests/test_core.py `test_add_result` | ASSERTS | `add(a, b)` MUST return the arithmetic sum of `a` and `b`, rounded per K-02. | tests/test_core.py:78 | mock: assertion token on 1 line(s) |
| R-01 | tests/test_core.py `test_add_rounding_fact` | ASSERTS | `add(a, b)` MUST return the arithmetic sum of `a` and `b`, rounded per K-02. | tests/test_core.py:84 | mock: assertion token on 1 line(s) |
| R-01 | tests/test_summary.py `test_summary_module_does_not_change_add` | ASSERTS | `add(a, b)` MUST return the arithmetic sum of `a` and `b`, rounded per K-02. | tests/test_summary.py:53, tests/test_summary.py:54 | mock: assertion token on 2 line(s) |
| R-02 | tests/test_core.py `test_subtract` | ASSERTS | `subtract(a, b)` MUST return `a - b`, rounded per K-02. | tests/test_core.py:26 | mock: assertion token on 1 line(s) |
| R-02 | tests/test_core.py `test_divide_error_names_the_dividend_example` | ASSERTS | `subtract(a, b)` MUST return `a - b`, rounded per K-02. | tests/test_core.py:71, tests/test_core.py:73 | mock: assertion token on 2 line(s) |
| R-02 | tests/test_core.py `test_subtract_result` | ASSERTS | `subtract(a, b)` MUST return `a - b`, rounded per K-02. | tests/test_core.py:89 | mock: assertion token on 1 line(s) |
| R-02 | tests/test_core.py `test_subtract_rounding_fact` | ASSERTS | `subtract(a, b)` MUST return `a - b`, rounded per K-02. | tests/test_core.py:95 | mock: assertion token on 1 line(s) |
| C-01 | tests/test_core.py `test_divide_by_zero` | ASSERTS | `divide(a, b)` raises `ZeroDivisionError` when `b == 0` The error message MUST … | tests/test_core.py:36 | mock: assertion token on 1 line(s) |
| C-01 | tests/test_core.py `test_divide_error_names_the_dividend_example` | ASSERTS | `divide(a, b)` raises `ZeroDivisionError` when `b == 0` The error message MUST … | tests/test_core.py:71, tests/test_core.py:73 | mock: assertion token on 2 line(s) |
| C-04 | tests/test_summary.py `test_summary_shape` | ASSERTS | Summary report: `summarize(values)` and the `Summary` shape ```python @dataclas… | tests/test_summary.py:13, tests/test_summary.py:14, tests/test_summary.py:15, tests/test_summary.py:16, tests/test_summary.py:17 | mock: assertion token on 5 line(s) |
| C-04 | tests/test_summary.py `test_summary_rounds_the_exact_sum_once` | ASSERTS | Summary report: `summarize(values)` and the `Summary` shape ```python @dataclas… | tests/test_summary.py:23, tests/test_summary.py:24 | mock: assertion token on 2 line(s) |
| C-04 | tests/test_summary.py `test_summary_ordering_is_stable_ascending` | ASSERTS | Summary report: `summarize(values)` and the `Summary` shape ```python @dataclas… | tests/test_summary.py:30, tests/test_summary.py:31, tests/test_summary.py:32, tests/test_summary.py:35 | mock: assertion token on 4 line(s) |
| C-04 | tests/test_summary.py `test_summary_empty_input` | ASSERTS | Summary report: `summarize(values)` and the `Summary` shape ```python @dataclas… | tests/test_summary.py:41, tests/test_summary.py:42 | mock: assertion token on 2 line(s) |
| C-04 | tests/test_summary.py `test_summary_runs_on_a_mixed_list` | EXECUTES_ONLY | Summary report: `summarize(values)` and the `Summary` shape ```python @dataclas… | — | mock: no assertion token |
| C-04 | tests/test_summary.py `test_summary_module_does_not_change_add` | ASSERTS | Summary report: `summarize(values)` and the `Summary` shape ```python @dataclas… | tests/test_summary.py:53, tests/test_summary.py:54 | mock: assertion token on 2 line(s) |
| C-04 | tests/test_summary.py `test_summary_total_result` | ASSERTS | Summary report: `summarize(values)` and the `Summary` shape ```python @dataclas… | tests/test_summary.py:59 | mock: assertion token on 1 line(s) |
| C-04 | tests/test_summary.py `test_summary_total_rounding_fact` | ASSERTS | Summary report: `summarize(values)` and the `Summary` shape ```python @dataclas… | tests/test_summary.py:65 | mock: assertion token on 1 line(s) |
| C-04 | tests/test_summary.py `test_summary_mean_result` | ASSERTS | Summary report: `summarize(values)` and the `Summary` shape ```python @dataclas… | tests/test_summary.py:70 | mock: assertion token on 1 line(s) |
| C-04 | tests/test_summary.py `test_summary_mean_uses_exact_total` | ASSERTS | Summary report: `summarize(values)` and the `Summary` shape ```python @dataclas… | tests/test_summary.py:75 | mock: assertion token on 1 line(s) |
| C-04 | tests/test_summary.py `test_summary_mean_rounding_fact` | ASSERTS | Summary report: `summarize(values)` and the `Summary` shape ```python @dataclas… | tests/test_summary.py:81 | mock: assertion token on 1 line(s) |
| I-001 | tests/test_core.py `test_add_commutes` | ASSERTS | `add` is commutative, per R-01: `add(a, b) == add(b, a)` for all finite inputs;… | tests/test_core.py:21 | mock: assertion token on 1 line(s) |
| I-001 | tests/test_core.py `test_add_commutes_on_floats` | ASSERTS | `add` is commutative, per R-01: `add(a, b) == add(b, a)` for all finite inputs;… | tests/test_core.py:127 | mock: assertion token on 1 line(s) |
| I-001 | tests/test_core.py `test_add_commutes_on_plain_sum` | ASSERTS | `add` is commutative, per R-01: `add(a, b) == add(b, a)` for all finite inputs;… | tests/test_core.py:134 | mock: assertion token on 1 line(s) |
| I-001 | tests/test_core.py `test_add_commutes_rounding_fact` | ASSERTS | `add` is commutative, per R-01: `add(a, b) == add(b, a)` for all finite inputs;… | tests/test_core.py:141 | mock: assertion token on 1 line(s) |
| I-002 | tests/test_core.py `test_scale_runs` | EXECUTES_ONLY | `scale` (C-02) preserves the length of its input list. | — | mock: no assertion token |
| K-02 | tests/test_core.py `test_version_string` | ASSERTS | Every result is rounded to two decimal places with `round(x, 2)`. | tests/test_core.py:65 | mock: assertion token on 1 line(s) |
| K-02 | tests/test_summary.py `test_summary_rounds_the_exact_sum_once` | ASSERTS | Every result is rounded to two decimal places with `round(x, 2)`. | tests/test_summary.py:23, tests/test_summary.py:24 | mock: assertion token on 2 line(s) |
| E-02 | tests/test_core.py `test_scale_empty` | ASSERTS | Empty list passed to `scale` (per C-02) | tests/test_core.py:58 | mock: assertion token on 1 line(s) |
| E-02 | tests/test_core.py `test_scale_empty_result` | ASSERTS | Empty list passed to `scale` (per C-02) | tests/test_core.py:100 | mock: assertion token on 1 line(s) |
| E-02 | tests/test_core.py `test_scale_empty_input_is_not_mutated` | ASSERTS | Empty list passed to `scale` (per C-02) | tests/test_core.py:107 | mock: assertion token on 1 line(s) |
| E-03 | tests/test_core.py `test_zero_division_propagates` | ASSERTS | A `ZeroDivisionError` raised by `divide`, per C-01, reached from a caller | tests/test_core.py:112, tests/test_core.py:114, tests/test_core.py:115 | mock: assertion token on 3 line(s) |
| E-03 | tests/test_core.py `test_zero_division_message_names_the_dividend` | ASSERTS | A `ZeroDivisionError` raised by `divide`, per C-01, reached from a caller | tests/test_core.py:120, tests/test_core.py:122 | mock: assertion token on 2 line(s) |
| T-01 | tests/test_core.py `test_add` | ASSERTS | `add` returns the sum for integers and floats. (R-01) | tests/test_core.py:16 | mock: assertion token on 1 line(s) |
| T-02 | tests/test_core.py `test_divide_by_zero` | ASSERTS | `divide` by zero raises with the dividend in the message. (C-01) | tests/test_core.py:36 | mock: assertion token on 1 line(s) |
| T-04 | tests/test_summary.py `test_summary_shape` | ASSERTS | `summarize` returns the pinned `Summary` shape: field names, order, types, `cou… | tests/test_summary.py:13, tests/test_summary.py:14, tests/test_summary.py:15, tests/test_summary.py:16, tests/test_summary.py:17 | mock: assertion token on 5 line(s) |
| T-05 | tests/test_summary.py `test_summary_rounds_the_exact_sum_once` | ASSERTS | `summarize` rounds the exact sum once: `[0.005, 0.005]` totals `0.01`. (C-04 ru… | tests/test_summary.py:23, tests/test_summary.py:24 | mock: assertion token on 2 line(s) |
| T-06 | tests/test_summary.py `test_summary_ordering_is_stable_ascending` | ASSERTS | `summarize` orders ascending with a stable sort and reports `smallest`/`largest… | tests/test_summary.py:30, tests/test_summary.py:31, tests/test_summary.py:32, tests/test_summary.py:35 | mock: assertion token on 4 line(s) |
| T-07 | tests/test_summary.py `test_summary_empty_input` | ASSERTS | `summarize([])` is the all-empty `Summary` with `mean` `None` and `total` `0.0`… | tests/test_summary.py:41, tests/test_summary.py:42 | mock: assertion token on 2 line(s) |

## 9. Notes

- edge to undeclared id: C-04 -> T-49
- edge to undeclared id: C-04 -> T-76
- edge to undeclared id: D-03 -> E-45
