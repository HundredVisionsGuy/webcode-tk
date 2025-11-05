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
from bs4 import NavigableString
from bs4 import Tag
from file_clerk import clerk

from webcode_tk import color_tools
from webcode_tk import css_tools
from webcode_tk import font_tools
from webcode_tk.font_tools import compute_font_size
from webcode_tk.font_tools import is_large_text
from webcode_tk.font_tools import split_value_unit

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


def generate_contrast_report(
    project_path: str, wcag_level: str = "AAA"
) -> list[str]:
    """returns a report on a project's color contrast results.

    Gets all contrast results (all elements that contains text), filters out
    warning entries, identify any failures. If there are no failures in a doc,
    then append a single pass for the file. Append a fail message for each
    element that fails to mee contrast requirement.

    Example Output:
    [
        "pass: index.html passes color contrast.",
        "fail: in about.html, the <h1> element failed WCAG AA contrast
            requirements (ratio: 3.2, required: 4.5).",
        "fail: in about.html, the <p class='intro'> element failed WCAG AA
            contrast requirements (ratio: 2.1, required: 4.5).",
        "pass: contact.html passes color contrast.",
        "fail: in gallery.html, the <a id='nav-home'> element failed WCAG AA
            contrast requirements (indeterminate due to background image)."
    ]

    Args:
        project_path: the web project's root folder.
        wcag_level: the WCAG level (AAA or AA).

    Returns:
        report: the list of strings to determine whether a page passes
            or fails.

    """
    report = []
    project_files = {}
    wcag_level_key = f"wcag_{wcag_level}_pass".lower()

    # Collect data from project folder
    contrast_data = analyze_contrast(project_path)

    # Analayze documents
    for item in contrast_data:
        current_file = item.get("filename")
        if current_file not in project_files:
            project_files[current_file] = []

        # Check if fails WCAG level
        result = item.get(wcag_level_key)
        if result:
            result = result.lower()
        else:
            warning_msg = item.get("warning_message")
            warning_msg = "fail: " + warning_msg
            project_files[current_file].append(warning_msg)
            continue
        if result == "fail":
            # collect data
            element = item.get("element_tag")
            is_large = item.get("is_large_text")
            if is_large:
                if wcag_level == "AAA":
                    target_ratio = WCAG_AAA_LARGE
                else:
                    target_ratio = WCAG_AA_LARGE
            else:
                if wcag_level == "AAA":
                    target_ratio = WCAG_AAA_NORMAL
                else:
                    target_ratio = WCAG_AA_NORMAL
            actual_ratio = item.get("contrast_ratio")
            actual_ratio = round(actual_ratio, 1)

            # append fail message to project_files
            msg = f"{result}: in {current_file}, the {element} failed WCAG "
            msg += f"{wcag_level} contrast requirements (ratio: "
            msg += f"{actual_ratio}, required: {target_ratio})."
            project_files[current_file].append(msg)

    # Check for html docs with no fails.
    for file in project_files:
        errors = project_files.get(file)
        if errors:
            if "has no CSS" in errors[0]:
                report.append(errors[0])
            else:
                report.extend(errors)
        else:
            # Check for global selectors (html, *, or body) and calculate
            # contrast
            global_color_result = css_tools.get_global_color_report(
                project_path
            )
            if isinstance(global_color_result, list):
                for result in global_color_result:
                    if "fail" in result:
                        if file in result:
                            error_msg = result.split(file)[1]
                            msg = f"fail: in {file}, {error_msg.strip()}"
                    else:
                        msg = f"pass: {file} passes color contrast."
            report.append(msg)
    return report


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
        doc_results = analyze_css(html_doc, css_files, project_folder)
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


def append_style_data(
    html_file: str, sheet: dict, href: str, parsed: list, css_source: dict
) -> None:
    """
    Append CSS style data to css_source dictionary.

    Args:
        html_file (str): HTML filename.
        sheet (dict): Sheet metadata dictionary.
        href (str): CSS file href or identifier.
        parsed (list): Parsed CSS rules from tinycss2.
        css_source (dict): Dictionary to append data to (modified in place).

    Returns:
        None: Modifies css_source dictionary in place.
    """
    data = {}
    data["source_type"] = sheet.get("type")
    data["css_name"] = href
    data["stylesheet"] = parsed
    css_source[html_file].append(data)


def analyze_css(
    html_doc: dict, css_files: list[dict], project_path=""
) -> list[dict]:
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

    # Check for CSS sources and create warnings if needed
    warnings = []

    if not has_any_css_sources(soup):
        message = f"{filename} has no CSS sources "
        message += "(no <link> or <style> tags)"
        warnings.append(
            {
                "type": "no_css_sources",
                "message": message,
                "impact": "Only browser defaults will be applied",
            }
        )

    # Step 1: Apply default styles to all elements
    default_styles = apply_browser_defaults(soup)

    # Find CSS rules specific to this HTML document
    doc_css_rules = get_css_rules_for_document(filename, css_files)

    # Additional warning if no CSS rules found
    if not doc_css_rules or all(len(rules) <= 1 for rules in doc_css_rules):
        warnings.append(
            {
                "type": "no_css_rules",
                "message": f"{filename} has no CSS rules to process",
                "impact": "Results will only show browser default styling",
            }
        )

    # Apply CSS rules to elements and compute styles
    computed_styles = compute_element_styles(
        soup, doc_css_rules, default_styles
    )

    # Traverse DOM and analyze contrast for elements with text
    doc_results = analyze_elements_for_contrast(computed_styles, filename)

    # Add warnings to results if any exist
    if warnings:
        for warning in warnings:
            warning_result = {
                "filename": filename,
                "element_tag": None,
                "element_id": None,
                "element_class": None,
                "text_content": None,
                "text_color": None,
                "text_color_source": None,
                "background_color": None,
                "background_color_source": None,
                "font_size_px": None,
                "font_weight": None,
                "is_large_text": None,
                "contrast_ratio": None,
                "wcag_aa_pass": None,
                "wcag_aaa_pass": None,
                "contrast_analysis": "warning",
                "warning_type": warning["type"],
                "warning_message": warning["message"],
                "warning_impact": warning["impact"],
            }
            doc_results.append(warning_result)
    return doc_results


def has_any_css_sources(soup: BeautifulSoup) -> bool:
    """
    Check if HTML document has any CSS sources (external or internal).

    Args:
        soup: BeautifulSoup object of the HTML document

    Returns:
        bool: True if CSS sources found, False otherwise
    """
    head = soup.find("head")
    if not head:
        return False

    # Check for external stylesheets
    links = head.find_all("link", {"rel": "stylesheet"})
    if links:
        return True

    # Check for internal style tags
    styles = head.find_all("style")
    if styles and any(style.get_text(strip=True) for style in styles):
        return True

    return False


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
                    "source": "default",
                    "is_default": True,
                },
                "background-color": {
                    "value": DEFAULT_GLOBAL_BACKGROUND,
                    "specificity": default_specificity,
                    "source": "default",
                    "is_default": True,
                },
                "font-size": {
                    "value": f"{ROOT_FONT_SIZE}px",
                    "specificity": default_specificity,
                    "source": "default",
                    "is_default": True,
                },
                "font-weight": {
                    "value": "bold" if element.name in IS_BOLD else "normal",
                    "specificity": default_specificity,
                    "source": "default",
                    "is_default": True,
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
            if element.name in HEADING_FONT_SIZES:
                element_styles[element]["font-size"] = {
                    "value": f"{HEADING_FONT_SIZES[element.name]}px",
                    "specificity": default_specificity,
                    "source": "default",
                    "is_default": True,
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
            if source.get("source_type") == "internal":
                source["css_name"] = f"style_tag--{filename}"
            parsed_styles = source.get("stylesheet")
            rules = parse_css_rules_from_tinycss2(parsed_styles)
            rules = [
                source,
            ] + rules
            css_rules.append(rules)
    return css_rules


def parse_css_rules_from_tinycss2(parsed_stylesheet: list) -> list:
    """
    Converts tinycss2 parsed rules into a more usable format.

    Args:
        parsed_stylesheet (list): List of tinycss2 parsed rule objects.

    Returns:
        list[dict]: List of rule dictionaries with 'selector' and
            'declarations' keys.
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
    for rules_list in css_rules:
        # Extract source data (first item in the list)
        source_data = rules_list[0]
        actual_rules = rules_list[1:]

        # Create CSS source info object
        css_source_info = {
            "filename": source_data.get("css_name"),
            "source_type": source_data.get("source_type"),
        }
        # Now iterate over the actual CSS rules
        for rule in actual_rules:
            # Find elements that match this rule's selector
            matching_elements = find_matching_elements(soup, rule["selector"])

            # Apply the rule to each matching element
            for element in matching_elements:
                apply_rule_to_element(
                    element, rule, computed_styles, css_source_info
                )

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
        list[Tag]: List of BeautifulSoup Tag objects that match the selector.
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


def apply_rule_to_element(
    element: Tag,
    rule: dict,
    computed_styles: dict,
    css_source_info: dict = None,
) -> None:
    """
    Applies CSS declarations from a rule to a specific element, handling
    specificity conflicts.

    Args:
        element: BeautifulSoup Tag object representing the target element.
        rule (dict): CSS rule dictionary containing 'selector' and
            'declarations'.
        computed_styles (dict): Dictionary mapping elements to their current
            computed styles (modified in place).
        css_source_info (dict): Information about the CSS source.

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

            # Special handling for font-size - convert to pixels
            # and store enhanced data
            if property_name == "font-size":
                original_value = property_value
                computed_pixels = convert_font_size_to_pixels(
                    property_value, element, computed_styles
                )

                # Classify unit type for debugging/analysis
                unit_type = classify_font_unit(original_value)

                font_size_data = {
                    "value": computed_pixels,
                    "original_value": original_value,
                    "unit_type": unit_type,
                    "specificity": rule_specificity,
                    "source": "rule",
                    "selector": selector,
                    "css_file": css_source_info.get("filename")
                    if css_source_info
                    else None,
                    "css_source_type": css_source_info.get("source_type")
                    if css_source_info
                    else None,
                }

                # Check if we should apply this font-size rule
                current_prop = computed_styles[element].get(property_name)
                should_apply = False

                if current_prop is None:
                    should_apply = True
                elif (
                    isinstance(current_prop, dict)
                    and "specificity" in current_prop
                ):
                    current_specificity = current_prop["specificity"]
                    if isinstance(current_specificity, tuple):
                        current_specificity = "".join(
                            map(str, current_specificity)
                        )
                    if rule_specificity >= current_specificity:
                        should_apply = True
                else:
                    should_apply = True

                if should_apply:
                    computed_styles[element][property_name] = font_size_data

            # Special handling for background-color and background
            elif property_name in ["background-color", "background"]:
                # Check if this background contains a raster image
                if contains_raster_image(property_value):
                    background_data = {
                        "value": None,
                        "specificity": rule_specificity,
                        "source": "rule",
                        "selector": selector,
                        "css_file": css_source_info.get("filename")
                        if css_source_info
                        else None,
                        "css_source_type": css_source_info.get("source_type")
                        if css_source_info
                        else None,
                        "contrast_analysis": "indeterminate",
                        "reason": "background_image_blocks_color_analysis",
                        "original_background": property_value,
                    }
                else:
                    # Extract usable color for contrast analysis
                    contrast_color = extract_contrast_color(property_value)
                    effective_color = (
                        contrast_color if contrast_color else property_value
                    )

                    background_data = {
                        "value": effective_color,
                        "specificity": rule_specificity,
                        "source": "rule",
                        "selector": selector,
                        "css_file": css_source_info.get("filename")
                        if css_source_info
                        else None,
                        "css_source_type": css_source_info.get("source_type")
                        if css_source_info
                        else None,
                        "contrast_analysis": "determinable",
                        "original_background": property_value
                        if property_value != effective_color
                        else None,
                    }

                # Apply specificity logic and set the property
                current_prop = computed_styles[element].get(property_name)
                should_apply = False

                if current_prop is None:
                    should_apply = True
                elif (
                    isinstance(current_prop, dict)
                    and "specificity" in current_prop
                ):
                    current_specificity = current_prop["specificity"]
                    if isinstance(current_specificity, tuple):
                        current_specificity = "".join(
                            map(str, current_specificity)
                        )
                    if rule_specificity >= current_specificity:
                        should_apply = True
                else:
                    should_apply = True

                if should_apply:
                    computed_styles[element][property_name] = background_data

            else:
                # Regular property handling for non-font-size, non-background
                # properties
                # ... rest of your existing else block code ...
                # Regular property handling for non-font-size properties
                current_prop = computed_styles[element].get(property_name)
                should_apply = False

                if current_prop is None:
                    # property doesn't exist, apply it
                    should_apply = True
                elif (
                    isinstance(current_prop, dict)
                    and "specificity" in current_prop
                ):
                    # property exists with specificity info
                    current_specificity = current_prop["specificity"]
                    if isinstance(current_specificity, tuple):
                        current_specificity = "".join(
                            map(str, current_specificity)
                        )
                    if rule_specificity >= current_specificity:
                        should_apply = True
                else:
                    # property exists but no specificity (default)
                    should_apply = True
                if should_apply:
                    computed_styles[element][property_name] = {
                        "value": property_value,
                        "specificity": rule_specificity,
                        "source": "rule",
                        "selector": selector,
                        "css_file": css_source_info.get("filename")
                        if css_source_info
                        else None,
                        "css_source_type": css_source_info.get("source_type")
                        if css_source_info
                        else None,
                    }

    return


def classify_font_unit(font_size_value: str) -> str:
    """Classify font-size unit type for analysis."""
    if re.match(r"^\d*\.?\d+(px|pt|pc|in|cm|mm)$", font_size_value, re.I):
        return "absolute"
    # Match number + unit pattern for relative units
    elif re.match(r"^\d*\.?\d+(em|rem|%)$", font_size_value, re.I):
        return "relative"
    elif font_size_value.lower() in ["larger", "smaller"]:
        return "relative_keyword"
    elif font_size_value.lower() in [
        "xx-small",
        "x-small",
        "small",
        "medium",
        "large",
        "x-large",
        "xx-large",
    ]:
        return "absolute_keyword"
    else:
        return "unknown"


def convert_font_size_to_pixels(
    font_size_value: str, element: Tag, computed_styles: dict
) -> str:
    """
    Converts font-size values to pixels for WCAG analysis using font_tools.

    Args:
        font_size_value (str): CSS font-size value (e.g., "2em", "120%",
            "16px")
        element: BeautifulSoup element for context
        computed_styles (dict): Current computed styles for inheritance
            context

    Returns:
        str: Font size converted to pixels (e.g., "32.0px")
    """
    font_size_value = font_size_value.strip()

    # Use font_tools to split value and unit
    try:
        value, unit = split_value_unit(font_size_value)

        # Get parent font size for relative calculations
        parent_font_size_px = get_parent_font_size(element, computed_styles)

        # Get element name for heading-specific calculations
        element_name = element.name if element else ""

        # Use your comprehensive compute_font_size function
        computed_px = compute_font_size(
            value=value,
            unit=unit,
            parent_size=parent_font_size_px,
            element_name=element_name,
        )

        return f"{computed_px:.1f}px"

    except Exception as e:
        # Fallback for parsing errors
        print(f"DEBUG: Exception caught: '{e}'")
        return f"{font_size_value}px"  # Assume it's already in pixels


def get_parent_font_size(element, computed_styles: dict) -> float:
    """
    Get parent's computed font size in pixels for relative calculations.

    Args:
        element (Tag): BeautifulSoup Tag object to find parent font size for.
        computed_styles (dict): Dictionary mapping elements to their
            computed styles.

    Returns:
        float: Parent's font size in pixels, or 16.0 (root default) if no
            parent found.
    """

    # Try to find parent in computed_styles
    current = element.parent if element else None
    while current:
        if current in computed_styles:
            parent_styles = computed_styles[current]
            if "font-size" in parent_styles:
                parent_size = parent_styles["font-size"]["value"]
                # Extract pixel value (remove 'px')
                return float(parent_size.replace("px", ""))
        current = current.parent

    # No parent found, use root font size (16px default)
    return 16.0


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
    # Step 1: Apply true CSS inheritance (color, font properties)
    apply_css_inheritance(computed_styles)

    # Step 2: Apply visual background inheritance
    apply_visual_background_inheritance(computed_styles)


def apply_css_inheritance(computed_styles: dict) -> None:
    """
    Apply traditional CSS inheritance for inheritable properties.

    Args:
        computed_styles (dict): Dictionary mapping elements to their
            computed styles (modified in place).

    Returns:
        None: Modifies computed_styles dictionary in place.
    """
    inheritable_props = {"color", "font-size", "font-weight"}

    for parent_element in computed_styles:
        parent_styles = computed_styles[parent_element]

        # Find all children that also have text content (in computed_styles)
        children = parent_element.find_all()
        children_with_styles = [
            child for child in children if child in computed_styles
        ]

        for child_element in children_with_styles:
            child_styles = computed_styles[child_element]

            # Apply inheritance for each inheritable property
            for prop in inheritable_props:
                parent_prop = parent_styles.get(prop)

                if parent_prop:  # Parent has this property
                    child_prop = child_styles.get(prop)
                    should_inherit = False

                    if child_prop is None:
                        # Child has no property at all - inherit
                        should_inherit = True
                    elif child_prop.get("source") == "default":
                        # Child has default style - inheritance wins
                        should_inherit = True
                    else:
                        # Child has explicit CSS rule - don't inherit
                        should_inherit = False

                    if should_inherit:
                        child_styles[prop] = {
                            "value": parent_prop["value"],
                            "specificity": parent_prop["specificity"],
                            "source": "inheritance",
                            "selector": parent_prop.get(
                                "selector", "inherited"
                            ),
                            "css_file": parent_prop.get("css_file"),
                            "css_source_type": parent_prop.get(
                                "css_source_type"
                            ),
                            "inherited_from": parent_element,
                        }


def apply_visual_background_inheritance(computed_styles: dict) -> None:
    """
    Apply visual background colors to elements without explicit
    backgrounds.

    Args:
        computed_styles: a dictionary of elements with computed styles.
    Returns:
        None
    """
    # Track which elements got new backgrounds this iteration
    changes_made = True
    max_iterations = 10  # Prevent infinite loops
    iteration = 0

    while changes_made and iteration < max_iterations:
        changes_made = False
        iteration += 1

        for element in computed_styles:
            element_styles = computed_styles[element]

            # Skip if element already has background-color
            if "background-color" in element_styles:
                continue

            # Check for explicit backgrounds
            if "background" in element_styles:
                bg_value = element_styles["background"]["value"]

                # Check if background contains a raster image
                if contains_raster_image(bg_value):
                    # Mark as contrast-indeterminate - cannot analyze
                    element_styles["background-color"] = {
                        "value": None,  # No usable color
                        "specificity": "000",
                        "contrast_analysis": "indeterminate",
                        "reason": "background_image_blocks_color_analysis",
                        "original_background": bg_value,
                        "visual_inheritance": False,
                    }
                    changes_made = True
                    continue
                else:
                    # Has usable background shorthand - skip inheritance
                    continue

            # Element needs background inheritance
            ancestor_bg = find_ancestor_background(element, computed_styles)

            if ancestor_bg.get("contrast_analysis") == "indeterminate":
                # Ancestor is indeterminate - propagate that status
                element_styles["background-color"] = {
                    "value": None,
                    "specificity": "000",
                    "contrast_analysis": "indeterminate",
                    "reason": ancestor_bg["reason"],
                    "inherited_from": ancestor_bg["source_element"],
                    "source": "visual_inheritance",
                    "original_background": ancestor_bg.get(
                        "original_background"
                    ),
                }
                changes_made = True
            else:
                # Normal inheritance - extract usable color
                contrast_color = extract_contrast_color(ancestor_bg["value"])
                effective_color = (
                    contrast_color if contrast_color else ancestor_bg["value"]
                )
                element_styles["background-color"] = {
                    "value": effective_color,
                    "specificity": "000",
                    "source": "visual_inheritance",
                    "inherited_from": ancestor_bg["source_element"],
                    "contrast_analysis": "determinable",
                    "original_background": (
                        ancestor_bg["value"]
                        if ancestor_bg["value"] != DEFAULT_GLOBAL_BACKGROUND
                        else None
                    ),
                }
                changes_made = True


def has_usable_background_color(background_prop: dict) -> bool:
    """
    Check if background property contains usable color for contrast.

    Args:
        background_prop (dict): Background property dictionary with 'value'
            key, or None.

    Returns:
        bool: True if background contains usable color for contrast
            analysis, False otherwise.
    """
    if not background_prop:
        return False

    background_value = background_prop["value"]

    # If it contains a raster image, color is not usable
    if contains_raster_image(background_value):
        return False

    # Check for gradients or solid colors
    return bool(
        re.search(
            r"(gradient|#[a-f0-9]{3,6}|rgb|hsl|[a-z]+)", background_value, re.I
        )
    )


def contains_raster_image(background_value: str) -> bool:
    """Check if background contains a raster image that blocks color analysis.

    Args:
        background_value: the css value applied to the background property.

    Returns:
        bool: whether the background value includes a raster image or not.
    """
    # Add None check
    if background_value is None:
        return False

    return bool(
        re.search(
            r"url\([^)]*\.(jpg|jpeg|png|gif|webp|bmp)", background_value, re.I
        )
    )


def extract_contrast_color(background_value: str) -> str:
    """
    Extract usable color for contrast analysis, or None.

    Args:
        background_value (str): CSS background property value.

    Returns:
        str: Color value suitable for contrast analysis, or None if no
            usable color found.
    """
    # Add None check at the beginning
    if background_value is None:
        return None

    # Remove raster images - they block color visibility
    if re.search(
        r"url\([^)]*\.(jpg|jpeg|png|gif|webp|bmp)", background_value, re.I
    ):
        return None

    # Handle gradients - extract representative color
    if "gradient" in background_value.lower():
        return extract_gradient_contrast_color(background_value)

    # Handle solid colors
    re_pattern = r"(#[a-f0-9]{3,6}|rgb\([^)]+\)|rgba\([^)]+\)|hsl\([^)]+\)|"
    re_pattern += r"hsla\([^)]+\)|[a-z]+)"
    color_match = re.search(
        re_pattern,
        background_value,
        re.I,
    )
    return color_match.group(1) if color_match else None


def extract_gradient_contrast_color(background_value: str) -> str:
    """
    Extract representative color from gradient for contrast analysis.

    Args:
        background_value (str): CSS gradient value (e.g.,
            'linear-gradient(red, blue)').

    Returns:
        str: Representative color for contrast analysis, or None if no
            color found.
    """
    # Add None check
    if background_value is None:
        return None

    # Strategy: Use the final color in gradient (most visible for reading)
    # This handles: linear-gradient(red, blue) -> blue
    #              radial-gradient(center, red, blue) -> blue

    # Find all colors in gradient
    color_pattern = r"(#[a-f0-9]{3,6}|rgb\([^)]+\)|rgba\([^)]+\)|"
    color_pattern += r"hsl\([^)]+\)|hsla\([^)]+\)|[a-z]+)"
    colors = re.findall(color_pattern, background_value, re.I)

    if colors:
        # Use last color (end of gradient)
        return colors[-1]

    return None


def find_ancestor_background(element: Tag, computed_styles: dict) -> dict:
    """
    Walk up DOM tree to find first ancestor with background.

    Args:
        element (Tag): BeautifulSoup Tag object to start searching from.
        computed_styles (dict): Dictionary mapping elements to their
            computed styles.

    Returns:
        dict: Dictionary containing 'value' (background color) and
            'source_element' (ancestor element or None).
    """
    current = element.parent

    while current:
        if current in computed_styles:
            current_styles = computed_styles[current]

            # Flag to track if we should skip this ancestor
            skip_ancestor = False

            # Check for background-color or background
            for bg_prop in ["background-color", "background"]:
                if bg_prop in current_styles:
                    bg_source = current_styles[bg_prop].get("source")

                    # Skip elements that only have visual inheritance
                    if bg_source == "visual_inheritance":
                        skip_ancestor = True
                        break  # ✅ Break out of property loop

                    # Accept both "rule" and "default" sources
                    if bg_source in ["rule", "default"]:
                        bg_value = current_styles[bg_prop]["value"]

                        # Does this ancestor already is indeterminate status
                        if (
                            current_styles[bg_prop].get("contrast_analysis")
                            == "indeterminate"
                        ):
                            return {
                                "value": None,
                                "source_element": current,
                                "contrast_analysis": "indeterminate",
                                "reason": "ancestor_has_background_image",
                                "original_background": current_styles[
                                    bg_prop
                                ].get("original_background", bg_value),
                            }

                        # Skip None values and continue searching
                        if bg_value is None:
                            continue  # Continue to next property

                        # Check if this background contains a raster image
                        if contains_raster_image(bg_value):
                            return {
                                "value": None,
                                "source_element": current,
                                "contrast_analysis": "indeterminate",
                                "reason": "ancestor_has_background_image",
                                "original_background": bg_value,
                            }

                        # Found explicit background
                        bg_items = current_styles[bg_prop].items()
                        return {
                            "value": bg_value,
                            "source_element": current,
                            "contrast_analysis": "determinable",
                            # Copy metadata from ancestor
                            **{
                                metadata_key: metadata_value
                                for metadata_key, metadata_value in bg_items
                                if metadata_key not in ["value"]
                            },
                        }

            # If we flagged this ancestor to skip, move to next ancestor
            if skip_ancestor:
                current = current.parent
                continue  # ✅ Now this continues to next ancestor

        current = current.parent

    # No ancestor background found, use default
    return {
        "value": DEFAULT_GLOBAL_BACKGROUND,
        "source_element": None,
        "contrast_analysis": "determinable",
        "source": "default",
    }


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


def analyze_elements_for_contrast(
    computed_styles: dict, filename: str
) -> list:
    """Returns a list of elements with text with contrast results

    Args:
        computed_styles: a dictionary of elements with font size, background
            color, color, and any other pertinent metadata
        filename: the name of the HTML document.

    Returns:
        contrast_results: a list of all elements that contain content
    """
    contrast_results = []

    for element in computed_styles:
        # filter out any element that doesn't directly render text
        direct_text = get_direct_text(element)
        if not direct_text:
            continue

        # get element contrast data
        element_data = computed_styles.get(element)
        font_size = element_data["font-size"].get("value")
        size, unit = font_tools.split_value_unit(font_size)
        font_size = font_tools.compute_font_size(size, unit)
        font_weight = element_data.get("font-weight").get("value")
        is_large = is_large_text(font_size, font_weight)
        text_color = element_data["color"].get("value")
        color_hex = color_tools.get_hex(text_color)
        text_bg = element_data["background-color"].get("value")
        bg_hex = color_tools.get_hex(text_bg)
        contrast_ratio = color_tools.contrast_ratio(color_hex, bg_hex)

        # Round to 1 decimal place before running the report
        contrast_ratio = round(contrast_ratio, 1)
        contrast_report = color_tools.get_color_contrast_report(
            color_hex, bg_hex
        )
        contrast_analysis = element_data["background-color"].get(
            "contrast_analysis"
        )
        if is_large:
            aaa_results = contrast_report.get("Large AAA")
            aa_results = contrast_report.get("Large AA")
        else:
            aaa_results = contrast_report.get("Normal AAA")
            aa_results = contrast_report.get("Normal AA")

        # apply results
        element_result = {
            "filename": filename,
            "element_tag": element.name,
            "element_id": element.get("id"),
            "element_class": element.get("class"),
            "text_content": direct_text,
            # Color values and their sources
            "text_color": text_color,
            "text_color_source": extract_property_source(
                element_data["color"]
            ),
            "background_color": text_bg,
            "background_color_source": extract_property_source(
                element_data["background-color"]
            ),
            # Font and contrast results
            "font_size_px": font_size,
            "font_weight": font_weight,
            "is_large_text": is_large,
            "contrast_ratio": contrast_ratio,
            "wcag_aa_pass": aa_results,
            "wcag_aaa_pass": aaa_results,
            "contrast_analysis": contrast_analysis,
        }

        # add to results
        contrast_results.append(element_result)
    return contrast_results


def get_direct_text(element: dict) -> str:
    """returns whether the element contains direct text

    Direct text means text rendered directly through an element. For example,
    in the following code: `<p><strong>Hey, everybody!</strong></p>`, only
    the `<strong>` element directly renders text (not the `<p>`). This is
    because the `<p>` could fail color contrast and the `<strong>` could
    pass. As long as the text itself passes color contrast, it doesn't matter
    if the `<p>` that contains the `<strong>` element does not.

    Args:
        element: the computed colors and size of an element.

    Returns:
        str: the direct text if any otherwise an empty string.
    """
    if element.name in [
        "html",
        "head",
        "title",
        "meta",
        "link",
        "script",
        "style",
    ]:
        return ""
    else:
        for content in element.contents:
            if isinstance(content, NavigableString):
                if content.strip():
                    return content.strip()
    return ""


def extract_property_source(property_data: dict) -> dict:
    """
    Extract source information from a computed property.

    Args:
        property_data (dict): Property dictionary with metadata

    Returns:
        dict: Source information for reporting
    """
    if not property_data:
        return {
            "source_type": "missing",
            "css_file": None,
            "selector": None,
            "inherited_from": None,
        }

    source_type = property_data.get("source", "unknown")

    if source_type == "inheritance":
        return {
            "source_type": "inherited",
            "css_file": property_data.get("css_file"),
            "selector": property_data.get("selector"),
            "inherited_from": getattr(
                property_data.get("inherited_from"), "name", None
            ),
        }
    elif source_type == "visual_inheritance":
        inherited_element = property_data.get("inherited_from")
        return {
            "source_type": "visual_inheritance",
            "css_file": "visual_cascade",
            "selector": "ancestor_background",
            "inherited_from": getattr(inherited_element, "name", None)
            if inherited_element
            else None,
        }
    elif source_type == "rule":
        return {
            "source_type": "css_rule",
            "css_file": property_data.get("css_file"),
            "selector": property_data.get("selector"),
            "inherited_from": None,
        }
    elif source_type == "default":
        return {
            "source_type": "browser_default",
            "css_file": "user_agent_stylesheet",
            "selector": element_name_or_default(property_data),
            "inherited_from": None,
        }
    else:
        return {
            "source_type": source_type,
            "css_file": property_data.get("css_file"),
            "selector": property_data.get("selector"),
            "inherited_from": None,
        }


def element_name_or_default(property_data: dict) -> str:
    """Get element name for default styling or fallback."""
    # You might need to pass element context here
    return "default"


if __name__ == "__main__":
    project_path = "tests/test_files/large_project/"
    project_path = "tests/test_files/contrast_tool_test/"
    contrast_results = generate_contrast_report(project_path, "AAA")
    print(contrast_results)
