from typing import Optional


class BpmnError(Exception):
    """Base exception class for BPMN processing errors."""

    pass


class BpmnFileError(BpmnError, FileNotFoundError):

    @staticmethod
    def not_found(file_path: str) -> "BpmnFileError":
        return BpmnFileError(f"BPMN file not found: {file_path}")

    @staticmethod
    def not_readable(
        file_path: str, reason: Optional[str] = None
    ) -> "BpmnFileError":
        msg = f"BPMN file cannot be read: {file_path}"
        if reason:
            msg += f" - {reason}"
        return BpmnFileError(msg)

    @staticmethod
    def not_a_file(file_path: str) -> "BpmnFileError":
        return BpmnFileError(f"Path is not a file: {file_path}")


class BpmnParseError(BpmnError):

    @staticmethod
    def invalid_xml(
        file_path: str, reason: Optional[str] = None
    ) -> "BpmnParseError":
        msg = f"Invalid XML syntax in BPMN file: {file_path}"
        if reason:
            msg += f" - {reason}"
        return BpmnParseError(msg)


class BpmnRenderError(BpmnError):

    @staticmethod
    def render_failed(
        output_path: str, reason: Optional[str] = None
    ) -> "BpmnRenderError":
        msg = f"Failed to render diagram to: {output_path}"
        if reason:
            msg += f" - {reason}"
        return BpmnRenderError(msg)

    @staticmethod
    def output_dir_error(
        dir_path: str, reason: Optional[str] = None
    ) -> "BpmnRenderError":
        msg = f"Cannot create output directory: {dir_path}"
        if reason:
            msg += f" - {reason}"
        return BpmnRenderError(msg)
