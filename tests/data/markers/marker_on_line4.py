"""Fixture for T-57: a file-level marker on line 4 has no file-level effect."""


# speccheck:ignore-file (too late: line 4)
def test_scanned():
    """R-01"""
    assert True
