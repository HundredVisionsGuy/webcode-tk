import pytest
from file_clerk import clerk

from webcode_tk import cascade_tools as cascade
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

variables = """
:root {
    --bg-text:#303030;
    --alt-text:#2ba5bd;
    --alt-bg:#ffb020;
    --light-bg:#2F6BA7;
    --border:#2ba5bd;
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

path_to_general_css = "tests/test_files/large_project/css/general.css"


@pytest.fixture
def large_project_path():
    return "tests/test_files/large_project/"


@pytest.fixture
def gallery_path():
    return "tests/test_files/large_project/gallery.html"


@pytest.fixture
def about_path(large_project_path):
    return large_project_path + "about.html"


@pytest.fixture
def general_stylesheet():
    css_code = clerk.file_to_string(path_to_general_css)
    stylesheet = css_tools.Stylesheet("general.css", css_code)
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


def test_css_with_variables_for_replaced_var_functions():
    file_path = "tests/test_files/css_with_variables.css"
    code = clerk.file_to_string(file_path)
    sheet = css_tools.Stylesheet("css_with_variables", code, "file")
    expected = sheet.rulesets[1].declaration_block.text
    assert "var(--bg-text)" not in expected


def test_get_variables_for_list_of_variables():
    expected = css_tools.get_variables(variables)
    assert len(expected) == 5


def test_get_variables_for_nonexistant_variables():
    """It should not crash if there are no variables"""
    expected = css_tools.get_variables(css_with_bg_and_gradient)
    assert not expected


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


def test_declaration_is_color_for_true(valid_color_declaration):
    assert valid_color_declaration.is_color


def test_declaration_is_color_for_false(ruleset1):
    declarations = ruleset1.declaration_block.declarations
    assert not declarations[0].is_color


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
    assert len(layout_css_stylesheet.selectors) == 22


def test_has_required_property_for_display(layout_css_stylesheet):
    assert css_tools.has_required_property("display", layout_css_stylesheet)


def test_has_required_property_for_border_radius(layout_css_stylesheet):
    assert css_tools.has_required_property(
        "border-radius", layout_css_stylesheet
    )


def test_get_id_score_for_3_ids():
    results = css_tools.get_id_score(selectors_with_3_ids)
    assert results == 3


def test_get_id_score_for_hash_in_middle_of_selector():
    selector = "body#image-gallery"
    results = css_tools.get_id_score(selector)
    assert results == 1


def test_get_id_score_for_no_ids():
    results = css_tools.get_id_score(selectors_with_no_ids)
    assert not results


def test_get_type_score_for_3_type_selectors():
    results = css_tools.get_type_score(selectors_with_3_ids)
    assert results == 3


def test_get_type_score_for_hyphenated_selector():
    results = css_tools.get_type_score("nav.primary-nav")
    assert results == 1


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


def test_get_specificity_for_101():
    selector = "body#image-gallery"
    results = css_tools.get_specificity(selector)
    assert results == "101"


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


def test_get_selector_type_for_descendant():
    selector = "header h1"
    results = css_tools.get_selector_type(selector)
    assert results == "descendant_selector"


def test_get_selector_type_for_type_selector():
    selector = "p"
    results = css_tools.get_selector_type(selector)
    assert results == "type_selector"


def test_get_selector_type_for_id_selector():
    selector = "body#main"
    results = css_tools.get_selector_type(selector)
    assert results == "id_selector"


def test_get_selector_type_for_class_selector():
    selector = ".primary"
    results = css_tools.get_selector_type(selector)
    assert results == "class_selector"


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


def test_get_all_stylesheets_by_file_for_4_sheets(gallery_path):
    results = css_tools.get_all_stylesheets_by_file(gallery_path)
    assert len(results) == 4


def test_get_all_stylesheets_for_style_tag(gallery_path):
    results = css_tools.get_all_stylesheets_by_file(gallery_path)
    assert "styletag" in results[0].type


def test_get_font_families_for_one(css_with_external_imports):
    results = css_tools.get_font_families(css_with_external_imports)
    assert "noto sans" in results[0].get("family").lower()


def test_get_font_families_for_two(general_stylesheet):
    results = css_tools.get_font_families(general_stylesheet)
    assert len(results) == 2


def test_get_all_stylesheets_by_file(about_path):
    expected = css_tools.get_all_stylesheets_by_file(about_path)
    assert len(expected) == 4


def test_get_styles_by_html_files_for_filenames(large_project_path):
    styles = css_tools.get_styles_by_html_files(large_project_path)
    results = []
    for style in styles:
        results.append(style.get("file"))
    expected = large_project_path + "gallery.html"
    assert expected in results


def test_get_styles_by_html_files_for_no_styles(large_project_path):
    styles_by_files = css_tools.get_styles_by_html_files(large_project_path)
    results = styles_by_files[-1].get("styleheets")
    assert not results


def test_get_project_global_colors_for_2_sets(large_project_path):
    global_colors = css_tools.get_project_global_colors(large_project_path)
    results = list(global_colors.keys())
    assert len(results) == 2


def test_get_global_colors_for_single_file(gallery_path):
    global_colors = css_tools.get_global_colors(gallery_path)
    results = global_colors[gallery_path].get("background-color")
    expected = "rgb(206, 208, 198)"
    assert results == expected


def test_passes_global_color_contrast_for_gallery(gallery_path):
    results = css_tools.passes_global_color_contrast(gallery_path)
    assert results


def test_get_unique_font_rules_for_2_sets_in_about(large_project_path):
    files_data = css_tools.get_unique_font_rules(large_project_path)
    results = []
    for file in files_data:
        filename = file.get("file")
        if "about.html" in filename:
            results = file.get("rules")
            break
    expected = 2
    assert (len(results)) == expected


def test_get_unique_font_rules_for_0_sets_in_index(large_project_path):
    files = css_tools.get_unique_font_rules(large_project_path)
    for file in files:
        desired_file_name = "tests/test_files/large_project/index.html"
        if file.get("file") == desired_file_name:
            results = file.get("rules")
    expected = 0
    assert len(results) == expected


def test_get_color_rules_from_stylesheet_for_11_declarations(
    styles_with_multiple_selectors,
):
    results = css_tools.get_color_rules_from_stylesheet(
        styles_with_multiple_selectors
    )
    assert len(results) == 11


def test_get_background_color_for_gradient():
    styles = css_tools.Stylesheet("page.html", css_with_bg_and_gradient)
    declaration = styles.rulesets[0].declaration_block.declarations[1]
    results = css_tools.get_background_color(declaration)
    assert results == "gradient"


def test_get_background_color_for_rgb_color():
    styles = css_tools.Stylesheet("style tag", external_imports_css)
    declaration = styles.rulesets[0].declaration_block.declarations[0]
    results = css_tools.get_background_color(declaration)
    assert results == "rgb(19, 19, 19)"


def test_get_background_color_for_hex(general_stylesheet):
    declaration_block = general_stylesheet.rulesets[1].declaration_block
    declaration = declaration_block.declarations[2]
    results = css_tools.get_background_color(declaration)
    assert results == "#bbddff"


def test_get_background_color_for_none(general_stylesheet):
    code = "body { background: url('bg.jpg') left top; }"
    styles = css_tools.Stylesheet("style tag", code)
    declaration_block = styles.rulesets[0].declaration_block
    declaration = declaration_block.declarations[0]
    results = css_tools.get_background_color(declaration)
    assert not results


def test_condense_the_rules(about_path):
    non_condensed = [
        (about_path, "body", "color", "aliceblue"),
        (about_path, "body", "background-color", "darkred"),
    ]
    results = css_tools.condense_the_rules(non_condensed, about_path)
    assert (
        results["body"]["color"] == "aliceblue"
        and results["body"]["background-color"] == "darkred"
    )


def test_get_project_color_contrast_for_header_h1_in_large(large_project_path):
    contrast_results = css_tools.get_project_color_contrast(large_project_path)
    expected = []
    for result in contrast_results:
        matching_result = (
            "about.html" in result[0] and result[1] == "header h1"
        )
        if matching_result:
            is_large = result[2] == "Large AAA"
            expected.append(is_large)
            contrast_is_correct = result[5] == 4.46
            expected.append(contrast_is_correct)
            break
    if expected:
        assert expected[0] and expected[1]
    else:
        assert expected


def test_file_applies_property_by_selector_for_h1_applied(about_path):
    results = css_tools.file_applies_property_by_selector(
        about_path, "h1", "padding"
    )
    assert results


def test_get_declaration_block_from_selector_for_h1(general_stylesheet):
    results = css_tools.get_declaration_block_from_selector(
        "h1", general_stylesheet
    )
    assert "righteous" in results.lower()


def test_is_selector_at_end_of_descendant_for_selector_plus_class():
    results = css_tools.is_selector_at_end_of_descendant(
        "h1", "header div h1.main"
    )
    assert results


def test_get_declaration_value_by_property_for_string(
    declaration_block_with_one_selector,
):
    declaration = declaration_block_with_one_selector.text
    results = css_tools.get_declaration_value_by_property(declaration, "width")
    assert "96vw" == results


def test_test_get_declaration_value_by_property_for_declaration_block(
    declaration_block_with_one_selector,
):
    results = css_tools.get_declaration_value_by_property(
        declaration_block_with_one_selector, "display"
    )
    assert "flex" == results


def test_has_link_selector_for_false(general_stylesheet):
    results = css_tools.has_link_selector(general_stylesheet)
    assert not results


def test_has_link_selector_for_single_a(styles_with_multiple_selectors):
    results = css_tools.has_link_selector(styles_with_multiple_selectors)
    assert results


def test_has_link_selector_for_multiple_links(navigation_styles):
    results = css_tools.has_link_selector(navigation_styles)
    assert results


def test_get_all_link_selectors_for_two(navigation_styles):
    results = css_tools.get_all_link_selectors(navigation_styles)
    assert len(results) == 2


def test_get_all_link_rules_for_two(navigation_styles):
    results = css_tools.get_all_link_rules(navigation_styles)
    assert len(results) == 2


def test_get_all_font_rules_for_number(general_stylesheet):
    results = css_tools.get_all_font_rules(general_stylesheet)
    assert len(results) == 2


def test_get_all_font_rules_for_four(layout_css_stylesheet):
    results = css_tools.get_all_font_rules(layout_css_stylesheet)
    assert len(results) == 5


def test_get_link_color_data_for_large_project(large_project_path):
    results = css_tools.get_link_color_data(large_project_path)
    assert len(results) == 4


def test_get_link_color_data_for_nav_li_a_failure(large_project_path):
    color_data = css_tools.get_link_color_data(large_project_path)
    results = (
        "tests/test_files/large_project/about.html",
        "nav li a",
        "Normal AAA",
        "rgb(114, 101, 87)",
        "beige",
        5.1,
        False,
    ) in color_data
    assert results


def test_get_all_color_rules_for_hover_link_inheritance():
    wonka = "tests/test_files/wiliwonka.html"
    color_rules = css_tools.get_all_color_rules(wonka)
    a_hover = color_rules.get("a:hover")
    results = a_hover.get("background-color")
    assert results == "darkblue"


def test_get_project_color_contrast_for_single_file_project():
    single_file = "tests/test_files/single_file_project"
    results = css_tools.get_project_color_contrast(single_file)
    assert results


def test_get_psuedo_element_score_for1():
    selector = "nav > a:hover::before"
    expected = 1
    results = css_tools.get_psuedo_element_score(selector)
    assert expected == results


def test_get_specificity_for_pseudo_element_inclusion():
    selector = "nav > a:hover::before"
    expected = "013"
    results = css_tools.get_specificity(selector)
    assert results == expected


def test_get_font_families_for_at_import_url():
    path = "tests/test_files/file_with_at_import_url.html"
    results = css_tools.get_all_stylesheets_by_file(path)
    assert len(results[0].rulesets) > 1


# Test CSS report style functions
def test_get_all_project_stylesheets_for_large_project(large_project_path):
    expected = 4
    sheets = css_tools.get_all_project_stylesheets(large_project_path)
    results = len(sheets[0][1])
    assert expected == results


@pytest.fixture
def project_attribute_report():
    directory = "tests/test_files/project"
    results = css_tools.no_style_attributes_allowed_report(directory)
    return results


def test_no_style_attributes_allowed_report_for_number_files(
    project_attribute_report,
):
    expected = 5
    assert len(project_attribute_report) == expected


def test_no_style_attributes_allowed_report_for_fail(project_attribute_report):
    failures = 0
    for i in project_attribute_report:
        if "fail" in i[:5]:
            failures += 1
    expected = 4
    assert failures == expected


def test_no_style_attributes_allowed_report_for_pass(project_attribute_report):
    successes = 0
    for i in project_attribute_report:
        if "pass" in i[:5]:
            successes += 1
    expected = 1
    assert successes == expected


def test_styles_applied_report_for_large_project(large_project_path):
    report = css_tools.styles_applied_report(large_project_path)
    passes = 0
    fails = 0
    for item in report:
        if "pass" in item[:4]:
            passes += 1
        else:
            fails += 1
    expected = passes == 2 and fails == 1
    assert expected


def test_fonts_applied_report_for_one_fail_2_required(large_project_path):
    report = css_tools.fonts_applied_report(large_project_path, min=2)
    passes = 0
    fails = 0
    for file in report:
        if "pass" in file[:4]:
            passes += 1
        else:
            fails += 1
    expected = passes == 2 and fails == 1
    assert expected


def test_fonts_applied_for_NoneType_error():
    path = "tests/test_files/debugging_project/"
    passes = 0
    fails = 0
    report = css_tools.fonts_applied_report(path, min=2)
    for file in report:
        if "pass" in file[:4]:
            passes += 1
        else:
            fails += 1
    expected = passes == 1 and fails == 1
    assert expected


def test_fonts_applied_report_for_min_2_fail():
    dir = "tests/test_files/project"
    report = css_tools.fonts_applied_report(dir, min=2)
    fails = 0
    has_one_font = 0
    for file in report:
        if "fail" in file[:4]:
            fails += 1
        if "fail: test.html did not apply 2" in file:
            has_one_font += 1
    expected = fails == 5 and has_one_font == 1
    assert expected


def test_get_global_color_report_for_single_file_pass():
    path = "tests/test_files/single_file_project"
    report = css_tools.get_global_color_report(path)
    assert "pass:" in report[0]


def test_get_global_color_report_for_large_project_pass(large_project_path):
    report = css_tools.get_global_color_report(large_project_path)
    passes = 0
    fails = 0
    for file in report:
        if "pass" in file[:4]:
            passes += 1
        else:
            fails += 1
    assert passes == 2 and fails == 1


def test_get_heading_color_report_for_large_project(large_project_path):
    report = css_tools.get_heading_color_report(large_project_path)
    passes = 0
    fails = 0
    for file in report:
        if "pass" in file[:4]:
            passes += 1
        else:
            fails += 1
    assert passes == 2 and fails == 1


def test_get_heading_color_report_for_project_inner():
    path = "tests/test_files/project/inner_folder"
    report = css_tools.get_heading_color_report(path)
    assert "pass:" in report[0]


# Test get_project_color_contrast_report
debugging_dir = "tests/test_files/debugging_project/"


@pytest.fixture
def debugging_project_color_report():
    report = css_tools.get_project_color_contrast_report(debugging_dir)
    return report


def test_css_for_color_contrast_report_a_visited_fails(
    debugging_project_color_report,
):
    fails = 0
    for item in debugging_project_color_report:
        if "fail" in item:
            fails += 1
    expected = fails == 1
    assert expected


def test_get_element_rulesets_for_figure_in_cascade_complexities():
    rulesets = css_tools.get_element_rulesets(
        "tests/test_files/cascade_complexities", "figure"
    )
    assert len(rulesets) == 4


def test_get_properties_applied_report_for_figure_2_fails():
    project_folder = "tests/test_files/cascade_complexities"
    goals = {
        "figure": {
            "properties": ("margin", "padding", "border", "float"),
        }
    }
    report = css_tools.get_properties_applied_report(project_folder, goals)
    fails = 0
    for item in report:
        if "fail" in item:
            fails += 1
    assert fails == 4


# Test variations on get_properties_applied function
project_folder = "tests/test_files/cascade_complexities"
properties_applied_simple = {
    "figure": {
        "properties": ("box-shadow", "border-radius", "animation"),
    }
}
properties_applied_min_2 = {
    "main": {
        "properties": ("box-shadow", "border-radius", "animation"),
        "min_required": 2,
    }
}
targets_main_tag_by_advanced = {
    "main": {"properties": ("box-shadow", "animation"), "min_required": 1}
}
simple_properties_applied_report = css_tools.get_properties_applied_report(
    project_folder, properties_applied_simple
)
properties_with_2_min_required = css_tools.get_properties_applied_report(
    project_folder, properties_applied_min_2
)
main_targets_animation_with_id = css_tools.get_properties_applied_report(
    project_folder, targets_main_tag_by_advanced
)


@pytest.mark.parametrize("results", simple_properties_applied_report)
def test_for_properties_applied_simple(results):
    if "amharic.html" in results:
        assert "fail:" in results[:5] and "3" in results
    elif "index.html" in results:
        assert "fail:" in results[:5] and "2" in results
    elif "keyframe-animation.html" in results:
        # this should fail because it does NOT target figure at all
        assert "fail:" in results[:5] and "3" in results
    elif "ufo.html" in results:
        assert "fail:" in results[:5] and "3" in results
    else:
        assert "pass:" in results[:5]


def test_get_properties_for_min2_properties_1_pass_2_fail():
    passed = 0
    failed = 0
    for result in properties_with_2_min_required:
        if "pass:" in result[:5]:
            passed += 1
        if "fail:" in result[:5]:
            failed += 1
    assert passed == 1 and failed == 4


def test_get_properties_for_solely_id_targetted():
    for result in main_targets_animation_with_id:
        if "amharic.html" in result:
            assert "pass:" == result[:5]


# Adding some color styles that are not just color or bg color
# could trigger errors, so we'll test it through the cascade
# tool, where I first discovered the error
# TODO: move the test to just test the stylesheet (not urgent)
non_text_color_colors_path = "tests/test_files/non_text_color_colors"
non_text_color_colors_results = []
non_text_color_colors_results = cascade.get_color_contrast_report(
    non_text_color_colors_path
)


@pytest.mark.parametrize("results", non_text_color_colors_results)
def test_for_nonetype_error_in_image_gallery(results):
    assert "fail:" in results[:5]
