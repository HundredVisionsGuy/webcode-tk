import sys

import pytest
from bs4 import BeautifulSoup
from bs4 import Tag
from file_clerk import clerk

from webcode_tk import html_tools

file_with_inline_styles = "tests/test_files/sample_with_inline_styles.html"
no_inline_styles = "tests/test_files/sample_no_inline_styles.html"
project_path = "tests/test_files/project"
sports_path = "tests/test_files/project/sports.html"
windows_path = "tests\\test_files\\project\\sports.html"
div_markup = '<div id="listdiv"><ul><li>this and</li><li>that</li></ul></div>'


@pytest.fixture
def markup_with_inline_styles():
    markup = clerk.file_to_string(file_with_inline_styles)
    return markup


@pytest.fixture
def html_soup():
    soup = html_tools.get_html(file_with_inline_styles)
    yield soup


@pytest.fixture
def sports_h1():
    tag = html_tools.get_elements("h1", sports_path)
    return tag[0]


@pytest.fixture
def div_list_tag():
    tag = html_tools.get_elements("div", no_inline_styles)
    return tag[0]


def test_html_report_for_file_that_uses_inline_styles(
    markup_with_inline_styles,
):
    assert html_tools.uses_inline_styles(markup_with_inline_styles)


def test_get_all_html_files_for_existence_of_file():
    project_files = html_tools.get_all_html_files(project_path)
    expected_path = project_path + "/background.html"
    assert expected_path in project_files


def test_get_all_html_files_for_all_5_files():
    # NOTE: I hid an inner_folder to make sure it worked for all
    # sub folders.
    results = html_tools.get_all_html_files(project_path)
    assert len(results) == 5


def test_get_html_for_return_type(html_soup):
    assert isinstance(html_soup, BeautifulSoup)


def test_get_html_for_file_not_found():
    with pytest.raises(FileNotFoundError):
        html_tools.get_html("file/to/non-existent.html")


def test_get_html_for_soup_contents(html_soup):
    assert "html" in html_soup.contents[0]


def test_get_num_elements_in_file():
    num_lis = html_tools.get_num_elements_in_file("p", file_with_inline_styles)
    assert num_lis == 2


def test_get_num_elements_in_file_for_FNF_exception():
    with pytest.raises(FileNotFoundError):
        html_tools.get_num_elements_in_file("p", "non/existent/file.html")


def test_get_num_elements_in_nonexistent_folder():
    with pytest.raises(FileNotFoundError):
        html_tools.get_num_elements_in_folder("p", "folder/path")


def test_get_num_elements_in_test_project_folder():
    num_paragraphs = html_tools.get_num_elements_in_folder("p", project_path)
    assert num_paragraphs == 6


def test_get_elements_for_file_not_found_exception():
    with pytest.raises(FileNotFoundError):
        html_tools.get_elements("p", "non/existent/file.html")


def test_get_elements_for_expected_number():
    results = html_tools.get_elements("ul", sports_path)
    assert len(results) == 2


def test_get_elements_for_Tag_object_in_list():
    results = html_tools.get_elements("ul", sports_path)
    assert isinstance(results[0], Tag)


def test_get_elements_for_expected_tag_type():
    results = html_tools.get_elements("ul", sports_path)
    assert results[0].name == "ul"


@pytest.mark.skipif(
    not sys.platform.startswith("win"), reason="WindowsOS only test"
)
def test_for_non_posix_path_for_WindowsOS():
    results = html_tools.get_elements("ul", windows_path)
    assert results


def test_get_element_content_for_sports_h1(sports_h1):
    results = html_tools.get_element_content(sports_h1)
    assert results == "Sports"


def test_uses_inline_styles_for_uses_inline():
    results = html_tools.uses_inline_styles(
        '<p style="font-size: normal">Hello</p>'
    )
    assert results


def test_uses_inline_styles_for_no_inline_styles():
    results = html_tools.uses_inline_styles(div_markup)
    assert not results


def test_get_element_content_for_nested_el_as_string():
    results = html_tools.get_element_content(div_markup)
    expected = "<ul><li>this and</li><li>that</li></ul>"
    assert results == expected


def test_get_element_content_for_el_as_tag(div_list_tag):
    results = html_tools.get_element_content(div_list_tag)
    expected = "<ul><li>this and</li><li>that</li></ul>"
    assert results == expected


def test_get_element_content_for_single_el_as_string():
    tag_string = "<h1>Hello, this is my title</h1>"
    expected = "Hello, this is my title"
    results = html_tools.get_element_content(tag_string)
    assert results == expected


def test_string_to_tag_for_div_markup():
    results = html_tools.string_to_tag(div_markup)
    assert isinstance(results, Tag)


def test_string_to_tag_for_value_error():
    non_html_string = "Malformed html</h1>"
    with pytest.raises(ValueError):
        html_tools.string_to_tag(non_html_string)


def test_string_to_tag_with_preceeding_space_no_error():
    html_string_with_opening_space = " <h1>Well formed html</h1>"
    results = html_tools.string_to_tag(html_string_with_opening_space)
    expected = "<h1>Well formed html</h1>"
    assert str(results) == expected
