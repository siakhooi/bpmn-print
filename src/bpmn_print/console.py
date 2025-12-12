"""Console output utilities with proper logging support.

This module provides a structured approach to console output using Python's
logging module. It supports different log levels, can be configured for
production use, and is easier to test and maintain than raw print statements.
"""

import logging
import sys

# Configure the logger for console output
_logger = logging.getLogger("bpmn_print")
_handler = logging.StreamHandler(sys.stderr)
_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
_logger.addHandler(_handler)
_logger.setLevel(logging.INFO)


def set_level(level: int) -> None:
    """Set the logging level for console output.

    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO, logging.ERROR)

    Example:
        >>> import logging
        >>> set_level(logging.DEBUG)  # Enable debug output
    """
    _logger.setLevel(level)


def error(e: Exception) -> None:
    """Log an error message to stderr.

    Args:
        e: Exception to log

    Example:
        >>> try:
        ...     risky_operation()
        ... except Exception as e:
        ...     error(e)
    """
    _logger.error("Error: %s", e)


def println(message: str) -> None:
    """Print an informational message to stdout.

    Args:
        message: Message to display

    Example:
        >>> println("Processing complete")
    """
    # Use print for info messages to stdout (not stderr)
    print(message)


def info(message: str) -> None:
    """Log an informational message.

    Args:
        message: Message to log

    Example:
        >>> info("Starting conversion process")
    """
    _logger.info(message)


def warning(message: str) -> None:
    """Log a warning message.

    Args:
        message: Warning message to log

    Example:
        >>> warning("File not found, skipping")
    """
    _logger.warning(message)


def debug(message: str) -> None:
    """Log a debug message (only visible when debug level is enabled).

    Args:
        message: Debug message to log

    Example:
        >>> set_level(logging.DEBUG)
        >>> debug("Processing file: example.bpmn")
    """
    _logger.debug(message)
