import sys


def error(e: Exception) -> None:
    print(f"Error: {e}", file=sys.stderr)
