import pytest

from webcode_tk import css_tools as css
from webcode_tk import font_tools as fonts

sample_file_path = "tests/test_files/font-sizes.html"

sample_file = css.get_all_stylesheets_by_file(sample_file_path)

size_unit_test_data = [
    ("14rem", "rem"),
    ("x-small", "absolute_keyword"),
    ("larger", "relative_keyword"),
    ("80%", "percentage"),
    ("0.8em", "em"),
    ("12px", "pixels"),
]


@pytest.mark.parametrize(
    "value,expected",
    size_unit_test_data,
    ids=[
        "rems",
        "absolute_keywords",
        "relative_keywords",
        "percentages",
        "ems",
        "pixels",
    ],
)
def test_get_font_unit(value, expected):
    results = fonts.get_font_unit(value)
    assert results == expected


value_unit_data = [
    ("14rem", (14.0, "rem")),
    ("x-small", ("x-small", "absolute_keyword")),
    ("larger", ("larger", "relative_keyword")),
    ("80%", (80.0, "%")),
    ("0.8em", (0.8, "em")),
    ("12px", (12, "px")),
]


@pytest.mark.parametrize(
    "value,expected",
    value_unit_data,
    ids=["14rem", "x-small", "larger", "80%", "0.8em", "12px"],
)
def test_split_value_unit(value, expected):
    results = fonts.split_value_unit(value)
    assert results == expected


# order: val, unit, parent_size, element, expected
compute_font_size_data = [
    ("initial", "initial", 20.0, "h2", 16.0),
    (
        110,
        "%",
        20.0,
        "span",
        22.0,
    ),
    (110, "percentage", 22.0, "span", 24.2),
    (110, "percent", 24.2, "span", 26.62),
    (1.2, "rem", 20.0, "p", 19.2),
    (1.2, "em", 20.0, "p", 24.0),
    ("x-small", "absolute_keyword", 20.0, "li", 10.0),
    ("larger", "relative_keyword", 13.0, "li", 15.6),
    ("smaller", "relative_keyword", 13.0, "li", 10.83),
    ("unset", "unset", 20.0, "p", 20.0),
    ("revert", "revert", 20.0, "p", 20.0),
    ("revert", "revert", 20.0, "h3", 23.4),
    ("inherit", "inherit", 20.0, "h3", 20.0),
]


@pytest.mark.parametrize(
    "value,unit,parent_size,element,expected",
    compute_font_size_data,
    ids=[
        "initial",
        "%",
        "percentage",
        "percent",
        "rem",
        "em",
        "absolute keyword",
        "relative larger",
        "relative smaller",
        "unset",
        "revert p",
        "revert h3",
        "inherit",
    ],
)
def test_compute_font_size(value, unit, parent_size, element, expected):
    results = fonts.compute_font_size(value, unit, parent_size, element)
    assert results == expected


@pytest.fixture
def font_page():
    return sample_file[0]


@pytest.fixture
def font_page_styles(font_page):
    return sample_file[0].text


def test_font_tools_for_num_keywords(font_page_styles):
    keywords = fonts.get_absolute_keyword_values(font_page_styles)
    assert len(keywords) == 9


def test_get_absolute_keyword_values_with_stylesheet(font_page):
    expected = 9
    results = fonts.get_absolute_keyword_values(font_page)
    assert len(results) == expected


def test_get_numeric_fontsize_values_for_num(font_page_styles):
    expected = 5
    results = fonts.get_numeric_fontsize_values(font_page_styles)
    assert len(results) == expected


def test_compute_keyword_size_for_xxxlarge():
    expected = 48
    results = fonts.compute_keyword_size("xxx-large")
    assert results == expected


def test_compute_rem_for_1_2():
    expected = 19.2
    results = fonts.compute_rem("1.2")
    assert results == expected


def test_is_large_text_for_bold_under_18_66():
    results = fonts.is_large_text(18.6, True)
    expected = False
    assert results == expected


def test_is_large_text_for_bold_at_18_66():
    results = fonts.is_large_text(18.66, True)
    expected = True
    assert results == expected


def test_is_large_text_for_not_bold_at_24():
    results = fonts.is_large_text(24.0, False)
    expected = True
    assert results == expected


def test_is_large_text_for_not_bold_under_24():
    results = fonts.is_large_text(23.9, False)
    expected = False
    assert results == expected
