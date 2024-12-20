import pytest

from webcode_tk import validator_tools as val

html_files = val.get_html_file_names()
browser = val.browser
valid_css_code = "p { font-size: 3em; }"
invalid_css_code = """ body {
   font-family: Arial, Helvetica, sans-serif;
   font-size: 100pct;
 }
 #graphic, h1 {
   text-align: center;
 }
 p {
   align: left;
 }"""
html_file_with_errors = "tests/test_files/sample_with_errors.html"
html_file_with_no_errors = "tests/test_files/sample_no_errors.html"
project_folder = "tests/test_files/project"


@pytest.fixture
def invalid_markup():
    invalid_markup = val.get_markup_validity(html_file_with_errors)
    return invalid_markup


@pytest.fixture
def invalid_css_results():
    results = val.validate_css(invalid_css_code)
    yield results


@pytest.fixture
def css_errors_list(invalid_css_results):
    errors = val.get_css_errors_list(invalid_css_results)
    return errors


@pytest.fixture
def valid_css_results():
    results = val.validate_css(valid_css_code)
    yield results


def test_get_num_markup_errors(invalid_markup):
    expected = 4
    results = val.get_num_markup_errors(invalid_markup)
    assert results == expected


def test_get_num_markup_warnings(invalid_markup):
    expected = 2
    results = val.get_num_markup_warnings(invalid_markup)
    assert results == expected


def test_get_markup_validity_for_no_errors():
    results = val.get_markup_validity(html_file_with_no_errors)
    assert not results


def test_get_markup_validity_for_6_items():
    results = len(val.get_markup_validity(html_file_with_errors))
    expected = 6
    assert results == expected


def test_get_html_file_names_for_test_files_project_folder():
    files = val.get_html_file_names("tests/test_files/project")
    results = len(files)
    assert results == 5


def test_get_num_html_files_for_project_folder():
    results = val.get_num_html_files(project_folder)
    expected = 5
    assert results == expected


# Test CSS validation
def test_is_css_valid_for_no_errors(valid_css_results):
    expected = True
    results = val.is_css_valid(valid_css_results)
    assert expected == results


def test_is_css_valid_for_errors(invalid_css_results):
    expected = False
    results = val.is_css_valid(invalid_css_results)
    assert expected == results


def test_get_num_errors_two(css_errors_list):
    expected = 2
    results = val.get_num_errors(css_errors_list)
    assert results == expected


def test_get_css_errors_with_valid_css(valid_css_results):
    expected = []
    results = val.get_css_errors_list(valid_css_results)
    assert results == expected


def test_clean_error_msg():
    expected = "Value Error: display phred is not a display value: phred"
    msg = (
        "\n                                Value Error :  display"
        "                                             phred is not"
        " a display "
        "value : \n                                            \n"
        "                                    phred\n"
        "                                \n"
    )
    results = val.clean_error_msg(msg)
    assert results == expected


def test_validate_css_with_no_errors(valid_css_results):
    results = val.validate_css(valid_css_code)
    assert results == valid_css_results


def test_validate_css_with_errors(invalid_css_results):
    results = val.validate_css(invalid_css_code)
    assert results == invalid_css_results


def test_get_project_validation_for_project_html_fails():
    results = val.get_project_validation(project_folder, "html")
    fails = 0
    for result in results:
        if "fail" in result[:4]:
            fails += 1
    expected_fails = 5
    assert len(results) == expected_fails


def test_get_project_validation_for_project_css_fail():
    results = val.get_project_validation(project_folder, "css")
    fails = 0
    for result in results:
        if "fail" in result[:4]:
            fails += 1
    expected_fails = 1
    assert len(results) == expected_fails
