
from typing import Protocol


class AuthProvider(Protocol):
    def get_headers(self) -> dict[str, str]:
        """Headers that authenticate one request, e.g. ``Authorization``."""
        ...
