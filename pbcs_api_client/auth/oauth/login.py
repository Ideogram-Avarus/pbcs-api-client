
import time
from collections.abc import Callable

from ...exceptions import PbcsAuthenticationError
from . import idcs
from .store import TokenStore


def device_login(
    identity_domain_url: str,
    client_id: str,
    scope: str,
    store: TokenStore,
    *,
    timeout: float = 30.0,
    show: Callable[[str], None] = print,
) -> None:
    """Get the first refresh token with the device code flow and save it.

    Needs a person: ``show`` displays a URL and a code to enter in the
    browser, signed in as the user the API calls should run as. The code
    expires after 5 minutes.
    """
    if "offline_access" not in scope.split():
        # Without offline_access the identity domain issues no refresh token.
        scope = f"{scope} offline_access"

    device = idcs.request_device_code(
        identity_domain_url, client_id, scope, timeout=timeout
    )
    show(
        f"Open {device['verification_uri']} in a browser, sign in as the user "
        f"the API calls should run as, and enter the code: {device['user_code']}\n"
        f"The code expires in {device['expires_in'] // 60} minutes. Waiting..."
    )

    interval = device.get("interval", 5)
    deadline = time.monotonic() + device["expires_in"]

    while time.monotonic() < deadline:
        time.sleep(interval)
        try:
            tokens = idcs.poll_device_token(
                identity_domain_url, client_id, device["device_code"], timeout=timeout
            )
        except idcs.IdcsError as exc:
            if exc.error == "authorization_pending":
                continue
            if exc.error == "slow_down":
                interval += 5
                continue
            raise

        store.save(tokens["refresh_token"])
        return

    raise PbcsAuthenticationError(
        "The device code expired before the sign-in was completed. Run login again."
    )
