"""Core arithmetic for the golden fixture. Every result is rounded per K-02."""


def _round(x: float) -> float:
    # K-02: two decimal places
    return round(x, 2)


def add(a: float, b: float) -> float:
    """R-01: the arithmetic sum. I-001 holds because float addition commutes."""
    return _round(a + b)


def subtract(a: float, b: float) -> float:
    """R-02: a - b."""
    return _round(a - b)


def divide(a: float, b: float) -> float:
    """C-01: raises ZeroDivisionError naming the dividend when b == 0. K-01: O(1)."""
    if b == 0:
        raise ZeroDivisionError(f"cannot divide {a} by zero")
    return _round(a / b)


def scale(values: list[float], factor: float) -> list[float]:
    """C-02: returns a new list, input untouched. I-002: same length.

    E-01: negative inputs scale like any other value. E-02: an empty list yields [].
    Overflow handling is R-09 territory and not implemented here.
    """
    return [_round(v * factor) for v in values]
