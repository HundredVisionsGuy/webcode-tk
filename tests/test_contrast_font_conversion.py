from bs4 import BeautifulSoup

from webcode_tk.contrast_tools import classify_font_unit
from webcode_tk.contrast_tools import convert_font_size_to_pixels
from webcode_tk.contrast_tools import get_parent_font_size


class TestConvertFontSizeToPixels:
    """Test convert_font_size_to_pixels function"""

    def test_convert_pixels_unchanged(self):
        html = "<p>Text</p>"
        soup = BeautifulSoup(html, "html.parser")
        p = soup.find("p")

        result = convert_font_size_to_pixels("16px", p, {})
        assert result == "16.0px"

    def test_convert_em_to_pixels(self):
        html = "<div><p>Text</p></div>"
        soup = BeautifulSoup(html, "html.parser")
        div = soup.find("div")
        p = soup.find("p")

        computed_styles = {div: {"font-size": {"value": "20px"}}}

        result = convert_font_size_to_pixels("1.5em", p, computed_styles)
        assert result == "30.0px"  # 1.5 * 20px = 30px

    def test_convert_percent_to_pixels(self):
        html = "<div><p>Text</p></div>"
        soup = BeautifulSoup(html, "html.parser")
        div = soup.find("div")
        p = soup.find("p")

        computed_styles = {div: {"font-size": {"value": "20px"}}}

        result = convert_font_size_to_pixels("150%", p, computed_styles)
        assert result == "30.0px"  # 150% of 20px = 30px

    def test_convert_rem_uses_root_size(self):
        html = "<div><p>Text</p></div>"
        soup = BeautifulSoup(html, "html.parser")
        p = soup.find("p")

        # rem should use root size (16px default), not parent
        result = convert_font_size_to_pixels("1.5rem", p, {})
        assert result == "24.0px"  # 1.5 * 16px = 24px

    def test_convert_with_decimal_values(self):
        html = "<div><p>Text</p></div>"
        soup = BeautifulSoup(html, "html.parser")
        div = soup.find("div")
        p = soup.find("p")

        computed_styles = {div: {"font-size": {"value": "18px"}}}

        result = convert_font_size_to_pixels("1.2em", p, computed_styles)
        assert result == "21.6px"  # 1.2 * 18px = 21.6px


class TestGetParentFontSize:
    """Test get_parent_font_size function"""

    def test_get_immediate_parent_font_size(self):
        html = "<div><p>Text</p></div>"
        soup = BeautifulSoup(html, "html.parser")
        div = soup.find("div")
        p = soup.find("p")

        computed_styles = {div: {"font-size": {"value": "20px"}}}

        result = get_parent_font_size(p, computed_styles)
        assert result == 20.0

    def test_get_ancestor_font_size(self):
        html = "<div><span><p>Text</p></span></div>"
        soup = BeautifulSoup(html, "html.parser")
        div = soup.find("div")
        p = soup.find("p")

        computed_styles = {
            div: {"font-size": {"value": "18px"}},
            # span has no font-size, should skip to div
        }

        result = get_parent_font_size(p, computed_styles)
        assert result == 18.0

    def test_get_default_font_size_no_parent(self):
        html = "<p>Text</p>"
        soup = BeautifulSoup(html, "html.parser")
        p = soup.find("p")

        computed_styles = {}

        result = get_parent_font_size(p, computed_styles)
        assert result == 16.0  # Default root font size

    def test_get_parent_font_size_none_element(self):
        result = get_parent_font_size(None, {})
        assert result == 16.0


class TestClassifyFontUnit:
    """Test classify_font_unit function"""

    def test_classify_absolute_units(self):
        assert classify_font_unit("16px") == "absolute"
        assert classify_font_unit("12pt") == "absolute"
        assert classify_font_unit("1in") == "absolute"

    def test_classify_relative_units(self):
        assert classify_font_unit("1.5em") == "relative"
        assert classify_font_unit("2rem") == "relative"
        assert classify_font_unit("120%") == "relative"

    def test_classify_keyword_units(self):
        assert classify_font_unit("larger") == "relative_keyword"
        assert classify_font_unit("smaller") == "relative_keyword"
        assert classify_font_unit("large") == "absolute_keyword"
        assert classify_font_unit("medium") == "absolute_keyword"

    def test_classify_unknown_units(self):
        assert classify_font_unit("invalid") == "unknown"
