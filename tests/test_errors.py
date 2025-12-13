import pytest

from bpmn_print.errors import (
    BpmnError,
    BpmnFileError,
    BpmnParseError,
    BpmnRenderError,
)


class TestBpmnError:
    """Tests for BpmnError base exception class."""

    def test_is_exception(self):
        """Test that BpmnError is an Exception."""
        assert issubclass(BpmnError, Exception)

    def test_can_be_raised(self):
        """Test that BpmnError can be raised."""
        with pytest.raises(BpmnError):
            raise BpmnError("Test error")

    def test_error_message(self):
        """Test that BpmnError preserves error message."""
        error = BpmnError("Custom message")
        assert str(error) == "Custom message"

    def test_can_be_caught_as_exception(self):
        """Test that BpmnError can be caught as Exception."""
        try:
            raise BpmnError("Test")
        except Exception as e:
            assert isinstance(e, BpmnError)

    def test_empty_message(self):
        """Test BpmnError with empty message."""
        error = BpmnError("")
        assert str(error) == ""


class TestBpmnFileError:
    """Tests for BpmnFileError exception class."""

    def test_inherits_from_bpmn_error(self):
        """Test that BpmnFileError inherits from BpmnError."""
        assert issubclass(BpmnFileError, BpmnError)

    def test_inherits_from_file_not_found_error(self):
        """Test that BpmnFileError inherits from FileNotFoundError."""
        assert issubclass(BpmnFileError, FileNotFoundError)

    def test_not_found_creates_error(self):
        """Test not_found factory method creates BpmnFileError."""
        file_path = "/path/to/file.bpmn"
        error = BpmnFileError.not_found(file_path)

        assert isinstance(error, BpmnFileError)

    def test_not_found_message_format(self):
        """Test not_found error message format."""
        file_path = "/path/to/file.bpmn"
        error = BpmnFileError.not_found(file_path)

        assert "BPMN file not found" in str(error)
        assert file_path in str(error)

    def test_not_found_with_relative_path(self):
        """Test not_found with relative path."""
        file_path = "relative/path/file.bpmn"
        error = BpmnFileError.not_found(file_path)

        assert file_path in str(error)

    def test_not_found_can_be_raised(self):
        """Test that not_found error can be raised."""
        with pytest.raises(BpmnFileError):
            raise BpmnFileError.not_found("test.bpmn")

    def test_not_readable_creates_error(self):
        """Test not_readable factory method creates BpmnFileError."""
        file_path = "/path/to/file.bpmn"
        error = BpmnFileError.not_readable(file_path)

        assert isinstance(error, BpmnFileError)

    def test_not_readable_message_format(self):
        """Test not_readable error message format."""
        file_path = "/path/to/file.bpmn"
        error = BpmnFileError.not_readable(file_path)

        assert "BPMN file cannot be read" in str(error)
        assert file_path in str(error)

    def test_not_readable_with_reason(self):
        """Test not_readable with reason provided."""
        file_path = "/path/to/file.bpmn"
        reason = "Permission denied"
        error = BpmnFileError.not_readable(file_path, reason)

        assert file_path in str(error)
        assert reason in str(error)
        assert " - " in str(error)

    def test_not_readable_without_reason(self):
        """Test not_readable without reason."""
        file_path = "/path/to/file.bpmn"
        error = BpmnFileError.not_readable(file_path, None)

        assert file_path in str(error)
        assert " - " not in str(error)

    def test_not_readable_with_empty_reason(self):
        """Test not_readable with empty string reason."""
        file_path = "/path/to/file.bpmn"
        error = BpmnFileError.not_readable(file_path, "")

        # Empty string is falsy, so no reason should be appended
        assert " - " not in str(error)

    def test_not_a_file_creates_error(self):
        """Test not_a_file factory method creates BpmnFileError."""
        file_path = "/path/to/directory"
        error = BpmnFileError.not_a_file(file_path)

        assert isinstance(error, BpmnFileError)

    def test_not_a_file_message_format(self):
        """Test not_a_file error message format."""
        file_path = "/path/to/directory"
        error = BpmnFileError.not_a_file(file_path)

        assert "Path is not a file" in str(error)
        assert file_path in str(error)

    def test_not_a_file_can_be_raised(self):
        """Test that not_a_file error can be raised."""
        with pytest.raises(BpmnFileError):
            raise BpmnFileError.not_a_file("/some/directory")

    def test_can_be_caught_as_file_not_found_error(self):
        """Test that BpmnFileError can be caught as FileNotFoundError."""
        try:
            raise BpmnFileError.not_found("test.bpmn")
        except FileNotFoundError as e:
            assert isinstance(e, BpmnFileError)


class TestBpmnParseError:
    """Tests for BpmnParseError exception class."""

    def test_inherits_from_bpmn_error(self):
        """Test that BpmnParseError inherits from BpmnError."""
        assert issubclass(BpmnParseError, BpmnError)

    def test_does_not_inherit_from_file_not_found_error(self):
        """Test that BpmnParseError doesn't inherit FileNotFoundError."""
        assert not issubclass(BpmnParseError, FileNotFoundError)

    def test_invalid_xml_creates_error(self):
        """Test invalid_xml factory method creates BpmnParseError."""
        file_path = "/path/to/file.bpmn"
        error = BpmnParseError.invalid_xml(file_path)

        assert isinstance(error, BpmnParseError)

    def test_invalid_xml_message_format(self):
        """Test invalid_xml error message format."""
        file_path = "/path/to/file.bpmn"
        error = BpmnParseError.invalid_xml(file_path)

        assert "Invalid XML syntax in BPMN file" in str(error)
        assert file_path in str(error)

    def test_invalid_xml_with_reason(self):
        """Test invalid_xml with reason provided."""
        file_path = "/path/to/file.bpmn"
        reason = "Unclosed tag at line 42"
        error = BpmnParseError.invalid_xml(file_path, reason)

        assert file_path in str(error)
        assert reason in str(error)
        assert " - " in str(error)

    def test_invalid_xml_without_reason(self):
        """Test invalid_xml without reason."""
        file_path = "/path/to/file.bpmn"
        error = BpmnParseError.invalid_xml(file_path, None)

        assert file_path in str(error)
        assert " - " not in str(error)

    def test_invalid_xml_with_empty_reason(self):
        """Test invalid_xml with empty string reason."""
        file_path = "/path/to/file.bpmn"
        error = BpmnParseError.invalid_xml(file_path, "")

        # Empty string is falsy, so no reason should be appended
        assert " - " not in str(error)

    def test_invalid_xml_can_be_raised(self):
        """Test that invalid_xml error can be raised."""
        with pytest.raises(BpmnParseError):
            raise BpmnParseError.invalid_xml("test.bpmn")

    def test_can_be_caught_as_bpmn_error(self):
        """Test that BpmnParseError can be caught as BpmnError."""
        try:
            raise BpmnParseError.invalid_xml("test.bpmn")
        except BpmnError as e:
            assert isinstance(e, BpmnParseError)


class TestBpmnRenderError:
    """Tests for BpmnRenderError exception class."""

    def test_inherits_from_bpmn_error(self):
        """Test that BpmnRenderError inherits from BpmnError."""
        assert issubclass(BpmnRenderError, BpmnError)

    def test_render_failed_creates_error(self):
        """Test render_failed factory method creates BpmnRenderError."""
        output_path = "/path/to/output.png"
        error = BpmnRenderError.render_failed(output_path)

        assert isinstance(error, BpmnRenderError)

    def test_render_failed_message_format(self):
        """Test render_failed error message format."""
        output_path = "/path/to/output.png"
        error = BpmnRenderError.render_failed(output_path)

        assert "Failed to render diagram to" in str(error)
        assert output_path in str(error)

    def test_render_failed_with_reason(self):
        """Test render_failed with reason provided."""
        output_path = "/path/to/output.png"
        reason = "Graphviz not installed"
        error = BpmnRenderError.render_failed(output_path, reason)

        assert output_path in str(error)
        assert reason in str(error)
        assert " - " in str(error)

    def test_render_failed_without_reason(self):
        """Test render_failed without reason."""
        output_path = "/path/to/output.png"
        error = BpmnRenderError.render_failed(output_path, None)

        assert output_path in str(error)
        assert " - " not in str(error)

    def test_render_failed_with_empty_reason(self):
        """Test render_failed with empty string reason."""
        output_path = "/path/to/output.png"
        error = BpmnRenderError.render_failed(output_path, "")

        # Empty string is falsy, so no reason should be appended
        assert " - " not in str(error)

    def test_render_failed_can_be_raised(self):
        """Test that render_failed error can be raised."""
        with pytest.raises(BpmnRenderError):
            raise BpmnRenderError.render_failed("output.png")

    def test_output_dir_error_creates_error(self):
        """Test output_dir_error factory method creates BpmnRenderError."""
        dir_path = "/path/to/output"
        error = BpmnRenderError.output_dir_error(dir_path)

        assert isinstance(error, BpmnRenderError)

    def test_output_dir_error_message_format(self):
        """Test output_dir_error error message format."""
        dir_path = "/path/to/output"
        error = BpmnRenderError.output_dir_error(dir_path)

        assert "Cannot create output directory" in str(error)
        assert dir_path in str(error)

    def test_output_dir_error_with_reason(self):
        """Test output_dir_error with reason provided."""
        dir_path = "/path/to/output"
        reason = "Permission denied"
        error = BpmnRenderError.output_dir_error(dir_path, reason)

        assert dir_path in str(error)
        assert reason in str(error)
        assert " - " in str(error)

    def test_output_dir_error_without_reason(self):
        """Test output_dir_error without reason."""
        dir_path = "/path/to/output"
        error = BpmnRenderError.output_dir_error(dir_path, None)

        assert dir_path in str(error)
        assert " - " not in str(error)

    def test_output_dir_error_with_empty_reason(self):
        """Test output_dir_error with empty string reason."""
        dir_path = "/path/to/output"
        error = BpmnRenderError.output_dir_error(dir_path, "")

        # Empty string is falsy, so no reason should be appended
        assert " - " not in str(error)

    def test_output_dir_error_can_be_raised(self):
        """Test that output_dir_error can be raised."""
        with pytest.raises(BpmnRenderError):
            raise BpmnRenderError.output_dir_error("/output")


class TestErrorHierarchy:
    """Tests for exception hierarchy and inheritance."""

    def test_all_errors_inherit_from_bpmn_error(self):
        """Test that all custom errors inherit from BpmnError."""
        assert issubclass(BpmnFileError, BpmnError)
        assert issubclass(BpmnParseError, BpmnError)
        assert issubclass(BpmnRenderError, BpmnError)

    def test_can_catch_all_with_bpmn_error(self):
        """Test that BpmnError can catch all BPMN exceptions."""
        errors = [
            BpmnFileError.not_found("test.bpmn"),
            BpmnParseError.invalid_xml("test.bpmn"),
            BpmnRenderError.render_failed("output.png"),
        ]

        for error in errors:
            try:
                raise error
            except BpmnError as e:
                assert isinstance(e, BpmnError)


class TestErrorMessageEdgeCases:
    """Tests for edge cases in error messages."""

    def test_special_characters_in_paths(self):
        """Test paths with special characters."""
        file_path = "/path/with spaces/file (1).bpmn"
        error = BpmnFileError.not_found(file_path)

        assert file_path in str(error)

    def test_unicode_in_paths(self):
        """Test paths with unicode characters."""
        file_path = "/路径/文件.bpmn"
        error = BpmnFileError.not_found(file_path)

        assert file_path in str(error)

    def test_very_long_path(self):
        """Test with very long file path."""
        file_path = "/a" * 100 + "/file.bpmn"
        error = BpmnFileError.not_found(file_path)

        assert file_path in str(error)

    def test_reason_with_special_characters(self):
        """Test reason with special characters."""
        reason = "Error: <tag> not closed properly"
        error = BpmnParseError.invalid_xml("test.bpmn", reason)

        assert reason in str(error)

    def test_multiline_reason(self):
        """Test reason with newlines."""
        reason = "Line 1\nLine 2\nLine 3"
        error = BpmnRenderError.render_failed("output.png", reason)

        assert reason in str(error)

    def test_empty_path(self):
        """Test with empty path string."""
        error = BpmnFileError.not_found("")
        assert "BPMN file not found" in str(error)

    def test_none_becomes_string_none(self):
        """Test that None in reason is handled correctly."""
        error = BpmnFileError.not_readable("test.bpmn", None)
        assert "None" not in str(error)
