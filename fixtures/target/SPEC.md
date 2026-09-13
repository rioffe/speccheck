# SPECIFICATION — `calc` (golden fixture for speccheck)

> - **Status:** fixture v1.0 — a deliberately defective project used by T-46/T-47 and `--self-check`
> - **Scope:** a four-function calculator with rounding; every planted defect is listed at the end

## 0. Intent

`calc` adds, subtracts, divides, and scales numbers, rounding results to two decimal places.
The fixture exists so that every `speccheck` status has one live example.

## 2. Requirements

| ID | Statement | Source |
| -- | --------- | ------ |
| **R-01** | `add(a, b)` MUST return the arithmetic sum of `a` and `b`. | brief |
| **R-02** | `subtract(a, b)` MUST return `a - b`. | brief |
| **R-03** | `multiply(a, b)` MUST return the product of `a` and `b`. | brief |
| ~~**R-04**~~ | `modulo(a, b)` MUST return `a % b`. (retired: dropped from the brief) | brief |

## 4. Contracts

### C-01 `divide(a, b)` raises `ZeroDivisionError` when `b == 0`

The error message MUST name the dividend.

### C-02 `scale(values, factor)` returns a new list and never mutates its input

### ~~C-03~~ `average(values)` returns the arithmetic mean (retired)

## 6. Invariants

| ID | Invariant |
| -- | --------- |
| **I-001** | `add` is commutative: `add(a, b) == add(b, a)` for all finite inputs. |
| **I-002** | `scale` preserves the length of its input list. |

## 7. Constraints

| ID | Constraint |
| -- | ---------- |
| **K-01** | `divide` completes in under 1 ms for inputs below 10^6. |
| **K-02** | Every result is rounded to two decimal places with `round(x, 2)`. |

## 8. Edge cases

| ID | Case | Semantics |
| -- | ---- | --------- |
| **E-01** | Negative inputs to `scale` | Scaled like any other value; sign preserved. |
| **E-02** | Empty list passed to `scale` | Returns an empty list. |

## 9. Acceptance tests

| ID | Test |
| -- | ---- |
| **T-01** | `add` returns the sum for integers and floats. (R-01) |
| **T-02** | `divide` by zero raises with the dividend in the message. (C-01) |
| **T-03** | `subtract` of floats keeps two-decimal precision. (R-02, K-02) |

```text
Example IDs inside a fence are not declarations: R-20, C-08, T-40.
```

## Planted defects (for T-46 / T-47)

- `R-03` is never cited anywhere (UNCITED).
- `C-02` is cited in `src/` only (UNTESTED).
- `E-01` is cited by `test_scale_negative`, which has no result in `junit.xml` (UNVERIFIED).
- `T-03` is cited by `test_subtract_precision`, which fails (FAILING).
- `K-01` is cited by `test_divide_fast`, which is skipped (SKIPPED).
- `I-002` is cited only by `test_scale_runs`, which has no assertion (EXECUTES_ONLY -> WEAKLY_PASSING).
- `src/calc/core.py` cites `R-09`, which is not declared (dangling).
- `src/calc/legacy.py` cites retired `R-04` (stale).
- `junit.xml` carries a result for `tests.test_gone::test_vanished` (unattributed).
- The module docstring of `tests/test_core.py` cites `E-02` (file-level citation).
