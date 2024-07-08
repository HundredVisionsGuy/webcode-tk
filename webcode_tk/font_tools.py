"""
A collection of functions used to process font-related styles.

As my other files were getting large and creeping in their scope,
I decided to create yet another single module to deal strictly
with font-related styles.

One of the things I want to do is to compute the size of a
particular element in the DOM, and the rules behind it can get a
little daunting, so here we are.
"""
import re
from typing import Union

from webcode_tk.css_tools import Stylesheet

absolute_keyword_regex = r"\b(?:xx-small|x-small|small|medium|large|x-large|"
absolute_keyword_regex += r"xx-large|xxx-large)\b"
relative_keyword_regex = r"\b(?:smaller|larger)\b"
numeric_value_regex = r"(\d+(\.\d+)?)(px|em|rem|pt|%)"
relative_keyword = re.compile(relative_keyword_regex)
HEADING_SIZES = {
    "h1": "2.0em",
    "h2": "1.5em",
    "h3": "1.17em",
    "h4": "1.0em",
    "h5": "0.83em",
    "h6": "0.67em",
}

KEYWORD_SIZE_MAP = {
    "xx-small": 9,
    "x-small": 10,
    "small": 13,
    "medium": 16,
    "large": 18,
    "x-large": 24,
    "xx-large": 32,
    "xxx-large": 48,
}


def get_absolute_keyword_values(css_code: Union[str, Stylesheet]) -> list:
    """returns a list of all keyword values in CSS

    To be safe, we should remove all selectors using the curly brackets
    with the split method.

    Args:
        css_code: the CSS styles in either string or Stylesheet format
    """
    if isinstance(css_code, Stylesheet):
        styles = css_code.text
    else:
        styles = css_code
    values = []
    style_split = styles.split("{")
    for i in style_split:
        if ":" in i:
            start = i.index(":")
            stop = len(i)
            if ";" in i:
                stop = i.index(";")
            elif "}" in i:
                stop = i.index("}")
            value_str = i[start:stop]
            matches = re.findall(absolute_keyword_regex, value_str)
        else:
            matches = re.findall(absolute_keyword_regex, i)
        if matches:
            values += matches
    return values


def get_numeric_fontsize_values(css_code: Union[str, Stylesheet]) -> list:
    """returns a list of all numeric font size values.

    This should work for any standard size value (em, px, %,
    rem). As of now, we are ignoring vw and vh because they are
    based on the size of the window, and that is out of our control.
    Args:
        css_code: the CSS styles in either string or Stylesheet format.
    """
    if isinstance(css_code, Stylesheet):
        code = css_code.text
    else:
        code = css_code
    matches = re.findall(numeric_value_regex, code)
    full_matches = []
    for match in matches:
        full_matches.append(match[0] + match[-1])
    return full_matches


def get_font_unit(value: str) -> str:
    """returns unit being use when setting font-size"""
    unit = ""
    # Check for relative keywords
    if value in KEYWORD_SIZE_MAP.keys():
        unit = "absolute_keyword"
    elif relative_keyword.search(value):
        unit = "relative_keyword"
    elif "rem" in value:
        unit = "rem"
    elif "em" in value:
        unit = "em"
    elif "px" in value:
        unit = "pixels"
    elif "%" in value:
        unit = "percentage"
    elif value == 0:
        unit = "zero"
    else:
        unit = value
    return unit


def split_value_unit(value: str) -> tuple:
    """returns the numeric value and unit of a size value

    First, check for absolute and relative keywords, then split at
    number

    Args:
        value: the CSS value (from a font-size declaration).

    Returns:
        value_unit: a tuple of the value and the unit.
    """
    value_unit = ["", ""]
    if value in KEYWORD_SIZE_MAP.keys():
        value_unit = (value, "absolute_keyword")
    elif relative_keyword.search(value):
        value_unit = (value, "relative_keyword")
    elif value in ["0", "0.0"]:
        value_unit = (value, "zero")
    else:
        # do a regex split
        num = re.findall(r"[+-]?(\d*\.\d+|\d+)", value)[0]
        unit = re.findall(r"%|rem|em|px", value)[0]
        value_unit = (float(num), unit)
    return tuple(value_unit)


def compute_rem(value: str) -> float:
    """returns computed value in pixels

    Convert rems to pixels by multiplying the rem value to
    pixels (rem * 16)

    Args:
        value: the value only of a rem.

    Returns:
        pixel: the computed size in pixels
    """
    pixels = float(value) * 16
    return pixels


def compute_keyword_size(value: str) -> int:
    """return computed value in pixels

    Extracts the keyword and uses it to get the value. Uses
    the absolute_keyword_regex.

    Args:
        value: the value from the font-size declaration.

    Returns:
        pixels: the font-size of the keyword in pixels.
    """
    pixels = 0
    keyword = re.findall(absolute_keyword_regex, value)[0]
    pixels = KEYWORD_SIZE_MAP.get(keyword)
    return pixels


def is_large_text(size: float, is_bold: bool) -> bool:
    """returns whether the text is considered large or not

    This is based on the WebAIM color contrast analyzer, which
    states that text is large if it is 18.66 and bold or larger
    or 24px or larger.

    Args:
        size: the computed font-size.
        is_bold: whether the text is bold or not.

    Returns:
        is_large: whether the text is considered large or not.
    """
    is_large = False
    return is_large


def compute_font_size(
    value: Union[str, int, float],
    unit: str,
    parent_size: Union[int, float] = 16.0,
    element_name: str = "",
) -> float:
    """Computes font size based on value, unit, and possibly parent size.

    This is for handling any font-size declaration value. Some sizes are
    fixed, and others are relative based on relative keyword, root size,
    or parent's computed size.

    The default size for parent_size is the root size of a font (by default,
    it is 16px).

    Args:
        value: numeric or keyword value (could be a string, int, or float).
        unit: the unit of measurement as a string.
        parent_size: if applicable, the computed font size of the parent.
        element_name: optionally, you may set this, but it's only necessary
            if your element is an h1 - h6 tag.

    Returns:
        computed_size: the computed size in pixels.

    Raises:
        TypeError: if the unit is not recognized (may be a true error, or
            may be using a new font-size)
    """
    computed_size = 16.0
    if unit == "absolute_keyword":
        computed_size = compute_keyword_size(value)
    elif unit == "relative_keyword":
        if value == "larger":
            computed_size = parent_size * 1.2
        elif value == "smaller":
            computed_size = parent_size * 0.833
    elif unit == "rem":
        computed_size = compute_rem(value)
    elif unit in ("percent", "percentage", "%"):
        percentage = value * 0.01
        computed_size = parent_size * percentage
    elif unit == "em":
        computed_size = parent_size * value
    elif unit in ("unset", "inherit"):
        computed_size = parent_size
    elif unit in "revert":
        if element_name in HEADING_SIZES.keys():
            ems = HEADING_SIZES.get(element_name)
            multiplier = ems.split("e")[0]
            computed_size = parent_size * float(multiplier)
        else:
            computed_size = parent_size
    elif unit == "initial":
        computed_size = 16.0
    else:
        raise TypeError("I'm afraid I can't compute that, Dave")
    return round(computed_size, 1)


if __name__ == "__main__":
    sample_styles = """
/* <absolute-size> values */
font-size: xx-small;
font-size: x-small;
font-size: small;
font-size: medium;
font-size: large;
font-size: x-large;
font-size: xx-large;
font-size: xxx-large;
font: small-caps;
/* <relative-size> values */
font-size: smaller;
font-size: larger;

font-size: 14rem;

/* <length> values */
font: 12px;
font-size: 0.8em;

/* <percentage> values */
font: 80%;
"""
    matches = get_absolute_keyword_values(sample_styles)
    print(matches)

    pattern = r"(\d+(\.\d+)?)(px|em|rem|pt|%)"

    # Find all matches in the CSS string
    matches = get_numeric_fontsize_values(sample_styles)
    print(matches)
