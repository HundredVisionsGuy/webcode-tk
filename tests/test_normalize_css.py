import pytest
from bs4 import BeautifulSoup

from webcode_tk import contrast_tools


def test_normalize_css_value_color_initial():
    """Test that color: initial resolves to DEFAULT_GLOBAL_COLOR."""
    result = contrast_tools.normalize_css_value("initial", "color", None, {})
    assert result == contrast_tools.DEFAULT_GLOBAL_COLOR
    assert result == "#000000"


def test_normalize_css_value_background_color_initial():
    """Test that background-color: initial resolves to default."""
    result = contrast_tools.normalize_css_value(
        "initial", "background-color", None, {}
    )
    assert result == contrast_tools.DEFAULT_GLOBAL_BACKGROUND
    assert result == "#ffffff"


def test_normalize_css_value_color_non_initial():
    """Test that non-initial color values pass through unchanged."""
    result = contrast_tools.normalize_css_value("#ff0000", "color", None, {})
    assert result == "#ff0000"


def test_normalize_css_value_background_non_initial():
    """Test that non-initial background values pass through unchanged."""
    result = contrast_tools.normalize_css_value(
        "#ffffff", "background-color", None, {}
    )
    assert result == "#ffffff"


def test_normalize_css_value_initial_case_insensitive():
    """Test that initial keyword is handled case-insensitively."""
    result = contrast_tools.normalize_css_value("INITIAL", "color", None, {})
    assert result == contrast_tools.DEFAULT_GLOBAL_COLOR


def test_normalize_css_value_named_color():
    """Test that named colors pass through unchanged."""
    result = contrast_tools.normalize_css_value("blue", "color", None, {})
    assert result == "blue"


@pytest.fixture
def initial_color_html():
    """HTML with color property set to initial in CSS rule."""
    return """
    <html>
    <head>
        <style>
            p { color: initial; }
        </style>
    </head>
    <body>
        <p>Text with initial color</p>
    </body>
    </html>
    """


@pytest.fixture
def initial_background_html():
    """HTML with background-color property set to initial."""
    return """
    <html>
    <head>
        <style>
            p { background-color: initial; }
        </style>
    </head>
    <body>
        <p>Text with initial background</p>
    </body>
    </html>
    """


@pytest.fixture
def initial_mixed_html():
    """HTML with explicit color and initial background."""
    return """
    <html>
    <head>
        <style>
            p { color: #ff0000; background-color: initial; }
        </style>
    </head>
    <body>
        <p>Red text on white background</p>
    </body>
    </html>
    """


@pytest.fixture
def initial_breaks_inheritance_html():
    """HTML where initial breaks CSS inheritance chain."""
    return """
    <html>
    <head>
        <style>
            body { color: #333333; }
            p { color: initial; }
        </style>
    </head>
    <body>
        <p>Text with initial breaks inheritance</p>
    </body>
    </html>
    """


def test_initial_color_in_contrast_analysis(initial_color_html, tmp_path):
    """Integration test: color: initial resolves and contrast analysis
    succeeds."""
    # Create temp HTML file
    html_file = tmp_path / "test.html"
    html_file.write_text(initial_color_html)

    # Parse and apply defaults
    soup = BeautifulSoup(initial_color_html, "html.parser")
    default_styles = contrast_tools.apply_browser_defaults(soup)

    # Get the p element
    p_element = soup.find("p")
    assert p_element in default_styles

    # Create a mock rule
    rule = {"selector": "p", "declarations": {"color": "initial"}}

    # Manually apply the rule (simulating CSS cascade)
    computed_styles = {p_element: default_styles[p_element]}
    contrast_tools.apply_rule_to_element(p_element, rule, computed_styles)

    # Verify color was normalized to DEFAULT_GLOBAL_COLOR
    assert (
        computed_styles[p_element]["color"]["value"]
        == contrast_tools.DEFAULT_GLOBAL_COLOR
    )


def test_initial_background_in_contrast_analysis(initial_background_html):
    """Integration test: background-color: initial resolves correctly."""
    soup = BeautifulSoup(initial_background_html, "html.parser")
    default_styles = contrast_tools.apply_browser_defaults(soup)

    p_element = soup.find("p")
    assert p_element in default_styles

    # Create rule with initial background
    rule = {"selector": "p", "declarations": {"background-color": "initial"}}

    computed_styles = {p_element: default_styles[p_element]}
    contrast_tools.apply_rule_to_element(p_element, rule, computed_styles)

    # Verify background-color was normalized
    assert (
        computed_styles[p_element]["background-color"]["value"]
        == contrast_tools.DEFAULT_GLOBAL_BACKGROUND
    )


def test_initial_mixed_explicit_and_initial(initial_mixed_html):
    """Integration test: mixed explicit color with initial background."""
    soup = BeautifulSoup(initial_mixed_html, "html.parser")
    default_styles = contrast_tools.apply_browser_defaults(soup)

    p_element = soup.find("p")

    # Apply both rules
    rule1 = {"selector": "p", "declarations": {"color": "#ff0000"}}
    rule2 = {"selector": "p", "declarations": {"background-color": "initial"}}

    computed_styles = {p_element: default_styles[p_element]}
    contrast_tools.apply_rule_to_element(p_element, rule1, computed_styles)
    contrast_tools.apply_rule_to_element(p_element, rule2, computed_styles)

    # Verify both values
    assert computed_styles[p_element]["color"]["value"] == "#ff0000"
    assert (
        computed_styles[p_element]["background-color"]["value"]
        == contrast_tools.DEFAULT_GLOBAL_BACKGROUND
    )


def test_initial_breaks_inheritance(initial_breaks_inheritance_html):
    """Integration test: initial keyword breaks CSS inheritance chain."""
    soup = BeautifulSoup(initial_breaks_inheritance_html, "html.parser")
    default_styles = contrast_tools.apply_browser_defaults(soup)

    body_element = soup.find("body")
    p_element = soup.find("p")

    # Apply body color rule
    body_rule = {"selector": "body", "declarations": {"color": "#333333"}}

    # Apply p color rule with initial
    p_rule = {"selector": "p", "declarations": {"color": "initial"}}

    computed_styles = {
        body_element: default_styles[body_element],
        p_element: default_styles[p_element],
    }

    contrast_tools.apply_rule_to_element(
        body_element, body_rule, computed_styles
    )
    contrast_tools.apply_rule_to_element(p_element, p_rule, computed_styles)

    # Body should have #333333
    assert computed_styles[body_element]["color"]["value"] == "#333333"

    # P should have DEFAULT_GLOBAL_COLOR, not inherited #333333
    assert (
        computed_styles[p_element]["color"]["value"]
        == contrast_tools.DEFAULT_GLOBAL_COLOR
    )
    assert computed_styles[p_element]["color"]["value"] != "#333333"


def test_initial_with_no_error_in_contrast_calculation(initial_mixed_html):
    """Integration test: contrast calculation succeeds with initial-normalized
    values."""
    from webcode_tk import color_tools

    soup = BeautifulSoup(initial_mixed_html, "html.parser")
    default_styles = contrast_tools.apply_browser_defaults(soup)

    p_element = soup.find("p")

    # Apply rules
    rule1 = {"selector": "p", "declarations": {"color": "#ff0000"}}
    rule2 = {"selector": "p", "declarations": {"background-color": "initial"}}

    computed_styles = {p_element: default_styles[p_element]}
    contrast_tools.apply_rule_to_element(p_element, rule1, computed_styles)
    contrast_tools.apply_rule_to_element(p_element, rule2, computed_styles)

    # Extract colors and calculate contrast
    text_color = computed_styles[p_element]["color"]["value"]
    bg_color = computed_styles[p_element]["background-color"]["value"]

    color_hex = color_tools.get_hex(text_color)
    bg_hex = color_tools.get_hex(bg_color)

    # Should succeed without error
    contrast_ratio = color_tools.contrast_ratio(color_hex, bg_hex)

    # Red (#ff0000) on white (#ffffff) should have valid contrast ratio
    assert contrast_ratio > 0
    assert contrast_ratio == pytest.approx(
        3.998, rel=0.01
    )  # Approximate value for red on white


def test_initial_case_insensitive_in_contrast(tmp_path):
    """Integration test: INITIAL (uppercase) also gets normalized."""
    html = """
    <html>
    <head>
        <style>
            p { color: INITIAL; }
        </style>
    </head>
    <body>
        <p>Text</p>
    </body>
    </html>
    """

    soup = BeautifulSoup(html, "html.parser")
    default_styles = contrast_tools.apply_browser_defaults(soup)

    p_element = soup.find("p")

    rule = {"selector": "p", "declarations": {"color": "INITIAL"}}

    computed_styles = {p_element: default_styles[p_element]}
    contrast_tools.apply_rule_to_element(p_element, rule, computed_styles)

    # Should normalize uppercase INITIAL too
    assert (
        computed_styles[p_element]["color"]["value"]
        == contrast_tools.DEFAULT_GLOBAL_COLOR
    )
