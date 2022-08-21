""" CSS
This module is a set of tools to analyze CSS syntax as well as properties
and values.
"""
import re

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
                and delcaration block.

        Returns:
            color_rulsets: a list of all selectors that target color
                in some way, but just with the color-based declarations.
        """
        color_rulesets = []
        if (
            ruleset.declaration_block
            and "color:" in ruleset.declaration_block.text
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

    Attributes:
        at_rule (str): the full at-rule such as '@media only and
            (min-width: 520px)'.
        text (str): the text of the code (without the at_rule).
            Provide the text if you do not provide a list of rulesets.
        rulesets (list): a list of rulesets. This is optional as long
            as you provide the text.
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
        if rules:
            self.rulesets = rules[:]
        else:
            self.rulesets = []
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
    """_summary_"""

    def __init__(self, text):
        self.__text = text
        self.selector = ""
        self.declaration_block = None
        self.is_valid = True
        self.validate()
        self.initialize()

    def initialize(self):
        if self.is_valid:
            contents = self.__text.split("{")
            self.selector = contents[0].replace("\n", "").strip()
            block = contents[1].replace("\n", "")
            self.declaration_block = DeclarationBlock(block)

    def validate(self):
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
    def __init__(self, text):
        self.text = text
        self.declarations = []
        self.__set_declarations()

    def __set_declarations(self):
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
        for i in range(len(declarations)):
            # make sure i is not out of range (after popping i)
            if i > len(declarations) - 1:
                break
            declarations[i] = declarations[i].replace("\n", "")
            declarations[i] = declarations[i].strip()
            if not declarations[i]:
                declarations.pop(i)
        # create our declaration objects
        # we separated the cleaning from the separating due
        # to the potential of popping i resulting in index error
        # or missing a declaration (it happened)
        for i in range(len(declarations)):
            declarations[i] = Declaration(declarations[i])
        self.declarations = declarations


class Declaration:
    def __init__(self, text):
        self.__text = text
        self.property = ""
        self.value = ""
        self.is_valid = False
        self.set_declaration()

    def set_declaration(self):
        """validate while trying to set declaration"""
        # assume it's valid until proven otherwise
        self.is_valid = True
        # Make sure there's a colon for validity and separating
        if ":" not in self.__text:
            self.is_valid = False
        else:
            elements = self.__text.split(":")
            # make sure there are 2 values after the split
            if len(elements) > 2:
                self.is_valid = False
            else:
                self.property = elements[0].strip()
                self.value = elements[1].strip()
                self.validate_declaration()

    def validate_declaration(self):
        # Check to see if there's only 1 character in value
        # 0 is valid; anything else is invalid
        if len(self.value) == 1 and not self.value == "0":
            self.is_valid = False

        # Make sure there are no spaces in between property
        prop_list = self.property.split()
        if len(prop_list) > 1:
            self.is_valid = False

        # Make sure there's nothing after the semi-colon
        # but account for the empty string element after the split
        # as well as spaces (just in case)
        val_list = self.value.split(";")
        if len(val_list) > 1 and val_list[1].strip():
            self.is_valid = False

    def get_declaration(self):
        return self.property + ": " + self.value


def get_nested_at_rule(code, rule):
    at_rule = []
    at_split = code.split(rule)
    if len(at_split) > 1:
        if at_split[0] == "":
            # rule was at the beginning
            at_rule.append(rule + " " + at_split[1])
        else:
            at_rule.append(rule + " " + at_split[0])
    return at_rule


def restore_braces(split):
    result = []
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


def split_by_partition(text, part):
    # base case
    if text.count(part) == 0:
        return [
            text,
        ]
    # recursive case
    else:
        text_tuple = text.partition(part)
        return [
            text_tuple[0],
        ] + split_by_partition(text_tuple[2], part)


def minify_code(text: str) -> str:
    """remove all new lines, tabs, and double spaces"""
    text = text.replace("\n", "")
    text = text.replace("  ", "")
    text = text.replace("\t", "")
    return text


def missing_end_semicolon(css_code: str) -> bool:
    # remove all whitespace and line breaks
    cleaned = css_code.replace(" ", "")
    cleaned = css_code.replace("\n", "")
    # if there is no semicolon preceding closing curly bracket,
    return ";}" in cleaned


def has_repeat_selector(styles: Stylesheet) -> bool:
    """checks stylesheet to determine whether any selectors are repeated
    or not."""
    return styles.has_repeat_selectors


def split_css(css_code):
    """returns list of selectors & declarations (no { or })"""
    # remove newlines
    css_code = css_code.replace("\n", "")
    pattern = r"\{(.*?)\}"
    return re.split(pattern, css_code)


def get_selectors(css_list):
    selectors = []
    for i in range(0, len(css_list), 2):
        selectors.append(css_list[i].strip())
    selectors.remove("")
    return selectors


def get_declarations(css_list):
    """extract all CSS declarations from a list of Css

    Args:
        css_list (_type_): _description_

    Returns:
        _type_: _description_
    """
    declarations = []
    for i in range(1, len(css_list), 2):
        declarations.append(css_list[i].strip())
    if "" in declarations:
        declarations.remove("")
    return declarations


def get_comment_positions(code):
    positions = []
    try:
        positions.append(code.index("/*"))
        positions.append(code.index("*/"))
        return positions
    except Exception as ex:
        print(ex)
        return


def separate_code(code):
    """splits code into two lists: code & comments"""
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
                print("We have a problem with the code syntax.")
    splitzky["code"] = new_code
    splitzky["comments"] = comments
    return splitzky


def get_color_rulesets(objects):
    color_rulesets = []
    if objects:
        for style_tag in objects:
            if style_tag.color_rulesets:
                for ruleset in style_tag.color_rulesets:
                    for declaration in ruleset.declaration_block.declarations:
                        if declaration.is_valid:
                            if "color" in declaration.property.lower():
                                if ruleset not in color_rulesets:
                                    color_rulesets.append(ruleset)
    return color_rulesets


def get_specificity(selector):
    id_selector = get_id_score(selector)
    class_selector = get_class_score(selector)
    type_selector = get_type_score(selector)
    return "{}{}{}".format(id_selector, class_selector, type_selector)


def get_id_score(selector):
    """receives a selector and returns # of id selectors"""
    pattern = regex_patterns["id_selector"]
    id_selectors = re.findall(pattern, selector)
    return len(id_selectors)


def get_class_score(selector):
    """receives a selector and returns # of class & psuedo-class selectors"""
    class_re = regex_patterns["class_selector"]
    selectors = re.findall(class_re, selector)
    pseudo_re = regex_patterns["pseudoclass_selector"]
    pseudo_selectors = re.findall(pseudo_re, selector)
    selectors += pseudo_selectors
    attribute_re = regex_patterns["attribute_selector"]
    attribute_selectors = re.findall(attribute_re, selector)
    selectors += attribute_selectors
    return len(selectors)


def get_type_score(selector):
    """receives a selector and returns # of type selectors"""
    pattern = regex_patterns["type_selector"]
    selectors = re.findall(pattern, selector)
    return len(selectors)


def get_header_color_details(rulesets):
    """receives rulesets and returns data on colors set by headers"""
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


def get_header_selectors(selector):
    """takes selector and returns any selector that selects an h1-h6"""
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


def get_global_color_details(rulesets):
    """receives rulesets and returns data on global colors"""
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


def has_vendor_prefix(property):
    vendor_prefixes = ("-webkit-", "-moz-", "-o-", "-ms-")
    for prefix in vendor_prefixes:
        if prefix in property:
            return True
    return False


def is_gradient(value):
    return "gradient" in value


def process_gradient(code: str) -> list:
    """returns list of all colors from gradient sorted light to dark"""
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


def sort_color_codes(codes):
    """sorts color codes from light to dark (luminance)"""
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


def remove_alpha(color_code):
    """removes the alpha channel from rgba or hsla"""
    color_code = color_code.split(",")
    a = color_code[0].index("a")
    color_code[0] = color_code[0][:a] + color_code[0][a + 1 :]
    color_code.pop(-1)
    color_code = ",".join(color_code)
    color_code += ")"
    return color_code


def get_colors_from_gradient(gradient):
    """extract all color codes from gradient"""
    colors = []
    # use regex to pull all possible color codes first
    append_color_codes("hsl", gradient, colors)
    append_color_codes("rgb", gradient, colors)
    append_color_codes("hex", gradient, colors)
    append_color_codes("keywords", gradient, colors)

    return colors


def append_color_codes(type, code, color_list):
    if type == "hsl":
        colors = re.findall(colortools.hsl_all_forms_re, code)
    elif type == "rgb":
        colors = re.findall(colortools.rgb_all_forms_re, code)
    elif type == "hex":
        colors = re.findall(colortools.hex_regex, code)
    elif type == "keywords":
        words = re.findall(r"[+a-z+A-Z]*", code)
        colors = []
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
        color_list += colors


def is_required_selector(selector_type: str, selector: str) -> bool:
    """checks selector to see if it's required type or not"""
    pattern = regex_patterns[selector_type]
    return re.search(pattern, selector)


def get_number_required_selectors(
    selector_type: str, sheet: Stylesheet
) -> int:
    """returns # of a specific selector type in a stylesheet"""
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
    to see if it's there or not"""
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
