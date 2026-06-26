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
    (110, "percent", 24.2, "span", 26.6),
    (1.2, "rem", 20.0, "p", 19.2),
    (1.2, "em", 20.0, "p", 24.0),
    ("x-small", "absolute_keyword", 20.0, "li", 10.0),
    ("larger", "relative_keyword", 13.0, "li", 15.6),
    ("smaller", "relative_keyword", 13.0, "li", 10.8),
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
    expected = 6
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
    results = fonts.is_large_text(18.7, True)
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


def test_property_is_font_shorthand_for_true():
    results = fonts.property_is_font_shorthand("font")
    expected = True
    assert results == expected


def test_property_is_font_shorthand_for_false():
    results = fonts.property_is_font_shorthand("font-family")
    expected = False
    assert results == expected


def test_is_valid_shorthand_for_true():
    results = fonts.is_valid_shorthand("italic 20px Serif")
    expected = True
    assert results == expected


def test_is_valid_shorthand_for_false():
    results = fonts.is_valid_shorthand("bold small-caps")
    expected = False
    assert results == expected


path = "tests/test_files/single_file_project"
large_project_path = "tests/test_files/large_project"


# Test Google font report
def test_get_google_font_report_for_single_page_no_fonts():
    report = fonts.get_google_font_report(path)
    assert "fail" in report[0]


def test_get_google_font_report_for_large_project_mixed_results():
    report = fonts.get_google_font_report(large_project_path, 2)
    num_fails = 0
    expected_fails = 1
    num_passed = 0
    expected_passed = 2
    for datum in report:
        if "pass:" in datum[:6]:
            num_passed += 1
        else:
            num_fails += 1
    meets_passed = num_passed == expected_passed
    meets_failed = num_fails == expected_fails
    assert len(report) == 3 and meets_passed and meets_failed


def test_get_google_font_report_for_too_many_fonts():
    directory = "tests/test_files/attribute_selector_file"
    report = fonts.get_google_font_report(directory)
    result = report[0]
    assert "fail" in result and "too many" in result


def test_get_google_font_data_for_two_in_single_page():
    url = "https://fonts.googleapis.com/css2?family=Elms+Sans:ital,wght@0,"
    url += "100..900;1,100..900&family=Tirra:wght@400;500;600;700;800;900&"
    url += "display=swap"
    results = fonts.get_google_font_data(url)
    assert len(results) == 2 and "Tirra" in results


def test_get_google_font_data_for_three_and_diff_char():
    url = "https://fonts.googleapis.com/css2?family=Open+Sans:ital,wght@0,300."
    url += ".800;1,300..800&family=Righteous&family=Source+Sans+3:ital,wght@0,"
    url += "200..900;1,200..900&display=swap"
    results = fonts.get_google_font_data(url)
    has_three_fonts = len(results) == 3
    has_no_ampersand = True
    for result in results:
        if "&" in result:
            has_no_ampersand = False
    assert has_three_fonts and has_no_ampersand


def test_extract_families_for_one_family():
    font_data = [{"selector": "body", "family": "'Open Sans', sans-serif"}]
    expected = ["Open Sans"]
    results = fonts.extract_families(font_data)
    assert results == expected


@pytest.fixture
def two_families():
    font_data = [
        {"selector": "body", "family": "'Open Sans', sans-serif"},
        {
            "selector": "article h1.important, h2, h3, h4, h5, h6",
            "family": "'Righteous', sans-serif",
        },
    ]
    families = fonts.extract_families(font_data)
    return families


def test_extract_families_for_two_families_in_all(two_families):
    has_both = len(two_families) == 2
    assert has_both


def test_extract_families_for_correct_families(two_families):
    has_both = "Open Sans" in two_families
    has_both = has_both and "Righteous" in two_families
    assert has_both


def test_get_google_font_data_for_two_plus_word_fonts():
    href = "https://fonts.googleapis.com/css2?family=Bitcount+Prop+Single:"
    href += "wght@100..900&family=Open+Sans:ital,wght@0,300..800;1,300..800&"
    href += "display=swap"
    font_data = fonts.get_google_font_data(href)
    has_both = len(font_data) == 2
    has_both = (
        has_both
        and "Open Sans" in font_data
        and "Bitcount Prop Single" in font_data
    )
    assert has_both


def test_get_google_font_data_for_one_word_font_with_symbols():
    href = "https://fonts.googleapis.com/css2?family=Source+Sans+3:ital,wght@"
    href += "0,200..900;1,200..900&display=swap"
    expected = ["Source Sans 3"]
    results = fonts.get_google_font_data(href)
    assert results == expected


if __name__ == "__main__":
    report = fonts.get_google_font_report(large_project_path, 2)
    print(report)
