from bs4 import BeautifulSoup

from webcode_tk import contrast_tools


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
