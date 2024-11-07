""" Cascade Tools
This module is a set of tools to determine CSS as applied through
inheritance and the cascade.

The goal is to use the DOM, inheritance, and the cascade, to determine
all styles applied to every element on the page.

With that, it scans each stylesheet and applies each style one at a time
to all elements and their children (if applicable) of a page.
"""
import ctypes
import re
from collections import abc
from typing import Union

from file_clerk import clerk

from webcode_tk import color_tools as color
from webcode_tk import css_tools as css
from webcode_tk import font_tools as fonts
from webcode_tk import html_tools


default_global_color = "#FFFFFF"
default_global_background = None
default_link_color = "#0000EE"
default_link_visited = "#551A8B"
root_font_size = 16


class Element(object):
    """an element object for each tag in a web page

    This will be used by the CSSAppliedTree to represent
    the DOM of a web page and will contain the computed
    CSS styles based on the styesheet.

    A NOTE on background color:
    background color is not applied through inheritance. By default,
    without being set, the background of all elements is white (or
    technically, it's transparent). All elements have a transparent
    background (and there is no inheritance).

    It is applied through one of two methods:
    1. when directly applied to the element
    2. through the context of a container element

    For example, if the background color of body is set using an ID
    selector, and a table inside the body has a different background
    color set using a type selector, even though the table's background
    has a lower specificity, it will be applied because there is no
    inheritance and therefore no specificity to consider.

    Therefore, the applied_by will be either "context" or "applied"
    Attributes:
        name (str): name of the element.
        children (list): any Elements nested in the tag.
        attributes (list): a list of attributes as dictionaries.
        parent (str): the direct parent of the element.
        ancestors (list): a list of all ancestors (in order of the appearance
            in the DOM)
    """

    def __init__(
        self,
        name=None,
        children=None,
        attributes=None,
        parent=None,
        parent_size=root_font_size,
        ancestors=None,
    ) -> None:
        self.name = name
        self.attributes = attributes
        self.background_color = {
            "value": "#ffffff",
            "has_alpha": False,
            "computed_value": "",
            "sheet": "user-agent",
            "selector": "",
            "specificity": "000",
            "applied_by": "context",
            "is_gradient": False,
            "gradient_colors": [],
        }
        self.color = {
            "value": "#000000",
            "sheet": "user-agent",
            "selector": "",
            "specificity": "000",
            "applied_by": "default",
        }
        if parent_size:
            self.font_size = parent_size
        else:
            self.font_size = root_font_size
        self.is_bold = False
        if name == "b":
            self.is_bold = True
        if name in fonts.HEADING_SIZES.keys():
            value = fonts.HEADING_SIZES.get(name)
            value, unit = fonts.split_value_unit(value)
            self.font_size = fonts.compute_font_size(
                value, unit, parent_size, name
            )
            self.is_bold = True
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
            "applied_by": "context",
        }
        self.is_large = False
        self.is_link = bool(name == "a")
        self.contrast_data = {
            "ratio": 21.0,
            "normal_aaa": True,
            "normal_aa": True,
            "large_aaa": True,
            "large_aa": True,
        }
        self.visited_contrast_data = {
            "ratio": 0.0,
            "normal_aaa": False,
            "normal_aa": False,
            "large_aaa": False,
            "large_aa": False,
        }
        self.__set_link_color()
        self.get_contrast_data("default")
        self.children = children if children is not None else []
        self.parent = parent
        self.parent_size = parent_size
        self.ancestors = ancestors.copy() if ancestors is not None else []
        if parent:
            self.ancestors.append(self.parent)

    def __set_link_color(self):
        if self.name == "a":
            self.color["value"] = default_link_color
            self.visited_color["value"] = default_link_visited
            self.visited_color["sheet"] = "user-agent"
            self.visited_color["specificity"] = "000"

    def ammend_color_styles(self, new_styles: dict, filename: str) -> None:
        """adjust color styles based on specificity.

        Args:
            new_styles: the new styles we want to apply.
            filename: the stylesheet the styles came from."""

        # are we even targetting color or bg color
        targets_color = bool(new_styles.get("color"))
        targets_bg_color = bool(new_styles.get("background-color"))

        # get relevant specificity
        new_specificity = new_styles.get("specificity")
        col_specificity = self.color.get("specificity")

        # Check for overrides
        color_has_override = new_specificity >= col_specificity

        # change color if applies
        selector = new_styles.get("selector")
        not_a_link = self.name != "a"
        if not_a_link:
            hover_selector = ":hover" in selector
            visited_selector = ":visited" in selector
            if not hover_selector and not visited_selector:
                if targets_color:
                    if color_has_override:
                        col = new_styles.get("color")
                        if col:
                            self.color["value"] = col
                            self.color["sheet"] = filename
                            self.color["selector"] = selector
                            self.color["specificity"] = new_specificity
                    else:
                        col = self.color.get("value")
                if targets_bg_color:
                    self.ammend_bg_color(
                        new_styles.get("background-color"),
                        new_styles.get("selector"),
                        new_specificity,
                        filename,
                    )
                # get contrast for color & bg_color
                self.get_contrast_data("standard")
        else:
            # Do we have a link selector?
            is_link_selector = css.is_link_selector(selector)
            if is_link_selector:
                print("We have a link selector in ammend_color_styles")
                print("I suppose we should check specificity")

    def ammend_bg_color(
        self,
        bg_color: str,
        new_selector: str,
        new_specificity: str,
        filename: str,
    ) -> None:
        """ammends the bg color based on the selector and specficity.

        Args:
            bg_color: the new bg color value.
            new_selector: the new selector.
            new_specificity: the specificity of the new selector.
            filename: the name of the file that is applying the styles.
        """

        old_specificity = self.background_color.get("specificity")
        bg_has_override = new_specificity >= old_specificity

        # Is the element is targetted directly.
        targeted_directly = targets_element_directly(self, new_selector)

        # Did the previous bg get set directly?
        bg_was_directly_set = self.background_color["applied_by"] == "directly"

        if targeted_directly:
            # don't apply if it was previously set with a higher specificity
            if bg_was_directly_set and not bg_has_override:
                return

            # set new values
            self.background_color["applied_by"] = "directly"
            self.background_color["value"] = bg_color
            self.background_color["specificity"] = new_specificity
            self.background_color["sheet"] = filename
        else:
            # If it was not directly set, we can change it
            if not bg_was_directly_set:
                self.background_color["value"] = bg_color

    def get_contrast_data(self, type="default") -> None:
        """get color contrast for the type specified

        contrast data could be for one of three possibile types:
        * default: this is when all elements get their default values,
        * standard: this is for checking contrast between color and
        background color,
        * hover: for the hover pseudoselector - could be applied to any
        element (not just hyperlinks)
        * visited: for visited links

        Args:
            type: the type of color contrast.
        """
        col = self.color.get("value")
        bg = self.background_color.get("value")
        if color.is_gradient(bg):
            results = color.get_color_contrast_with_gradients(
                col, bg, self.ancestors
            )
            # Set bg to composite color with lowest contrast ratio
            bg = results[0][-2]
            has_alpha = results[0][-1]
            if has_alpha:
                self.background_color["has_alpha"] = True
                self.background_color["computed_value"] = bg

        hexc = color.get_hex(col)
        hexbg = color.get_hex(bg)
        self.__build_contrast_report(hexc, hexbg)
        if self.name == "a" and type == "default" or type == "visited":
            vcol = self.visited_color.get("value")
            hexv = color.get_hex(vcol)
            self.__build_visited_contrast_report(hexv, hexbg)
        if type == "hover":
            self.hover_color["value"] = col
            self.hover_color["applied_by"] = "directly"

    def __build_contrast_report(self, hexc: str, hexbg: str) -> None:
        """creates a full contrast report for Element.

        Args:
            hexc: the hex code for the color value.
            hexbg: the hex code for the background color.
        """
        bg_gradient = color.is_gradient(hexbg)
        c_gradient = color.is_gradient(hexc)
        if bg_gradient or c_gradient:
            # worst contrast ratio takes the hit
            print("let's process this")
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

    def __build_visited_contrast_report(self, hexc: str, hexbg: str) -> None:
        """builds contrast report for visited color settings.

        This applies only for anchor tags as they are the only ones with a
        visited property.

        Args:
            hexc: the hex code for the color value.
            hexbg: the hex code for the background color.
        """
        has_gradient = color.is_gradient(hexc) or color.is_gradient(hexbg)
        if has_gradient:
            print()
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
        self.visited_contrast_data["large_aa"] = bool(
            link_contrast.get("Large AA") == "Pass"
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
            filename: file where the styles come from.
        """

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
                self.apply_background_color(
                    selector,
                    property,
                    val,
                    old_specificity,
                    new_specificity,
                    filename,
                )
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
            self.ammend_bg_color(val, selector, new_specificity, filename)
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
        element_name = self.name

        if selector == self.name:
            targets = True
        elif element_name in selector:
            selector_type = css.get_selector_type(selector)
            if selector_type == "descendant_selector":
                selectors = selector.split(" ")
                if element_name in selectors[-1]:
                    targets = True
            elif selector_type == "grouped_selector":
                selectors = selector.split(",")
                for sel in selectors:
                    if element_name in sel:
                        targets = True
                        break
            elif selector_type == "id_selector":
                # If it's an id selector, the id attribute must be there.
                id_value = selector.split("#")[1]
                try:
                    if isinstance(self.attributes, abc.ItemsView):
                        for attr, value in self.attributes:
                            if attr == "id":
                                element_id = value
                    else:
                        element_id = self.attributes.get("id")
                except AttributeError:
                    element_id = None
                if id_value == element_id:
                    targets = True
            elif selector_type == "advanced_link_selector":
                if ":hover" in selector and element_name == "a":
                    targets = True
        else:
            # check for attribute selector
            selector_type = css.get_selector_type(selector)
            if self.attributes:
                if selector_type == "class_selector":
                    if "class" in self.attributes.keys():
                        for val in self.attributes.get("class"):
                            if val == selector[1:]:
                                targets = True
                                break
                if selector_type == "id_selector":
                    if "id" in self.attributes.keys():
                        print("do like we do for classes")
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
        if applied_by not in ["default", "context", "inheritance"]:
            applied = True
        return applied

    def apply_background_color(
        self,
        selector: str,
        property: str,
        val: str,
        old_specificity: str,
        new_specificity: str,
        filename: str,
    ) -> None:
        """Applies background color by context or directly.

        Args:
            selector: the selector of the new styles.
            property: the property of the new styles.
            val: the value of the new styles.
            old_specificity: the specificity rank of styles currently in use.
            new_specificity: the specificity of the new selector.
            filename: the file (html or css) that applied the styles.
        """
        # Are we directly targeted or not?
        directly_targeted = self.directly_targets(selector)
        previously_set = self.background_color.get("applied_by") == "directly"
        bg_gradient = color.is_gradient(val)

        # If directly, check specificity
        if directly_targeted:
            if previously_set:
                if new_specificity < old_specificity:
                    return
            colors = []
            if bg_gradient:
                self.background_color["is_gradient"] = True
                c = self.color.get("value")
                details = color.get_color_contrast_with_gradients(
                    c, val, self.ancestors
                )
                colors = color.get_gradient_colors(val)

                # Set gradient colors with highest and lowest contrast
                self.background_color["best_contrast"] = {}
                self.background_color["worst_contrast"] = {}

                def process_gradient_data(details, bg_dict):
                    contrast_ratio = details[0]
                    size = self.font_size
                    is_bold = self.is_bold
                    results = color.get_contrast_results_from_ratio(
                        contrast_ratio, size, is_bold
                    )
                    has_alpha = details[-1]
                    if has_alpha:
                        bg_dict["has_alpha"] = has_alpha
                        self.background_color["has_alpha"] = True
                        self.background_color["computed_value"] = details[3]
                        bg_dict["computed_value"] = details[-2]
                    else:
                        bg_dict["value"] = details[2]
                    bg_dict["contrast_ratio"] = details[0]
                    bg_dict["results"] = results

                best = details[-1]
                worst = details[0]
                process_gradient_data(
                    best, self.background_color["best_contrast"]
                )
                process_gradient_data(
                    worst, self.background_color["worst_contrast"]
                )
                self.background_color["gradient_colors"] = colors
            # set color, specificity, and directly applied
            self.background_color["value"] = val
            self.background_color["sheet"] = filename
            self.background_color["specificity"] = new_specificity
            self.background_color["applied_by"] = "directly"
            self.background_color["selector"] = selector
        else:
            if not previously_set:
                self.background_color["value"] = val
                self.background_color["sheet"] = filename
                self.background_color["applied_by"] = "context"


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
        self.root_font_size = 16.0
        self.children = []
        self.font_rules = []
        self.__get_filename()
        self.__get_soup(path)
        self.__get_font_rules()
        self.__calculate_root_font_size()
        self.__build_tree()
        self.__adjust_largeness()
        self.__apply_colors()

    def __get_soup(self, path: str):
        """Gets bs4 soup from the file path

        Args:
            path: the relative file path to the html document
        """
        self.soup = html_tools.get_html(path)

    def __get_filename(self):
        """Extracts filename from path"""
        self.filename = clerk.get_file_name(self.file_path)

    def __get_font_rules(self):
        for sheet in self.stylesheets:
            self.font_rules += css.get_all_font_rules(sheet)

    def __calculate_root_font_size(self):
        """checks stylesheets for global font-size settings and adjusts"""
        for sheet in self.stylesheets:
            font_rules = css.get_all_font_rules(sheet)
            for rule in font_rules:
                selector = rule[0]
                is_global = selector in ("body", "html", "*")
                not_at_rule = not rule[1].get("at_rule")
                is_size_property = rule[1].get("property") == "font-size"
                if is_global and is_size_property and not_at_rule:
                    value = rule[1].get("value")
                    size, unit = fonts.split_value_unit(value)
                    computed_value = fonts.compute_font_size(size, unit)
                    self.root_font_size = computed_value

    def __build_tree(self) -> None:
        """Constructs initial tree (recursively?)"""
        # Start with the body element, and divide and conquer
        root = Element("html")
        self.root = root
        root_id = id(root)
        parent_bg = root.background_color.get("value")
        body = Element(
            "body",
            parent=("html", root_id, parent_bg),
            parent_size=root_font_size,
        )
        body.parent_size = body.font_size
        self.children.append(body)
        body_soup = self.soup.body
        attributes = body_soup.attrs
        if attributes:
            body.attributes = attributes.items()
        self.compute_font_size(body)
        children = body_soup.contents
        self.__get_children(body, children)

    def __get_children(self, element: Element, soup_contents: list) -> None:
        """gets all children of the element and their children from the soup

        The soup refers to the bs4 (Beautiful Soup) of the HTML element.

        Args:
            element: the parent element.
            soup_contents: a list of all items in the bs4 soup
        """
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
            tag_attributes = tag.attrs
            parent = (element.name, id(element))
            new_element = Element(
                tag_name,
                attributes=tag_attributes,
                parent=parent,
                parent_size=element.font_size,
                ancestors=element.ancestors,
            )
            self.__adjust_font_size(new_element)
            element.children.append(new_element)
            for tag in tag_children:
                if tag and not isinstance(tag, str):
                    their_kids = tag.contents
                    kids_attributes = tag.attrs
                    if kids_attributes:
                        kid_element = Element(
                            tag.name,
                            attributes=kids_attributes,
                            parent=(new_element.name, id(new_element)),
                            parent_size=new_element.font_size,
                            ancestors=new_element.ancestors,
                        )
                    else:
                        kid_element = Element(
                            tag.name,
                            parent=(new_element.name, id(new_element)),
                            parent_size=new_element.font_size,
                            ancestors=new_element.ancestors,
                        )
                    self.__adjust_font_size(kid_element)
                    new_element.children.append(kid_element)
                    self.__get_children(kid_element, their_kids)
        return

    def __adjust_largeness(self) -> None:
        """sets the is_large property based on whether it's bold or not
        and the computed font size.
        """
        for child in self.children:
            self.set_is_large(child)
            for kid in child.children:
                self.set_is_large(kid)

    def set_is_large(self, element):
        size = element.font_size
        is_bold = element.is_bold
        is_large = fonts.is_large_text(size, is_bold)
        element.is_large = is_large
        if element.children:
            for kiddo in element.children:
                self.set_is_large(kiddo)

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
                # get filename
                filename = clerk.get_file_name(sheet.href)
                self.__adjust_colors(body, ruleset, filename)

    def targets_body(self, ruleset: dict) -> bool:
        """returns whether the ruleset is targetting the body or not.

        Args:
            ruleset: a dictionary of selectors and their declaration blocks.

        Returns:
            body_in_ruleset: whether body is in one of the selectors.
        """
        body_in_ruleset = False
        for selector in list(ruleset.keys()):
            if "body" in selector:
                body_in_ruleset = True
        return body_in_ruleset

    def __set_global_colors(self) -> Element:
        """sets global colors to the body element.

        This loops through all stylesheets, and at each iteration, it checks
        specificity, and if the global colors beat previous specificity, they
        get applied. The last of the styles to be applied win, and we return
        the body element with global colors applied.

        Returns:
            body: the Body element with global colors applied.
        """
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
            if is_background_prop:
                value = declaration.get("background-color")
                if not value:
                    value = declaration.get("background")
                if property == "background-image":
                    value = declaration.get("background-image")
                element.apply_background_color(
                    selector,
                    property,
                    value,
                    old_specificity,
                    specificity,
                    filename,
                )
            else:
                if ":hover" in selector:
                    color = element.hover_color
                else:
                    color = element.color
                color["value"] = declaration.get("color")
                color["sheet"] = filename
                color["selector"] = selector
                color["specificity"] = specificity
                color["applied_by"] = "directly"
            for child in element.children:
                self.__adjust_child_colors(child, ruleset, filename)

        can_inherit = self.can_inherit_styles(element, selector, ruleset)
        if can_inherit and applies:
            declaration = ruleset.get(selector)
            new_specificity = css.get_specificity(selector)
            element.change_styles(
                selector, declaration.copy(), new_specificity, filename
            )
        for child in element.children:
            self.__adjust_colors(child, ruleset, filename)

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

    def __adjust_font_size(self, element: Element) -> None:
        """looks for rules that apply and then adjusts accordingly

        Args:
            element: the Element object we wish to adjust.
        """
        ######################################################
        # WHat happens if we first change size to parent size?
        # element.font_size = element.parent_size
        ######################################################

        # loop through rules and if they apply, then adjust
        # adjust for all children
        for selector, rule in self.font_rules:
            selector_applies = does_selector_apply(element, selector)
            property = rule.get("property")
            if property == "font":
                is_valid_property = fonts.is_valid_shorthand(rule.get("value"))
                if not is_valid_property:
                    continue
            if property in ("font", "font-weight") and selector_applies:
                self.verify_weight(element, property, rule)
            adjusts_font_size = property in ("font", "font-size")
            not_at_rule = not rule.get("at_rule")
            if selector_applies and adjusts_font_size and not_at_rule:
                value = rule.get("value")
                val, unit = fonts.split_value_unit(value)
                computed_size = fonts.compute_font_size(
                    val, unit, element.parent_size, element.name
                )
                if computed_size != element.font_size:
                    element.font_size = computed_size
                    # recursively change font size on all children
                    for child in element.children:
                        child.font_size = computed_size

    def compute_font_size(self, element: Element, parent=None):
        for selector, rule in self.font_rules:
            selector_applies = does_selector_apply(element, selector)
            is_at_rule = bool(rule.get("at_rule"))
            if selector_applies and not is_at_rule:
                # get the other stuff and process
                property = rule.get("property")
                if property in ("font", "font-size"):
                    self.change_font_size(element, rule)

    def change_font_size(self, element, declaration):
        value = declaration.get("value")
        if element.name == "body":
            parent_size = element.font_size
            element.parent_size = element.font_size
        else:
            parent_size = element.parent_size
        size, unit = fonts.split_value_unit(value)
        computed_size = fonts.compute_font_size(
            size, unit, parent_size, element.name
        )
        element.font_size = computed_size

    def verify_weight(
        self, element: Element, property: str, rule: dict
    ) -> bool:
        """verifies whether font weight is set to bold."""
        is_bold = False
        value = rule.get("value")
        if property == "font":
            is_valid_shorthand = fonts.is_valid_shorthand(value)
            if is_valid_shorthand:
                is_bold = "bold" in value
        else:
            is_bold = "bold" in value
        if is_bold:
            element.is_bold = True

    def can_inherit_styles(
        self, element: Element, selector: str, ruleset: dict
    ) -> bool:
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
            ruleset: the ruleset dictionary (the key is the selector, and
                the value is the declaration block).

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
                if isinstance(element.attributes, abc.ItemsView):
                    for id, value in element.attributes:
                        if id == "id":
                            element_id = value
                else:
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
                for name in attributes:
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
                # first check for attributes
                if is_attribute_selector:
                    # check to see if there is both an attribute and value
                    applies = attribute_selector_applies(element, selector)
                else:
                    applies = True
            break
        elif is_psuedo_class_selector:
            # check for element before psuedoclass
            pre_pseudo = sel.split(":")[0]
            applies = pre_pseudo == element_name
            if applies:
                break
        elif is_attribute_selector:
            applies = attribute_selector_applies(element, selector)
        elif is_descendant_selector:
            applies = descendant_selector_applies(element, sel)
            if applies:
                break
        else:
            raise ValueError(f"Selector not recognized: Got {selector}")
    return applies


def descendant_selector_applies(element: Element, sel: str) -> None:
    """checks all ancestors to see if the descendant selector applies.

    First, we need to check the last component of the descendant selector
    to see if it applies to the element in question. If so, continue. If
    not, return with a False.

    If the element has a match, then we need to check each tag leading up to
    our element in question. According to the article by Pavel Panchekha,
    "What is the Complexity of Selector Matching?" we should start at the
    top of the DOM and work our way down.
    """
    applies = False
    selector_list = sel.split()
    ancestor_list = element.ancestors
    possible_child_selector = selector_list.pop()
    child_selector_applies = does_selector_apply(
        element, possible_child_selector
    )
    if not child_selector_applies:
        return applies

    # loop through the ancestor list
    current_pos = 0
    for ancestor in ancestor_list:
        id = ancestor[1]
        ancestor_element = __get_element_by_id(id)
        selector = selector_list[current_pos]
        cur_selector_applies = does_selector_apply(ancestor_element, selector)
        if cur_selector_applies:
            selector_list = selector_list[1:]
    applies = not selector_list
    return applies


def __get_element_by_id(id: int) -> Element:
    """returns element from id.

    This is created to retrieve an element by its ID. The necessity
    was born out of trying to ascertain whether a descendant selector
    applies to an element while avoiding a recursive tree search through
    the DOM.

    Since a descendant selector could be using any type of selector
    (example: `#main .nav ul a:hover {}`), then just knowing the name
    is not enough.

    Args:
        id: the memory address of the element object.

    Returns:
        element: the element object."""
    element = ctypes.cast(id, ctypes.py_object).value
    return element


def attribute_selector_applies(element: Element, selector: str) -> bool:
    """determines if the attribute selector applies or not.

    Args:
        element: the element in question.
        selector: the attribute selector in question.

    Returns:
        applies: a bool representing whether the attribute selector
            applies or not.
    """
    applies = False
    if "=" in selector:
        attr = selector.split("=")[0]
        start_pos = attr.index("[") + 1
        if attr[-1] in ("*", "$", "~"):
            attribute = attr[start_pos:-1]
        else:
            attr = attr[start_pos:]
        if "*=" in selector:
            # value need only be a partial match
            attr, partial = selector.split("*=")
            partial = "".join(i for i in partial if i not in '"]')
            value = element.attributes.get(attribute)
            if isinstance(value, list):
                for v in value:
                    if partial in v:
                        applies = True
                        break
            else:
                applies = partial in value
        elif "$=" in selector:
            # looking for value ending in text
            ending = selector.split("$=")[1]
            text = ending.split('"')[1]
            case_insenstive = "i]" in selector or "i ]" in selector
            value = ""
            if isinstance(element.attributes, list):
                if attribute in element.attributes:
                    pos = element.attributes.index(value)
                    value = element.attributes[pos]
            elif isinstance(element.attributes, dict):
                if attribute in element.attributes.keys():
                    value = element.attributes.get(attribute)
            if value:
                end_pos = -len(text)
                value_end = value[end_pos:]
                if case_insenstive:
                    value_end = value_end.lower()
                applies = text == value_end
        elif "~=" in selector:
            # looking for whole word in space-separated list
            attr, word = selector.split("~=")
            word = "".join(i for i in word if i not in '"]')
            value = element.attributes.get(attribute)
            if isinstance(value, list):
                for v in value:
                    if word == v:
                        applies = True
                        break
            else:
                applies = word == value
        else:
            attr, value = selector.split("=")
    else:
        # we're just looking for an attribute match
        start = selector.index("[") + 1
        stop = selector.index("]")
        attr = selector[start:stop]
        applies = attr in element.attributes.keys()
    return applies


def is_selector_pseudoclass(selector: str) -> bool:
    """returns whether selector is a pseudoclass selector.

    Args:
        selector: the selector in question.

    Returns:
        is_pseudo_class_selector: whether the selector is a psuedoclass
            or not.
    """
    pc_regex = css.regex_patterns.get("pseudoclass_selector")
    is_pseudo_class_selector = bool(re.match(pc_regex, selector))
    is_pseudo_class_selector = is_pseudo_class_selector or ":" in selector

    # pseudo-elements do NOT count - they are scored like a type selector
    if "::" in selector:
        is_pseudo_class_selector = False
    return is_pseudo_class_selector


def targets_element_directly(element: Element, selector: str) -> bool:
    """returns whether selector targets element directly.

    Args:
        element: the element we are checking.
        selector: the selector in question.
    Returns:
        targets: whether the selector targets the element directly."""
    targets = False
    selector_type = css.get_selector_type(selector)
    if selector_type == "type_selector":
        targets = element.name == selector
    elif selector_type == "id_selector":
        attributes = element.attributes
        if attributes:
            id_attribute = attributes.get("id")
            if id_attribute:
                targets = selector in attributes.get("id")
    elif selector_type == "class_selector":
        attributes = element.attributes
        if attributes:
            classes = attributes.get("class")
            if classes:
                selector_value = selector[1:]
                targets = selector_value in classes
    return targets


def get_color_contrast_results(
    element: Element, results: dict, min_regular="AAA"
) -> dict:
    """returns a list of color contrast results for all elements in a file.

    Recursively searches through the css_tree of HTML elements looking to
    determine whether the element is normal or large in size, and whether it
    passes the AIM color contrast goals.

    The minimum passing level could be either at an AAA or AA level (according
    to the WebAIM Color Contrast Checker). Be default we'll look for AAA
    sizes to see if they pass.
    [WebAim Contrast Checker](https://webaim.org/resources/contrastchecker/)

    Calculating whether an element qualifies as large depends on the styles
    applied. The CSSAppliedTree and Element objects now support computed font
    size as well as whether each Element object is large or not based on the
    description in the WebAim Contrast Checker.

    It states, "Large text is defined as 14 point (typically 18.66px) and bold
    or larger, or 18 point (typically 24px) or larger."

    Args:
        css_tree: the css tree of color styles for a particular file.
        min_regular: the minimum passing size ('AAA' or 'AA') for color
            contrast for normal sized elements (anything except h1-h4).

    Returns:
        results: a dictionary of color contrast results for each element in
            the file.
    """
    tag = element.name
    is_large = element.is_large
    if not results.get(tag):
        results[tag] = {
            "num_elements": 0,
            "num_passed": 0,
            "num_failed": 0,
            "all_pass": True,
        }
    results = update_contrast_results(
        results, tag, is_large, element.contrast_data, min_regular
    )
    if element.children:
        for child in element.children:
            results = get_color_contrast_results(child, results, min_regular)
    return results


def update_contrast_results(
    results: dict,
    tag: str,
    is_large: bool,
    contrast_data: dict,
    min_regular: str,
) -> dict:
    """updates the results of color contrast for the tag.

    we've updated this to match whether the element computes as large or not
    based on the WebAIM Color Contrast page which states, 'Large text is
    defined as 14 point (typically 18.66px) and bold or larger, or 18 point
    (typically 24px) or larger.'

    Args:
        results: the overall results we want to adjust.
        tag: the element we want to adjust.
        is_large: whether the element is considered large.
        contrast_data: the contrast results for the tag.
        min_regular: the minimum level required for standard text passing.

    Returns:
        results: adjusted results after processing contrast data.
    """
    passes = False
    data = results.get(tag)

    data["num_elements"] += 1

    if is_large:
        passes = contrast_data.get("large_aaa")
    else:
        if min_regular == "AAA":
            passes = contrast_data.get("normal_aaa")
        else:
            passes = contrast_data.get("normal_aa")
    if passes:
        data["num_passed"] += 1
    else:
        data["num_failed"] += 1
    data["all_pass"] = not data["num_failed"]
    return results


def get_color_contrast_details(tree: CSSAppliedTree, rating="AAA") -> list:
    """returns a list of all failures or a pass based on rating

    We'll create a recursive inner nested function to traverse the DOM. We will
    target only the styles that are applied directly so as to not overwhelm the
    user and allow fixing the error more easily.

    Args:
        tree: the cascade tree for a single file.
        rating: the rating of contrast we check for (AAA or AA). The default
            is AAA.
    Returns:
        results"""
    results = []
    filename = tree.filename
    # Loop recursively through the tree
    elements = tree.children

    def check_element(
        el: Element, rating: str, filename: str
    ) -> Union[list, None]:
        children = el.children
        msg = ""
        applied_directly = (
            el.background_color.get("applied_by") == "directly"
            or el.color.get("applied_by") == "directly"
        )
        if applied_directly or el.name == "body":
            is_gradient = el.background_color.get("is_gradient")
            if is_gradient:
                # get worst case
                worst_case = el.background_color.get("worst_contrast")
                worst_results = worst_case.get("results")
                fails = "fail" in worst_results[:5]
                if fails:
                    selector = el.background_color.get("selector")
                    if el.is_large:
                        size = "Large"
                    else:
                        size = "Normal"
                    msg = f"{el.name} tag (selector: {selector}) fails color "
                    msg += f"contrast at {size} {rating}."
                    results.append(msg)
                    return
            contrast_data = el.contrast_data
            if el.is_large:
                if rating == "AAA":
                    passes = contrast_data.get("large_aaa")
                else:
                    passes = contrast_data.get("large_aa")
            else:
                if rating == "AAA":
                    passes = contrast_data.get("normal_aaa")
                else:
                    passes = contrast_data.get("normal_aa")
            # only add results if failure
            if not passes:
                if el.is_large:
                    size = "Large"
                else:
                    size = "Normal"
                selector = el.background_color.get("selector")
                if not selector:
                    selector = el.color.get("selector")
                msg = f"{el.name} tag (selector: {selector}) fails color "
                msg += f"contrast at {size} {rating}."
                results.append(msg)
        if not children:
            return
        else:
            for kid in children:
                check_element(kid, rating, filename)

    for element in elements:
        check_element(element, rating, filename)
    if results:
        adjusted = []
        for result in results:
            adjusted.append("fail: " + result)
        results = adjusted
    else:
        # It's a success! Let's let them know
        msg = f"success: {filename} passes color contrast for {rating} Normal"
        msg += " and Large."
        results.append(msg)
    return results


if __name__ == "__main__":
    project_path = "tests/test_files/attribute_selector_file"
    project_path = "tests/test_files/large_project/"
    gradients_path = "tests/test_files/gradients.html"
    contents = clerk.file_to_string(gradients_path)
    sheet = css.Stylesheet(gradients_path, contents)
    gradient_tree = CSSAppliedTree(
        gradients_path,
        [
            sheet,
        ],
    )
    results = get_color_contrast_details(gradient_tree, "AAA")
    styles_by_html_files = css.get_styles_by_html_files(project_path)
    for file in styles_by_html_files:
        filepath = file.get("file")
        sheets = file.get("stylesheets")
        css_tree = CSSAppliedTree(filepath, sheets)
        results = {}
        root = css_tree.children[0]
        results = get_color_contrast_results(root, results)
