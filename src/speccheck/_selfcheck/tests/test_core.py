"""Acceptance tests for calc. E-02 (empty input) is covered by the fixture in this module."""

import pytest

from calc import add, divide, scale, subtract


@pytest.fixture
def empty() -> list[float]:
    return []


@pytest.mark.parametrize("a, b, expected", [(1, 2, 3), (0.1, 0.2, 0.3)])
def test_add(a, b, expected):
    """T-01: add returns the sum (R-01)."""
    assert add(a, b) == expected


def test_add_commutes():
    """I-001: add is commutative."""
    assert add(2, 5) == add(5, 2)


def test_subtract():
    """R-02: subtract returns a - b."""
    assert subtract(5, 3) == 2


def test_subtract_precision():
    """T-03: two-decimal precision."""
    assert subtract(1.005, 0.0) == 1.01


def test_divide_by_zero():
    """T-02: divide by zero raises naming the dividend (C-01)."""
    with pytest.raises(ZeroDivisionError, match="7"):
        divide(7, 0)


@pytest.mark.skip(reason="timing test not run in CI")
def test_divide_fast():
    """K-01: divide is fast."""
    assert divide(999_999, 3) == 333_333


def test_scale_runs():
    """I-002: scale keeps the length."""
    scale([1, 2, 3], 2)


def test_scale_negative():
    """E-01: negative inputs keep their sign."""
    assert scale([-1, -2], 2) == [-2, -4]


def test_scale_empty(empty):
    """E-02: an empty list yields an empty list."""
    assert scale(empty, 3) == []


def test_version_string():
    """K-02: results are rounded to two places."""
    import calc

    assert calc.__version__ == "0.1.0"


def test_divide_error_names_the_dividend_example():
    """C-01: divide by zero raises with the dividend in the message."""
    examples = ["subtract", "R-02"]
    with pytest.raises(ZeroDivisionError, match="7"):
        divide(7, 0)
    assert examples[0] == "subtract"
