import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
import os

from bpmn_print.path_utils import prepare_output_path
from bpmn_print.errors import BpmnRenderError


class TestPrepareOutputPath:
    """Tests for prepare_output_path function."""

    def test_basic_path_without_auto_extension(self):
        """Test basic path without auto extension."""
        with TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "output.png")
            path, parent = prepare_output_path(output_path)

            assert path == Path(output_path)
            assert parent == Path(tmpdir)
            assert parent.exists()

    def test_path_with_auto_extension_removes_existing_extension(self):
        """Test that auto_extension removes existing extension."""
        with TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "diagram.png")
            path, parent = prepare_output_path(output_path, ".png")

            # Extension should be removed
            assert path == Path(tmpdir) / "diagram"
            assert path.suffix == ""
            assert parent == Path(tmpdir)

    def test_path_with_different_auto_extension(self):
        """Test with different auto extension."""
        with TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "diagram.svg")
            path, _ = prepare_output_path(output_path, ".svg")

            assert path == Path(tmpdir) / "diagram"
            assert path.suffix == ""

    def test_creates_parent_directory_if_not_exists(self):
        """Test that parent directory is created if it doesn't exist."""
        with TemporaryDirectory() as tmpdir:
            nested_path = os.path.join(tmpdir, "sub1", "sub2", "diagram.png")
            _, parent = prepare_output_path(nested_path)

            assert parent.exists()
            assert parent == Path(tmpdir) / "sub1" / "sub2"

    def test_creates_deeply_nested_directories(self):
        """Test creation of deeply nested directory structure."""
        with TemporaryDirectory() as tmpdir:
            nested_path = os.path.join(
                tmpdir, "a", "b", "c", "d", "output.png"
            )
            path, parent = prepare_output_path(nested_path, ".png")

            assert parent.exists()
            assert parent == Path(tmpdir) / "a" / "b" / "c" / "d"
            assert path == Path(tmpdir) / "a" / "b" / "c" / "d" / "output"

    def test_existing_directory_not_recreated(self):
        """Test that existing directories are not recreated."""
        with TemporaryDirectory() as tmpdir:
            subdir = Path(tmpdir) / "existing"
            subdir.mkdir()

            output_path = os.path.join(tmpdir, "existing", "file.png")
            _, parent = prepare_output_path(output_path)

            assert parent.exists()
            assert parent == subdir

    def test_empty_auto_extension(self):
        """Test with empty string as auto_extension."""
        with TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "file.png")
            path, _ = prepare_output_path(output_path, "")

            # Empty string should not remove extension
            assert path == Path(output_path)
            assert path.suffix == ".png"

    def test_multiple_extensions_with_auto_extension(self):
        """Test file with multiple extensions."""
        with TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "file.tar.gz")
            path, _ = prepare_output_path(output_path, ".gz")

            # Only last extension should be removed
            assert path == Path(tmpdir) / "file.tar"
            assert path.suffix == ".tar"

    def test_file_without_extension_with_auto_extension(self):
        """Test file without extension when auto_extension provided."""
        with TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "diagram")
            path, _ = prepare_output_path(output_path, ".png")

            assert path == Path(tmpdir) / "diagram"
            assert path.suffix == ""

    def test_current_directory_as_parent(self):
        """Test when output is in current directory."""
        output_path = "output.png"
        path, parent = prepare_output_path(output_path)

        assert path == Path("output.png")
        assert parent == Path(".")

    def test_relative_path_with_subdirectory(self):
        """Test relative path with subdirectory."""
        with TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            output_path = "subdir/output.png"
            path, parent = prepare_output_path(output_path, ".png")

            assert parent.exists()
            assert path == Path("subdir/output")
            assert parent == Path("subdir")

    def test_absolute_path(self):
        """Test with absolute path."""
        with TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "output.png")
            path, _ = prepare_output_path(output_path, ".png")

            assert path.is_absolute()
            assert path == Path(tmpdir) / "output"

    def test_path_with_spaces(self):
        """Test path with spaces in directory and filename."""
        with TemporaryDirectory() as tmpdir:
            nested = os.path.join(tmpdir, "my folder", "output file.png")
            path, parent = prepare_output_path(nested)

            assert parent.exists()
            assert "my folder" in str(parent)
            assert path.name == "output file.png"

    def test_path_with_special_characters(self):
        """Test path with special characters."""
        with TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "diagram-v1.0_final.png")
            path, _ = prepare_output_path(output_path, ".png")

            assert path == Path(tmpdir) / "diagram-v1.0_final"

    def test_returns_tuple_of_path_objects(self):
        """Test that function returns tuple of Path objects."""
        with TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.png")
            result = prepare_output_path(output_path)

            assert isinstance(result, tuple)
            assert len(result) == 2
            assert isinstance(result[0], Path)
            assert isinstance(result[1], Path)

    def test_parent_equals_path_parent(self):
        """Test that returned parent matches path.parent."""
        with TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "sub", "output.png")
            path, parent = prepare_output_path(output_path)

            assert parent == path.parent

    def test_auto_extension_with_dot(self):
        """Test auto_extension with leading dot."""
        with TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "file.png")
            path, _ = prepare_output_path(output_path, ".png")

            assert path.suffix == ""
            assert path.name == "file"

    def test_auto_extension_without_dot(self):
        """Test auto_extension without leading dot."""
        with TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "file.png")
            path, _ = prepare_output_path(output_path, "png")

            # with_suffix handles extensions without dots
            assert path.suffix == ""

    def test_idempotent_directory_creation(self):
        """Test that calling twice doesn't cause errors."""
        with TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "new", "output.png")

            path1, parent1 = prepare_output_path(output_path)
            path2, parent2 = prepare_output_path(output_path)

            assert path1 == path2
            assert parent1 == parent2
            assert parent1.exists()


class TestPrepareOutputPathErrors:
    """Tests for error conditions in prepare_output_path."""

    def test_raises_error_when_directory_creation_fails(self, monkeypatch):
        """Test that BpmnRenderError is raised when mkdir fails."""
        with TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "sub", "output.png")

            # Mock mkdir to raise OSError
            original_mkdir = Path.mkdir

            def failing_mkdir(self, *args, **kwargs):
                if "sub" in str(self):
                    raise OSError("Permission denied")
                return original_mkdir(self, *args, **kwargs)

            monkeypatch.setattr(Path, "mkdir", failing_mkdir)

            with pytest.raises(BpmnRenderError) as exc_info:
                prepare_output_path(output_path)

            assert "Cannot create output directory" in str(exc_info.value)
            assert "Permission denied" in str(exc_info.value)

    def test_error_message_contains_directory_path(self, monkeypatch):
        """Test that error message contains the directory path."""
        with TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "fail", "output.png")

            def failing_mkdir(self, *args, **kwargs):
                raise OSError("Test error")

            monkeypatch.setattr(Path, "mkdir", failing_mkdir)

            with pytest.raises(BpmnRenderError) as exc_info:
                prepare_output_path(output_path)

            assert "fail" in str(exc_info.value)

    def test_preserves_original_oserror(self, monkeypatch):
        """Test that original OSError is preserved in exception chain."""
        with TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "sub", "output.png")

            def failing_mkdir(self, *args, **kwargs):
                raise OSError("Original error")

            monkeypatch.setattr(Path, "mkdir", failing_mkdir)

            with pytest.raises(BpmnRenderError) as exc_info:
                prepare_output_path(output_path)

            # Check that original exception is in the chain
            assert exc_info.value.__cause__ is not None
            assert isinstance(exc_info.value.__cause__, OSError)
            assert "Original error" in str(exc_info.value.__cause__)


class TestPrepareOutputPathEdgeCases:
    """Tests for edge cases in prepare_output_path."""

    def test_hidden_directory(self):
        """Test with hidden directory (starting with dot)."""
        with TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, ".hidden", "output.png")
            _, parent = prepare_output_path(output_path)

            assert parent.exists()
            assert ".hidden" in str(parent)

    def test_unicode_characters_in_path(self):
        """Test path with unicode characters."""
        with TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "diagrams", "图表.png")
            path, parent = prepare_output_path(output_path, ".png")

            assert parent.exists()
            assert path.name == "图表"

    def test_very_long_filename(self):
        """Test with very long filename."""
        with TemporaryDirectory() as tmpdir:
            long_name = "a" * 200 + ".png"
            output_path = os.path.join(tmpdir, long_name)
            path, parent = prepare_output_path(output_path, ".png")

            assert parent.exists()
            assert len(path.stem) == 200

    def test_extension_only_filename(self):
        """Test with filename that is only an extension."""
        with TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, ".png")
            _, parent = prepare_output_path(output_path, ".png")

            # Path behavior: .png with suffix removed becomes empty stem
            assert parent.exists()
