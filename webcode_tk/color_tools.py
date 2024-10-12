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

from webcode_tk import color_keywords

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
hex_re = r"#\w{3},*\s|#\w{6},*\s|#\w{8},*\s"
gradient_re = r"\b(linear-gradient|radial-gradient|conic-gradient)\b"


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


def get_contrast_results_from_ratio(
    ratio: float, size: float, is_bold: bool
) -> str:
    """takes contrast, compares to map and returns results as a string

    Args:
        ratio: the contrast ratio.
        size: calculated font size.

    Returns:
        str: whether it passes or not with details.
    """
    # is the text large or not?
    is_large = size >= 24 or is_bold and size >= 16.66
    if is_large:
        aaa_goal = contrast_ratio_map.get("Large AAA")
        passes = ratio >= aaa_goal
        if passes:
            return "pass: Large AAA contrast rating"
        aa_goal = contrast_ratio_map.get("Large AA")
        conditionally_passes = ratio >= aa_goal
        if conditionally_passes:
            return "conditional pass: Large AA contrast rating"
        else:
            return "fail: fails all contrast ratings"
    else:
        aaa_goal = contrast_ratio_map.get("Normal AAA")
        passes = ratio >= aaa_goal
        if passes:
            return "pass: Normal AAA contrast rating"
        aa_goal = contrast_ratio_map.get("Normal AA")
        conditionally_passes = ratio >= aa_goal
        if conditionally_passes:
            return "conditional pass: Normal AA contrast rating"
        else:
            return "fail: fails normal sized text contrast"


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
        hex1: a foreground or background color (doesn't matter
            which)
        hex2: a foreground or background color (doesn't matter
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


def get_hex(value: str) -> str:
    """Gets any color code value and returns as hex value.

    Color value must be hex, rgb, hsl, or a color keyword.
    Determines what type of color code it is, converts it to hex
    if necessary, and returns a hex value.

    This will NOT work with an alpha channel.

    Args:
        code: a CSS color code value (any type)

    Returns:
        hex: a hex equivalent of the color code
    """
    hex = ""
    if is_hex(value):
        hex = value
    elif is_rgb(value):
        hex = rgb_to_hex(value)
    elif is_hsl(value):
        values = re.findall(r"\d+", value)
        ints_not_strings = [eval(i) for i in values]
        hsl = tuple(ints_not_strings)
        rgb = hsl_to_rgb(hsl)
        rgb = "rgb" + str(rgb)
        hex = rgb_to_hex(rgb)
    else:
        # is it a color keyword?
        if color_keywords.is_a_keyword(value):
            hex = color_keywords.get_hex_by_keyword(value)
    return hex


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
            if isinstance(rgb, str):
                r, g, b = extract_rgb_from_string(rgb)
            if isinstance(rgb, tuple) and len(rgb) == 3:
                r, g, b = rgb
        except Exception:
            # throw an exception
            return "err"
    # Convert r, g, b to hexidecimal format
    r_hex = hex(int(r))[2:]
    g_hex = hex(int(g))[2:]
    b_hex = hex(int(b))[2:]
    # prepend 0 if necessary
    if len(r_hex) == 1:
        r_hex = "0" + r_hex
    if len(g_hex) == 1:
        g_hex = "0" + g_hex
    if len(b_hex) == 1:
        b_hex = "0" + b_hex
    hex_code = "#" + r_hex + g_hex + b_hex
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

    NOTE: hsl() might have an alpha channel. If there is a slash, then
    there is an alpha channel.

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
    if "hsl(" in code and "/" in code:
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
    hue /= 360
    if sat == 0:
        r = light
        g = light
        b = light
    else:
        sat /= 100
        light /= 100

        def hue2rgb(p, q, t):
            if t < 0.0:
                t += 1
            if t > 1:
                t -= 1
            if t < 1 / 6:
                return p + (q - p) * 6 * t
            if t < 1 / 2:
                return q
            if t < 2 / 3:
                return p + (q - p) * (2 / 3 - t) * 6
            return p

    if light < 0.5:
        q = light * (1 + sat)
    else:
        q = light + sat - light * sat
    p = 2 * light - q

    r = hue2rgb(p, q, hue + 1 / 3)
    g = hue2rgb(p, q, hue)
    b = hue2rgb(p, q, hue - 1 / 3)

    return (round(r * 255), round(g * 255), round(b * 255))


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
    elif is_keyword(val):
        is_valid = True
    else:
        is_valid = False
    return is_valid


def is_keyword(val: str) -> bool:
    """checks to see if a value is a color keyword or not

    Args:
        val: the CSS value in question.

    Returns:
        is_keyword: if the value is a color keyword or not."""
    val = val.lower()
    is_keyword = val in color_keywords.get_all_keywords()
    return is_keyword


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
    ratio_string = str(ratio)
    dot_pos = ratio_string.index(".")
    ratio_string = ratio_string[: dot_pos + 3]
    return float(ratio_string)


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
    elif color_keywords.is_a_keyword(code):
        color_type = "keyword"
    else:
        msg = "The color code is not a recognized color code. "
        msg += "It must be a variation of hex, hsl, or rgb."
        raise ValueError(msg)
    return color_type


def is_gradient(val: str) -> bool:
    """returns whether the value is a gradient or not

    Args:
        val: the CSS value in question
    """
    gradient_pattern = re.compile(gradient_re, re.IGNORECASE)
    return bool(gradient_pattern.search(val))


def get_gradient_colors(gradient: str) -> list:
    """returns all color values from a gradient

    Returns all hex, rgb, rgba, hsl, hsla, and keyword values.

    Args:
        gradient: the gradient value

    Returns:
        colors: a list of all colors in a gradient"""
    colors = []

    # Get all rgb, hex, hsl, and keywords through regex
    all_rgbs = re.findall(rgb_all_forms_re, gradient)
    if all_rgbs:
        colors += all_rgbs
    all_keywords = get_all_keywords(gradient)
    if all_keywords:
        colors += all_keywords
    all_hex_codes = get_all_hex_codes(gradient)
    if all_hex_codes:
        colors += all_hex_codes
    if "hsl" in gradient:
        all_hsl_codes = get_all_hsl_codes(gradient)
        colors += all_hsl_codes
    return colors


def get_all_hex_codes(text: str) -> list:
    """returns a list of all hex code in the text

    Args:
        text: the css_code or text you want to search.

    Returns:
        all_hex_codes: a list of all valid hexadecimal color codes
    """
    all_hex_codes = []
    possible_hex_codes = re.findall(hex_re, text)
    if possible_hex_codes:
        for color in possible_hex_codes:
            color = color.strip()
            if "," in color:
                color = color.replace(",", "")
            if is_hex(color):
                all_hex_codes.append(color)
    return all_hex_codes


def get_all_keywords(text: str) -> list:
    """returns any and all color kewords from text.

    This was designed to capture all color keywords that
    might be in a gradient, but there may be other uses.

    Args:
        text: the string in question (most likely a gradient)

    Returns:
        keywords: a list of color keywords
    """
    possible_keyword_re = r"([A-Za-z0-9\-]+)"
    potential_keywords = re.findall(possible_keyword_re, text)
    keywords = []
    for word in potential_keywords:
        if is_keyword(word):
            keywords.append(word)
    return keywords


def get_all_hsl_codes(text: str) -> list:
    """returns a list of all hsl code in the text

    Args:
        text: the css_code or text you want to search.

    Returns:
        all_hex_codes: a list of all valid hexadecimal color codes
    """
    all_hsl_codes = []
    possible_hsl_codes = re.findall(hsl_all_forms_re, text)
    if possible_hsl_codes:
        for color in possible_hsl_codes:
            hsl_code = ""
            if "hsla" in color:
                hsl_code = "hsla("
            else:
                hsl_code = "hsl("
            color_values = color.split(",")
            hue = color_values[0].split("(")[1]
            sat = color_values[1]
            light = color_values[2]
            if "hsla" in color:
                alpha = color_values[3]
                hsl_code = f"{hsl_code}{hue},{sat},{light},{alpha}"
            else:
                hsl_code = f"{hsl_code}{hue},{sat},{light}"
            all_hsl_codes.append(hsl_code)
    return all_hsl_codes


def get_color_contrast_with_gradients(
    fg_color: str, bg_color: str, ancestors=None
) -> list:
    """gets a list of all color contrast permutations with 1 or 2 gradients

    Checks all combinations of foreground and background colors when one or
    both are gradients. Creates a tuple of results (starting with contrast)
    and original color code sort by contrast.

    Args:
        fg_color: foreground color, could be any color type (including
            gradient).
        bg_color: background color, could also be any color type (including
            gradient).

    Returns:
        results: a list of all color contrast result data sorted by
            contrast ratio (lowest to highest)"""
    results = []

    # if foreground color is a gradient, get all colors or convert to list
    if is_gradient(fg_color):
        foreground_colors = get_gradient_colors(fg_color)
    else:
        foreground_colors = [
            fg_color,
        ]
    if is_gradient(bg_color):
        bg_colors = get_gradient_colors(bg_color)
    else:
        bg_colors = [
            bg_color,
        ]
    composite_color = ""
    # check all permutations of color combinations for contrast results
    for foreground in foreground_colors:
        for background in bg_colors:
            composite_color = ""
            # check for background alpha transparency
            bg_has_alpha = has_alpha_channel(background)
            if bg_has_alpha:
                container_bg = ""
                for i in range(len(ancestors) - 1, -1, -1):
                    ancestor = ancestors[i]
                    if len(ancestor) > 2:
                        base_color = ancestor[2]
                        composite_color = blend_alpha(base_color, background)
                        container_bg = ancestor[2]
                if not composite_color:
                    composite_color = blend_alpha(container_bg, background)
            # convert each to hex
            hex1 = to_hex(foreground)
            if composite_color:
                hex2 = to_hex(composite_color)
            else:
                hex2 = to_hex(background)

            # get color contrast
            contrast = contrast_ratio(hex1, hex2)

            # append to results list
            if composite_color:
                results.append(
                    (
                        contrast,
                        foreground,
                        background,
                        composite_color,
                        bg_has_alpha,
                    )
                )
            else:
                results.append(
                    (contrast, foreground, background, background, False)
                )
    results.sort()
    return results


def to_hex(color_code: str) -> str:
    """converts any color code to hex

    Checks to see if it is a hex and returns if so. Then sees which type of
    color code it is and converts to hex and returns the value.

    Args:
        color_code: a string version of a color code.

    Returns:
        str: a hexadecimal color code based on the original color
    """
    hex = ""
    if is_hex(color_code):
        hex = color_code
    elif is_rgb(color_code):
        hex = rgb_to_hex(color_code)
    elif is_keyword(color_code):
        hex = color_keywords.get_hex_by_keyword(color_code)
    elif is_hsl(color_code):
        if isinstance(color_code, str):
            hsl = get_hsl_from_string(color_code)
        else:
            hsl = color_code
        rgb = hsl_to_rgb(hsl)
        hex = rgb_to_hex(rgb)
    return hex


def blend_alpha(base: str, color_with_alpha: str) -> str:
    """blend a color with an alpha channel with base color

    returns a color in the same format as the alpha color but
    without the alpha channel.

    The algorithm:
    new_color = (alpha)*(foreground_color) + (1 - alpha)*(background_color)

    Try this:
    result.r = background.r * (1 - A) + foreground.r * A
    result.g = background.g * (1 - A) + foreground.g * A
    result.b = background.b * (1 - A) + foreground.b * A
    This computation is done separately for the red, blue, and green color
    components.

    Args:
        base: the background color (must be computed and not alpha).
        color_with_alpha: a color code as a string that has an alpha value

    Returns:
        result: the computed code using the original type of color value but
            without an alpha channel

    Raises:
        ValueError: if we don't recognize the color value with an alpha
        channel.
    """
    result = ""
    # Get the RGB for base color
    red1, green1, blue1 = get_rgb(base)
    color_minus_alpha = ""
    alpha_a = 0.0
    alpha_color_type = get_color_type(color_with_alpha)
    if alpha_color_type == "hsla":
        # Get alpha channel
        if "," in color_with_alpha:
            hsl_values = color_with_alpha.split(",")
        else:
            hsl_values = color_with_alpha.split(" ")
        if "/" in color_with_alpha:
            alpha_a = color_with_alpha.split("/")[-1]
            alpha_a = alpha_a.replace("%", "")
            alpha_a = alpha_a.replace(")", "")
            alpha_a = alpha_a.strip()
            alpha_a = float(alpha_a) / 100.0
        else:
            alpha_a = hsl_values[-1].strip()
            alpha_a = alpha_a.replace(")", "")
            alpha_a = float(alpha_a)

        # just get hsl (no alpha)
        color_minus_alpha = "hsl("
        hue = hsl_values[0].split("(")[-1].strip()
        hue = int(hue)
        sat = hsl_values[1].strip().replace("%", "")
        sat = int(sat)
        light = hsl_values[2].strip().replace("%", "")
        light = int(light)

        # Get RGB from hue saturation and lightness
        red2, green2, blue2 = hsl_to_rgb((hue, sat, light))

    elif alpha_color_type == "rgba":
        if isinstance(color_with_alpha, str):
            values = color_with_alpha.split("(")[1]
            alpha_raw = values.split(",")
            r_g_b = ",".join(alpha_raw[:-1])
            color_minus_alpha = f"rgb({r_g_b})"
            alpha_raw = alpha_raw[-1]
            alpha_a = float(alpha_raw[:-1])
    elif alpha_color_type == "hex_alpha":
        alpha_a = color_with_alpha[-2:]
        alpha_a = hex_to_decimal(alpha_a) / 255
        alpha_a = round(alpha_a, 2)
        color_minus_alpha = color_with_alpha[:-2]
    else:
        raise ValueError("I don't recognize that color type")
    if alpha_a == 0.0:
        result = base
    elif alpha_a == 1.0:
        result = color_minus_alpha
    else:
        # get red, green, and blue channel values
        red2, green2, blue2 = get_rgb(color_with_alpha)
        # Here is the math part where we calculate to composite color
        # alpha_b = 1.0
        # alpha = alpha_a + alpha_b * (1 - alpha_a)

        # (alpha)*(foreground_color) + (1 - alpha)*(background_color)
        new_red = blend_channel(red1, red2, alpha_a)
        new_green = blend_channel(green1, green2, alpha_a)
        new_blue = blend_channel(blue1, blue2, alpha_a)
        rgb_string = rgb_as_string((new_red, new_green, new_blue))
        if "hsl" in alpha_color_type:
            result = color_to_hsl(rgb_string)
        elif "hex" in alpha_color_type:
            result = get_hex(rgb_string)
        else:
            result = rgb_string
    return result


def blend_channel(background, foreground, alpha):
    """
    result.c = background.c * (1 - A) + foreground.c * A
    """
    new_color = background * (1 - alpha) + foreground * alpha
    return round(new_color)


def get_rgb(code: str) -> tuple:
    """returns tuple of r,g,b values from any color value"""
    # make code lowercase, just in case (mostly for keywords)
    code = code.lower()
    red, green, blue = (0, 0, 0)
    color_type = get_color_type(code)
    if color_type == "hex":
        red, green, blue = hex_to_rgb(code)
    if color_type == "hex_alpha":
        code = code[:7]
        red, green, blue = hex_to_rgb(code)
    if "rgb" in code:
        red, green, blue = extract_rgb_from_string(code)
    if color_type == "hsl" or color_type == "hsla":
        # get just hsl as a tuple
        color_split = re.findall(r"-?\d+\.?\d*", code)
        values = (
            int(color_split[0]),
            int(color_split[1]),
            int(color_split[2]),
        )
        red, green, blue = hsl_to_rgb(values)
    if is_keyword(code):
        hex = color_keywords.get_hex_by_keyword(code)
        red, green, blue = hex_to_rgb(hex)
    return (red, green, blue)


def color_to_hsl(color_code: str) -> str:
    """converts keyword, hex, or rgb to hsl

    Args:
        color_code: string version of color code
    Returns:
        hsl: hsl color code as a string
    """
    hsl = "hsl("

    # Get the RGB color channels from code
    if is_keyword(color_code):
        hex = color_keywords.get_hex_by_keyword(color_code)
        red, green, blue = hex_to_rgb(hex)
    elif is_hex(color_code):
        red, green, blue = hex_to_rgb(color_code)
    elif is_rgb(color_code):
        red, green, blue = extract_rgb_from_string(color_code)

    # Convert each channel to a decimal between 0 and 1
    red = red / 255
    green = green / 255
    blue = blue / 255
    decimal_values = (red, green, blue)

    # Calculate luminance
    minimum = min(decimal_values)
    maximum = max(decimal_values)
    lightness = (maximum + minimum) / 2
    hue = (maximum + minimum) / 2
    saturation = (maximum + minimum) / 2

    if maximum == minimum:
        hue = 0
        saturation = 0
    else:
        delta = maximum - minimum
        saturation = (
            delta / (2 - maximum - minimum)
            if lightness > 0.5
            else delta / (maximum + minimum)
        )
        if red == maximum:
            if green < blue:
                hue = (green - blue) / delta + 6
            else:
                hue = (green - blue) / delta
        if green == maximum:
            hue = (blue - red) / delta + 2
        else:
            hue = (red - green) / delta + 4
        hue /= 6
        hue *= 360
        hue = round(hue)
    lightness *= 100
    lightness = round(lightness)
    saturation *= 100
    saturation = round(saturation)
    hsl = f"{hsl}{hue}, {saturation}%, {lightness}%)"
    return hsl


if __name__ == "__main__":
    # print()
    # hex = rgb_to_hex("rgb(190, 228, 210)")
    # print(hex)
    # hex2 = rgb_to_hex("rgb(215, 248, 247)")
    # print(hex2)
    # hex = rgb_to_hex("rgb(250, 178, 172)")
    # print(hex)
    hex = rgb_to_hex("rgb(237, 161, 193)")
    print(hex)
