
"""ApplicationsEndpoint against the PBCS test instance. Read-only requests only."""

from pbcs_api_client import Pbcs


def test_list_includes_configured_application(pbcs: Pbcs, application: str) -> None:
    names = [item["name"] for item in pbcs.applications.list()["items"]]

    assert application in names
