import pytest

from webcode_tk import animation_tools as animations

project_folder = "tests/test_files/cascade_complexities"


@pytest.fixture
def animation_report():
    report = animations.get_animation_report(project_folder)
    return report


@pytest.fixture
def keyframe_data(animation_report):
    report = animations.get_keyframe_data(animation_report)
    return report


# Keyframe report tests
# animations.html has 6 % keyframes in all
# keyframe-animations.html has 3 % keyframes, 1 from, and 1 to


def test_keyframe_report_for_overall_goal_of_6():
    report = animations.get_keyframe_report(project_folder, 6)
    animations_passes = False
    for file in report:
        if "animations.html" in file:
            if "pass:" in file:
                animations_passes = True
    assert animations_passes


def test_keyframe_report_for_failed_pct():
    report = animations.get_keyframe_report(project_folder, 5, 5)
    keyframes_fail = False
    for file in report:
        if "keyframe-animation.html" in file:
            if "does not have enough percentage" in file:
                keyframes_fail = True
    assert keyframes_fail


def test_keyframe_report_for_two_from_tos_pass():
    report = animations.get_keyframe_report(project_folder, 2, from_to_goals=2)
    keyframes_passes = False
    for file in report:
        if "keyframe-animation.html" in file:
            if "pass:" in file and "from and to" in file:
                keyframes_passes = True
    assert keyframes_passes


def test_get_animation_report_for_values_targetted(animation_report):
    assert len(animation_report) == 3


def test_get_animation_report_for_number_properties(animation_report):
    # passes until proven failed
    passes = True
    for file in animation_report:
        # animations.html targets width and background-color
        if "animations.html" in file.keys():
            properties = file["animations.html"].get("properties")
            passes = passes and "background-color" in properties
            passes = passes and "width" in properties
        elif "keyframe-animation.html" in file.keys():
            # keyframe-animations.html targets transform-translate,
            # transform-rotate, and opacity
            properties = file["keyframe-animation.html"].get("properties")
            passes = passes and "transform-rotate()" in properties
            passes = passes and "opacity" in properties
        else:
            # ufo.html has so 4 animations, 10 % keyframes, one from and a to
            animations = file["ufo.html"].get("keyframes")
            num_animations = len(animations)
            pct_keyframes = file["ufo.html"].get("pct_keyframes")
            num_pct = len(pct_keyframes)
            passes = passes and num_pct == 10 and num_animations == 4
    assert passes


# keyframe properties report
# keyframe-animation.html has opacity,
# transform-rotate(), and transform-translate()


def test_get_animation_properties_report_for_keyframe_animation_meets():
    properties_report = animations.get_animation_properties_report(
        project_folder, 3, ("transform-rotate()", "transform-translate()")
    )
    keyframe_animations_passes = False
    for file in properties_report:
        if "keyframe-animation.html" in file:
            if "pass:" in file:
                keyframe_animations_passes = True
    assert keyframe_animations_passes


def test_get_animation_properties_report_for_keyframe_fails_missing_prop():
    properties_report = animations.get_animation_properties_report(
        project_folder, 3, ("transform-skew()", "transform-translate()")
    )
    keyframe_animations_fails = False
    for file in properties_report:
        if "keyframe-animation.html" in file:
            if "fail:" in file:
                keyframe_animations_fails = True
    assert keyframe_animations_fails


def test_get_animation_properties_report_for_only_number_keyframes_fail():
    properties_report = animations.get_animation_properties_report(
        project_folder, 5
    )
    keyframe_animations_fails = False
    for file in properties_report:
        if "keyframe-animation.html" in file:
            if "fail:" in file:
                keyframe_animations_fails = True
    assert keyframe_animations_fails


def test_get_animation_properties_report_for_only_number_keyframes_pass():
    properties_report = animations.get_animation_properties_report(
        project_folder, 3
    )
    keyframe_animations_passes = False
    for file in properties_report:
        if "keyframe-animation.html" in file:
            if "pass:" in file:
                keyframe_animations_passes = True
    assert keyframe_animations_passes


# animations.html has width and
# background-color


def test_animation_properties_report_for_animations_fail_with_enough_props():
    properties_report = animations.get_animation_properties_report(
        project_folder, 3, ("width", "background-color")
    )
    animations_failed = False
    for file in properties_report:
        if "animations.html" in file:
            animations_failed = "fail:" in file
    assert animations_failed


def test_animation_properties_report_for_animations_pass_with_enough_props():
    properties_report = animations.get_animation_properties_report(
        project_folder, 2, ("width", "background-color")
    )
    animations_passed = False
    for file in properties_report:
        if "animations.html" in file:
            animations_passed = "pass:" in file
    assert animations_passed
