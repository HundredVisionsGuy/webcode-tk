# Tutorials

## Set up
In order to grade student projects, you'll want to create a directory in your root project folder. I title mine "project".

Be sure you have installed and imported webcode-tk (I prefer poetry: `poetry install webcode-tk`)

Place your web documents in the project folder.

Be sure to import one or more of the webcode-tk scripts:
`from webcode_tk import html_tools`
or
`from webcode_tk import validator_tools`

In your Python script, set the project folder as a path:
`project_path = "project"`

Create a `tests` folder.
Add one or more pytest files in the tests folder.
I prefer to have a `test_html.py` and `test_css.py`

### HTML Tasks (`test_html.py`)
Here is a suggested script for testing HTML with notes.
```
import pytest
from webcode_tk import html_tools
from webcode_tk import validator_tools as validator

# Get your files from the project folder
project_dir = "project/"
all_html_files = html_tools.get_all_html_files(project_dir)

# Set a list of required elements (per web page) - these must be exact
required_elements = [("doctype", 1),
                     ("html", 1),
                     ("head", 1),
                     ("title", 1),
                     ("h1", 1)]

"""
Set a minimum number of elements
Note how this tests for at least three different types of lists
Doesn't matter which of the three it is as long as there are three.
Note how the list items could be an li or dt.
"""
min_required_elements = [
    ("h2", 3),
    ("ul OR ol OR dl", 3),
    ("li OR dt", 12),
    ("a", 4)
    ]

exact_number_of_elements = html_tools.get_number_of_elements_per_file(
    project_dir, required_elements
)
min_number_of_elements = html_tools.get_number_of_elements_per_file(
    project_dir, min_required_elements
)
html_validation_results = validator.get_project_validation(project_dir)


@pytest.fixture
def html_files():
    html_files = html_tools.get_all_html_files(project_dir)
    return html_files


def test_has_index_file(html_files):
    assert "project/index.html" in html_files


@pytest.mark.parametrize("file,element,num", exact_number_of_elements)
def test_files_for_exact_number_of_elements(file, element, num):
    if not html_files:
        assert False
    actual = html_tools.get_num_elements_in_file(element, file)
    assert actual == num


@pytest.mark.parametrize("file,element,num", min_number_of_elements)
def test_files_for_minimum_number_of_elements(file, element, num):
    if not html_files:
        assert False
    if "or" in element.lower():
        elements = element.split()
        actual = 0
        for el in elements:
            el = el.strip()
            actual += html_tools.get_num_elements_in_file(el, file)
    else:
        actual = html_tools.get_num_elements_in_file(element, file)
    assert actual >= num


def test_passes_html_validation(html_files):
    errors = []
    if not html_files:
        assert "html files" in html_files
    for file in html_files:
        results = validator.get_markup_validity(file)
        for result in results:
            errors.append(result.get("message"))
    assert not errors

```
The goal is to have readable pytests. Below is a sample run of a student's project.
```
=========================== short test summary info ============================
FAILED tests/test_html.py::test_files_for_minimum_number_of_elements[project/index.html-p-6] - assert 0 >= 6
FAILED tests/test_html.py::test_files_for_minimum_number_of_elements[project/index.html-a-4] - assert 0 >= 4
FAILED tests/test_html.py::test_passes_html_validation - AssertionError: assert not ['Element “ul” not allowed as child of element “...
========================= 3 failed, 9 passed in 1.42s ==========================
```
