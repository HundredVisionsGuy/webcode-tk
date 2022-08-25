import os
import re

import bs4
import mechanicalsoup
import requests
from bs4 import BeautifulSoup
from file_clerk import clerk

w3cURL = "https://validator.w3.org/nu/?out=json"

# Instantiate a stateful browser
browser = mechanicalsoup.StatefulBrowser()


def get_num_errors(report: list) -> int:
    """Gets the number of errors from a list.

    Args:
        report: a list of error messages.

    Returns:
        num_errors: how many error messages there are."""
    num_errors = len(report)
    return num_errors


def clean_error_msg(msg: str) -> str:
    """Cleans up the msg to remove unwanted details.

    This function removes new lines, added spaces, and strips spaces.

    Args:
        msg: a string message.

    Returns:
        msg: cleaned of all unnecessary text."""
    msg = msg.replace("\n", "")
    msg = re.sub(r"[ ]{2,}", " ", msg)
    msg = msg.replace(" :", ":")
    msg = msg.strip()
    return msg


def get_css_errors_list(val_results: bs4.ResultSet) -> list:
    """Extracts a list of CSS errors from the CSS validator results.

    This function takes a ResultSet of Tags from the validate_css()
    function, and extracts all errors as a list of strings.

    Args:
        val_results: the results from the [CSS validator]
        (jigsaw.w3.org/css-validator)

    Returns:
        error_list: a list of any error messages from the
            ResultSet. Each error message is in string format.
    """
    soup = bs4.BeautifulSoup(str(val_results), "lxml")
    errors = soup.find_all("td")
    num_errors = len(errors)
    error_list = []
    for i in range(num_errors):
        # every 3rd TD has the error message
        if (i - 2) % 3 == 0:
            msg = errors[i].text
            msg = clean_error_msg(msg)
            error_list.append(msg)
    return error_list


def get_markup_validity(file_path: str) -> list:
    """returns a list of errors from a file.

    This function takes the contents of a file and runs it through
    the [W3C validator](https://validator.w3.org/nu/?out=json) and
    returns a list of warnings and errors from the validator in a
    dictionary object. If there are no warnings or errors, it returns
    an empty list. It also checks the response code, and if it's not
    200, then it returns an alert message (in the form of a list).

    Args:
        file_path: the relative path to an HTML or CSS document (in
            relationship to the root of the python project.

    Returns:
        errors: a list of dictionary types (converted from the JSON
            response from the validator."""
    errors = []
    payload = open(file_path)
    with open(file_path, "rb") as payload:
        headers = {
            "content-type": "text/html; charset=utf-8",
            "Accept-Charset": "UTF-8",
        }

        r = requests.post(w3cURL, data=payload, headers=headers)
        errors = r.json()
        errors = errors.get("messages")

        # raise the alarm if the response code is not 200
        if r.status_code != 200:
            errors = [
                {
                    "type": "ALERT!",
                    "lastLine": "NA",
                    "lastColumn": "NA",
                    "firstColumn": "NA",
                    "message": "Problems connecting with the validator - "
                    "probably no connection",
                    "extract": "NA",
                    "hiliteStart": "NA",
                    "hiliteLength": "NA",
                }
            ]
    return errors


def get_num_markup_errors(markup_response: list) -> int:
    """Gets the number of markup errors (not warnings).

    This function sifts through the online validator response and
    counts the number of errors only (ignores any warnings).

    Args:
        markup_response: a list a markup errors and warnings from the
            online validator.

    Returns:
        count: the number of errors in the validator response."""
    count = 0
    for i in markup_response:
        if i["type"] == "error":
            count += 1
    return count


def get_num_markup_warnings(markup_errors: list) -> int:
    """Gets the number of markup warnings (not errors).

    This function sifts through the online validator response and
    counts the number of warnings only (ignores any errors).

    Args:
        markup_errors: a list a markup errors and warnings from the
            online validator.

    Returns:
        count: the number of warnings in the validator response."""
    count = 0
    for i in markup_errors:
        if i["type"] == "info":
            count += 1
    return count


def get_html_file_names(dir_path=r"." + os.sep + "project") -> list:
    """Gets a list of all html documents from directory path.

    This function takes a directory path (if provided) in string form
    and returns a list of all HTML document paths from that directory.
    If no path is provided, it assumes there's a project folder in the
    root of the project folder, and it will check there.

    Args:
        dir_path (str): a path to the directory you want to check.
            It has a default directory of `project/` in case no
            directory is provided.

    Returns:
        names: a list of filenames as relative links to the HTML
            documents in the directory."""
    names = []

    # remove final slash if present
    if dir_path[-1] == "/":
        dir_path = dir_path[:-1]
    for subdir, _dirs, files in os.walk(dir_path):
        for filename in files:
            # if using posix (forward slash), use posix
            # otherwise, use the os.sep (for Windows paths)
            if "/" in subdir:
                file_path = subdir + "/" + filename
            else:
                file_path = subdir + os.sep + filename
            if file_path.endswith(".html"):
                names.append(file_path)
    return names


def get_num_html_files(dir_path=r"." + os.sep + "project") -> int:
    """Returns the number of HTML documents in project folder.

    This function will look into the project directory (`dir_path` or
    the default project location, which is "project" inside of the
    root Python project folder. It will return the number of all HTML
    documents (including folders nested inside of `dir_path`).

    Args:
        dir_path (str): the path to the folder you want to check. It
            has a default location of project (inside the root folder
            of your python project.

    Returns:
        num_html_files: the number of HTML documents within all
            folders of the provided (or default) project folder."""
    html_files = get_html_file_names(dir_path)
    num_html_files = len(html_files)
    return num_html_files


def is_css_valid(validator_results):
    """Checks to make sure CSS code is valid"""
    # create a soup of validator results
    soup = BeautifulSoup(str(validator_results[0]), "html.parser")
    return bool(soup.find(id="congrats"))


def validate_css(css_code: str) -> bs4.ResultSet:
    """Validates CSS and returns the results from the css-validator.

    This function will send any CSS code as a string to the W3.org
    css validator using a mechanicalsoup browser, and it will return
    the validator results as a ResultSet (a list of query results in
    the form of bs4 Tags).

    Args:
        css_code: CSS code in the form of a string.

    Returns:
        results: A ResultSet of Tag objects.
    """
    try:
        browser.open("https://jigsaw.w3.org/css-validator")
        # Fill-in the search form based on css_code
        browser.select_form("#validate-by-input form")
        browser["text"] = css_code
        browser.submit_selected()
        results = browser.get_current_page().select("#results_container")
    except Exception:
        # Convert the file "no_css_connection.html" into a soup tag object
        no_connection_code = clerk.file_to_string(
            "webanalyst/no_css_connection.html"
        )
        soup = BeautifulSoup(no_connection_code, "lxml")
        # Convert string to result set
        results = soup.select("#results_container")
    return results


if __name__ == "__main__":
    path = "tests/test_files/sample_with_errors.html"
    report = get_markup_validity(path)
    print("report is a {}.".format(type(report)))
    for item in report:
        print(item)
    num_errors = get_num_markup_errors(report)
    # how many html files in project directory?
    html_files = get_html_file_names()

    # test getting number of errorsz
    print(get_num_errors(report))

    css_code = clerk.file_to_string("tests/test_files/css_for_testing.css")
    css_validator_results = validate_css(css_code)
    is_valid = is_css_valid(css_validator_results)
    print(is_valid)
    css_validator_results = validate_css("p } color: #336699; }")
    print(css_validator_results)
    is_valid = is_css_valid(css_validator_results)
    print(is_valid)
