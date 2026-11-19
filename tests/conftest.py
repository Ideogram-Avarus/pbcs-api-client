
"""Integration test settings, read from the environment or the project's .env.

See .env.example for the variables. Tests whose settings are missing are
skipped, so the offline tests still run without a PBCS instance.

The ``pbcs`` fixture signs in with OAuth 2. It needs a refresh token in
.pbcs-tokens/refresh_token; create it once, from the project folder, with:
    python -m pbcs_api_client login
Refresh tokens expire after 7 days unused by default: run it again then.
"""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from dotenv import dotenv_values

from pbcs_api_client import DEFAULT_TOKEN_FILE, FileTokenStore, OAuthProvider, Pbcs

PROJECT_DIR = Path(__file__).resolve().parents[1]

# Environment variables win, so CI can provide them as secrets.
_SETTINGS = {**dotenv_values(PROJECT_DIR / ".env"), **os.environ}


def setting(name: str, default: str | None = None) -> str:
    """Test setting ``name``; skips the test when it is not set."""
    value = _SETTINGS.get(name) or default
    if not value:
        pytest.skip(f"{name} is not set in .env or the environment (see .env.example)")
    return value


def timeout() -> float:
    return float(setting("PBCS_TIMEOUT_SECONDS", "30"))


@pytest.fixture(scope="session")
def application() -> str:
    return setting("PBCS_APPLICATION")


def oauth_provider(store: FileTokenStore) -> OAuthProvider:
    return OAuthProvider(
        setting("PBCS_IDENTITY_DOMAIN_URL"),
        setting("PBCS_CLIENT_ID"),
        store,
        timeout=timeout(),
    )


def project_token_store() -> FileTokenStore:
    """The refresh token saved by the login command; skips the test without one."""
    store = FileTokenStore(PROJECT_DIR / DEFAULT_TOKEN_FILE)
    if store.load() is None:
        pytest.skip(f"No refresh token in {store.path} yet: run the login command")
    return store


@pytest.fixture(scope="session")
def pbcs(application: str) -> Iterator[Pbcs]:
    auth = oauth_provider(project_token_store())
    with Pbcs(
        setting("PBCS_URL"), auth, application=application, timeout=timeout()
    ) as pbcs:
        yield pbcs
