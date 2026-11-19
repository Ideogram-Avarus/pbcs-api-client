import argparse

from ..auth.oauth import FileTokenStore, device_login
from .base import Script, add_oauth_options, env_option


def configure(parser: argparse.ArgumentParser) -> None:
    add_oauth_options(parser)
    env_option(
        parser,
        "--scope",
        "PBCS_OAUTH_SCOPE",
        "OAuth 2 scope of the PBCS instance; offline_access is added",
    )


def run(args: argparse.Namespace) -> None:
    store = FileTokenStore(args.token_file)
    device_login(
        args.identity_domain_url,
        args.client_id,
        args.scope,
        store,
        timeout=args.timeout,
    )
    print(f"Signed in. Refresh token saved to {store.path}")


script = Script(
    name="login",
    help="sign in and save the first refresh token",
    description="One-time browser sign-in (device code flow) that saves the "
    "first refresh token to --token-file.",
    configure=configure,
    run=run,
)
