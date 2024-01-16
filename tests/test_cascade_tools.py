import pytest

from webcode_tk import cascade_tools as cascade
from webcode_tk import css_tools as css

project_path = "tests/test_files/single_file_project/"
styles_by_html_files = css.get_styles_by_html_files(project_path)


@pytest.fixture
def single_file_tree():
    css_tree = None
    file = styles_by_html_files[0]
    filepath = file.get("file")
    sheets = file.get("stylesheets")
    css_tree = cascade.CSSAppliedTree(filepath, sheets)
    return css_tree


@pytest.fixture
def single_file_link(single_file_tree):
    p = single_file_tree.children[0].children[1]
    a = p.children[0]
    return a


def test_css_tree_for_tree(single_file_tree):
    assert single_file_tree


def test_single_link_for_color(single_file_link):
    color = single_file_link.styles.get("color")
    bg_color = single_file_link.styles.get("background-color")
    assert color == "rgb(228, 234, 220)" and bg_color == "darkblue"


def test_element_for_non_link():
    h1_tag = cascade.Element("h1")
    assert h1_tag


def test_element_for_link_styles():
    link = cascade.Element("a")
    assert link.styles.get("color") == cascade.default_link_color
