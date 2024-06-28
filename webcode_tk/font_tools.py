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

absolute_keyword_regex = r"\b(?:xx-small|x-small|small|medium|large|x-large|"
absolute_keyword_regex += r"xx-large|xxx-large|smaller|larger)\b"
numeric_value_regex = r"(\d+(\.\d+)?)(px|em|rem|pt|%)"


def get_absolute_keyword_values(css_code: str) -> list:
    matches = re.findall(absolute_keyword_regex, css_code)
    return matches


def get_numeric_fontsize_values(css_code: str) -> list:
    matches = re.findall(numeric_value_regex, css_code)
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
