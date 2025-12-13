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
        level: Logging level (logging.DEBUG, logging.INFO, logging.ERROR)
    """
    _logger.setLevel(level)


def error(e: Exception) -> None:
    _logger.error("Error: %s", e)


def println(message: str) -> None:
    print(message)


def info(message: str) -> None:
    _logger.info(message)


def warning(message: str) -> None:
    _logger.warning(message)


def debug(message: str) -> None:
    _logger.debug(message)
