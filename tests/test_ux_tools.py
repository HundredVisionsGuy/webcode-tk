#!/usr/bin/env python
"""Tests for `colortools` package."""
import pytest
from file_clerk import clerk

from webcode_tk import ux_tools


@pytest.fixture
def automate_text():
    sample = clerk.file_to_string("tests/test_files/automate_boring_stuff.txt")
    return sample


@pytest.fixture
def css_basics():
    sample = clerk.file_to_string("tests/test_files/css_basics.txt")
    return sample


def test_get_flesch_kincaid_grade_level_for_9_7(automate_text):
    results = ux_tools.get_flesch_kincaid_grade_level(automate_text)
    expected = 9.7
    assert results == expected


def test_get_flesch_kincaid_grade_level_for_4_5(css_basics):
    results = ux_tools.get_flesch_kincaid_grade_level(css_basics)
    expected = 4.5
    assert results == expected
