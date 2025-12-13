from pathlib import Path
from typing import Tuple

from .errors import BpmnRenderError


def prepare_output_path(
    output_path: str, auto_extension: str = ""
) -> Tuple[Path, Path]:
    """Prepare an output path by ensuring the directory exists.

    This utility handles:
    - Removing existing extensions when auto_extension is provided
    - Creating parent directories if they don't exist
    - Returning both the prepared path and its parent directory

    Args:
        output_path: The desired output file path
        auto_extension: Extension that will be automatically added by the
            rendering tool (e.g., ".png" for Graphviz). If provided, any
            existing extension will be removed to prevent double extensions.

    Returns:
        Tuple of (prepared_path, parent_directory)

    Raises:
        BpmnRenderError: If the output directory cannot be created

    Example:
        >>> path, parent = prepare_output_path("output/diagram.png", ".png")
        >>> # path will be "output/diagram" (extension removed)
        >>> # parent will be "output" (and will be created if needed)
    """
    path = Path(output_path)

    # Remove extension if auto_extension is provided
    if auto_extension:
        path = path.with_suffix("")

    # Ensure parent directory exists
    parent_dir = path.parent
    if parent_dir and not parent_dir.exists():
        try:
            parent_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise BpmnRenderError.output_dir_error(
                str(parent_dir), str(e)
            ) from e

    return path, parent_dir
