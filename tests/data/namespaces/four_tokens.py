# speccheck:ignore-file — line 1 is dropped by tests/test_16_namespaces.py (F-713)
"""Fixture for T-107: four foreign references on one line."""


def test_many():
    """platform:R-04 platform:R-03 other:R-02 x-y:R-01"""
    assert True
