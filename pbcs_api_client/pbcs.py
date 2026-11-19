
from typing import Any, Self, override

import httpx

from .auth import AuthProvider
from .endpoints.applications import ApplicationsEndpoint
from .endpoints.dimensions import DimensionsEndpoint
from .endpoints.forms import FormsEndpoint
from .endpoints.plan_types import PlanTypesEndpoint
from .exceptions import PbcsAuthenticationError, PbcsRequestError


class Pbcs:
    """Entry point to the PBCS REST API, with one attribute per endpoint group.

    ``url`` is the address of the PBCS instance, e.g.
    ``https://<instance>.pbcs.<region>.oraclecloud.com``. ``application`` is
    the application that application-level endpoint groups, like ``forms``,
    work on.

    To add an endpoint group, write an ``Endpoint`` subclass in ``endpoints/``
    and create it in ``__init__`` below.
    """

    def __init__(
        self,
        url: str,
        auth: AuthProvider,
        *,
        application: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.url = url.rstrip("/")
        self.application = application
        self._auth = auth

        self._http = httpx.Client(
            base_url=f"{self.url}/",
            timeout=timeout,
            headers={"Accept": "application/json"},
        )

        self.applications = ApplicationsEndpoint(self)
        self.dimensions = DimensionsEndpoint(self)
        self.forms = FormsEndpoint(self)
        self.plan_types = PlanTypesEndpoint(self)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any = None,
    ) -> Any:
        """Send an authenticated request and return the decoded JSON body.

        ``path`` is relative to ``url``, e.g. ``"HyperionPlanning/rest/v3/applications"``.
        Use it for REST APIs that have no endpoint group yet.
        """
        try:
            response = self._http.request(
                method,
                path.lstrip("/"),
                params=params,
                json=json,
                headers=self._auth.get_headers(),
            )
        except httpx.HTTPError as exc:
            raise PbcsRequestError(
                f"Could not reach PBCS: {exc}"
            ) from exc

        if response.status_code in (401, 403):
            raise PbcsAuthenticationError(
                f"PBCS returned HTTP {response.status_code}. "
                "Check authentication and permissions."
            )

        if not response.is_success:
            raise PbcsRequestError(
                f"PBCS returned HTTP {response.status_code}: "
                f"{response.text[:1000]}"
            )

        if not response.content:
            return None

        try:
            return response.json()
        except ValueError as exc:
            raise PbcsRequestError(
                "PBCS returned an invalid JSON response"
            ) from exc

    @override
    def __repr__(self) -> str:
        return f"Pbcs({self.url!r}, application={self.application!r})"
