"""
Test for any bugs found in a project
TODO The next time a project triggers an error exposing a need...
1.  put the files in question in project_refactor_tests folder (
    see `project_path`).
2.  bring in the test code from that project to recreate the bug

"""
import pytest

from webcode_tk import css_tools as css
from webcode_tk import html_tools as html

project_path = "tests/test_files/project_refactor_tests/"
html_files = html.get_all_html_files(project_path)
styles_by_html_files = css.get_styles_by_html_files(project_path)


@pytest.fixture
def html_docs():
    return html_files


# for now, run a pytest
def test_for_files_in_refactor_test_folder(html_docs):
    assert html_docs
