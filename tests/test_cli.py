from unittest.mock import patch

from bpmn_print.cli import run
from bpmn_print.errors import BpmnRenderError, BpmnFileError

import pytest


@pytest.mark.parametrize("option_help", ["-h", "--help"])
def test_run_help(monkeypatch, capsys, option_help):
    monkeypatch.setattr(
        "sys.argv",
        ["bpmn-print", option_help],
    )

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        run()
    assert pytest_wrapped_e.type is SystemExit
    assert pytest_wrapped_e.value.code == 0

    with open("tests/expected-output/cli-help.txt", "r") as f:
        expected_output = f.read()

    captured = capsys.readouterr()
    assert captured.out == expected_output


@pytest.mark.parametrize("option_version", ["-v", "--version"])
def test_run_show_version(monkeypatch, capsys, option_version):
    monkeypatch.setattr(
        "sys.argv",
        ["bpmn-print", option_version],
    )

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        run()
    assert pytest_wrapped_e.type is SystemExit
    assert pytest_wrapped_e.value.code == 0

    with open("tests/expected-output/cli-version.txt", "r") as f:
        expected_output = f.read()

    captured = capsys.readouterr()
    assert captured.out == expected_output


@pytest.mark.parametrize("options", [["-p"], ["-p", "-j"]])
def test_run_wrong_options(monkeypatch, capsys, options):
    monkeypatch.setattr(
        "sys.argv",
        ["bpmn-print", options],
    )

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        run()
    assert pytest_wrapped_e.type is SystemExit
    assert pytest_wrapped_e.value.code == 2

    with open("tests/expected-output/cli-wrong-options.txt", "r") as f:
        expected_output = f.read()

    captured = capsys.readouterr()
    assert captured.err == expected_output


@patch("bpmn_print.cli.pretty_print")
def test_run_with_valid_arguments(mock_pretty_print, monkeypatch):
    """Test run with valid input and output folders."""
    monkeypatch.setattr(
        "sys.argv",
        ["bpmn-print", "/input", "/output"],
    )

    run()

    mock_pretty_print.assert_called_once_with("/input", "/output", False, 2200)


@patch("bpmn_print.cli.pretty_print")
def test_run_with_keep_flag_short(mock_pretty_print, monkeypatch):
    """Test run with -k flag to keep PNG files."""
    monkeypatch.setattr(
        "sys.argv",
        ["bpmn-print", "-k", "/input", "/output"],
    )

    run()

    mock_pretty_print.assert_called_once_with("/input", "/output", True, 2200)


@patch("bpmn_print.cli.pretty_print")
def test_run_with_keep_flag_long(mock_pretty_print, monkeypatch):
    """Test run with --keep flag to keep PNG files."""
    monkeypatch.setattr(
        "sys.argv",
        ["bpmn-print", "--keep", "/input", "/output"],
    )

    run()

    mock_pretty_print.assert_called_once_with("/input", "/output", True, 2200)


@patch("bpmn_print.cli.pretty_print")
def test_run_with_threshold_flag_short(mock_pretty_print, monkeypatch):
    """Test run with -t flag for custom threshold."""
    monkeypatch.setattr(
        "sys.argv",
        ["bpmn-print", "-t", "3000", "/input", "/output"],
    )

    run()

    mock_pretty_print.assert_called_once_with("/input", "/output", False, 3000)


@patch("bpmn_print.cli.pretty_print")
def test_run_with_threshold_flag_long(mock_pretty_print, monkeypatch):
    """Test run with --diagram-landscape-threshold flag."""
    monkeypatch.setattr(
        "sys.argv",
        [
            "bpmn-print",
            "--diagram-landscape-threshold",
            "2500",
            "/input",
            "/output",
        ],
    )

    run()

    mock_pretty_print.assert_called_once_with("/input", "/output", False, 2500)


@patch("bpmn_print.cli.pretty_print")
def test_run_with_all_flags(mock_pretty_print, monkeypatch):
    """Test run with both keep and threshold flags."""
    monkeypatch.setattr(
        "sys.argv",
        ["bpmn-print", "-k", "-t", "1800", "/input", "/output"],
    )

    run()

    mock_pretty_print.assert_called_once_with("/input", "/output", True, 1800)


@patch("bpmn_print.cli.console")
@patch("bpmn_print.cli.pretty_print")
def test_run_handles_bpmn_error(mock_pretty_print, mock_console, monkeypatch):
    """Test that BpmnError is caught and exits with code 2."""
    monkeypatch.setattr(
        "sys.argv",
        ["bpmn-print", "/input", "/output"],
    )

    error = BpmnRenderError("Test error")
    mock_pretty_print.side_effect = error

    with pytest.raises(SystemExit) as exc_info:
        run()

    assert exc_info.value.code == 2
    mock_console.error.assert_called_once_with(error)


@patch("bpmn_print.cli.console")
@patch("bpmn_print.cli.pretty_print")
def test_run_handles_bpmn_file_error(
    mock_pretty_print, mock_console, monkeypatch
):
    """Test that BpmnFileError is caught and exits with code 2."""
    monkeypatch.setattr(
        "sys.argv",
        ["bpmn-print", "/input", "/output"],
    )

    error = BpmnFileError("File not found")
    mock_pretty_print.side_effect = error

    with pytest.raises(SystemExit) as exc_info:
        run()

    assert exc_info.value.code == 2
    mock_console.error.assert_called_once_with(error)


@patch("bpmn_print.cli.console")
@patch("bpmn_print.cli.pretty_print")
def test_run_handles_os_error(mock_pretty_print, mock_console, monkeypatch):
    """Test that OSError is caught and exits with code 2."""
    monkeypatch.setattr(
        "sys.argv",
        ["bpmn-print", "/input", "/output"],
    )

    os_error = OSError("Permission denied")
    mock_pretty_print.side_effect = os_error

    with pytest.raises(SystemExit) as exc_info:
        run()

    assert exc_info.value.code == 2
    # Check error message contains "File system error"
    call_args = mock_console.error.call_args[0][0]
    assert "File system error" in str(call_args)


@patch("bpmn_print.cli.console")
@patch("bpmn_print.cli.pretty_print")
def test_run_handles_unexpected_error(
    mock_pretty_print, mock_console, monkeypatch
):
    """Test that unexpected errors are caught and exit with code 3."""
    monkeypatch.setattr(
        "sys.argv",
        ["bpmn-print", "/input", "/output"],
    )

    unexpected_error = RuntimeError("Unexpected failure")
    mock_pretty_print.side_effect = unexpected_error

    with pytest.raises(SystemExit) as exc_info:
        run()

    assert exc_info.value.code == 3
    # Check error message contains "Unexpected error"
    call_args = mock_console.error.call_args[0][0]
    assert "Unexpected error" in str(call_args)


def test_run_missing_required_arguments(monkeypatch, capsys):
    """Test that missing required arguments causes exit."""
    monkeypatch.setattr(
        "sys.argv",
        ["bpmn-print"],
    )

    with pytest.raises(SystemExit) as exc_info:
        run()

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "required" in captured.err.lower()


def test_run_missing_output_folder(monkeypatch, capsys):
    """Test that missing output folder argument causes exit."""
    monkeypatch.setattr(
        "sys.argv",
        ["bpmn-print", "/input"],
    )

    with pytest.raises(SystemExit) as exc_info:
        run()

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "required" in captured.err.lower()
