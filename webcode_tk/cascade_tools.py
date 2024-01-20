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

    def __init__(self, name=None, children=None) -> None:
        self.name = name
        self.attributes = []
        self.background_color = {
            "value": "#ffffff",
            "sheet": "user-agent",
            "selector": "",
            "specificity": "000",
        }
        self.color = {
            "value": "#000000",
            "sheet": "user-agent",
            "selector": "",
            "specificity": "000",
        }
        self.visited_color = {
            "value": "",
            "sheet": "",
            "selector": "",
            "specificity": "",
        }
        self.is_link = bool(name == "a")
        self.contrast_data = {
            "ratio": 21.0,
            "normal_aaa": True,
            "normal_aa": True,
            "large_aaa": True,
        }
        self.visited_contrast_data = {
            "ratio": 0.0,
            "normal_aaa": False,
            "normal_aa": False,
            "large_aaa": False,
        }
        self.__set_link_color()
        self.get_contrast_data()
        self.children = children if children is not None else []
        self.parents = []

    def __set_link_color(self):
        if self.name == "a":
            self.color["value"] = default_link_color
            self.visited_color["value"] = default_link_visited

    def ammend_color_styles(self, new_styles: dict, filename: str) -> None:
        """adjust color styles based on specificity.

        Args:
            new_styles: the new styles we want to apply.
            filename: the stylesheet the styles came from."""
        # Make a copy of styles (being mutable and all)
        styles = new_styles.copy()

        # check specificity
        specificity = self.styles.get("specificity")
        new_specificity = styles.get("specificity")
        if not specificity or new_specificity >= specificity:
            background_value = styles.get("background-color")
            if not background_value:
                background_value = self.styles["background-color"].get("value")
            color_value = styles.get("color")
            selector = styles.get("selector")
            is_link_selector = css.is_link_selector(selector)

            # apply background color data (if present)
            background = self.styles["background-color"]
            if background_value:
                background["value"] = background_value
                background["selector"] = selector
                background["specificity"] = new_specificity
                background["sheet"] = filename

            # apply color data (if we are allowed to change color)
            # to qualify, there must first be a color value.
            # if that's so, then it either must not be a link
            # or if it is a link there must also be a link selector
            can_apply_color = (
                color_value
                and self.name != "a"
                or (self.name == "a" and is_link_selector)
            )
            col = self.styles["color"]
            if can_apply_color:
                col["value"] = color_value
                col["selector"] = selector
                col["specificity"] = new_specificity
                col["sheet"] = filename
            else:
                if not color_value:
                    # there was not a color value applied
                    color_value = self.styles["color"].get("value")
            # apply color contrast data to bg and color
            if isinstance(background_value, dict):
                print("Here's the problem")
            hexbg = color.get_hex(background_value)
            if isinstance(color_value, dict):
                print("Here's the problem")
            hexcol = color.get_hex(color_value)
            contrast_data = self.__build_contrast_report(hexbg, hexcol)
            background["contrast_data"] = contrast_data
            col["contrast_data"] = contrast_data

    def get_contrast_data(self) -> None:
        col = self.color.get("value")
        bg = self.background_color.get("value")
        hexc = color.get_hex(col)
        hexbg = color.get_hex(bg)
        self.__build_contrast_report(hexc, hexbg)
        if self.name == "a":
            vcol = self.visited_color.get("value")
            if not vcol:
                vcol = default_link_visited
            hexv = color.get_hex(vcol)
            self.__build_visited_contrast_report(hexv, hexbg)

    def __build_contrast_report(self, hexc, hexbg):
        link_contrast = color.get_color_contrast_report(hexc, hexbg)
        link_ratio = color.contrast_ratio(hexc, hexbg)

        self.contrast_data["ratio"] = link_ratio
        self.contrast_data["normal_aaa"] = bool(
            link_contrast.get("Normal AAA") == "Pass"
        )
        self.contrast_data["normal_aa"] = bool(
            link_contrast.get("Normal AA") == "Pass"
        )
        self.contrast_data["large_aaa"] = bool(
            link_contrast.get("Large AAA") == "Pass"
        )

    def __build_visited_contrast_report(self, hexc, hexbg):
        link_contrast = color.get_color_contrast_report(hexc, hexbg)
        link_ratio = color.contrast_ratio(hexc, hexbg)

        self.visited_contrast_data["ratio"] = link_ratio
        self.visited_contrast_data["normal_aaa"] = bool(
            link_contrast.get("Normal AAA") == "Pass"
        )
        self.visited_contrast_data["normal_aa"] = bool(
            link_contrast.get("Normal AA") == "Pass"
        )
        self.visited_contrast_data["large_aaa"] = bool(
            link_contrast.get("Large AAA") == "Pass"
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

            element.children.append(new_element)
            for tag in tag_children:
                if tag and not isinstance(tag, str):
                    their_kids = tag.contents
                    kid_element = Element(tag.name)
                    new_element.children.append(kid_element)
                    self.__get_children(kid_element, their_kids)
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
                # only adjust colors if the selector doesn't target body
                body_in_ruleset = self.targets_body(ruleset)
                if body_in_ruleset:
                    continue

                # get filename
                filename = clerk.get_file_name(sheet.href)
                self.__adjust_colors(body, ruleset, filename)

    def targets_body(self, ruleset):
        body_in_ruleset = False
        for selector in list(ruleset.keys()):
            if "body" in selector:
                body_in_ruleset = True
        return body_in_ruleset

    def __set_global_colors(self):
        body = None
        for sheet in self.stylesheets:
            global_colors = css.get_global_color_details(sheet.rulesets)
            body = self.children[0]
            filename = clerk.get_file_name(sheet.href)
            if global_colors:
                self.__apply_global_colors(body, global_colors, filename)
        return body

    def __apply_global_colors(
        self, element: Element, global_colors: list, filename="user-agent"
    ) -> None:
        """recursively apply global colors to all elements
        except color on links (they remain default)

        base case is an element with no children

        Args:
            element: the tag we are applying colors to.
            global_colors: a list of global color data.
            filename: the stylesheet where the global styles come from."""
        # first apply styles with specificity
        if not isinstance(global_colors, list):
            global_colors = [global_colors]
        for gc in global_colors:
            selector = gc.get("selector")
            specificity = css.get_specificity(selector)
            gc["specificity"] = specificity
            element.ammend_color_styles(gc, filename)

            # loop through all children and call
            children = element.children
            for child in children:
                self.__apply_global_colors(child, gc)
        return

    def __adjust_colors(
        self, element: Element, ruleset: dict, filename: str
    ) -> None:
        """recursively adjust color where necessary to all elements that
        apply.

        Args:
            element: the element in question.
            ruleset: the ruleset we want to apply.
            filename: the file where the styles came from."""
        # Adjust colors if necessary - if there was a change,
        # adjust colors for children
        selector = list(ruleset.keys())[0]
        if selector == "nav.primary-nav":
            print("Now is the time to check. Something is mutating.")
        selector_applies = does_selector_apply(element, selector)
        if selector_applies:
            declaration = ruleset.get(selector)
            new_specificity = css.get_specificity(selector)
            self.change_styles(
                element, selector, declaration, new_specificity, filename
            )
        for child in element.children:
            if child.name == "header":
                print("check it out.")
            self.__adjust_colors(child, ruleset, filename)

    def change_styles(
        self,
        element: Element,
        selector: str,
        declaration: str,
        new_specificity: str,
        filename: str,
    ) -> None:
        """changes styles for the element and recalculate all contrast data

        Args:
            element: the tag we want to change.
            selector: the selector being used.
            declaration: the declaration (property and value to change).
            new_specificity: the specificity of the selector.
            filename: the file where the changes come from.
        """
        selector_is_pseudoclass = is_selector_pseudoclass(selector)

        # get property and value
        new_prop, new_val = tuple(declaration.items())[0]

        # if they are different from current element
        if new_prop == "background":
            new_prop = "background-color"
        el_val = element.styles.get(new_prop).get("value")
        if el_val != new_val:
            # If psuedo-class selector
            # Adjust styles to match then break
            if selector_is_pseudoclass:
                pseudo_key = selector + "-" + new_prop
                other_pseudo_key = selector + "-"

                # get all the data for the property not being changed
                if new_prop == "color":
                    other_pseudo_key += "background"
                    other_styles = element.styles.get("background-color")
                else:
                    other_pseudo_key += "color"
                    other_styles = element.styles.get("color")
                other_value = other_styles.get("value")
                other_sheet = other_styles.get("sheet")
                other_selector = other_styles.get("selector")
                other_specificity = other_styles.get("specificity")

                # Set all the new data
                element.styles[pseudo_key] = {}
                new_pseudo_styles = element.styles[pseudo_key]
                new_pseudo_styles["value"] = new_val
                new_pseudo_styles["sheet"] = filename
                new_pseudo_styles["selector"] = selector
                new_pseudo_styles["specificity"] = new_specificity
                new_pseudo_styles["contrast_data"] = {}

                # Set all the other data
                element.styles[other_pseudo_key] = {}
                other_pseudo_styles = element.styles[other_pseudo_key]
                other_pseudo_styles["value"] = other_value
                other_pseudo_styles["sheet"] = other_sheet
                other_pseudo_styles["selector"] = other_selector
                other_pseudo_styles["specificity"] = other_specificity
                other_pseudo_styles["contrast_data"] = {}

                # Calculate contrast data
                hex1 = color.get_hex(new_val)
                hex2 = color.get_hex(other_value)
                contrast_report = color.get_color_contrast_report(hex1, hex2)
                new_contrast = new_pseudo_styles["contrast_data"]
                other_contrast = other_pseudo_styles["contrast_data"]

                # Extract contrast data
                self.set_contrast_data(
                    hex1, hex2, contrast_report, new_contrast
                )
                self.set_contrast_data(
                    hex1, hex2, contrast_report, other_contrast
                )
            else:
                # apply the new color, selector, and check contrast
                new_styles = {}
                new_styles["value"] = new_val
                new_styles["sheet"] = filename
                new_styles["selector"] = selector
                new_styles["specificity"] = new_specificity
                element.styles[new_prop] = new_styles
                old_prop = "color"
                if new_prop == "color":
                    old_prop = "background-" + old_prop
                old_val = element.styles[old_prop].get("value")
                new_contrast = adjust_color_contrast(
                    new_prop, new_val, old_prop, old_val
                )
                element.styles[new_prop]["contrast_data"] = new_contrast
                element.styles[old_prop]["contrast_data"] = new_contrast
            # loop through all children and adjust colors
            children = element.children
            if children:
                for child in children:
                    child_styles = child.styles.copy()
                    is_link = child.is_link
                    new_styles = get_new_styles(
                        child_styles,
                        is_link,
                        new_specificity,
                        selector,
                        new_prop,
                        new_val,
                        filename,
                    )
                    child.styles = new_styles

    def set_contrast_data(self, hex1, hex2, contrast_report, new_contrast):
        passes_normal_aaa = contrast_report.get("Normal AAA")
        passes_normal_aa = contrast_report.get("Normal AA")
        passes_large_aaa = contrast_report.get("Large AAA")
        contrast_ratio = color.contrast_ratio(hex1, hex2)

        # Set contrast data
        new_contrast["contrast_ratio"] = contrast_ratio
        new_contrast["passes_normal_aaa"] = passes_normal_aaa
        new_contrast["passes_normal_aa"] = passes_normal_aa
        new_contrast["passes_large_aaa"] = passes_large_aaa

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
            # TODO: adjust for attribute selectors
            print("This must be an attribute selector")
        elif is_descendant_selector:
            items = sel.split()
            applies = items[-1] == element.name
            if applies:
                break
        else:
            raise ValueError(f"Selector not recognized: Got {selector}")
    return applies


def is_selector_pseudoclass(selector: str) -> bool:
    """returns whether selector is a pseudoclass selector"""
    pc_regex = css.regex_patterns.get("pseudoclass_selector")
    is_psuedo_class_selector = bool(re.match(pc_regex, selector))
    is_psuedo_class_selector = is_psuedo_class_selector or ":" in selector
    return is_psuedo_class_selector


def change_children_colors(
    element: Element(),
    specificity: str,
    sel: str,
    prop: str,
    value: str,
    filename: str,
) -> None:
    """
    recursively change colors on all descendants (if they apply).

    Args:
        element: the element
        specificity: the computed specificity
        sel: the selector used to change
        prop: the property we want to change (color or bg color)
        value: the value we will change it to
    """
    # Get the element property we want to change
    element_property = {}

    # Change property if selector works
    if element.styles:
        element_specificity = element.styles[prop].get("specificity")
    else:
        element_specificity = "000"
        print("Delete this else block if never runs.")
    if specificity >= element_specificity:
        link_selector = css.is_link_selector(sel)
        if not element.is_link and not link_selector:
            element_property["value"] = value
            element_property["sheet"] = filename
            element_property["specificity"] = specificity
            element_property["selector"] = sel
            element.styles[prop] = element_property
            other_prop = "color"
            if prop == "color":
                other_prop = "background-" + other_prop
            other_val = element.styles[other_prop].get("value")
            new_contrast = adjust_color_contrast(
                prop, value, other_prop, other_val
            )
            element.styles[prop]["contrast_data"] = new_contrast
            element.styles[other_prop]["contrast_data"] = new_contrast
        kids = element.children
        if kids:
            for kid in kids:
                change_children_colors(
                    kid, specificity, sel, prop, value, filename
                )


def get_new_styles(
    old_styles: dict,
    is_link: bool,
    specificity: str,
    sel: str,
    prop: str,
    value: str,
    filename: str,
) -> dict:
    """
    get new styles if they can be changed

    Args:
        old_styles: the styles from the element in question
        specificity: the computed specificity
        sel: the selector used to change
        prop: the property we want to change (color or bg color)
        value: the value we will change it to

    Returns:
        new_styles: either the adjusted styles or the old styles.
    """
    # Get the element property we want to change
    new_styles = {prop: {}}

    # Change property if selector works
    element_specificity = old_styles[prop].get("specificity")
    if specificity >= element_specificity:
        link_selector = css.is_link_selector(sel)
        if not is_link and not link_selector:
            new_styles[prop]["value"] = value
            new_styles[prop]["sheet"] = filename
            new_styles[prop]["specificity"] = specificity
            new_styles[prop]["selector"] = sel

            other_prop = "color"
            if prop == "color":
                other_prop = "background-" + other_prop
            other_val = old_styles[other_prop].get("value")
            new_contrast = adjust_color_contrast(
                prop, value, other_prop, other_val
            )
            new_styles[prop]["contrast_data"] = new_contrast
            new_styles[other_prop] = {}
            new_styles[other_prop]["contrast_data"] = new_contrast
            for prop_key in list(old_styles.keys()):
                if prop_key not in list(new_styles.keys()):
                    new_styles[prop_key] = {}
                    vals = old_styles[prop_key]
                    new_styles[prop_key] = vals
        else:
            return old_styles
    return new_styles


def adjust_color_contrast(new_prop, new_val, old_prop, old_val):
    hex1 = color.get_hex(new_val)
    hex2 = color.get_hex(old_val)
    contrast_report = color.get_color_contrast_report(hex1, hex2)
    passes_normal_aaa = contrast_report.get("Normal AAA")
    passes_normal_aa = contrast_report.get("Normal AA")
    passes_large_aaa = contrast_report.get("Large AAA")
    ratio = color.contrast_ratio(hex1, hex2)

    contrast_data = {}
    contrast_data["contrast_ratio"] = ratio
    contrast_data["passes_normal_aaa"] = passes_normal_aaa
    contrast_data["passes_normal_aa"] = passes_normal_aa
    contrast_data["passes_large_aaa"] = passes_large_aaa
    return contrast_data


if __name__ == "__main__":
    project_path = "tests/test_files/single_file_project/"
    project_path = "tests/test_files/large_project/"
    styles_by_html_files = css.get_styles_by_html_files(project_path)
    for file in styles_by_html_files:
        filepath = file.get("file")
        sheets = file.get("stylesheets")
        css_tree = CSSAppliedTree(filepath, sheets)
        print(css_tree)
