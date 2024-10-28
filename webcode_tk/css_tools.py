""" CSS
This module is a set of tools to analyze CSS syntax as well as properties
and values.
"""
import re
from typing import Union

from file_clerk import clerk

from webcode_tk import color_keywords as keyword
from webcode_tk import color_tools
from webcode_tk import html_tools

# regex patterns for various selectors
# on attribute selector, if you want
regex_patterns: dict = {
    "adjacent_sibling_combinator": r"\w+\s*\+\s*\w+",
    "advanced_link_selector": r"(a[:.#\[]\w+)",
    "attribute_selectors": r"[a-zA-Z]*\[(.*?)\]",
    "child_combinator": r"\w+\s*>\s*\w+",
    "class_selector": r"\.\w+",
    "descendant_selector": r"\w+\s\w+",
    "general_sibling_combinator": r"\w+\s*~\s*\w+",
    "grouped_selector": r"\w+\s*,\s*\w+",
    "header_selector": r"h[1-6]",
    "id_selector": r"(.*?)#[a-zA-Z0-9-_.:]+",
    "pseudoclass_selector": r"(?<!:):\w+",
    "pseudoelement_selector": r"(\w+)?::\w+(-\w+)?",
    "single_attribute_selector": r"^[a-zA-Z]*\[(.*?)\]",
    "single_type_selector": r"^[a-zA-Z][a-zA-Z0-9]*$",
    "type_selector": r"(?:^|\s)([a-zA-Z][a-zA-Z0-9_-]*)",
    "vendor_prefix": r"\A-moz-|-webkit-|-ms-|-o-",
}

# all relevant at-rules.
# from the Mozilla Developer Network's article, At-rules
# https://developer.mozilla.org/en-US/docs/Web/CSS/At-rule
nested_at_rules: tuple = (
    "@supports",
    "@document",
    "@page",
    "@font-face",
    "@keyframes",
    "@media",
    "@viewport",
    "@counter-style",
    "@font-feature-values",
    "@property",
)


class Stylesheet:
    """A Stylesheet object with details about the sheet and its
    components.

    The stylesheet object has the full code, a list of comments from the
    stylesheet, a list of nested @rules, rulesets pertaining to colors,
    a list of all selectors, and information about repeated selectors.

    About repeated selectors, front-end developers should always employ
    the DRY principle: Don't Repeat Yourself. In other words, if you
    use a selector once in your stylesheet, the only other place you
    would logically put the same selector would be in a nested at-rule
    (in particular, an @media or @print breakpoint)

    For this reason, both the Stylesheet object and the NesteAtRule
    objects have attributes that show whether there are repeated
    selectors or not as well as which selectors get repeated.

    Attributes:
        href: the filename (not path), which may end with .css or .html
            (if stylesheet object comes from a style tag).
        text: the actual code itself of the entire file or style tag.
        type: whether it's a file or local if it's from an style tag.
        nested_at_rules: a list of all nested at-rules.
        rulesets: a list of all rulesets.
        comments: a list of all comments in string format.
        color_rulesets: a list of all rulesets that target color or
            background colors.
        selectors: a list of all selectors.
        has_repeat_selectors (bool): whether there are any repeated
            selectors anywhere in the stylesheet (including in the
            NestedAtRule.
        repeated_selectors (list): a list of any selectors that are
            repeated. They might be repeated in the main stylesheet
            or they might be repeated in one of the nested @rules.
    """

    def __init__(
        self, href: str, text: str, stylesheet_type: str = "file"
    ) -> None:
        """Inits Stylesheet with href, text (CSS code), and type."""
        self.type = stylesheet_type
        self.href = href
        self.text = text
        self.nested_at_rules = []
        self.rulesets = []
        self.comments = []
        self.color_rulesets = []
        self.selectors = []
        self.has_repeat_selectors = False
        self.repeated_selectors = []
        self.__minify()
        self.__replace_variables()
        self.__remove_external_imports()
        self.__extract_comments()
        self.__extract_nested_at_rules()
        self.__extract_rulesets()
        self.__set_selectors()

    def __minify(self):
        """Removes all whitespace, line returns, and tabs from text."""
        self.text = minify_code(self.text)

    def __replace_variables(self):
        """Looks for and replaces any variables set in stylesheet with
        the variable's values."""
        # get a list of all variables and their values
        variable_list = get_variables(self.text)

        # Loop through the variable list and do a find
        # and replace on all occurrances of the variable
        new_text = self.text
        for variable in variable_list:
            var = variable.get("variable")
            value = variable.get("value")
            var = r"var\(" + var + r"\)"
            new_text = re.sub(var, value, new_text)
        self.text = new_text

    def __extract_comments(self):
        """Gets all comments from the code and stores in a list."""
        # split all CSS text at opening comment
        text_comment_split = self.text.split("/*")
        comments = []
        code_without_comments = ""

        # loop through the list of code
        # in each iteration extract the comment
        for i in text_comment_split:
            if "*/" in i:
                comment = i.split("*/")
                comments.append("/*" + comment[0] + "*/")
                code_without_comments += comment[1]
            else:
                # no comments, just get code
                code_without_comments += i
        self.comments = comments
        self.text = code_without_comments

    def __extract_nested_at_rules(self):
        """Pulls out any nested at-rule and stores them in a list."""
        at_rules = []
        non_at_rules_css = []

        # split at the double }} (end of a nested at rule)
        css_split = self.text.split("}}")
        css_split = restore_braces(css_split)

        if len(css_split) == 1:
            return
        for code in css_split:
            # continue if empty
            if not code.strip():
                continue
            for rule in nested_at_rules:
                # if there is a nested @rule
                # split code from @rule
                if rule in code:
                    split_code = code.split(rule)
                    if len(split_code) == 2:
                        if split_code[0]:
                            # an @rule was NOT at the beginning or else,
                            # there would be an empty string
                            # that means there is CSS to add (non-at-rules)
                            non_at_rules_css.append(split_code[0])

                        # create a nested at-rule object
                        text = split_code[1]
                        pos = text.find("{")
                        at_rule = rule + text[:pos]
                        ruleset_string = text[pos + 1 : -1]
                        nested = NestedAtRule(at_rule, ruleset_string)
                        if nested.has_repeat_selectors:
                            self.has_repeat_selectors = True
                        at_rules.append(nested)
                    else:
                        # it's only an @rule
                        print("skipping non-nested @rule.")

        self.text = "".join(non_at_rules_css)
        self.nested_at_rules = at_rules

    def __extract_rulesets(self):
        """Separates all code into individual rulesets."""
        # split rulesets by closing of rulesets: }
        ruleset_list = self.text.split("}")
        for ruleset in ruleset_list:
            if ruleset:
                ruleset = Ruleset(ruleset + "}")
                self.rulesets.append(ruleset)
                self.get_color_ruleset(ruleset)

    def __remove_external_imports(self):
        text = self.text
        # look for external link by protocol (http or https)
        external_import_re = r"@import url\(['\"]https://|"
        external_import_re += r"@import url\(['\"]http://"

        # remove external imports if there's a protocol
        # text = text.lower()
        match = re.search(external_import_re, text)
        if match:
            # but only if it's in an @import url function
            split_text = re.split(external_import_re, text)

            # we now have 1 or more code segments without the
            # beginnings of an @import url( segment
            for i in range(1, len(split_text)):
                segment = split_text[i]
                # get everything after the first );
                paren_pos = segment.index(")") + 1
                segment = segment[paren_pos:]
                if ";" in segment[:2]:
                    pos = segment[:2].index(";")
                    segment = segment[pos + 1 :]
                split_text[i] = segment
            # put text back in string form
            text = "".join(split_text)
        self.text = text

    def get_color_ruleset(self, ruleset: "Ruleset") -> list:
        """Returns a list of all rules targetting color or background color.

        Args:
            ruleset(Ruleset): a Ruleset object complete with selector
                and declaration block.

        Returns:
            color_rulesets: a list of all selectors that target color
                in some way, but just with the color-based declarations.
        """
        color_rulesets = []
        if ruleset.declaration_block and (
            "color:" in ruleset.declaration_block.text
            or "background" in ruleset.declaration_block.text
        ):
            selector = ruleset.selector
            for declaration in ruleset.declaration_block.declarations:
                if (
                    "color" in declaration.property
                    or "background" in declaration.property
                ):
                    property = declaration.property
                    value = declaration.value

                    # Check for a gradient bg color
                    is_bg_gradient = color_tools.is_gradient(value)
                    if is_bg_gradient:
                        print()
                    # skip if has vendor prefix
                    if has_vendor_prefix(value):
                        continue
                    # skip if not valid color value
                    is_valid_color = color_tools.is_color_value(value)
                    if not is_valid_color and not is_bg_gradient:
                        continue
                    # make sure the value is a color (not other)
                    rule = {selector: {property: value}}
                    color_rulesets.append(rule)
        if color_rulesets:
            self.color_rulesets += color_rulesets

    def __set_selectors(self):
        """Adds all selectors from stylesheet to selectors attribute."""
        for rule in self.rulesets:
            if rule.selector in self.selectors:
                self.has_repeat_selectors = True
                self.repeated_selectors.append(rule.selector)
            self.selectors.append(rule.selector)

    def sort_selectors(self):
        """Puts all selectors in alphabetical order."""
        self.selectors.sort()


class NestedAtRule:
    """An at-rule rule that is nested, such as @media or @keyframes.

    Nested at-rules include animation keyframes, styles for print
    (@media print), and breakpoints (@media screen). Each nested
    at-rule has an at-rule, which works like a selector, and a
    ruleset for that at-rule. The ruleset may contain any number
    of selectors and their declaration blocks.

    You can almost think of them as stylesheets within a stylesheet
    *"A dweam within a dweam"* -The Impressive Clergyman.
    *"We have to go deeper"* -Dom Cobb.

    Nested at-rules are defined in the global variable: nested_at_rules.
    For more information on nested at-rules, you want to refer to MDN's
    [nested]
    (https://developer.mozilla.org/en-US/docs/Web/CSS/At-rule#nested)

    Args:
        at_rule (str): the full at-rule such as '@media only and
            (min-width: 520px)'.
        text (str): the text of the code (without the at_rule).
            Provide the text if you do not provide a list of rulesets.
        rules (list): a list of Ruleset objects. This is optional and
            defaults to None. Just be sure to add text if you don't
            provide a list.
    Attributes:
        at_rule (str): the full at-rule such as '@media only and
            (min-width: 520px)'.
        rulesets (list): a list of Ruleset objects.
        selectors (list): a list of all selectors from the rulesets
        has_repeat_selectors (bool): whether there are any repeated
            selectors in the NestedAtRule.
        repeated_selectors (list): a list of any selectors that are
            repeated.
    """

    def __init__(self, at_rule, text="", rules=None):
        """Inits a Nested @rule object.

        Raises:
            ValueError: an error is raised if neither at_rule nor text is
                provided for the constructor or both are provided but they
                do not match.
        """
        self.at_rule = at_rule.strip()
        if rules is None:
            self.rulesets = []
        else:
            self.rulesets = rules[:]
        self.selectors = []
        self.has_repeat_selectors = False
        self.repeated_selectors = []

        # If rulesets were NOT passed in, we need to get them from the text
        if not rules:
            self.set_rulesets(text)
        else:
            # if both rules and text were passed in make sure they
            # match and raise a ValueError if not
            if rules and text:
                code_split = text.split("}")
                if len(code_split) != len(rules):
                    msg = "You passed both a ruleset and text, but "
                    msg += "The text does not match the rules"
                    raise ValueError(msg)
            # let's get our selectors
            for rule in self.rulesets:
                selector = rule.selector
                self.selectors.append(selector)
        self.check_repeat_selectors()

    def check_repeat_selectors(self):
        """Checks to see if there are any repeated selectors"""
        for selector in self.selectors:
            count = self.selectors.count(selector)
            if count > 1:
                self.has_repeat_selectors = True
                self.repeated_selectors.append(selector)

    def set_rulesets(self, text):
        """Converts string of text into a list of ruleset objects"""
        # first, make sure text was not an empty string
        if text.strip():
            self.__text = minify_code(text)
        else:
            msg = "A NestedAtRule must be provided either rulesets"
            msg += " or text, but you provided no useable code."
            raise ValueError(msg)
        if self.__text.count("}") == 1:
            ruleset = Ruleset(self.__text)
            self.selectors.append(ruleset.selector)
            self.rulesets.append(ruleset)
        else:
            code_split = self.__text.split("}")
            rulesets = []
            for part in code_split:
                if part.strip():
                    ruleset = Ruleset(part + "}")
                    if ruleset:
                        selector = ruleset.selector
                        self.selectors.append(selector)
                    rulesets.append(ruleset)
            if rulesets:
                self.rulesets = rulesets


class Ruleset:
    """Creates a ruleset: a selector with a declaration block.

    For more information about Rulesets, please read MDN's article on
    [Rulesets]
    (https://developer.mozilla.org/en-US/docs/Web/CSS/Syntax#css_rulesets)

    Args:
        text (str): the CSS code in text form.

    Attributes:
        __text (str): the CSS code.
        selector (str): the selector of the Ruleset
        declaration_block (DeclarationBlock): a DeclarationBlock
            object.
        is_valid (bool): whether the Ruleset is valid or not.
    """

    def __init__(self, text):
        """Inits a DeclarationBlock object using CSS code"""
        self.__text = text
        self.selector = ""
        self.declaration_block = None
        self.is_valid = True
        self.validate()
        self.initialize()

    def initialize(self):
        """converts the text into a DeclarationBlock."""
        if self.is_valid:
            contents = self.__text.split("{")
            self.selector = contents[0].replace("\n", "").strip()
            block = contents[1].replace("\n", "")
            self.declaration_block = DeclarationBlock(block)

    def validate(self):
        """Determines whether the code is valid or not"""
        try:
            open_brace_pos = self.__text.index("{")
            close_brace_pos = self.__text.index("}")
            if open_brace_pos > close_brace_pos:
                # { needs to come before }
                self.is_valid = False
        except Exception:
            self.is_valid = False

        if "{" not in self.__text or "}" not in self.__text:
            self.is_valid = False


class DeclarationBlock:
    """A set of properties and values that go with a selector

    In CSS a declaration block is a block of code set off by curly
    brackets `{}`. They come after a selector and contain one or more
    declarations (pairs of properties and values such as
    `width: 200px`).

    Attributes:
        text (str): full text of the declaration block including
            curly brackets.
        declarations: a list of Declaration objects (see the
            Declaration class below)."""

    def __init__(self, text):
        """Inits a declaration block"""
        self.text = text
        self.declarations = []
        self.__set_declarations()

    def __set_declarations(self):
        """converts text into a list of declarations."""
        declarations = self.text

        # remove selectors and braces if present
        if "{" in self.text:
            declarations = declarations.split("{")
            declarations = declarations[1]
        if "}" in declarations:
            declarations = declarations.split("}")
            declarations = declarations[0]

        declarations = declarations.split(";")

        # remove all spaces and line returns
        # capture positions of content we want to keep
        keep = []
        for i in range(len(declarations)):
            declarations[i] = declarations[i].replace("\n", "")
            declarations[i] = declarations[i].strip()
            if declarations[i]:
                keep.append(i)

        # get only declarations with content
        to_keep = []
        for pos in keep:
            to_keep.append(declarations[pos])
        declarations = to_keep

        # set all Declaration objects
        for i in range(len(declarations)):
            declarations[i] = Declaration(declarations[i])
        self.declarations = declarations


class Declaration:
    """A property and value pair.

    A declaration is a pairing of a property with a specific value.
    Examples include: `font-family: Helvetica;` which changes the
    font to Helvetica. Another example could be `min-height: 100px`
    which sets the height of the element to be at the very least
    100 pixels.

    Attributes:
        text (str): the text of the declaration in the form of
            `property: value;`
        property (str): the thing you want to change (like `color`
            or `border-width`.
        value (str): what you want to change it to (like `aquamarine`
            or `5px`"""

    def __init__(self, text):
        """Inits a Declaration object."""
        self.__text = text
        self.property = ""
        self.value = ""
        self.invalid_message = ""
        self.is_color = False
        # validate before trying to set the declaration.
        try:
            self.validate_declaration()
            self.is_valid = True
            self.set_declaration()
            self.is_color_property()
        except ValueError as e:
            self.is_valid = False
            self.invalid_message = str(e)

    def set_declaration(self):
        """Sets the property and value based on the text (CSS code).

        Note: this only gets run if the declaration was valid, and
        we already ran the validation. Had the code not been valid,
        it would have already thrown an exception, and we wouldn't
        be in this method."""
        elements = self.__text.split(":")
        self.property = elements[0].strip()
        self.value = elements[1].strip()

    def validate_declaration(self):
        """Raises a ValueError if any part of the Declaration is
        invalid."""

        # split text at colon (should have 2 items only: the property
        # on the left of the colon and the value on the right of the
        # colon)
        try:
            property, value = self.__text.split(":")
        except ValueError as err:
            if "not enough values" in str(err):
                # There was no colon - there must be one
                msg = "The code is missing a colon. All declarations "
                msg += "must have a colon between the property and "
                msg += "the value."
                raise ValueError(msg)
            elif "too many values" in str(err):
                # There were two or more colons - can only be one
                msg = "You have too many colons. There should only be "
                msg += "one colon between the property and the value."
                raise ValueError(msg)

        self.validate_property(property)
        self.validate_value(value)

    def validate_property(self, property) -> bool:
        """checks property to make sure it is a valid CSS property.

        A CSS property is valid if there are no spaces in between the
        text. In future versions, we could check against a list of
        valid properties, but that might take us down a rabbit hole
        of ever changing properties.

        Args:
            property (str): the property of the Declaration which might
                or might not be valid.

        Raises:
            ValueError: if the property is an invalid property
        """

        # Make sure there are no spaces in between property
        prop_list = property.strip().split()
        if len(prop_list) > 1:
            msg = "You cannot have a space in the middle of a property."
            msg += "Did you forget the dash `-`?"
            raise ValueError(msg)

    def validate_value(self, value, property=None):
        """Raises a ValueError if the value is invalid.

        Caveat: this is by no means a comprehensive validation, and
        so there is much room for improvement. For now, we're focusing
        on the basics, such as there can be no text after the semi-
        colon and there should be no units if the value is 0.

        In future versions, we could extend the validation to make
        sure the units match the property, which is why we added a
        default value for property.

        Args:
            value (str): the code after the colon (what specifically
                do you want the property set to)
            property (str): the property which defaults to None.

        Raises:
            ValueError: if the value is invalid.
        """
        if property is None:
            property = ""

        value = value.strip()
        # Make sure there's nothing after the semi-colon
        # but account for the empty string element after the split
        # as well as spaces (just in case)
        val_list = value.split(";")
        if len(val_list) > 1 and val_list[1].strip():
            msg = "There should be no text after the semi-colon."
            raise ValueError(msg)
        if value == ";" or not value:
            msg = "You are missing a value. You must include a "
            msg += "value in between the colon : and the semi-"
            msg += "colon ;"
            raise ValueError(msg)
        # Check for a value of 0 and make sure there are no units
        zero_pattern = r"^\b0\w"
        match = re.search(zero_pattern, value)
        if match:
            msg = "Values of 0 do not need a unit. Example: 0px should "
            msg += "be just 0."
            raise ValueError(msg)

        # TODO: add some validation based on property type

    def get_declaration(self) -> str:
        """Returns the declaration in the form of `property: value`

        Returns:
            declaration (str): a property and its value separated by
            a colon. Example: `"color: rebeccapurple"`"""

        declaration = self.property + ": " + self.value
        return declaration

    def is_color_property(self):
        value = self.value
        if value[-1] == ";":
            value = value[:-1]
        self.is_color = color_tools.is_color_value(value)


def adjust_overrides(file_path: str, rules: dict) -> dict:
    """Returns a dictionary with a single global ruleset.

    Gets the final computed value of all rulesets in a file. It loops
    through the rulesets, and whenever there is an override (due to a
    repeat selector), it replaces whichever value is in the repeated
    selector.

    Args:
        file_path: path to the file in question, to be used as a
            key in the adjusted rule
        rules: a dictionary where the key is the filename and the value
            is a list of rules.

    Returns:
        adjusted_rule: a dictionary where the key is the same, but
            there is only one ruleset (the computed ruleset).
    """
    adjusted_rule = {}
    old_rules = list(rules.get(file_path))
    pre_selector, pre_bg_color, pre_color = ("", "", "")
    for rule in old_rules:
        selector = rule.get("selector")
        bg_color = rule.get("background-color")
        color = rule.get("color")
        if pre_selector:
            # we have looped at least once.
            # check to see if we have the same selector or not
            if selector == pre_selector:
                # same selector, it's time to check our stats
                # for an override
                if bg_color and bg_color != pre_bg_color:
                    adjusted_rule[file_path]["background-color"] = bg_color
                if color and color != pre_color:
                    adjusted_rule[file_path]["color"] = color
        else:
            # this is the first time we are looping
            adjusted_rule[file_path] = rule
            pre_selector = selector
            pre_bg_color = bg_color
            pre_color = color
    return adjusted_rule


def check_for_inherited_colors(
    rules: list, condensed: dict, source_file: str
) -> None:
    """Double-check and fix any necessary overrides.

    This is a tough one. The goal is to look for advanced selectors
    (descendant, class, id, pseudo, attribute), and if they did NOT
    specify color or bg color, then replace it with the nearest
    ancestor

    Args:
        rules: a list of all color rules.
        condensed: the already condensed set of color rules
        source_file: the file we are looking at."""
    for rule in rules:
        file, sel, prop, val = rule
        if file != source_file:
            continue
        if "." in sel or ":" in sel or "#" in sel or "[" in sel:
            # if either color or bg color is missing, look behind
            if not condensed[sel].get("color") or not condensed[sel].get(
                "background-color"
            ):
                for char in ".:#[":
                    if char in sel:
                        split_selector = sel.split(char)
                        behind = split_selector[0]
                        if condensed.get(behind):
                            for data in rules:
                                filename = data[0]
                                if filename != source_file:
                                    continue
                                rule_selector = data[1]
                                if behind == rule_selector:
                                    # we found an ancestor
                                    ancestor_data = condensed.get(behind)
                                    current_condensed = condensed.get(sel)
                                    if not current_condensed.get("color"):
                                        color = ancestor_data.get("color")
                                        current_condensed["color"] = color
                                    if not current_condensed.get(
                                        "background-color"
                                    ):
                                        bg = ancestor_data.get(
                                            "background-color"
                                        )
                                        cur_bg = current_condensed
                                        cur_bg["background-color"] = bg
                                    break


def condense_the_rules(rules: list, source_file: str) -> dict:
    """takes a list of color rules and returns only the unique color rulesets

    Brings together both background and foreground color for each selector
    (when present)

    Args:
        rules: list of tuples that contain filename, selector, property,
            and value
        source_file: the HTML document the contains the rules
    Returns:
        condensed: a dictionary with file and all selectors that target
            colors with what was set for background-color and color
    """
    condensed = {"file": source_file}
    for rule in rules:
        file, sel, prop, val = rule
        if file != source_file:
            continue
        if not condensed.get("file"):
            condensed["file"] = file
        if not condensed.get(sel):
            # we don't yet have the selector in place
            condensed[sel] = {}
        # set the color or background color here
        if prop == "color":
            condensed[sel]["color"] = val
        if prop == "background-color":
            condensed[sel]["background-color"] = val
    check_for_inherited_colors(rules, condensed, source_file)
    return condensed


def file_applies_property_by_selector(
    file_path: str, selector: str, property: str
) -> bool:
    """determines whether a specific property is applied to selector or not.

    Args:
        file_path: path to html doc in question.
        selector: CSS selector (or element) that the property is applied.
        property: the CSS property we are looking for.

    Returns:
        applies_property: whether that selector applies the property or not.
    """
    applies_property = False
    style_sheets = get_all_stylesheets_by_file(file_path)

    # look for the selector get all declaration block
    declarations = []
    for sheet in style_sheets:
        declaration_block = get_declaration_block_from_selector(
            selector, sheet
        )
        if declaration_block:
            declarations.append(declaration_block)
    combined_declaration_block = "\n".join(declarations)
    if combined_declaration_block:
        # check for property in declaration_block
        declarations = combined_declaration_block.split(";")
        for declaration in declarations:
            try:
                prop, value = declaration.split(":")
                if property in prop:
                    applies_property = True
                    break
            except ValueError:
                print("Declaration is missing a colon!")
    return applies_property


def get_all_color_rules(file: str) -> list:
    """gets all color rulesets from html file

    Gets all color rulesets applied to an HTML file, whether that be
    through a style tag or linked stylesheet and condensing them.

    Creates a list of tuples that include filename, selector, color,
    and background color, and adjusts for overrides. In other words,
    it should be each selector and the final color applied.

    Caveats: It does not yet account for inheritance. That would require
    traversing the DOM. It also does not yet account for @media rules. As
    of now, it's ignoring any @media breakpoint rule.

    Args:
        file: an html file

    Returns:
        all_color_rules: a dictionary of all color rulesets applied to an
        html document."""
    all_color_rules = []
    styles_by_file = get_all_stylesheets_by_file(file)
    for style in styles_by_file:
        rules = get_color_rules_from_stylesheet(style)
        if rules:
            for rule in rules:
                all_color_rules.append((file,) + rule)
    condensed_rules = condense_the_rules(all_color_rules, file)
    return condensed_rules


def get_all_font_rules(sheet: Stylesheet) -> list:
    """returns a list of all rules targetting font properties.

    Args:
        sheet: a stylesheet object.

    Returns:
        font_rules: a list of all font rules.
    """
    rules = {}
    for rule in sheet.rulesets:
        if "font" in rule._Ruleset__text:
            for declaration in rule.declaration_block.declarations:
                if "font" in declaration.property:
                    selector = rule.selector
                    property = declaration.property
                    value = declaration.value
                    if not rules.get(selector):
                        rules[selector] = {}
                    rules[selector]["at_rule"] = None
                    rules[selector]["property"] = property
                    rules[selector]["value"] = value
    font_rules = list(rules.items())
    at_rules = get_all_at_rules(sheet)
    font_rules = font_rules + at_rules
    return font_rules


def get_all_at_rules(sheet):
    adjusted_at_rules = []
    for declaration in sheet.nested_at_rules:
        at_rule = declaration.at_rule
        for rule in declaration.rulesets:
            for declaration in rule.declaration_block.declarations:
                if "font" in declaration.property:
                    selector = rule.selector
                    property = declaration.property
                    value = declaration.value
                    details = {
                        "at_rule": at_rule,
                        "property": property,
                        "value": value,
                    }
                    new_rule = (selector, details)
                    adjusted_at_rules.append(new_rule)

    return adjusted_at_rules


def get_all_link_rules(sheet: Stylesheet) -> list:
    """returns all rules that target a hyperlink

    returns all rules that target a link

    Args:
        sheet: the stylesheet object.

    Returns:
        rules: a list of all rules that target a link"""
    rules = []
    link_selectors = get_all_link_selectors(sheet)
    all_rulesets = sheet.rulesets
    for rule in all_rulesets:
        current_selector = rule.selector
        if current_selector in link_selectors:
            rules.append(rule)
    return rules


def get_all_link_selectors(sheet: Stylesheet) -> list:
    """returns all selectors that target a link

    Args:
        sheet: the stylesheet object.

    Returns:
        selectors: a list of all selectors that target a link"""
    selectors = []
    all_selectors = sheet.selectors
    for selector in all_selectors:
        selector_match = is_link_selector(selector)
        if selector_match:
            selectors.append(selector.strip())
    return selectors


def get_all_styles_in_order(project_path: str) -> list:
    """returns a list of all files' stylesheets in order of appearance.

    The goal is to allows user to identify the cascade order of selectors
    and their values. This will allow one to determine if one ruleset
    overrides another (same specificity)

    Iterates through each html file in a project folder and extracts
    any style tags and local stylesheets. Each styletag or stylesheet
    is converted into a Stylesheet object and appended to a dictionary
    of file names.

    Args:
        project_path: the path to the main project folder.

    Returns:
        styles_by_html_files: a list of dictionary objects. Each dictionary
            has two keys: file and stylesheets.
    """
    styles_by_html_files = []
    html_files = html_tools.get_all_html_files(project_path)
    for file in html_files:
        file_data = get_all_stylesheets_by_file(file)
        styles_by_html_files.append({"file": file, "stylesheets": file_data})
    return styles_by_html_files


def get_all_stylesheets_by_file(file_path: str) -> list:
    """returns a list of all Stylesheet objects from an HTML file in order of
    appearance.

    This will check an HTML file for any links to stylesheets or style tags,
    and get each stylesheet in the order in which they were called (in case
    there is a CSS override).

    It will only accept links to local stylesheets and ignore any external
    stylesheets called with an http or https.

    Args:
        file_path: the path to an HTML file.

    Returns:
        all_styles: a list of stylesheet objects in the order in which they
            are called (as a link or style tag).
    """
    all_styles = []
    head_tags = html_tools.get_elements("head", file_path)
    for item in head_tags:
        for tag in item.contents:
            if tag == "\n":
                continue
            if tag.name == "link":
                href = tag.attrs.get("href")
                if ".css" in href:
                    if "http" not in href[:5]:
                        # remove html filename with sheet href
                        path_list = clerk.get_path_list(file_path)
                        path_list.pop()
                        path_list.append(href)
                        sheet_path = "/".join(path_list)
                        code = clerk.file_to_string(sheet_path)
                        css_sheet = Stylesheet(sheet_path, code)
                        all_styles.append(css_sheet)
            if tag.name == "style":
                # first check for @import url
                contents = tag.text
                if "@import url(" in contents:
                    filename = contents.split("url(")[1]
                    filename = filename.split(")")[0]
                    filename = filename.replace('"', "")
                    filename = filename.replace("'", "")
                    path_list = clerk.get_path_list(file_path)
                    path_list.pop()
                    path_list.append(filename)
                    sheet_path = "/".join(path_list)
                    code = clerk.file_to_string(sheet_path)
                    css_sheet = Stylesheet(sheet_path, code)
                    all_styles.append(css_sheet)
                else:
                    css_sheet = Stylesheet(file_path, tag.text, "styletag")
                    all_styles.append(css_sheet)
    return all_styles


def get_background_color(declaration: Declaration) -> Union[str, None]:
    """Returns a color value from a declaration with a property of background

    Args:
        declaration: the declaration we want to test.

    Returns:
        color_value: either a valid color value, None, or gradient - if it's a
            gradient"""
    color_value = None
    is_rgb = color_tools.is_rgb(declaration.value)
    if is_rgb:
        return declaration.value
    values = declaration.value.split()
    for val in values:
        color = color_tools.is_color_value(val)
        if color:
            color_value = val
            break
        is_keyword = val in color_tools.color_keywords.get_all_keywords()
        if is_keyword:
            color_value = val
            break
        gradient = is_gradient(val)
        if gradient:
            color_value = "gradient"
            break
    return color_value


def get_bg_or_color(prop):
    declaration = {"type": {}, "declaration": {}}
    if prop == "color":
        declaration["type"] = "color"
        declaration["declaration"] = {"color": prop}
    if "background" in prop:
        declaration["type"] = "background"
        declaration["declaration"] = {"background": prop}
    return declaration


def get_class_score(selector: str) -> int:
    """receives a selector and returns the class score

    The class score represents the combined number of class,
    pseudo-class, and attribute selectors.

    Args:
        selector (str): the complete CSS selector

    Returns:
        score: the number of class selectors, which includes attribute
        and pseudoclass selectors (but NOT pseudo-elements).
    """
    class_re = regex_patterns["class_selector"]
    selectors = re.findall(class_re, selector)
    pseudo_re = regex_patterns["pseudoclass_selector"]
    pseudo_selectors = re.findall(pseudo_re, selector)
    selectors += pseudo_selectors
    attribute_re = regex_patterns["attribute_selectors"]
    attribute_selectorss = re.findall(attribute_re, selector)
    selectors += attribute_selectorss
    score = len(selectors)
    return score


def get_color_codes_of_type(color_type: str, gradient: str) -> list:
    """returns all color codes of a particular type from a gradient

    Args:
        color_type: the type of color code it might be (hex, rgb, hsl,
            or keyword)
        gradient: the gradient code.

    Returns:
        colors: any color values that were found.
    """
    colors = []
    if color_type == "hsl":
        colors = re.findall(color_tools.hsl_all_forms_re, gradient)
    elif color_type == "rgb":
        colors = re.findall(color_tools.rgb_all_forms_re, gradient)
    elif color_type == "hex":
        colors = re.findall(color_tools.hex_re, gradient)
    elif color_type == "keywords":
        words = re.findall(r"[+a-z+A-Z]*", gradient)
        for i in words:
            # regex captures non-strings, so we don't process if empty
            if i:
                i = i.strip().lower()
                is_keyword = keyword.is_a_keyword(i.strip(" "))
                if is_keyword:
                    colors.append(i)
    if colors:
        # strip each color code (if hex regex)
        colors = [i.strip(" ") for i in colors]
    return colors


def get_color_rules_from_stylesheet(stylesheet: Stylesheet) -> list:
    """Gets all color-based rules from a stylesheet.

    Args:
        stylesheet: Stylesheet object.

    Returns:
        rules: a list of color-based rules"""
    rules = []
    for ruleset in stylesheet.rulesets:
        declaration_block = ruleset.declaration_block
        declarations = declaration_block.declarations
        for declaration in declarations:
            property = declaration.property
            if property == "color" or "background" in property:
                selector = ruleset.selector
                value = declaration.value
                if "background" in property:
                    background_color = get_background_color(declaration)
                    if not background_color:
                        continue
                    else:
                        value = background_color
                rules.append((selector, property, value))
    return rules


def get_colors_from_gradient(gradient: str) -> list:
    """extract all color codes from gradient

    Args:
        gradient: the CSS color gradient value.

    Returns:
        colors: a list of all colors found in the gradient.
    """
    colors = []
    # use regex to pull all possible color codes first
    color_types = ("hsl", "rgb", "hex", "keywords")
    for color_type in color_types:
        items = get_color_codes_of_type(color_type, gradient)
        if items:
            colors += items
    return colors


def get_comment_positions(code: (str)) -> Union[list, None]:
    """looks for index positions of first opening and closing comment.

    From this function, you can create a slice of a comment from the
    code. You would do this if you want to extract the comments from
    the code, or if you wanted to inspect what was in the comments, or
    even identify if there are comments.

    Note: this only works for the first comment in code. You would
    want to loop through the code extracting each comment one at a
    time using this function until it returns None.

    Args:
        code (str): the CSS code you want to extract comments from.

    Returns:
        list: a list of the index positions for the beginning and end
            of the first occuring comment in the code.
    """
    positions = []
    try:
        positions.append(code.index("/*"))
        positions.append(code.index("*/"))
        return positions
    except Exception as ex:
        print(ex)
        return


def get_declaration_block_from_selector(
    selector: str, style_sheet: Stylesheet
) -> str:
    declaration_block = ""
    for ruleset in style_sheet.rulesets:
        cur_selector = ruleset.selector
        if selector in cur_selector:
            # Check for grouped selectors
            grouped_selectors = cur_selector.split(",")
            if len(grouped_selectors) > 1:
                for item in grouped_selectors:
                    if selector in item:
                        if " " not in item:
                            declaration_block += ruleset.declaration_block.text
                            break
                        elif is_selector_at_end_of_descendant(selector, item):
                            declaration_block += ruleset.declaration_block.text
                            break

            # Check for descendant selectors
            if " " in cur_selector:
                # we have a descendant selector
                if is_selector_at_end_of_descendant(selector, cur_selector):
                    declaration_block += ruleset.declaration_block.text
                continue
            declaration_block += ruleset.declaration_block.text + "\n"
    return declaration_block


def get_declaration_value_by_property(
    block: Union[str, DeclarationBlock], property: str
) -> str:
    """returns the value of a property from a declaration block

    Args:
        block: the declaration block in question (could be as a string
            or as a DeclarationBlock)
        property: the property we are looking for

    Returns:
        value: the value of the property"""
    value = ""
    try:
        block = block.text
    except AttributeError:
        declarations = block.strip()
    declarations = block.split(";")
    for item in declarations:
        item = item.strip()
        try:
            # check for @media rules
            if "{" in item:
                item_split = item.split("{")
                item = item_split[1].strip()
            prop, val = item.split(":")
            if prop.lower().strip() == property.lower():
                value = val.strip()
                continue
        except ValueError:
            print("Doh! no colon")
    return value


def get_families(declaration_block: DeclarationBlock) -> list:
    """returns a list of all font families in a declaration block"""
    families = []
    for ruleset in declaration_block.declarations:
        if ruleset.property in ("font", "font-family"):
            families.append(ruleset.value)
    return families


def get_font_families(sheet: Stylesheet) -> list:
    """returns a list of all font families targeted in a stylesheet

    Args:
        sheet: a stylesheet object, which could be a style tag or entire
            stylesheet (*.css file)

    Returns:
        font_families: a list of dictionary objects that contain all selectors
            and their values (but only if the value is a font family)
    """
    font_families = []
    for ruleset in sheet.rulesets:
        block = ruleset.declaration_block
        families = get_families(block)
        if families:
            # create dict of selector and family
            selector = ruleset.selector

            # always take the last family as it would be an override in CSS
            family = families[-1]
            font_families.append({"selector": selector, "family": family})
    return font_families


def get_global_color_details(rulesets: Union[list, tuple]) -> list:
    """receives rulesets and returns data on global colors

    Note: a global selector is any selector that targets all elements
    in the DOM. Examples include `html`, `body`, `:root`, and
    the universal selector: `*`.

    Args:
        rulesets: a list or tuple of Ruleset objects

    Returns:
        global_rulesets: a list of dictionary objects that each contain
            a selector, a background color, a text color, contrast ratio,
            whether it passes at various levels.
    """
    # Are color and background color set on global selectors?
    global_selectors = ("html", "body", ":root", "*")
    global_rulesets = []
    for ruleset in rulesets:
        if ruleset.selector in global_selectors:
            selector = ruleset.selector
            background_color = ""
            color = ""
            for declaration in ruleset.declaration_block.declarations:
                if declaration.property == "background-color":
                    background_color = declaration.value
                elif declaration.property == "color":
                    color = declaration.value
                    if is_gradient(color):
                        colors = process_gradient(color)
                        todo = input("We have colors: " + colors)
                        print(todo)
                elif declaration.property == "background":
                    background_color = declaration.value
                    if is_gradient(background_color):
                        bg_colors = process_gradient(background_color)
                        print("We have bg colors: " + str(bg_colors))

            if background_color or color:
                contrast_ratio = "NA"
                passes_normal_aaa = False
                passes_normal_aa = False
                passes_large_aaa = False
                if background_color and color:
                    bg_hex = color_tools.get_hex(background_color)
                    color_hex = color_tools.get_hex(color)
                    contrast_ratio = color_tools.contrast_ratio(
                        bg_hex, color_hex
                    )
                    passes_normal_aaa = color_tools.passes_color_contrast(
                        "Normal AAA", bg_hex, color_hex
                    )
                    passes_normal_aa = color_tools.passes_color_contrast(
                        "Normal AA", bg_hex, color_hex
                    )
                    passes_large_aaa = color_tools.passes_color_contrast(
                        "Large AAA", bg_hex, color_hex
                    )
                global_rulesets.append(
                    {
                        "selector": selector,
                        "background-color": background_color,
                        "color": color,
                        "contrast_ratio": contrast_ratio,
                        "passes_normal_aaa": passes_normal_aaa,
                        "passes_normal_aa": passes_normal_aa,
                        "passes_large_aaa": passes_large_aaa,
                    }
                )
    return global_rulesets


def get_global_colors(file_path: str) -> dict:
    """Returns a dictionary of color rules applied the entire document.

    Global colors (in this context) are colors that apply to an entire
    document. Selectors that target the entire document are *, html,
    and body.

    Since it's possible that an author could accidentally override
    a color or background color, this function will remove any
    previous rules that are overridden in a file.

    NOTE: This should not consider an override if the would-be
    selector is in an @media ruleset, we won't treat it as an
    override.

    Args:
        file_path: the path to the file.

    Returns:
        global_color_rules: a dictionary of filenames and their global
            rulesets.
    """
    global_color_rules = {}
    sheets = get_all_stylesheets_by_file(file_path)
    if sheets:
        for sheet in sheets:
            rules = sheet.rulesets
            global_colors = get_global_color_details(rules)
            if global_colors:
                # Have we added the file to the global rules?
                if not global_color_rules.get(file_path):
                    global_color_rules[file_path] = []
                for gc in global_colors:
                    global_color_rules[file_path].append(gc)
        if sheets and len(global_color_rules.get(file_path)) > 1:
            # figure out the override
            global_colors = adjust_overrides(file_path, global_color_rules)
            adjusted_rule = global_colors.get(file_path)
            global_color_rules[file_path] = adjusted_rule
    return global_color_rules


def get_header_color_details(rulesets: Union[list, tuple]) -> list:
    """receives rulesets and returns data on colors set by headers

    This function will look through all rules in a ruleset and extracts
    the rules that target color or background color for a heading (h1
    -h6).

    Args:
        rulesets: a list or tuple of Ruleset objects.

    Returns:
        header_rulesets: a list of dictionary objects that each contain
            a selector, a background color, and a text color.
    """
    header_rulesets = []
    for ruleset in rulesets:
        selector = ruleset.selector
        # check selector for having a header
        heading_selectors = get_header_selectors(selector)
        if heading_selectors:
            # get color data
            background_color = ""
            color = ""
            for declaration in ruleset.declaration_block.declarations:
                if declaration.property == "background-color":
                    background_color = declaration.value
                elif declaration.property == "color":
                    color = declaration.value
                elif declaration.property == "background":
                    # check to see if the color value is present
                    print("it's time to figure out the background shorthand")
                if background_color and color:
                    break

            # then apply color data to all others
            if background_color or color:
                for h_selector in heading_selectors:
                    header_rulesets.append(
                        {
                            "selector": h_selector,
                            "background-color": background_color,
                            "color": color,
                        }
                    )

    return header_rulesets


def get_header_selectors(selector: str) -> list:
    """takes selector and returns any selector that selects an h1-h6

    Args:
        selector: A CSS selector

    Returns:
        header_selectors: a list of selectors that target a heading.
    """
    # NOTE the following:
    # a selector is only selecting a header if it's the last item
    # example: header h1 {} does but h1 a {} does not
    header_selectors = []
    selectors = [sel.strip() for sel in selector.split(",")]
    if selectors[0]:
        for selector in selectors:
            items = selector.split()
            pattern = regex_patterns["header_selector"]
            h_match = re.search(pattern, items[-1])
            if h_match:
                header_selectors.append(selector)
    return header_selectors


def get_id_score(selector: str) -> int:
    """receives a selector and returns # of ID selectors

    Args:
        selector (str): the complete CSS selector

    Returns:
        score: the number of ID selectors.
    """
    pattern = regex_patterns["id_selector"]
    id_selectors = re.findall(pattern, selector)
    score = len(id_selectors)
    return score


def get_link_color_data(project_path: str) -> list:
    """returns all colors applied to links.

    Identifies all selectors that target a link, and gets a
    list of dictionaries that identify colors.

    Args:
        project_path: path to project folder

    Returns:
        link_styles: a list of link color data applied to each
            file that includes a link color data"""
    link_styles = []
    color_contrast_data = get_project_color_contrast(project_path)
    for item in color_contrast_data:
        selector = item[1]
        if not is_link_selector(selector):
            continue
        # it must be a link selector, let's get our data
        link_styles.append(item)
    return link_styles


def get_number_required_selectors(
    selector_type: str, sheet: Stylesheet
) -> int:
    """returns # of a specific selector type in a stylesheet

    Args:
        selector_type: what kind of selector we're looking for.
        sheet: the Stylesheet object we're inspecting.

    Returns:
        count: the number of occurrences of the selector.
    """
    count = 0
    pattern = regex_patterns[selector_type]
    for selector in sheet.selectors:
        matches = re.findall(pattern, selector)
        count += len(matches)
    # Loop through all nested @rules and count selectors
    for rules in sheet.nested_at_rules:
        for selector in rules.selectors:
            matches = re.findall(pattern, selector)
            count += len(matches)
    return count


def get_project_color_contrast(
    project_path: str, normal_goal="Normal AAA", large_goal="Large AAA"
) -> list:
    """checks all color rules for each file in a project folder for contrast

    Args:
        project_path: path to project folder.
        normal_goal: color contrast goal for most text in document (all except
            headers) - could be 'Normal AAA' or 'Normal AA' (default set to
            'Normal AAA')
        large_goal: color contrast goal for large (headings) text. May be
            'Large AAA' or 'Large AA' (default is set to 'Large AAA')

    Returns:
        results: a list of tuples. Each tuple contains a filename, selector,
            goal, color, bg_color, computed contrast ratio, passes_color"""

    results = []
    global_color_rules = get_project_global_colors(project_path)
    for file in global_color_rules.keys():
        global_details = global_color_rules.get(file)
        all_color_rules = get_all_color_rules(file)
        if global_details:
            if isinstance(global_details, list):
                if len(global_details) == 1:
                    global_details = global_details[0]
            global_color = global_details.get("color")
            global_bg = global_details.get("background-color")
        items = list(all_color_rules.keys())
        heading_tag_re = r"h[1-6]"
        for key in items:
            # skip first key and any key that is a global selector
            if key == "file":
                continue
            goal = normal_goal
            if re.search(heading_tag_re, key):
                goal = large_goal
            else:
                goal = normal_goal
            selector = key
            details = all_color_rules.get(selector)
            color = details.get("color")
            if not color:
                if not global_color:
                    color = "#000000"
                else:
                    color = global_color
            color_hex = color_tools.get_hex(color)
            bg_color = details.get("background-color")
            if not bg_color:
                if not global_bg:
                    bg_color = "#ffffff"
                else:
                    bg_color = global_bg
            bg_hex = color_tools.get_hex(bg_color)
            passes_color = color_tools.passes_color_contrast(
                goal, bg_hex, color_hex
            )
            contrast_ratio = color_tools.contrast_ratio(color_hex, bg_hex)
            results.append(
                (
                    file,
                    selector,
                    goal,
                    color,
                    bg_color,
                    contrast_ratio,
                    passes_color,
                )
            )
    return results


def get_project_global_colors(project_path: str) -> dict:
    """Returns a dictionary of color rules applied to all html files
    in a project folder.

    Global colors (in this context) are colors that apply to an entire
    document. Selectors that target the entire document are *, html,
    and body.

    Since it's possible that an author could accidentally override
    a color or background color, this function will remove any
    previous rules that are overridden in a file.

    NOTE: This should not consider an override if the would-be
    selector is in an @media ruleset, we won't treat it as an
    override.

    Args:
        project_path: the project folder path.

    Returns:
        global_color_rules: a dictionary of filenames and their global
            rulesets.
    """
    global_color_rules = {}
    styles_by_files = get_styles_by_html_files(project_path)
    for file in styles_by_files:
        filename = file.get("file")
        sheets = file.get("stylesheets")
        if sheets:
            for sheet in sheets:
                rules = sheet.rulesets
                global_colors = get_global_color_details(rules)
                if global_colors:
                    # Have we added the file to the global rules?
                    if not global_color_rules.get(filename):
                        global_color_rules[filename] = []
                    for gc in global_colors:
                        global_color_rules[filename].append(gc)
        if sheets and len(global_color_rules.get(filename)) > 1:
            # figure out the override
            global_colors = adjust_overrides(filename, global_color_rules)
            adjusted_rule = global_colors.get(filename)
            global_color_rules[filename] = adjusted_rule
    return global_color_rules


def get_selector_type(selector: str) -> str:
    """returns the type of selector it is.

    Cycles through selector regexes to see which one it is. When it has a
    match, it returns the key.

    Args:
        selector: the selector in question.

    Returns:
        str: the key of the selector regex dictionary if there's a match."""
    for type, regex in regex_patterns.items():
        match = re.match(regex, selector)
        if "#" in selector and selector.index("#") != len(selector) - 1:
            return "id_selector"
        if match:
            if type == "single_type_selector":
                return "type_selector"
            return type


def get_specificity(selector: str) -> str:
    """Gets the specificity score on the selector.

    According to MDN's article on Specificity, Specificity is the
    algorithm used by browsers to determine the CSS declaration that
    is the most relevant to an element, which in turn, determines
    the property value to apply to the element.

    The specificity algorithm calculates the weight of a CSS selector
    to determine which rule from competing CSS declarations gets
    applied to an element.

    The specificity score is basically a number, and if two selectors
    target the same element, the selector with the highest specificity
    score wins. The number is like a 3-digit number, where the "ones"
    place is the number of type selectors, the "tens" place is the
    number of class selectors, and the "hundreds" place is the number
    of id selectors.

    For example, the selector: `h1, h2, h3` has a specificity of `003`
    because there are neither id nor class selectors, but there are 3
    type selectors.

    The selector: `nav#main ul` has a specificity of `102` because
    there is one id selector (`#main`) and two type selectors (`nav`
    and `ul`).

    Args:
        selector (str): the CSS selector in question.

    Returns:
        specificity: the specificity score.
    """
    id_selector = get_id_score(selector)
    class_selector = get_class_score(selector)
    pseudo_element_selector = get_psuedo_element_score(selector)
    type_selector = get_type_score(selector)
    type_count = type_selector + pseudo_element_selector
    specificity = "{}{}{}".format(id_selector, class_selector, type_count)
    return specificity


def get_psuedo_element_score(selector):
    pseudo_element_selector = 0
    psuedo_element_re = regex_patterns["pseudoelement_selector"]
    matches = re.findall(psuedo_element_re, selector)
    pseudo_element_selector = len(matches)
    return pseudo_element_selector


def get_styles_by_html_files(project_path: str) -> list:
    """Returns a list of filenames with their stylesheets in order of
    appearance.

    This will identify all HTML documents in the project folder. For
    each HTML document, it will create a dictionary with two keys:
    filename for the HTML document and stylesheets for a list of the
    css styles created through link tags or style tags.

    As it uses get_all_stylesheets_by_files, you can be sure that no
    external stylesheets (https://...) will be included in the list.

    Args:
        project_path: a string of the path to the project folder you
            want to test.

    Returns:
        styles_by_html_files: a list of dictionary objects indicating
            each html document and its styles in order of appearance.
    """
    styles_by_html_files = []
    html_files = html_tools.get_all_html_files(project_path)
    for file in html_files:
        file_data = get_all_stylesheets_by_file(file)
        styles_by_html_files.append({"file": file, "stylesheets": file_data})
    return styles_by_html_files


def get_type_score(selector: str) -> int:
    """receives a selector and returns the number of type selectors

    Args:
        selector: the complete CSS selector

    Returns:
        score: the number of type selectors.
    """
    pattern = regex_patterns["type_selector"]
    selectors = re.findall(pattern, selector)
    score = len(selectors)
    return score


def get_unique_font_rules(project_folder: str) -> list:
    """Returns list of files with only unique font rules applied.

    Args:
        project_folder: a string path to the project folder we are testing.

    Returns:
        project_font_data: a list of dictionary objects that each store
            the file where styles are applied and their unique font-related
            rules.
    """
    styles_by_html_files = get_styles_by_html_files(project_folder)
    font_families_tests = []
    for file in styles_by_html_files:
        style_sheets = file.get("stylesheets")
        unique_rules = []
        unique_font_values = []
        unique_font_selectors = []
        font_rules = []
        for sheet in style_sheets:
            font_families = get_font_families(sheet)
            if font_families:
                for family in font_families:
                    font_rules.append(family)
        # Let's build results for this page
        for rule in font_rules:
            if rule:
                if rule not in unique_rules:
                    unique_rules.append(rule)
                    selector = rule.get("selector")
                    value = rule.get("family")
                    if selector not in unique_font_selectors:
                        unique_font_selectors.append(selector)
                    if value not in unique_font_values:
                        unique_font_values.append(value)
                else:
                    print()
        # apply the file, unique rules, unique selectors, and unique values
        filename = file.get("file")
        file_data = {"file": filename, "rules": unique_rules}
        font_families_tests.append(file_data)
    return font_families_tests


def get_variables(text: str) -> list:
    """returns a list of css variables and their values.

    This will extract any variables if they exist, copy the
    variable name and its value and create a dictionary object
    and append to list.

    Args:
        text: full text of css stylesheet

    Returns:
        variables: a list of variable dictionaries each with a
            key for the variable and a value for its value.
    """
    variables = []
    variable_split = text.split(":root {")
    if len(variable_split) == 1:
        return []
    variable_text = variable_split[1].strip()
    variables_list = variable_text.strip().split(";")
    for var in variables_list:
        var = var.strip()
        if "}" in var:
            break
        variable, value = var.split(":")
        var_dict = {"variable": variable, "value": value}
        variables.append(var_dict)
    return variables


def restore_braces(split: list) -> list:
    """restore the missing braces removed by the .split() method

    This is more of a helper function to make sure that after splitting
    at-rule code by two curly braces, we restore it back.

    In CSS, to find the end of a nested @rule, you can use the
    following code: `css_code.split("}}")` This is because a nested
    @rule ends with two closing curly braces: one for the last
    declaration, and the other for the end of the nested @rule.

    Args:
        split (list): a list created by the split method on CSS code

    Returns:
        list: the list but with the double closing braces restored from
            the split.
    """
    result = []
    split = tuple(split)
    if len(split) <= 1:
        return split
    for item in split:
        # only restore braces if there is an at-rule
        # this is more of a precaution in case there we
        # two closing brackets on accident.
        if len(item) > 0 and "@" in item:
            item = item + "}}"
            result.append(item)
    return result


def minify_code(text: str) -> str:
    """remove all new lines, tabs, and double spaces from text

    This is a classic function for web developers to minify their code
    by removing new lines, tabs, and any double spaces from text.

    Args:
        text: the code you want to minify.

    Returns:
        text: the code without all the additional whitespace."""
    text = text.replace("\n", "")
    text = text.replace("  ", "")
    text = text.replace("\t", "")
    return text


def has_vendor_prefix(property: str) -> bool:
    """Checks a property to see if it uses a vendor prefix or not.

    Args:
        property: A CSS property in string format.

    Returns:
        has_prefix: whether the property uses a vendor prefix or not.
    """
    vendor_prefixes = ("-webkit-", "-moz-", "-o-", "-ms-")
    has_prefix = False
    for prefix in vendor_prefixes:
        if prefix in property:
            has_prefix = True
            break
    return has_prefix


def is_gradient(value: str) -> bool:
    """checks a CSS value to see if it's using a gradient or not.

    Args:
        value (str): a CSS value.

    Returns:
        uses_gradient: whether it uses a gradient or not.
    """
    uses_gradient = "gradient" in value
    return uses_gradient


def process_gradient(code: str) -> list:
    """returns list of all colors from gradient sorted light to dark

    This function is a work in progress. The goal is to eventually use
    it to determine whether a gradient meets color contrast
    accessibility ratings when compared against another color or
    color gradient.

    In order to do this, the plan is to find
    the lightest color and the darkest color, so we can check both
    sides of the range. If the lightest or darkest color fails color
    contrast, then it's a fail. If both pass, then all colors in
    between will pass.

    Note: we may be adding more to this and refactoring functionality.

    Args:
        code: the color gradient value

    Returns:
        only_colors: a list of just color codes sorted by luminance
    """
    colors = []
    data = code.split("),")

    # split the last datum in data into two
    last_item = data[-1].strip()
    last_split = last_item.split("\n")
    if len(last_split) == 2:
        data.append(last_split[1])

    # remove all vendor prefixes
    pattern = regex_patterns["vendor_prefix"]
    for datum in data:
        datum = datum.strip()
        if not re.match(pattern, datum):
            colors.append(datum)

    # capture only color codes and append to colors
    only_colors = []
    if colors:
        # grab only color codes (Nothing else)
        for gradient in colors:
            color_codes = get_colors_from_gradient(gradient)
            if color_codes:
                only_colors += color_codes
    only_colors = sort_color_codes(only_colors)
    return only_colors


def separate_code(code: str) -> dict:
    """splits code into two lists: code & comments

    Args:
        code (str): the stylesheet or style tag code

    Returns:
        splitzky: a dictionary with two lists: a list of code snippets
            without comments, and a list of comments.

    Raises:
        ValueError: if there is only one comment symbol: either /* or
            */ but not both (a syntax error)
    """
    code = code.strip()
    splitzky = {"code": [], "comments": []}

    new_code = []
    comments = []
    # Get positions of comments and place all code up to the comments
    # in code and comments in comments
    # do this till all code has been separated
    while code:
        positions = get_comment_positions(code)
        if positions and len(positions) == 2:
            start = positions[0]
            stop = positions[1]
            if code[:start]:
                new_code.append(code[:start])
            if code[start : stop + 2]:
                comments.append(code[start : stop + 2])
            code = code[stop + 2 :]
            code = code.strip()
        else:
            if "/*" not in code and "*/" not in code:
                new_code.append(code)
                code = ""
            else:
                # we're here because we have only one valid comment
                # symbol
                if "/*" in code:
                    has, has_not = (
                        "opening comment symbol: /*",
                        "closing comment symbol: */",
                    )
                else:
                    has, has_not = (
                        "closing comment symbol: */",
                        "opening comment symbol: /*",
                    )
                msg = "There's a syntax issue with your code comments."
                msg += " You have a {0} but no {1}.".format(has, has_not)
                raise ValueError(msg)
    splitzky["code"] = new_code
    splitzky["comments"] = comments
    return splitzky


def sort_color_codes(codes: Union[list, tuple]) -> list:
    """sorts color codes from light to dark (luminance)

    Args:
        codes: a list or tuple of color values.

    Returns:
        sorted: a list of initial color values but in order from
            lightest to darkest (using luminance).
    """
    # convert code to rgb then calculate luminance
    colors = []
    for c in codes:
        # get the color type and convert to hsl
        temp_c = c
        color_type = color_tools.get_color_type(c)
        has_alpha = color_tools.has_alpha_channel(c)
        is_hex = color_tools.is_hex(temp_c)
        if has_alpha and not is_hex:
            temp_c = remove_alpha(c)
        if "hsl" not in color_type:
            if is_hex:
                rgb = color_tools.hex_to_rgb(temp_c)
            else:
                rgb = temp_c
        else:
            rgb = color_tools.hsl_to_rgb(c)
        if "<class 'str'>" == str(type(rgb)):
            r, g, b = color_tools.extract_rgb_from_string(rgb)
            light = color_tools.luminance((int(r), int(g), int(b)))
        else:
            light = color_tools.luminance(rgb)
        colors.append([light, c])
    colors.sort()
    colors.reverse()
    sorted = []
    for i in colors:
        sorted.append(i[1])
    return sorted


def remove_alpha(color_code: str) -> str:
    """removes the alpha channel from rgba or hsla

    Honestly, I'm not sure if this is even needed. I am looking to
    eventually move over to the APCA algorithm for testing color
    contrast accessibility, but at this point, I cannot find the
    algorithm. If and when I do, I will work to replace the current
    algorithm (WCAG AA/AAA rating).

    Args:
        color_code: the color code (hex, rgb, or hsl) with an alpha
            channel.

    Returns:
        color_code: the color code without the alpha channel.
    """
    color_code = color_code.split(",")
    a = color_code[0].index("a")
    color_code[0] = color_code[0][:a] + color_code[0][a + 1 :]
    color_code.pop(-1)
    color_code = ",".join(color_code)
    color_code += ")"
    return color_code


def is_required_selector(selector_type: str, selector: str) -> bool:
    """checks selector to see if it's required type or not.

    Example: you may wish to loop through selectors and see which
    ones are class selectors, or id selectors, etc..

    It makes use of the list of regex_patterns for selector type.

    Args:
        selector_type: the type of selector in question, such as
            an id, class, type, etc.
        selector: the selector we are checking.

    Returns:
        match: whether the selector matches the type.
    """
    pattern = regex_patterns[selector_type]
    match = bool(re.search(pattern, selector))
    return match


def has_required_property(property: str, sheet: Stylesheet) -> bool:
    """checks stylesheet for a particular property

    Args:
        property: the property we're looking for
        sheet (Stylesheet): the Stylesheet object we're inspecting

    Returns:
        has_property: whether the Stylesheet has the property or not.
    """
    has_property = False
    for rule in sheet.rulesets:
        for declaration in rule.declaration_block.declarations:
            if declaration.property == property:
                return True
    return has_property


def passes_global_color_contrast(file: str, goal="Normal AAA") -> bool:
    """determines whether a file passes global color contrast

    Args:
        file: path to file in question.

        goal: what's the color contrast goal - set to Normal AAA by
            default.

    Returns:
        meets: whether it passes contrast goals or not
    """
    global_colors = get_global_colors(file)
    details = global_colors.get(file)
    goal_key = "passes_" + goal.replace(" ", "_").lower()
    meets = details.get(goal_key)
    return meets


def is_selector_at_end_of_descendant(selector: str, cur_selector: str) -> bool:
    """returns whether a selector is at the end of a descendant selector"""
    selector_at_end_of_descendant = False
    selectors = cur_selector.split()
    if selector in selectors[-1]:
        # selector must be at the end of descendant selector
        # or it doesn't count
        selector_at_end_of_descendant = True
    return selector_at_end_of_descendant


def has_link_selector(sheet: Stylesheet) -> bool:
    """returns whether any style in a stylesheet targets a hyperlink

    There could be one or more link selectors. This will check each possible
    link selector (or psuedoselector). It only has to target a link and not
    a descendant of a link.

    Args:
        sheet: the stylesheet object.

    Returns:
        has_selector: whether there is a selector that targets a link"""
    has_selector = False
    all_selectors = sheet.selectors
    for selector in all_selectors:
        selector_copy = selector
        if " " in selector:
            # we need to add a space at the end for the split to work
            selector = selector.strip() + " "
            selector_split = selector.split()
            selector_copy = selector_split[-1]
        if selector_copy == "a":
            has_selector = True
            break
        # Check selector_copy to see if it's an anchor
        regex_pattern = regex_patterns.get("advanced_link_selector")
        selector_match = re.search(regex_pattern, selector_copy)
        if selector_match:
            has_selector = True
            break
    return has_selector


def is_link_selector(selector: str) -> bool:
    """returns a true if selector targets a link

    Args:
        selector: the selector in question"""
    selector_copy = selector
    if " " in selector:
        # we need to add a space at the end for the split to work
        selector = selector.strip() + " "
        selector_split = selector.split()
        selector_copy = selector_split[-1]
    if selector_copy == "a":
        return True
        # Check selector_copy to see if it's an anchor
    regex_pattern = regex_patterns.get("advanced_link_selector")
    selector_match = re.search(regex_pattern, selector_copy)
    return bool(selector_match)


def get_all_project_stylesheets(project_dir: str) -> list:
    """returns a list of all styles and stylesheets from a project folder.

    This includes styles from style tags as well as linked stylesheets.

    Args:
        project_dir: the relative link to the folder with the web docs.

    Returns:
        all_files_styles: a list of all stylesheets and style tag contents.
    """
    directory = project_dir
    html_files = clerk.get_all_files_of_type(directory, "html")
    all_files_styles = []
    for file in html_files:
        filename = clerk.get_file_name(file)
        stylesheets = get_all_stylesheets_by_file(file)
        all_files_styles.append((filename, stylesheets))
    return all_files_styles


def no_style_attributes_allowed_report(project_dir: str) -> list:
    """returns a report on whether HTML docs use style attributes or not.

    Only call this report if you do not allow a style attribute in an
    HTML doc

    Args:
        project_dir: the relative link to the folder with the web docs.

    Returns:
        report: a list of all HTML docs and a pass or fail message.
    """
    report = []

    html_files = clerk.get_all_files_of_type(project_dir, "html")
    for file in html_files:
        try:
            has_style_attr = html_tools.has_style_attribute_data(file)
        except AttributeError:
            continue
        if has_style_attr:
            result = f"fail: {file} uses style attributes"
        else:
            result = f"pass: {file} does not use style attributes"
        report.append(result)
    return report


def styles_applied_report(project_dir: str) -> list:
    """returns a report of all files in a project folder that apply styles

    This lets us know for each HTML doc if they apply styles (pass) or
    if they do not apply styles (fail)

    Args:
        project_dir: a relative path to the project folder.

    Returns:
        report: a list of HTML docs and whether they pass or fail (pass) means
            they did apply styles and fail is the opposite.
    """
    report = []
    html_files = clerk.get_all_files_of_type(project_dir, "html")
    for file in html_files:
        styles = get_all_stylesheets_by_file(file)
        if not styles:
            results = f"fail: {file} does NOT apply CSS."
        else:
            results = f"pass: {file} applies CSS."
        report.append(results)
    return report


def fonts_applied_report(project_dir: str, min=1, max=2) -> list:
    """returns a report of all files in a project folder that apply font
    families.

    You can set the minimum and maximum number of fonts applied per page.

    Args:
        project_dir: the relative path to the project folder we want to check.
        min: the minimum number of fonts applied per file.
        max: the maximum number of fonts applied per file.
    Returns:
        report: a list of font data results.
    """
    report = []
    all_file_data = get_styles_by_html_files(project_dir)
    for file in all_file_data:
        number_of_fonts = 0
        filename = clerk.get_file_name(file.get("file"))
        stylesheets = file.get("stylesheets")
        font_styles = []
        for sheet in stylesheets:
            font_details = get_font_families(sheet)
            number_of_fonts += len(font_details)
            for item in font_details:
                selector = item.get("selector")
                family = item.get("family")
                if "," in family:
                    first_font = family.split(",")[0].strip()
                else:
                    first_font = family
                first_font = first_font.replace("'", "")
                first_font = first_font.replace('"', "")
                if first_font.lower() == "times new roman":
                    results = f"fail: {filename}: {selector} element was set "
                    results += "to the default font"
                elif number_of_fonts >= min and number_of_fonts <= max:
                    results = f"pass: {filename}: {selector} element "
                    results += f"was set to {first_font}"
                elif number_of_fonts < min:
                    results = f"fail: {filename} did not apply {min} fonts, "
                    results += f"instead, it applied {number_of_fonts} fonts."
                if results not in font_styles:
                    font_styles.append(results)
        # We have all font styles applied
        if not font_styles:
            report.append(f"fail: {filename} No modified fonts for {filename}")
        else:
            report += font_styles
    if not report:
        report.append("fail: no html files to apply font styling to")
    return report


def get_global_color_report(project_dir: str, level="aaa") -> list:
    """Returns a report on which files in a project apply global colors

    Args:
        project_dir: the project folder path.
        level: whether we are testing for Normal AAA or Normal AA

    Returns:
        report: a list of files and a pass or fail message for each."""
    report = []
    all_file_data = get_all_project_stylesheets(project_dir)
    for data in all_file_data:
        filename = data[0]
        passes = []
        for sheet in data[1]:
            rules = sheet.rulesets
            global_color_data = get_global_color_details(rules)
            if global_color_data:
                for item in global_color_data:
                    file, result = get_color_data(filename, item, level)
                    passes.append(f"pass: {file} {result}")
        if passes:
            details = ""
            for detail in passes:
                details += detail
        else:
            details = f"fail: {filename} does NOT apply global colors"
        report.append(details)
    if not report:
        report.append("fail: no html files to apply color styles to")
    return report


def get_color_data(file: str, color_details: dict, level="aaa") -> tuple:
    """returns the color contrast data on a color.

    pulls out the selector, background color, text color, contrast
    ratio, and whether it passes color contrast.

    Args:
        file: just the name of the file (not path).
        color_details: tuple of full color & bg color details.
        level: the level of normal text (AAA or AA).

    Returns:
        color_data: a tuple with filename and results as a string"""
    selector = color_details.get("selector")
    bg_color = color_details.get("background-color")
    color = color_details.get("color")
    contrast_ratio = color_details.get("contrast_ratio")
    if level == "aaa":
        passes = color_details.get("passes_normal_aaa")
    else:
        passes = color_details.get("passes_normal_aa")
    if passes:
        results = "passes global colors"
    else:
        results = f"{selector} {bg_color} and {color} fail with a contrast"
        results += f" ratio of {contrast_ratio}."
    color_data = (file, results)
    return color_data


def get_heading_color_report(project_dir: str) -> list:
    """Returns a report on which files in a project apply heading colors

    For now, we just want to have at least a color or background color
    applied.

    Args:
        project_dir: the project folder path.

    Returns:
        report: a list of files and a pass or fail message for each."""
    report = []
    header_re = regex_patterns.get("header_selector")
    if project_dir[-1] != "/":
        project_dir += "/"
    all_file_data = get_all_project_stylesheets(project_dir)
    for file in all_file_data:
        filename = file[0]
        filepath = project_dir + filename
        all_color_rules = get_all_color_rules(filepath)
        header_selectors = []
        for key, val in all_color_rules.items():
            if key == "file":
                continue
            is_header_selector = re.findall(header_re, key)
            if is_header_selector:
                # we have a header selector
                # we only need to check color
                color_data = val
                color_value = color_data.get("color")
                bg_value = color_data.get("background-color")
                if color_value:
                    if bg_value:
                        header_selectors.append(
                            (filename, color_value, bg_value)
                        )
                    else:
                        header_selectors.append((filename, color_value, None))
                if bg_value:
                    header_selectors.append((filename, None, bg_value))
        if header_selectors:
            report.append(f"pass: {filename} applies colors to headers")
        else:
            report.append(f"fail: {filename} does NOT apply colors to headers")
    if not report:
        report.append("fail: no html files to apply header colors to")
    return report


if __name__ == "__main__":
    insane_gradient = """
    -moz-radial-gradient(0% 200%, ellipse cover,
    rgba(143, 193, 242, 0.22) 10%,rgba(240, 205, 247,0) 40%),
    -webkit-radial-gradient(0% 200%, ellipse cover,
    rgba(143, 193, 242, 0.22) 10%,rgba(240, 205, 247,0) 40%),
    -o-radial-gradient(0% 200%, ellipse cover,
    rgba(143, 193, 242, 0.22) 10%,rgba(240, 205, 247,0) 40%),
    -ms-radial-gradient(0% 200%, ellipse cover,
    rgba(143, 193, 242, 0.22) 10%,rgba(240, 205, 247,0) 40%),
    radial-gradient(0% 200%, ellipse cover, antiquewhite 10%,
    rgba(240, 205, 247,0) 40%),
    -moz-linear-gradient(top, rgba(169, 235, 206,.25) 0%,
    rgba(42,60,87,.4) 200%),
    -ms-linear-gradient(-45deg, #46ABA6 0%, #092756 200%),
    linear-gradient(-45deg, maroon 0%, #092756 200%)
    """

    insane_gradient = """
-moz-radial-gradient(0% 200%, ellipse cover,
rgba(143, 193, 242, 0.22) 10%,rgba(240, 205, 247,0) 40%),
-webkit-radial-gradient(0% 200%, ellipse cover,
rgba(143, 193, 242, 0.22) 10%,rgba(240, 205, 247,0) 40%),
-o-radial-gradient(0% 200%, ellipse cover,
rgba(143, 193, 242, 0.22) 10%,rgba(240, 205, 247,0) 40%),
-ms-radial-gradient(0% 200%, ellipse cover,
rgba(143, 193, 242, 0.22) 10%,rgba(240, 205, 247,0) 40%),
radial-gradient(0% 200%, ellipse cover,
rgba(143, 193, 242, 0.22) 10%,rgba(240, 205, 247,0) 40%),
-moz-linear-gradient(top, rgba(169, 235, 206,.25) 0%,
rgba(42,60,87,.4) 200%),
-ms-linear-gradient(-45deg, #46ABA6 0%, #092756 200%)',
linear-gradient(-45deg, #46ABA6 0%, #092756 200%)'
"""
    results = process_gradient(insane_gradient)
    print(results)
    project_path = "tests/test_files/large_project/"
    css_path = project_path + "css/general.css"
    html_path = project_path + "index.html"
    wonka = "tests/test_files/wiliwonka.html"
    test_stuff = get_all_color_rules(wonka)
    tests = get_project_color_contrast(project_path)
