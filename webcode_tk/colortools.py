"""A collection of functions for processing and converting CSS
color codes.

I created this on an airplane flight because coding is more fun
than watching streaming shows and movies. I was thinking about my
Web Design and programming classes, and I had been going over number
systems (binary, hexadecimal, octal, etc.), and I decided to write
some functions to convert various web color coding schemes (RGB to
Hex and vice versa), so I decided to play around with conversions.

Later, I wanted to know what the algorithm for determining the color
contrast ratio as set out in the
[WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/),
so I found the algorithm and wrote some tests to see if it worked or
not. The algorithm meant that I needed to break down some of the
functions even further.

One thing led to another, yada yada, then I realized that this could
be a useful tool in my web grading projects, and there you have it:
`color_tools`.
"""
import re

hex_map = {
    "0": 0,
    "1": 1,
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "a": 10,
    "b": 11,
    "c": 12,
    "d": 13,
    "e": 14,
    "f": 15,
}

contrast_ratio_map = {
    "Normal AA": 4.5,
    "Normal AAA": 7,
    "Large AA": 3,
    "Large AAA": 4.5,
    "Graphics UI components": 3,
}

rgb_all_forms_re = r"rgba\(.*?\)|rgb\(.*?\)"
hsl_all_forms_re = r"hsl\(.*?\)|hsla\(.*?\)"
hex_regex = r"(#\w{3}\s|#\w{6}\s|#\w{8}\s)"


def passes_color_contrast(level: str, hex1: str, hex2: str) -> bool:
    """Compares the two hex codes (1 & 2) to see if it passes color
    contrast ratio.

    Args:
        level: String of size and rating (ex. `Normal AAA`,
            `Large AA`, etc.)
        hex1: a hexadecimal color code in string format, which
            could be the text or background color.
        hex2: a hexadecimal color code in string format, which
            could be the text or background color.

    Returns:
        passes: whether the two color codes pass the contrast at the
            level specified.
    """
    ratio = contrast_ratio(hex1, hex2)
    min_ratio = contrast_ratio_map[level]
    passes = ratio >= min_ratio
    return passes


def get_color_contrast_report(hex1: str, hex2: str) -> dict:
    """creates a report on how the two hex colors rate on the color
    contrast chart

    This functions compares the two colors to see if they meet the
    Web Content Accessibility Guidelines (WCAG) for normal sized
    and large sized text.

    WCAG 2.0 level AA requires a contrast ratio of at least 4.5:1 for
    normal text and 3:1 for large text. WCAG 2.1 requires a contrast
    ratio of at least 3:1 for graphics and user interface components
    (such as form input borders). WCAG Level AAA requires a contrast
    ratio of at least 7:1 for normal text and 4.5:1 for large text.

    Large text is defined as 14 point (typically 18.66px) and bold or
    larger, or 18 point (typically 24px) or larger.

    from the [WebAIM Contrast Checker]
    (https://webaim.org/resources/contrastchecker/)

    Args:
        hex1 (str): a foreground or background color (doesn't matter
            which)
        hex2 (str): a foreground or background color (doesn't matter
            which)

    Returns:
        report: a map of normal, large, and graphics UI components
            with a result of Pass or Fail for AAA and AA ratings.
    """
    report = {}
    # check for gradients and apply to every color in the gradient
    # if "gradient" in hex1
    for key, item in contrast_ratio_map.items():
        contrast = contrast_ratio(hex1, hex2)
        passes = "Pass" if contrast >= item else "Fail"
        report[key] = passes
    return report


def rgb_to_hex(*args) -> str:
    """converts an RGB color to hexadecimal format

    This function can receive either an RGB string or a tuple of
    integers and will convert it to a hexadecimal.

    Returns:
        hex_code: a hexidecimal color (eg. #336699)
    """
    # are there three separate values or 1 string
    if len(args) == 3:
        r, g, b = args
    else:
        try:
            rgb = args[0]
            r, g, b = extract_rgb_from_string(rgb)
        except Exception:
            # throw an exception
            return "err"
    # Convert r, g, b to hexidecimal format
    r = hex(int(r))[2:]
    g = hex(int(g))[2:]
    b = hex(int(b))[2:]
    # prepend 0 if necessary
    if len(r) == 1:
        r = "0" + r
    if len(g) == 1:
        g = "0" + g
    if len(b) == 1:
        b = "0" + b
    hex_code = "#" + r + g + b
    return hex_code


def hex_to_rgb(hex_code: str) -> tuple:
    """converts a hexidecimal code into an rgb value.

    This function takes a hex format (e.g. `#336699`) and returns an
    RGB as a tuple of color channels (red, green, and blue). Each
    channel will be an integer between 0 and 255.

    Args:
        hex_code: a hexadecimal color code.

    Returns:
        rgb: a tuple of 3 integers each a value between 0 and 255 that
            represent the color channels: red, green, and blue
            (respectively).
    """
    hex_code = hex_code.lower()
    if "#" in hex_code[0]:
        hex_code = hex_code[1:]
    r = hex_code[:2]
    g = hex_code[2:4]
    b = hex_code[4:]

    r = hex_to_decimal(r)
    g = hex_to_decimal(g)
    b = hex_to_decimal(b)

    rgb = (r, g, b)
    return rgb


def get_hsl_from_string(hsl_string: str) -> tuple:
    """converts a CSS HSL() color code format as a string into a tuple
    of HSL values.

    HSL stands for Hue, Saturation, and Lightness. For more info, read
    the article from the Mozilla Developer Network: [HSL()]
    (https://developer.mozilla.org/en-US/docs/Web/CSS/color_value/hsl)

    Hue is the base color from the additive color wheel represented as
    a degree (0-360 degrees), where 0 degrees is the top of the wheel
    (red), and the values rotate clockwise from red (0 degrees)
    to green (120 degrees) to blue (240 degrees) and back to red.

    Saturation represents how much of the color is present as a
    percentage from 0% gray to 100% fully saturated color.

    Lightness represents the amount of black or white also a percentage
    from 0% (all black) to 50% (just the color) to 100% (all white).

    Args:
        hsl_string (str): an HSL color value as a string in the format
            of `hsl(0, 100%, 50%)`

    Returns:
        hsl: a tuple of 3 integers that represen the hsl format
    """
    numbers = re.findall("[0-9]+", hsl_string)
    for i in range(len(numbers)):
        numbers[i] = int(numbers[i])
    hsl = tuple(numbers)
    return hsl


def has_alpha_channel(code: str) -> bool:
    """returns a true if rgba, hsla, or 8 digit hex code

    This function can receive a color value as hexidecimal, hsl, hsla,
    rgb, or rgba and determine whether there is an alpha channel or
    not.

    Args:
        code: any form of hex, rgb or hsl with alpha channel or not.

    Returns:
        has_alpha: whether there is an alpha channel present or not.
    """
    has_alpha = False
    if "#" in code:
        if len(code) == 9:
            has_alpha = True
    if "hsla(" in code:
        has_alpha = True
    if "rgba(" in code:
        has_alpha = True
    return has_alpha


def hsl_to_rgb(hsl: tuple) -> tuple:
    """converts hsl to rgb format (as tuples of integers)

    This comes from [From HSL to RGB color conversion]
    (https://www.rapidtables.com/convert/color/hsl-to-rgb.html)

    Args:
        hsl (tuple): a tuple of integers that represent hue,
            saturation, and lightness

    Returns:
        rgb: a tuple of integers that represent the red, green,
            and blue channels.
    """
    hue, sat, light = hsl
    sat /= 100
    light /= 100
    c = (1 - abs(2 * light - 1)) * sat
    x = c * (1 - abs((hue / 60) % 2 - 1))
    m = light - c / 2
    if hue < 60:
        r1, g1, b1 = (c, x, 0)
    elif hue < 120:
        r1, g1, b1 = (x, c, 0)
    elif hue < 180:
        r1, g1, b1 = (0, c, x)
    elif hue < 240:
        r1, g1, b1 = (0, x, c)
    elif hue < 300:
        r1, g1, b1 = (x, 0, c)
    else:
        r1, g1, b1 = (c, 0, x)
    r = round((r1 + m) * 255)
    g = round((g1 + m) * 255)
    b = round((b1 + m) * 255)
    rgb = (r, g, b)
    return rgb


def rgb_as_string(rgb: tuple) -> str:
    """receive rgb as tuple -> returns formatted string

    Args:
        rgb (tuple): _description_

    Returns:
        rgb_string: the rgb channels in the form of CSS rgb() value. For
            example: `rgb(100, 100, 255)`
    """
    r, g, b = rgb
    rgb_string = f"rgb({r},{g},{b})"
    return rgb_string


def hex_to_decimal(c: str) -> int:
    """converts 2-digit hex code channel to a base 10 integer

    Args:
        c: represents a single, 2-digit hexadecimal color channel

    Raises:
        ValueError: In case the channel is either not 2 digits or if
            one or more of the digits is not a hexadecimal digit.

    Returns:
        total: the base-10 value of the hex number (as an integer)
    """
    # make sure to convert to lower case
    # so FF becomes ff
    if len(c) != 2:
        msg = "The hex_to_decimal function only accepts strings of "
        msg += "2 digits"
        raise ValueError(msg)
    if c[0].lower() not in hex_map.keys():
        raise ValueError(f"The value `{c}` is not a valid hex code.")
    c = c.lower()
    ones = hex_map[c[1]]
    sixteens = hex_map[c[0]] * 16
    total = sixteens + ones
    return total


def extract_rgb_from_string(rgb: str) -> tuple:
    """Converts an RGB CSS color code into a tuple of integers.

    Args:
        rgb (str): An RGB CSS color code, such as `rgb(100, 255, 100)`

    Returns:
        rgb: A tuple of integer color values for red, green, and blue
            (respectively).
    """
    output = []
    if "," in rgb:
        sep = ","
    else:
        sep = " "
    rgb = rgb.split(sep)
    for i in rgb:
        try:
            output.append(i.split("(")[1].strip())
            continue
        except Exception:
            try:
                output.append(i.split(")")[0].strip())
            except Exception:
                output.append(i.strip())
                continue

    rgb = (int(output[0]), int(output[1]), int(output[2]))
    return rgb


def is_hex(val: str) -> bool:
    """Checks a CSS hex value string to make sure it is valid.

    Args:
        val (str): the CSS hex value.

    Returns:
        is_valid: whether the hex value is valid or not.
    """
    is_valid = False
    # test for hash and correct number of digits
    is_valid = "#" in val and (len(val) == 7 or len(val) == 4 or len(val) == 9)
    if not is_valid:
        is_valid = False
    else:
        # check for valid hex digits
        for i in val:
            if i != "#" and i.lower() not in list(hex_map.keys()):
                is_valid = False
    return is_valid


def is_rgb(val: str) -> bool:
    """Checks a CSS rgb value string to make sure it is valid.

    Args:
        val (str): a string in question (could be valid RGB or not)

    Returns:
        is_valid: whether the code is a valid RGB code.
    """
    is_valid = bool(re.match(rgb_all_forms_re, val))
    comma_count = val.count(",")
    is_valid = is_valid and (comma_count == 2 or comma_count == 3)
    return is_valid


def is_hsl(val: str) -> bool:
    """Checks a CSS hsl value string to make sure it is valid.

    Args:
        val (str): a string in question (could be valid HSL or not)

    Returns:
        is_valid: whether the code is a valid HSL code.
    """
    is_valid = bool(re.match(hsl_all_forms_re, val))
    comma_count = val.count(",")
    is_valid = is_valid and (comma_count == 2 or comma_count == 3)
    return is_valid


def is_color_value(val: str) -> bool:
    """Checks a string value to see if it's a valid CSS color code
    value.

    Args:
        val (str): The value in question.

    Returns:
        is_valid: whether the color code is a valid hex, hsl, or rgb
            color value.
    """
    if is_hex(val):
        is_valid = True
    elif is_hsl(val):
        is_valid = True
    elif is_rgb(val):
        is_valid = True
    else:
        is_valid = False
    return is_valid


def get_relative_luminance(val: int) -> float:
    """Returns the relative brightness of a color channel normalized
    to 0 for black and 1 for all white.

    The formula for relative luminance comes from the WCAG 2.x. The full
    details are at the W3C article: [Relative Luminence]
    (https://www.w3.org/WAI/GL/wiki/Relative_luminance).

    Note: at some point, this algorithm will be deprecated, but today
    is not that day.

    Args:
        val (int): the R, G, or B value as an integer between 0 and
            255.

    Returns:
        relative_lum: The relative luminance of the value.
    """
    val /= 255
    relative_lum = 0.0
    if val <= 0.03928:
        relative_lum = val / 12.92
    else:
        relative_lum = ((val + 0.055) / 1.055) ** 2.4
    return relative_lum


def luminance(rgb: tuple) -> float:
    """Calculates the luminance of a given color in RGB format.

    Args:
        rgb (tuple): a tuple of red, green, and blue values.

    Returns:
        luminance: the luminance value of the full CSS color.
    """
    r, g, b = rgb
    r = get_relative_luminance(r)
    g = get_relative_luminance(g)
    b = get_relative_luminance(b)
    luminance = r * 0.2126 + g * 0.7152 + b * 0.0722
    return luminance


def contrast_ratio(hex1: str, hex2: str) -> float:
    """Calculates the contrast ration between two colors.

    In WCAG 2, contrast is a measure of the difference in perceived
    "luminance" or brightness between two colors (the phrase "color
    contrast" is never used in WCAG).

    This brightness difference is expressed as a ratio ranging from
    1:1 (e.g. white on white) to 21:1 (e.g., black on a white).

    Args:
        hex1 (str): the foreground or background color.
        hex2 (str): the foreground or background color.

    Returns:
        float: the contrast ratio expressed as a float.
    """
    try:
        rgb1 = hex_to_rgb(hex1)
        rgb2 = hex_to_rgb(hex2)
    except ValueError as e:
        print(f"Oops {str(e)}")
        return 0
    l1 = luminance(rgb1)
    l2 = luminance(rgb2)
    # Make sure l1 is the lighter of the two or swap them
    if l1 < l2:
        temp = l1
        l1 = l2
        l2 = temp
    ratio = (l1 + 0.05) / (l2 + 0.05)
    # get the ratio to 2 decimal places without rounding
    # take it to 3rd decimal place, then truncate (3rd has been rounded)
    ratio = format(ratio, ".3f")[:-1]
    return float(ratio)


def get_color_type(code: str) -> str:
    """Determines what type of color code the code is.

    The only color codes this library accepts is hexadecimal (with or
    without an alpha channel), rgb, rgba, hsl, or hsla. No other color
    values are recognized.

    There may come a time this will accept another color type, but for
    now, this is it.

    Args:
        code (str): The color code as a string. It should be in the
            format of a CSS color value.

    Raises:
        ValueError: if the color code is not recognized.

    Returns:
        color_type: what type of color it is.
    """
    color_type = ""
    if "#" in code[0]:
        if len(code) > 7:
            color_type = "hex_alpha"
        else:
            color_type = "hex"
    elif "hsla" in code[:4]:
        color_type = "hsla"
    elif "hsl" in code[:3]:
        color_type = "hsl"
    elif "rgba" in code[:4]:
        color_type = "rgba"
    elif "rgb" in code[:3]:
        color_type = "rgb"
    else:
        msg = "The color code is not a recognized color code. "
        msg += "It must be a variation of hex, hsl, or rgb."
        raise ValueError(msg)
    return color_type


if __name__ == "__main__":
    r, g, b = hex_to_rgb("#336699")
    hsl = get_hsl_from_string("hsl(355, 96%, 46%)")
    rgb = hsl_to_rgb((355, 96, 46))
    is_it_correct = is_rgb(rgb)
    valid_hex = is_hex("#336699")
    print(valid_hex)
    ratio = contrast_ratio("#336699", "#ffffff")
    print("Contrast ratio between #336699 and #ffffff is: {}".format(ratio))
    get_color_contrast_report("#336699", "#ffffff")
