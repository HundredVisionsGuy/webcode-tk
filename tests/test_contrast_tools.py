import os

from bs4 import BeautifulSoup

from webcode_tk.contrast_tools import append_style_data
from webcode_tk.contrast_tools import apply_browser_defaults
from webcode_tk.contrast_tools import apply_css_inheritance
from webcode_tk.contrast_tools import apply_rule_to_element
from webcode_tk.contrast_tools import apply_visual_background_inheritance
from webcode_tk.contrast_tools import convert_font_size_to_pixels
from webcode_tk.contrast_tools import DEFAULT_GLOBAL_BACKGROUND
from webcode_tk.contrast_tools import DEFAULT_GLOBAL_COLOR
from webcode_tk.contrast_tools import DEFAULT_LINK_COLOR
from webcode_tk.contrast_tools import DEFAULT_LINK_VISITED
from webcode_tk.contrast_tools import find_ancestor_background
from webcode_tk.contrast_tools import find_matching_elements
from webcode_tk.contrast_tools import get_css_source_order
from webcode_tk.contrast_tools import get_or_parse_external_stylesheet
from webcode_tk.contrast_tools import get_parent_font_size
from webcode_tk.contrast_tools import get_parsed_documents
from webcode_tk.contrast_tools import HEADING_FONT_SIZES
from webcode_tk.contrast_tools import is_selector_supported_by_bs4
from webcode_tk.contrast_tools import load_css_files
from webcode_tk.contrast_tools import parse_internal_style_tag
from webcode_tk.contrast_tools import ROOT_FONT_SIZE


def test_get_parsed_documents(tmp_path):
    # Create sample HTML files
    file1 = tmp_path / "index.html"
    file1.write_text("<html><body><h1>Home</h1></body></html>")
    file2 = tmp_path / "about.html"
    file2.write_text("<html><body><p>About</p></body></html>")

    # Run the function
    results = get_parsed_documents(str(tmp_path))

    # Check that both files are parsed
    filenames = [entry["filename"] for entry in results]
    assert "index.html" in filenames
    assert "about.html" in filenames

    # Check that soup objects are correct
    for entry in results:
        assert isinstance(entry["soup"], BeautifulSoup)
        # Optionally, check content
        if entry["filename"] == "index.html":
            assert entry["soup"].h1.text == "Home"
        if entry["filename"] == "about.html":
            assert entry["soup"].p.text == "About"


def test_css_source_order_mixed():
    html = """
    <html>
      <head>
        <link rel="stylesheet" href="a.css">
        <style>body { color: red; }</style>
        <link rel="stylesheet" href="b.css">
      </head>
      <body></body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    sources = get_css_source_order(soup)
    assert sources == [
        {"type": "external", "href": "a.css"},
        {"type": "internal", "content": "body { color: red; }"},
        {"type": "external", "href": "b.css"},
    ]


def test_css_source_order_only_external():
    html = """
    <html>
      <head>
        <link rel="stylesheet" href="main.css">
      </head>
      <body></body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    sources = get_css_source_order(soup)
    assert sources == [
        {"type": "external", "href": "main.css"},
    ]


def test_css_source_order_only_internal():
    html = """
    <html>
      <head>
        <style>h1 { color: blue; }</style>
      </head>
      <body></body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    sources = get_css_source_order(soup)
    assert sources == [
        {"type": "internal", "content": "h1 { color: blue; }"},
    ]


def test_css_source_order_empty_head():
    html = """
    <html>
      <head></head>
      <body></body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    sources = get_css_source_order(soup)
    assert sources == []


def test_get_css_source_order_mixed():
    html = """
    <html>
      <head>
        <link rel="stylesheet" href="a.css">
        <style>body { color: red; }</style>
        <link rel="stylesheet" href="b.css">
      </head>
      <body></body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    sources = get_css_source_order(soup)
    assert sources == [
        {"type": "external", "href": "a.css"},
        {"type": "internal", "content": "body { color: red; }"},
        {"type": "external", "href": "b.css"},
    ]


def test_parse_internal_style_tag():
    css = "body { color: blue; }"
    rules = parse_internal_style_tag(css)
    assert isinstance(rules, list)
    assert any(rule.type == "qualified-rule" for rule in rules)


def test_get_or_parse_external_stylesheet(tmp_path):
    css_content = b"body { background: #fff; }"
    css_file = tmp_path / "test.css"
    css_file.write_bytes(css_content)
    cache = {}
    # First call parses and caches
    rules = get_or_parse_external_stylesheet(
        str(css_file.name), str(tmp_path) + os.sep, cache
    )
    assert isinstance(rules, list)
    assert css_file.name in cache
    # Second call uses cache
    rules2 = get_or_parse_external_stylesheet(
        str(css_file.name), str(tmp_path) + os.sep, cache
    )
    assert rules2 is rules


def test_append_style_data():
    css_source = {"index.html": []}
    sheet = {"type": "internal"}
    href = "style_tag"
    parsed = ["dummy_rule"]
    append_style_data("index.html", sheet, href, parsed, css_source)
    assert len(css_source["index.html"]) == 1
    entry = css_source["index.html"][0]
    assert entry["source_type"] == "internal"
    assert entry["css_name"] == "style_tag"
    assert entry["stylesheet"] == ["dummy_rule"]


def test_load_css_files(tmp_path):
    # Create a fake HTML file and CSS file
    html_content = """
    <html>
      <head>
        <link rel="stylesheet" href="test.css">
        <style>body { color: green; }</style>
      </head>
      <body></body>
    </html>
    """
    css_content = b"body { background: #fff; }"
    html_file = tmp_path / "index.html"
    css_file = tmp_path / "test.css"
    html_file.write_text(html_content)
    css_file.write_bytes(css_content)

    # Simulate parsed HTML docs
    soup = BeautifulSoup(html_content, "html.parser")
    html_docs = [{"filename": "index.html", "soup": soup}]
    css_files = load_css_files(html_docs, str(tmp_path) + os.sep)

    # Should contain both external and internal sources
    assert any(
        item["css_name"] == "test.css"
        for css_dict in css_files
        for html_file, items in css_dict.items()
        for item in items
    )

    assert any(
        item["css_name"] == "style_tag"
        for css_dict in css_files
        for html_file, items in css_dict.items()
        for item in items
    )


def test_apply_browser_defaults_basic_elements():
    """Test basic element styling with default values."""
    html = "<html><body><p>Test paragraph</p><div>Test div</div></body></html>"
    soup = BeautifulSoup(html, "html.parser")

    styles = apply_browser_defaults(soup)

    # Should have styles for p and div elements
    p_element = soup.find("p")
    div_element = soup.find("div")

    assert p_element in styles
    assert div_element in styles

    # Check default values
    assert styles[p_element]["color"]["value"] == DEFAULT_GLOBAL_COLOR
    assert styles[p_element]["color"]["source"] == "default"
    assert styles[p_element]["font-size"]["value"] == f"{ROOT_FONT_SIZE}px"
    assert styles[p_element]["background-color"]["source"] == "default"


def test_apply_browser_defaults_links():
    """Test that links get special color treatment."""
    html = '<html><body><a href="test.html">Test link</a></body></html>'
    soup = BeautifulSoup(html, "html.parser")

    styles = apply_browser_defaults(soup)
    link_element = soup.find("a")

    assert link_element in styles
    assert styles[link_element]["color"]["value"] == DEFAULT_LINK_COLOR
    assert (
        styles[link_element]["visited-color"]["value"] == DEFAULT_LINK_VISITED
    )


def test_apply_browser_defaults_bold_elements():
    """Test that bold elements get font-weight: bold."""
    html = "<html><body><strong>Bold</strong><b>Also bold</b></body></html>"
    soup = BeautifulSoup(html, "html.parser")

    styles = apply_browser_defaults(soup)
    strong_element = soup.find("strong")
    b_element = soup.find("b")

    assert strong_element in styles
    assert b_element in styles
    assert styles[strong_element]["font-weight"]["value"] == "bold"
    assert styles[b_element]["font-weight"]["value"] == "bold"


def test_apply_browser_defaults_headings():
    """Test that headings get correct font sizes and bold weight."""
    html = "<html><body><h1>Heading 1</h1><h3>Heading 3</h3><h6>Heading 6"
    html += "</h6></body></html>"
    soup = BeautifulSoup(html, "html.parser")

    styles = apply_browser_defaults(soup)
    h1_element = soup.find("h1")
    h3_element = soup.find("h3")
    h6_element = soup.find("h6")

    # All headings should be present
    assert h1_element in styles
    assert h3_element in styles
    assert h6_element in styles

    # Check font sizes from HEADING_FONT_SIZES
    assert (
        styles[h1_element]["font-size"]["value"]
        == f"{HEADING_FONT_SIZES['h1']}px"
    )
    assert (
        styles[h3_element]["font-size"]["value"]
        == f"{HEADING_FONT_SIZES['h3']}px"
    )
    assert (
        styles[h6_element]["font-size"]["value"]
        == f"{HEADING_FONT_SIZES['h6']}px"
    )

    # All headings should be bold
    assert styles[h1_element]["font-weight"]["value"] == "bold"
    assert styles[h3_element]["font-weight"]["value"] == "bold"
    assert styles[h6_element]["font-weight"]["value"] == "bold"


def test_apply_browser_defaults_empty_elements():
    """Test that empty elements are excluded."""
    html = '<html><body><p>Text</p><br><img src="test.jpg"><hr></body></html>'
    soup = BeautifulSoup(html, "html.parser")

    styles = apply_browser_defaults(soup)

    # Only p should have styles (has text content)
    p_element = soup.find("p")
    br_element = soup.find("br")
    img_element = soup.find("img")
    hr_element = soup.find("hr")

    assert p_element in styles
    assert br_element not in styles  # empty element
    assert img_element not in styles  # empty element
    assert hr_element not in styles  # empty element


def test_apply_browser_defaults_no_text_content():
    """Test that elements without text content are excluded."""
    html = "<html><body><div></div><p>   </p><span>Text</span></body></html>"
    soup = BeautifulSoup(html, "html.parser")

    styles = apply_browser_defaults(soup)

    div_element = soup.find("div")
    p_element = soup.find("p")
    span_element = soup.find("span")

    # Only span should have styles (has actual text)
    assert div_element not in styles  # no text
    assert p_element not in styles  # only whitespace
    assert span_element in styles  # has text


def test_apply_browser_defaults_mixed_content():
    """Test complex HTML with multiple element types."""
    html = """
    <html>
        <body>
            <h1>Main Title</h1>
            <p>A paragraph with <strong>bold text</strong> and a
               <a href="link.html">link</a>.</p>
            <div>
                <h2>Subtitle</h2>
                <ul>
                    <li>List item</li>
                </ul>
            </div>
            <br>
            <img src="test.jpg" alt="Test">
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")

    styles = apply_browser_defaults(soup)

    h1 = soup.find("h1")
    h2 = soup.find("h2")
    p = soup.find("p")
    strong = soup.find("strong")
    a = soup.find("a")
    div = soup.find("div")
    li = soup.find("li")
    br = soup.find("br")
    img = soup.find("img")

    # Elements with text should have styles
    assert h1 in styles
    assert h2 in styles
    assert p in styles
    assert strong in styles
    assert a in styles
    assert li in styles

    # div should have styles because it contains elements with text
    assert div in styles

    # Empty elements should not have styles
    assert br not in styles
    assert img not in styles

    # Check specific styling
    assert styles[h1]["font-size"]["value"] == f"{HEADING_FONT_SIZES['h1']}px"
    assert styles[h1]["font-weight"]["value"] == "bold"
    assert styles[h2]["font-size"]["value"] == f"{HEADING_FONT_SIZES['h2']}px"
    assert styles[h2]["font-weight"]["value"] == "bold"
    assert styles[strong]["font-weight"]["value"] == "bold"
    assert styles[a]["color"]["value"] == DEFAULT_LINK_COLOR
    assert styles[a]["visited-color"]["value"] == DEFAULT_LINK_VISITED


def test_apply_browser_defaults_return_type():
    """Test that function returns correct data structure."""
    html = "<html><body><p>Test</p></body></html>"
    soup = BeautifulSoup(html, "html.parser")

    styles = apply_browser_defaults(soup)

    # Should return a dictionary
    assert isinstance(styles, dict)

    # Keys should be BeautifulSoup elements
    for element in styles.keys():
        assert hasattr(element, "name")  # BeautifulSoup Tag property

    # Values should be style dictionaries
    for style_dict in styles.values():
        assert isinstance(style_dict, dict)
        assert "color" in style_dict
        assert "background-color" in style_dict
        assert "font-size" in style_dict


class TestIsSelectorSupportedByBs4:
    """Test suite for is_selector_supported_by_bs4 function."""

    def test_empty_selector(self):
        """Test that empty selectors return False."""
        assert is_selector_supported_by_bs4("") is False
        assert is_selector_supported_by_bs4("   ") is False

    def test_basic_supported_selectors(self):
        """Test basic selectors that BS4 supports."""
        supported_selectors = [
            "p",
            "div",
            ".class",
            "#id",
            "div.class",
            "p#id",
            "div p",
            "div > p",
            "h1 + p",
            "*",
            "[href]",
            "[class='value']",
            "p, div, span",
            "ul li",
            "nav ul li a",
        ]

        for selector in supported_selectors:
            assert (
                is_selector_supported_by_bs4(selector) is True
            ), f"Should support: {selector}"

    def test_pseudo_elements_not_supported(self):
        """Test that pseudo-elements return False."""
        pseudo_elements = [
            "p::before",
            "div::after",
            "h1::first-line",
            "p::first-letter",
            "input::placeholder",
            ".class::before",
        ]

        for selector in pseudo_elements:
            assert (
                is_selector_supported_by_bs4(selector) is False
            ), f"Should not support: {selector}"

    def test_pseudo_classes_not_supported(self):
        """Test that most pseudo-classes return False."""
        pseudo_classes = [
            "a:hover",
            "input:focus",
            "button:active",
            "a:visited",
            "a:link",
            "p:first-child",
            "div:last-child",
            "li:nth-child(2)",
            "span:nth-of-type(odd)",
            "input:checked",
            "input:disabled",
            "input:enabled",
            "div:empty",
            "a:target",
            ":root",
            "p:first-letter",
            "div:first-line",
        ]

        for selector in pseudo_classes:
            assert (
                is_selector_supported_by_bs4(selector) is False
            ), f"Should not support: {selector}"

    def test_not_pseudo_class_supported(self):
        """Test that :not() pseudo-class is supported (BS4 exception)."""
        supported_not_selectors = [
            "div:not(.class)",
            "p:not(#id)",
            ":not(span)",
        ]

        for selector in supported_not_selectors:
            assert (
                is_selector_supported_by_bs4(selector) is True
            ), f"Should support: {selector}"

    def test_general_sibling_combinator_not_supported(self):
        """Test that general sibling combinator (~) is not supported."""
        sibling_selectors = ["h1 ~ p", "div ~ span", ".class ~ #id"]

        for selector in sibling_selectors:
            assert (
                is_selector_supported_by_bs4(selector) is False
            ), f"Should not support: {selector}"

    def test_case_insensitive_attributes_not_supported(self):
        """Test that case-insensitive attribute selectors are not supported."""
        case_insensitive_selectors = [
            "[class='value' i]",
            "[href='link' i]",
            "[data-attr='test' i]",
        ]

        for selector in case_insensitive_selectors:
            assert (
                is_selector_supported_by_bs4(selector) is False
            ), f"Should not support: {selector}"

    def test_complex_supported_selectors(self):
        """Test complex but supported selectors."""
        complex_supported = [
            "nav > ul > li > a",
            "div.container p.text",
            "#main .sidebar ul li",
            "table tr:not(.hidden)",
            "[data-role='button']",
            "input[type='text']",
        ]

        for selector in complex_supported:
            assert (
                is_selector_supported_by_bs4(selector) is True
            ), f"Should support: {selector}"

    def test_mixed_unsupported_features(self):
        """Test selectors with multiple unsupported features."""
        mixed_unsupported = [
            "a:hover::before",
            "div:first-child ~ p",
            "input:focus:checked",
            ".class:hover [attr='val' i]",
        ]

        for selector in mixed_unsupported:
            assert (
                is_selector_supported_by_bs4(selector) is False
            ), f"Should not support: {selector}"

    def test_whitespace_handling(self):
        """Test that whitespace is properly handled."""
        assert is_selector_supported_by_bs4("  p  ") is True
        assert is_selector_supported_by_bs4("  a:hover  ") is False
        assert is_selector_supported_by_bs4("\t.class\n") is True


def test_find_matching_elements_empty_selector():
    """Test that empty/whitespace selectors return empty list."""
    html = "<html><body><p>Test</p><div>Content</div></body></html>"
    soup = BeautifulSoup(html, "html.parser")

    # Test empty string
    result = find_matching_elements(soup, "")
    assert result == []

    # Test whitespace only
    result = find_matching_elements(soup, "   ")
    assert result == []


def test_find_matching_elements_whitespace_trimming():
    """Test that leading/trailing whitespace is handled for supported
    selectors."""
    html = "<html><body><p>Test paragraph</p><div class='content'>Div</div>"
    html += "</body></html>"
    soup = BeautifulSoup(html, "html.parser")

    # Test with leading/trailing spaces
    result = find_matching_elements(soup, "  p  ")
    assert len(result) == 1
    assert result[0].name == "p"

    # Test with tabs and newlines
    result = find_matching_elements(soup, "\t.content\n")
    assert len(result) == 1
    assert result[0].get("class") == ["content"]


def test_find_matching_elements_unsupported_selector():
    """Test that unsupported selectors return empty list with warning."""
    html = "<html><body><a href='#'>Link</a><p>Paragraph</p></body></html>"
    soup = BeautifulSoup(html, "html.parser")

    # Test pseudo-class selector (should be caught)
    result = find_matching_elements(soup, "a:hover")
    assert result == []

    # Test pseudo-element selector
    result = find_matching_elements(soup, "p::before")
    assert result == []


def test_find_matching_elements_exception_handling(monkeypatch):
    """Test that exceptions from soup.select() are handled gracefully."""
    html = "<html><body><p>Test</p></body></html>"
    soup = BeautifulSoup(html, "html.parser")

    # Mock soup.select to raise an exception
    def mock_select(selector):
        raise ValueError("Simulated parsing error")

    monkeypatch.setattr(soup, "select", mock_select)

    # Should return empty list and not crash
    result = find_matching_elements(soup, "p")
    assert result == []


def test_find_matching_elements_successful_matching():
    """Test successful selector matching for various supported selectors."""
    html = """
    <html>
        <body>
            <div id="main" class="container">
                <p class="text">Paragraph 1</p>
                <p>Paragraph 2</p>
                <span class="text">Span text</span>
            </div>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")

    # Test element selector
    result = find_matching_elements(soup, "p")
    assert len(result) == 2
    assert all(elem.name == "p" for elem in result)

    # Test class selector
    result = find_matching_elements(soup, ".text")
    assert len(result) == 2

    # Test ID selector
    result = find_matching_elements(soup, "#main")
    assert len(result) == 1
    assert result[0].get("id") == "main"

    # Test descendant selector
    result = find_matching_elements(soup, "div p")
    assert len(result) == 2
    assert all(elem.name == "p" for elem in result)


# Test apply_rule_to_element function
def test_apply_rule_to_element_element_not_in_computed_styles():
    """Test that function returns early if element not in computed_styles."""
    html = "<html><body><p>Test</p></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    p_element = soup.find("p")

    computed_styles = {}  # Empty - element not present
    rule = {
        "selector": "p",
        "declarations": {"color": "red", "font-size": "18px"},
    }

    apply_rule_to_element(p_element, rule, computed_styles)

    # Should remain empty since element wasn't in computed_styles
    assert computed_styles == {}


def test_apply_rule_to_element_new_properties():
    """Test applying rule with new properties that don't exist on element."""
    html = "<html><body><p>Test</p></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    p_element = soup.find("p")

    computed_styles = {
        p_element: {"color": "black"}  # Element exists with basic style
    }
    rule = {
        "selector": "p",
        "declarations": {"font-size": "18px", "font-weight": "bold"},
    }

    apply_rule_to_element(p_element, rule, computed_styles)

    # Should add new properties
    assert "font-size" in computed_styles[p_element]
    assert "font-weight" in computed_styles[p_element]
    assert computed_styles[p_element]["font-size"]["value"] == "18.0px"
    assert computed_styles[p_element]["font-weight"]["value"] == "bold"


def test_apply_rule_to_element_filters_irrelevant_properties():
    """Test that non-contrast-relevant properties are filtered out."""
    html = "<html><body><p>Test</p></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    p_element = soup.find("p")

    computed_styles = {p_element: {"color": "black"}}
    rule = {
        "selector": "p",
        "declarations": {
            "color": "red",  # Should be applied (relevant)
            "margin": "10px",  # Should be filtered out
            "position": "absolute",  # Should be filtered out
            "font-size": "16px",  # Should be applied (relevant)
        },
    }

    apply_rule_to_element(p_element, rule, computed_styles)

    # Only contrast-relevant properties should be applied
    assert "color" in computed_styles[p_element]
    assert "font-size" in computed_styles[p_element]
    assert "margin" not in computed_styles[p_element]
    assert "position" not in computed_styles[p_element]


def test_apply_rule_to_element_higher_specificity_wins():
    """Test that higher specificity rules override lower specificity."""
    html = "<html><body><p class='text'>Test</p></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    p_element = soup.find("p")

    # Start with element selector (low specificity)
    computed_styles = {
        p_element: {
            "color": {
                "value": "black",
                "specificity": (0, 0, 0, 1),  # Element selector
            }
        }
    }

    # Apply class selector rule (higher specificity)
    rule = {"selector": ".text", "declarations": {"color": "red"}}

    apply_rule_to_element(p_element, rule, computed_styles)

    # Higher specificity should win
    assert computed_styles[p_element]["color"]["value"] == "red"
    assert computed_styles[p_element]["color"]["specificity"] == "010"


def test_apply_rule_to_element_lower_specificity_loses():
    """Test that lower specificity rules don't override higher specificity."""
    html = "<html><body><p class='text'>Test</p></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    p_element = soup.find("p")

    # Start with class selector (higher specificity)
    computed_styles = {
        p_element: {
            "color": {
                "value": "blue",
                "specificity": (0, 0, 1, 0),  # Class selector
            }
        }
    }

    # Try to apply element selector rule (lower specificity)
    rule = {"selector": "p", "declarations": {"color": "red"}}

    apply_rule_to_element(p_element, rule, computed_styles)

    # Lower specificity should NOT override
    assert computed_styles[p_element]["color"]["value"] == "blue"
    assert computed_styles[p_element]["color"]["specificity"] == (0, 0, 1, 0)


def test_apply_rule_to_element_same_specificity_later_wins():
    """Test that with same specificity, later rule wins (source order)."""
    html = "<html><body><p>Test</p></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    p_element = soup.find("p")

    # Start with element selector
    computed_styles = {
        p_element: {
            "color": {
                "value": "black",
                "specificity": "001",  # Element selector
            }
        }
    }

    # Apply another element selector rule (same specificity)
    rule = {"selector": "p", "declarations": {"color": "red"}}

    apply_rule_to_element(p_element, rule, computed_styles)

    # Later rule should win with same specificity
    assert computed_styles[p_element]["color"]["value"] == "red"
    assert computed_styles[p_element]["color"]["specificity"] == "001"


def test_apply_rule_to_element_overrides_default_styles():
    """Test that any CSS rule overrides default browser styles."""
    html = "<html><body><p>Test</p></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    p_element = soup.find("p")

    # Start with default style (no specificity stored)
    computed_styles = {p_element: {"color": "#000000"}}  # Default style format

    rule = {"selector": "p", "declarations": {"color": "red"}}

    apply_rule_to_element(p_element, rule, computed_styles)

    # CSS rule should override default
    assert computed_styles[p_element]["color"]["value"] == "red"
    assert "specificity" in computed_styles[p_element]["color"]


def test_apply_rule_to_element_multiple_properties():
    """Test applying rule with multiple contrast-relevant properties."""
    html = "<html><body><p>Test</p></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    p_element = soup.find("p")

    computed_styles = {p_element: {"color": "black"}}
    rule = {
        "selector": "p",
        "declarations": {
            "color": "red",
            "background-color": "yellow",
            "font-size": "18px",
            "font-weight": "bold",
            "opacity": "0.8",
        },
    }

    apply_rule_to_element(p_element, rule, computed_styles)

    # All properties should be applied
    for prop in [
        "color",
        "background-color",
        "font-size",
        "font-weight",
        "opacity",
    ]:
        assert prop in computed_styles[p_element]
        assert "value" in computed_styles[p_element][prop]
        assert "specificity" in computed_styles[p_element][prop]


def test_apply_rule_to_element_empty_declarations():
    """Test applying rule with empty declarations."""
    html = "<html><body><p>Test</p></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    p_element = soup.find("p")

    original_styles = {"color": "black"}
    computed_styles = {p_element: original_styles.copy()}

    rule = {"selector": "p", "declarations": {}}  # Empty declarations

    apply_rule_to_element(p_element, rule, computed_styles)

    # Styles should remain unchanged
    assert computed_styles[p_element] == original_styles


def test_convert_font_size_to_pixels_already_pixels():
    """Test that pixel values are returned unchanged."""
    html = "<html><body><p>Test</p></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    p_element = soup.find("p")
    computed_styles = {}

    result = convert_font_size_to_pixels("16px", p_element, computed_styles)
    assert result == "16.0px"

    result = convert_font_size_to_pixels("24px", p_element, computed_styles)
    assert result == "24.0px"


def test_convert_font_size_to_pixels_em_units():
    """Test em unit conversion using parent font size."""
    html = "<html><body><div><p>Test</p></div></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    div_element = soup.find("div")
    p_element = soup.find("p")

    # Set up parent with 20px font size
    computed_styles = {div_element: {"font-size": {"value": "20px"}}}

    result = convert_font_size_to_pixels("1.5em", p_element, computed_styles)
    assert result == "30.0px"  # 20px * 1.5


def test_convert_font_size_to_pixels_percentage():
    """Test percentage unit conversion using parent font size."""
    html = "<html><body><div><p>Test</p></div></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    div_element = soup.find("div")
    p_element = soup.find("p")

    # Set up parent with 16px font size
    computed_styles = {div_element: {"font-size": {"value": "16px"}}}

    result = convert_font_size_to_pixels("120%", p_element, computed_styles)
    assert result == "19.2px"  # 16px * 1.2


def test_convert_font_size_to_pixels_rem_units():
    """Test rem unit conversion using root font size."""
    html = "<html><body><div><p>Test</p></div></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    p_element = soup.find("p")
    computed_styles = {}

    result = convert_font_size_to_pixels("1.5rem", p_element, computed_styles)
    assert result == "24.0px"  # 16px * 1.5 (ROOT_FONT_SIZE)


def test_convert_font_size_to_pixels_no_parent():
    """Test em units when no parent font size is found."""
    html = "<html><body><p>Test</p></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    p_element = soup.find("p")
    computed_styles = {}

    result = convert_font_size_to_pixels("2em", p_element, computed_styles)
    assert result == "32.0px"  # 16px * 2 (fallback to root size)


def test_convert_font_size_to_pixels_keyword_values():
    """Test CSS keyword font size values."""
    html = "<html><body><p>Test</p></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    p_element = soup.find("p")
    computed_styles = {}

    result = convert_font_size_to_pixels("large", p_element, computed_styles)
    assert result == "18.0px"  # Based on CSS keyword mapping

    result = convert_font_size_to_pixels("small", p_element, computed_styles)
    assert result == "13.0px"


def test_convert_font_size_to_pixels_heading_element():
    """Test that heading elements are passed correctly to compute_font_size."""
    html = "<html><body><h1>Test</h1></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    h1_element = soup.find("h1")
    computed_styles = {}

    # Test that element name is used (compute_font_size handles heading logic)
    result = convert_font_size_to_pixels("1em", h1_element, computed_styles)
    # Result depends on your font_tools.compute_font_size implementation
    # This tests that the function is called with correct element_name
    assert result.endswith("px")


def test_convert_font_size_to_pixels_error_handling():
    """Test error handling for invalid font size values."""
    html = "<html><body><p>Test</p></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    p_element = soup.find("p")
    computed_styles = {}

    # Test invalid value that would cause split_value_unit to fail
    result = convert_font_size_to_pixels("invalid", p_element, computed_styles)
    assert result == "16.0px"  # Fallback behavior

    # Test empty string
    result = convert_font_size_to_pixels("", p_element, computed_styles)
    assert result == "16.0px"  # Fallback behavior


def test_convert_font_size_to_pixels_whitespace_handling():
    """Test that whitespace is properly stripped."""
    html = "<html><body><p>Test</p></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    p_element = soup.find("p")
    computed_styles = {}

    result = convert_font_size_to_pixels(
        "  16px  ", p_element, computed_styles
    )
    assert result == "16.0px"

    result = convert_font_size_to_pixels("\t2em\n", p_element, computed_styles)
    assert result == "32.0px"


def test_get_parent_font_size_direct_parent():
    """Test finding font size from direct parent."""
    html = "<html><body><div><p>Test</p></div></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    div_element = soup.find("div")
    p_element = soup.find("p")

    computed_styles = {div_element: {"font-size": {"value": "20px"}}}

    result = get_parent_font_size(p_element, computed_styles)
    assert result == 20.0


def test_get_parent_font_size_grandparent():
    """Test finding font size from grandparent when parent has no font-size."""
    html = (
        "<html><body><div><section><p>Test</p></section></div></body></html>"
    )
    soup = BeautifulSoup(html, "html.parser")
    div_element = soup.find("div")
    section_element = soup.find("section")
    p_element = soup.find("p")

    computed_styles = {
        div_element: {"font-size": {"value": "18px"}},
        section_element: {"color": {"value": "red"}},  # No font-size
    }

    result = get_parent_font_size(p_element, computed_styles)
    assert result == 18.0


def test_get_parent_font_size_no_parent_in_computed_styles():
    """Test fallback to root font size when no parent has computed styles."""
    html = "<html><body><div><p>Test</p></div></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    p_element = soup.find("p")

    computed_styles = {}  # No parents in computed_styles

    result = get_parent_font_size(p_element, computed_styles)
    assert result == 16.0  # ROOT_FONT_SIZE


def test_get_parent_font_size_parent_no_font_size():
    """Test fallback when parent exists but has no font-size property."""
    html = "<html><body><div><p>Test</p></div></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    div_element = soup.find("div")
    p_element = soup.find("p")

    computed_styles = {
        div_element: {
            "color": {"value": "red"},  # No font-size property
            "background": {"value": "blue"},
        }
    }

    result = get_parent_font_size(p_element, computed_styles)
    assert result == 16.0  # Fallback to root


def test_get_parent_font_size_none_element():
    """Test handling of None element."""
    computed_styles = {}

    result = get_parent_font_size(None, computed_styles)
    assert result == 16.0  # Fallback to root


def test_get_parent_font_size_decimal_values():
    """Test handling of decimal pixel values."""
    html = "<html><body><div><p>Test</p></div></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    div_element = soup.find("div")
    p_element = soup.find("p")

    computed_styles = {div_element: {"font-size": {"value": "18.5px"}}}

    result = get_parent_font_size(p_element, computed_styles)
    assert result == 18.5


def test_apply_css_inheritance_basic_color_inheritance():
    """Test basic color inheritance from parent to child."""
    html = "<html><body><div><p>Test</p></div></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    div_element = soup.find("div")
    p_element = soup.find("p")

    computed_styles = {
        div_element: {
            "color": {
                "value": "red",
                "specificity": "010",
                "source": "rule",
                "selector": ".parent",
            }
        },
        p_element: {
            "font-size": {"value": "16px", "specificity": "001"}
            # No color property - should inherit
        },
    }

    apply_css_inheritance(computed_styles)

    # Child should inherit color from parent
    assert "color" in computed_styles[p_element]
    assert computed_styles[p_element]["color"]["value"] == "red"
    # assert computed_styles[p_element]["color"]["source"] == "inheritance"
    assert computed_styles[p_element]["color"]["inherited_from"] == div_element


def test_apply_css_inheritance_font_size_inheritance():
    """Test font-size inheritance from parent to child."""
    html = "<html><body><div><span>Test</span></div></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    div_element = soup.find("div")
    span_element = soup.find("span")

    computed_styles = {
        div_element: {
            "font-size": {
                "value": "20px",
                "specificity": "010",
                "source": "rule",
                "selector": "#parent",
            }
        },
        span_element: {
            "color": {"value": "blue", "specificity": "001"}
            # No font-size - should inherit
        },
    }

    apply_css_inheritance(computed_styles)

    # Child should inherit font-size from parent
    assert "font-size" in computed_styles[span_element]
    assert computed_styles[span_element]["font-size"]["value"] == "20px"
    # assert computed_styles[span_element]["font-size"]["inherited"]


def test_apply_css_inheritance_parent_higher_specificity_wins():
    """
    Test that inheritance doesn't override explicit child values regardless
    of specificity.
    """
    html = "<html><body><div><p>Test</p></div></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    div_element = soup.find("div")
    p_element = soup.find("p")

    computed_styles = {
        div_element: {
            "color": {
                "value": "red",
                "specificity": "100",  # ID selector
                "source": "rule",
                "selector": "#parent",
            }
        },
        p_element: {
            "color": {
                "value": "blue",
                "specificity": "001",  # Element selector
                "source": "rule",
                "selector": "p",
            }
        },
    }

    apply_css_inheritance(computed_styles)

    # Since p_element has explicitly applied color, no inheritance occurs
    assert computed_styles[p_element]["color"]["value"] == "blue"
    assert computed_styles[p_element]["color"]["specificity"] == "001"
    assert computed_styles[p_element]["color"]["source"] == "rule"


def test_apply_css_inheritance_multiple_inheritable_properties():
    """Test inheritance of multiple properties (color, font-size,
    font-weight)."""
    html = "<html><body><div><span>Test</span></div></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    div_element = soup.find("div")
    span_element = soup.find("span")

    computed_styles = {
        div_element: {
            "color": {
                "value": "red",
                "specificity": "010",
                "source": "rule",
            },  # ← Add
            "font-size": {
                "value": "18px",
                "specificity": "010",
                "source": "rule",
            },  # ← Add
            "font-weight": {
                "value": "bold",
                "specificity": "010",
                "source": "rule",
            },  # ← Add
            "background-color": {"value": "yellow", "specificity": "010"},
        },
        span_element: {
            # Add default source for properties that should exist
            "color": {
                "value": "#000000",
                "specificity": "000",
                "source": "default",
            },  # ← Add
            "font-size": {
                "value": "16px",
                "specificity": "000",
                "source": "default",
            },  # ← Add
            "font-weight": {
                "value": "normal",
                "specificity": "000",
                "source": "default",
            },  # ← Add
        },
    }

    apply_css_inheritance(computed_styles)

    # Should inherit inheritable properties
    assert computed_styles[span_element]["color"]["value"] == "red"
    assert computed_styles[span_element]["font-size"]["value"] == "18px"
    assert computed_styles[span_element]["font-weight"]["value"] == "bold"

    # Should NOT inherit non-inheritable property
    assert "background-color" not in computed_styles[span_element]


def test_apply_css_inheritance_nested_inheritance():
    """Test inheritance through multiple levels (grandparent -> parent ->
    child)."""
    html = (
        "<html><body><div><section><p>Test</p></section></div></body></html>"
    )
    soup = BeautifulSoup(html, "html.parser")
    div_element = soup.find("div")
    section_element = soup.find("section")
    p_element = soup.find("p")

    computed_styles = {
        div_element: {
            "color": {
                "value": "red",
                "specificity": "010",
                "source": "rule",  # ← ADD
            }
        },
        section_element: {
            "font-size": {
                "value": "20px",
                "specificity": "010",
                "source": "rule",  # ← ADD
            },
            # Add default color so it can inherit
            "color": {
                "value": "#000000",
                "specificity": "000",
                "source": "default",  # ← ADD
            },
        },
        p_element: {
            # Add defaults so inheritance can work
            "color": {
                "value": "#000000",
                "specificity": "000",
                "source": "default",  # ← ADD
            },
            "font-size": {
                "value": "16px",
                "specificity": "000",
                "source": "default",  # ← ADD
            },
        },
    }

    apply_css_inheritance(computed_styles)

    # Section should inherit color from div
    assert computed_styles[section_element]["color"]["value"] == "red"
    assert computed_styles[section_element]["color"]["source"] == "inheritance"
    # P should inherit color from section (which got it from div)
    assert computed_styles[p_element]["color"]["value"] == "red"
    assert computed_styles[p_element]["color"]["source"] == "inheritance"

    # P should inherit font-size directly from section
    assert computed_styles[p_element]["font-size"]["value"] == "20px"
    assert computed_styles[p_element]["font-size"]["source"] == "inheritance"


def test_apply_css_inheritance_no_parent_in_computed_styles():
    """Test elements whose parents are not in computed_styles (no text
    content)."""
    html = "<html><body><div><p>Test</p></div></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    p_element = soup.find("p")

    # Div parent not in computed_styles (maybe it has no text)
    computed_styles = {
        p_element: {"font-size": {"value": "16px", "specificity": "001"}}
    }

    apply_css_inheritance(computed_styles)

    # Should remain unchanged (no parent to inherit from)
    assert len(computed_styles[p_element]) == 1
    assert computed_styles[p_element]["font-size"]["value"] == "16px"


def test_apply_css_inheritance_parent_no_inheritable_properties():
    """Test inheritance when parent has no inheritable properties."""
    html = "<html><body><div><p>Test</p></div></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    div_element = soup.find("div")
    p_element = soup.find("p")

    computed_styles = {
        div_element: {
            "background-color": {"value": "yellow", "specificity": "010"},
            "display": {"value": "block", "specificity": "010"}
            # No inheritable properties
        },
        p_element: {"font-size": {"value": "16px", "specificity": "001"}},
    }

    apply_css_inheritance(computed_styles)

    # Child should remain unchanged (nothing to inherit)
    assert len(computed_styles[p_element]) == 1
    assert computed_styles[p_element]["font-size"]["value"] == "16px"


def test_apply_css_inheritance_default_style_gets_inherited():
    """Test that default styles get overridden by inheritance."""
    html = "<html><body><div><p>Test</p></div></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    div_element = soup.find("div")
    p_element = soup.find("p")

    computed_styles = {
        div_element: {
            "color": {
                "value": "red",
                "specificity": "010",
                "source": "rule",  # Explicit CSS rule
                "selector": ".parent",
                "css_file": "styles.css",
                "css_source_type": "external",
            }
        },
        p_element: {
            "color": {
                "value": "black",
                "specificity": "000",
                "source": "default",
            }
        },
    }

    apply_css_inheritance(computed_styles)

    # Inherited value should override default
    assert computed_styles[p_element]["color"]["value"] == "red"
    assert (
        computed_styles[p_element]["color"]["source"] == "inheritance"
    )  # UPDATED
    assert computed_styles[p_element]["color"]["inherited_from"] == div_element


def test_apply_css_inheritance_tuple_specificity_conversion():
    """Test that tuple specificity values are converted to strings for
    comparison."""
    html = "<html><body><div><p>Test</p></div></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    div_element = soup.find("div")
    p_element = soup.find("p")

    computed_styles = {
        div_element: {
            "color": {
                "value": "red",
                "specificity": (0, 1, 0),
                "source": "rule",
            }
        },
        p_element: {
            # No color property - should inherit from parent
            "font-size": {"value": "16px", "specificity": "001"}
        },
    }

    apply_css_inheritance(computed_styles)

    # Child should inherit parent's color (no explicit color on child)
    assert computed_styles[p_element]["color"]["value"] == "red"
    assert computed_styles[p_element]["color"]["source"] == "inheritance"

    # Verify tuple specificity is preserved in inheritance
    assert computed_styles[p_element]["color"]["specificity"] == (0, 1, 0)


def test_apply_css_inheritance_empty_computed_styles():
    """Test function handles empty computed_styles gracefully."""
    computed_styles = {}

    # Should not crash
    apply_css_inheritance(computed_styles)

    assert computed_styles == {}


def test_apply_css_inheritance_preserves_source_metadata():
    """Test that inherited properties preserve source metadata from parent."""
    html = "<html><body><div><p>Test</p></div></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    div_element = soup.find("div")
    p_element = soup.find("p")

    computed_styles = {
        div_element: {
            "color": {
                "value": "red",
                "specificity": "010",
                "source": "rule",
                "selector": ".parent-class",
                "css_file": "styles.css",
                "css_source_type": "external",
            }
        },
        p_element: {"font-size": {"value": "16px", "specificity": "001"}},
    }

    apply_css_inheritance(computed_styles)

    # Should preserve parent's source metadata
    inherited_color = computed_styles[p_element]["color"]
    assert inherited_color["value"] == "red"
    assert inherited_color["source"] == "inheritance"
    assert inherited_color["selector"] == ".parent-class"  # From parent
    assert inherited_color["css_file"] == "styles.css"  # From parent
    assert inherited_color["css_source_type"] == "external"  # From parent
    assert inherited_color["source"] == "inheritance"
    assert inherited_color["inherited_from"] == div_element


def test_find_ancestor_background_nested_hierarchy():
    """
    Test finding background from nearest ancestor in nested hierarchy.

    Structure: body > header > nav > ul
    - body has background via CSS
    - header has background via CSS
    - nav has no background
    - ul has no background
    Expected: ul should inherit header's background (nearest ancestor)
    """
    html = (
        "<html><body><header><nav><ul><li>Item</li></ul></nav>"
        "</header></body></html>"
    )
    soup = BeautifulSoup(html, "html.parser")
    body_element = soup.find("body")
    header_element = soup.find("header")
    nav_element = soup.find("nav")
    ul_element = soup.find("ul")

    # Setup computed styles - only body and header have backgrounds
    computed_styles = {
        body_element: {
            "background-color": {
                "value": "lightgray",
                "specificity": "001",
                "source": "rule",
                "selector": "body",
            }
        },
        header_element: {
            "background-color": {
                "value": "darkblue",
                "specificity": "001",
                "source": "rule",
                "selector": "header",
            }
        },
        nav_element: {
            # No background properties - should be skipped
            "color": {"value": "black", "specificity": "001"}
        },
        ul_element: {
            # No background properties - this is what we're testing
            "color": {"value": "black", "specificity": "001"}
        },
    }

    # Test that ul finds header's background (nearest ancestor)
    result = find_ancestor_background(ul_element, computed_styles)

    # Should find header's background, not body's
    assert result["value"] == "darkblue"
    assert result["source_element"] == header_element

    # Verify it didn't pick up body's background
    assert result["value"] != "lightgray"
    assert result["source_element"] != body_element


def test_find_ancestor_background_skips_elements_without_styles():
    """
    Test that find_ancestor_background skips ancestors not in
    computed_styles.
    """
    html = (
        "<html><body><header><nav><ul><li>Item</li></ul></nav>"
        "</header></body></html>"
    )
    soup = BeautifulSoup(html, "html.parser")
    body_element = soup.find("body")
    ul_element = soup.find("ul")

    # Only body has computed styles (header, nav not included)
    computed_styles = {
        body_element: {
            "background-color": {
                "value": "lightgray",
                "specificity": "001",
                "source": "rule",  # ADD THIS
                "selector": "body",
            }
        },
        ul_element: {"color": {"value": "black", "specificity": "001"}}
        # header and nav intentionally not in computed_styles
    }

    result = find_ancestor_background(ul_element, computed_styles)

    # Should skip header/nav and find body's background
    assert result["value"] == "lightgray"
    assert result["source_element"] == body_element


def test_find_ancestor_background_checks_background_property():
    """
    Test that find_ancestor_background finds 'background' property
    (not just background-color).
    """
    html = "<html><body><div><p>Text</p></div></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    div_element = soup.find("div")
    p_element = soup.find("p")

    computed_styles = {
        div_element: {
            "background": {
                "value": "url(image.jpg) red",
                "specificity": "010",
                "source": "rule",  # ADD THIS
                "selector": "div",
            }
        },
        p_element: {"color": {"value": "black", "specificity": "001"}},
    }

    result = find_ancestor_background(p_element, computed_styles)

    assert result["value"] is None
    assert result["original_background"] == "url(image.jpg) red"
    assert result["source_element"] == div_element


def test_find_ancestor_background_no_ancestor_found():
    """
    Test fallback to default background when no ancestor has background.
    """
    html = "<html><body><div><p>Text</p></div></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    div_element = soup.find("div")
    p_element = soup.find("p")

    computed_styles = {
        div_element: {
            # No background properties
            "color": {"value": "black", "specificity": "001"}
        },
        p_element: {"color": {"value": "black", "specificity": "001"}},
    }

    result = find_ancestor_background(p_element, computed_styles)

    # Should return default background
    assert result["value"] == DEFAULT_GLOBAL_BACKGROUND  # "#ffffff"
    assert result["source_element"] is None


def test_find_ancestor_background_prefers_background_color():
    """
    Test that function checks both background-color and background
    properties.
    """
    html = "<html><body><div><p>Text</p></div></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    div_element = soup.find("div")
    p_element = soup.find("p")

    computed_styles = {
        div_element: {
            "background-color": {
                "value": "blue",
                "specificity": "010",
                "source": "rule",  # ADD THIS
                "selector": "div",
            },
            "background": {
                "value": "url(image.jpg) red",
                "specificity": "005",
                "source": "rule",  # ADD THIS
                "selector": "div",
            },
        },
        p_element: {"color": {"value": "black", "specificity": "001"}},
    }

    result = find_ancestor_background(p_element, computed_styles)

    # Should find background-color (checked first in loop)
    assert result["value"] == "blue"
    assert result["source_element"] == div_element


def test_find_ancestor_background_element_with_no_parent():
    """
    Test handling of element with no parent (edge case).
    """
    # Create isolated element
    html = "<p>Isolated</p>"
    soup = BeautifulSoup(html, "html.parser")
    p_element = soup.find("p")

    computed_styles = {
        p_element: {"color": {"value": "black", "specificity": "001"}}
    }

    result = find_ancestor_background(p_element, computed_styles)

    # Should return default since no parent exists
    assert result["value"] == DEFAULT_GLOBAL_BACKGROUND
    assert result["source_element"] is None


# apply_visual_background_inheritance tests
def test_apply_visual_background_inheritance_basic_inheritance():
    """Test basic visual background inheritance from parent to child."""
    html = "<html><body><div><p>Text</p></div></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    div_element = soup.find("div")
    p_element = soup.find("p")

    computed_styles = {
        div_element: {
            "background-color": {
                "value": "blue",
                "specificity": "010",
                "source": "rule",
                "selector": "div",
                "css_file": "main.css",
                "css_source_type": "external",
            },
            "color": {"value": "black", "specificity": "001"},
        },
        p_element: {
            "color": {"value": "black", "specificity": "001"},
            # ← ADD default background so inheritance can work:
            "background-color": {
                "value": "#ffffff",
                "specificity": "000",
                "source": "default",
            },
        },
    }
    apply_visual_background_inheritance(computed_styles)

    # P should get visual background from div
    assert "background-color" in computed_styles[p_element]
    bg_prop = computed_styles[p_element]["background-color"]
    assert bg_prop["value"] == "blue"
    assert bg_prop["source"] == "visual_inheritance"
    assert bg_prop["inherited_from"] == div_element


def test_apply_visual_background_inheritance_has_explicit_background():
    """
    Test that elements with explicit backgrounds don't get inheritance.
    """
    html = "<html><body><div><p>Text</p></div></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    div_element = soup.find("div")
    p_element = soup.find("p")

    computed_styles = {
        div_element: {
            "background-color": {"value": "blue", "specificity": "010"}
        },
        p_element: {
            "background-color": {
                "value": "red",  # Explicit background
                "specificity": "001",
            },
            "color": {"value": "black", "specificity": "001"},
        },
    }

    apply_visual_background_inheritance(computed_styles)

    # P should keep its explicit background, not inherit
    assert computed_styles[p_element]["background-color"]["value"] == "red"
    assert (
        "visual_inheritance"
        not in computed_styles[p_element]["background-color"]
    )


def test_apply_visual_background_inheritance_image_blocks_contrast():
    """
    Test that background images mark elements as contrast-indeterminate.
    """
    html = "<html><body><div><p>Text</p></div></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    div_element = soup.find("div")
    p_element = soup.find("p")

    computed_styles = {
        div_element: {
            "background-color": {"value": "blue", "specificity": "010"}
        },
        # Note below how an image blocks the color
        p_element: {
            "background": {
                "value": "url(image.jpg) yellow",
                "specificity": "001",
            },
            "color": {"value": "black", "specificity": "001"},
        },
    }

    apply_visual_background_inheritance(computed_styles)

    # P should be marked as contrast-indeterminate
    bg_prop = computed_styles[p_element]["background-color"]
    assert bg_prop["value"] is None
    assert bg_prop["contrast_analysis"] == "indeterminate"
    assert bg_prop["reason"] == "background_image_blocks_color_analysis"
    assert bg_prop["original_background"] == "url(image.jpg) yellow"
    assert not bg_prop["visual_inheritance"]


def test_apply_visual_background_inheritance_children_inherit_indeterminate():
    """
    Test that children of image-background elements also become indeterminate.
    """
    html = "<html><body><div><p><span>Text</span></p></div></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    div_element = soup.find("div")
    p_element = soup.find("p")
    span_element = soup.find("span")

    computed_styles = {
        div_element: {
            "background": {
                "value": "url(photo.jpg)",  # No fallback color
                "specificity": "010",
                "source": "rule",
            }
        },
        p_element: {
            "color": {"value": "black", "specificity": "001"},
            "background-color": {  # ← ADD
                "value": "#ffffff",
                "specificity": "000",
                "source": "default",
            },
        },
        span_element: {
            "color": {"value": "black", "specificity": "001"},
            "background-color": {  # ← ADD
                "value": "#ffffff",
                "specificity": "000",
                "source": "default",
            },
        },
    }

    apply_visual_background_inheritance(computed_styles)

    # div should be indeterminate (has image)
    div_bg = computed_styles[div_element]["background-color"]
    assert div_bg["contrast_analysis"] == "indeterminate"
    assert div_bg["reason"] == "background_image_blocks_color_analysis"

    # Both p and span should be indeterminate due to ancestor image
    for element in [p_element, span_element]:
        bg_prop = computed_styles[element]["background-color"]
        assert bg_prop["value"] is None
        assert bg_prop["contrast_analysis"] == "indeterminate"
        assert bg_prop["reason"] == "ancestor_has_background_image"


def test_apply_visual_background_inheritance_nested_hierarchy():
    """Test inheritance in nested hierarchy with realistic initial state."""
    html = (
        "<html><body><header><nav><ul><li>Item</li></ul></nav>"
        "</header></body></html>"
    )
    soup = BeautifulSoup(html, "html.parser")
    body_element = soup.find("body")
    header_element = soup.find("header")
    li_element = soup.find("li")

    computed_styles = {
        body_element: {
            "background-color": {
                "value": "lightgray",
                "specificity": "001",
                "source": "rule",
                "selector": "body",
            }
        },
        header_element: {
            "background-color": {
                "value": "darkblue",
                "specificity": "001",
                "source": "rule",
                "selector": "header",
            }
        },
        # ONLY li has text, so only li would be in computed_styles
        li_element: {
            "color": {"value": "black", "specificity": "001"},
            "background-color": {  # ← Added by apply_browser_defaults()
                "value": "#ffffff",
                "specificity": "000",
                "source": "default",
            },
        },
    }

    apply_visual_background_inheritance(computed_styles)

    # assert li inherits from header (nearest ancestor with CSS background)
    assert "background-color" in computed_styles[li_element]
    bg_prop = computed_styles[li_element]["background-color"]
    assert bg_prop["value"] == "darkblue"
    assert bg_prop["source"] == "visual_inheritance"
    assert bg_prop["inherited_from"] == header_element


def test_apply_visual_background_inheritance_no_ancestor_background():
    """Test fallback to default when no ancestor has background."""
    html = "<html><body><div><p>Text</p></div></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    div_element = soup.find("div")
    p_element = soup.find("p")

    computed_styles = {
        div_element: {
            "color": {"value": "black", "specificity": "001"},
            "background-color": {  # ← ADD
                "value": "#ffffff",
                "specificity": "000",
                "source": "default",
            },
        },
        p_element: {
            "color": {"value": "black", "specificity": "001"},
            "background-color": {  # ← ADD
                "value": "#ffffff",
                "specificity": "000",
                "source": "default",
            },
        },
    }

    apply_visual_background_inheritance(computed_styles)

    # P should get default background
    assert "background-color" in computed_styles[p_element]
    bg_prop = computed_styles[p_element]["background-color"]
    assert bg_prop["value"] == DEFAULT_GLOBAL_BACKGROUND
    assert bg_prop["source"] == "default"  # UPDATED
    assert "inherited_from" not in bg_prop


def test_apply_visual_background_inheritance_multiple_elements():
    """Test inheritance for multiple elements without backgrounds."""
    html = (
        "<html><body><div><p>Para 1</p><span>Span</span><p>Para 2</p>"
        "</div></body></html>"
    )
    soup = BeautifulSoup(html, "html.parser")
    div_element = soup.find("div")
    p_elements = soup.find_all("p")
    span_element = soup.find("span")

    computed_styles = {
        div_element: {
            "background-color": {
                "value": "yellow",
                "specificity": "010",
                "source": "rule",
            }
        },
        p_elements[0]: {
            "color": {"value": "black", "specificity": "001"},
            "background-color": {  # ← ADD
                "value": "#ffffff",
                "specificity": "000",
                "source": "default",
            },
        },
        span_element: {
            "color": {"value": "black", "specificity": "001"},
            "background-color": {  # ← ADD
                "value": "#ffffff",
                "specificity": "000",
                "source": "default",
            },
        },
        p_elements[1]: {
            "color": {"value": "black", "specificity": "001"},
            "background-color": {  # ← ADD
                "value": "#ffffff",
                "specificity": "000",
                "source": "default",
            },
        },
    }
    apply_visual_background_inheritance(computed_styles)

    # All child elements should inherit div's background
    for element in [p_elements[0], span_element, p_elements[1]]:
        assert "background-color" in computed_styles[element]
        bg_prop = computed_styles[element]["background-color"]
        assert bg_prop["value"] == "yellow"
        assert bg_prop["source"] == "visual_inheritance"  # UPDATED
        assert bg_prop["inherited_from"] == div_element


def test_apply_visual_background_inheritance_mixed_explicit_inherited():
    """Test mix of elements with explicit and inherited backgrounds."""
    html = (
        "<html><body><div><p>Para</p><span>Span</span><em>Em</em>"
        "</div></body></html>"
    )
    soup = BeautifulSoup(html, "html.parser")
    div_element = soup.find("div")
    p_element = soup.find("p")
    span_element = soup.find("span")
    em_element = soup.find("em")

    computed_styles = {
        div_element: {
            "background-color": {
                "value": "green",
                "specificity": "010",
                "source": "rule",
            }
        },
        p_element: {
            "background-color": {
                "value": "red",
                "specificity": "001",
                "source": "rule",  # ← ADD (so it won't be overridden)
            }
        },
        span_element: {
            "color": {"value": "black", "specificity": "001"},
            "background-color": {  # ← ADD
                "value": "#ffffff",
                "specificity": "000",
                "source": "default",
            },
        },
        em_element: {
            "background": {
                "value": "blue",
                "specificity": "001",
            }
            # em has "background", not "background-color" no change needed
        },
    }

    apply_visual_background_inheritance(computed_styles)

    # P should keep explicit background
    assert computed_styles[p_element]["background-color"]["value"] == "red"
    assert (
        "source" not in computed_styles[p_element]["background-color"]
        or computed_styles[p_element]["background-color"]["source"]
        != "visual_inheritance"
    )

    # Span should inherit from div
    assert (
        computed_styles[span_element]["background-color"]["value"] == "green"
    )
    assert (
        computed_styles[span_element]["background-color"]["source"]
        == "visual_inheritance"
    )

    # Em should keep explicit background shorthand
    assert computed_styles[em_element]["background"]["value"] == "blue"
    assert "background-color" not in computed_styles[em_element]


def test_apply_visual_background_inheritance_empty_computed_styles():
    """
    Test that function handles empty computed_styles gracefully.
    """
    computed_styles = {}

    # Should not crash
    apply_visual_background_inheritance(computed_styles)

    assert computed_styles == {}


def test_apply_visual_background_inheritance_element_not_in_dom():
    """
    Test handling of elements that might not have proper DOM structure.
    """
    # Create isolated elements
    html1 = "<p>Isolated para</p>"
    html2 = "<div>Isolated div</div>"
    soup1 = BeautifulSoup(html1, "html.parser")
    soup2 = BeautifulSoup(html2, "html.parser")
    p_element = soup1.find("p")
    div_element = soup2.find("div")

    computed_styles = {
        p_element: {
            "color": {
                "value": "black",
                "specificity": "001",
                "source": "rule",
            },
            "background-color": {  # ← ADD
                "value": "#ffffff",
                "specificity": "000",
                "source": "default",
            },
        },
        div_element: {
            "background-color": {
                "value": "purple",
                "specificity": "001",
                "source": "rule",
            }
        },
    }
    apply_visual_background_inheritance(computed_styles)

    # P should get default background (no ancestors)
    assert (
        computed_styles[p_element]["background-color"]["value"]
        == DEFAULT_GLOBAL_BACKGROUND
    )
    assert (
        computed_styles[p_element]["background-color"]["source"] == "default"
    )  # FIXED

    # Div already has background, should remain unchanged
    assert (
        computed_styles[div_element]["background-color"]["value"] == "purple"
    )
    assert (
        "visual_inheritance"
        not in computed_styles[div_element]["background-color"]
    )


def test_apply_visual_background_inheritance_skips_ancestors_not_in_styles():
    """Test that function skips ancestors not in computed_styles."""
    html = (
        "<html><body><article><section><div><p>Text</p></div></section>"
        "</article></body></html>"
    )
    soup = BeautifulSoup(html, "html.parser")
    body_element = soup.find("body")
    p_element = soup.find("p")

    computed_styles = {
        body_element: {
            "background-color": {
                "value": "orange",
                "specificity": "001",
                "source": "rule",
            }
        },
        p_element: {
            "color": {
                "value": "black",
                "specificity": "001",
                "source": "rule",
            },
            "background-color": {  # ← ADD
                "value": "#ffffff",
                "specificity": "000",
                "source": "default",
            },
        },
    }

    apply_visual_background_inheritance(computed_styles)

    # P should inherit from body (skipping intermediate elements)
    assert computed_styles[p_element]["background-color"]["value"] == "orange"
    assert (
        computed_styles[p_element]["background-color"]["source"]
        == "visual_inheritance"
    )
    assert (
        computed_styles[p_element]["background-color"]["inherited_from"]
        == body_element
    )


def test_apply_visual_background_inheritance_both_background_properties():
    """
    Test that function correctly identifies existing backgrounds from both
    background-color and background properties.
    """
    html = "<html><body><div><p>Para</p><span>Span</span></div></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    div_element = soup.find("div")
    p_element = soup.find("p")
    span_element = soup.find("span")

    computed_styles = {
        div_element: {
            "background-color": {"value": "pink", "specificity": "010"}
        },
        p_element: {
            "background-color": {
                "value": "red",  # Has background-color
                "specificity": "001",
            }
        },
        span_element: {
            "background": {
                "value": "blue",  # Has background shorthand
                "specificity": "001",
            }
        },
    }

    apply_visual_background_inheritance(computed_styles)

    # Both p and span already have backgrounds, should not inherit
    assert computed_styles[p_element]["background-color"]["value"] == "red"
    assert (
        "visual_inheritance"
        not in computed_styles[p_element]["background-color"]
    )

    assert computed_styles[span_element]["background"]["value"] == "blue"
    assert "background-color" not in computed_styles[span_element]


def test_apply_visual_background_inheritance_specificity_zero():
    """
    Test that inherited background gets low specificity.
    """
    html = "<html><body><div><p>Text</p></div></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    div_element = soup.find("div")
    p_element = soup.find("p")

    computed_styles = {
        div_element: {
            "background-color": {
                "value": "teal",
                "specificity": "100",
                "source": "rule",
            }
        },
        p_element: {
            "color": {
                "value": "black",
                "specificity": "001",
                "source": "rule",
            },
            "background-color": {  # ← ADD
                "value": "#ffffff",
                "specificity": "000",
                "source": "default",
            },
        },
    }

    apply_visual_background_inheritance(computed_styles)

    # Inherited background should have low specificity
    bg_prop = computed_styles[p_element]["background-color"]
    assert bg_prop["specificity"] == "000"  # Low specificity for inheritance
    assert bg_prop["value"] == "teal"
    assert bg_prop["source"] == "visual_inheritance"
