# speccheck:ignore-file — line 1 is dropped by tests/test_16_namespaces.py (F-713)
"""Fixture for T-107: a test whose docstring names someone else's id."""


def test_platform_rule():
    """platform:R-04 is the platform spec's rule, not this project's."""
    assert 1 + 1 == 2
