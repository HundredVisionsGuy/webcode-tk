"""A set of tools to conduct some UX (User eXperience) checks.

As of now, I just want to check for best UX and SEO practices such
as checking for best practices in writing for the web.

The primary source of information we will begin to use are from
[Writing Compelling Digital Copy](https://www.nngroup.com/courses/writing/).

According to the article...
* Be Succinct! (Writing for the Web)
* "The 3 main guidelines for writing for the web are:
    - Be succinct: write no more than 50% of the text you would have used in a
    hardcopy publication
    - Write for scannability: don't require users to read long continuous
    blocks of text
    - Use hypertext to split up long information into multiple pages"
"""
import re
from collections.abc import Sequence
from typing import Union

from file_clerk import clerk
from textatistic import Textatistic

from webcode_tk import html_tools


def get_flesch_kincaid_grade_level(path: str) -> float:
    """returns the required education to be able to understand the text.

    We're only looking at the paragraphs (not headers or list items) and
    ignoring break tags as being paragraph breaks (that could be up for
    debate in the future).

    This function first checks to see if it's a project folder or just a
    single file and ascertains for all HTML documents if it's a project.

    Args:
        path: the path to the page or project that we are measuring.

    Returns:
        grade_level: the US grade level equivalent."""

    # convert all paragraph content into a single string
    paragraphs = get_all_paragraphs(path)
    paragraph_text = get_paragraph_text(paragraphs)

    # get stats from textatistic
    r = Textatistic(paragraph_text)
    grade_level = r.fleschkincaid_score

    # return grade level rounded to 1 decimal point
    return round(grade_level, 1)


def get_readability_stats(
    path: str, elements: Union[str, Sequence] = "p"
) -> dict:
    """returns a dictionary of various readability stats.

    It will collect all stats from the textastic libary as well as add
    a few of my own (words per sentence, sentences per paragraph).

    Args:
        path: the path to the file or folder (only looks at HTML files)
        elements: by default we will only look at the text from paragraph
            tags. You could supply other elements in the form of a list or
            tuple (e.g. ['p', 'div', 'li', 'figcaption']).

    Returns:
        stats: a dictionary of stats on readability metrics.
    """
    stats = {}

    # Get text and numbers
    text = get_text_from_elements(path, elements)
    num_lines = len(text)

    # get stats from textatistic
    text = "\n".join(text)
    r = Textatistic(text)

    for key, value in r.scores.items():
        stats[key] = round(value, 2)
    stats["character_count"] = r.char_count
    stats["word_count"] = r.word_count
    stats["sentence_count"] = r.sent_count
    stats["paragraph_count"] = num_lines
    stats["words_per_sentence"] = round(r.word_count / r.sent_count, 2)
    stats["sent_per_paragraph"] = round(r.sent_count / num_lines, 2)

    return stats


def get_paragraph_text(paragraphs: list) -> str:
    """Returns a string of all the contents of the list of paragraphs

    Args:
        paragraphs: a list of paragraph elements.

    Returns:
        paragraph_text: a string of all the content of the paragraph
            elements.
    """
    paragraph_text = ""
    for paragraph in paragraphs:
        paragraph_text += html_tools.get_element_content(paragraph) + "\n"
    return paragraph_text.strip()


def get_all_paragraphs(path: str) -> list:
    """returns a list of paragraph elements from a single file or project
    folder.

    It checks the path to determine if it's a path to a single page or a
    project folder.

    Args:
        path: a string path to either an html document or a project folder.

    Returns:
        paragraphs: a list of paragraph elements."""

    paragraphs = []
    is_single_page = "html" == clerk.get_file_type(path)

    if not is_single_page:
        # it's a project, so we need to process all html files in the folder
        all_files = clerk.get_all_files_of_type(path, "html")
        for file in all_files:
            paragraphs += html_tools.get_elements("p", file)
    else:
        paragraphs += html_tools.get_elements("p", path)
    return paragraphs


def get_text_from_elements(
    path: str, elements: Union[str, Sequence] = "p"
) -> list:
    """returns a list of text from elements (as strings) from a single file or
    project folder.

    It checks the path to determine if it's a path to a single page or a
    project folder. It then uses the elements to determine from which
    HTML element it will grab paragraphs.

    By default, it will only pull paragraphs from the `<p>` tag, but you
    can specify other elements (e.g. `<div>`, `<li>`, `<figcaption>`, etc.).

    NOTE: When selecting other tags, pass it a list or tuple of strings. Only
    specify the element without angle brackets (e.g. `['p', 'li', 'div']`)

    Args:
        path: a string path to either an html document or a project folder.
        elements: the elements we want to pull our paragrphs from.
    Returns:
        paragraphs: a list of strings - text only without markup (for example
        if an anchor is nested in a pargraph, the markup will be extracted, and
        only the visible text on the page will be present."""

    paragraphs = []
    is_single_page = "html" == clerk.get_file_type(path)
    if elements == "p":
        elements = ["p"]
    if not is_single_page:
        # it's a project, so we need to process all html files in the folder
        all_files = clerk.get_all_files_of_type(path, "html")
        for file in all_files:
            for element in elements:
                markup = html_tools.get_elements(element, file)
                for tag in markup:
                    text = extract_text(tag)
                    paragraphs.append(text)
    else:
        for element in elements:
            markup = html_tools.get_elements(element, path)
            for tag in markup:
                text = extract_text(tag)
                paragraphs.append(text)
    return paragraphs


def remove_extensions(text: str) -> str:
    """removes extension from filenames.

    Filenames with extensions end up causing textatistic to count filenames
    as two words instead of one, and we don't really need to count the
    extensions when calculating readability stats.

    Args:
        text: the text which may or may not have filenames in them.

    Returns:
        newtext: the text without file extensions.
    """
    newtext = ""

    # get the last character just in case it gets dropped with extension.
    last_char = text[-1]
    regex = r"\.[a-zA-Z0-9]+"
    newtext = re.sub(regex, "", text)

    # add back the last character if it was dropped.
    if newtext[-1] != last_char:
        newtext += last_char
    return newtext


def extract_text(tag) -> str:
    """extracts only the text from a tag (no markup)

    Args:
        tag: this is a Tag (bs4)
    Returns:
        text: just the visible text from the element (with no
        nested markup)."""
    text = tag.text
    text = " ".join(text.split())
    return text


def get_words_per_paragraph(path: str) -> float:
    """returns average number of words per paragraph

    uses Textatistic stats"""
    paragraphs = get_all_paragraphs(path)
    text = get_paragraph_text(paragraphs)
    text = text.replace("\n", " ")
    r = Textatistic(text)
    words = r.counts.get("word_count")
    num_paragraphs = len(paragraphs)
    return round(words / num_paragraphs, 1)


if __name__ == "__main__":
    # let's test some stuff out.
    path = "tests/test_files/large_project/"
    all = extract_text(path, ["p", "figcaption"])
    all = get_paragraph_text(all)
    print(all)
