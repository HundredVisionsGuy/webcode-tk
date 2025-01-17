import pytest

from webcode_tk import animation_tools as animations

project_folder = "tests/test_files/cascade_complexities"


@pytest.fixture
def animation_report():
    report = animations.get_animation_report(project_folder)
    return report


@pytest.fixture
def keyframe_report(animation_report):
    report = animations.get_keyframe_results(animation_report)
    return report


def test_get_animation_report_for_values_targetted(animation_report):
    assert len(animation_report) == 4


def test_keyframe_report_for_something(keyframe_report):
    meets = True
    for item in keyframe_report:
        filename, keyframes, values = item
        if filename == "animations.html":
            meets = meets and keyframes == 6 and values == 2
        if filename == "keyframe-animation.html":
            meets = meets and keyframes == 5 and values == 2
    assert meets
