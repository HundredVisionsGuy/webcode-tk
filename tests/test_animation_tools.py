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


def test_get_animation_report_for_values_targetted(animation_report):
    assert len(animation_report) == 2


def test_get_animation_report_for_number_properties(animation_report):
    # passes until proven failed
    passes = True
    for file in animation_report:
        # animations.html targets width and background-color
        if "animations.html" in file.keys():
            properties = file["animations.html"].get("properties")
            passes = passes and "background-color" in properties
            passes = passes and "width" in properties
        else:
            # keyframe-animations.html targets transform-translate,
            # transform-rotate, and opacity
            properties = file["keyframe-animation.html"].get("properties")
            passes = passes and "transform-rotate()" in properties
            passes = passes and "opacity" in properties
    assert passes


def test_keyframe_report_for_num_keyframes_in_animations(keyframe_data):
    # passes until proven failed
    files = keyframe_data.keys()
    num_names = 0
    for file in files:
        if file == "animations.html":
            # Animations should have 2 keyframe names and 6 % keyframes
            data = keyframe_data.get(file)
            keyframe_names = data["keyframe_names"]
            num_names = len(keyframe_names)
    assert num_names == 2


def test_keyframe_report_for_num_pct_keyframes_in_animations(keyframe_data):
    # passes until proven failed
    files = keyframe_data.keys()
    pct_keyframes = 0
    for file in files:
        if file == "animations.html":
            # Animations should have 2 keyframe names and 6 % keyframes
            data = keyframe_data.get(file)
            pct_keyframes = data["pct_keyframes"]
    assert pct_keyframes == 6


def test_keyframe_report_for_num_from_to_keyframes(keyframe_data):
    # passes until proven failed
    files = keyframe_data.keys()
    froms_tos = 0
    for file in files:
        if file == "keyframe-animation.html":
            # Animations should have 2 keyframe names and 6 % keyframes
            data = keyframe_data.get(file)
            froms_tos = data["froms_tos"]
    assert froms_tos == 2
