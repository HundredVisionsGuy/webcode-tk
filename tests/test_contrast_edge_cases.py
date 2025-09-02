# tests/test_contrast_edge_cases.py
"""Tests for edge cases and error handling"""
from bs4 import BeautifulSoup

from webcode_tk.contrast_tools import analyze_elements_for_contrast
from webcode_tk.contrast_tools import apply_browser_defaults
from webcode_tk.contrast_tools import classify_font_unit
from webcode_tk.contrast_tools import has_any_css_sources


class TestHasAnyCssSources:
    """Test has_any_css_sources function"""

    def test_external_css_detected(self):
        html = """
        <html>
        <head><link rel="stylesheet" href="style.css"></head>
        <body><h1>Test</h1></body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        assert has_any_css_sources(soup) is True

    def test_internal_css_detected(self):
        html = """
        <html>
        <head><style>h1 { color: red; }</style></head>
        <body><h1>Test</h1></body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        assert has_any_css_sources(soup) is True

    def test_empty_style_tag_not_detected(self):
        html = """
        <html>
        <head><style></style></head>
        <body><h1>Test</h1></body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        assert has_any_css_sources(soup) is False

    def test_no_head_element(self):
        html = "<html><body><h1>Test</h1></body></html>"
        soup = BeautifulSoup(html, "html.parser")
        assert has_any_css_sources(soup) is False

    def test_no_css_sources(self):
        html = """
        <html>
        <head><title>Test</title></head>
        <body><h1>Test</h1></body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        assert has_any_css_sources(soup) is False


class TestContrastEdgeCases:
    """Test edge cases in contrast analysis"""

    def test_empty_computed_styles(self):
        """Test analyze_elements_for_contrast with empty computed_styles"""
        results = analyze_elements_for_contrast({}, "test.html")
        assert results == []


class TestBrowserDefaults:
    """Test browser default application"""

    def test_heading_font_weight_defaults(self):
        """Test that headings get bold font-weight by default"""
        html = "<h1>Heading</h1><p>Paragraph</p>"
        soup = BeautifulSoup(html, "html.parser")

        defaults = apply_browser_defaults(soup)

        h1 = soup.find("h1")
        p = soup.find("p")

        assert defaults[h1]["font-weight"]["value"] == "bold"
        assert defaults[p]["font-weight"]["value"] == "normal"

    def test_link_color_defaults(self):
        """Test that links get special color defaults"""
        html = "<a href='#'>Link</a>"
        soup = BeautifulSoup(html, "html.parser")

        defaults = apply_browser_defaults(soup)

        a = soup.find("a")
        assert defaults[a]["color"]["value"] == "#0000EE"  # DEFAULT_LINK_COLOR

    def test_heading_font_size_defaults(self):
        """Test that headings get appropriate font sizes"""
        html = "<h1>H1</h1><h2>H2</h2><h6>H6</h6>"
        soup = BeautifulSoup(html, "html.parser")

        defaults = apply_browser_defaults(soup)

        h1 = soup.find("h1")
        h2 = soup.find("h2")
        h6 = soup.find("h6")

        h1_size = float(defaults[h1]["font-size"]["value"].replace("px", ""))
        h2_size = float(defaults[h2]["font-size"]["value"].replace("px", ""))
        h6_size = float(defaults[h6]["font-size"]["value"].replace("px", ""))

        # H1 should be larger than H2, which should be larger than H6
        assert h1_size > h2_size > h6_size


class TestClassifyFontUnit:
    """Test classify_font_unit function"""

    def test_classify_absolute_units(self):
        assert classify_font_unit("16px") == "absolute"
        assert classify_font_unit("12pt") == "absolute"
        assert classify_font_unit("1in") == "absolute"
        assert classify_font_unit("2cm") == "absolute"

    def test_classify_relative_units(self):
        assert classify_font_unit("1.5em") == "relative"
        assert classify_font_unit("2rem") == "relative"
        assert classify_font_unit("120%") == "relative"

    def test_classify_relative_keywords(self):
        assert classify_font_unit("larger") == "relative_keyword"
        assert classify_font_unit("smaller") == "relative_keyword"

    def test_classify_absolute_keywords(self):
        assert classify_font_unit("large") == "absolute_keyword"
        assert classify_font_unit("medium") == "absolute_keyword"
        assert classify_font_unit("small") == "absolute_keyword"
        assert classify_font_unit("x-large") == "absolute_keyword"

    def test_classify_unknown_units(self):
        assert classify_font_unit("invalid") == "unknown"
        assert classify_font_unit("") == "unknown"
