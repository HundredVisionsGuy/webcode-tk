"""A set of tools to conduct some UX (User eXperience) checks.

As of now, I just want to check for best UX and SEO practices such
as checking for best practices in writing for the web.

The primary source of information we will begin to use are from
[Writing Compelling Digital Copy](https://www.nngroup.com/courses/writing/).

According to the article...
* Be Succinct! (Writing for the Web)
* "The 3 main guidelines for writing for the web are:
    - Be succinct: write no more than 50% of the text you would have used in a
    hardcopy publication
    - Write for scannability: don't require users to read long continuous
    blocks of text
    - Use hypertext to split up long information into multiple pages"
"""
import re
from collections.abc import Sequence
from typing import Union

import textatistic
from file_clerk import clerk
from textatistic import Textatistic

from webcode_tk import html_tools

DEFAULT_GOALS = {
    "avg_words_sentence_range": (10, 25),
    "max_sentences_per_paragraph": 4,
    "min_num_single_sentence_paragraphs": 2,
    "min_word_count": 400,
}
DEFAULT_EXCEEDS_GOALS = {
    "max_avg_words_sentence": 20,
    "max_li_per_list": 9,
    "max_words_per_li": 45,
    "max_words_per_paragraph": 80,
    "min_word_count": 800,
}


def get_flesch_kincaid_grade_level(path: str) -> float:
    """returns the required education to be able to understand the text.

    We're only looking at the paragraphs (not headers or list items) and
    ignoring break tags as being paragraph breaks (that could be up for
    debate in the future).

    This function first checks to see if it's a project folder or just a
    single file and ascertains for all HTML documents if it's a project.

    Args:
        path: the path to the page or project that we are measuring.

    Returns:
        grade_level: the US grade level equivalent."""

    # convert all paragraph content into a single string
    paragraphs = get_all_paragraphs(path)
    paragraph_text = get_paragraph_text(paragraphs)

    # get stats from textatistic
    r = Textatistic(paragraph_text)
    grade_level = r.fleschkincaid_score

    # return grade level rounded to 1 decimal point
    return round(grade_level, 1)


def get_readability_stats(
    path: str, elements: Union[str, Sequence] = "p"
) -> dict:
    """returns a dictionary of various readability stats.

    It will collect all stats from the textastic libary as well as add
    a few of my own (words per sentence, sentences per paragraph).

    Args:
        path: the path to the file or folder (only looks at HTML files)
        elements: by default we will only look at the text from paragraph
            tags. You could supply other elements in the form of a list or
            tuple (e.g. ['p', 'div', 'li', 'figcaption']).

    Returns:
        stats: a dictionary of stats on readability metrics.
    """
    stats = {}

    # Get text and numbers
    text = get_text_from_elements(path, elements)
    num_lines = len(text)

    # get stats from textatistic
    text = "\n".join(text)
    r = Textatistic(text)

    for key, value in r.scores.items():
        stats[key] = round(value, 2)
    stats["character_count"] = r.char_count
    stats["word_count"] = r.word_count
    stats["sentence_count"] = r.sent_count
    stats["paragraph_count"] = num_lines
    stats["words_per_sentence"] = round(r.word_count / r.sent_count, 2)
    stats["sent_per_paragraph"] = round(r.sent_count / num_lines, 2)

    return stats


def get_paragraph_text(paragraphs: list) -> str:
    """Returns a string of all the contents of the list of paragraphs

    Args:
        paragraphs: a list of paragraph elements.

    Returns:
        paragraph_text: a string of all the content of the paragraph
            elements.
    """
    paragraph_text = ""
    for paragraph in paragraphs:
        paragraph_text += html_tools.get_element_content(paragraph) + "\n"
    return paragraph_text.strip()


def get_all_paragraphs(path: str) -> list:
    """returns a list of paragraph elements from a single file or project
    folder.

    It checks the path to determine if it's a path to a single page or a
    project folder.

    Args:
        path: a string path to either an html document or a project folder.

    Returns:
        paragraphs: a list of paragraph elements."""

    paragraphs = []
    is_single_page = "html" == clerk.get_file_type(path)

    if not is_single_page:
        # it's a project, so we need to process all html files in the folder
        all_files = clerk.get_all_files_of_type(path, "html")
        for file in all_files:
            paragraphs += html_tools.get_elements("p", file)
    else:
        paragraphs += html_tools.get_elements("p", path)
    return paragraphs


def get_text_from_elements(
    path: str, elements: Union[str, Sequence] = "p"
) -> list:
    """returns a list of text from elements (as strings) from a single file or
    project folder.

    It checks the path to determine if it's a path to a single page or a
    project folder. It then uses the elements to determine from which
    HTML element it will grab paragraphs.

    By default, it will only pull paragraphs from the `<p>` tag, but you
    can specify other elements (e.g. `<div>`, `<li>`, `<figcaption>`, etc.).

    NOTE: When selecting other tags, pass it a list or tuple of strings. Only
    specify the element without angle brackets (e.g. `['p', 'li', 'div']`)

    Args:
        path: a string path to either an html document or a project folder.
        elements: the elements we want to pull our paragrphs from.
    Returns:
        paragraphs: a list of strings - text only without markup (for example
        if an anchor is nested in a pargraph, the markup will be extracted, and
        only the visible text on the page will be present."""

    paragraphs = []
    is_single_page = "html" == clerk.get_file_type(path)
    if elements == "p":
        elements = ["p"]
    if not is_single_page:
        # it's a project, so we need to process all html files in the folder
        all_files = clerk.get_all_files_of_type(path, "html")
        for file in all_files:
            for element in elements:
                markup = html_tools.get_elements(element, file)
                for tag in markup:
                    text = extract_text(tag)
                    paragraphs.append(text)
    else:
        for element in elements:
            markup = html_tools.get_elements(element, path)
            for tag in markup:
                text = extract_text(tag)
                paragraphs.append(text)
    return paragraphs


def remove_extensions(text: str) -> str:
    """removes extension from filenames.

    Filenames with extensions end up causing textatistic to count filenames
    as two words instead of one, and we don't really need to count the
    extensions when calculating readability stats.

    Args:
        text: the text which may or may not have filenames in them.

    Returns:
        newtext: the text without file extensions.
    """
    newtext = ""

    # get the last character just in case it gets dropped with extension.
    last_char = text[-1]
    regex = r"\.[a-zA-Z0-9]+"
    newtext = re.sub(regex, "", text)

    # add back the last character if it was dropped.
    if newtext[-1] != last_char:
        newtext += last_char
    return newtext


def extract_text(tag) -> str:
    """extracts only the text from a tag (no markup)

    Args:
        tag: this is a Tag (bs4)
    Returns:
        text: just the visible text from the element (with no
        nested markup)."""
    text = tag.text
    text = " ".join(text.split())
    return text


def get_words_per_paragraph(path: str) -> float:
    """returns average number of words per paragraph

    uses Textatistic stats"""
    paragraphs = get_all_paragraphs(path)
    text = get_paragraph_text(paragraphs)
    words = get_word_count(text)
    num_paragraphs = len(paragraphs)
    return round(words / num_paragraphs, 1)


def get_word_count(txt: str) -> int:
    """returns word count of text.

    Args:
        txt: the raw text (may or may not contain line returns)

    Returns:
        word_count: number of words as measured by Textastic
    """

    text = txt.replace("\n", " ")
    word_count = textatistic.word_count(text)
    return word_count


def check_li_count(filename: str, list_type: str, max: int, min=3) -> list:
    """returns any warnings regarding li count

    Warns if too many lis in a list, too few in a list (default is 3), or
    too much content in a list item.

    Args:
        filename: name of the HTML document.
        list_type: "ul" or "li" - we don't check definition lists.
        max: maximum recommended list items per list.
        min: minimum recommend list items per list (default is 3)

    Returns"""
    warnings = []
    uls = html_tools.get_elements(list_type, filename)
    if uls:
        num_lis = 0
        for ul in uls:
            lis = html_tools.get_element_content(ul)
            li_count = lis.count("<li>")
            num_lis += li_count
            if num_lis > max:
                msg = f"warning: ul should have less than {max} "
                msg += f"lis per ul - you have {num_lis} in {filename}"
                warnings.append(msg)
    return warnings


def check_li_word_count(filepath: str, max=45) -> list:
    """sends warnings if too many words are in a list item.

    Args:
        filepath: relative path to the HTML document in question.
        max: maximum number of words per li (default is 45)

    Returns:
        warnings: any warnings about the li content having too many words.
    """
    warnings = []
    filename = clerk.get_file_name(filepath)
    lis = html_tools.get_elements("li", filepath)
    for li in lis:
        txt = html_tools.get_element_content(li)
        text = txt.replace("\n", " ")
        word_count = textatistic.word_count(text)
        if word_count > max:
            msg = "warning: An <li> element exceeds recommended word"
            msg += f" count of {max} {filename} has an <li> with "
            msg += f"{word_count} words."
            warnings.append(msg)
    return warnings


def get_usability_report(
    project_dir: str,
    elements: tuple,
    goals=DEFAULT_GOALS,
    exceeds=DEFAULT_EXCEEDS_GOALS,
) -> list:
    """Generates a list of pass, fail, and warnings on usability.

    If goals or exceeds not set, goals & exceeds should follow the example
    keys...
    goals   avg_words_sentence_range, max_sentences_per_paragraph,
            min_word_count, min_num_single_sentence_paragraphs

    exceeds max_avg_words_sentence, max_li_per_list, max_sentence_paragraph,
            max_words_per_li, max_words_per_paragraph, min_word_count

    Args:
        project_dir: path to project folder
        goals: set of goals to test for.
        exceeds: set of metrics to determine if content goes above & beyond.
        elements: set of elements to capture

    Returns:
        report: a list of pass, fails, and warnings
    """
    report = []
    readability_report = get_readability_stats(project_dir, elements)
    all_html_files = clerk.get_all_files_of_type(project_dir, "html")
    if not all_html_files and ".html" == project_dir[-5:]:
        all_html_files = [
            project_dir,
        ]
    for type, expected in goals.items():
        if type == "avg_words_sentence_range":
            words_per_sentence = readability_report.get("words_per_sentence")
            min, max = expected
            msg = ""
            if words_per_sentence <= min:
                msg = "fail: not enough average words per sentence (actual = "
                msg += f"{words_per_sentence})."
            elif words_per_sentence >= max:
                msg = f"fail: sentences are too long (should be between {min}"
                msg += f" & {max}) (actual = {words_per_sentence} - should be"
                msg += f" no more than {max})"
            else:
                msg += f"pass: at {words_per_sentence} words per sentence, "
                msg += f"you are within expected range ({min}-{max} wps)."
            report.append(msg)
        if type == "max_sentences_per_paragraph":
            max_sent = expected
            min_single_sentence_data = []
            single_sentences = 0
            for file in all_html_files:
                paragraphs = html_tools.get_elements("p", file)
                para_num = 0
                filename = clerk.get_file_name(file)
                for paragraph in paragraphs:
                    para_num += 1
                    content = html_tools.get_element_content(paragraph).strip()
                    sentence_count = textatistic.sent_count(content)
                    if content and sentence_count == 0:
                        sentence_count = 1
                    if sentence_count == 1:
                        single_sentences += 1
                    if sentence_count > max_sent:
                        sentence_msg = sentence_count - max_sent
                        if sentence_msg == 1:
                            sentence_msg = f"{sentence_msg} more sentence"
                        else:
                            sentence_msg = f"{sentence_msg} more sentences"
                        msg = f"fail: in file, {filename}, paragraph #"
                        msg += f"{para_num}, you have {sentence_msg} than the"
                        msg += f" maximum number of {max_sent}."
                        report.append(msg)
                min_single_sentence_data.append((filename, single_sentences))
        if type == "min_word_count":
            num_words = readability_report.get("word_count")
            if num_words >= expected:
                msg = f"pass: {filename} at {num_words} words has enough "
                msg += "words to effectively measure readability."
            else:
                msg = f"fail: {filename} at only {num_words} words, does not "
                msg += "have enough words to effectively measure readability."
            report.append(msg)
        if type == "min_num_single_sentence_paragraphs":
            for datum in min_single_sentence_data:
                name, paras_with_one_sentence = datum
                if paras_with_one_sentence >= expected:
                    msg = f"pass: {name} has enough paragraphs with just one"
                    msg += " sentence."
                else:
                    msg = f"fail: {name} does not have enough paragraphs with"
                    msg += " a single sentence. You should have at least"
                    msg += f" {expected}."
                report.append(msg)

    # Get List data for exceeds:
    li_report = []
    for file in all_html_files:
        filename = clerk.get_file_name(file)
        max_li_per_ul = exceeds.get("max_li_per_list")
        li_report += check_li_count(file, "ul", max_li_per_ul)
        li_report += check_li_word_count(file)

    for type, goal in exceeds.items():
        if type == "max_avg_words_sentence":
            if words_per_sentence > 20:
                warning = "warning: Average words per sentence should be 20 "
                warning += "or less (you have an average of "
                warning += f"{words_per_sentence})."
                report.append(warning)
        if type == "max_li_per_list":
            if li_report:
                for item in li_report:
                    report.append(item)
        if type == "max_sentence_paragraph":
            if sentence_count > goal:
                warning = "warning: for best results, you should have fewer "
                warning += f"than {goal} sentences per paragraph, but you "
                warning += f"have {sentence_count}."
        if type == "max_words_per_li":
            if li_report:
                for item in li_report:
                    if "An <li> element exceeds recommended" in item:
                        report.append(item)
        if type == "max_words_per_paragraph":
            paragraphs_exceeding = 0
            maximum_num_words = 0
            for paragraph in paragraphs:
                content = html_tools.get_element_content(paragraph)
                word_count = textatistic.word_count(content)
                if word_count > expected:
                    paragraphs_exceeding += 1
                    if word_count > maximum_num_words:
                        maximum_num_words = word_count
            if paragraphs_exceeding:
                msg = f"warning: you should not exceed {expected} words per "
                msg += f"paragraph, but you have {paragraphs_exceeding} "
                msg += "paragraphs that exceed, the maximum having "
                msg += f"{maximum_num_words} words."
                report.append(msg)
        if type == "min_word_count":
            # warn if meets minimum word count but not the goal for exceeds
            min_words = goals.get("min_word_count")
            if num_words > min_words and num_words < goal:
                msg = "warning: for best results, you should have at least"
                msg += f" {goal} words in your project."
                report.append(msg)
    return report


if __name__ == "__main__":
    # let's test some stuff out.
    path = "tests/test_files/large_project/"
    all = extract_text(path, ["p", "figcaption"])
    all = get_paragraph_text(all)
    print(all)
