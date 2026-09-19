"""Summary-contract tests: four assert one clause each; one only runs the code; one asserts another id."""

import dataclasses

import pytest

from calc import Summary, add, summarize


def test_summary_shape():
    """T-04: the pinned Summary shape — fields, order, types, duplicates counted, frozen (C-04)."""
    s = summarize([2, 2, 3.5])
    assert isinstance(s, Summary)
    assert [f.name for f in dataclasses.fields(s)] == ["count", "total", "mean", "ordered", "smallest", "largest"]
    assert s.count == 3 and isinstance(s.count, int)
    assert isinstance(s.total, float) and isinstance(s.ordered, tuple)
    with pytest.raises(dataclasses.FrozenInstanceError):
        s.count = 9  # type: ignore[misc]


def test_summary_rounds_the_exact_sum_once():
    """T-05: total is round(sum, 2) applied once, not a sum of rounded inputs (C-04, K-02)."""
    assert summarize([0.005, 0.005]).total == 0.01
    assert summarize([1.004, 1.004, 1.004]).total == 3.01


def test_summary_ordering_is_stable_ascending():
    """T-06: ordered ascending with a stable sort; smallest and largest follow (C-04)."""
    s = summarize([2.0, 1, 2])
    assert s.ordered == (1, 2.0, 2)
    assert isinstance(s.ordered[1], float) and isinstance(s.ordered[2], int)
    assert s.smallest == 1 and s.largest == 2
    src = [3, 1, 2]
    summarize(src)
    assert src == [3, 1, 2]


def test_summary_empty_input():
    """T-07: summarize([]) is the all-empty Summary; mean is None, total is the float 0.0 (C-04)."""
    s = summarize([])
    assert s == Summary(0, 0.0, None, (), None, None)
    assert s.mean is None and isinstance(s.total, float)


def test_summary_runs_on_a_mixed_list():
    """Exercises C-04 on a mixed list of ints and floats; asserts nothing about it."""
    summarize([1, 2.5, 3, 4.75, 5])
    summarize([10])


def test_summary_module_does_not_change_add():
    """R-01 still holds with the summary module imported (cites C-04 for the import only)."""
    assert add(1, 2) == 3
    assert add(0.1, 0.2) == 0.3
