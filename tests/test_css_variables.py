import pytest

from webcode_tk import contrast_tools as contrast

project_dir = "tests/test_files/css_variables_test/"


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
        if page_path in r.get("file", "") and r.get("selector") == selector
    ]

    assert (
        len(matching_result) > 0
    ), f"No result found for {selector} in {page}"

    element_result = matching_result[0]
    assert element_result.get("color") == expected_color
    assert element_result.get("background-color") == expected_bg
