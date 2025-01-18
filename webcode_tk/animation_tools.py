"""
A group of functions that work with css_tools and cascade_tools to provide
reports on CSS animations.
"""
from file_clerk import clerk

from webcode_tk import css_tools


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
                    "keyframes": [
                        keyframe,
                    ],
                    "pct_keyframes": [],
                    "from_keyframes": [],
                    "to_keyframes": [],
                    "properties": set(),
                }
            }
            report.append(animation_dict)
        current_dict = animation_dict.get(filename)
        for rule in rulesets:
            declarations = rule.declaration_block.declarations
            for declaration in declarations:
                if declaration.property == "transform":
                    value_type = declaration.value
                    value_split = value_type.split("(")
                    transform_value = value_split[0] + "()"
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


def get_keyframe_results(report: list) -> dict:
    keyframe_results = {}
    for animation in report:
        filename = animation.get("file")
        if filename not in keyframe_results:
            keyframe_results[filename] = {}
            keyframe_results[filename]["froms_tos"] = 0
            keyframe_results[filename]["pct_keyframes"] = 0
        keyframes = animation.get("keyframes")
        for keyframe_data in keyframes:
            keyframe_type = keyframe_data[0]
            num_keyframes = len(keyframe_data[1])
            if keyframe_type == "percentage":
                keyframe_results[filename]["pct_keyframes"] += num_keyframes
            elif keyframe_type in ("from", "to"):
                keyframe_results[filename]["froms_tos"] += num_keyframes
    results = []
    for file, frames in keyframe_results.items():
        results.append(
            (file, frames.get("pct_keyframes"), frames.get("froms_tos"))
        )
    return results


def get_keyframe_report(
    keyframe_results: list, pct_goal: int, overall_goal: int
) -> list:
    """returns a list of pass/fail messages (1 for each file)

    Args:
        keyframe_results: a list of filenames with number of percentage
            keyframes and from and to keyframes.
        pct_goal: the minimum number of percentage keyframes we would want
            to see.
        overall_goal: the total number of keyframes in case there are not
            the minimum number of percentage keyframes.

    Returns:
        results: a list of messages (one for each file in the project) with
            a pass or fail with number present of each type.
    """
    results = []
    for item in keyframe_results:
        file, pct_keyframes, from_to_keyframes = item
        msg = ""

        # first check the percentage goal
        if pct_keyframes > pct_goal:
            msg = f"pass: {file} has {pct_keyframes} percentage keyframes."
        else:
            # if that fails, check overall
            num_overall = pct_keyframes + from_to_keyframes
            if num_overall >= overall_goal:
                msg = f"pass: {file} has {num_overall} keyframes (enough "
                msg += "overall to meet)."
            else:
                msg = f"fail: {file} does not have enough keyframes to pass."
        results.append(msg)
    return results


def get_animation_properties_report(
    animation_values: list, num_goal: int, specific_properties=None
):
    """returns a list of pass/fail messages (1 for each file)

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
    results = []
    properties_targetted = set()
    current_file = animation_values[0].get("file")
    for item in animation_values:
        filename = item.get("file")
        if filename != current_file:
            # we are on to a new file, it's time to create a message
            if specific_properties:
                # make sure it's a list
                msg = get_targetted_properties_msg(
                    specific_properties, properties_targetted, current_file
                )
                results.append(msg)
            else:
                # Now lets check for num of unique properties
                msg = get_num_properties_msg(
                    num_goal, properties_targetted, current_file
                )
                results.append(msg)

            # now is the time to restart our list of properties
            properties_targetted = set()
            current_file = filename

        # will need to change the key on the animations_values list
        properties = item.get("values_targetted")
        for property in properties:
            # add only unique properties
            properties_targetted.add(property)

    # process the current file (now that we're done looping)
    # check to see if there are any required properties
    if specific_properties:
        # make sure it's a list
        msg = get_targetted_properties_msg(
            specific_properties, properties_targetted, current_file
        )
        results.append(msg)
    else:
        # Now lets check for num of unique properties
        msg = get_num_properties_msg(
            num_goal, properties_targetted, current_file
        )
        results.append(msg)
    return results


def get_num_properties_msg(num_goal, properties_targetted, current_file):
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
    properties, properties_targetted, current_file
):
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
