from bs4 import BeautifulSoup

from webcode_tk.contrast_tools import DEFAULT_GLOBAL_BACKGROUND
from webcode_tk.contrast_tools import find_ancestor_background


class TestFindAncestorBackground:
    """Test find_ancestor_background function - edge cases"""

    def test_ancestor_with_determinable_background(self):
        html = "<div><p>Text</p></div>"
        soup = BeautifulSoup(html, "html.parser")
        div = soup.find("div")
        p = soup.find("p")

        computed_styles = {
            div: {
                "background-color": {
                    "value": "#ff0000",
                    "source": "rule",
                    "contrast_analysis": "determinable",
                }
            }
        }

        result = find_ancestor_background(p, computed_styles)
        assert result["value"] == "#ff0000"
        assert result["source_element"] == div
        assert result["contrast_analysis"] == "determinable"

    def test_ancestor_with_indeterminate_status(self):
        html = "<div><p>Text</p></div>"
        soup = BeautifulSoup(html, "html.parser")
        div = soup.find("div")
        p = soup.find("p")

        computed_styles = {
            div: {
                "background-color": {
                    "value": None,
                    "source": "rule",
                    "contrast_analysis": "indeterminate",
                    "reason": "background_image_blocks_color_analysis",
                    "original_background": "url('bg.jpg')",
                }
            }
        }

        result = find_ancestor_background(p, computed_styles)
        assert result["contrast_analysis"] == "indeterminate"
        assert result["source_element"] == div
        assert result["reason"] == "ancestor_has_background_image"

    def test_skip_visual_inheritance_ancestor(self):
        html = "<div><span><p>Text</p></span></div>"
        soup = BeautifulSoup(html, "html.parser")
        div = soup.find("div")
        span = soup.find("span")
        p = soup.find("p")

        computed_styles = {
            div: {"background-color": {"value": "#ff0000", "source": "rule"}},
            span: {
                "background-color": {
                    "value": "#ff0000",
                    "source": "visual_inheritance",  # Should be skipped
                }
            },
        }

        result = find_ancestor_background(p, computed_styles)
        # Should skip span and find div
        assert result["source_element"] == div
        assert result["value"] == "#ff0000"

    def test_no_ancestor_returns_default(self):
        html = "<p>Text</p>"
        soup = BeautifulSoup(html, "html.parser")
        p = soup.find("p")

        computed_styles = {}

        result = find_ancestor_background(p, computed_styles)
        assert result["value"] == DEFAULT_GLOBAL_BACKGROUND
        assert result["source_element"] is None
        assert result["contrast_analysis"] == "determinable"

    def test_ancestor_without_background_color_property(self):
        html = "<div><p>Text</p></div>"
        soup = BeautifulSoup(html, "html.parser")
        div = soup.find("div")
        p = soup.find("p")

        computed_styles = {
            div: {
                "color": {"value": "#000000", "source": "rule"}
                # No background-color property
            }
        }

        result = find_ancestor_background(p, computed_styles)
        # Should return default since div has no background-color
        assert result["value"] == DEFAULT_GLOBAL_BACKGROUND
        assert result["source_element"] is None

    def test_multiple_ancestors_finds_first_with_background(self):
        html = "<div><section><article><p>Text</p></article></section></div>"
        soup = BeautifulSoup(html, "html.parser")
        div = soup.find("div")
        section = soup.find("section")
        article = soup.find("article")
        p = soup.find("p")

        computed_styles = {
            div: {"background-color": {"value": "#ff0000", "source": "rule"}},
            section: {
                "color": {"value": "#000", "source": "rule"}
                # No background-color
            },
            article: {
                "background-color": {"value": "#00ff00", "source": "rule"}
            },
        }

        result = find_ancestor_background(p, computed_styles)
        # Should find article (closest ancestor with background)
        assert result["source_element"] == article
        assert result["value"] == "#00ff00"
