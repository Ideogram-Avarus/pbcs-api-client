
import os
from pathlib import Path
from typing import Protocol, override

DEFAULT_TOKEN_FILE = Path(".pbcs-tokens/refresh_token")
"""Where ``login`` saves the refresh token and ``FileTokenStore`` looks for
it, relative to the current directory."""


class TokenStore(Protocol):
    """Keeps the current refresh token between runs.

    Refresh tokens are single-use: every refresh returns a new one, which
    must be saved before the next run. Each process or scheduled job needs
    its own store; two jobs sharing one token invalidate each other.
    """

    def load(self) -> str | None:
        ...

    def save(self, refresh_token: str) -> None:
        ...


class FileTokenStore:
    """Refresh token in a plain file, readable only by the current user.

    Keep the file out of git and on persistent storage (e.g. a Docker
    volume). For stronger protection, implement ``TokenStore`` on top of a
    secrets manager instead.

    ``path`` defaults to ``DEFAULT_TOKEN_FILE``, the file ``python -m
    pbcs_api_client login`` writes when run from the same directory.
    """

    def __init__(self, path: str | Path = DEFAULT_TOKEN_FILE) -> None:
        self.path = Path(path)

    def load(self) -> str | None:
        try:
            token = self.path.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            return None
        return token or None

    def save(self, refresh_token: str) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

        # Write to a temporary file and swap it in, so a crash mid-write
        # never leaves a truncated token behind.
        tmp = self.path.with_name(f"{self.path.name}.tmp")
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            file.write(refresh_token)
        os.replace(tmp, self.path)

    @override
    def __repr__(self) -> str:
        return f"FileTokenStore('{self.path}')"
