
"""OAuth 2 against the test identity domain and PBCS instance. Read-only requests only.

The request test needs a refresh token in .pbcs-tokens/refresh_token; create it once,
from the project folder (the command reads its settings from .env), with:
    python -m pbcs_api_client login
Running it rotates that token, as any real use does.
"""

from pathlib import Path

import pytest

from conftest import oauth_provider, project_token_store, setting, timeout
from pbcs_api_client import FileTokenStore, Pbcs, PbcsAuthenticationError


def test_invalid_refresh_token_is_rejected(tmp_path: Path) -> None:
    store = FileTokenStore(tmp_path / "test.refresh_token")
    store.save("not-a-real-refresh-token")
    provider = oauth_provider(store)

    with pytest.raises(PbcsAuthenticationError, match="was rejected"):
        provider.get_headers()

    # A rejected refresh must not touch the stored token.
    assert store.load() == "not-a-real-refresh-token"


def test_requests_use_oauth_and_rotate_the_refresh_token(application: str) -> None:
    store = project_token_store()
    before = store.load()

    with Pbcs(
        setting("PBCS_URL"),
        oauth_provider(store),
        application=application,
        timeout=timeout(),
    ) as pbcs:
        names = [item["name"] for item in pbcs.applications.list()["items"]]

    assert application in names
    assert store.load() not in (None, before)
