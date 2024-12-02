#!/usr/bin/env python
"""Tests for `colortools` package."""
import pytest
from file_clerk import clerk

from webcode_tk import html_tools
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
def figcaption():
    file = "tests/test_files/large_project/gallery.html"
    markup = html_tools.get_elements("figcaption", file)
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
    assert len(results) == 13


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


def test_get_readability_stats_for_2_paras_in_sample():
    path = "tests/test_files/sample_no_errors.html"
    results = ux_tools.get_readability_stats(path)
    assert results.get("paragraph_count") == 2


def test_get_readability_stats_for_11_words():
    path = "tests/test_files/sample_no_errors.html"
    results = ux_tools.get_readability_stats(path)
    assert results.get("word_count") == 11


def test_remove_extensions_for_two_file_names():
    sample = "Hey, I just removed extensions from main.py and base.css."
    expected = "Hey, I just removed extensions from main and base."
    results = ux_tools.remove_extensions(sample)
    assert results == expected


def test_remove_extensions_for_no_file_names():
    sample = "Sentence one, without a filename. Sentence two: no filename."
    expected = sample
    results = ux_tools.remove_extensions(sample)
    assert results == expected


def test_remove_extensions_for_many_symbols():
    sample = "Image of Aurora Borealis (File:Virmalised 15.09.2017 - Aurora"
    sample += "Borealis 15.09.2017 copy.jpg) by Kristian Pikner "
    sample += "[CC BY-SA 4.0]."
    expected = "Image of Aurora Borealis (File:Virmalised 15 - Aurora"
    expected += "Borealis 15 copy) by Kristian Pikner [CC BY-SA 4]."
    results = ux_tools.remove_extensions(sample)
    assert results == expected


def test_get_usability_report_for_css_basics_default_everything(
    css_basics_path,
):
    report = ux_tools.get_usability_report(css_basics_path, ("p",))
    results = []
    for item in report:
        if "1 more sentence than the maximum number of 4" in item:
            results.append(item)
        if "not have enough paragraphs with a single sentence" in item:
            results.append(item)
        if "pass" in item and "words per sentence" in item:
            results.append(item)
        if "does not have enough words" in item and "fail" in item:
            results.append(item)
    results_length = len(results)
    assert results_length == 4


def test_get_usability_report_for_warnings(large_project_path):
    goals = {
        "avg_words_sentence_range": (10, 25),
        "max_sentences_per_paragraph": 4,
        "min_num_single_sentence_paragraphs": 2,
        "min_word_count": 200,
    }
    exceeds = {
        "max_avg_words_sentence": 20,
        "max_li_per_list": 9,
        "max_words_per_li": 45,
        "max_words_per_paragraph": 80,
        "min_word_count": 500,
    }
    report = ux_tools.get_usability_report(
        large_project_path, ("p",), goals, exceeds
    )
    failures = 0
    passing = 0
    warnings = 0
    for item in report:
        if "warning: for best results" in item:
            if "words in your project" in item:
                warnings += 1
        if "fail:" in item:
            failures += 1
        if "pass:" in item:
            passing += 1
    expected = warnings == 1 and failures == 11 and passing == 1
    assert expected
