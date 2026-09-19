# Specification Conformance Report

**Spec:** `SPEC.md` · **Judge:** mock (available) · **Strict:** on

## 1. Verdict

speccheck: NOT CONFORMING - 13/19 passing (68.4%), 1 failing, 1 skipped, 1 weak, 1 unverified, 1 untested, 1 uncited; 1 dangling, 1 stale; judge=mock

## 2. Metrics

| Metric | Value |
| --- | --- |
| Declared | 21 |
| Retired | 2 |
| In scope | 19 |
| Conformance | 13/19 (0.6842) |
| PASSING | 13 |
| WEAKLY_PASSING | 1 |
| FAILING | 1 |
| SKIPPED | 1 |
| UNVERIFIED | 1 |
| UNTESTED | 1 |
| UNCITED | 1 |
| Judge strength | 13/14 (0.9286) |
| Unknown rate | 0.0000 |

| Family | In scope | Passing | Ratio |
| --- | --- | --- | --- |
| R | 3 | 2 | 0.6667 |
| C | 3 | 2 | 0.6667 |
| I | 2 | 1 | 0.5000 |
| K | 2 | 1 | 0.5000 |
| E | 2 | 1 | 0.5000 |
| T | 7 | 6 | 0.8571 |

## 3. Per-ID evidence

| ID | Status | Statement | Source citations | Test citations (outcome · verdict) |
| --- | --- | --- | --- | --- |
| R-01 | PASSING | `add(a, b)` MUST return the arithmetic sum of `a` and `b`. | src/calc/core.py:10 | `test_add` tests/test_core.py:15 (passed · ASSERTS); `test_summary_module_does_not_change_add` tests/test_summary.py:52 (passed · ASSERTS) |
| R-02 | PASSING | `subtract(a, b)` MUST return `a - b`. | src/calc/core.py:15 | `test_subtract` tests/test_core.py:25 (passed · ASSERTS) |
| R-03 | UNCITED | `multiply(a, b)` MUST return the product of `a` and `b`. | — | — |
| ~~R-04~~ | RETIRED | `modulo(a, b)` MUST return `a % b`. (retired: dropped from the brief) | — | — |
| C-01 | PASSING | `divide(a, b)` raises `ZeroDivisionError` when `b == 0` | src/calc/core.py:20 | `test_divide_by_zero` tests/test_core.py:35 (passed · ASSERTS) |
| C-02 | UNTESTED | `scale(values, factor)` returns a new list and never mutates its input | src/calc/core.py:27 | — |
| ~~C-03~~ | RETIRED | `average(values)` returns the arithmetic mean (retired) | — | — |
| C-04 | PASSING | Summary report: `summarize(values)` and the `Summary` shape | src/calc/summary.py:1, src/calc/summary.py:21 | `test_summary_shape` tests/test_summary.py:11 (passed · ASSERTS); `test_summary_rounds_the_exact_sum_once` tests/test_summary.py:22 (passed · ASSERTS); `test_summary_ordering_is_stable_ascending` tests/test_summary.py:28 (passed · ASSERTS); `test_summary_empty_input` tests/test_summary.py:39 (passed · ASSERTS); `test_summary_runs_on_a_mixed_list` tests/test_summary.py:46 (passed · EXECUTES_ONLY); `test_summary_module_does_not_change_add` tests/test_summary.py:52 (passed · ASSERTS) |
| I-001 | PASSING | `add` is commutative: `add(a, b) == add(b, a)` for all finite inputs. | src/calc/core.py:10 | `test_add_commutes` tests/test_core.py:20 (passed · ASSERTS) |
| I-002 | WEAKLY_PASSING | `scale` preserves the length of its input list. | src/calc/core.py:27 | `test_scale_runs` tests/test_core.py:47 (passed · EXECUTES_ONLY) |
| K-01 | SKIPPED | `divide` completes in under 1 ms for inputs below 10^6. | src/calc/core.py:20 | `test_divide_fast` tests/test_core.py:42 (skipped · —) |
| K-02 | PASSING | Every result is rounded to two decimal places with `round(x, 2)`. | src/calc/core.py:1, src/calc/core.py:5, src/calc/summary.py:29 | `test_version_string` tests/test_core.py:62 (passed · ASSERTS); `test_summary_rounds_the_exact_sum_once` tests/test_summary.py:22 (passed · ASSERTS) |
| E-01 | UNVERIFIED | Negative inputs to `scale` | src/calc/core.py:29 | `test_scale_negative` tests/test_core.py:52 (unrun · —) |
| E-02 | PASSING | Empty list passed to `scale` | src/calc/core.py:29 | `(file)` tests/test_core.py:1 (unrun · —); `test_scale_empty` tests/test_core.py:57 (passed · ASSERTS) |
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
| R-01 | tests/test_core.py `test_add` | ASSERTS | `add(a, b)` MUST return the arithmetic sum of `a` and `b`. | tests/test_core.py:16 | mock: assertion token on 1 line(s) |
| R-01 | tests/test_summary.py `test_summary_module_does_not_change_add` | ASSERTS | `add(a, b)` MUST return the arithmetic sum of `a` and `b`. | tests/test_summary.py:53, tests/test_summary.py:54 | mock: assertion token on 2 line(s) |
| R-02 | tests/test_core.py `test_subtract` | ASSERTS | `subtract(a, b)` MUST return `a - b`. | tests/test_core.py:26 | mock: assertion token on 1 line(s) |
| C-01 | tests/test_core.py `test_divide_by_zero` | ASSERTS | `divide(a, b)` raises `ZeroDivisionError` when `b == 0` The error message MUST … | tests/test_core.py:36 | mock: assertion token on 1 line(s) |
| C-04 | tests/test_summary.py `test_summary_shape` | ASSERTS | Summary report: `summarize(values)` and the `Summary` shape ```python @dataclas… | tests/test_summary.py:13, tests/test_summary.py:14, tests/test_summary.py:15, tests/test_summary.py:16, tests/test_summary.py:17 | mock: assertion token on 5 line(s) |
| C-04 | tests/test_summary.py `test_summary_rounds_the_exact_sum_once` | ASSERTS | Summary report: `summarize(values)` and the `Summary` shape ```python @dataclas… | tests/test_summary.py:23, tests/test_summary.py:24 | mock: assertion token on 2 line(s) |
| C-04 | tests/test_summary.py `test_summary_ordering_is_stable_ascending` | ASSERTS | Summary report: `summarize(values)` and the `Summary` shape ```python @dataclas… | tests/test_summary.py:30, tests/test_summary.py:31, tests/test_summary.py:32, tests/test_summary.py:35 | mock: assertion token on 4 line(s) |
| C-04 | tests/test_summary.py `test_summary_empty_input` | ASSERTS | Summary report: `summarize(values)` and the `Summary` shape ```python @dataclas… | tests/test_summary.py:41, tests/test_summary.py:42 | mock: assertion token on 2 line(s) |
| C-04 | tests/test_summary.py `test_summary_runs_on_a_mixed_list` | EXECUTES_ONLY | Summary report: `summarize(values)` and the `Summary` shape ```python @dataclas… | — | mock: no assertion token |
| C-04 | tests/test_summary.py `test_summary_module_does_not_change_add` | ASSERTS | Summary report: `summarize(values)` and the `Summary` shape ```python @dataclas… | tests/test_summary.py:53, tests/test_summary.py:54 | mock: assertion token on 2 line(s) |
| I-001 | tests/test_core.py `test_add_commutes` | ASSERTS | `add` is commutative: `add(a, b) == add(b, a)` for all finite inputs. | tests/test_core.py:21 | mock: assertion token on 1 line(s) |
| I-002 | tests/test_core.py `test_scale_runs` | EXECUTES_ONLY | `scale` preserves the length of its input list. | — | mock: no assertion token |
| K-02 | tests/test_core.py `test_version_string` | ASSERTS | Every result is rounded to two decimal places with `round(x, 2)`. | tests/test_core.py:65 | mock: assertion token on 1 line(s) |
| K-02 | tests/test_summary.py `test_summary_rounds_the_exact_sum_once` | ASSERTS | Every result is rounded to two decimal places with `round(x, 2)`. | tests/test_summary.py:23, tests/test_summary.py:24 | mock: assertion token on 2 line(s) |
| E-02 | tests/test_core.py `test_scale_empty` | ASSERTS | Empty list passed to `scale` | tests/test_core.py:58 | mock: assertion token on 1 line(s) |
| T-01 | tests/test_core.py `test_add` | ASSERTS | `add` returns the sum for integers and floats. (R-01) | tests/test_core.py:16 | mock: assertion token on 1 line(s) |
| T-02 | tests/test_core.py `test_divide_by_zero` | ASSERTS | `divide` by zero raises with the dividend in the message. (C-01) | tests/test_core.py:36 | mock: assertion token on 1 line(s) |
| T-04 | tests/test_summary.py `test_summary_shape` | ASSERTS | `summarize` returns the pinned `Summary` shape: field names, order, types, `cou… | tests/test_summary.py:13, tests/test_summary.py:14, tests/test_summary.py:15, tests/test_summary.py:16, tests/test_summary.py:17 | mock: assertion token on 5 line(s) |
| T-05 | tests/test_summary.py `test_summary_rounds_the_exact_sum_once` | ASSERTS | `summarize` rounds the exact sum once: `[0.005, 0.005]` totals `0.01`. (C-04 ru… | tests/test_summary.py:23, tests/test_summary.py:24 | mock: assertion token on 2 line(s) |
| T-06 | tests/test_summary.py `test_summary_ordering_is_stable_ascending` | ASSERTS | `summarize` orders ascending with a stable sort and reports `smallest`/`largest… | tests/test_summary.py:30, tests/test_summary.py:31, tests/test_summary.py:32, tests/test_summary.py:35 | mock: assertion token on 4 line(s) |
| T-07 | tests/test_summary.py `test_summary_empty_input` | ASSERTS | `summarize([])` is the all-empty `Summary` with `mean` `None` and `total` `0.0`… | tests/test_summary.py:41, tests/test_summary.py:42 | mock: assertion token on 2 line(s) |

## 9. Notes

None.
