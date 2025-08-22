from webcode_tk.contrast_tools import contains_raster_image
from webcode_tk.contrast_tools import extract_contrast_color
from webcode_tk.contrast_tools import extract_gradient_contrast_color
from webcode_tk.contrast_tools import has_usable_background_color
from webcode_tk.contrast_tools import is_selector_supported_by_bs4


class TestContainsRasterImage:
    """Test contains_raster_image function"""

    def test_contains_raster_image_with_jpg(self):
        assert contains_raster_image("url('image.jpg')") is True

    def test_contains_raster_image_with_png(self):
        assert contains_raster_image("url(background.png)") is True

    def test_contains_raster_image_with_gif(self):
        assert contains_raster_image("url('/path/to/image.gif')") is True

    def test_contains_raster_image_with_webp(self):
        assert contains_raster_image("url(image.webp)") is True

    def test_contains_raster_image_with_svg(self):
        # SVG is not a raster image
        assert contains_raster_image("url('icon.svg')") is False

    def test_contains_raster_image_with_gradient(self):
        assert contains_raster_image("linear-gradient(red, blue)") is False

    def test_contains_raster_image_with_solid_color(self):
        assert contains_raster_image("#ff0000") is False

    def test_contains_raster_image_with_none(self):
        assert contains_raster_image(None) is False

    def test_contains_raster_image_case_insensitive(self):
        assert contains_raster_image("url('IMAGE.JPG')") is True


class TestExtractContrastColor:
    """Test extract_contrast_color function"""

    def test_extract_solid_color_hex(self):
        assert extract_contrast_color("#ff0000") == "#ff0000"

    def test_extract_solid_color_rgb(self):
        assert extract_contrast_color("rgb(255, 0, 0)") == "rgb(255, 0, 0)"

    def test_extract_solid_color_named(self):
        assert extract_contrast_color("red") == "red"

    def test_extract_color_with_raster_image(self):
        # Should return None when raster image blocks analysis
        assert extract_contrast_color("url('bg.jpg') red") is None

    def test_extract_color_from_gradient(self):
        result = extract_contrast_color("linear-gradient(red, blue)")
        assert result == "blue"  # Should return last color

    def test_extract_color_none_input(self):
        assert extract_contrast_color(None) is None


class TestExtractGradientContrastColor:
    """Test extract_gradient_contrast_color function"""

    def test_linear_gradient_two_colors(self):
        gradient = "linear-gradient(red, blue)"
        assert extract_gradient_contrast_color(gradient) == "blue"

    def test_linear_gradient_multiple_colors(self):
        gradient = "linear-gradient(red, green, blue, yellow)"
        assert extract_gradient_contrast_color(gradient) == "yellow"

    def test_radial_gradient(self):
        gradient = "radial-gradient(circle, red, blue)"
        assert extract_gradient_contrast_color(gradient) == "blue"

    def test_gradient_with_hex_colors(self):
        gradient = "linear-gradient(#ff0000, #0000ff)"
        assert extract_gradient_contrast_color(gradient) == "#0000ff"


class TestIsSelectorSupportedByBs4:
    """Test is_selector_supported_by_bs4 function"""

    def test_simple_element_selector(self):
        assert is_selector_supported_by_bs4("p") is True

    def test_class_selector(self):
        assert is_selector_supported_by_bs4(".myclass") is True

    def test_id_selector(self):
        assert is_selector_supported_by_bs4("#myid") is True

    def test_descendant_selector(self):
        assert is_selector_supported_by_bs4("div p") is True

    def test_child_selector(self):
        assert is_selector_supported_by_bs4("div > p") is True

    def test_pseudo_element_not_supported(self):
        assert is_selector_supported_by_bs4("p::before") is False

    def test_pseudo_class_hover_not_supported(self):
        assert is_selector_supported_by_bs4("a:hover") is False

    def test_pseudo_class_first_child_not_supported(self):
        assert is_selector_supported_by_bs4("p:first-child") is False

    def test_general_sibling_not_supported(self):
        assert is_selector_supported_by_bs4("h1 ~ p") is False

    def test_empty_selector(self):
        assert is_selector_supported_by_bs4("") is False


class TestHasUsableBackgroundColor:
    """Test has_usable_background_color function"""

    def test_has_usable_background_solid_color(self):
        bg_prop = {"value": "#ff0000"}
        assert has_usable_background_color(bg_prop) is True

    def test_has_usable_background_gradient(self):
        bg_prop = {"value": "linear-gradient(red, blue)"}
        assert has_usable_background_color(bg_prop) is True

    def test_has_usable_background_none_prop(self):
        assert has_usable_background_color(None) is False

    def test_has_usable_background_with_raster_image(self):
        bg_prop = {"value": "url('bg.jpg') red"}
        assert has_usable_background_color(bg_prop) is False
