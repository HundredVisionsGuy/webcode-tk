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
            "applied_by": "default",
        }
        self.color = {
            "value": "#000000",
            "sheet": "user-agent",
            "selector": "",
            "specificity": "000",
            "applied_by": "default",
        }
        self.visited_color = {
            "value": "",
            "sheet": "",
            "selector": "",
            "specificity": "",
            "applied_by": "default",
        }
        self.hover_color = {
            "value": "",
            "sheet": "",
            "selector": "",
            "specificity": "",
            "applied_by": "default",
        }
        self.hover_background = {
            "value": "",
            "sheet": "",
            "selector": "",
            "specificity": "",
            "applied_by": "default",
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
        # check specificity
        new_specificity = new_styles.get("specificity")
        col_specificity = self.color.get("specificity")
        bg_specificity = self.background_color.get("specificity")

        # change color if applies
        selector = new_styles.get("selector")
        selector_applies = self.name != "a"
        if selector_applies:
            hover_selector = ":hover" in selector
            if hover_selector:
                print("Create a new method to deal")
            else:
                if new_specificity >= col_specificity:
                    col = new_styles.get("color")
                    if col:
                        self.color["value"] = col
                        self.color["sheet"] = filename
                        self.color["selector"] = selector
                        self.color["specificity"] = new_specificity
                else:
                    col = self.color.get("value")
                if new_specificity >= bg_specificity:
                    bg_color = new_styles.get("background-color")
                    if bg_color:
                        self.background_color["value"] = bg_color
                        self.background_color["sheet"] = filename
                        self.background_color["selector"] = selector
                        self.background_color["specificity"] = new_specificity
                else:
                    bg_color = self.background_color.get("value")

                # get contrast for color & bg_color
                self.get_contrast_data()

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

    def change_styles(
        self,
        selector: str,
        declaration: str,
        new_specificity: str,
        filename: str,
    ) -> None:
        """change styles and apply them to all descendants

        Args:
            selector: the selector used to make a change
            declaration: the declaration (property and value)
            new_specificity: the specificity value of the selector
            filename: file where the styles come from."""
        if self.name == "a":
            print("What's up?")
        if self.name == "p":
            print("Let's follow up with the children")
        hover_selector = "a:hover" in selector

        for property, val in list(declaration.items()):
            if hover_selector:
                (prop,) = declaration
                val = declaration.get(prop)
                if "background" in prop:
                    specificity = self.hover_background.get("specificity")
                    if not specificity or new_specificity >= specificity:
                        self.hover_background["value"] = val
                        self.hover_background["sheet"] = filename
                        self.hover_background["selector"] = selector
                        self.hover_background["specificity"] = new_specificity
                        self.hover_background["applied_by"] = (
                            "selector: " + selector
                        )
                else:
                    specificity = self.hover_color.get("specificity")
                    if not specificity or new_specificity >= specificity:
                        self.hover_color["value"] = val
                        self.hover_color["sheet"] = filename
                        self.hover_color["selector"] = selector
                        self.hover_color["specificity"] = new_specificity
                        self.hover_color["applied_by"] = (
                            "selector: " + selector
                        )
            elif property == "background" or property == "background-color":
                old_specificity = self.background_color.get("specificity")
                if new_specificity >= old_specificity:
                    self.background_color["value"] = val
                    self.background_color["sheet"] = filename
                    self.background_color["selector"] = selector
                    self.background_color["specificity"] = new_specificity
            elif property == "color":
                old_specificity = self.color.get("specificity")
                if new_specificity >= old_specificity:
                    self.color["value"] = val
                    self.color["sheet"] = filename
                    self.color["selector"] = selector
                    self.color["specificity"] = new_specificity
            if not hover_selector:
                self.get_contrast_data()
            for child in self.children:
                if child.name == "td":
                    print("did we get this?")
                child.change_child_styles(
                    selector, property, val, new_specificity, filename
                )

    def change_child_styles(
        self,
        selector: str,
        property: str,
        val: str,
        new_specificity: str,
        filename: str,
    ) -> None:
        """changes child styles based on inheritance.

        Styles were changed by an ancestor, so we are passing down styles
        through inheritance, and so we must only change styles if they weren't
        already set directly.

        Args:
            selector: selector being used.
            property: property being passed down.
            val: value being passed down
            new_specificity: in case it matters (selector should also be
                targetting in some way).
            filename: the file where the styles came from.
        """
        if self.name == "td":
            print("What's up?")

        # has the element already had same property targetted previously?
        already_applied = self.been_applied(property)
        if already_applied:
            return

        # If it's a link, it shouldn't be applied unless it's a link selector
        if self.name == "a":
            link_selector = css.is_link_selector(selector)
            if not link_selector:
                return

        # is the selector targetting the tag directly (by type, id, or class)
        targets_directly = does_selector_apply(self, selector)

        # if it targets directly, then look to specificity
        if targets_directly:
            if "background" in property:
                old_specificity = self.background_color.get("specificity")
            else:
                old_specificity = self.color.get("specificity")
            if old_specificity > new_specificity:
                # new specificity loses - nothing to add here
                return

        # Apply the styles
        if "background" in property:
            self.background_color["value"] = val
            self.background_color["sheet"] = filename
            if targets_directly:
                self.background_color["selector"] = selector
                self.background_color["specificity"] = new_specificity
                self.background_color["applied_by"] = "selector: " + selector
            else:
                self.background_color["applied_by"] = "inheritance"
        else:
            self.color["value"] = val
            self.color["sheet"] = filename
            if targets_directly:
                self.color["selector"] = selector
                self.color["specificity"] = new_specificity
                self.color["applied_by"] = "selector: " + selector
            else:
                self.color["applied_by"] = "inheritance"

    def directly_targets(self, selector: str) -> bool:
        """returns whether selector directly targets tag.

        Checks all possible selector types

        Args:
            selector: the selector in question.

        Returns:
            targets: a boolean value (does the selector target the tag?)"""
        targets = False
        if selector == self.name:
            targets = True
        return targets

    def been_applied(self, property: str) -> bool:
        """has this property already had a style directly applied?

        Args:
            property: the property in question.

        Returns:
            applied: whether it has had a style applied or not."""
        applied = False
        if "background" in property:
            applied_by = self.background_color.get("applied_by")

        else:
            applied_by = self.color.get("applied_by")
        if applied_by not in ["default", "inheritance"]:
            applied = True
        return applied


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
                rule_keys = list(ruleset.keys())
                if body_in_ruleset and "body#image-gallery" not in rule_keys:
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

        Step 1: recursively search through children until we find an
        element where the selector applies (both by selector and by
        specificity).

        Step 2: if we find a selector that applies, apply changes to
        element AND all children that have same or lower specificity
        except a link (unless the selector is a link)

        Args:
            element: the element in question.
            ruleset: the ruleset we want to apply.
            filename: the file where the styles came from."""
        # Adjust colors if necessary - if there was a change,
        # adjust colors for children
        selector = list(ruleset.keys())[0]
        if selector in ["a:hover", "h1, h2, h3, h4"]:
            print("Now is the time to check. Something is mutating.")

        # does the selector apply to the element?
        selector_applies = False
        specificity = css.get_specificity(selector)
        declaration = list(ruleset.values())[0]
        property = list(declaration.keys())[0]
        is_background_prop = "background" in property
        if is_background_prop:
            old_specificity = element.background_color.get("specificity")
        else:
            old_specificity = element.color.get("specificity")
        applies = does_selector_apply(element, selector)
        selector_applies = (specificity >= old_specificity) and applies
        if selector_applies:
            for child in element.children:
                self.__adjust_child_colors(child, ruleset, filename)

        # --------- Stopped here --------- #

        can_inherit = can_inherit_styles(element, selector, ruleset)
        if can_inherit:
            declaration = ruleset.get(selector)
            new_specificity = css.get_specificity(selector)
            element.change_styles(
                selector, declaration.copy(), new_specificity, filename
            )
        for child in element.children:
            child_name = child.name
            if selector in ["h1, h2, h3, h4", "table"] and child_name == "td":
                print("Check it out.")
            if child_name == "td" and selector not in [
                "tr",
                "th",
                "td",
                "a",
                "a:hover",
            ]:
                print("check it out.")
            self.__adjust_colors(child, ruleset, filename)

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

    def __adjust_child_colors(
        self, child: Element, ruleset: dict, filename: str
    ) -> None:
        """adjusts colors for child of an element.

        A parent element already had styles applied, so we only need to check
        to see if the child element is a link or not (as well as the selector)
        and check the specificity of the ruleset.

        Args:
            child: the child element in question
            ruleset: the CSS rule being applied
            filename: name of the file where the styles came from
        """
        # Adjust colors if necessary - if there was a change,
        # adjust colors for children
        selector = list(ruleset.keys())[0]
        is_link_selector = css.is_link_selector(selector)
        element_name = child.name
        can_inherit = (
            is_link_selector
            and element_name == "a"
            or not is_link_selector
            and element_name != "a"
        )
        if can_inherit:
            declaration = ruleset.get(selector)
            new_specificity = css.get_specificity(selector)
            child.change_styles(
                selector, declaration.copy(), new_specificity, filename
            )
        for kid in child.children:
            self.__adjust_child_colors(kid, ruleset, filename)


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
    element_name = element.name
    if element_name == "td" and selector == "body":
        print("This should be applied")
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
        if element_name == "a" and not is_link_selector:
            break
        elif is_type_selector:
            applies = element_name == sel
            if applies:
                break
        elif is_id_selector:
            # get ID attribute (if there is one)
            possible_el, id_attr = selector.split("#")
            if element.attributes:
                element_id = element.attributes.get("id")
                if possible_el:
                    applies = (
                        possible_el == element_name and id_attr == element_id
                    )
                else:
                    applies = id_attr == element_id
                if applies:
                    break
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
                            possible_selectors.append(element_name + "." + val)
                        if selector in possible_selectors:
                            applies = True
                            break
        elif is_link_selector:
            # If the selector is a link selector, but the element is not
            # NOTE: if this doesn't solve it, we should double check the
            # parent to see if it was a link (might already be taken care of)
            if element_name == "a":
                applies = True
            break
        elif is_psuedo_class_selector:
            # check for element before psuedoclass
            pre_pseudo = sel.split(":")[0]
            applies = pre_pseudo == element_name
            if applies:
                break
        elif is_attribute_selector:
            # TODO: adjust for attribute selectors
            print("This must be an attribute selector")
        elif is_descendant_selector:
            items = sel.split()
            applies = items[-1] == element_name
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


def can_inherit_styles(element: Element, selector: str, ruleset: dict) -> bool:
    """returns whether element can get styles through inheritance.

    Descendant elements may inherit styles, but only under certain
    conditions: The element is not a link (or it is a link but the
    selector is selecting it also by type, class, or id). The
    element has not had other styles applied to it.

    There may be more, but this is it for now.

    Args:
        element: the tag that is a descendant of another tag targetted
            by the selector.
        selector: the selector in question.
    Returns:
        can_inherit: whether the element should get the inherited
            styles or not."""
    can_inherit = False
    element_name = element.name
    # is it a link?
    if element_name == "a":
        is_link_selector = css.is_link_selector(selector)
        if is_link_selector:
            can_inherit = True
            return can_inherit
        selector_type = css.get_selector_type(selector)
        if selector_type in ("id_selector", "class_selector"):
            attributes = element.attributes
            if attributes:
                print("TODO: check to see if selector targets class or id")
    selector_applies = does_selector_apply(element, selector)
    if selector_applies:
        can_inherit = True

    if can_inherit:
        # check to see how property has been changed.
        (declaration,) = ruleset.values()
        (property,) = declaration
        if "background" in property:
            applied_by = element.background_color.get("applied_by")
        else:
            applied_by = element.color.get("applied_by")
        if "selector" not in applied_by:
            can_inherit = True
    return can_inherit


if __name__ == "__main__":
    project_path = "tests/test_files/single_file_project/"
    project_path = "tests/test_files/large_project/"
    styles_by_html_files = css.get_styles_by_html_files(project_path)
    for file in styles_by_html_files:
        filepath = file.get("file")
        sheets = file.get("stylesheets")
        css_tree = CSSAppliedTree(filepath, sheets)
        print(css_tree)
