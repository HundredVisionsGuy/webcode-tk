# tests/test_contrast_direct_text.py
"""Tests for direct text detection and property source extraction"""
from bs4 import BeautifulSoup

from webcode_tk.contrast_tools import extract_property_source
from webcode_tk.contrast_tools import get_direct_text


class TestGetDirectText:
    """Test get_direct_text function"""

    def test_element_with_direct_text(self):
        html = "<p>Hello world!</p>"
        soup = BeautifulSoup(html, "html.parser")
        p = soup.find("p")

        result = get_direct_text(p)
        assert result == "Hello world!"

    def test_element_with_no_direct_text(self):
        html = "<div><p>Hello</p></div>"
        soup = BeautifulSoup(html, "html.parser")
        div = soup.find("div")

        result = get_direct_text(div)
        assert result == ""

    def test_element_with_mixed_content(self):
        html = "<p>Hello <strong>world</strong>!</p>"
        soup = BeautifulSoup(html, "html.parser")
        p = soup.find("p")

        result = get_direct_text(p)

        # Should return concatenated direct text
        assert "Hello" in result or "!" in result

    def test_head_elements_return_empty(self):
        html = "<title>Page Title</title>"
        soup = BeautifulSoup(html, "html.parser")
        title = soup.find("title")

        result = get_direct_text(title)
        assert result == ""

    def test_whitespace_only_returns_empty(self):
        html = "<p>   \n\t   </p>"
        soup = BeautifulSoup(html, "html.parser")
        p = soup.find("p")

        result = get_direct_text(p)
        assert result == ""


class TestExtractPropertySource:
    """Test extract_property_source function"""

    def test_extract_css_rule_source(self):
        property_data = {
            "value": "#ff0000",
            "source": "rule",
            "css_file": "style.css",
            "selector": "h1",
        }

        result = extract_property_source(property_data)

        assert result["source_type"] == "css_rule"
        assert result["css_file"] == "style.css"
        assert result["selector"] == "h1"
        assert result["inherited_from"] is None

    def test_extract_browser_default_source(self):
        property_data = {"value": "#000000", "source": "default"}

        result = extract_property_source(property_data)

        assert result["source_type"] == "browser_default"
        assert result["css_file"] == "user_agent_stylesheet"
        assert result["selector"] == "default"

    def test_extract_inheritance_source(self):
        # Mock element for testing
        mock_element = type("MockElement", (), {"name": "div"})()

        property_data = {
            "value": "#000000",
            "source": "inheritance",
            "inherited_from": mock_element,
            "css_file": "style.css",
            "selector": "p",
        }

        result = extract_property_source(property_data)

        assert result["source_type"] == "inherited"
        assert result["inherited_from"] == "div"
        assert result["css_file"] == "style.css"

    def test_extract_visual_inheritance_source(self):
        mock_element = type("MockElement", (), {"name": "body"})()

        property_data = {
            "value": "#ffffff",
            "source": "visual_inheritance",
            "inherited_from": mock_element,
        }

        result = extract_property_source(property_data)

        assert result["source_type"] == "visual_inheritance"
        assert result["css_file"] == "visual_cascade"
        assert result["selector"] == "ancestor_background"
        assert result["inherited_from"] == "body"

    def test_extract_missing_property_source(self):
        result = extract_property_source(None)

        assert result["source_type"] == "missing"
        assert result["css_file"] is None
        assert result["selector"] is None
        assert result["inherited_from"] is None
