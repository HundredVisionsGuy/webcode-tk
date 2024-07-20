import pytest

from webcode_tk import cascade_tools as cascade
from webcode_tk import css_tools as css

project_path = "tests/test_files/single_file_project/"
large_project = "tests/test_files/large_project/"
attribute_selector_path = "tests/test_files/attribute_selector_file/"
attribute_selector_styles = css.get_styles_by_html_files(
    attribute_selector_path
)
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
def attribute_selectors_tree():
    css_tree = None
    file = attribute_selector_styles[0]
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
            break
    return css_tree


@pytest.fixture
def single_file_link(single_file_tree):
    p = single_file_tree.children[0].children[1]
    a = p.children[0]
    return a


@pytest.fixture
def single_file_table(single_file_tree):
    table = single_file_tree.children[0].children[2]
    return table


@pytest.fixture
def single_file_td(single_file_table):
    tr = single_file_table.children[3]
    td = tr.children[1]
    return td


@pytest.fixture
def gallery_h1(gallery_file_tree):
    header = gallery_file_tree.children[0].children[0].children[0]
    h1 = header.children[0]
    return h1


@pytest.fixture
def gallery_body(gallery_file_tree):
    body = gallery_file_tree.children[0]
    return body


@pytest.fixture
def gallery_article(gallery_file_tree):
    article = gallery_file_tree.children[0].children[0].children[1]
    return article


@pytest.fixture
def attribute_selectors_article(attribute_selectors_tree):
    article = attribute_selectors_tree.children[0].children[0].children[1]
    return article


@pytest.fixture
def attribute_selectors_header(attribute_selectors_tree):
    div = attribute_selectors_tree.children[0].children[0]
    header = div.children[0]
    return header


@pytest.fixture
def font_sizes_body():
    path = "tests/test_files/font-sizes.html"
    styles = css.get_all_stylesheets_by_file(path)
    tree = cascade.CSSAppliedTree(path, styles)
    return tree.children[0].children


def test_css_tree_for_tree(single_file_tree):
    assert single_file_tree


def test_gallery_file_for_tree(gallery_file_tree):
    assert gallery_file_tree.filename == "gallery.html"


def test_single_link_for_color(single_file_link):
    color = single_file_link.color.get("value")
    bg_color = single_file_link.background_color.get("value")
    assert color == "rgb(228, 234, 220)" and bg_color == "darkblue"


def test_element_for_non_link():
    h1_tag = cascade.Element("h1")
    assert h1_tag


def test_element_for_link_styles():
    link = cascade.Element("a")
    results = link.color.get("value")
    assert results == cascade.default_link_color


def test_single_link_for_contrast_ratio(single_file_link):
    expected = 12.45
    results = single_file_link.contrast_data.get("ratio")
    assert results == expected


def test_single_link_for_specificity(single_file_link):
    expected = "001"
    results = single_file_link.color.get("specificity")
    assert expected == results


def test_td_for_color(single_file_td):
    expected = "aliceblue"
    results = single_file_td.color.get("value")
    assert expected == results


def test_td_for_bg_color(single_file_td):
    expected = "rgb(218, 236, 236)"
    results = single_file_td.background_color.get("value")
    assert expected == results


def test_table_for_bg_color(single_file_table):
    expected = "rgb(218, 236, 236)"
    results = single_file_table.background_color.get("value")
    assert expected == results


def test_gallery_h1_for_specificity(gallery_h1):
    expected = "002"
    results = gallery_h1.background_color.get("specificity")
    assert expected == results


def test_gallery_h1_for_colors(gallery_h1):
    color = gallery_h1.color.get("value")
    background = gallery_h1.background_color.get("value")
    assert background == "rgb(114, 101, 87)" and color == "#e7e4e1"


def test_gallery_body_for_101_specificity(gallery_body):
    expected = "101"
    results = gallery_body.background_color.get("specificity")
    assert results == expected


def test_gallery_body_for_background_color(gallery_body):
    expected = "azure"
    results = gallery_body.background_color.get("value")
    assert results == expected


def test_gallery_article_for_background_color(gallery_article):
    expected = "azure"
    results = gallery_article.background_color.get("value")
    assert results == expected


def test_attribute_selectors_for_title_attribute(attribute_selectors_article):
    expected = "purple"
    link = attribute_selectors_article.children[1].children[0]
    results = link.color.get("value")
    assert results == expected


def test_attribute_selectors_for_exact_attribute_values(
    attribute_selectors_article,
):
    expected = "cadetblue"
    link = attribute_selectors_article.children[2].children[0]
    results = link.color.get("value")
    assert results == expected


def test_attribute_selectors_for_contains_word(attribute_selectors_article):
    expected = "mediumvioletred"
    link = attribute_selectors_article.children[3].children[0]
    results = link.color.get("value")
    assert results == expected


def test_attribute_selectors_for_ends_with_case_insensitive(
    attribute_selectors_header,
):
    expected = "rgb(40, 34, 75)"
    link = attribute_selectors_header.children[2].children[0]
    results = link.color.get("value")
    assert results == expected


def test_attribute_selectors_for_ends_with_case_sensitive(
    attribute_selectors_header,
):
    expected = "#336699"
    link = attribute_selectors_header.children[0].children[0]
    results = link.color.get("value")
    assert results == expected


def test_font_size_for_h1(font_sizes_body):
    h1 = font_sizes_body[0].children[0]
    expected = 40.0
    results = h1.font_size
    assert results == expected


def test_font_size_for_p_with_descendant_selector(font_sizes_body):
    p = font_sizes_body[1].children[4]
    expected = 20.0
    results = p.font_size
    assert results == expected


def test_font_size_for_p_with_20px_root_size_on_body(font_sizes_body):
    p = font_sizes_body[0].children[1]
    expected = 23.0
    results = p.font_size
    assert results == expected


def test_font_size_for_x_small_li(font_sizes_body):
    li = font_sizes_body[1].children[5].children[1]
    results = li.font_size
    expected = 10.0
    assert results == expected


def test_font_size_for_xxx_large_li(font_sizes_body):
    li = font_sizes_body[1].children[5].children[7]
    results = li.font_size
    expected = 48.0
    assert results == expected


def test_font_size_for_smaller_large(font_sizes_body):
    ul = font_sizes_body[1].children[10]
    li = ul.children[2].children[0].children[0]
    results = li.font_size
    expected = 15
    assert results == expected


def test_font_size_for_larger_large(font_sizes_body):
    ul = font_sizes_body[1].children[10]
    li = ul.children[2].children[0].children[1]
    results = li.font_size
    expected = 21.6
    assert results == expected


def test_font_size_for_1pt2_em_p(font_sizes_body):
    p = font_sizes_body[2].children[2]
    results = p.font_size
    expected = 24
    assert results == expected


def test_font_size_for_1pt2_rem_p(font_sizes_body):
    p = font_sizes_body[2].children[1]
    results = p.font_size
    expected = 19.2
    assert results == expected


def test_span_within_span_within_span_each_at_120percent(font_sizes_body):
    outer_span = font_sizes_body[1].children[12].children[0]
    innermost_span = outer_span.children[0].children[0]
    results = innermost_span.font_size
    expected = 26.6
    assert results == expected


def test_medium_span_within_span_within_span_each_120percent(font_sizes_body):
    outer_span = font_sizes_body[1].children[12].children[0]
    medium_span = outer_span.children[0].children[0].children[0]
    results = medium_span.font_size
    expected = 16
    assert results == expected


# Test for bold or not
def test_is_bold_for_bold_p_in_header(font_sizes_body):
    p = font_sizes_body[0].children[1]
    results = p.is_bold
    expected = True
    assert results == expected


def test_is_bold_for_normal_p_not(font_sizes_body):
    p = font_sizes_body[1].children[4]
    results = p.is_bold
    expected = False
    assert results == expected


def test_is_bold_for_h3(font_sizes_body):
    h3 = font_sizes_body[1].children[3]
    results = h3.is_bold
    expected = True
    assert results == expected


def test_is_bold_for_h4(font_sizes_body):
    h4 = font_sizes_body[3].children[7]
    results = h4.is_bold
    expected = True
    assert results == expected


# Tests for if large or not
def test_is_large_for_bold_p_in_header(font_sizes_body):
    p = font_sizes_body[0].children[1]
    results = p.is_large
    expected = True
    assert results == expected


def test_is_large_for_normal_p_20_px(font_sizes_body):
    p = font_sizes_body[1].children[4]
    results = p.is_large
    expected = False
    assert results == expected


def test_is_large_for_h3_bold(font_sizes_body):
    h3 = font_sizes_body[1].children[3]
    results = h3.is_large
    expected = True
    assert results == expected


def test_is_large_for_h4_bold_not_bold_16px(font_sizes_body):
    h4 = font_sizes_body[3].children[7]
    results = h4.is_large
    expected = False
    assert results == expected


if __name__ == "__main__":
    path = "tests/test_files/font-sizes.html"
    styles = css.get_all_stylesheets_by_file(path)
    tree = cascade.CSSAppliedTree(path, styles)
    children = tree.children[0].children
    test_font_size_for_h1(children)
    test_font_size_for_p_with_20px_root_size_on_body(children)
    test_font_size_for_x_small_li(children)
    test_font_size_for_xxx_large_li(children)
    test_font_size_for_smaller_large(children)
    test_font_size_for_1pt2_em_p(children)
    test_span_within_span_within_span_each_at_120percent(children)
    test_font_size_for_larger_large(children)
