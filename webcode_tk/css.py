""" CSS
This module is a set of tools to analyze CSS syntax as well as properties
and values.
"""
import re
from typing import Union

from webcode_tk import color_keywords as keyword
from webcode_tk import colortools

# regex patterns for various selectors
regex_patterns: dict = {
    "vendor_prefix": r"\A-moz-|-webkit-|-ms-|-o-",
    "header_selector": r"h[1-6]",
    "id_selector": r"#\w+",
    "class_selector": r"\.\w+",
    "pseudoclass_selector": r":\w+",
    "attribute_selector": r"\[\w+=\w+]",
    "type_selector": r"([^#:\+.\[=a-zA-Z][a-zA-Z$][a-zA-Z1-6]*|^\w*)",
    "descendant_selector": r"\w+\s\w+",
    "child_combinator": r"\w+\s*>\s*\w+",
    "adjacent_sibling_combinator": r"\w+\s*\+\s*\w+",
    "general_sibling_combinator": r"\w+\s*~\s*\w+",
    "grouped_selector": r"\w+\s*,\s*\w+",
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
        self.__extract_comments()
        self.__extract_nested_at_rules()
        self.__extract_rulesets()
        self.__set_selectors()

    def __minify(self):
        """Removes all whitespace, line returns, and tabs from text."""
        self.text = minify_code(self.text)

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

    def get_color_ruleset(self, ruleset) -> list:
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
                    # skip if has vendor prefix
                    if has_vendor_prefix(value):
                        continue
                    # skip if not valid color value
                    if not colortools.is_color_value(value):
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
        # validate before trying to set the declaration.
        try:
            self.validate_declaration()
            self.is_valid = True
            self.set_declaration()
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
            print(item)
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
    type_selector = get_type_score(selector)
    specificity = "{}{}{}".format(id_selector, class_selector, type_selector)
    return specificity


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


def get_class_score(selector: str) -> int:
    """receives a selector and returns the class score

    The class score represents the combined number of class,
    pseudo-class, and attribute selectors.

    Args:
        selector (str): the complete CSS selector

    Returns:
        score: the number of class selectors, which includes attribute
        and pseudoclass selectors.
    """
    class_re = regex_patterns["class_selector"]
    selectors = re.findall(class_re, selector)
    pseudo_re = regex_patterns["pseudoclass_selector"]
    pseudo_selectors = re.findall(pseudo_re, selector)
    selectors += pseudo_selectors
    attribute_re = regex_patterns["attribute_selector"]
    attribute_selectors = re.findall(attribute_re, selector)
    selectors += attribute_selectors
    score = len(selectors)
    return score


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


def get_global_color_details(rulesets: Union[list, tuple]) -> list:
    """receives rulesets and returns data on global colors

    Note: a global selector is any selector that targets all elements
    in the DOM. Examples include `html`, `body`, `:root`, and
    the universal selector: `*`.

    Args:
        rulesets: a list or tuple of Ruleset objects

    Returns:
        global_rulesets: a list of dictionary objects that each contain
            a selector, a background color, and a text color.
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
                global_rulesets.append(
                    {
                        "selector": selector,
                        "background-color": background_color,
                        "color": color,
                    }
                )
    return global_rulesets


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
        color_type = colortools.get_color_type(c)
        has_alpha = colortools.has_alpha_channel(c)
        is_hex = colortools.is_hex(temp_c)
        if has_alpha and not is_hex:
            temp_c = remove_alpha(c)
        if "hsl" not in color_type:
            if is_hex:
                rgb = colortools.hex_to_rgb(temp_c)
            else:
                rgb = temp_c
        else:
            rgb = colortools.hsl_to_rgb(c)
        if "<class 'str'>" == str(type(rgb)):
            r, g, b = colortools.extract_rgb_from_string(rgb)
            light = colortools.luminance((int(r), int(g), int(b)))
        else:
            light = colortools.luminance(rgb)
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


def get_color_codes_of_type(color_type: str, gradient: str) -> list:
    """returns all color codes of a particular type (hsl, rgb, etc.)

    Args:
        type: the type of color code it might be (hex, rgb, hsl, or
            keyword)
        gradient: the gradient code.

    Returns:
        colors: any color values that were found.
    """
    colors = []
    if color_type == "hsl":
        colors = re.findall(colortools.hsl_all_forms_re, gradient)
    elif color_type == "rgb":
        colors = re.findall(colortools.rgb_all_forms_re, gradient)
    elif color_type == "hex":
        colors = re.findall(colortools.hex_regex, gradient)
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


def is_required_selector(selector_type: str, selector: str) -> bool:
    """checks selector to see if it's required type or not

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


if __name__ == "__main__":
    from file_clerk import clerk

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
    project_path = "projects/single-page/"
    css_path = project_path + "style.css"
    html_path = project_path + "index.html"
    css_code = clerk.file_to_string(css_path)
    html_code = clerk.file_to_string(html_path)

    styles = Stylesheet("style.css", css_code)
    color_rules = styles.color_rulesets
    for rule in color_rules:
        selector = rule.selector
        for declaration in rule.declaration_block.declarations:
            property = declaration.property
            value = declaration.value
