# pbcs-api-client

Python client for the Oracle PBCS / EPM Cloud Planning REST APIs.

Not affiliated with or endorsed by Oracle.

## Install

```sh
pip install pbcs-api-client
```

Requires Python 3.12+.

## Usage

```python
from pbcs_api_client import BasicAuthProvider, Pbcs

auth = BasicAuthProvider("user@example.com", "password")

with Pbcs(
    "https://<instance>.pbcs.<region>.oraclecloud.com",
    auth,
    application="Vision",
) as pbcs:
    apps = pbcs.applications.list()

    dimensions = pbcs.dimensions.list("Plan1")
    entity = pbcs.dimensions.get("Entity", plan_type="Plan1")
    top_members = [member["name"] for member in entity["children"]]

    data = pbcs.forms.export_data(
        "Revenue Plan",
        page={"Entity": "410"},
        filters={"Account": ["4110", "4120"], "Period": "Jan"},
    )

    # Change values and write them back to the form's plan type (cube).
    data["rows"][0]["data"][0] = "1500"
    result = pbcs.plan_types.import_data(data["gridInfo"]["cubeName"], grid=data)
    if result["numRejectedCells"]:
        print(result.get("rejectedCells"))
```

`plan_types.import_data` writes straight to the cube, not through the form: the
form's validations and "Run on Save" rules don't run (pass
`post_import_rules=[...]` to run rules after the import). Unknown members fail the whole
request with HTTP 400; other cells PBCS can't save (read-only, invalid values)
are rejected one by one while the rest are saved, so check `numRejectedCells`.

Types for each endpoint group's arguments and results are imported from the
group's module, e.g.
`from pbcs_api_client.endpoints.forms import DisplayMemberAs, FormData`.

The library reads no configuration files or environment variables: load
credentials however your application does, and pass them in.

For REST APIs without an endpoint group yet, `pbcs.request(method, path)` sends
an authenticated request and returns the decoded JSON.

## OAuth 2

`OAuthProvider` sends an access token instead of the password. It needs an
integrated application registered in your OCI identity domain, and a first
refresh token from a one-time browser sign-in:

```sh
python -m pbcs_api_client login \
    --identity-domain-url https://idcs-<id>.identity.oraclecloud.com \
    --client-id <client id> \
    --scope <PBCS scope>
```

The refresh token is saved to `.pbcs-tokens/refresh_token` in the current
directory (`--token-file` to change it); keep `.pbcs-tokens/` out of git.
Each option left out is read from its environment variable
(`PBCS_IDENTITY_DOMAIN_URL`, `PBCS_CLIENT_ID`, `PBCS_OAUTH_SCOPE`,
`PBCS_TIMEOUT_SECONDS`). A `.env` file in the current directory is loaded
first, without overriding variables already set, so with those in `.env` this
is enough:

```sh
python -m pbcs_api_client login
```

Then, from the same directory, `FileTokenStore()` finds that token:

```python
from pbcs_api_client import FileTokenStore, OAuthProvider, Pbcs

auth = OAuthProvider(
    "https://idcs-<id>.identity.oraclecloud.com",
    "<client id>",
    FileTokenStore(),
)
pbcs = Pbcs("https://<instance>.pbcs.<region>.oraclecloud.com", auth)
```

Refresh tokens are single-use and expire after 7 days by default. Each use
rotates the token in the store, so give each process its own token file. For
jobs that run less than weekly, schedule
`python -m pbcs_api_client refresh ...` every 6 days. To keep the
token elsewhere, such as a secrets manager, implement `TokenStore`.

## Scripts

`python -m pbcs_api_client` lists the command line scripts, and
`python -m pbcs_api_client <script> --help` shows a script's options. Scripts
live in `pbcs_api_client/scripts/`: to add one, write a module that defines
a `Script` (see `scripts/base.py`) and list it in `scripts/__init__.py`.

## Development

```sh
pip install -e ".[dev]"
cp .env.example .env   # then fill in a test instance
python -m pbcs_api_client login   # once, and again when the refresh token expires
pytest
pyright                # strict type checking, configured in pyproject.toml
```

The integration tests run against a real PBCS instance configured in `.env` or
environment variables; tests whose settings are missing are skipped. They sign
in with OAuth 2, using the refresh token the login command saves; only one test
uses basic auth (`PBCS_USERNAME` / `PBCS_PASSWORD`, optional).

To add endpoints, follow the conventions in [CONTRIBUTING.md](CONTRIBUTING.md).
