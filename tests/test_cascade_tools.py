import pytest

from webcode_tk import cascade_tools as cascade
from webcode_tk import css_tools as css

project_path = "tests/test_files/single_file_project/"
large_project = "tests/test_files/large_project/"
styles_by_html_files = css.get_styles_by_html_files(project_path)
large_project_styles = css.get_styles_by_html_files(large_project)


@pytest.fixture
def single_file_tree():
    css_tree = None
    file = styles_by_html_files[0]
    filepath = file.get("file")
    sheets = file.get("stylesheets")
    css_tree = cascade.CSSAppliedTree(filepath, sheets)
    return css_tree


@pytest.fixture
def gallery_file_tree():
    css_tree = None
    all_files = large_project_styles
    for file in all_files:
        if "gallery.html" in file.get("file"):
            filepath = file.get("file")
            sheets = file.get("stylesheets")
            css_tree = cascade.CSSAppliedTree(filepath, sheets)
    return css_tree


@pytest.fixture
def single_file_link(single_file_tree):
    p = single_file_tree.children[0].children[1]
    a = p.children[0]
    return a


@pytest.fixture
def single_file_td(single_file_tree):
    tr = single_file_tree.children[0].children[2].children[3]
    td = tr.children[1]
    return td


@pytest.fixture
def gallery_file_h1(gallery_file_tree):
    header = gallery_file_tree.children[0].children[0].children[0]
    h1 = header.children[0]
    return h1


def test_css_tree_for_tree(single_file_tree):
    assert single_file_tree


def test_gallery_file_for_tree(gallery_file_tree):
    assert gallery_file_tree.filename == "gallery.html"


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


def test_single_link_for_contrast_ratio(single_file_link):
    expected = 12.45
    results = single_file_link.styles.get("contrast_ratio")
    assert results == expected


def test_single_link_for_specificity(single_file_link):
    expected = "001"
    results = single_file_link.styles.get("specificity")
    assert expected == results


def test_td_for_color(single_file_td):
    expected = "aliceblue"
    results = single_file_td.styles.get("color")
    assert expected == results


def test_td_for_bg_color(single_file_td):
    expected = "rgb(218, 236, 236)"
    results = single_file_td.styles.get("background-color")
    assert expected == results


def test_gallery_file_h1_for_specificity(gallery_file_h1):
    expected = "002"
    results = gallery_file_h1.styles.get("specificity")
    assert expected == results


def test_gallery_file_h1_for_colors(gallery_file_h1):
    color = gallery_file_h1.styles.get("color")
    background = gallery_file_h1.styles.get("background-color")
    assert background == "rgb(114, 101, 87)" and color == "#e7e4e1"
