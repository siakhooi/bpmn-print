"""Standardized error handling and error messages for BPMN processing.

This module provides consistent error types and message templates to ensure
uniform error handling across the application.
"""

from typing import Optional


class BpmnError(Exception):
    """Base exception class for BPMN processing errors."""
    pass


class BpmnFileError(BpmnError, FileNotFoundError):
    """Raised when a BPMN file cannot be found or accessed."""

    @staticmethod
    def not_found(file_path: str) -> 'BpmnFileError':
        """Create error for file not found."""
        return BpmnFileError(f"BPMN file not found: {file_path}")

    @staticmethod
    def not_readable(
        file_path: str, reason: Optional[str] = None
    ) -> 'BpmnFileError':
        """Create error for file not readable."""
        msg = f"BPMN file cannot be read: {file_path}"
        if reason:
            msg += f" - {reason}"
        return BpmnFileError(msg)

    @staticmethod
    def not_a_file(file_path: str) -> 'BpmnFileError':
        """Create error for path that is not a file."""
        return BpmnFileError(f"Path is not a file: {file_path}")


class BpmnParseError(BpmnError):
    """Raised when a BPMN XML file cannot be parsed."""

    @staticmethod
    def invalid_xml(
        file_path: str, reason: Optional[str] = None
    ) -> 'BpmnParseError':
        """Create error for invalid XML syntax."""
        msg = f"Invalid XML syntax in BPMN file: {file_path}"
        if reason:
            msg += f" - {reason}"
        return BpmnParseError(msg)


class BpmnRenderError(BpmnError):
    """Raised when diagram rendering fails."""

    @staticmethod
    def render_failed(
        output_path: str, reason: Optional[str] = None
    ) -> 'BpmnRenderError':
        """Create error for rendering failure."""
        msg = f"Failed to render diagram to: {output_path}"
        if reason:
            msg += f" - {reason}"
        return BpmnRenderError(msg)

    @staticmethod
    def output_dir_error(
        dir_path: str, reason: Optional[str] = None
    ) -> 'BpmnRenderError':
        """Create error for output directory creation failure."""
        msg = f"Cannot create output directory: {dir_path}"
        if reason:
            msg += f" - {reason}"
        return BpmnRenderError(msg)
