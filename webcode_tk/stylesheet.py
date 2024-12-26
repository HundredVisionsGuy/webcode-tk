""" stylesheet
This module is a class to define CSS stylesheets for use in css_tools and
others.
"""
import re

from webcode_tk import color_tools
from webcode_tk import css_tools


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
        self.__clean_text()
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

    def __clean_text(self):
        """cleans up CSS like removing extra line returns

        This is here because if a student has more than 2 blank lines, it
        could trigger an attribute error (at least it did in the past)
        """
        text_to_clean = self.text
        split_text = text_to_clean.split("\n")
        cleaned_text = ""
        consecutive_blanks = 0
        for line in split_text:
            if not line:
                consecutive_blanks += 1
            if consecutive_blanks > 1:
                consecutive_blanks = 1
                continue
            else:
                if not line and cleaned_text:
                    cleaned_text += "\n"
                cleaned_text += line + "\n"
        if cleaned_text[-1:] == "\n":
            cleaned_text = cleaned_text[:-1].strip()
        self.text = cleaned_text

    def __minify(self):
        """Removes all whitespace, line returns, and tabs from text."""
        self.text = css_tools.minify_code(self.text)

    def __replace_variables(self):
        """Looks for and replaces any variables set in stylesheet with
        the variable's values."""
        # get a list of all variables and their values
        variable_list = css_tools.get_variables(self.text)

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
        css_split = css_tools.restore_braces(css_split)

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
                    if css_tools.has_vendor_prefix(value):
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
            self.__text = css_tools.minify_code(text)
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
