"""Fixture for T-57: a line-level ignore marker inside a test case."""


def test_marker():
    """C-01 is cited normally on this line."""
    x = 1  # R-01 speccheck:ignore
    assert x == 1  # R-01
