import argparse
import sys
from importlib.metadata import version

from .pretty_print import pretty_print
from .errors import BpmnError
from . import console


def run() -> None:
    __version__: str = version("bpmn-print")

    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Print BPMN workflow for developer readings"
    )

    parser.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "-k",
        "--keep",
        action="store_true",
        help="keep PNG files after PDF generation",
    )
    parser.add_argument(
        "-t",
        "--diagram-landscape-threshold",
        type=int,
        default=2200,
        metavar="PIXELS",
        help=(
            "width threshold in pixels for landscape diagram layout "
            "(default: 2200)"
        ),
    )
    parser.add_argument("input_folder", help="input folder")
    parser.add_argument("output_folder", help="output folder")

    args = parser.parse_args()

    try:
        pretty_print(
            args.input_folder,
            args.output_folder,
            args.keep,
            args.diagram_landscape_threshold,
        )
    except BpmnError as e:
        # Catch all BPMN-specific errors
        console.error(e)
        sys.exit(2)
    except OSError as e:
        # Catch file system errors
        console.error(Exception(f"File system error: {e}"))
        sys.exit(2)
    except Exception as e:
        # Re-raise unexpected errors for better debugging
        console.error(Exception(f"Unexpected error: {e}"))
        sys.exit(3)
