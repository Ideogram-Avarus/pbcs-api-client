import argparse

from ..auth.oauth import FileTokenStore, OAuthProvider
from .base import Script, add_oauth_options


def run(args: argparse.Namespace) -> None:
    store = FileTokenStore(args.token_file)
    OAuthProvider(
        args.identity_domain_url,
        args.client_id,
        store,
        timeout=args.timeout,
    ).refresh()
    print(f"Refresh token rotated in {store.path}")


script = Script(
    name="refresh",
    help="rotate the saved refresh token",
    description="Rotates the saved refresh token. Schedule it every 6 days for "
    "jobs that run less than weekly, since refresh tokens expire after 7 days.",
    configure=add_oauth_options,
    run=run,
)
