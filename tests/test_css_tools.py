import pytest
from file_clerk import clerk

from webcode_tk import css_tools

css_code_1_with_comments = """
/* comment #1 */
body {
    font-size: 1.1em;
    color: white;
    background-color: black;
}
/* comment #2 */
h1, h2, h3 {
    font-family: sans-serif;
}
p {
    font-size: 1.2em;
}
/* one more comment */
.float-right {
    float: right;
}
"""
declarations = {
    "valid1": "color: #336699;",
    "invalid1": "value;",
    "invalid2": "property:;",
    "invalid3": "property:val; something",
}

declaration_block_with_selector = """
article#gallery {
    display: flex;
    flex-wrap: wrap;
    width: 96vw;
    margin: 0 auto;
}"""

minified_declaration_block_with_selector = "article#gallery "
minified_declaration_block_with_selector += "{display: flex;flex-wrap: "
minified_declaration_block_with_selector += "wrap;width: 96vw;margin: 0 auto;}"

invalid_css = """
body }
    background: #efefef;
    color: #101010;
{
"""

declaration_block_just_block = """
    width: 200px;
    background-color: #7D8C45;
    padding: .7em;
    border: .3em solid #142326;
    margin: .5rem;
"""

css_with_comments = """
/* css.css */
body { font-size: 120%; }
/* other comment */
h1 { font-family: serif;}
"""

external_imports_css = """
@import url('https://fonts.googleapis.com/css?family=Noto+Sans&display=swap');
body {
    background: rgb(19, 19, 19);
    color: #fff;
    font-family: 'Noto Sans', sans-serif;
}
"""

external_two_imports_css = """
@import url('https://fonts.googleapis.com/css?family=Noto+Sans&display=swap');
body {
    background: rgb(19, 19, 19);
    color: #fff;
}
@import url("http://docs.python.org/3/_static/pygments.css");
h1, h2, h3, h4 {
    color: #336699;
}
"""

# specificity of 303
selectors_with_3_ids = "body #nav div#phred, p#red"
# specificity of 014
selectors_with_no_ids = "h1, h2, h3, a:active"
specificity303 = selectors_with_3_ids
specificity014 = selectors_with_no_ids

insane_gradient = """
-moz-radial-gradient(0% 200%, ellipse cover,
rgba(143, 193, 242, 0.22) 10%,rgba(240, 205, 247,0) 40%),
-webkit-radial-gradient(0% 200%, ellipse cover,
rgba(143, 193, 242, 0.22) 10%,rgba(240, 205, 247,0) 40%),
-o-radial-gradient(0% 200%, ellipse cover,
rgba(143, 193, 242, 0.22) 10%,rgba(240, 205, 247,0) 40%),
-ms-radial-gradient(0% 200%, ellipse cover,
rgba(143, 193, 242, 0.22) 10%,rgba(240, 205, 247,0) 40%),
radial-gradient(0% 200%, ellipse cover,
rgba(143, 193, 242, 0.22) 10%,rgba(240, 205, 247,0) 40%),
-moz-linear-gradient(top, rgba(169, 235, 206,.25) 0%,
rgba(42,60,87,.4) 200%),
-ms-linear-gradient(-45deg, #46ABA6 0%, #092756 200%)',
linear-gradient(-45deg, #46ABA6 0%, #092756 200%)'
"""

css_with_bg_and_gradient = """
h4 {
        background: rgb(2,0,36);
        background: linear-gradient(90deg, rgba(2,0,36,1) 0%,
        rgba(9,9,121,1) 35%, rgba(0,212,255,1) 100%);
    }
"""

path_to_gradients_project = "tests/test_files/"
path_to_gradients_project += "projects/page_with_gradients_and_alpha/style.css"
path_to_general_css = "tests/test_files/large_project/css/general.css"
gallery_path = "tests/test_files/large_project/gallery.html"


@pytest.fixture
def general_stylesheet():
    css_code = clerk.file_to_string(path_to_general_css)
    stylesheet = css_tools.Stylesheet("general.css", css_code)
    return stylesheet


@pytest.fixture
def stylesheet_with_gradients():
    css_code = clerk.file_to_string(path_to_gradients_project)
    stylesheet = css_tools.Stylesheet("style.css", css_code)
    return stylesheet


@pytest.fixture
def css_with_external_imports():
    stylesheet = css_tools.Stylesheet("style tag", external_imports_css)
    return stylesheet


@pytest.fixture
def css_with_two_external_imports():
    stylesheet = css_tools.Stylesheet("style tag", external_two_imports_css)
    return stylesheet


@pytest.fixture
def css_code_1_split():
    code_split = css_tools.separate_code(css_code_1_with_comments)
    return code_split


@pytest.fixture
def ruleset1():
    ruleset = css_tools.Ruleset(declaration_block_with_selector)
    return ruleset


@pytest.fixture
def invalid_ruleset():
    ruleset = css_tools.Ruleset(invalid_css)
    return ruleset


@pytest.fixture
def valid_color_declaration():
    dec = css_tools.Declaration(declarations["valid1"])
    return dec


@pytest.fixture
def stylesheet_with_one_declaration_block():
    sheet = css_tools.Stylesheet("local", declaration_block_with_selector, "")
    return sheet


@pytest.fixture
def declaration_block_no_selector():
    block = css_tools.DeclarationBlock(declaration_block_just_block)
    return block


@pytest.fixture
def declaration_block_with_one_selector():
    block = css_tools.DeclarationBlock(declaration_block_with_selector)
    return block


@pytest.fixture
def layout_css():
    layout_css = clerk.file_to_string(
        "tests/test_files/large_project/css/layout.css"
    )
    yield layout_css


@pytest.fixture
def layout_css_stylesheet(layout_css):
    css_sheet = css_tools.Stylesheet("layout.css", layout_css)
    return css_sheet


@pytest.fixture
def layout_css_at_rules(layout_css_stylesheet):
    yield layout_css_stylesheet.nested_at_rules


@pytest.fixture
def styles_with_multiple_selectors():
    styles = clerk.file_to_string("tests/test_files/multiple_selectors.css")
    sheet = css_tools.Stylesheet("multiple_selectors.css", styles)
    yield sheet


@pytest.fixture
def navigation_styles():
    path = "tests/test_files/large_project/css/"
    path += "navigation.css"
    styles = clerk.file_to_string(path)
    sheet = css_tools.Stylesheet("navigation.css", styles)
    yield sheet


def test_separate_code_for_3_comments(css_code_1_split):
    assert len(css_code_1_split["comments"]) == 3


def test_separate_code_for_3_css_items(css_code_1_split):
    assert len(css_code_1_split["code"]) == 3


def test_ruleset1_for_selector(ruleset1):
    assert ruleset1.selector == "article#gallery"


def test_invalid_ruleset_for_swapped_brace_position(invalid_ruleset):
    assert not invalid_ruleset.is_valid


def test_ruleset1_for_validity(ruleset1):
    assert ruleset1.is_valid


def test_declaration_block_with_selector(declaration_block_with_one_selector):
    assert len(declaration_block_with_one_selector.declarations) == 4


def test_declaration_block_without_selector(declaration_block_no_selector):
    assert len(declaration_block_no_selector.declarations) == 5


def test_valid_color_declaration_property(valid_color_declaration):
    expected = "color"
    results = valid_color_declaration.property
    assert expected == results


def test_valid_color_declaration_is_valid(valid_color_declaration):
    assert valid_color_declaration.is_valid


def test_invalid1_declaration_for_value_error_no_colon():
    declaration = css_tools.Declaration(declarations["invalid1"])
    assert "missing a colon" in declaration.invalid_message


def test_invalid2_declaration_for_value_error_no_value():
    declaration = css_tools.Declaration(declarations["invalid2"])
    assert "missing a value" in declaration.invalid_message


def test_invalid3_declaration_for_value_error_due_to_missing_value():
    declaration = css_tools.Declaration(declarations["invalid3"])
    assert "no text after" in declaration.invalid_message


def test_nested_at_rules_for_three(layout_css):
    assert "@media" in layout_css


def test_nested_at_rules_for_non_nested_at_rule():
    with pytest.raises(ValueError):
        css_tools.NestedAtRule(declaration_block_with_selector)


def test_nested_at_rules_for_rules(layout_css_at_rules):
    rule = "@keyframes pulse"
    expected = layout_css_at_rules[0].at_rule
    assert rule == expected


def test_style_sheet_object_minify_method():
    sheet = css_tools.Stylesheet("local", declaration_block_with_selector)
    results = css_tools.minify_code(sheet.text)
    assert results == minified_declaration_block_with_selector


def test_style_sheet_object_extract_comments(layout_css_stylesheet):
    assert len(layout_css_stylesheet.comments) == 6


def test_style_sheet_object_extract_comments_for_first_comment(
    layout_css_stylesheet,
):
    assert layout_css_stylesheet.comments[0] == "/* layout.css */"


def test_stylesheet_extract_comments_for_code_after_extraction(
    layout_css_stylesheet,
):
    assert len(layout_css_stylesheet.comments) == 6


def test_stylesheet_extract_text_after_code_extraction(layout_css_stylesheet):
    assert layout_css_stylesheet.text[:6] == "body {"


def test_stylesheet_for_extracted_nested_at_rules(layout_css_stylesheet):
    assert len(layout_css_stylesheet.nested_at_rules) == 4


# Test properties of Stylesheet
def test_stylesheet_for_selectors_with_one(
    stylesheet_with_one_declaration_block,
):
    assert len(stylesheet_with_one_declaration_block.selectors) == 1


def test_layout_css_stylesheet_for_multiple_selectors(layout_css_stylesheet):
    assert len(layout_css_stylesheet.selectors) == 21


def test_has_required_property_for_display(layout_css_stylesheet):
    assert css_tools.has_required_property("display", layout_css_stylesheet)


def test_has_required_property_for_border_radius(layout_css_stylesheet):
    assert css_tools.has_required_property(
        "border-radius", layout_css_stylesheet
    )


def test_get_id_score_for_3_ids():
    results = css_tools.get_id_score(selectors_with_3_ids)
    assert results == 3


def test_get_id_score_for_no_ids():
    results = css_tools.get_id_score(selectors_with_no_ids)
    assert not results


def test_get_type_score_for_3_type_selectors():
    results = css_tools.get_type_score(selectors_with_3_ids)
    assert results == 3


def test_get_type_score_for_4_type_selectors():
    results = css_tools.get_type_score(selectors_with_no_ids)
    assert results == 4


def test_get_type_score_for_descendant_selectors():
    selector = "header h1"
    results = css_tools.get_type_score(selector)
    assert results == 2


def test_get_class_score_for_0_results():
    results = css_tools.get_class_score(selectors_with_3_ids)
    assert results == 0


def test_get_class_score_for_3_results():
    selector = "a:hover, a:link, input[type=text]"
    results = css_tools.get_class_score(selector)
    assert results == 3


def test_get_specificity_for_303():
    results = css_tools.get_specificity(specificity303)
    assert results == "303"


def test_get_specificity_for_014():
    results = css_tools.get_specificity(specificity014)
    assert results == "014"


def test_get_specificity_for_033():
    selector = "a:hover, a:link, input[type=text]"
    results = css_tools.get_specificity(selector)
    assert results == "033"


def test_get_specificity_for_002():
    selector = "header h1"
    results = css_tools.get_specificity(selector)
    assert results == "002"


def test_has_vendor_prefix_for_false():
    selector = "transition"
    results = css_tools.has_vendor_prefix(selector)
    expected = False
    assert results == expected


def test_has_vendor_prefix_for_webkit():
    selector = "-webkit-transition"
    results = css_tools.has_vendor_prefix(selector)
    expected = True
    assert results == expected


def test_has_vendor_prefix_for_moz():
    selector = "-moz-transition"
    results = css_tools.has_vendor_prefix(selector)
    expected = True
    assert results == expected


def test_has_vendor_prefix_for_property_with_dash_not_prefix():
    selector = "background-color"
    results = css_tools.has_vendor_prefix(selector)
    expected = False
    assert results == expected


def test_is_gradient_for_false():
    value = "rgba(155, 155, 155, 0)"
    results = css_tools.is_gradient(value)
    assert not results


def test_is_gradient_for_true():
    value = "-moz-radial-gradient(0% 200%, ellipse cover, "
    value += "rgba(143, 193, 242, 0.22) 10%,rgba(240, 205, 247,0) "
    value += "40%),-moz-linear-gradient(top, rgba(169, 235, 206,"
    value += ".25) 0%, rgba(42,60,87,.4) 200%), "
    value += "-moz-linear-gradient(-45deg, #46ABA6 0%, #092756 200%)"
    results = css_tools.is_gradient(value)
    assert results


def test_process_gradient_for_insane_css_for_four_returned_colors():
    colors = css_tools.process_gradient(insane_gradient)
    results = len(colors)
    expected = 4
    assert results == expected


def test_sort_color_codes_for_two_rgbas():
    colors = ["rgba(143, 193, 242, 0.22)", "rgba(240, 205, 247,0)"]
    expected = ["rgba(240, 205, 247,0)", "rgba(143, 193, 242, 0.22)"]
    results = css_tools.sort_color_codes(colors)
    assert results == expected


def test_sort_color_codes_for_three_hexes():
    colors = ["#336699", "#ff0000", "#4C3A51"]
    expected = ["#ff0000", "#336699", "#4C3A51"]
    results = css_tools.sort_color_codes(colors)
    assert results == expected


def test_get_colors_from_gradient_for_hex():
    gradient = "linear-gradient(-45deg, #46ABA6 0%, #092756 200%)"
    expected = ["#46ABA6", "#092756"]
    results = css_tools.get_colors_from_gradient(gradient)
    assert expected == results


def test_get_colors_from_gradient_for_rgba():
    gradient = (
        "linear-gradient(-45deg, rgba(200, 100, 100, 0.5) 0% #336699 100%)"
    )
    results = css_tools.get_colors_from_gradient(gradient)
    assert "rgba(200, 100, 100, 0.5)" in results


def test_stylesheet_for_color_rulesets_with_bg_and_gradient():
    results = css_tools.Stylesheet(
        "test.html", css_with_bg_and_gradient, "tag"
    )
    assert results.color_rulesets


def test_get_color_codes_of_type_for_none():
    gradient = "linear-gradient(to bottom, rgba(169, "
    gradient += "235, 206,.25) 0%,rgba(42,60,87,.4) 200%"
    colors = css_tools.get_color_codes_of_type("hsl", gradient)
    assert not colors


def test_get_color_codes_of_type_for_rgba():
    gradient = (
        "linear-gradient(to bottom, "
        "rgba(169, 235, 206,.25) 0%,rgba(42,60,87,.4) 200%"
    )
    colors = css_tools.get_color_codes_of_type("rgb", gradient)
    assert "rgba(169, 235, 206,.25)" in colors


def test_get_color_codes_of_type_for_rgb():
    gradient = (
        "linear-gradient(to bottom, rgb(169, 235, "
        "206,.25) 0%,rgba(42,60,87,.4) 200%"
    )
    colors = css_tools.get_color_codes_of_type("rgb", gradient)
    assert "rgb(169, 235, 206,.25)" in colors


def test_get_color_codes_of_type_for_hex():
    gradient = "linear-gradient(-45deg, #46ABA6 0%, #092756 200%)"
    colors = css_tools.get_color_codes_of_type("hex", gradient)
    assert "#092756" in colors


def test_get_color_codes_of_type_for_keyword_antiquewhite():
    gradient = "linear-gradient(-45deg, maroon 0%, #092756 200%)"
    colors = css_tools.get_color_codes_of_type("keywords", gradient)
    assert "maroon" in colors


def test_is_required_selector_for_not_required():
    results = css_tools.is_required_selector("id_selector", "nav ul {")
    assert not results


def test_is_required_selector_for_id_selector():
    selector = "main#main nav a.active"
    assert css_tools.is_required_selector("id_selector", selector)


def test_is_required_selector_for_class_selector():
    selector = "main#main nav a.active"
    assert css_tools.is_required_selector("class_selector", selector)


def test_is_required_selector_for_type_selector():
    selector = "main#main nav a.active"
    assert css_tools.is_required_selector("type_selector", selector)


def test_is_required_selector_for_grouped_selectors():
    selector = "h1, h2, h3 {"
    assert css_tools.is_required_selector("grouped_selector", selector)


def test_get_num_required_selectors_for_3_ids():
    css_code = "body #nav div#phred, p#red"
    css_code += "{ color: green;}"
    style_sheet = css_tools.Stylesheet("styletag", css_code)
    results = css_tools.get_number_required_selectors(
        "id_selector", style_sheet
    )
    expected = 3
    assert results == expected


def test_get_num_required_selectors_for_layout_sheet(layout_css_stylesheet):
    results = css_tools.get_number_required_selectors(
        "class_selector", layout_css_stylesheet
    )
    expected = 29
    assert results == expected


def test_has_repeat_selectors_for_false(navigation_styles):
    assert not navigation_styles.has_repeat_selectors


def test_has_repeat_selectors_for_true_layout(layout_css_stylesheet):
    assert layout_css_stylesheet.has_repeat_selectors


def test_has_repeat_selectors_for_true(styles_with_multiple_selectors):
    assert styles_with_multiple_selectors


def test_remove_external_imports(css_with_external_imports):
    assert "http" not in css_with_external_imports.text


def test_remove_two_external_imports(css_with_two_external_imports):
    assert "http" not in css_with_two_external_imports.text


def test_get_all_stylesheets_by_file_for_4_sheets():
    results = css_tools.get_all_stylesheets_by_file(gallery_path)
    assert len(results) == 4


def test_get_all_stylesheets_for_style_tag():
    results = css_tools.get_all_stylesheets_by_file(gallery_path)
    assert "styletag" in results[0].type


def test_get_font_families_for_one(css_with_external_imports):
    results = css_tools.get_font_families(css_with_external_imports)
    assert "noto sans" in results[0].get("family")


def test_get_families_for_declaration_block():
    stylesheet = css_tools.Stylesheet("sample.css", css_code_1_with_comments)
    ruleset = stylesheet.rulesets[1]
    results = css_tools.get_families(ruleset.declaration_block)
    assert "sans-serif" in results


def test_get_font_families_for_two(general_stylesheet):
    results = css_tools.get_font_families(general_stylesheet)
    assert len(results) == 2
