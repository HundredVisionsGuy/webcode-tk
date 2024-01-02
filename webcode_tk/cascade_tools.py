""" Cascade Tools
This module is a set of tools to determine CSS as applied through
inheritance and the cascade.

The goal is to use the DOM, inheritance, and the cascade, to determine
all styles applied to every element on the page.

With that, it scans each stylesheet and applies eacSh style one at a time
to all elements and their children (if applicable) of a page.
"""
import re

from bs4 import Tag
from file_clerk import clerk

from webcode_tk import color_tools as color
from webcode_tk import css_tools as css
from webcode_tk import html_tools


default_global_color = "#FFFFFF"
default_global_background = "#000000"
default_link_color = "#0000EE"
default_link_visited = "#551A8B"


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
        self.parents = []

    def ammend_color_styles(self, new_styles: dict) -> None:
        """adjust color styles based on specificity"""
        # Make a copy of styles (being mutable and all)
        styles = new_styles.copy()
        # check first to make sure it's not a link
        is_a_link = False
        if self.name == "a":
            is_a_link = True
        if not self.styles:
            if is_a_link:
                # set the color to default blue
                styles["color"] = default_link_color
                styles["visited-color"] = default_link_visited
                hexc = color.get_hex(styles.get("color"))
                hexbg = color.get_hex(styles.get("background-color"))
                hexv = color.get_hex(styles.get("visited-color"))
                link_contrast = color.get_color_contrast_report(hexc, hexbg)
                link_ratio = color.contrast_ratio(hexc, hexbg)
                link_visited_contrast = color.get_color_contrast_report(
                    hexv, hexbg
                )
                visited_ratio = color.contrast_ratio(hexv, hexbg)
                styles["contrast_ratio"] = link_ratio
                styles["passes_normal_aaa"] = link_contrast.get("Normal AAA")
                styles["passes_normal_aa"] = link_contrast.get("Normal AA")
                styles["passes_large_aaa"] = link_contrast.get("Large AAA")
                styles["visited_contrast_ratio"] = visited_ratio
                styles["visited_normal_aaa"] = link_visited_contrast.get(
                    "Normal AAA"
                )
            self.styles = styles
        else:
            # check specificity
            specificity = self.styles.get("specificity")
            new_specificity = styles.get("specificity")
            if not specificity or new_specificity >= specificity:
                self.styles["specificity"] = new_specificity

                # no specificity, apply all possible styles
                bg = styles.get("background-color")

                # if it's a link, only change bg (not color)
                if is_a_link:
                    col = None
                else:
                    col = styles.get("color")
                if bg and col:
                    self.styles = styles
                else:
                    if bg:
                        self.styles["background-color"] = bg
                    if col:
                        self.styles["color"] = col


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
        stylesheets: list of all stylesheet objects applied to the
            page.
        root (Element): the root node of the document (the HTML
            element).
        children (list): a list of all child elements of the doc
            (minus the title tag).
    """

    def __init__(self, path: str, stylesheets: list):
        self.soup = None
        self.file_path = path
        self.stylesheets = stylesheets
        self.root = None
        self.children = []
        self.__get_filename()
        self.__get_soup(path)
        self.__build_tree()
        self.__apply_colors()

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
        attributes = body_soup.attrs
        if attributes:
            body.attributes = attributes
        body.parents = self.__get_parents(body_soup)
        children = body_soup.contents
        self.__get_children(body, children)

    def __get_children(self, element: Element, soup_contents: list):
        """gets all children of the element and their children from the soup"""
        contents = []
        for child in soup_contents:
            if isinstance(child, str):
                continue
            contents.append(child)
        for tag in contents:
            tag_name = tag.name
            tag_children = tag.contents
            new_element = Element(tag_name)
            new_element.parents = self.__get_parents(tag)
            if tag.attrs:
                new_element.attributes = tag.attrs
            element.children.append(new_element)
            self.__get_children(new_element, tag_children)
        return

    def __apply_colors(self) -> None:
        """applies all color rules to any elements targeted by styles.

        This includes by the cascade and by applying specificity. We'll
        loop through all color styles applied from the stylesheets.

        After all styles have been applied, do one last check to see
        if anything wasn't applied, and then apply the default colors."""
        for sheet in self.stylesheets:
            global_colors = css.get_global_color_details(sheet.rulesets)[0]
            body = self.children[0]
            self.__apply_global_colors(body, global_colors)
            color_rules = sheet.color_rulesets
            for ruleset in color_rules:
                self.__adjust_colors(body, ruleset)
                children = body.children
                for child in children:
                    self.__adjust_colors(child, ruleset)

    def __apply_global_colors(self, element: Element, global_colors) -> None:
        """recursively apply global colors to all elements
        except color on links (they remain default)

        base case is an element with no children"""
        # first apply styles with specificity
        selector = global_colors.get("selector")
        specificity = css.get_specificity(selector)
        global_colors["specificity"] = specificity
        element.ammend_color_styles(global_colors)

        # loop through all children and call
        children = element.children
        for child in children:
            self.__apply_global_colors(child, global_colors)
        return

    def __adjust_colors(self, element: Element, ruleset: dict) -> None:
        """recursively adjust color where necessary to all elements that
        apply.

        Args:
            element: the element in question.
            ruleset: the ruleset we want to apply"""
        selector = list(ruleset.keys())[0]

        # make sure the selector selects the element
        selector_applies = does_selector_apply(element, selector)
        if not selector_applies:
            return
        declaration = list(ruleset.values())[0]

        # Check specificity & override if necessary
        new_specificity = css.get_specificity(selector)
        old_specificity = element.styles.get("specificity")
        if new_specificity >= old_specificity:
            # get property and value
            new_prop, new_val = tuple(declaration.items())[0]

            # if they are different from current element
            el_val = element.styles.get(new_prop)
            if el_val != new_val:
                # loop through all children and adjust colors
                children = element.children
                for child in children:
                    self.__adjust_colors(child, ruleset)
        return

    def __get_parents(self, tag: Tag) -> list:
        """gets all parent tag names and possible selectors as dictionary
        objects.

        Args:
            element: the Element object (the one that will get the list of
            parents)
            tag: the bs4 tag object that contains the parent information

        Returns:
            parents: a list of parent tag information in the form of a
                dictionary."""
        parents = []
        for parent in tag.parents:
            details = {}
            if parent.name == "[document]":
                continue
            details["name"] = parent.name
            details["classes"] = parent.attrs.get("class")
            details["id"] = parent.attrs.get("id")
            parents.append(details)
        return parents


def does_selector_apply(element: Element, selector: str) -> bool:
    """returns whether the selector applies to the element.

    Since the selector could be a grouped selector, we might have to
    loop through all selectors in the grouped selector. For that reason,
    grouped selectors, will be converted to a list of selectors, and
    non-grouped selectors will be placed in a list.

    From there, we will loop through the list of selectors and check
    for type, class, id, and any other selectors in our list of regex
    expressions from the css library. With that information,
    we can then check to see if it applies to the tag or not.

    Args:
        element: the element we are checking.
        selector: the selector in question.
    Returns:
        applies: whether the selector actually applies to the element."""
    applies = False
    regex_patterns = css.regex_patterns

    # make a list of all selectors (in case of grouped selector)
    selectors = []
    is_grouped = bool(
        re.match(regex_patterns.get("grouped_selector"), selector)
    )
    if is_grouped:
        selectors = selector.split(",")
    else:
        selectors.append(selector)
    for sel in selectors:
        sel = sel.strip()
        is_type_selector = bool(
            re.match(regex_patterns.get("single_type_selector"), sel)
        )
        is_id_selector = bool(re.match(regex_patterns.get("id_selector"), sel))
        is_class_selector = bool(
            re.match(regex_patterns.get("class_selector"), sel)
        )
        is_psuedo_class_selector = bool(
            re.match(regex_patterns.get("pseudoclass_selector"), sel)
        )
        is_psuedo_class_selector = is_psuedo_class_selector or ":" in sel
        is_attribute_selector = bool(
            re.match(regex_patterns.get("attribute_selector"), sel)
        )
        if is_type_selector:
            applies = element.name == sel
            if applies:
                break
        elif is_id_selector:
            # get ID attribute (if there is one)
            print(element.attributes)
        elif is_class_selector:
            # get all class attributes
            attributes = element.attributes
            if attributes:
                print(attributes)
        elif is_psuedo_class_selector:
            # check for element before psuedoclass
            pre_pseudo = sel.split(":")[0]
            applies = selector == sel and pre_pseudo == element.name
            if applies:
                break
        elif is_attribute_selector:
            print("This must be an attribute selector")
        else:
            print("What is this?")
    return applies


if __name__ == "__main__":

    project_path = "tests/test_files/project_refactor_tests/"
    styles_by_html_files = css.get_styles_by_html_files(project_path)
    print(styles_by_html_files)
    for file in styles_by_html_files:
        filepath = file.get("file")
        sheets = file.get("stylesheets")
        css_tree = CSSAppliedTree(filepath, sheets)
        print(css_tree)
