"""A collection of functions for getting HTML code and contents.

This is a library I created in order to help me autograde student web
desing projects. For example, in a web design assignment, I might ask
my students to be sure to include at least two bullet lists or five
links.

This tool allows you to get and analyze what tags are present in a
project, get contents from elements, find out how many particular
elements were present or not.

    Typical usage example:
    ``
"""
import os
import re
from typing import Union

from bs4 import BeautifulSoup
from bs4 import Tag
from file_clerk import clerk
from lxml import html

# global variables
STARTS_WITH_OPENING_TAG_RE = "^<[^/]+?>"
OPENING_TAG_RE = "<[^/]+?>"
CLOSING_TAG_RE = "</.+?>"


def get_all_html_files(dir_path: str) -> list:
    """Returns a list of all files in the dir_path folder.

    This function takes a path to a directory and returns a list of all
    html documents in that folder as full paths (including the path to
    the directory).


    Args:
        dir_path: a string of a path to a folder (directory). This path
            should be a relative path starting at the root directory of
            your python project.

    Returns:
        html_files: a list of full paths to all HTML documents in the
            dir_path folder.
    """
    html_files = clerk.get_all_files_of_type(dir_path, "html")
    return html_files


def get_html(file_path: str) -> BeautifulSoup:
    """Returns an html document (from file_path) as a BeautifulSoup object

    This function takes advantage of the bs4 library's `BeautifulSoup`
    datatype, also known as simply a soup object.

    Args:
        file_path: the file location (and filename as a relative link).

    Returns:
        soup: this is a BeautifulSoup object that represents an HTML tree
            or NoneType if there is a failure.

    Raises:
        FileNotFound: the file path did not exist.

    .. Beautiful Soup Documentation:
        https://www.crummy.com/software/BeautifulSoup/bs4/doc/#making-the-soup
    """
    try:
        with open(file_path, encoding="utf-8") as fp:
            soup = BeautifulSoup(fp, "html.parser")
            return soup
    except FileNotFoundError:
        print("This is a non-existent file")
        raise


def get_num_elements_in_file(el: str, file_path: str) -> int:
    """Returns the number of HTML elements in a web page (file)

    This function takes the name of an element in the string form and
    the relative path to the HTML document, and it returns the number
    of occurences of that tag in the document.

    Args:
        el: the name of a tag, but not in tag form (for example: p, ul,
            or div)
        file_path: relative path to an html document (relative to the
            project folder)

    Returns:
        num: the number of elements found in the document in integer form

    Raises:
        FileNotFound: the file path did not exist.
    """
    with open(file_path, encoding="utf-8") as fp:
        if (
            el.lower() in ["doctype", "html", "head", "title", "body"]
            and el.lower() != "header"
        ):
            # bs4 won't find doctype
            contents = fp.read()
            contents = contents.lower()
            substring = el.lower()
            if el.lower() == "doctype":
                substring = "<!" + substring
            else:
                substring = "<" + substring

            # if the element is the head, you must use a regex
            # to not count the <header> tag
            if el.lower() == "head":
                count = len(re.findall(r"<head[\s>]", contents))
            else:
                count = contents.count(substring)
            # return the number of doctypes
            return count
        soup = BeautifulSoup(fp, "html.parser")
        elements = soup.find_all(el.lower())
    num = len(elements)
    return num


def get_num_elements_in_folder(el: str, dir_path: str) -> int:
    """Returns the total number of a specific element in all files
    of a project.

    Checks to make sure the folder exists, then goes through all html
    files in the directory to see how many occurrences there are among
    all the files.

    Args:
        el: the name of a tag, but not in tag form (for example: p, ul,
            or div)
        dir_path: relative path to an html document (relative to the
            project folder).

    Returns:
        num: the number of elements found in the document in integer form

    Raises:
        FileNotFound: the folder path did not exist.
    """
    elements = 0
    # raise error if path does not exist
    if not os.path.isdir(dir_path):
        raise FileNotFoundError
    for subdir, _dirs, files in os.walk(dir_path):
        for filename in files:
            filepath = subdir + os.sep + filename
            if filepath.endswith(".html"):
                elements += get_num_elements_in_file(el, filepath)
    return elements


def get_elements(el: str, file_path: str) -> list:
    """Returns a list of all Tag objects of type el from file path.

    Extracts all tags of type (el) from the filename (file_path) as
    a list of BeautifulSoup Tag ojects.

    Args:
        el: the name of a tag, but not in tag form (for example: p, ul,
            or div)
        file_path: relative path to an html document (relative to the
            project folder)

    Returns:
        num: the number of elements found in the document in integer form

    Raises:
        FileNotFound: the folder path did not exist.
    """
    with open(file_path, encoding="utf-8") as fp:
        soup = BeautifulSoup(fp, "html.parser")
        elements = soup.find_all(el)
    return elements


def get_element_content(el: Union[Tag, str]) -> str:
    """gets the content of element (el) as a string

    This function can accept a Tag (a BeautifulSoup object) or a string
    and returns the contents of the tag as a string.

    Args:
        el: the element can either be a Tag (preferred) or a string.

    Returns:
        content: the contents of the tag as a string. This is like
            .innerText() method in JavaScript.
    """
    # Convert to tag if it's a string
    if isinstance(el, str):
        el = string_to_tag(el)
    content = ""
    for i in el:
        content += str(i).replace("\n", "")
    return content


def string_to_tag(el: str) -> Tag:
    """Takes html markup as a string and returns a bs4 Tag object

    Args:
        el: HTML code in the form of a string. (example: '<h1>My Header</h1>')

    Returns:
        tag: A BeautifulSoup 4 Tag object

    Raises:
        ValueError: to get a tag object, the BeautifulSoup object must
            start with an opening tag. Without an opening tag, soup.find()
            will return a None type object.

    .. BeautifulSoup Tag Object:
        https://www.crummy.com/software/BeautifulSoup/bs4/doc/#tag
    """

    # raise ValueError if there is no opening tag at the beginning
    # of the string
    el = el.strip()
    match = re.search(STARTS_WITH_OPENING_TAG_RE, el)
    if not match:
        raise ValueError(f"{el} is not proper HTML.")

    # find the first element of the string
    start = el.index("<") + 1
    stop = el.index(">")
    tag_name = el[start:stop]
    if " " in tag_name:
        stop = tag_name.index(" ")
        tag_name = tag_name[:stop]

    # get the tag from the string using find()
    soup = BeautifulSoup(el, "html.parser")
    tag = soup.find(tag_name)
    return tag


def uses_inline_styles(markup: Union[Tag, str]) -> bool:
    """determines whether the markup uses inline styles or not as a
    boolean.

    Args:
        markup: the code in string or Tag form.

    Returns:
        has_inline_styles: boolean True if contains style attribute
            False if it does not contain style attribute.
    """
    tree = html.fromstring(markup)
    tags_with_inline_styles = tree.xpath("//@style")
    has_inline_styles = bool(tags_with_inline_styles)
    return has_inline_styles


if __name__ == "__main__":
    file_with_inline_styles = "tests/test_files/sample_with_inline_styles.html"
    markup = clerk.file_to_string(file_with_inline_styles)
    has_inline_styles = uses_inline_styles(markup)
    print(has_inline_styles)
