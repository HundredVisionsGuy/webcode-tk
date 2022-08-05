import pytest
from bs4 import BeautifulSoup
from file_clerk import clerk

from webcode_tk import html

file_with_inline_styles = "tests/test_files/sample_with_inline_styles.html"
project_path = "tests/test_files/project"


@pytest.fixture
def markup_with_inline_styles():
    markup = clerk.file_to_string(file_with_inline_styles)
    return markup


@pytest.fixture
def html_soup():
    soup = html.get_html(file_with_inline_styles)
    yield soup


def test_html_report_for_file_that_uses_inline_styles(
    markup_with_inline_styles,
):
    assert html.uses_inline_styles(markup_with_inline_styles)


def test_get_html_for_return_type(html_soup):
    assert isinstance(html_soup, BeautifulSoup)


def test_get_html_for_(html_soup):
    assert "html" in html_soup.contents[0]


def test_get_num_elements_in_file():
    num_lis = html.get_num_elements_in_file("p", file_with_inline_styles)
    assert num_lis == 2
