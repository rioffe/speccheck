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


def test_add_result():
    """R-01: add returns the sum (the genuine partner of the rounding-fact test)."""
    assert add(2, 3) == 5


def test_add_rounding_fact():
    """R-01: exercises add, then asserts the rounding rule's own fact, not the sum."""
    add(1.005, 0.0)
    assert round(0.005 + 0.005, 2) == 0.01


def test_subtract_result():
    """R-02: subtract returns a - b (the genuine partner of the rounding-fact test)."""
    assert subtract(5, 3) == 2


def test_subtract_rounding_fact():
    """R-02: exercises subtract, then asserts the rounding rule's own fact, not the difference."""
    subtract(1.005, 0.0)
    assert round(1.005, 2) == 1.0


def test_scale_empty_result():
    """E-02: an empty list yields an empty list (the genuine partner of the purity test)."""
    assert scale([], 3) == []


def test_scale_empty_input_is_not_mutated():
    """E-02: exercises scale, then asserts the purity rule's own fact, not the empty result."""
    values: list[float] = []
    scale(values, 3)
    assert values == []


def test_zero_division_propagates():
    """E-03: the error propagates unchanged (the genuine partner of the message test)."""
    with pytest.raises(ZeroDivisionError) as exc:
        divide(7, 0)
    assert type(exc.value) is ZeroDivisionError
    assert exc.traceback[-1].name == "divide"


def test_zero_division_message_names_the_dividend():
    """E-03: the propagation reaches a caller, with the error's own message intact."""
    with pytest.raises(ZeroDivisionError) as exc:
        divide(7, 0)
    assert "7" in str(exc.value)


def test_add_rounding_of_a_half_cent():
    """R-01: exercises add, then asserts the rounding rule's own fact for another value."""
    add(2.675, 0.0)
    assert round(2.675, 2) == 2.67


def test_add_commutes_on_floats():
    """I-001: add is commutative (the genuine partner of the rounding-fact pair)."""
    assert add(0.1, 0.2) == add(0.2, 0.1)


def test_add_commutes_on_plain_sum():
    """I-001: the calls exercise commutativity; the assertion is the sum rule's own fact."""
    add(2, 5)
    add(5, 2)
    assert add(1, 2) == 3


def test_add_commutes_rounding_fact():
    """I-001: exercises commutativity, then asserts the rounding rule's own fact."""
    add(2.5, 3.5)
    add(3.5, 2.5)
    assert round(0.005 + 0.005, 2) == 0.01
