import pytest

from webcode_tk import cascade_tools as cascade
from webcode_tk import css_tools as css

project_path = "tests/test_files/single_file_project/"
styles_by_html_files = css.get_styles_by_html_files(project_path)


@pytest.fixture
def single_file_tree():
    css_tree = None
    file = styles_by_html_files[0]
    filepath = file.get("file")
    sheets = file.get("stylesheets")
    css_tree = cascade.CSSAppliedTree(filepath, sheets)
    return css_tree


def test_css_tree_for_tree(single_file_tree):
    assert single_file_tree
