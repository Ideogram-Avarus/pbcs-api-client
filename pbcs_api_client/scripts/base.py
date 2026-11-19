"""Scaffolding shared by the command line scripts.

Each script is a ``Script`` registered in ``scripts/__init__.py``; ``__main__``
gives it a subcommand. Unlike the library, scripts read their settings from
environment variables, loaded first from a .env file in the current directory.
"""

import argparse
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from ..auth.oauth import DEFAULT_TOKEN_FILE


@dataclass(frozen=True)
class Script:
    name: str
    help: str
    configure: Callable[[argparse.ArgumentParser], None]
    """Adds the script's options to its parser."""
    run: Callable[[argparse.Namespace], None]
    """Runs the script; raises ``PbcsError`` or ``ValueError`` on failure."""
    description: str | None = None


def load_env_file(path: Path) -> None:
    """Add ``KEY=value`` lines from ``path`` to the environment, if it exists.

    Variables already in the environment win over the file.
    """
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.removeprefix("export ").split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]

        os.environ.setdefault(key.strip(), value)


def env_option(
    parser: argparse.ArgumentParser, flag: str, variable: str, help: str
) -> None:
    """Add ``flag``, defaulting to ``$variable``; required when that is unset."""
    default = os.environ.get(variable) or None
    parser.add_argument(
        flag,
        default=default,
        required=default is None,
        help=f"{help} (default: ${variable})",
    )


def add_oauth_options(parser: argparse.ArgumentParser) -> None:
    """Options to reach the identity domain and the saved refresh token."""
    env_option(
        parser,
        "--identity-domain-url",
        "PBCS_IDENTITY_DOMAIN_URL",
        "e.g. https://idcs-<id>.identity.oraclecloud.com",
    )
    env_option(
        parser,
        "--client-id",
        "PBCS_CLIENT_ID",
        "client ID of the integrated application registered for OAuth 2",
    )
    parser.add_argument(
        "--token-file",
        default=DEFAULT_TOKEN_FILE,
        help=f"file that keeps the refresh token (default: {DEFAULT_TOKEN_FILE})",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=float(os.environ.get("PBCS_TIMEOUT_SECONDS") or 30.0),
        help="seconds (default: $PBCS_TIMEOUT_SECONDS, then 30)",
    )
