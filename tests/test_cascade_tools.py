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
gradients_path = "tests/test_files/gradients.html"


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


def test_font_size_for_inline_child_of_h1(font_sizes_body):
    code = font_sizes_body[0].children[0].children[0]
    expected = 40.0
    results = code.font_size
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


def test_is_selector_pseudoclass_for_only_pseudoclass():
    selector = ":focus"
    expected = True
    results = cascade.is_selector_pseudoclass(selector)
    assert expected == results


def test_is_selector_pseudoclass_for_element_plus_pseudoclasss():
    selector = "p:first-of_type"
    expected = True
    results = cascade.is_selector_pseudoclass(selector)
    assert expected == results


def test_is_selector_pseudoclass_for_only_pseudoelement():
    selector = "::before"
    expected = False
    results = cascade.is_selector_pseudoclass(selector)
    assert expected == results


def test_is_selector_pseudoclass_for_element_plus_pseudo_element():
    selector = "p::first-letter"
    expected = False
    results = cascade.is_selector_pseudoclass(selector)
    assert expected == results


##########################
# Test gradients on a page
##########################


@pytest.fixture
def gradients_file_large_tree():
    css_tree = None
    sheets = css.get_all_stylesheets_by_file(gradients_path)
    css_tree = cascade.CSSAppliedTree(gradients_path, sheets)
    return css_tree


@pytest.fixture
def gradients_file_normal_tree():
    gradient_path = "tests/test_files/gradients-large.html"
    sheets = css.get_all_stylesheets_by_file(gradient_path)
    css_tree = cascade.CSSAppliedTree(gradient_path, sheets)
    return css_tree


def test_gradients_file_tree_for_tree(gradients_file_large_tree):
    assert gradients_file_large_tree


def test_get_color_contrast_details_for_AAA_large(gradients_file_large_tree):
    results = cascade.get_color_contrast_details(gradients_file_large_tree)
    expected = 3  # fail normal (radial) fail all (horizontal), footer (fails)
    assert len(results) == expected


def test_get_color_contrast_details_for_AAA_fail_single_file_style_tag():
    path = "tests/test_files/color_contrast_test/"
    styles = css.get_all_styles_in_order(path)
    file = styles[0].get("file")
    sheets = styles[0].get("stylesheets")
    tree = cascade.CSSAppliedTree(file, sheets)
    results = cascade.get_color_contrast_details(tree)
    expected = "h1, h2 triggered 4" in results[0]
    assert expected


def test_get_color_contrast_details_for_AA_large(gradients_file_large_tree):
    results = cascade.get_color_contrast_details(
        gradients_file_large_tree, "AA"
    )
    # Should fail: horizontal and simple linear - 2 errors each
    expected = (
        len(results) == 2
        and "triggered 2" in results[0]
        and "triggered 2" in results[1]
    )
    assert expected


def test_get_color_contrast_for_AAA_normal(gradients_file_normal_tree):
    results = cascade.get_color_contrast_details(gradients_file_normal_tree)
    expected = 4
    assert len(results) == expected


def test_get_color_contrast_for_AA_normal(gradients_file_normal_tree):
    results = cascade.get_color_contrast_details(
        gradients_file_normal_tree, "AA"
    )
    # Should fail: radial, footer
    expected = 3
    assert len(results) == expected


@pytest.fixture
def font_sizes_tree():
    path = "tests/test_files/font-sizes.html"
    sheets = css.get_all_stylesheets_by_file(path)
    css_tree = cascade.CSSAppliedTree(path, sheets)
    return css_tree


def test_get_color_contrast_for_AAA_success(font_sizes_tree):
    expected = "pass: font-sizes.html passes color contrast for AAA Normal"
    expected += " and Large."
    results = cascade.get_color_contrast_details(font_sizes_tree)
    assert results[0] == expected


def test_get_color_contrast_for_AA_success(font_sizes_tree):
    expected = "pass: font-sizes.html passes color contrast for AA Normal "
    expected += "and Large."
    results = cascade.get_color_contrast_details(font_sizes_tree, "AA")
    assert results[0] == expected


@pytest.fixture
def radial_gradient_children(gradients_file_large_tree):
    body = gradients_file_large_tree.children[0]
    main = body.children[0]
    return main.children


@pytest.fixture
def radial_gradient_section(radial_gradient_children):
    radial_section = radial_gradient_children[1]
    return radial_section


def test_radial_gradient_section_for_contrast_ratio_failure(
    radial_gradient_section,
):
    # contrast should fail at 4.08
    expected_results = 4.08
    actual_contrast_data = radial_gradient_section.contrast_data
    actual_results = actual_contrast_data.get("ratio")
    assert expected_results == actual_results


def test_radial_gradient_section_for_contrast_results(radial_gradient_section):
    # contrast should fail
    expected_results = False
    actual_contrast_data = radial_gradient_section.contrast_data
    actual_results = actual_contrast_data.get("normal_aa")
    assert expected_results == actual_results


@pytest.fixture
def horizontal_gradient_section(radial_gradient_children):
    horizontal_section = radial_gradient_children[2]
    return horizontal_section


def test_horizontal_gradient_for_expected_child_ratio(
    horizontal_gradient_section,
):
    child = horizontal_gradient_section.children[0]
    actual_ratio = child.contrast_data.get("ratio")
    expected_ratio = 2.44
    assert actual_ratio == expected_ratio


@pytest.fixture
def other_gradient_section(radial_gradient_children):
    other_section = radial_gradient_children[3]
    return other_section


def test_other_gradient_section_for_pass_results(other_gradient_section):
    expected_result = True
    actual_results = other_gradient_section.contrast_data.get("normal_aaa")
    assert expected_result == actual_results


@pytest.fixture
def footer_gradient(radial_gradient_children):
    footer = radial_gradient_children[4]
    return footer


# Tests on nested color report

debugging_project_dir = "tests/test_files/debugging_project"
debugging_styles_report = cascade.get_color_contrast_report(
    debugging_project_dir
)


def test_color_contrast_on_nested_links():
    expected = True
    fails = 0
    for item in debugging_styles_report:
        if "fail" in item:
            fails += 1
    expected = fails == 1
    assert expected


# Test Amharic Script Page for color contrast

cascade_complexities_dir = "tests/test_files/cascade_complexities"
cascade_complexities_report = cascade.get_color_contrast_report(
    cascade_complexities_dir
)


@pytest.fixture
def cascade_complexities():
    cascade_styles = css.get_styles_by_html_files(cascade_complexities_dir)
    return cascade_styles


@pytest.fixture
def amharic_tree(cascade_complexities):
    css_tree = None
    for page in cascade_complexities:
        if "amharic.html" in page.get("file"):
            filepath = page.get("file")
            sheets = page.get("stylesheets")
    css_tree = cascade.CSSAppliedTree(filepath, sheets)
    return css_tree


@pytest.fixture
def gallery_tree(cascade_complexities):
    css_tree = None
    for page in cascade_complexities:
        if "index.html" in page.get("file"):
            filepath = page.get("file")
            sheets = page.get("stylesheets")
    css_tree = cascade.CSSAppliedTree(filepath, sheets)
    return css_tree


def test_nested_color_combos_for_proper_contrast_report():
    passing = []
    failing = []
    for item in cascade_complexities_report:
        if "pass" in item:
            passing.append(item)
    assert passing and not failing


def test_gallery_for_applied_colors_to_figcaption(gallery_tree):
    figcaption = gallery_tree.children[0].children[1].children[0].children[1]
    color = figcaption.color.get("value")
    bg_color = figcaption.background_color.get("value")
    contrast_ratio = figcaption.contrast_data.get("ratio")
    expected = (
        color == "black"
        and bg_color == "whitesmoke"
        and contrast_ratio == 19.26
    )
    assert expected


def test_amharic_file_for_proper_application_of_nav_link(amharic_tree):
    nav = amharic_tree.children[0].children[0].children[1]
    link = nav.children[0].children[0].children[0]
    color = link.color.get("value")
    bg_color = link.background_color.get("value")
    contrast_ratio = link.contrast_data.get("ratio")
    expected = (
        contrast_ratio == 12.6 and color == "#ffffff" and bg_color == "#003366"
    )
    assert expected
