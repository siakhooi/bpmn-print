import argparse
from importlib.metadata import version
from bpmn_print.bpmn_pretty_print import pretty_print
import bpmn_print.console as console


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
        console.error(
            Exception("Both input_folder and output_folder are required.")
        )
        exit(1)

    try:
        pretty_print(args.input_folder, args.output_folder)
    except Exception as e:
        console.error(e)
        exit(2)
