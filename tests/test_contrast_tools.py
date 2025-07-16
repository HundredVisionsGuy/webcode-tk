import os

from bs4 import BeautifulSoup

from webcode_tk import contrast_tools
from webcode_tk.contrast_tools import append_style_data
from webcode_tk.contrast_tools import get_css_source_order
from webcode_tk.contrast_tools import get_or_parse_external_stylesheet
from webcode_tk.contrast_tools import load_css_files
from webcode_tk.contrast_tools import parse_internal_style_tag


def test_get_parsed_documents(tmp_path):
    # Create sample HTML files
    file1 = tmp_path / "index.html"
    file1.write_text("<html><body><h1>Home</h1></body></html>")
    file2 = tmp_path / "about.html"
    file2.write_text("<html><body><p>About</p></body></html>")

    # Run the function
    results = contrast_tools.get_parsed_documents(str(tmp_path))

    # Check that both files are parsed
    filenames = [entry["filename"] for entry in results]
    assert "index.html" in filenames
    assert "about.html" in filenames

    # Check that soup objects are correct
    for entry in results:
        assert isinstance(entry["soup"], BeautifulSoup)
        # Optionally, check content
        if entry["filename"] == "index.html":
            assert entry["soup"].h1.text == "Home"
        if entry["filename"] == "about.html":
            assert entry["soup"].p.text == "About"


def test_css_source_order_mixed():
    html = """
    <html>
      <head>
        <link rel="stylesheet" href="a.css">
        <style>body { color: red; }</style>
        <link rel="stylesheet" href="b.css">
      </head>
      <body></body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    sources = contrast_tools.get_css_source_order(soup)
    assert sources == [
        {"type": "external", "href": "a.css"},
        {"type": "internal", "content": "body { color: red; }"},
        {"type": "external", "href": "b.css"},
    ]


def test_css_source_order_only_external():
    html = """
    <html>
      <head>
        <link rel="stylesheet" href="main.css">
      </head>
      <body></body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    sources = contrast_tools.get_css_source_order(soup)
    assert sources == [
        {"type": "external", "href": "main.css"},
    ]


def test_css_source_order_only_internal():
    html = """
    <html>
      <head>
        <style>h1 { color: blue; }</style>
      </head>
      <body></body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    sources = contrast_tools.get_css_source_order(soup)
    assert sources == [
        {"type": "internal", "content": "h1 { color: blue; }"},
    ]


def test_css_source_order_empty_head():
    html = """
    <html>
      <head></head>
      <body></body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    sources = contrast_tools.get_css_source_order(soup)
    assert sources == []


def test_get_css_source_order_mixed():
    html = """
    <html>
      <head>
        <link rel="stylesheet" href="a.css">
        <style>body { color: red; }</style>
        <link rel="stylesheet" href="b.css">
      </head>
      <body></body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    sources = get_css_source_order(soup)
    assert sources == [
        {"type": "external", "href": "a.css"},
        {"type": "internal", "content": "body { color: red; }"},
        {"type": "external", "href": "b.css"},
    ]


def test_parse_internal_style_tag():
    css = "body { color: blue; }"
    rules = parse_internal_style_tag(css)
    assert isinstance(rules, list)
    assert any(rule.type == "qualified-rule" for rule in rules)


def test_get_or_parse_external_stylesheet(tmp_path):
    css_content = b"body { background: #fff; }"
    css_file = tmp_path / "test.css"
    css_file.write_bytes(css_content)
    cache = {}
    # First call parses and caches
    rules = get_or_parse_external_stylesheet(
        str(css_file.name), str(tmp_path) + os.sep, cache
    )
    assert isinstance(rules, list)
    assert css_file.name in cache
    # Second call uses cache
    rules2 = get_or_parse_external_stylesheet(
        str(css_file.name), str(tmp_path) + os.sep, cache
    )
    assert rules2 is rules


def test_append_style_data():
    css_source = {"index.html": []}
    sheet = {"type": "internal"}
    href = "style_tag"
    parsed = ["dummy_rule"]
    append_style_data("index.html", sheet, href, parsed, css_source)
    assert len(css_source["index.html"]) == 1
    entry = css_source["index.html"][0]
    assert entry["source_type"] == "internal"
    assert entry["css_name"] == "style_tag"
    assert entry["stylesheet"] == ["dummy_rule"]


def test_load_css_files(tmp_path):
    # Create a fake HTML file and CSS file
    html_content = """
    <html>
      <head>
        <link rel="stylesheet" href="test.css">
        <style>body { color: green; }</style>
      </head>
      <body></body>
    </html>
    """
    css_content = b"body { background: #fff; }"
    html_file = tmp_path / "index.html"
    css_file = tmp_path / "test.css"
    html_file.write_text(html_content)
    css_file.write_bytes(css_content)

    # Simulate parsed HTML docs
    soup = BeautifulSoup(html_content, "html.parser")
    html_docs = [{"filename": "index.html", "soup": soup}]
    css_files = load_css_files(html_docs, str(tmp_path) + os.sep)

    # Should contain both external and internal sources
    assert any(
        item["css_name"] == "test.css"
        for css_dict in css_files
        for html_file, items in css_dict.items()
        for item in items
    )

    assert any(
        item["css_name"] == "style_tag"
        for css_dict in css_files
        for html_file, items in css_dict.items()
        for item in items
    )
