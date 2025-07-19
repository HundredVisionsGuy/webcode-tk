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
"""
import tinycss2
from bs4 import BeautifulSoup
from file_clerk import clerk

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

    # TODO: Apply CSS rules to elements and compute styles
    # computed_styles = compute_element_styles(soup, doc_css_rules)

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

    for element in soup.find_all():
        if not element.is_empty_element and element.get_text(strip=True):
            # The element object itself becomes the key
            element_styles[element] = {
                "color": DEFAULT_GLOBAL_COLOR,
                "background-color": DEFAULT_GLOBAL_BACKGROUND,
                "font-size": f"{ROOT_FONT_SIZE}px",
            }

            # Apply element-specific defaults
            # Apply link colors
            if element.name == "a":
                element_styles[element]["color"] = DEFAULT_LINK_COLOR
                element_styles[element]["visited-color"] = DEFAULT_LINK_VISITED

            if element.name in IS_BOLD:
                element_styles[element]["font-weight"] = "bold"

            if element.name in HEADING_FONT_SIZES:
                element_styles[element][
                    "font-size"
                ] = f"{HEADING_FONT_SIZES[element.name]}px"

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


if __name__ == "__main__":
    project_path = "tests/test_files/large_project/"
    contrast_results = analyze_contrast(project_path)
