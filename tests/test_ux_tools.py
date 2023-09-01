#!/usr/bin/env python
"""Tests for `colortools` package."""
import pytest
from file_clerk import clerk

from webcode_tk import html
from webcode_tk import ux_tools


@pytest.fixture
def automate_path():
    return "tests/test_files/automate_boring_stuff.html"


@pytest.fixture
def automate_text():
    text = clerk.file_to_string("tests/test_files/automate_paragraph_text.txt")
    return text.strip()


@pytest.fixture
def css_basics_path():
    return "tests/test_files/css_basics.html"


@pytest.fixture
def single_page_path():
    return "tests/test_files/project/sports.html"


@pytest.fixture
def large_project_path():
    return "tests/test_files/large_project/"


@pytest.fixture
def figcaption(large_project_path):
    files = clerk.get_all_files_of_type(large_project_path, "html")
    file = files[0]
    markup = html.get_elements("figcaption", file)
    return markup[0]


def test_get_flesch_kincaid_grade_level_for_12(automate_path):
    results = ux_tools.get_flesch_kincaid_grade_level(automate_path)
    expected = 10.8
    assert results == expected


def test_get_flesch_kincaid_grade_level_for_5_2(css_basics_path):
    results = ux_tools.get_flesch_kincaid_grade_level(css_basics_path)
    expected = 3.8
    assert results == expected


def test_get_all_paragraphs_for_single_page(automate_path):
    results = ux_tools.get_all_paragraphs(automate_path)
    assert len(results) == 3


def test_get_paragraph_text_for_automate_page(automate_path, automate_text):
    paragraphs = ux_tools.get_all_paragraphs(automate_path)
    results = ux_tools.get_paragraph_text(paragraphs)
    assert results == automate_text


def test_get_all_paragraphs_for_large_project(large_project_path):
    results = ux_tools.get_all_paragraphs(large_project_path)
    assert len(results) == 4


def test_get_words_per_sentence_for_automate(automate_path):
    results = ux_tools.get_words_per_paragraph(automate_path)
    expected = 55.0
    assert results == expected


def test_simple_page_for_5_and_half_words_per_sentence(single_page_path):
    """simple page has 2 paragraph tags and a header, 11 words in all.
    That's 5.5 words per sentence"""
    results = ux_tools.get_words_per_paragraph(single_page_path)
    expected = 19.0
    assert results == expected


def test_get_text_from_elements_for_length_of_p_and_figcaption(
    large_project_path,
):
    results = ux_tools.get_text_from_elements(
        large_project_path, ["p", "figcaption"]
    )
    assert len(results) == 22


def test_extract_text_for_no_nested_elements(large_project_path):
    results = ux_tools.get_text_from_elements(large_project_path)
    assert "<a href=" not in results[0]


def test_extract_text_for_anchor_nested_in_paragraph(figcaption):
    results = ux_tools.extract_text(figcaption)
    assert "<a href=" not in results
