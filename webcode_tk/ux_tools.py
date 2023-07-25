"""A set of tools to conduct some UX (User eXperience) checks.

As of now, I just want to check for best UX and SEO practices such
as checking for best practices in writing for the web.

The primary source of information we will begin to use are from
[Writing Compelling Digital Copy](https://www.nngroup.com/courses/writing/).

According to the article, *Be Succinct! (Writing for the Web)*,
"The 3 main guidelines for writing for the web are:
* Be succinct: write no more than 50% of the text you would have used in a
hardcopy publication
* Write for scannability: don't require users to read long continuous blocks
of text
* Use hypertext to split up long information into multiple pages"
"""
from readability import Readability
from textatistic import Textatistic


def get_flesch_kincaid_grade_level(text: str) -> float:
    """returns the required education to be able to understand the text.

    The formula is as follows:
    `0.39 x (words/sentences) + 11.8 x (syllables/words) – 15.59`

    206.835 - (1.015 × ASL) - (84.6 × ASW)

    This is based on the following article: [What Is Flesch-Kincaid
    Readability?](https://www.webfx.com/tools/read-able/flesch-kincaid/)

    Args:
        text: the text that we are measuring.

    Returns:
        grade_level: the US grade level."""
    r = Readability(text)
    t = Textatistic(text)
    print(t.fleschkincaid_score)
    grade_level = r.flesch_kincaid()
    ease = r.flesch()
    stats = r.statistics()
    print(ease)
    print(stats)
    return grade_level
