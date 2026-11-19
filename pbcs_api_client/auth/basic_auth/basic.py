
import base64
from typing import override


class BasicAuthProvider:
    """Sends the username and password with every request (HTTP Basic)."""

    def __init__(
        self,
        username: str,
        password: str,
    ) -> None:
        self._username = username
        self._password = password

    def get_headers(self) -> dict[str, str]:
        credentials = (
            f"{self._username}:{self._password}"
        ).encode("utf-8")

        token = base64.b64encode(credentials).decode("ascii")

        return {"Authorization": f"Basic {token}"}

    @override
    def __repr__(self) -> str:
        # Never show the password, e.g. in tracebacks or logs.
        return f"BasicAuthProvider(username={self._username!r}, password='***')"
