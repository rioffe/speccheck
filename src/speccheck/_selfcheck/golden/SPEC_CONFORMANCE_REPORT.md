# Specification Conformance Report

**Spec:** `SPEC.md` · **Judge:** mock (available) · **Strict:** on

## 1. Verdict

speccheck: NOT CONFORMING - 8/14 passing (57.1%), 1 failing, 1 skipped, 1 weak, 1 unverified, 1 untested, 1 uncited; 1 dangling, 1 stale; judge=mock

## 2. Metrics

| Metric | Value |
| --- | --- |
| Declared | 16 |
| Retired | 2 |
| In scope | 14 |
| Conformance | 8/14 (0.5714) |
| PASSING | 8 |
| WEAKLY_PASSING | 1 |
| FAILING | 1 |
| SKIPPED | 1 |
| UNVERIFIED | 1 |
| UNTESTED | 1 |
| UNCITED | 1 |
| Judge strength | 8/9 (0.8889) |
| Unknown rate | 0.0000 |

| Family | In scope | Passing | Ratio |
| --- | --- | --- | --- |
| R | 3 | 2 | 0.6667 |
| C | 2 | 1 | 0.5000 |
| I | 2 | 1 | 0.5000 |
| K | 2 | 1 | 0.5000 |
| E | 2 | 1 | 0.5000 |
| T | 3 | 2 | 0.6667 |

## 3. Per-ID evidence

| ID | Status | Statement | Source citations | Test citations (outcome · verdict) |
| --- | --- | --- | --- | --- |
| R-01 | PASSING | `add(a, b)` MUST return the arithmetic sum of `a` and `b`. | src/calc/core.py:10 | `test_add` tests/test_core.py:15 (passed · ASSERTS) |
| R-02 | PASSING | `subtract(a, b)` MUST return `a - b`. | src/calc/core.py:15 | `test_subtract` tests/test_core.py:25 (passed · ASSERTS) |
| R-03 | UNCITED | `multiply(a, b)` MUST return the product of `a` and `b`. | — | — |
| ~~R-04~~ | RETIRED | `modulo(a, b)` MUST return `a % b`. (retired: dropped from the brief) | — | — |
| C-01 | PASSING | `divide(a, b)` raises `ZeroDivisionError` when `b == 0` | src/calc/core.py:20 | `test_divide_by_zero` tests/test_core.py:35 (passed · ASSERTS) |
| C-02 | UNTESTED | `scale(values, factor)` returns a new list and never mutates its input | src/calc/core.py:27 | — |
| ~~C-03~~ | RETIRED | `average(values)` returns the arithmetic mean (retired) | — | — |
| I-001 | PASSING | `add` is commutative: `add(a, b) == add(b, a)` for all finite inputs. | src/calc/core.py:10 | `test_add_commutes` tests/test_core.py:20 (passed · ASSERTS) |
| I-002 | WEAKLY_PASSING | `scale` preserves the length of its input list. | src/calc/core.py:27 | `test_scale_runs` tests/test_core.py:47 (passed · EXECUTES_ONLY) |
| K-01 | SKIPPED | `divide` completes in under 1 ms for inputs below 10^6. | src/calc/core.py:20 | `test_divide_fast` tests/test_core.py:42 (skipped · —) |
| K-02 | PASSING | Every result is rounded to two decimal places with `round(x, 2)`. | src/calc/core.py:1, src/calc/core.py:5 | `test_version_string` tests/test_core.py:62 (passed · ASSERTS) |
| E-01 | UNVERIFIED | Negative inputs to `scale` | src/calc/core.py:29 | `test_scale_negative` tests/test_core.py:52 (unrun · —) |
| E-02 | PASSING | Empty list passed to `scale` | src/calc/core.py:29 | `(file)` tests/test_core.py:1 (unrun · —); `test_scale_empty` tests/test_core.py:57 (passed · ASSERTS) |
| T-01 | PASSING | `add` returns the sum for integers and floats. (R-01) | — | `test_add` tests/test_core.py:15 (passed · ASSERTS) |
| T-02 | PASSING | `divide` by zero raises with the dividend in the message. (C-01) | — | `test_divide_by_zero` tests/test_core.py:35 (passed · ASSERTS) |
| T-03 | FAILING | `subtract` of floats keeps two-decimal precision. (R-02, K-02) | — | `test_subtract_precision` tests/test_core.py:30 (failed · —) |

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

| ID | Test | Verdict | Evidence | Rationale |
| --- | --- | --- | --- | --- |
| R-01 | tests/test_core.py `test_add` | ASSERTS | tests/test_core.py:16 | mock: assertion token on 1 line(s) |
| R-02 | tests/test_core.py `test_subtract` | ASSERTS | tests/test_core.py:26 | mock: assertion token on 1 line(s) |
| C-01 | tests/test_core.py `test_divide_by_zero` | ASSERTS | tests/test_core.py:36 | mock: assertion token on 1 line(s) |
| I-001 | tests/test_core.py `test_add_commutes` | ASSERTS | tests/test_core.py:21 | mock: assertion token on 1 line(s) |
| I-002 | tests/test_core.py `test_scale_runs` | EXECUTES_ONLY | — | mock: no assertion token |
| K-02 | tests/test_core.py `test_version_string` | ASSERTS | tests/test_core.py:65 | mock: assertion token on 1 line(s) |
| E-02 | tests/test_core.py `test_scale_empty` | ASSERTS | tests/test_core.py:58 | mock: assertion token on 1 line(s) |
| T-01 | tests/test_core.py `test_add` | ASSERTS | tests/test_core.py:16 | mock: assertion token on 1 line(s) |
| T-02 | tests/test_core.py `test_divide_by_zero` | ASSERTS | tests/test_core.py:36 | mock: assertion token on 1 line(s) |

## 9. Notes

None.
