from webcode_tk import animation_tools

project_folder = "tests/test_files/cascade_complexities"


def test_get_animation_report_for_values_targetted():
    report = animation_tools.get_animation_report(project_folder)

    # let's change this assertion when we get the chance
    assert len(report) == 4
