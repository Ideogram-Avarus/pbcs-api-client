# Contributing

How to add endpoints so that every group feels the same to use: someone who
has used `pbcs.forms` should be able to guess how `pbcs.jobs` works.

See the README's Development section to set up a test instance and run the
tests.

## Endpoint groups

Each group is an attribute on `Pbcs`, named after the PBCS concept users see
in the UI, not after Oracle's URL layout:

```python
pbcs.applications     # instance level
pbcs.files            # inbox/outbox upload, download, list
pbcs.snapshots
pbcs.forms            # application level
pbcs.jobs             # rules, imports, exports, cube refresh
pbcs.dimensions
pbcs.plan_types        # data slices written to a cube
pbcs.substitution_variables
```

Oracle spreads these over several REST APIs (Planning, Migration, Data
Management), each with its own base path. Keep those paths as constants in
`endpoints/base.py`, next to `PLANNING_API`; users never see them.

Application-level groups build their paths with `self._application_path()`,
which uses the `application` passed to `Pbcs`.

## Imports

The package root exports only what every user needs: `Pbcs`, the auth
providers and token stores, and the exceptions. Each group's types are
imported from the group's own subpackage:

```python
from pbcs_api_client import OAuthProvider, Pbcs, PbcsRequestError
from pbcs_api_client.endpoints.forms import DisplayMemberAs, FormData
```

This keeps the root short as groups are added, and makes it clear which
group a type belongs to.

- `endpoints/<group>/__init__.py` exports the group's `Endpoint` subclass
  and every public name in its `types.py`, listed in `__all__`.
- Neither `endpoints/__init__.py` nor `pbcs_api_client/__init__.py`
  re-exports group types or endpoint classes. `endpoints/__init__.py`
  exports only the `Endpoint` base class.
- Inside the package, import from the module that defines the name:
  `pbcs.py` imports `FormsEndpoint` from `.endpoints.forms`.

## Naming

- Group subpackage and `Pbcs` attribute: plural snake_case, the same word
  (`endpoints/substitution_variables/`, `pbcs.substitution_variables`).
- Endpoint class: the group in PascalCase plus `Endpoint`
  (`SubstitutionVariablesEndpoint`).
- Types are named after the singular concept they describe, prefixed with
  it (`FormData`, `FormGridInfo`, `FormRow`, not `Data` or `GridInfo`), so
  types from different groups can be imported side by side without
  clashing. Argument types that mirror a PBCS parameter keep its name
  (`DisplayMemberAs`).
- `TypedDict` fields keep PBCS's camelCase keys (`gridInfo`, `rowDimNames`),
  since they describe the JSON as PBCS returns it. Method arguments use
  snake_case (see [Arguments](#arguments)).

## Method names

Use the same verbs in every group:

| Verb | Meaning | Returns |
|---|---|---|
| `list(...)` | a collection | `list[ItemType]` |
| `get(name)` | one item | `ItemType` |
| `create` / `update` / `delete` | changes | the item, or `None` |
| `run(...)` | start a job | a job handle (see [Jobs](#jobs)) |
| `export_<x>` / `import_<x>` | data transfer | a typed result |

## Arguments

- The required identifier (form name, job name, ...) is the first positional
  argument. Everything else is keyword-only, after `*`.
- Use Python names and values: `display_member_as="MEMBER_NAME"`, not
  `displayMemberAs="Member Name"`. Translate to what PBCS expects inside the
  method.
- Use `Literal` types for fixed choices, so editors suggest the valid values.
- Default to `None` and only send a parameter when the user set it, so PBCS
  keeps its own defaults.

## Return values

- Describe every response with a `TypedDict` in the group's `types.py`, with a
  docstring on each field that gives an example value. `FormData` is the model
  to follow.
- Return what the user asked for. Drop Oracle's wrappers (`items`, `links`,
  `hasMore`): `list()` returns the items themselves.
- If an endpoint is paginated, fetch every page inside `list()`, so the user
  gets one list. `self._get_all_pages(path)` does this for collections that
  page with `offset`/`limit` and report `hasMore`.

## Jobs

Many PBCS operations start a job that runs in the background: the response
has a `jobId`, and `status: -1` means it is still running. Methods that start
a job return the same job handle, which can wait for the job, report its
status and details, and raise an error if the job fails. Users should never
have to write a polling loop.

## Errors

- `Pbcs.request` raises `PbcsAuthenticationError` for HTTP 401/403 and
  `PbcsRequestError` for other failures. Don't catch these in endpoints.
- Raise `ValueError` for invalid arguments before sending the request, when
  the check is cheap.
- Check for mistakes that PBCS accepts silently. For example, PBCS ignores
  filter members it can't use and returns the unfiltered grid, so
  `forms.export_data` checks the filter dimensions against the form.
- Say what was wrong and what is valid: "Form 'Revenue Plan' has no page
  dimension(s) ['Region']; page dimensions are ['Entity']".

## Docstrings

Each public method's docstring explains each argument with an example value,
points to the return type, and notes any PBCS behavior that could surprise the
user, such as PBCS remembering the page you send to a form.

## Adding an endpoint group

1. Create `pbcs_api_client/endpoints/<group>/` with:
   - `endpoint.py`: an `Endpoint` subclass whose methods call
     `self._pbcs.request(...)`.
   - `types.py`: the `TypedDict`s and `Literal`s for its arguments and
     responses.
   - `__init__.py`: exports the endpoint class and the public types, in
     `__all__` (see [Imports](#imports)).
2. Import the endpoint class in `pbcs.py` from its subpackage
   (`from .endpoints.jobs import JobsEndpoint`) and create the group in
   `Pbcs.__init__`: `self.jobs = JobsEndpoint(self)`. Don't add it to
   `endpoints/__init__.py` or `pbcs_api_client/__init__.py`.
3. Import the group's types in tests and the README from
   `pbcs_api_client.endpoints.<group>`.
4. Add integration tests in `tests/test_<group>.py`. Use read-only requests
   where possible, and read instance-specific names with `setting(...)`, listed
   in `.env.example`, so tests whose settings are missing are skipped.
5. Add a usage example to the README.
6. Run `pytest` and `pyright`.

To add a method to an existing group, follow steps 4 to 6.

## Not in place yet

These conventions are ahead of the code:

- `applications.list()` still returns the raw response; it should return the
  items.
- There is no job handle yet. Build it with the first group that starts a
  job, then reuse it.
- `Pbcs.request` puts the raw response text in `PbcsRequestError`; it should
  use the `detail` or `message` from PBCS error responses.
