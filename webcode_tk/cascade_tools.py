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
        self.styles = {
            "background-color": "#ffffff",
            "color": "#000000",
            "specificity": "000",
            "selector": "user-agent",
        }
        self.is_link = False
        if val == "a":
            self.is_link = True
            self.styles["color"] = default_link_color
            self.styles["visited-color"] = default_link_visited
        self.get_contrast_data(self.styles)
        self.children = children if children is not None else []
        self.parents = []

    def ammend_color_styles(self, new_styles: dict) -> None:
        """adjust color styles based on specificity"""
        # Make a copy of styles (being mutable and all)
        styles = new_styles.copy()
        # check first to see if it's a link
        if self.is_link:
            selector = new_styles.get("selector")
            is_link_selector = css.is_link_selector(selector)

            # if it is a link selector, we change
            if is_link_selector:
                print("Make sure we're doing this right")
                self.styles = new_styles
                self.get_contrast_data(styles)
        if not self.styles:
            if self.is_link:
                print("Yo")
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
                if self.is_link:
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

    def get_contrast_data(self, styles: dict) -> None:
        hexc = color.get_hex(styles.get("color"))
        hexbg = color.get_hex(styles.get("background-color"))
        link_contrast = color.get_color_contrast_report(hexc, hexbg)
        link_ratio = color.contrast_ratio(hexc, hexbg)
        styles["contrast_ratio"] = link_ratio
        styles["passes_normal_aaa"] = link_contrast.get("Normal AAA")
        styles["passes_normal_aa"] = link_contrast.get("Normal AA")
        styles["passes_large_aaa"] = link_contrast.get("Large AAA")
        visited_color = styles.get("visited_color")
        if visited_color:
            hexv = color.get_hex(styles.get("visited-color"))
            link_visited_contrast = color.get_color_contrast_report(
                hexv, hexbg
            )
            visited_ratio = color.contrast_ratio(hexv, hexbg)
            styles["visited_contrast_ratio"] = visited_ratio
            styles["visited_normal_aaa"] = link_visited_contrast.get(
                "Normal AAA"
            )


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
            if tag_name == "script":
                continue
            tag_children = tag.contents
            new_element = Element(tag_name)
            if tag.name != "a":
                new_element.styles = element.styles
            new_element.styles["specificity"] = "000"
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
        body = self.__set_global_colors()
        for sheet in self.stylesheets:
            color_rules = sheet.color_rulesets
            for ruleset in color_rules:
                if "body" in ruleset.keys():
                    print("We found a body selector")
                    continue
                self.__adjust_colors(body, ruleset)

    def __set_global_colors(self):
        for sheet in self.stylesheets:
            global_colors = css.get_global_color_details(sheet.rulesets)
            body = self.children[0]
            if global_colors:
                self.__apply_global_colors(body, global_colors)
        return body

    def __apply_global_colors(self, element: Element, global_colors) -> None:
        """recursively apply global colors to all elements
        except color on links (they remain default)

        base case is an element with no children"""
        # first apply styles with specificity
        if not isinstance(global_colors, list):
            global_colors = [global_colors]
        for gc in global_colors:
            selector = gc.get("selector")
            specificity = css.get_specificity(selector)
            gc["specificity"] = specificity
            element.ammend_color_styles(gc)

            # loop through all children and call
            children = element.children
            for child in children:
                self.__apply_global_colors(child, gc)
        return

    def __adjust_colors(self, element: Element, ruleset: dict) -> None:
        """recursively adjust color where necessary to all elements that
        apply.

        Args:
            element: the element in question.
            ruleset: the ruleset we want to apply"""
        # Adjust colors if necessary - if there was a change,
        # adjust colors for children
        selector = list(ruleset.keys())[0]
        selector_applies = does_selector_apply(element, selector)
        if selector_applies:
            declaration = ruleset.get(selector)
            new_specificity = css.get_specificity(selector)
            self.change_styles(element, selector, declaration, new_specificity)
        for child in element.children:
            self.__adjust_colors(child, ruleset)

    def change_styles(self, element, selector, declaration, new_specificity):
        element.styles["specificity"] = new_specificity

        # get property and value
        new_prop, new_val = tuple(declaration.items())[0]

        # if they are different from current element
        el_val = element.styles.get(new_prop)
        if el_val != new_val:
            # If psuedo-class selector
            # Adjust styles to match then break
            if is_selector_pseudoclass(selector):
                pseudo_key = selector + "-" + new_prop
                other_pseudo_key = selector + "-"
                if new_prop == "color":
                    other_pseudo_key += "background"
                    other_value = element.styles.get("background-color")
                else:
                    other_pseudo_key += "color"
                    other_value = element.styles.get("color")
                element.styles[pseudo_key] = new_val
                element.styles[other_pseudo_key] = other_value
                hex1 = color.get_hex(new_val)
                hex2 = color.get_hex(other_value)
                pseudo_report_key = selector + "-contrast"
                contrast_report = color.get_color_contrast_report(hex1, hex2)
                element.styles[pseudo_report_key] = contrast_report
                return
            # apply the new color
            element.styles[new_prop] = new_val

            # loop through all children and adjust colors
            children = element.children
            if children:
                for child in children:
                    change_children_colors(
                        child, new_specificity, selector, new_prop, new_val
                    )

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
        is_link_selector = bool(
            re.match(regex_patterns.get("advanced_link_selector"), sel)
            or selector == "a"
        )
        is_type_selector = bool(
            re.match(regex_patterns.get("single_type_selector"), sel)
        )
        is_id_selector = bool(re.match(regex_patterns.get("id_selector"), sel))
        is_class_selector = bool(
            re.match(regex_patterns.get("class_selector"), sel)
        )
        is_class_selector = is_class_selector or "." in sel
        is_psuedo_class_selector = is_selector_pseudoclass(sel)
        is_attribute_selector = bool(
            re.match(regex_patterns.get("single_attribute_selector"), sel)
        )
        is_descendant_selector = bool(
            re.match(regex_patterns.get("descendant_selector"), sel)
        )

        # If the tag is an anchor, but the selector is not - doesn't apply
        # link color can only be changed by a link selector
        if element.name == "a" and not is_link_selector:
            break
        elif is_type_selector:
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
                attribute_names = list(attributes.keys())
                for name in attribute_names:
                    if name == "class":
                        possible_selectors = []
                        class_values = attributes.get("class")
                        for val in class_values:
                            possible_selectors.append("." + val)
                            possible_selectors.append(element.name + "." + val)
                        if selector in possible_selectors:
                            applies = True
                            break
        elif is_psuedo_class_selector:
            # check for element before psuedoclass
            pre_pseudo = sel.split(":")[0]
            applies = pre_pseudo == element.name
            if applies:
                break
        elif is_attribute_selector:
            print("This must be an attribute selector")
        elif is_descendant_selector:
            items = sel.split()
            applies = items[-1] == element.name
            if applies:
                break
        else:
            print("What is this?")
    return applies


def is_selector_pseudoclass(selector: str) -> bool:
    """returns whether selector is a pseudoclass selector"""
    pc_regex = css.regex_patterns.get("pseudoclass_selector")
    is_psuedo_class_selector = bool(re.match(pc_regex, selector))
    is_psuedo_class_selector = is_psuedo_class_selector or ":" in selector
    return is_psuedo_class_selector


def change_children_colors(
    element: Element(), specificity: str, sel: str, prop: str, value: str
) -> None:
    """
    recursively change colors on all descendants.

    Args:
        element: the element
        specificity: the computed specificity
        sel: the selector used to change
        prop: the property we want to change (color or bg color)
        value: the value we will change it to
    """
    # Change property if selector works
    if element.styles:
        element_specificity = element.styles.get("specificity")
    else:
        element.styles = {}
        element_specificity = "000"
    if specificity >= element_specificity:
        element.styles[prop] = value
        element.styles["specificity"] = specificity
        element.styles["selector"] = sel
        kids = element.children
        if kids:
            for kid in kids:
                change_children_colors(kid, specificity, sel, prop, value)


if __name__ == "__main__":

    project_path = "tests/test_files/single_file_project/"
    styles_by_html_files = css.get_styles_by_html_files(project_path)
    for file in styles_by_html_files:
        filepath = file.get("file")
        sheets = file.get("stylesheets")
        css_tree = CSSAppliedTree(filepath, sheets)
        print(css_tree)
