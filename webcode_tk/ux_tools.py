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
from file_clerk import clerk
from textatistic import Textatistic

from webcode_tk import html


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
        paragraph_text += html.get_element_content(paragraph) + "\n"
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
            paragraphs += html.get_elements("p", file)
    else:
        paragraphs += html.get_elements("p", path)
    return paragraphs


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
