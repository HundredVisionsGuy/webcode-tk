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

from bs4 import BeautifulSoup
from file_clerk import clerk
from lxml import html


def get_html(file_path: str) -> BeautifulSoup:
    """Returns an html document (from file_path) as a BeautifulSoup object

    This function takes advantage of the bs4 library's `BeautifulSoup`
    datatype, also known as simply a soup object.

    Args:
        file_path: the file location (and filename as a relative link).

    Returns:
        soup: this is a BeautifulSoup object that represents an HTML tree
            or NoneType if there is a failure.

    .. Beautiful Soup Documentation:
        https://www.crummy.com/software/BeautifulSoup/bs4/doc/#making-the-soup
    """
    with open(file_path, encoding="utf-8") as fp:
        soup = BeautifulSoup(fp, "html.parser")
        return soup
    return None


def get_num_elements_in_file(el: str, file_path: str):
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
    return len(elements)


def get_num_elements_in_folder(el, dir_path):
    elements = 0
    for subdir, dirs, files in os.walk(dir_path):
        for filename in files:
            filepath = subdir + os.sep + filename
            if filepath.endswith(".html"):
                elements += get_num_elements_in_file(el, filepath)
    return elements


def get_elements(el, path):
    with open(path, encoding="utf-8") as fp:
        soup = BeautifulSoup(fp, "html.parser")
        elements = soup.find_all(el)
    return elements


def get_element_content(el):
    return el.get_text()


def uses_inline_styles(markup):
    tree = html.fromstring(markup)
    tags_with_inline_styles = tree.xpath("//@style")
    return bool(tags_with_inline_styles)


if __name__ == "__main__":
    file_with_inline_styles = "tests/test_files/sample_with_inline_styles.html"
    markup = clerk.file_to_string(file_with_inline_styles)
    has_inline_styles = uses_inline_styles(markup)
    print(has_inline_styles)
