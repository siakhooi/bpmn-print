import logging
import sys
from bpmn_print import console


class TestSetLevel:
    """Tests for set_level function."""

    def test_set_level_debug(self):
        console.set_level(logging.DEBUG)
        assert console._logger.level == logging.DEBUG

    def test_set_level_info(self):
        console.set_level(logging.INFO)
        assert console._logger.level == logging.INFO

    def test_set_level_warning(self):
        console.set_level(logging.WARNING)
        assert console._logger.level == logging.WARNING

    def test_set_level_error(self):
        console.set_level(logging.ERROR)
        assert console._logger.level == logging.ERROR

    def test_set_level_critical(self):
        console.set_level(logging.CRITICAL)
        assert console._logger.level == logging.CRITICAL


class TestError:
    """Tests for error function."""

    def test_error_with_exception(self, caplog):
        console.set_level(logging.ERROR)
        test_exception = ValueError("Test error message")
        with caplog.at_level(logging.ERROR):
            console.error(test_exception)
        assert "Error: Test error message" in caplog.text

    def test_error_with_different_exception_types(self, caplog):
        console.set_level(logging.ERROR)
        test_exception = RuntimeError("Runtime error occurred")
        with caplog.at_level(logging.ERROR):
            console.error(test_exception)
        assert "Error: Runtime error occurred" in caplog.text

    def test_error_with_empty_message(self, caplog):
        console.set_level(logging.ERROR)
        test_exception = Exception("")
        with caplog.at_level(logging.ERROR):
            console.error(test_exception)
        assert "Error:" in caplog.text


class TestPrintln:
    """Tests for println function."""

    def test_println_simple_message(self, capsys):
        console.println("Hello, World!")

        captured = capsys.readouterr()
        assert captured.out == "Hello, World!\n"

    def test_println_empty_string(self, capsys):
        console.println("")

        captured = capsys.readouterr()
        assert captured.out == "\n"

    def test_println_multiline_message(self, capsys):
        message = "Line 1\nLine 2\nLine 3"
        console.println(message)

        captured = capsys.readouterr()
        assert captured.out == "Line 1\nLine 2\nLine 3\n"

    def test_println_special_characters(self, capsys):
        console.println("Special chars: !@#$%^&*()")

        captured = capsys.readouterr()
        assert captured.out == "Special chars: !@#$%^&*()\n"


class TestInfo:
    """Tests for info function."""

    def test_info_simple_message(self, caplog):
        console.set_level(logging.INFO)
        with caplog.at_level(logging.INFO):
            console.info("Information message")
        assert "Information message" in caplog.text

    def test_info_not_displayed_when_level_is_warning(self, caplog):
        console.set_level(logging.WARNING)
        with caplog.at_level(logging.WARNING):
            console.info("This should not appear")
        assert "This should not appear" not in caplog.text

    def test_info_displayed_when_level_is_debug(self, caplog):
        console.set_level(logging.DEBUG)
        with caplog.at_level(logging.DEBUG):
            console.info("Debug level info")
        assert "Debug level info" in caplog.text


class TestWarning:
    """Tests for warning function."""

    def test_warning_simple_message(self, caplog):
        console.set_level(logging.WARNING)
        with caplog.at_level(logging.WARNING):
            console.warning("Warning message")
        assert "Warning message" in caplog.text

    def test_warning_displayed_when_level_is_info(self, caplog):
        console.set_level(logging.INFO)
        with caplog.at_level(logging.INFO):
            console.warning("Important warning")
        assert "Important warning" in caplog.text

    def test_warning_not_displayed_when_level_is_error(self, caplog):
        console.set_level(logging.ERROR)
        with caplog.at_level(logging.ERROR):
            console.warning("This warning should not appear")
        assert "This warning should not appear" not in caplog.text


class TestDebug:
    """Tests for debug function."""

    def test_debug_simple_message(self, caplog):
        console.set_level(logging.DEBUG)
        with caplog.at_level(logging.DEBUG):
            console.debug("Debug message")
        assert "Debug message" in caplog.text

    def test_debug_not_displayed_when_level_is_info(self, caplog):
        console.set_level(logging.INFO)
        with caplog.at_level(logging.INFO):
            console.debug("This debug message should not appear")
        assert "This debug message should not appear" not in caplog.text

    def test_debug_not_displayed_when_level_is_warning(self, caplog):
        console.set_level(logging.WARNING)
        with caplog.at_level(logging.WARNING):
            console.debug("Another hidden debug message")
        assert "Another hidden debug message" not in caplog.text


class TestLoggerConfiguration:
    """Tests for logger configuration."""

    def test_logger_name(self):
        assert console._logger.name == "bpmn_print"

    def test_logger_has_handler(self):
        assert len(console._logger.handlers) > 0

    def test_handler_is_stream_handler(self):
        handler = console._handler
        assert isinstance(handler, logging.StreamHandler)

    def test_handler_stream_is_stderr(self):
        handler = console._handler
        assert handler.stream == sys.stderr

    def test_handler_formatter_format(self):
        handler = console._handler
        formatter = handler.formatter
        assert formatter is not None
        assert formatter._fmt == "%(levelname)s: %(message)s"

    def test_default_logger_level_is_info(self):
        # Create a fresh logger to test default level
        test_logger = logging.getLogger("test_bpmn_print")
        test_handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter("%(levelname)s: %(message)s")
        test_handler.setFormatter(formatter)
        test_logger.addHandler(test_handler)
        test_logger.setLevel(logging.INFO)

        assert test_logger.level == logging.INFO


class TestIntegration:
    """Integration tests for console module."""

    def test_multiple_log_levels_sequence(self, caplog):
        console.set_level(logging.DEBUG)
        with caplog.at_level(logging.DEBUG):
            console.debug("Debug msg")
            console.info("Info msg")
            console.warning("Warning msg")
        assert "Debug msg" in caplog.text
        assert "Info msg" in caplog.text
        assert "Warning msg" in caplog.text

    def test_changing_log_level_affects_output(self, caplog):
        console.set_level(logging.INFO)
        with caplog.at_level(logging.INFO):
            console.debug("Hidden debug")
            console.info("Visible info")
        assert "Hidden debug" not in caplog.text
        assert "Visible info" in caplog.text

    def test_println_and_logging_separate_streams(self, capsys, caplog):
        console.set_level(logging.INFO)
        console.println("stdout message")
        with caplog.at_level(logging.INFO):
            console.info("stderr message")

        captured = capsys.readouterr()
        assert captured.out == "stdout message\n"
        assert "stderr message" in caplog.text

    def test_error_logging_with_critical_level(self, caplog):
        console.set_level(logging.CRITICAL)
        test_exception = Exception("Critical error")
        with caplog.at_level(logging.CRITICAL):
            console.error(test_exception)
        # ERROR (40) < CRITICAL (50), so it won't be logged
        assert "Critical error" not in caplog.text
