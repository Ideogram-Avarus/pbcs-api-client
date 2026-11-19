"""Run a script from the command line.

    python -m pbcs_api_client <script> [options]
    python -m pbcs_api_client <script> --help

Options left out are read from environment variables. A .env file in the
current directory is loaded into the environment first, without overriding
variables that are already set.
"""

import argparse
import sys
from pathlib import Path

from .exceptions import PbcsError
from .scripts import SCRIPTS
from .scripts.base import load_env_file


def main(argv: list[str] | None = None) -> int:
    # Before the parsers are built, since option defaults come from it.
    load_env_file(Path(".env"))

    parser = argparse.ArgumentParser(
        prog="python -m pbcs_api_client",
        description="Scripts for the PBCS REST APIs.",
        epilog="Options left out are read from environment variables, "
        "or from a .env file in the current directory.",
    )
    commands = parser.add_subparsers(dest="script", metavar="script", required=True)
    for script in SCRIPTS:
        command = commands.add_parser(
            script.name, help=script.help, description=script.description
        )
        script.configure(command)
        command.set_defaults(run=script.run)

    args = parser.parse_args(argv)
    try:
        args.run(args)
    except (PbcsError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
