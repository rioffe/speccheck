# SPECIFICATION — `calc` (golden fixture for speccheck)

> - **Status:** fixture v1.3 — a deliberately defective project used by T-46/T-47 and `--self-check`; v1.1 added the long-body contract C-04 and its labeled tests for T-49/T-76; v1.2 adds a decision table for T-79/T-80/T-81; v1.3 adds the cross-references and the eight adjacent tests of T-76/T-84 (each paired with a genuine test that uses the same calls and asserts the id's own clause)
> - **Scope:** a four-function calculator with rounding; every planted defect is listed at the end

## 0. Intent

`calc` adds, subtracts, divides, and scales numbers, rounding results to two decimal places.
The fixture exists so that every `speccheck` status has one live example.

## 2. Requirements

| ID | Statement | Source |
| -- | --------- | ------ |
| **R-01** | `add(a, b)` MUST return the arithmetic sum of `a` and `b`, rounded per K-02. | brief |
| **R-02** | `subtract(a, b)` MUST return `a - b`, rounded per K-02. | brief |
| **R-03** | `multiply(a, b)` MUST return the product of `a` and `b`. | brief |
| ~~**R-04**~~ | `modulo(a, b)` MUST return `a % b`. (retired: dropped from the brief) | brief |

## 4. Contracts

### C-01 `divide(a, b)` raises `ZeroDivisionError` when `b == 0`

The error message MUST name the dividend.

### C-02 `scale(values, factor)` returns a new list and never mutates its input

### ~~C-03~~ `average(values)` returns the arithmetic mean (retired)

### C-04 Summary report: `summarize(values)` and the `Summary` shape

```python
@dataclass(frozen=True)
class Summary:
    count: int                 # rule 1: number of input values, including duplicates
    total: float               # rule 2: the K-02-rounded sum of the inputs
    mean: float | None         # rule 3: total / count rounded per K-02; None when count == 0
    ordered: tuple[float, ...] # rule 4: the inputs sorted ascending, ties kept in input order
    smallest: float | None     # rule 4: ordered[0], or None when empty
    largest: float | None      # rule 4: ordered[-1], or None when empty

def summarize(values: list[float]) -> Summary: ...   # pure; never mutates `values`
```

Rules (normative; each is one clause a test may assert on its own):

1. **Shape.** `summarize` returns a `Summary` whose fields are exactly `count`, `total`, `mean`,
   `ordered`, `smallest`, `largest`, in that order, with the types shown. `count` equals
   `len(values)`; a value that appears twice is counted twice. The result is immutable
   (`frozen=True`): assigning a field raises `FrozenInstanceError`.
2. **Rounding.** `total` is the sum of the inputs rounded per K-02 — `round(sum(values), 2)` — and
   never the sum of the individually rounded inputs, so `summarize([0.005, 0.005]).total == 0.01`
   while `add(0.005, 0.0) + add(0.005, 0.0)` would give `0.02`. The rounding is applied once, to
   the exact sum.
3. **Mean.** `mean` is `round(total_exact / count, 2)` where `total_exact` is the unrounded sum;
   it is `None` — not `0.0`, not `NaN` — when `count == 0`. `summarize([1, 2]).mean == 1.5`;
   `summarize([1, 1, 2]).mean == 1.33`.
4. **Ordering.** `ordered` is the inputs sorted ascending by value; equal values keep their input
   order (a stable sort), so `summarize([2.0, 1, 2]).ordered == (1, 2.0, 2)` with the float `2.0`
   before the int `2`. `smallest` is `ordered[0]` and `largest` is `ordered[-1]`; both are `None`
   for an empty input. The input list itself is not reordered.
5. **Error text.** A non-numeric value (anything that is not an `int` or a `float`; `bool` counts
   as non-numeric here) raises `TypeError` whose message is exactly
   `summary: non-numeric value at index <i>` for the first offending index; nothing is summed
   before the check, so a later offending value is never reached.
6. **Empty input.** `summarize([])` returns `Summary(count=0, total=0.0, mean=None, ordered=(),
   smallest=None, largest=None)` and does not raise; `total` is the float `0.0`, not the int `0`.

The contract exists for speccheck's own judge evaluation (its T-49 / T-76): its body is long and has
several independent clauses, so a judge that grades a test against the gist of the whole contract
rather than against the clause the test asserts is caught by the labels in `golden/judge_labels.json`.

## 6. Invariants

| ID | Invariant |
| -- | --------- |
| **I-001** | `add` is commutative, per R-01: `add(a, b) == add(b, a)` for all finite inputs; both calls are rounded per K-02. |
| **I-002** | `scale` (C-02) preserves the length of its input list. |

## 7. Constraints

| ID | Constraint |
| -- | ---------- |
| **K-01** | `divide` completes in under 1 ms for inputs below 10^6. |
| **K-02** | Every result is rounded to two decimal places with `round(x, 2)`. |

## 8. Edge cases

| ID | Case | Semantics |
| -- | ---- | --------- |
| **E-01** | Negative inputs to `scale` | Scaled like any other value; sign preserved. |
| **E-02** | Empty list passed to `scale` (per C-02) | Returns a new empty list; the input list is not mutated. |
| **E-03** | A `ZeroDivisionError` raised by `divide`, per C-01, reached from a caller | Propagates unchanged: the same exception type and message, with nothing wrapped around it. |

## 9. Acceptance tests

| ID | Test |
| -- | ---- |
| **T-01** | `add` returns the sum for integers and floats. (R-01) |
| **T-02** | `divide` by zero raises with the dividend in the message. (C-01) |
| **T-03** | `subtract` of floats keeps two-decimal precision. (R-02, K-02) |
| **T-04** | `summarize` returns the pinned `Summary` shape: field names, order, types, `count` including duplicates, frozen. (C-04 rule 1) |
| **T-05** | `summarize` rounds the exact sum once: `[0.005, 0.005]` totals `0.01`. (C-04 rule 2, K-02) |
| **T-06** | `summarize` orders ascending with a stable sort and reports `smallest`/`largest`. (C-04 rule 4) |
| **T-07** | `summarize([])` is the all-empty `Summary` with `mean` `None` and `total` `0.0`. (C-04 rule 6) |

```text
Example IDs inside a fence are not declarations: R-20, C-08, T-40.
```

## 12. Decisions

| ID | Decision | Default | Alternatives | Affects | Owner |
| -- | -------- | ------- | ------------- | ------- | ----- |
| D-01 | Rounding library | stdlib `round()` | `decimal.Decimal` | K-02, C-04 | fixture |
| D-02 | Legacy `average` | dropped, replaced by C-04 | keep `average` as a compatibility shim | C-03 | fixture |
| D-03 | Negative-index guard | not yet specified | add a dedicated edge case | E-45 | fixture |

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
- D-01's *Affects* cell names two declared ids (K-02, C-04); D-02's names the retired C-03
  (an `affects` edge with `retired: true`); D-03's names E-45, undeclared *in this fixture*
  (a Note, no edge; T-79) — chosen because it is a real id of the outer speccheck project,
  so this fixture's packaged copy under `src/speccheck/_selfcheck/` does not dangle-cite it
  when the outer suite scans its own `src/`.
