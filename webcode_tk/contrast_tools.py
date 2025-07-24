""" Contrast Tools
Tools for determining CSS as applied through inheritance and the cascade.

This module analyzes the DOM, inheritance, and the cascade to determine all
styles applied to every element on a page. It scans each stylesheet and
applies each style, one at a time, to all applicable elements and their
children.

Constants:
    DEFAULT_GLOBAL_COLOR (str): Default text color for all elements (#000000).
    DEFAULT_GLOBAL_BACKGROUND (str): Default background color (#ffffff).
    DEFAULT_LINK_COLOR (str): Default color for unvisited links (#0000EE).
    DEFAULT_LINK_VISITED (str): Default color for visited links (#551A8B).
    ROOT_FONT_SIZE (int): Base font size in pixels for root element (16).
    IS_BOLD (list[str]): HTML elements that are bold by default.
    HEADING_FONT_SIZES (dict[str, int]): Default font sizes for heading
        elements in pixels (h1-h6).
    WCAG_AA_NORMAL (float): WCAG AA contrast ratio threshold for normal
        text (4.5).
    WCAG_AA_LARGE (float): WCAG AA contrast ratio threshold for large
        text (3.0).
    WCAG_AAA_NORMAL (float): WCAG AAA contrast ratio threshold for normal
        text (7.0).
    WCAG_AAA_LARGE (float): WCAG AAA contrast ratio threshold for large
        text (4.5).
    LARGE_TEXT_SIZE_PX (float): Minimum font size in pixels for large
        text (24.0).
    LARGE_TEXT_BOLD_SIZE_PX (float): Minimum font size in pixels for large bold
        text (18.66).
    CONTRAST_RELEVANT_PROPERTIES (tuple): properties that directly impact the
        mathematical contrast ratios and size thresholds that determine WCAG
        compliance.
"""
import copy
import re

import tinycss2
from bs4 import BeautifulSoup
from file_clerk import clerk

from webcode_tk import css_tools

# Browser default styling constants
DEFAULT_GLOBAL_COLOR = "#000000"
DEFAULT_GLOBAL_BACKGROUND = "#ffffff"
DEFAULT_LINK_COLOR = "#0000EE"
DEFAULT_LINK_VISITED = "#551A8B"
ROOT_FONT_SIZE = 16
IS_BOLD = ["strong", "b", "h1", "h2", "h3", "h4", "h5", "h6"]
HEADING_FONT_SIZES = {
    "h1": 32,  # 2em
    "h2": 24,  # 1.5em
    "h3": 20,  # 1.25em
    "h4": 16,  # 1em
    "h5": 13,  # 0.83em
    "h6": 11,  # 0.67em
}

# WCAG Contrast threshold constants
WCAG_AA_NORMAL = 4.5
WCAG_AA_LARGE = 3.0
WCAG_AAA_NORMAL = 7.0
WCAG_AAA_LARGE = 4.5
LARGE_TEXT_SIZE_PX = 24.0
LARGE_TEXT_BOLD_SIZE_PX = 18.66

# CSS properties relevant to contrast analysis
CONTRAST_RELEVANT_PROPERTIES = {
    "color",
    "background-color",
    "background",
    "font-size",
    "font-weight",
    "opacity",
    "visibility",
    "display",
}


def analyze_contrast(project_folder: str) -> list[dict]:
    """
    Analyzes color contrast for all HTML documents in the given project
    folder.

    Args:
        project_folder (str): Path to the root folder of the website project.

    Returns:
        list[dict]: List of dictionaries with contrast analysis results for
        each element.
    """

    project_contrast_results = []
    parsed_html_docs = get_parsed_documents(project_folder)
    css_files = load_css_files(parsed_html_docs, project_folder)

    # Analyze CSS Files
    for html_doc in parsed_html_docs:
        doc_results = analyze_css(html_doc, css_files)
        project_contrast_results.extend(doc_results)
    return project_contrast_results


def get_parsed_documents(project_folder: str) -> list[dict]:
    """
    Parses all HTML documents in the given project folder.

    Args:
        project_folder (str): Path to the root folder of the website project.

    Returns:
        list[dict]: A list of dictionaries, each containing:
            - 'filename' (str): The HTML file's name or path.
            - 'soup' (BeautifulSoup): The parsed BeautifulSoup object.
    """
    parsed_documents = []

    # Get all html file paths
    files = clerk.get_all_files_of_type(project_folder, "html")

    # get the soup for each html doc
    for file in files:
        filename = clerk.get_file_name(file)
        with open(file, "r", encoding="utf-8") as f:
            html = f.read()

        soup = BeautifulSoup(html, "html.parser")
        file_dict = {}
        file_dict["filename"] = filename
        file_dict["soup"] = soup
        parsed_documents.append(file_dict)

    return parsed_documents


def load_css_files(html_docs: list[dict], project_folder: str) -> list[dict]:
    """
    Parses and collects all CSS sources (external and internal) for each HTML
    document.

    Args:
        html_docs (list[dict]): List of dictionaries, each with 'filename' and
            'soup' for an HTML document.
        project_folder (str): Path to the root folder of the website project.

    Returns:
        list[dict]: List of dictionaries, each containing parsed CSS sources
            for each HTML file.
    """
    css_files = []
    stylesheet_cache = {}
    for file in html_docs:
        soup = file.get("soup")
        source_order = get_css_source_order(soup)
        html_file = file.get("filename")

        for sheet in source_order:
            if sheet.get("type") == "external":
                href = sheet.get("href")
                parsed = get_or_parse_external_stylesheet(
                    href, project_folder, stylesheet_cache
                )
            else:
                parsed = parse_internal_style_tag(sheet.get("content"))
                href = "style_tag"
            css_source = {}
            if not css_source.get(html_file):
                css_source[html_file] = []
            append_style_data(html_file, sheet, href, parsed, css_source)
            css_files.append(css_source)
    return css_files


def get_css_source_order(soup: "BeautifulSoup") -> list[dict]:
    """
    Returns the ordered list of CSS sources (external stylesheets and internal
    style tags) as they appear in the <head> of the HTML document.

    Args:
        soup (BeautifulSoup): Parsed BeautifulSoup object of the HTML document.

    Returns:
        list[dict]: A list of dictionaries, each representing a CSS source in
        order.
            For external stylesheets:
                {"type": "external", "href": "<stylesheet href>"}
            For internal style tags:
                {"type": "internal", "content": "<style tag content>"}
    """
    source_order = []
    head = soup.find("head")
    for child in head.children:
        if child.name == "link":
            source = child.attrs.get("href")

            # just in case the rel attribute is still missing
            if source[-4:] == ".css":
                styles = {"type": "external", "href": source}
                source_order.append(styles)
        elif child.name == "style":
            contents = child.string
            styles = {"type": "internal", "content": contents}
            source_order.append(styles)
    return source_order


def get_or_parse_external_stylesheet(
    href: str, project_folder: str, cache: dict
):
    """
    Retrieves a parsed external stylesheet from cache, or parses and caches it
    if not already done.

    Args:
        href (str): The href (path) to the external CSS file.
        project_folder (str): Path to the root folder of the website project.
        cache (dict): Dictionary used to cache parsed stylesheets.

    Returns:
        list: Parsed CSS rules from tinycss2 for the given stylesheet.
    """
    if href not in cache:
        css_path = project_folder + href
        with open(css_path, "rb") as fd:
            css = fd.read()
        if isinstance(css, bytes):
            css = css.decode("utf-8")
        parsed = tinycss2.parse_stylesheet(css)
        cache[href] = parsed
    return cache[href]


def parse_internal_style_tag(css: str):
    """
    Parses the contents of an internal <style> tag using tinycss2.

    Args:
        css (str): The CSS string from a <style> tag.

    Returns:
        list: Parsed CSS rules from tinycss2.
    """
    css = css.strip()
    if isinstance(css, bytes):
        return tinycss2.parse_stylesheet_bytes(css)
    else:
        return tinycss2.parse_stylesheet(css)


def append_style_data(html_file, sheet, href, parsed, css_source):
    data = {}
    data["source_type"] = sheet.get("type")
    data["css_name"] = href
    data["stylesheet"] = parsed
    css_source[html_file].append(data)


def analyze_css(html_doc: dict, css_files: list[dict]) -> list[dict]:
    """
    Analyzes CSS application and color contrast for a single HTML document.

    Args:
        html_doc (dict): Dictionary containing 'filename' and 'soup' for an
            HTML document.
        css_files (list[dict]): List of dictionaries containing parsed CSS
            sources for all HTML files, with each dict mapping filename to
            CSS sources in cascade order.

    Returns:
        list[dict]: List of dictionaries with contrast analysis results for
            each element in this HTML document. Each result contains element
            info, computed styles, colors, contrast ratio, and WCAG
            compliance.
    """
    doc_results = []
    filename = html_doc["filename"]
    soup = html_doc["soup"]

    print(soup)
    contents = []
    print(contents)

    # Step 1: Apply default styles to all elements
    default_styles = apply_browser_defaults(soup)
    print(default_styles)

    # Find CSS rules specific to this HTML document
    doc_css_rules = get_css_rules_for_document(filename, css_files)
    print(doc_css_rules)

    # Apply CSS rules to elements and compute styles
    computed_styles = compute_element_styles(
        soup, doc_css_rules, default_styles
    )
    print(computed_styles)

    # TODO: Traverse DOM and analyze contrast for elements with text
    # doc_results = traverse_elements_for_contrast(soup,
    # computed_styles, filename)

    return doc_results


def apply_browser_defaults(soup: BeautifulSoup) -> dict:
    """
    Apply browser default styles to all elements with text content.

    Returns:
        dict: Mapping of elements to their default computed styles
    """
    element_styles = {}
    default_specificity = css_tools.get_specificity("")

    for element in soup.find_all():
        if not element.is_empty_element and element.get_text(strip=True):
            # The element object itself becomes the key
            element_styles[element] = {
                "color": {
                    "value": DEFAULT_GLOBAL_COLOR,
                    "specificity": default_specificity,
                },
                "background-color": {
                    "value": DEFAULT_GLOBAL_BACKGROUND,
                    "specificity": default_specificity,
                },
                "font-size": {
                    "value": f"{ROOT_FONT_SIZE}px",
                    "specificity": default_specificity,
                },
            }

            # Apply element-specific defaults
            # Apply link colors
            if element.name == "a":
                element_styles[element]["color"] = {
                    "value": DEFAULT_LINK_COLOR,
                    "specificity": default_specificity,
                }
                element_styles[element]["visited-color"] = {
                    "value": DEFAULT_LINK_VISITED,
                    "specificity": default_specificity,
                }

            if element.name in IS_BOLD:
                element_styles[element]["font-weight"] = {
                    "value": "bold",
                    "specificity": default_specificity,
                }

            if element.name in HEADING_FONT_SIZES:
                element_styles[element]["font-size"] = element_styles[element][
                    "color"
                ] = {
                    "value": f"{HEADING_FONT_SIZES[element.name]}px",
                    "specificity": default_specificity,
                }

    return element_styles


def get_css_rules_for_document(
    filename: str, css_files: list[dict]
) -> list[dict]:
    """
    Extracts CSS rules specific to a given HTML document from the CSS files
    list.

    Args:
        filename (str): The HTML filename to find CSS rules for.
        css_files (list[dict]): List of dictionaries containing parsed CSS
            sources for all HTML files, with each dict mapping filename to
            CSS sources in cascade order.

    Returns:
        list[dict]: List of CSS rule dictionaries for the specified HTML
            document, maintaining the cascade order.
    """
    css_rules = []
    for sheet in css_files:
        if sheet.get(filename):
            source = sheet.get(filename)[0]
            parsed_styles = source.get("stylesheet")
            rules = parse_css_rules_from_tinycss2(parsed_styles)
            css_rules.append(rules)
    return css_rules


def parse_css_rules_from_tinycss2(parsed_stylesheet):
    """
    Converts tinycss2 parsed rules into a more usable format.
    """
    css_rules = []

    for rule in parsed_stylesheet:
        if rule.type == "qualified-rule":
            # Extract selector
            selector = tinycss2.serialize(rule.prelude).strip()

            # Extract declarations
            declarations = {}
            declaration_list = tinycss2.parse_declaration_list(rule.content)

            for decl in declaration_list:
                if decl.type == "declaration":
                    prop_name = decl.name
                    prop_value = tinycss2.serialize(decl.value).strip()
                    declarations[prop_name] = prop_value

            css_rules.append(
                {"selector": selector, "declarations": declarations}
            )

    return css_rules


def compute_element_styles(
    soup: BeautifulSoup, css_rules: list[dict], default_styles: dict
) -> dict:
    """
    Computes final styles for all elements by applying CSS rules and
    inheritance.

    Args:
        soup (BeautifulSoup): Parsed HTML document.
        css_rules (list[dict]): List of CSS rule dictionaries with selectors
            and declarations.
        default_styles (dict): Dictionary mapping elements to their default
            browser styles.

    Returns:
        dict: Dictionary mapping elements to their final computed styles
            after applying CSS cascade and inheritance.
    """
    # Step 1: Start with default styles
    computed_styles = copy.deepcopy(default_styles)

    # Step 2: Apply all CSS rules (cascade resolution)
    for rules in css_rules:
        for rule in rules:
            matching_elements = find_matching_elements(soup, rule["selector"])
            for element in matching_elements:
                apply_rule_to_element(element, rule, computed_styles)

    # Step 3: Apply inheritance (after all rules processed)
    apply_inheritance(soup, computed_styles)

    return computed_styles


def find_matching_elements(soup: BeautifulSoup, selector: str) -> list:
    """
    Finds all elements in the DOM that match a given CSS selector.

    Args:
        soup (BeautifulSoup): Parsed HTML document.
        selector (str): CSS selector string (e.g., "p", ".class", "#id").

    Returns:
        list: List of BeautifulSoup Tag objects that match the selector.
    """

    # Clean and validate
    selector = selector.strip()

    # Handle empty selectors
    if not selector:
        return []

    # Check for valid, but not supported by bs4 selectors
    if not is_selector_supported_by_bs4(selector):
        warning = f"Warning: Selector '{selector}' contains features not "
        warning += "supported by BS4"
        print(warning)
        return []

    # Try BeautifulSoup's select method
    try:
        return soup.select(selector)
    except Exception as e:
        print(f"Error parsing selector '{selector}': {e}")
        return []


def is_selector_supported_by_bs4(selector: str) -> bool:
    """
    Determines if a CSS selector can be handled by BeautifulSoup's .select()
    method.

    Args:
        selector (str): CSS selector string to check.

    Returns:
        bool: True if the selector is supported by BS4, False if it contains
            unsupported features like pseudo-classes or pseudo-elements.
    """
    # Clean the selector
    selector = selector.strip()

    if not selector:
        return False

    # Patterns that BS4 does NOT support
    unsupported_patterns = [
        r"::",  # Pseudo-elements (::before, ::after, etc.)
        r":(?!not\()",  # Pseudo-classes except :not() (BS4 supports)
        r"~",  # General sibling combinator
        r"\[.*?\s+i\]",  # Case-insensitive attribute matching
    ]

    # Check for unsupported patterns
    for pattern in unsupported_patterns:
        if re.search(pattern, selector):
            return False

    # Additional checks for specific pseudo-classes BS4 doesn't support
    problematic_pseudos = [
        "hover",
        "focus",
        "active",
        "visited",
        "link",
        "first-child",
        "last-child",
        "nth-child",
        "nth-of-type",
        "checked",
        "disabled",
        "enabled",
        "empty",
        "target",
        "root",
        "first-letter",
        "first-line",
    ]

    for pseudo in problematic_pseudos:
        if f":{pseudo}" in selector:
            return False

    return True


def apply_rule_to_element(element, rule: dict, computed_styles: dict) -> None:
    """
    Applies CSS declarations from a rule to a specific element, handling
    specificity conflicts.

    Args:
        element: BeautifulSoup Tag object representing the target element.
        rule (dict): CSS rule dictionary containing 'selector' and
            'declarations'.
        computed_styles (dict): Dictionary mapping elements to their current
            computed styles (modified in place).

    Returns:
        None: Modifies computed_styles dictionary in place.
    """
    # Check if element of key exists
    element_styles = computed_styles.get(element)
    if element_styles:
        selector = rule.get("selector")
        rule_specificity = css_tools.get_specificity(selector)
        declarations = rule.get("declarations", {})

        for property_name, property_value in declarations.items():
            if property_name not in CONTRAST_RELEVANT_PROPERTIES:
                continue
            current_prop = computed_styles[element].get(property_name)

            should_apply = False

            if current_prop is None:
                # property doesn't exist, apply it
                should_apply = True
            elif (
                isinstance(current_prop, dict)
                and "specificity" in current_prop
            ):
                # property exists with specificiy info
                current_specificity = current_prop["specificity"]
                if isinstance(current_specificity, tuple):
                    current_specificity = "".join(
                        map(str, current_specificity)
                    )
                if rule_specificity > current_specificity:
                    should_apply = True
                elif rule_specificity == current_specificity:
                    should_apply = True
            else:
                # property exits but no specificity (default)
                should_apply = True
            if should_apply:
                computed_styles[element][property_name] = {
                    "value": property_value,
                    "specificity": rule_specificity,
                }

    return


def apply_inheritance(soup: BeautifulSoup, computed_styles: dict) -> None:
    """
    Applies CSS inheritance rules, copying inheritable property values from
    parent elements to child elements.

    Args:
        soup (BeautifulSoup): Parsed HTML document for DOM traversal.
        computed_styles (dict): Dictionary mapping elements to their computed
            styles (modified in place).

    Returns:
        None: Modifies computed_styles dictionary in place.
    """
    pass


def calculate_css_specificity(selector: str) -> tuple[int, int, int, int]:
    """
    Calculates CSS specificity for a given selector.

    Args:
        selector (str): CSS selector string.

    Returns:
        tuple[int, int, int, int]: Specificity tuple in format
            (inline, IDs, classes, elements) where higher values indicate
            higher specificity.
    """
    return (0, 0, 0, 0)


def is_inheritable_property(property_name: str) -> bool:
    """
    Determines if a CSS property is inheritable by default.

    Args:
        property_name (str): Name of the CSS property (e.g., 'color',
            'margin').

    Returns:
        bool: True if the property is inheritable, False otherwise.
    """
    return False


if __name__ == "__main__":
    project_path = "tests/test_files/large_project/"
    contrast_results = analyze_contrast(project_path)
