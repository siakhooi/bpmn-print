import argparse
import sys
from importlib.metadata import version
from bpmn_print.bpmn_pretty_print import pretty_print


def print_to_stderr_and_exit(e: Exception, exit_code: int) -> None:
    print(f"Error: {e}", file=sys.stderr)
    exit(exit_code)


def run() -> None:
    __version__: str = version("bpmn-print")

    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Print BPMN workflow for developer readings"
    )

    parser.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument("input_folder", help="input folder")
    parser.add_argument("output_folder", help="output folder")

    args = parser.parse_args()

    if not args.input_folder or not args.output_folder:
        print_to_stderr_and_exit(
            Exception("Both input_folder and output_folder are required."), 1
        )

    try:
        pretty_print(args.input_folder, args.output_folder)
    except Exception as e:
        print_to_stderr_and_exit(e, 1)
