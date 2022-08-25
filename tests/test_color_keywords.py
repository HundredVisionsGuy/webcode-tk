#!/usr/bin/env python
"""Tests for `colortools` package."""
import pytest

from webcode_tk import color_keywords as keywords


@pytest.fixture
def basic_keywords():
    basic_keywords = keywords.get_basic_color_keywords()
    yield basic_keywords


@pytest.fixture
def full_color_keywords():
    full_color = keywords.get_full_color_keywords()
    yield full_color


@pytest.fixture
def all_keywords():
    all = keywords.get_all_keywords()
    yield all


def test_get_basic_color_keywords_for_valid_color(basic_keywords):
    assert basic_keywords["fuchsia"] == "#FF00FF"


def test_get_basic_color_keywords_for_dict_type(basic_keywords):
    assert isinstance(basic_keywords, dict)


def test_get_full_color_keywords_for_basic(full_color_keywords):
    assert "lime" in full_color_keywords.keys()


def test_get_full_color_keywords_for_extended(full_color_keywords):
    assert "rebeccapurple" in full_color_keywords.keys()


def test_get_all_keywords_for_dodgerblue(all_keywords):
    assert "dodgerblue" in all_keywords


def test_get_all_keywords_for_thistle(all_keywords):
    # just because thistle
    assert "thistle" in all_keywords


def test_is_a_keyword_for_papayawhip():
    assert keywords.is_a_keyword("papayawhip")


def test_is_a_keyword_for_misspelled_keyword():
    assert not keywords.is_a_keyword("siena")


def test_is_a_keyword_for_nonexistent_keyword():
    assert not keywords.is_a_keyword("dolewhip")


def test_get_hex_by_keyword_for_burlywood():
    results = keywords.get_hex_by_keyword("burlywood")
    assert results == "#DEB887"


def test_get_hex_by_keyword_for_honeydew():
    results = keywords.get_hex_by_keyword("honeydew")
    assert results == "#F0FFF0"
