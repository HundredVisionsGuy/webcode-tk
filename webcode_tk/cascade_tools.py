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
            "background-color": {
                "value": "#ffffff",
                "sheet": "user-agent",
                "selector": "",
                "specificity": "000",
            },
            "color": {
                "value": "#000000",
                "sheet": "user-agent",
                "selector": "",
                "specificity": "000",
            },
            "visited-color": {
                "value": "",
                "sheet": "",
                "selector": "",
                "specificity": "",
            },
        }
        self.is_link = False
        self.contrast_data = {}
        if val == "a":
            self.is_link = True
            self.styles.get("color")["value"] = default_link_color
            self.styles.get("visited-color")["value"] = default_link_visited
        self.get_contrast_data(self.styles)
        self.children = children if children is not None else []
        self.parents = []

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

    def get_contrast_data(self, styles: dict) -> None:
        col = styles.get("color")
        col = col.get("value")
        bg = styles.get("background-color")
        bg = bg.get("value")
        if isinstance(col, dict) or isinstance(bg, dict):
            print("Here's the problem")
        hexc = color.get_hex(col)
        hexbg = color.get_hex(bg)
        contrast_report = self.__build_contrast_report(hexc, hexbg)
        for property, data in styles.items():
            if property == "background-color" or property == "color":
                data["contrast_data"] = contrast_report
            else:
                visited_color = data.get("value")
                if visited_color:
                    if isinstance(styles.get("visited-color")["value"], dict):
                        print("Here's the problem")
                    hexv = color.get_hex(styles.get("visited-color")["value"])
                    contrast_report = self.__build_contrast_report(hexv, hexbg)
                    styles["visited-color"]["contrast_data"] = contrast_report

    def __build_contrast_report(self, hexc, hexbg):
        link_contrast = color.get_color_contrast_report(hexc, hexbg)
        link_ratio = color.contrast_ratio(hexc, hexbg)
        contrast_data = {}
        contrast_data["contrast_ratio"] = link_ratio
        contrast_data["passes_normal_aaa"] = link_contrast.get("Normal AAA")
        contrast_data["passes_normal_aa"] = link_contrast.get("Normal AA")
        contrast_data["passes_large_aaa"] = link_contrast.get("Large AAA")
        return contrast_data


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
        selector_applies = does_selector_apply(element, selector)
        if selector_applies:
            declaration = ruleset.get(selector)
            new_specificity = css.get_specificity(selector)
            self.change_styles(
                element, selector, declaration, new_specificity, filename
            )
        for child in element.children:
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
                property = element.styles[new_prop]
                property["value"] = new_val
                property["sheet"] = filename
                property["selector"] = selector
                property["specificity"] = new_specificity
                adjust_color_contrast(element, new_prop, new_val)

            # loop through all children and adjust colors
            children = element.children
            if children:
                for child in children:
                    change_children_colors(
                        child,
                        new_specificity,
                        selector,
                        new_prop,
                        new_val,
                        filename,
                    )

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
    recursively change colors on all descendants.

    Args:
        element: the element
        specificity: the computed specificity
        sel: the selector used to change
        prop: the property we want to change (color or bg color)
        value: the value we will change it to
    """
    # Get the element property we want to change
    element_property = element.styles[prop]

    # Change property if selector works
    if element.styles:
        element_specificity = element_property.get("specificity")
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
            adjust_color_contrast(element, prop, value)
        kids = element.children
        if kids:
            for kid in kids:
                change_children_colors(
                    kid, specificity, sel, prop, value, filename
                )


def adjust_color_contrast(element, new_prop, new_val):
    if isinstance(new_val, dict):
        print("Here's the problem")
    hex1 = color.get_hex(new_val)
    if new_prop == "background" or new_prop == "background-color":
        hex2 = element.styles["color"].get("value")
    elif new_prop == "color":
        hex2 = element.styles["background-color"].get("value")
    else:
        print("What the heck is this?")
    if isinstance(hex2, dict):
        print("Here's the problem")
    hex2 = color.get_hex(hex2)
    contrast_report = color.get_color_contrast_report(hex1, hex2)
    passes_normal_aaa = contrast_report.get("Normal AAA")
    passes_normal_aa = contrast_report.get("Normal AA")
    passes_large_aaa = contrast_report.get("Large AAA")
    ratio = color.contrast_ratio(hex1, hex2)
    element_property = element.styles[new_prop]
    contrast_data = element_property["contrast_data"]
    contrast_data["contrast_ratio"] = ratio
    contrast_data["passes_normal_aaa"] = passes_normal_aaa
    contrast_data["passes_normal_aa"] = passes_normal_aa
    contrast_data["passes_large_aaa"] = passes_large_aaa


if __name__ == "__main__":
    project_path = "tests/test_files/single_file_project/"
    styles_by_html_files = css.get_styles_by_html_files(project_path)
    for file in styles_by_html_files:
        filepath = file.get("file")
        sheets = file.get("stylesheets")
        css_tree = CSSAppliedTree(filepath, sheets)
        print(css_tree)
