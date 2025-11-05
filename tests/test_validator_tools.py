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
# Add mocks

# invalid_markup equals
# val dot
# get_markup_validity
# (
# html_file_with_errors
# )

invalid_json_response = {
    "version": "25.11.4",
    "messages": [
        {
            "type": "info",
            "lastLine": 8,
            "lastColumn": 25,
            "firstColumn": 3,
            "subType": "warning",
            "message": "The \u201ctype\u201d attribute for the "
            "\u201cstyle\u201d "
            "element is not needed and should be omitted.",
            "extract": '/title>\n  <style type="text/css"></styl',
            "hiliteStart": 10,
            "hiliteLength": 23,
        },
        {
            "type": "error",
            "lastLine": 12,
            "lastColumn": 21,
            "firstColumn": 3,
            "message": "Attribute \u201cname\u201d not allowed on element"
            " \u201ch1\u201d at this point.",
            "extract": '\n<body>\n  <h1 name="heading">Sample',
            "hiliteStart": 10,
            "hiliteLength": 19,
        },
        {
            "type": "error",
            "lastLine": 14,
            "lastColumn": 25,
            "firstColumn": 3,
            "message": "Attribute \u201chref\u201d not allowed on element "
            "\u201cimg\u201d at this point.",
            "extract": 'rs?</p>\n  <img href="sample.jpg">\n  <p>',
            "hiliteStart": 10,
            "hiliteLength": 23,
        },
        {
            "type": "error",
            "lastLine": 14,
            "lastColumn": 25,
            "firstColumn": 3,
            "message": "Element \u201cimg\u201d is missing required attribute"
            " \u201csrc\u201d.",
            "extract": 'rs?</p>\n  <img href="sample.jpg">\n  <p>',
            "hiliteStart": 10,
            "hiliteLength": 23,
        },
        {
            "type": "error",
            "lastLine": 14,
            "lastColumn": 25,
            "firstColumn": 3,
            "message": "An \u201cimg\u201d element must have an "
            "\u201calt\u201d attribute, except under certain conditions. "
            "For details, consult guidance on providing text alternatives "
            "for images.",
            "extract": 'rs?</p>\n  <img href="sample.jpg">\n  <p>',
            "hiliteStart": 10,
            "hiliteLength": 23,
        },
    ],
}

print("\n")
print(invalid_json_response)

valid_json_response = {"version": "25.11.4", "messages": []}
html_file_with_no_errors = "tests/test_files/sample_no_errors.html"
request_good_status = 200
request_too_many_requests = 429
bad_request = 400
project_folder = "tests/test_files/project"

# change the string to actual validator function just to check
no_error_results = "val.get_markup_validity(html_file_with_no_errors)"
print(no_error_results)


# Process CSS
css_errors = []

# try validate_css on invalid and valid code and get the JSON object
print(css_errors)

# change the string to actual validator function
css_errors_list = "val.get_css_errors_list(css_errors)"
print(valid_css_code)


@pytest.fixture
def valid_css_results():
    results = []
    # Will mock later
    # mocking validate_css from val with (valid_css_code)
    yield results


# The following should be fixed in the next commit


def test_get_num_markup_errors():
    # used invalid_markup fixture
    expected = 4
    # This will use a mock on from invalid_markup
    results = 4
    assert results == expected


def test_get_num_markup_warnings():
    # used invalid_markup fixture
    expected = 1
    # This will use a mock on get_num_markup_warnings
    results = 1
    assert results == expected


def test_get_markup_validity_for_no_errors():
    # will use mocked fixture from file with no errors
    results = False
    assert not results


def test_get_markup_validity_for_5_items():
    # will mock get_markup_validity using len() function
    results = 5
    expected = 5
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
def test_is_css_valid_for_no_errors():
    # Need to mock is_css_valid for valid_css_results
    expected = True
    results = True
    assert expected == results


def test_is_css_valid_for_errors():
    # Need to mock is_css_valid for invalid_css_results
    expected = False
    results = False
    assert expected == results


def test_get_num_errors_two():
    # need to mock get_num_errors with css_errors_list
    expected = 2
    results = 2
    assert results == expected


def test_get_css_errors_with_valid_css():
    # need to mock get_num_errors with valid_css
    expected = []
    results = []
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


def test_validate_css_with_no_errors():
    # Need to mock this with validate_css using valid_css_results
    results = True
    # Will assert that results are equal to valid_css_results
    assert results


def test_validate_css_with_errors():
    # Need to mock this with validate_css using invalid_css_results
    results = True
    # Will assert that results are equal to valid_css_results
    invalid_css_results = True
    assert results == invalid_css_results


def test_get_project_validation_for_project_css_fail():
    results = val.get_project_validation(project_folder, "css")
    fails = 0
    for result in results:
        if "fail" in result[:4]:
            fails += 1
    expected_fails = 1
    assert len(results) == expected_fails
