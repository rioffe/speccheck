# SPECIFICATION — `Calc` (Swift golden fixture for speccheck)

> - **Status:** fixture v1.0 — a deliberately defective SwiftPM project used by T-71
> - **Scope:** a four-function calculator with rounding, in Swift; every planted defect is listed at the end

## 0. Intent

`Calc` adds, subtracts, divides, and scales numbers, rounding results to two decimal places.
The fixture exists so that every `speccheck` status has one live Swift example, with the
citations written where `spec-build` puts them: in the tests' doc comments.

## 2. Requirements

| ID | Statement | Source |
| -- | --------- | ------ |
| **R-01** | `add(a, b)` MUST return the arithmetic sum of `a` and `b`. | brief |
| **R-02** | `subtract(a, b)` MUST return `a - b`. | brief |
| **R-03** | `multiply(a, b)` MUST return the product of `a` and `b`. | brief |

## 4. Contracts

### C-01 `divide(a, b)` throws `CalcError.divideByZero(dividend:)` when `b == 0`

The error MUST carry the dividend.

### C-02 `scale(values, by:)` returns a new array and never mutates its input

## 6. Invariants

| ID | Invariant |
| -- | --------- |
| **I-001** | `add` is commutative: `add(a, b) == add(b, a)` for all finite inputs. |
| **I-002** | `scale` preserves the length of its input. |

## 7. Constraints

| ID | Constraint |
| -- | ---------- |
| **K-01** **[port]** | `divide` completes in under 1 ms for inputs below 10^6. (the `**[port]**` decoration exercises E-44) |
| **K-02** | Every result is rounded to two decimal places. |

## 8. Edge cases

| ID | Case | Semantics |
| -- | ---- | --------- |
| **E-01** | Negative inputs to `scale` | Scaled like any other value; sign preserved. |
| **E-02** | Empty array passed to `scale` | Returns an empty array. |

## 9. Acceptance tests

| ID | Test |
| -- | ---- |
| **T-01** | `add` returns the sum for integers and floats. (R-01) |
| **T-02** | `divide` by zero throws with the dividend in the error. (C-01) |
| **T-03** | `subtract` of floats keeps two-decimal precision. (R-02, K-02) |

## Planted defects (for T-71)

- `R-03` is never cited anywhere (UNCITED).
- `C-02` is cited in `Sources/` only (UNTESTED).
- `E-01` is cited by `testScaleNegative`, a `test*` function with no `@Test` inside a non-`XCTestCase` type: undelimited (E-43), so its citation is file-level (UNVERIFIED).
- `T-03` and `K-02` are cited by `subtractPrecision`, which fails (FAILING).
- `K-01` is cited by `divideFast`, which is `.disabled` and therefore `<skipped>` (SKIPPED); its declaring row carries `**[port]**` decoration (E-44).
- `I-002` is cited only by `scaleRuns`, which has no assertion (EXECUTES_ONLY -> WEAKLY_PASSING).
- `junit.xml` carries a result for `CalcTests.GoneTests::testVanished` (unattributed).
- `add(a:b:expected:)` is a parameterized test: one `<testcase>` whose name is the signature (C-04 step 2).
- `Edges.scaleEmpty` is a nested suite (`CalcTests.CalcTests.Edges`); `LegacyTests.testVersionString` is XCTest.
