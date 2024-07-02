import pytest

from webcode_tk import css_tools as css
from webcode_tk import font_tools as fonts

sample_file_path = "tests/test_files/font-sizes.html"

sample_file = css.get_all_stylesheets_by_file(sample_file_path)


@pytest.fixture
def font_page():
    return sample_file[0]


@pytest.fixture
def font_page_styles(font_page):
    return sample_file[0].text


def test_font_tools_for_num_keywords(font_page_styles):
    keywords = fonts.get_absolute_keyword_values(font_page_styles)
    assert len(keywords) == 11


def test_get_absolute_keyword_values_with_stylesheet(font_page):
    expected = 11
    results = fonts.get_absolute_keyword_values(font_page)
    assert len(results) == expected


def test_get_numeric_fontsize_values_for_num(font_page_styles):
    expected = 2
    results = fonts.get_numeric_fontsize_values(font_page_styles)
    assert len(results) == expected
