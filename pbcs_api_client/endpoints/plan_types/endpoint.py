
from collections.abc import Sequence
from typing import Any

from ..base import Endpoint
from ..forms.types import FormData
from .types import DateFormat, PlanTypeDataGrid, PlanTypeImportResult

# Member PBCS puts in the headers of a form's spacer columns.
_SPACER = " "


class PlanTypesEndpoint(Endpoint):
    def import_data(
        self,
        plan_type: str,
        *,
        grid: PlanTypeDataGrid | FormData,
        aggregate: bool | None = None,
        date_format: DateFormat | None = None,
        strict_date_validation: bool | None = None,
        post_import_rules: Sequence[str] | None = None,
        include_rejection_details: bool | None = None,
    ) -> PlanTypeImportResult:
        """Write a grid of values into a plan type (cube), cell by cell.

        ``plan_type`` is the plan type name, e.g. ``"Plan1"``; for a grid
        exported from a form, it is ``data["gridInfo"]["cubeName"]``.

        ``grid`` holds the members and values; see ``PlanTypeDataGrid``. A
        ``FormData`` from ``forms.export_data`` can be sent back after changing
        its values: its ``gridInfo`` and spacer columns are left out.

        ``aggregate=True`` adds each value to the one in the cube instead of
        replacing it, and rejects non-numeric cells (PBCS default: replace).

        ``date_format`` is the format of date values, e.g. ``"DD/MM/YYYY"``.
        With ``strict_date_validation=False``, dates in other formats are
        accepted too (PBCS default: rejected).

        ``post_import_rules`` names business rules for PBCS to run after the
        import, e.g. ``["Calculate Revenue"]``.

        ``include_rejection_details=True`` adds why each cell was rejected.

        See ``PlanTypeImportResult`` for the response. The request writes to
        the cube directly, not through a form: no form validation or
        "Run on Save" rule runs.

        A member that doesn't exist in the plan type, or that this user
        can't access, fails the whole request with HTTP 400
        (``PbcsRequestError`` naming the members). Other cells PBCS can't
        save, e.g. read-only or invalid values, are rejected one by one
        while the others are saved, with HTTP 200, so check
        ``numRejectedCells``.
        """
        payload: dict[str, Any] = {"dataGrid": _data_grid(grid)}
        custom_params: dict[str, Any] = {}

        if aggregate is not None:
            payload["aggregateEssbaseData"] = aggregate
        if date_format is not None:
            payload["dateFormat"] = date_format
        if strict_date_validation is not None:
            payload["strictDateValidation"] = strict_date_validation
        if post_import_rules:
            custom_params["PostDataImportRuleNames"] = ", ".join(
                f'"{rule}"' if "," in rule else rule for rule in post_import_rules
            )
        if include_rejection_details is not None:
            custom_params["IncludeRejectedCellsWithDetails"] = include_rejection_details
        if custom_params:
            payload["customParams"] = custom_params

        return self._pbcs.request(
            "POST",
            f"{self._plan_type_path(plan_type)}/importdataslice",
            json=payload,
        )


def _data_grid(grid: PlanTypeDataGrid | FormData) -> dict[str, Any]:
    """The ``dataGrid`` to send: ``pov``, ``columns`` and ``rows`` only,
    without spacer columns, after checking the grid is rectangular."""
    columns = grid["columns"]
    rows = grid["rows"]

    if not columns or not columns[0]:
        raise ValueError("grid has no columns")
    width = len(columns[0])
    if any(len(members) != width for members in columns):
        raise ValueError(
            f"every list in grid['columns'] needs one member per column; "
            f"got lengths {[len(members) for members in columns]}"
        )
    if not rows:
        raise ValueError("grid has no rows")
    header_count = len(rows[0]["headers"])
    for index, row in enumerate(rows):
        if len(row["headers"]) != header_count:
            raise ValueError(
                f"grid row {index} has {len(row['headers'])} headers; "
                f"row 0 has {header_count}"
            )
        if len(row["data"]) != width:
            raise ValueError(
                f"grid row {index} {row['headers']} has {len(row['data'])} "
                f"values for {width} columns"
            )

    keep = [
        c for c in range(width)
        if any(members[c] != _SPACER for members in columns)
    ]
    return {
        "pov": list(grid["pov"]),
        "columns": [[members[c] for c in keep] for members in columns],
        "rows": [
            {"headers": list(row["headers"]), "data": [row["data"][c] for c in keep]}
            for row in rows
        ],
    }
