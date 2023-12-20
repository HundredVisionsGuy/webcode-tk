""" Cascade Tools
This module is a set of tools to determine CSS as applied through
inheritance and the cascade.

The goal is to use the DOM, inheritance, and the cascade, to determine
all styles applied to every element on the page.

With that, it scans each stylesheet and applies eacSh style one at a time
to all elements and their children (if applicable) of a page.
"""
from typing import Type

from file_clerk import clerk

from webcode_tk import html_tools

NavigableString = Type["NavigableString"]


class Element(object):
    """an element object for each tag in a web page

    This will be used by the CSSAppliedTree to represent
    the DOM of a web page and will contain the computed
    CSS styles based on the styesheet.

    Attribues:
        name (str): name of the element.
        attributes (list): a list of attributes as dictionries.
        styles (list): a list of computed styles in key-value pairs.
        children (list): any Elements nested in the tag.
    """

    def __init__(self, val=None, children=None) -> None:
        self.name = val
        self.attributes = []
        self.styles = []
        self.children = children if children is not None else []


class CSSAppliedTree:
    """a tree of an HTML document with all styles applied.

    The point is to identify every element and the styles
    applied to that element based on inheritance and
    specificity rules (like you would see in the inspector)

    We'll use an Element object for storing the tree.
    Each node is an element (starting at HTML) and a optionally
    a list of attributes as individual key value pairs.
    Each node has 1 or more children (their nested elements).

    In addition, each node has a list of computed rules.

    Attributes:
        soup (BeautifulSoup): a bs4 object representing the page
        file_path (str): path to the file as a string.
        filename: name of file as a string.
    """

    def __init__(self, path: str):
        self.soup = None
        self.file_path = path
        self.root = None
        self.children = []
        self.__get_filename()
        self.__get_soup(path)
        self.__build_tree()

    def __get_soup(self, path: str):
        """Gets bs4 soup from the file path"""
        self.soup = html_tools.get_html(path)

    def __get_filename(self):
        """Extracts filename from path"""
        self.filename = clerk.get_file_name(self.file_path)

    def __build_tree(self) -> None:
        """Constructs initial tree (recursively?)"""
        # Start with the body element, and divide and conquer
        root = Element("html")
        self.root = root
        body = Element("body")
        body.styles = {"background-color": "#ffffff", "color": "#000000"}
        self.children.append(body)
        body_soup = self.soup.body
        children = body_soup.contents
        self.get_children(body, children)

    def get_children(self, element: Element, soup_contents: list):
        contents = []
        for child in soup_contents:
            if isinstance(child, str):
                continue
            contents.append(child)
        for tag in contents:
            tag_name = tag.name
            tag_children = tag.contents
            new_element = Element(tag_name)
            element.children.append(new_element)
            self.get_children(new_element, tag_children)
        return

    def __add_children(self, element: Element) -> None:
        pass


if __name__ == "__main__":
    from webcode_tk import css_tools as css

    project_path = "tests/test_files/single_file_project/"
    styles_by_html_files = css.get_styles_by_html_files(project_path)
    print(styles_by_html_files)
    for file in styles_by_html_files:
        filepath = file.get("file")
        css_tree = CSSAppliedTree(filepath)
        print(css_tree)
