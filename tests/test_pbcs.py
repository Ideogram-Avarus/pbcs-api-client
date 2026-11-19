
"""Pbcs configuration and raw requests.

The configuration tests run offline; the request tests use the PBCS test
instance from .env and only send read-only requests. They sign in with
OAuth 2, except the basic auth test, which is skipped without
PBCS_USERNAME and PBCS_PASSWORD.
"""

import pytest

from conftest import setting, timeout
from pbcs_api_client import BasicAuthProvider, Pbcs, PbcsRequestError

REST = "HyperionPlanning/rest"
AUTH = BasicAuthProvider("user", "secret")


def test_url_trailing_slash_is_removed() -> None:
    with Pbcs("https://pbcs.example.com/", AUTH) as pbcs:
        assert pbcs.url == "https://pbcs.example.com"


def test_application_endpoints_need_an_application() -> None:
    with Pbcs("https://pbcs.example.com", AUTH) as pbcs:
        with pytest.raises(ValueError, match="needs an application"):
            pbcs.forms.export_data("Any form")
        with pytest.raises(ValueError, match="needs an application"):
            pbcs.dimensions.list("Any plan type")
        with pytest.raises(ValueError, match="needs an application"):
            pbcs.plan_types.import_data(
                "Any plan type",
                grid={"pov": [], "columns": [["Jan"]], "rows": [{"headers": ["A"], "data": [1]}]},
            )


def test_password_is_hidden_from_repr() -> None:
    assert "secret" not in repr(AUTH)


def test_unreachable_host_raises_request_error() -> None:
    # The .invalid TLD is reserved and never resolves.
    with Pbcs("https://pbcs.invalid", AUTH) as pbcs:
        with pytest.raises(PbcsRequestError, match="Could not reach PBCS"):
            pbcs.request("GET", f"{REST}/")


def test_lists_api_versions(pbcs: Pbcs) -> None:
    result = pbcs.request("GET", f"{REST}/")

    versions = result["items"]
    assert versions
    assert all("version" in item for item in versions)
    assert any(item["isLatest"] for item in versions)


def test_leading_slash_in_path_is_accepted(pbcs: Pbcs) -> None:
    result = pbcs.request("GET", f"/{REST}/v3/applications")

    assert result["items"]


def test_unknown_path_raises_request_error(pbcs: Pbcs) -> None:
    with pytest.raises(PbcsRequestError, match="404"):
        pbcs.request("GET", f"{REST}/v3/__pytest_missing__")


def test_basic_auth_request(application: str) -> None:
    auth = BasicAuthProvider(setting("PBCS_USERNAME"), setting("PBCS_PASSWORD"))
    with Pbcs(
        setting("PBCS_URL"), auth, application=application, timeout=timeout()
    ) as pbcs:
        names = [item["name"] for item in pbcs.applications.list()["items"]]

    assert application in names
