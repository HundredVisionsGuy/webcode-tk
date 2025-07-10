""" Contrast Tools
Tools for determining CSS as applied through inheritance and the cascade.

This module analyzes the DOM, inheritance, and the cascade to determine all
styles applied to every element on a page. It scans each stylesheet and
applies each style, one at a time, to all applicable elements and their
children.
"""
import tinycss2
from bs4 import BeautifulSoup
from file_clerk import clerk


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

    # TODO: Analyze CSS Files
    for file in css_files:
        print(file)
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
        parsed = tinycss2.parse_stylesheet_bytes(css)
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


if __name__ == "__main__":
    project_path = "tests/test_files/large_project/"
    contrast_results = analyze_contrast(project_path)
