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
absolute_keyword_regex += r"xx-large|xxx-large|smaller|larger)\b"
numeric_value_regex = r"(\d+(\.\d+)?)(px|em|rem|pt|%)"

KEYWORD_SIZE_MAP = {
    "xx-small": "9px",
    "x-small": "10px",
    "small": "13px",
    "medium": "16px",
    "large": "18px",
    "x-large": "24px",
    "xx-large": "32px",
    "xxx-large": "48px",
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
    full_matches = ["".join(match) for match in matches]
    return full_matches


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
