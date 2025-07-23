import os

from bs4 import BeautifulSoup

from webcode_tk.contrast_tools import append_style_data
from webcode_tk.contrast_tools import apply_browser_defaults
from webcode_tk.contrast_tools import DEFAULT_GLOBAL_BACKGROUND
from webcode_tk.contrast_tools import DEFAULT_GLOBAL_COLOR
from webcode_tk.contrast_tools import DEFAULT_LINK_COLOR
from webcode_tk.contrast_tools import DEFAULT_LINK_VISITED
from webcode_tk.contrast_tools import find_matching_elements
from webcode_tk.contrast_tools import get_css_source_order
from webcode_tk.contrast_tools import get_or_parse_external_stylesheet
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
    assert styles[p_element]["color"] == DEFAULT_GLOBAL_COLOR
    assert styles[p_element]["background-color"] == DEFAULT_GLOBAL_BACKGROUND
    assert styles[p_element]["font-size"] == f"{ROOT_FONT_SIZE}px"


def test_apply_browser_defaults_links():
    """Test that links get special color treatment."""
    html = '<html><body><a href="test.html">Test link</a></body></html>'
    soup = BeautifulSoup(html, "html.parser")

    styles = apply_browser_defaults(soup)
    link_element = soup.find("a")

    assert link_element in styles
    assert styles[link_element]["color"] == DEFAULT_LINK_COLOR
    assert styles[link_element]["visited-color"] == DEFAULT_LINK_VISITED


def test_apply_browser_defaults_bold_elements():
    """Test that bold elements get font-weight: bold."""
    html = "<html><body><strong>Bold</strong><b>Also bold</b></body></html>"
    soup = BeautifulSoup(html, "html.parser")

    styles = apply_browser_defaults(soup)
    strong_element = soup.find("strong")
    b_element = soup.find("b")

    assert strong_element in styles
    assert b_element in styles
    assert styles[strong_element]["font-weight"] == "bold"
    assert styles[b_element]["font-weight"] == "bold"


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
    assert styles[h1_element]["font-size"] == f"{HEADING_FONT_SIZES['h1']}px"
    assert styles[h3_element]["font-size"] == f"{HEADING_FONT_SIZES['h3']}px"
    assert styles[h6_element]["font-size"] == f"{HEADING_FONT_SIZES['h6']}px"

    # All headings should be bold
    assert styles[h1_element]["font-weight"] == "bold"
    assert styles[h3_element]["font-weight"] == "bold"
    assert styles[h6_element]["font-weight"] == "bold"


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
    assert styles[h1]["font-size"] == f"{HEADING_FONT_SIZES['h1']}px"
    assert styles[h1]["font-weight"] == "bold"
    assert styles[h2]["font-size"] == f"{HEADING_FONT_SIZES['h2']}px"
    assert styles[h2]["font-weight"] == "bold"
    assert styles[strong]["font-weight"] == "bold"
    assert styles[a]["color"] == DEFAULT_LINK_COLOR
    assert styles[a]["visited-color"] == DEFAULT_LINK_VISITED


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
