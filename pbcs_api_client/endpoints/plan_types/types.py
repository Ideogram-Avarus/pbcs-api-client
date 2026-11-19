
from typing import Literal, NotRequired, TypedDict

DateFormat = Literal[
    "MM-DD-YYYY",
    "DD-MM-YYYY",
    "YYYY-MM-DD",
    "MM/DD/YYYY",
    "DD/MM/YYYY",
    "YYYY/MM/DD",
]
"""Format of the date values in an imported grid."""

CellValue = str | float
"""A cell value to import, e.g. ``1200``, ``"1200"``, ``"70%"``, a Smart
List label or a date. ``"#missing"`` clears the cell."""


class PlanTypeDataRow(TypedDict):
    headers: list[str]
    """One member per row dimension, e.g. ``["4110"]``. Every row has the
    same row dimensions, in the same order."""
    data: list[CellValue]
    """One value per column, aligned with ``PlanTypeDataGrid.columns``."""


class PlanTypeDataGrid(TypedDict):
    """A data slice to import into a plan type.

    Each cell is the intersection of the ``pov`` members, its column's
    members and its row's headers, which together must name one member of
    every dimension of the plan type. ``FormData`` from
    ``FormsEndpoint.export_data`` has this shape and can be imported as is.
    """

    pov: list[str]
    """Members shared by every cell, e.g. ``["FY26", "Plan", "Working", "410"]``."""
    columns: list[list[str]]
    """One list per column dimension (not per column): ``columns[i][c]`` is
    the member of column dimension ``i`` in column ``c``, e.g.
    ``[["Jan", "Feb"]]``."""
    rows: list[PlanTypeDataRow]


class PlanTypeRejectedCell(TypedDict):
    """Why PBCS rejected a cell, with ``include_rejection_details=True``."""

    memberNames: list[str]
    """Members of the cell, e.g. ``["FY26", "Plan", "Working", "410", "Jan", "4110"]``."""
    readOnlyReasons: list[str]
    """e.g. ``["Invalid Intersection"]``."""
    otherReasons: list[str]


class PlanTypeImportResult(TypedDict):
    """Result of ``PlanTypesEndpoint.import_data``."""

    numAcceptedCells: int
    """Cells saved without errors, e.g. ``8``."""
    numUpdateCells: NotRequired[int]
    """Accepted cells whose value changed in Essbase, e.g. ``3``. Cells
    sent with the value they already had are accepted but not updated.
    Absent on instances older than the June 2025 update."""
    numRejectedCells: int
    """Cells not saved, e.g. ``4``: read-only or invalid intersections,
    invalid values, or a non-numeric value with ``aggregate=True``.
    Unknown members fail the whole request instead (HTTP 400)."""
    rejectedCells: NotRequired[list[str]]
    """The first 100 rejected cells, each as its members in brackets, e.g.
    ``"[FY26, Plan, Working, 410, Jan, 4110]"``."""
    rejectedCellsWithDetails: NotRequired[list[PlanTypeRejectedCell]]
    """Rejected cells with the reasons, with ``include_rejection_details=True``."""
