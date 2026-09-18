# Specification Conformance Report

**Spec:** `SPEC.md` · **Judge:** mock (available) · **Strict:** on

## 1. Verdict

speccheck: NOT CONFORMING - 7/14 passing (50.0%), 2 failing, 1 skipped, 1 weak, 1 unverified, 1 untested, 1 uncited; 0 dangling, 0 stale; judge=mock

## 2. Metrics

| Metric | Value |
| --- | --- |
| Declared | 14 |
| Retired | 0 |
| In scope | 14 |
| Conformance | 7/14 (0.5000) |
| PASSING | 7 |
| WEAKLY_PASSING | 1 |
| FAILING | 2 |
| SKIPPED | 1 |
| UNVERIFIED | 1 |
| UNTESTED | 1 |
| UNCITED | 1 |
| Judge strength | 7/8 (0.8750) |
| Unknown rate | 0.0000 |

| Family | In scope | Passing | Ratio |
| --- | --- | --- | --- |
| R | 3 | 2 | 0.6667 |
| C | 2 | 1 | 0.5000 |
| I | 2 | 1 | 0.5000 |
| K | 2 | 0 | 0.0000 |
| E | 2 | 1 | 0.5000 |
| T | 3 | 2 | 0.6667 |

## 3. Per-ID evidence

| ID | Status | Statement | Source citations | Test citations (outcome · verdict) |
| --- | --- | --- | --- | --- |
| R-01 | PASSING | `add(a, b)` MUST return the arithmetic sum of `a` and `b`. | Sources/Calc/Calc.swift:7 | `add` Tests/CalcTests/CalcTests.swift:8 (passed · ASSERTS); `testVersionString` Tests/CalcTests/LegacyTests.swift:7 (passed · ASSERTS) |
| R-02 | PASSING | `subtract(a, b)` MUST return `a - b`. | Sources/Calc/Calc.swift:12 | `subtract` Tests/CalcTests/CalcTests.swift:19 (passed · ASSERTS) |
| R-03 | UNCITED | `multiply(a, b)` MUST return the product of `a` and `b`. | — | — |
| C-01 | PASSING | `divide(a, b)` throws `CalcError.divideByZero(dividend:)` when `b == 0` | Sources/Calc/Calc.swift:4, Sources/Calc/Calc.swift:17 | `divideByZero` Tests/CalcTests/CalcTests.swift:29 (passed · ASSERTS) |
| C-02 | UNTESTED | `scale(values, by:)` returns a new array and never mutates its input | Sources/Calc/Calc.swift:23 | — |
| I-001 | PASSING | `add` is commutative: `add(a, b) == add(b, a)` for all finite inputs. | Sources/Calc/Calc.swift:9 | `addCommutes` Tests/CalcTests/CalcTests.swift:14 (passed · ASSERTS) |
| I-002 | WEAKLY_PASSING | `scale` preserves the length of its input. | — | `scaleRuns` Tests/CalcTests/CalcTests.swift:42 (passed · EXECUTES_ONLY) |
| K-01 | SKIPPED | `divide` completes in under 1 ms for inputs below 10^6. (the `**[port]**` decoration exercises E-44) | — | `divideFast` Tests/CalcTests/CalcTests.swift:36 (skipped · —) |
| K-02 | FAILING | Every result is rounded to two decimal places. | Sources/Calc/Calc.swift:7, Sources/Calc/Calc.swift:12, Sources/Calc/Calc.swift:28 | `subtractPrecision` Tests/CalcTests/CalcTests.swift:24 (failed · —) |
| E-01 | UNVERIFIED | Negative inputs to `scale` | — | `(file)` Tests/CalcTests/CalcTests.swift:54 (unrun · —) |
| E-02 | PASSING | Empty array passed to `scale` | Sources/Calc/Calc.swift:23 | `scaleEmpty` Tests/CalcTests/CalcTests.swift:48 (passed · ASSERTS) |
| T-01 | PASSING | `add` returns the sum for integers and floats. (R-01) | — | `add` Tests/CalcTests/CalcTests.swift:8 (passed · ASSERTS) |
| T-02 | PASSING | `divide` by zero throws with the dividend in the error. (C-01) | — | `divideByZero` Tests/CalcTests/CalcTests.swift:29 (passed · ASSERTS) |
| T-03 | FAILING | `subtract` of floats keeps two-decimal precision. (R-02, K-02) | — | `subtractPrecision` Tests/CalcTests/CalcTests.swift:24 (failed · —) |

## 4. Dangling citations

None.

## 5. Stale citations

None.

## 6. Unattributed results

| Classname | Name | Outcome |
| --- | --- | --- |
| CalcTests.GoneTests | testVanished | passed |

## 7. Unrun test citations

| ID | File | Name |
| --- | --- | --- |
| E-01 | Tests/CalcTests/CalcTests.swift | (file) |

## 8. Judge details

| ID | Test | Verdict | Evidence | Rationale |
| --- | --- | --- | --- | --- |
| R-01 | Tests/CalcTests/CalcTests.swift `add` | ASSERTS | Tests/CalcTests/CalcTests.swift:11 | mock: assertion token on 1 line(s) |
| R-01 | Tests/CalcTests/LegacyTests.swift `testVersionString` | ASSERTS | Tests/CalcTests/LegacyTests.swift:9, Tests/CalcTests/LegacyTests.swift:10 | mock: assertion token on 2 line(s) |
| R-02 | Tests/CalcTests/CalcTests.swift `subtract` | ASSERTS | Tests/CalcTests/CalcTests.swift:21 | mock: assertion token on 1 line(s) |
| C-01 | Tests/CalcTests/CalcTests.swift `divideByZero` | ASSERTS | Tests/CalcTests/CalcTests.swift:31 | mock: assertion token on 1 line(s) |
| I-001 | Tests/CalcTests/CalcTests.swift `addCommutes` | ASSERTS | Tests/CalcTests/CalcTests.swift:16 | mock: assertion token on 1 line(s) |
| I-002 | Tests/CalcTests/CalcTests.swift `scaleRuns` | EXECUTES_ONLY | — | mock: no assertion token |
| E-02 | Tests/CalcTests/CalcTests.swift `scaleEmpty` | ASSERTS | Tests/CalcTests/CalcTests.swift:50 | mock: assertion token on 1 line(s) |
| T-01 | Tests/CalcTests/CalcTests.swift `add` | ASSERTS | Tests/CalcTests/CalcTests.swift:11 | mock: assertion token on 1 line(s) |
| T-02 | Tests/CalcTests/CalcTests.swift `divideByZero` | ASSERTS | Tests/CalcTests/CalcTests.swift:31 | mock: assertion token on 1 line(s) |

## 9. Notes

- undelimited tests in Tests/CalcTests/CalcTests.swift: CalcTests.testScaleNegative
