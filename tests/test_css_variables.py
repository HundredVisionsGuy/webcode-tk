import pytest

from webcode_tk import contrast_tools as contrast
from webcode_tk import css_tools

project_dir = "tests/test_files/css_variables_test/"


# test extract_variables_for_document
@pytest.mark.parametrize(
    "html_file,var_name,expected_entries",
    [
        # page1.html tests
        (
            "page1.html",
            "--primary-color",
            [
                {
                    "value": "#333",
                    "selector": ":root",
                    "specificity": "010",
                    "sheet_index": 0,
                },
                {
                    "value": "#111",
                    "selector": ":root",
                    "specificity": "010",
                    "sheet_index": 2,
                },
            ],
        ),
        (
            "page1.html",
            "--text-color",
            [
                {
                    "value": "#160739",
                    "selector": ":root",
                    "specificity": "010",
                    "sheet_index": 0,
                },
            ],
        ),
        (
            "page1.html",
            "--p-color",
            [
                {
                    "value": "#111c26",
                    "selector": ":root",
                    "specificity": "010",
                    "sheet_index": 0,
                },
            ],
        ),
        (
            "page1.html",
            "--bg-color",
            [
                {
                    "value": "#bdd7bd",
                    "selector": ":root",
                    "specificity": "010",
                    "sheet_index": 0,
                },
            ],
        ),
        # page2.html tests
        (
            "page2.html",
            "--primary-color",
            [
                {
                    "value": "#333",
                    "selector": ":root",
                    "specificity": "010",
                    "sheet_index": 0,
                },
                {
                    "value": "#d7e3d8",
                    "selector": ":root",
                    "specificity": "010",
                    "sheet_index": 2,
                },
            ],
        ),
        (
            "page2.html",
            "--bg-color",
            [
                {
                    "value": "#bdd7bd",
                    "selector": ":root",
                    "specificity": "010",
                    "sheet_index": 0,
                },
                {
                    "value": "#1b0505",
                    "selector": ":root",
                    "specificity": "010",
                    "sheet_index": 2,
                },
            ],
        ),
    ],
)
def test_extract_variables_for_document(html_file, var_name, expected_entries):
    html_path = f"tests/test_files/css_variables_test/{html_file}"

    # get stylesheets
    stylesheets = css_tools.get_all_stylesheets_by_file(html_path)
    variables_registry = css_tools.extract_variables_for_document(stylesheets)

    assert var_name in variables_registry
    actual_entries = variables_registry[var_name]

    for expected in expected_entries:
        assert expected in actual_entries


@pytest.mark.parametrize(
    "page,selector,expected_color,expected_bg",
    [
        ("page1.html", "p", "#111", "#bdd7bd"),  # Override in page1 style tag
        ("page1.html", "p.highlight", "#ccc", "#bdd7bd"),  # Uses fallback
        (
            "page2.html",
            "p",
            "#d7e3d8",
            "#1b0505",
        ),  # Override in page2 style tag
        ("page2.html", "a", "#b0dab4", "#1b0505"),  # Uses fallback
    ],
)
def test_css_variables_contrast_resolution(
    page, selector, expected_color, expected_bg
):
    # Run contrast analysis for the project
    results = contrast.analyze_contrast(project_dir)

    # Find the matching element result
    page_path = f"{project_dir}{page}"
    matching_result = [
        r
        for r in results
        if page_path in r.get("filename", "") and r.get("selector") == selector
    ]

    assert (
        len(matching_result) > 0
    ), f"No result found for {selector} in {page}"

    element_result = matching_result[0]
    assert element_result.get("color") == expected_color
    assert element_result.get("background-color") == expected_bg


@pytest.mark.parametrize(
    "var_name,fallback,expected_value,expected_resolved",
    [
        # Variable exists in registry
        ("--primary-color", None, "#111", True),
        ("--text-color", None, "#160739", True),
        # Variable doesn't exist, has fallback
        ("--missing-color", "#b0dab4", "#b0dab4", False),
        ("--undefined-var", "#ccc", "#ccc", False),
        # Variable doesn't exist, no fallback
        ("--nonexistent", None, None, False),
    ],
)
def test_resolve_variable(
    var_name, fallback, expected_value, expected_resolved
):
    html_path = "tests/test_files/css_variables_test/page1.html"
    # Get stylesheets first (NEW)
    stylesheets = css_tools.get_all_stylesheets_by_file(html_path)
    # Pass stylesheets instead of html_path (CHANGED)
    variables_registry = css_tools.extract_variables_for_document(stylesheets)

    resolved_value, was_resolved = css_tools.resolve_variable(
        var_name, variables_registry, fallback
    )

    assert resolved_value == expected_value
    assert was_resolved == expected_resolved


results = contrast.analyze_contrast(project_dir)
variables_results = {
    "h1": {"page1.html": [], "page3.html": []},
    "p": {"page1.html": [], "page3.html": []},
    "p.highlight": {"page1.html": [], "page3.html": []},
}
for result in results:
    filename = result.get("filename")
    if filename == "page2.html":
        continue
    tag = result.get("element_tag")

    if result.get("element_tag") == "h1":
        header_data = variables_results[tag].get(filename)
        if len(header_data) <= 2:
            color = result.get("text_color")
            bg_color = result.get("background_color")
            contrast_ratio = result.get("contrast_ratio")
            variables_results[tag][filename].append(
                ["", color, bg_color, contrast_ratio]
            )
        else:
            continue
    elif result.get("element_tag") == "p" and not result.get("element_class"):
        p_data = variables_results[tag].get(filename)
        if len(p_data) < 2:
            color = result.get("text_color")
            bg_color = result.get("background_color")
            contrast_ratio = result.get("contrast_ratio")
            variables_results[tag][filename].append(
                ["no class", color, bg_color, contrast_ratio]
            )
    elif result.get("element_tag") == "p" and result.get("element_class"):
        p_data = variables_results["p.highlight"].get(filename)
        if len(p_data) <= 2:
            color = result.get("text_color")
            bg_color = result.get("background_color")
            contrast_ratio = result.get("contrast_ratio")
            element_classes = result.get("element_class")
            variables_results["p.highlight"][filename].append(
                ["classes", color, bg_color, contrast_ratio]
            )
variables_integration_data = []
for item in variables_results.items():
    element = item[0]
    filename_data = item[1]
    page1, page2 = filename_data.keys()
    page1_results = filename_data.get(page1)[0]
    page2_results = filename_data.get(page2)[0]
    variables_integration_data.append([page1_results, page2_results])


@pytest.mark.parametrize(
    "var_results,no_var_results", variables_integration_data
)
def test_variables_resolve_same_as_hardcoded(var_results, no_var_results):
    """Integration test: Variables resolve to same results as hardcoded colors.

    page1.html uses CSS variables via theme.css and reset.css
    page3.html uses hardcoded colors in page3_styles.css
    Both should produce identical contrast analysis results.
    """
    assert var_results == no_var_results
