"""Tests for `colortools` package."""
import pytest

from webcode_tk import color_tools as color

# define some colors
indigo = "#4b0082"
aquamarine = "#7FFFD4"
white = "#ffffff"
favorite_test_color = "#336699"
hsl_string_1 = "hsl(355, 96%, 46%)"
hsl_string_1_as_rgb_str = "rgb(230, 5, 23)"
hsl_string_1_as_rgb = (230, 5, 23)
hsl_string_1_as_hex = "#E60517"
hsla_string_1 = "hsla(355, 96%, 46%, 1.0)"
hsla_string_1_as_rgba = "rgba(230, 5, 23, 1.0)"

favorite_test_color_contrast_report = {
    "Normal AA": "Pass",
    "Normal AAA": "Fail",
    "Large AA": "Pass",
    "Large AAA": "Pass",
    "Graphics UI components": "Pass",
}
all_pass_color_contrast_report = {
    "Normal AA": "Pass",
    "Normal AAA": "Pass",
    "Large AA": "Pass",
    "Large AAA": "Pass",
    "Graphics UI components": "Pass",
}
all_fail_color_contrast_report = {
    "Normal AA": "Fail",
    "Normal AAA": "Fail",
    "Large AA": "Fail",
    "Large AAA": "Fail",
    "Graphics UI components": "Fail",
}


@pytest.fixture
def indigo_rgb():
    indigo_rgb = color.hex_to_rgb(indigo)
    return indigo_rgb


@pytest.mark.parametrize(
    "input,output",
    [
        ("#336699", "#336699"),
        ("black", "#000000"),
        ("rgb(255,255,255)", "#ffffff"),
        ("hsl(0, 100%, 50%)", "#ff0000"),
    ],
)
def test_get_hex_for_various_values(input, output):
    expected = color.get_hex(input)
    assert expected == output


def test_get_hsl_from_string():
    results = color.get_hsl_from_string(hsl_string_1)
    expected = (355, 96, 46)
    assert results == expected


def test_hsl_to_rgb():
    results = color.hsl_to_rgb((355, 96, 46))
    expected = hsl_string_1_as_rgb
    assert results == expected


def test_hsl_to_rgb_240_100_50():
    results = color.hsl_to_rgb((240, 100, 50))
    expected = (0, 0, 255)
    assert results == expected


def test_hex_to_decimal_for_bc():
    bc_hex = "bc"
    expected = 188
    results = color.hex_to_decimal(bc_hex)
    assert expected == results


def test_hex_to_decimal_for_CB():
    cb_hex = "CB"
    expected = 203
    results = color.hex_to_decimal(cb_hex)
    assert expected == results


def test_extract_rgb_from_string_for_green():
    green = "rgb(0, 255, 0);"
    results = color.extract_rgb_from_string(green)
    expected = (0, 255, 0)
    assert results == expected


def test_rgb_to_hex_for_black():
    results = color.rgb_to_hex(0, 0, 0)
    expected = "#000000"
    assert results == expected


def test_rgb_to_hex_for_white():
    results = color.rgb_to_hex(255, 255, 255)
    expected = "#ffffff"
    assert results == expected


def test_rgb_to_hex_for_336699():
    results = color.rgb_to_hex(51, 102, 153)
    expected = "#336699"
    assert results == expected


def test_rgb_to_hex_for_string_336699():
    results = color.rgb_to_hex("rgb(51,102,153)")
    expected = "#336699"
    assert results == expected


def test_is_hex_for_no_hash():
    assert not color.is_hex("336699")


def test_is_hex_for_valid_hex():
    assert color.is_hex("#336699")


def test_is_hex_for_invalid_not_hex_digit():
    assert not color.is_hex("#3366lh")


def test_is_hex_for_alpha_channel():
    assert color.is_hex("#33aa0088")


def test_is_hex_for_3_codes():
    assert color.is_hex("#369")


def test_is_hex_for_invalid_number_digits():
    assert not color.is_hex("#4469")


def test_contrast_ratio_for_inverted_indigo_white(indigo_rgb):
    expected = 12.95
    results = color.contrast_ratio("#4B0082", "#ffffff")
    assert expected == results


def test_contrast_ratio_for_aquamarine_and_white():
    expected = 1.22
    results = color.contrast_ratio(aquamarine, white)
    assert expected == results


def test_passes_color_contrast_normal_aa_for_no_pass_aquamarine_white():
    expected = False
    results = color.passes_color_contrast("Normal AA", aquamarine, white)
    assert results == expected


def test_passes_normal_aa_for_pass_indigo_white():
    expected = True
    results = color.passes_color_contrast("Normal AA", indigo, white)
    assert results == expected


def test_passes_normal_aaa_for_no_pass_336699_white():
    expected = False
    results = color.passes_color_contrast(
        "Normal AAA", favorite_test_color, white
    )
    assert results == expected


def test_get_color_contrast_report_for_favorite_color():
    expected = favorite_test_color_contrast_report
    results = color.get_color_contrast_report(favorite_test_color, white)
    assert results == expected


def test_get_color_contrast_report_for_all_passing():
    expected = all_pass_color_contrast_report
    results = color.get_color_contrast_report(indigo, white)
    assert expected == results


def test_get_color_contrast_report_for_all_failing():
    expected = all_fail_color_contrast_report
    results = color.get_color_contrast_report(aquamarine, white)
    assert expected == results


def test_has_alpha_channel_for_hex_code_with_alpha():
    expected = True
    results = color.has_alpha_channel("#33669966")
    assert expected == results


def test_has_alpha_channel_for_hex_code_without_alpha():
    expected = False
    results = color.has_alpha_channel("#336699")
    assert expected == results


def test_has_alpha_channel_for_hsl_with_alpha():
    expected = True
    results = color.has_alpha_channel("hsl(120deg 75% 25% / 60%)")
    assert results == expected


def test_is_rgb_for_non_rgb():
    value = "hsla(0, 0, 0, 0)"
    results = color.is_rgb(value)
    expected = False
    assert results == expected


def test_is_rgb_for_rgb():
    value = "rgb(255, 0, 124)"
    results = color.is_rgb(value)
    expected = True
    assert results == expected


def test_is_rgb_for_rgba():
    value = "rgba(255, 0, 0, 0.2)"
    results = color.is_rgb(value)
    expected = True
    assert results == expected


def test_is_color_value_for_hex():
    assert color.is_color_value("#fff")


def test_is_color_value_for_hsla():
    assert color.is_color_value(hsla_string_1)


def test_is_color_value_for_rgb():
    assert color.is_color_value(hsl_string_1_as_rgb_str)


def test_is_color_value_for_rgba():
    assert color.is_color_value(hsla_string_1_as_rgba)


def test_is_color_value_for_non_color_fill():
    # test for some non-color values (associated with background prop)
    assert not color.is_color_value("fill")


def test_is_color_value_for_non_color_url():
    assert not color.is_color_value('url("images/BannerFlag.png")')


def test_get_color_type_for_hex():
    assert color.get_color_type("#336699") == "hex"


def test_get_color_type_for_hex_alpha():
    assert color.get_color_type("#33669988") == "hex_alpha"


def test_get_color_type_for_rbga():
    assert color.get_color_type("rgba(143, 193, 242, 0.22)") == "rgba"


def test_get_color_type_for_other_colors():
    assert color.get_color_type("rgb(143, 193, 242)") == "rgb"
    assert color.get_color_type("hsl(0, 100%, 50%)") == "hsl"
    assert color.get_color_type("hsla(100, 100%, 50%, 1)") == "hsla"


@pytest.mark.parametrize(
    "css_value,expected",
    [
        ("linear-gradient(to right, #ff7e5f, #feb47b)", True),
        ("radial-gradient(circle, #ff7e5f, #feb47b)", True),
        ("conic-gradient(from 0deg, red, yellow, green)", True),
        ("background-color: #ff7e5f;", False),
        ("border: 1px solid #000;", False),
    ],
)
def test_is_gradient_for_value(css_value, expected):
    results = color.is_gradient(css_value)
    assert results == expected


radial_gradient = (
    "radial-gradient(circle at 7.5% 24%, #d7f8f7 0%, #fab2ac 25.5%,"
)
radial_gradient += "#bee4d2 62.3%, rgb(237, 161, 193) 93.8%);"
four_mixed_gradient = ".gradient { background-image: linear-gradient( "
four_mixed_gradient += "to right, red, #f06d06, rgb(255, 255, 0), green);}"


@pytest.mark.parametrize(
    "color_code,output",
    [
        ("#336699", "#336699"),
        ("red", "#FF0000"),
        ("rgb(255, 255, 0)", "#ffff00"),
        ("hsl(120, 100%, 25%)", "#008000"),
    ],
)
def test_to_hex(color_code, output):
    results = color.to_hex(color_code)
    assert results == output


@pytest.mark.parametrize(
    "fg_color,bg_color,expected",
    [
        (
            radial_gradient,
            "#ffffff",
            [
                (1.12, "#d7f8f7", "#ffffff", "#ffffff"),
                (1.37, "#bee4d2", "#ffffff", "#ffffff"),
                (1.74, "#fab2ac", "#ffffff", "#ffffff"),
                (2.0, "rgb(237, 161, 193)", "#ffffff", "#ffffff"),
            ],
        ),
    ],
)
def test_get_color_contrast_with_gradients(fg_color, bg_color, expected):
    results = color.get_color_contrast_with_gradients(fg_color, bg_color)
    assert results == expected


def test_color_to_hsl_for_rgb_green():
    results = color.color_to_hsl("rgb(51, 151, 51)")
    expected = "hsl(120, 50%, 40%)"
    assert results == expected


def test_color_to_hsl_for_hex336699():
    results = color.color_to_hsl("#336699")
    expected = "hsl(210, 50%, 40%)"
    assert results == expected


def test_color_to_hsl_for_hex_gray():
    results = color.color_to_hsl("#efefef")
    expected = "hsl(0, 0%, 94%)"
    assert results == expected


def test_color_to_hsl_for_white():
    results = color.color_to_hsl("rgb(255, 255, 255)")
    expected = "hsl(0, 0%, 100%)"
    assert results == expected


def test_color_to_hsl_for_deepskyblue_rgb():
    results = color.color_to_hsl("rgb(0, 191, 255)")
    expected = "hsl(195, 100%, 50%)"
    assert results == expected


def test_blend_alpha_for_hsla():
    expected = "hsl(240, 100%, 60%)"
    actual = color.blend_alpha("#ffffff", "hsla(240, 100%, 50%, 0.8)")
    assert expected == actual


def test_blend_alpha_for_hexa():
    expected = "#c4d3e1"
    actual = color.blend_alpha("#ffffff", "#3366994a")
    assert actual == expected


def test_blend_alpha_for_rgba():
    expected = "rgb(185,208,216)"
    actual = color.blend_alpha(
        "rgb(255, 255, 255)", "rgba(102, 153, 170, 0.46)"
    )
    assert actual == expected


def test_get_rgb_for_standard_hex():
    expected = (51, 102, 153)
    actual = color.get_rgb("#336699")
    assert actual == expected


def test_get_rgb_for_hex_with_alpha():
    expected = (51, 102, 153)
    actual = color.get_rgb("#336699aa")
    assert actual == expected


def test_get_rgb_for_rgba():
    expected = (0, 170, 255)
    actual = color.get_rgb("rgba(0, 170, 255, 0.56)")
    assert actual == expected


def test_get_rgb_for_keyword():
    expected = (30, 144, 255)
    actual = color.get_rgb("DodgerBlue")
    assert actual == expected


def test_get_rgb_for_hsl_with_commas():
    expected = (31, 143, 255)
    actual = color.get_rgb("hsl(210, 100%, 56%)")
    assert actual == expected
