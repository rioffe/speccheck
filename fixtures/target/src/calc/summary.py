"""C-04: `summarize(values)` and the `Summary` shape. Rules 1-6 are numbered in the fixture SPEC."""

from __future__ import annotations

from dataclasses import dataclass

from calc.core import _round


@dataclass(frozen=True)
class Summary:
    count: int
    total: float
    mean: float | None
    ordered: tuple[float, ...]
    smallest: float | None
    largest: float | None


def summarize(values: list[float]) -> Summary:
    """C-04. Rule 5 first (nothing is summed before the check), then rules 1-4 and 6."""
    for i, v in enumerate(values):
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise TypeError(f"summary: non-numeric value at index {i}")
    count = len(values)  # rule 1
    if count == 0:  # rule 6
        return Summary(0, 0.0, None, (), None, None)
    exact = sum(values)
    total = _round(exact)  # rule 2: rounded once, from the exact sum (K-02)
    mean = _round(exact / count)  # rule 3
    ordered = tuple(sorted(values))  # rule 4: sorted() is stable
    return Summary(count, total, mean, ordered, ordered[0], ordered[-1])
