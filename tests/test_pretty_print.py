import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from bpmn_print.pretty_print import (
    ConversionConfig,
    convert_bpmn_to_pdf,
    pretty_print,
    BPMN_EXTENSION,
    PDF_EXTENSION,
    PNG_EXTENSION,
)
from bpmn_print.errors import BpmnRenderError


class TestConversionConfig:
    """Tests for ConversionConfig dataclass."""

    def test_config_creation(self):
        """Test creating a ConversionConfig instance."""
        config = ConversionConfig(
            bpmn_file="input.bpmn",
            pdf_path="output.pdf",
            png_file="diagram.png",
            keep_png=False,
        )

        assert config.bpmn_file == "input.bpmn"
        assert config.pdf_path == "output.pdf"
        assert config.png_file == "diagram.png"
        assert config.keep_png is False
        assert config.landscape_threshold == 2200  # default value

    def test_config_with_keep_png(self):
        """Test config with keep_png set to True."""
        config = ConversionConfig(
            bpmn_file="input.bpmn",
            pdf_path="output.pdf",
            png_file="diagram.png",
            keep_png=True,
        )

        assert config.keep_png is True

    def test_config_default_keep_png(self):
        """Test that keep_png defaults to False."""
        config = ConversionConfig(
            bpmn_file="input.bpmn",
            pdf_path="output.pdf",
            png_file="diagram.png",
        )

        assert config.keep_png is False

    def test_config_with_custom_threshold(self):
        """Test config with custom landscape threshold."""
        config = ConversionConfig(
            bpmn_file="input.bpmn",
            pdf_path="output.pdf",
            png_file="diagram.png",
            landscape_threshold=3000,
        )

        assert config.landscape_threshold == 3000


class TestConvertBpmnToPdf:
    """Tests for convert_bpmn_to_pdf function."""

    @patch("bpmn_print.pretty_print.pdf")
    @patch("bpmn_print.pretty_print.bpmn_data")
    @patch("bpmn_print.pretty_print.bpmn_diagram")
    @patch("bpmn_print.pretty_print.create_bpmn_context")
    def test_converts_bpmn_to_pdf(
        self, mock_context, mock_diagram, mock_data, mock_pdf
    ):
        """Test successful BPMN to PDF conversion."""
        # Setup mocks
        mock_ctx = Mock()
        mock_context.return_value = mock_ctx
        mock_diagram.render.return_value = [Mock(num=1, expression="x>0")]
        mock_extract_result = Mock(
            nodes=[Mock()], parameters=[Mock()], scripts=[Mock()]
        )
        mock_data.extract.return_value = mock_extract_result

        config = ConversionConfig(
            bpmn_file="test.bpmn",
            pdf_path="test.pdf",
            png_file="test.png",
            keep_png=False,
        )

        convert_bpmn_to_pdf(config)

        # Verify context was created once
        mock_context.assert_called_once_with("test.bpmn")

        # Verify diagram was rendered with context
        mock_diagram.render.assert_called_once_with(mock_ctx, "test.png")

        # Verify data was extracted with context
        mock_data.extract.assert_called_once_with(mock_ctx)

        # Verify PDF was created
        mock_pdf.make.assert_called_once()

    @patch("bpmn_print.pretty_print.pdf")
    @patch("bpmn_print.pretty_print.bpmn_data")
    @patch("bpmn_print.pretty_print.bpmn_diagram")
    @patch("bpmn_print.pretty_print.create_bpmn_context")
    @patch("bpmn_print.pretty_print.os.path.exists")
    @patch("bpmn_print.pretty_print.os.remove")
    def test_removes_png_when_not_keeping(
        self,
        mock_remove,
        mock_exists,
        mock_context,
        mock_diagram,
        mock_data,
        mock_pdf,
    ):
        """Test that PNG file is removed when keep_png is False."""
        mock_context.return_value = Mock()
        mock_diagram.render.return_value = []
        mock_data.extract.return_value = Mock(
            nodes=[], parameters=[], scripts=[]
        )
        mock_exists.return_value = True

        config = ConversionConfig(
            bpmn_file="test.bpmn",
            pdf_path="test.pdf",
            png_file="test.png",
            keep_png=False,
        )

        convert_bpmn_to_pdf(config)

        mock_exists.assert_called_once_with("test.png")
        mock_remove.assert_called_once_with("test.png")

    @patch("bpmn_print.pretty_print.pdf")
    @patch("bpmn_print.pretty_print.bpmn_data")
    @patch("bpmn_print.pretty_print.bpmn_diagram")
    @patch("bpmn_print.pretty_print.create_bpmn_context")
    @patch("bpmn_print.pretty_print.os.path.exists")
    @patch("bpmn_print.pretty_print.os.remove")
    def test_keeps_png_when_requested(
        self,
        mock_remove,
        mock_exists,
        mock_context,
        mock_diagram,
        mock_data,
        mock_pdf,
    ):
        """Test that PNG file is kept when keep_png is True."""
        mock_context.return_value = Mock()
        mock_diagram.render.return_value = []
        mock_data.extract.return_value = Mock(
            nodes=[], parameters=[], scripts=[]
        )

        config = ConversionConfig(
            bpmn_file="test.bpmn",
            pdf_path="test.pdf",
            png_file="test.png",
            keep_png=True,
        )

        convert_bpmn_to_pdf(config)

        mock_exists.assert_not_called()
        mock_remove.assert_not_called()

    @patch("bpmn_print.pretty_print.pdf")
    @patch("bpmn_print.pretty_print.bpmn_data")
    @patch("bpmn_print.pretty_print.bpmn_diagram")
    @patch("bpmn_print.pretty_print.create_bpmn_context")
    @patch("bpmn_print.pretty_print.os.path.exists")
    @patch("bpmn_print.pretty_print.os.remove")
    @patch("bpmn_print.pretty_print.console")
    def test_handles_png_removal_error(
        self,
        mock_console,
        mock_remove,
        mock_exists,
        mock_context,
        mock_diagram,
        mock_data,
        mock_pdf,
    ):
        """Test handling of error when removing PNG file."""
        mock_context.return_value = Mock()
        mock_diagram.render.return_value = []
        mock_data.extract.return_value = Mock(
            nodes=[], parameters=[], scripts=[]
        )
        mock_exists.return_value = True
        mock_remove.side_effect = OSError("Permission denied")

        config = ConversionConfig(
            bpmn_file="test.bpmn",
            pdf_path="test.pdf",
            png_file="test.png",
            keep_png=False,
        )

        convert_bpmn_to_pdf(config)

        mock_console.warning.assert_called_once()
        assert "Could not remove PNG file" in str(
            mock_console.warning.call_args
        )

    @patch("bpmn_print.pretty_print.pdf.make")
    @patch("bpmn_print.pretty_print.pdf.PdfData")
    @patch("bpmn_print.pretty_print.bpmn_data")
    @patch("bpmn_print.pretty_print.bpmn_diagram")
    @patch("bpmn_print.pretty_print.create_bpmn_context")
    def test_passes_all_data_to_pdf(
        self,
        mock_context,
        mock_diagram,
        mock_data,
        mock_pdf_data,
        mock_make,
    ):
        """Test that all extracted data is passed to PDF generation."""
        mock_context.return_value = Mock()
        conditions = [Mock(num=1, expression="test")]
        nodes = [Mock(name="Node1")]
        parameters = [Mock(node_name="Node1", param_name="p1")]
        scripts = [Mock(text="script")]

        mock_diagram.render.return_value = conditions
        mock_data.extract.return_value = Mock(
            nodes=nodes, parameters=parameters, scripts=scripts
        )

        config = ConversionConfig(
            bpmn_file="test.bpmn",
            pdf_path="test.pdf",
            png_file="test.png",
        )

        convert_bpmn_to_pdf(config)

        # Verify PdfData was created with correct arguments
        mock_pdf_data.assert_called_once_with(
            png_file="test.png",
            branch_conditions=conditions,
            nodes=nodes,
            parameters=parameters,
            jexl_scripts=scripts,
        )

        # Verify make was called
        mock_make.assert_called_once()


class TestPrettyPrint:
    """Tests for pretty_print function."""

    @patch("bpmn_print.pretty_print.convert_bpmn_to_pdf")
    @patch("bpmn_print.pretty_print.console")
    def test_processes_single_bpmn_file(self, mock_console, mock_convert):
        """Test processing a single BPMN file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = Path(temp_dir) / "input"
            output_dir = Path(temp_dir) / "output"
            input_dir.mkdir()

            # Create a BPMN file
            bpmn_file = input_dir / "test.bpmn"
            bpmn_file.write_text("<bpmn/>")

            pretty_print(str(input_dir), str(output_dir), keep_png=False)

            # Verify conversion was called
            mock_convert.assert_called_once()
            config = mock_convert.call_args[0][0]
            assert config.bpmn_file == str(bpmn_file)
            assert config.keep_png is False

    @patch("bpmn_print.pretty_print.convert_bpmn_to_pdf")
    @patch("bpmn_print.pretty_print.console")
    def test_processes_multiple_bpmn_files(self, mock_console, mock_convert):
        """Test processing multiple BPMN files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = Path(temp_dir) / "input"
            output_dir = Path(temp_dir) / "output"
            input_dir.mkdir()

            # Create multiple BPMN files
            (input_dir / "test1.bpmn").write_text("<bpmn/>")
            (input_dir / "test2.bpmn").write_text("<bpmn/>")
            (input_dir / "test3.bpmn").write_text("<bpmn/>")

            pretty_print(str(input_dir), str(output_dir))

            # Verify conversion was called 3 times
            assert mock_convert.call_count == 3

    @patch("bpmn_print.pretty_print.console")
    def test_creates_output_directory(self, mock_console):
        """Test that output directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = Path(temp_dir) / "input"
            output_dir = Path(temp_dir) / "output" / "subdir"
            input_dir.mkdir()

            # Create a BPMN file
            (input_dir / "test.bpmn").write_text("<bpmn/>")

            with patch("bpmn_print.pretty_print.convert_bpmn_to_pdf"):
                pretty_print(str(input_dir), str(output_dir))

            # Verify output directory was created
            assert output_dir.exists()

    @patch("bpmn_print.pretty_print.console")
    def test_handles_no_bpmn_files(self, mock_console):
        """Test handling when no BPMN files are found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = Path(temp_dir) / "input"
            output_dir = Path(temp_dir) / "output"
            input_dir.mkdir()

            # Create a non-BPMN file
            (input_dir / "test.txt").write_text("not bpmn")

            pretty_print(str(input_dir), str(output_dir))

            # Verify info message about no files
            calls = [str(call) for call in mock_console.info.call_args_list]
            assert any("No BPMN files found" in str(c) for c in calls)

    @patch("bpmn_print.pretty_print.console")
    def test_output_dir_creation_error(self, mock_console):
        """Test error handling when output directory cannot be created."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = Path(temp_dir) / "input"
            input_dir.mkdir()

            # Use an invalid path for output
            invalid_output = "/root/invalid_path_no_permission"

            with pytest.raises(BpmnRenderError) as exc_info:
                pretty_print(str(input_dir), invalid_output)

            assert "output directory" in str(exc_info.value).lower()

    @patch("bpmn_print.pretty_print.console")
    def test_input_dir_not_readable_error(self, mock_console):
        """Test handling when input directory doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "output"

            # Use a non-existent input directory
            invalid_input = "/nonexistent/path/that/does/not/exist"

            # Non-existent path just results in no files found
            pretty_print(invalid_input, str(output_dir))

            # Verify message about no files
            calls = [str(call) for call in mock_console.info.call_args_list]
            assert any("No BPMN files found" in str(c) for c in calls)

    @patch("bpmn_print.pretty_print.console")
    def test_input_dir_glob_oserror(self, mock_console):
        """Test error handling when glob raises OSError."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = Path(temp_dir) / "input"
            output_dir = Path(temp_dir) / "output"
            input_dir.mkdir()

            # Mock Path.glob to raise OSError
            with patch("pathlib.Path.glob") as mock_glob:
                mock_glob.side_effect = OSError("Permission denied")

                from bpmn_print.errors import BpmnFileError

                with pytest.raises(BpmnFileError) as exc_info:
                    pretty_print(str(input_dir), str(output_dir))

                assert "cannot be read" in str(exc_info.value).lower()

    @patch("bpmn_print.pretty_print.convert_bpmn_to_pdf")
    @patch("bpmn_print.pretty_print.console")
    def test_generates_correct_output_paths(self, mock_console, mock_convert):
        """Test that output file paths are generated correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = Path(temp_dir) / "input"
            output_dir = Path(temp_dir) / "output"
            input_dir.mkdir()

            # Create a BPMN file
            (input_dir / "workflow.bpmn").write_text("<bpmn/>")

            pretty_print(str(input_dir), str(output_dir))

            config = mock_convert.call_args[0][0]
            assert config.pdf_path.endswith("workflow.pdf")
            assert config.png_file.endswith("workflow.png")

    @patch("bpmn_print.pretty_print.convert_bpmn_to_pdf")
    @patch("bpmn_print.pretty_print.console")
    def test_passes_keep_png_option(self, mock_console, mock_convert):
        """Test that keep_png option is passed to conversion."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = Path(temp_dir) / "input"
            output_dir = Path(temp_dir) / "output"
            input_dir.mkdir()

            (input_dir / "test.bpmn").write_text("<bpmn/>")

            pretty_print(str(input_dir), str(output_dir), keep_png=True)

            config = mock_convert.call_args[0][0]
            assert config.keep_png is True

    @patch("bpmn_print.pretty_print.convert_bpmn_to_pdf")
    @patch("bpmn_print.pretty_print.console")
    def test_prints_progress_messages(self, mock_console, mock_convert):
        """Test that progress messages are printed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = Path(temp_dir) / "input"
            output_dir = Path(temp_dir) / "output"
            input_dir.mkdir()

            (input_dir / "test.bpmn").write_text("<bpmn/>")

            pretty_print(str(input_dir), str(output_dir))

            # Verify info messages were printed
            assert mock_console.info.call_count >= 3
            mock_console.println.assert_called_with("Done.")

    @patch("bpmn_print.pretty_print.convert_bpmn_to_pdf")
    @patch("bpmn_print.pretty_print.console")
    def test_ignores_non_bpmn_files(self, mock_console, mock_convert):
        """Test that non-BPMN files are ignored."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = Path(temp_dir) / "input"
            output_dir = Path(temp_dir) / "output"
            input_dir.mkdir()

            # Create mixed files
            (input_dir / "test.bpmn").write_text("<bpmn/>")
            (input_dir / "readme.txt").write_text("text")
            (input_dir / "data.xml").write_text("<xml/>")

            pretty_print(str(input_dir), str(output_dir))

            # Should only process the .bpmn file
            assert mock_convert.call_count == 1


class TestConstants:
    """Tests for module constants."""

    def test_file_extension_constants(self):
        """Test that file extension constants are defined correctly."""
        assert BPMN_EXTENSION == ".bpmn"
        assert PDF_EXTENSION == ".pdf"
        assert PNG_EXTENSION == ".png"
