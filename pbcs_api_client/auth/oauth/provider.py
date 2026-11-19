
import threading
import time

from ...exceptions import PbcsAuthenticationError
from . import idcs
from .store import TokenStore

LOGIN_HINT = (
    "Run `python -m pbcs_api_client login` to sign in again "
    "(see --help)."
)


class OAuthProvider:
    """Sends an OAuth 2 access token (Bearer) instead of the password.

    The access token lives only in memory and is renewed from the refresh
    token shortly before it expires (by default every hour). Each renewal
    also rotates the refresh token, which is saved to ``store`` right away.
    """

    def __init__(
        self,
        identity_domain_url: str,
        client_id: str,
        store: TokenStore,
        *,
        timeout: float = 30.0,
        refresh_margin_seconds: float = 60.0,
    ) -> None:
        self._identity_domain_url = identity_domain_url
        self._client_id = client_id
        self._store = store
        self._timeout = timeout
        self._refresh_margin = refresh_margin_seconds

        self._lock = threading.RLock()
        self._access_token: str | None = None
        self._expires_at = 0.0

    def get_headers(self) -> dict[str, str]:
        with self._lock:
            if self._access_token is None or time.monotonic() >= self._expires_at:
                self.refresh()
            return {"Authorization": f"Bearer {self._access_token}"}

    def refresh(self) -> None:
        """Get a new access token and rotate the stored refresh token.

        Call it at least every 6 days from a scheduled job when nothing else
        uses the token, since refresh tokens expire after 7 days by default.
        """
        with self._lock:
            refresh_token = self._store.load()
            if refresh_token is None:
                raise PbcsAuthenticationError(
                    f"No OAuth refresh token in {self._store!r}. {LOGIN_HINT}"
                )

            try:
                tokens = idcs.refresh_access_token(
                    self._identity_domain_url,
                    self._client_id,
                    refresh_token,
                    timeout=self._timeout,
                )
            except idcs.IdcsError as exc:
                raise PbcsAuthenticationError(
                    f"The refresh token in {self._store!r} was rejected "
                    f"({exc.description}). It may have expired, been used by "
                    f"another process, or been revoked. {LOGIN_HINT}"
                ) from exc

            # The old refresh token is consumed now: save the new one first.
            try:
                self._store.save(tokens["refresh_token"])
            except OSError as exc:
                raise PbcsAuthenticationError(
                    f"Could not save the new refresh token to {self._store!r}; "
                    f"the previous one is no longer valid. {LOGIN_HINT}"
                ) from exc

            self._access_token = tokens["access_token"]
            self._expires_at = (
                time.monotonic() + tokens["expires_in"] - self._refresh_margin
            )
