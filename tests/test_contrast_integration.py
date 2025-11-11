# tests/test_contrast_integration.py
"""Integration tests using actual HTML test projects"""
from webcode_tk.contrast_tools import analyze_contrast


class TestContrastIntegration:
    """Integration tests with real HTML projects"""

    def test_large_project_analysis(self):
        """Test analysis of complete project with CSS"""
        project_path = "tests/test_files/large_project/"
        results = analyze_contrast(project_path)

        assert len(results) > 0
        # Verify structure matches your actual output
        for result in results:
            if result.get("contrast_analysis") != "warning":
                assert "filename" in result
                assert "element_tag" in result
                assert "text_color" in result
                assert "background_color" in result
                assert "text_color_source" in result  # New field
                assert "background_color_source" in result  # New field
                assert "contrast_ratio" in result
                assert "wcag_aa_pass" in result
                assert "wcag_aaa_pass" in result

    def test_no_css_document_generates_warning(self):
        """Test document with no CSS sources generates warning"""
        project_path = "tests/test_files/no_css_test/"
        results = analyze_contrast(project_path)
        assert len(results) > 0
        assert results[0]["text_content"] == "No CSS Test Files"

        # Check that non-warning results have proper structure
        non_warnings = [
            r for r in results if r.get("contrast_analysis") != "warning"
        ]
        if non_warnings:
            result = non_warnings[0]

            # color inherits by default
            assert (
                result["text_color_source"]["source_type"] == "browser_default"
            )

            # background color is invisible and doesn't inherit by default
            assert (
                result["background_color_source"]["source_type"]
                == "browser_default"
            )
