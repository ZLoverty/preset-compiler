"""Small package smoke-test CLI; source file traversal stays with callers."""

from __future__ import annotations

import argparse

from . import __version__


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="preset-compiler package information")
    parser.add_argument("--version", action="version", version=__version__)
    parser.parse_args(argv)
    parser.print_help()
    return 0
