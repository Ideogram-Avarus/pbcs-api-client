
"""Requests to the OCI identity domain (IDCS) token endpoints.

See "Authentication with OAuth 2" in the REST APIs for Oracle Fusion Cloud
EPM guide for the requests these mirror.
"""

from typing import Any, NotRequired, TypedDict

import httpx

from ...exceptions import PbcsAuthenticationError, PbcsRequestError

DEVICE_CODE_GRANT = "urn:ietf:params:oauth:grant-type:device_code"


class DeviceCodeResponse(TypedDict):
    device_code: str
    user_code: str
    verification_uri: str
    expires_in: int
    interval: NotRequired[int]


class TokenResponse(TypedDict):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str


class IdcsError(PbcsAuthenticationError):
    """The identity domain rejected a token request."""

    def __init__(self, error: str, description: str) -> None:
        super().__init__(f"Identity domain returned '{error}': {description}")
        self.error = error
        self.description = description


def request_device_code(
    identity_domain_url: str, client_id: str, scope: str, *, timeout: float
) -> DeviceCodeResponse:
    return _post(
        identity_domain_url,
        "device",
        {"response_type": "device_code", "scope": scope, "client_id": client_id},
        timeout=timeout,
    )


def poll_device_token(
    identity_domain_url: str, client_id: str, device_code: str, *, timeout: float
) -> TokenResponse:
    return _post(
        identity_domain_url,
        "token",
        {
            "grant_type": DEVICE_CODE_GRANT,
            "device_code": device_code,
            "client_id": client_id,
        },
        timeout=timeout,
    )


def refresh_access_token(
    identity_domain_url: str, client_id: str, refresh_token: str, *, timeout: float
) -> TokenResponse:
    return _post(
        identity_domain_url,
        "token",
        {
            "grant_type": "refresh_token",
            "client_id": client_id,
            "refresh_token": refresh_token,
        },
        timeout=timeout,
    )


def _post(
    identity_domain_url: str, path: str, data: dict[str, str], *, timeout: float
) -> Any:
    try:
        response = httpx.post(
            f"{identity_domain_url}/oauth2/v1/{path}", data=data, timeout=timeout
        )
    except httpx.HTTPError as exc:
        raise PbcsRequestError(
            f"Could not reach the identity domain: {exc}"
        ) from exc

    try:
        body: Any = response.json()
    except ValueError:
        body = {}

    if not response.is_success:
        raise IdcsError(
            body.get("error", f"HTTP {response.status_code}"),
            body.get("error_description", response.text[:300]),
        )

    return body
