# speccheck:ignore-file — line 1 is dropped by tests/test_16_namespaces.py (F-713)
"""Fixture for T-107: an uncapped namespace is foreign; an ID-shaped label is not a namespace."""


def test_long_namespace():
    """regulated_platform_core_services_v2_extra:R-04"""
    assert True


def test_colon_pair():
    # R-01:R-02
    assert True
