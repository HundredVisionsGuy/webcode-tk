""" Cascade Tools
This module is a set of tools to determine CSS as applied through
inheritance and the cascade.

The goal is to use the DOM, inheritance, and the cascade, to determine
all styles applied to every element on the page.

With that, it scans each stylesheet and applies eacSh style one at a time
to all elements and their children (if applicable) of a page.
"""
from file_clerk import clerk

from webcode_tk import color_tools as color
from webcode_tk import css_tools as css
from webcode_tk import html_tools


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

    default_global_color = ("#FFFFFF",)
    default_global_background = "#000000"
    default_link_color = "#0000EE"
    default_link_visited = "#551A8B"

    def __init__(self, val=None, children=None) -> None:
        self.name = val
        self.attributes = []
        self.styles = []
        self.children = children if children is not None else []

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
                styles["color"] = Element.default_link_color
                styles["visited-color"] = Element.default_link_visited
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
                selector = list(ruleset.keys())[0]
                declaration = list(ruleset.values())[0]
                print(declaration)
                print(selector)
                prop, val = tuple(declaration.items())[0]
                print(prop)
                print(val)

    def __apply_global_colors(self, element, global_colors):
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


if __name__ == "__main__":

    project_path = "tests/test_files/single_file_project/"
    styles_by_html_files = css.get_styles_by_html_files(project_path)
    print(styles_by_html_files)
    for file in styles_by_html_files:
        filepath = file.get("file")
        sheets = file.get("stylesheets")
        css_tree = CSSAppliedTree(filepath, sheets)
        print(css_tree)
