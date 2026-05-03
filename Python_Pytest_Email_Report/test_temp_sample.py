import pytest


def test_sample_pass():
    assert 2 + 2 == 4


def test_sample_fail():
    assert 3 * 3 == 9


def test_sample_skip():
    pytest.skip("Temporary skip for sample report")
