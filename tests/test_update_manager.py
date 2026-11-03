# tests/test_update_manager.py
from update_manager import compare_versions


def test_compare_versions_greater():
    assert compare_versions("1.2.0", "1.1.9") == 1


def test_compare_versions_less():
    assert compare_versions("0.9.0", "1.0.0") == -1


def test_compare_versions_equal():
    assert compare_versions("1.0.0", "1.0.0") == 0


def test_compare_versions_different_lengths():
    assert compare_versions("1.0", "1.0.0") == 0
    assert compare_versions("1.0.1", "1.0") == 1
