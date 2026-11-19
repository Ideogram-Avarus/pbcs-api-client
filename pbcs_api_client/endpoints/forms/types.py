
from collections.abc import Sequence
from typing import Literal, TypedDict

DisplayMemberAs = Literal[
    "MEMBER_NAME",
    "MEMBER_NAME_THEN_ALIAS",
    "ALIAS_THEN_MEMBER_NAME",
]

Members = str | Sequence[str]
"""One member name, or several."""


class FormGridInfo(TypedDict):
    """Layout of the form: which dimensions sit on which axis."""

    cubeName: str
    """Cube (plan type) the form reads from, e.g. ``"Plan1"``."""
    povDimNames: list[str]
    """Dimensions fixed by the form's POV, e.g. ``["Scenario", "Version"]``."""
    pageDimNames: list[str]
    """Dimensions selectable with ``page``, e.g. ``["Entity"]``."""
    allowedPageMembersByDim: dict[str, list[str]]
    """Valid ``page`` members per page dimension."""
    rowDimNames: list[str]
    """Row dimensions, in the order of ``FormRow.headers``."""
    columnDimNames: list[str]
    """Column dimensions, in the order of ``FormData.columns``."""


class FormRow(TypedDict):
    headers: list[str]
    """One member per row dimension, aligned with ``gridInfo.rowDimNames``."""
    data: list[str]
    """One value per column, aligned with ``FormData.columns``.

    Values are strings as PBCS returns them, e.g. ``"120"``; an empty
    string is an empty cell (#Missing). Convert them as your form needs.
    """


class FormData(TypedDict):
    """JSON grid returned by ``FormsEndpoint.export_data``.

    With ``fields``, only the requested keys are present (plus ``gridInfo``).

    Reading cell ``(r, c)``::

        row = result["rows"][r]
        row_members = dict(zip(result["gridInfo"]["rowDimNames"], row["headers"]))
        col_members = {
            dim: result["columns"][i][c]
            for i, dim in enumerate(result["gridInfo"]["columnDimNames"])
        }
        value = row["data"][c]
    """

    gridInfo: FormGridInfo
    pov: list[str]
    """Members of ``gridInfo.povDimNames`` followed by the selected page
    members, e.g. ``["Plan", "Working", "410"]``. The page members are
    only included when rows are returned."""
    rows: list[FormRow]
    columns: list[list[str]]
    """One list per column dimension (not per column): ``columns[i][c]`` is
    the member of ``gridInfo.columnDimNames[i]`` in column ``c``. Spacer
    columns use ``" "``."""
