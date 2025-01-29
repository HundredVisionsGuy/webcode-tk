"""
A group of functions that work with css_tools and cascade_tools to provide
reports on CSS animations.
"""
from collections.abc import Iterable
from typing import Union

from file_clerk import clerk

from webcode_tk import css_tools
from webcode_tk import utils


def get_animation_report(project_dir: str) -> list:
    """gets a report on the implementation of animation in a project.

    The animation report should contain a single entry for each HTML
    file. Each HTML file will have a list of animations: the name of the
    keyframe, a list of each keyframe type (percentage, from, or two),
    and a list of properties included and if it is transform, it will
    treat each type of transform as a unique property: eg. skew(), rotate(),
    translate(), etc.

    Args:
        project_dir: the path to the project folder.

    Returns:
        report: a list of dictionary objects"""
    report = []
    # Animation Tests (test for # of keyframes and types of transitions)
    files_by_styles = css_tools.get_styles_by_html_files(project_dir)

    # loop through each file's stylesheet objects
    keyframe_animations = []

    for file in files_by_styles:
        for sheet in file.get("stylesheets"):
            filename = clerk.get_file_name(file.get("file"))
            nested_at_rules = sheet.nested_at_rules
            for at_rule in nested_at_rules:
                if "@keyframes" in at_rule.at_rule:
                    keyframe_animations.append(
                        (filename, at_rule.at_rule, at_rule.rulesets)
                    )

    report = []
    animation_dict = {}
    for animation in keyframe_animations:
        filename, keyframe, rulesets = animation
        if filename not in animation_dict:
            animation_dict = {
                filename: {
                    "keyframes": [],
                    "pct_keyframes": [],
                    "from_keyframes": [],
                    "to_keyframes": [],
                    "properties": set(),
                }
            }
            report.append(animation_dict)
        animation_dict[filename]["keyframes"].append(keyframe)
        current_dict = animation_dict.get(filename)
        for rule in rulesets:
            declarations = rule.declaration_block.declarations
            for declaration in declarations:
                if declaration.property == "transform":
                    value_type = declaration.value
                    value_split = value_type.split("(")
                    transform_value = "transform-" + value_split[0] + "()"
                    current_dict["properties"].add(transform_value)
                else:
                    current_dict["properties"].add(declaration.property)
            if "%" in rule.selector:
                current_dict["pct_keyframes"].append(rule.selector)
            elif "from" in rule.selector:
                current_dict["from_keyframes"].append(rule.selector)
            elif "to" in rule.selector:
                current_dict["to_keyframes"].append(rule.selector)
    return report


def get_keyframe_data(report: list) -> dict:
    """return a list of keyframe types and numbers from an animation report

    The goal is to track all data related to animation keyframes per file.
    The data is a dictionary of filenames. The filenames will be the key, and
    each filename's values will be a dictionary of keyframe names, number of
    percentage keyframes, and the number of from {} and to {} keyframes.

    Args:
        report: an animation report, which is a list of project files with a
            dictionary of details

    Returns:
        data: a dictionary of filenames as primary keys with a dictionary of
            keyframe data as the key's value.
    """
    data = {}
    for animation_data in report:
        filename = utils.get_first_dict_key(animation_data)
        if filename not in data:
            data[filename] = {}
            names = animation_data[filename].get("keyframes")
            data[filename]["keyframe_names"] = names
            data[filename]["froms_tos"] = 0
            data[filename]["pct_keyframes"] = 0
        else:
            names = animation_data[filename].get("keyframes")
            if names:
                data[filename]["keyframe_names"] += names
        pct_keyframes = animation_data[filename].get("pct_keyframes")
        froms = animation_data[filename].get("from_keyframes")
        if froms:
            data[filename]["froms_tos"] += len(froms)
        tos = animation_data[filename].get("to_keyframes")
        if tos:
            data[filename]["froms_tos"] += len(tos)
        if pct_keyframes:
            data[filename]["pct_keyframes"] += len(pct_keyframes)
    return data


def get_keyframe_report(
    project_folder: str, num_goal: int, pct_goal=None, from_to_goals=None
) -> list:
    """returns a list of pass/fail messages (1 for each goal in each file).

    A report that allows you to set the minimum number of keyframes for each
    file. By setting num_goal, you are stating how many keyframes in all you
    expect to see in a project.

    You can also set a minimum number of percentage keyframes, and the minimum
    number of from {} and to {} keyframes.

    NOTE: for every goal, there will be a report on that goal (one for each
    file). If your project has two files, and you set all three goals (
    num_goal, pct_goal, and from_to_goals), the report will create a list of
    6 messages.

    Args:
        project_folder: the folder that houses the project.
        num_goal: the minimum number of keyframes per file (overall)
        pct_goal: the minimum number of percentage keyframes we would want
            to see.
        from_to_goals: the minimum number of from and to keyframes.

    Returns:
        results: a list of messages (one for each file in the project) with
            a pass or fail with number present of each type.
    """
    report = []
    animation_report = get_animation_report(project_folder)
    keyframe_results = get_keyframe_data(animation_report)
    for file, results in keyframe_results.items():
        pct_keyframes = results["pct_keyframes"]
        if isinstance(pct_keyframes, Iterable):
            pct_keyframes = len(pct_keyframes)
        num_froms_tos = results["froms_tos"]
        if isinstance(num_froms_tos, Iterable):
            num_froms_tos = len(num_froms_tos)
        overall_num = pct_keyframes + num_froms_tos
        if overall_num >= num_goal:
            msg = f"pass: {file} has {overall_num} keyframes (enough "
            msg += "overall to meet)."
        else:
            remaining = num_goal - overall_num
            msg = f"fail: {file} has only {overall_num} keyframes (needs "
            msg += f"{remaining} more to pass)."
        report.append(msg)
        if pct_goal:
            if pct_keyframes >= pct_goal:
                msg = f"pass: {file} has {pct_keyframes} percentage "
                msg += "keyframes."
            else:
                msg = f"fail: {file} does not have enough percentage "
                msg += "keyframes to pass."
            report.append(msg)
        if from_to_goals:
            if num_froms_tos >= from_to_goals:
                msg = f"pass: {file} has {num_froms_tos} from and to "
                msg += "keyframes."
            else:
                msg = f"fail: {file} does not have enough from and to "
                msg += "keyframes to pass."
            report.append(msg)
    return report


def get_animation_properties_report(
    project_folder: str, num_goal: int, specific_properties=None
) -> list:
    """returns a list of pass/fail messages based on number and type of
    unique animation keyframe properties.

    You can specify just the number of unique properties or you can specify
    both the number as well as check for specific targetted properties. If you
    specify both, both must be met for a pass.

    NOTE: In the case of the transform properties, you can just specify
    transform, or you can include the type of transform in the form of
    transform- + the transform value (eg. transform-rotate(),
    transform-translate(), transfrom-skew(), etc.)

    Since animation_values might have multiple entries for the same file,
    we need to track a per file record to see if it meets or not.

    Args:
        animation_values: a list of filenames with keyframe and property
            data.
        num_goal: the minimum number of percentage keyframes we would want
            to see.
        specific_properties: a list or tuple of properties required to be
            present.

    Returns:
        results: a list of messages (one for each file in the project) with
            a pass or fail with number present of each type.
    """
    report = []
    animation_report = get_animation_report(project_folder)
    for item in animation_report:
        filename = utils.get_first_dict_key(item)
        properties_targetted = item[filename].get("properties")
        num_properties = len(properties_targetted)
        num_remaining = num_goal - num_properties
        if num_remaining > 0:
            msg = f"fail: {filename} did not target enough properties; should"
            msg += f"target {num_remaining} properties more."
            report.append(msg)
        else:
            if specific_properties:
                # make sure it's a list
                msg = get_targetted_properties_msg(
                    specific_properties, properties_targetted, filename
                )
                report.append(msg)
            else:
                # Now lets check for num of unique properties
                msg = get_num_properties_msg(
                    num_goal, properties_targetted, filename
                )
                report.append(msg)

        # now is the time to restart our list of properties
        properties_targetted = set()
    return report


def get_num_properties_msg(
    num_goal: int,
    properties_targetted: Union[list, tuple, set],
    current_file: str,
) -> str:
    """Returns a pass/fail message based on whether a file targets the min
    number of properties found.

    Args:
        num_goal: the number of unique properties that should be targetted"""
    num_unique_props = len(properties_targetted)
    if num_unique_props >= num_goal:
        msg = f"pass: {current_file}'s animations targetted the minimum "
        msg += "required number of properties."
    else:
        off_by = num_goal - num_unique_props
        msg = f"fail: {current_file}'s animations did not target the "
        msg += f"{num_goal} required number of properties (missing "
        msg += f"{off_by})"
    return msg


def get_targetted_properties_msg(
    properties: Union[list, tuple],
    properties_targetted: Union[list, tuple],
    current_file: str,
) -> str:
    """returns whether the file addresses all targetted keyframe properties or
    not.

    Receives the keyframe properties found in a file's styles and returns a
    message that states whether the file has targetted all required properties
    in the form of "pass" or "fail".

    Args:
        properties: a list or tuple of the keyframe properties targetted in a
            file's stylesheets or not.
        properties_targetted: a list or tuple of the properties that the file
            should contain.
        current_file: the name of the HTML document we are checking.

    Returns:
        msg: a string that begins with 'pass:' or 'fail:', and details on what
            was missing if a fail."""
    properties = list(properties)
    for property in properties_targetted:
        if property in properties:
            properties.remove(property)
    if properties:
        # we failed to include all required properties
        msg = f"fail: {current_file}'s animations did not target all "
        msg += f"required properties (missing {properties})"
    else:
        # Success on the required properties
        msg = f"pass: {current_file}'s animations targetted all "
        msg += "required properties"
    return msg


if __name__ == "__main__":
    project_folder = "tests/test_files/cascade_complexities"
    report = get_animation_report(project_folder)
