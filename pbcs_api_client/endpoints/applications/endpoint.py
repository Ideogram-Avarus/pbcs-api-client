
from typing import Any

from ..base import PLANNING_API, Endpoint


class ApplicationsEndpoint(Endpoint):
    def list(self) -> dict[str, Any]:
        """Applications available on the PBCS instance."""
        return self._pbcs.request("GET", f"{PLANNING_API}/applications")
