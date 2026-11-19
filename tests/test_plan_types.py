
"""PlanTypesEndpoint.

The grid checks run offline. The integration tests use the form from the
PBCS_TEST_* settings in .env: the unknown members test sends a grid PBCS
refuses, and the round trip test, which writes the form's values back
unchanged, only runs with PBCS_TEST_ALLOW_WRITES=1.
"""

from typing import Any

import pytest

from conftest import setting
from pbcs_api_client import BasicAuthProvider, Pbcs, PbcsRequestError
from pbcs_api_client.endpoints.forms import FormData
from pbcs_api_client.endpoints.plan_types import PlanTypeDataGrid

MISSING_MEMBER = "__pytest_missing__"


def grid(**changes: Any) -> PlanTypeDataGrid:
    base: dict[str, Any] = {
        "pov": ["FY26", "Plan", "Working", "410"],
        "columns": [["Jan", "Feb"]],
        "rows": [
            {"headers": ["4110"], "data": [1000, "1200"]},
            {"headers": ["4120"], "data": ["500", "#missing"]},
        ],
    }
    return {**base, **changes}  # type: ignore[return-value]


@pytest.fixture
def offline() -> Pbcs:
    return Pbcs(
        "https://pbcs.invalid", BasicAuthProvider("user", "secret"), application="App"
    )


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"columns": []}, "no columns"),
        ({"columns": [["Jan", "Feb"], ["Plan"]]}, "one member per column"),
        ({"rows": []}, "no rows"),
        (
            {"rows": [{"headers": ["4110"], "data": ["1", "2"]},
                      {"headers": ["4120", "P_000"], "data": ["1", "2"]}]},
            "row 1 has 2 headers",
        ),
        ({"rows": [{"headers": ["4110"], "data": ["1"]}]}, "1 values for 2 columns"),
    ],
)
def test_malformed_grid_is_rejected_before_sending(
    offline: Pbcs, changes: dict[str, Any], message: str
) -> None:
    # pbcs.invalid never resolves, so reaching PBCS would raise PbcsRequestError.
    with pytest.raises(ValueError, match=message):
        offline.plan_types.import_data("Plan1", grid=grid(**changes))


@pytest.fixture(scope="module")
def form_data(pbcs: Pbcs) -> FormData:
    return pbcs.forms.export_data(
        setting("PBCS_TEST_FORM"),
        page={setting("PBCS_TEST_PAGE_DIMENSION"): setting("PBCS_TEST_PAGE_MEMBER")},
    )


def cell_count(data: FormData) -> int:
    width = sum(
        any(members[c] != " " for members in data["columns"])
        for c in range(len(data["columns"][0]))
    )
    return width * len(data["rows"])


def test_unknown_members_fail_the_whole_request(
    pbcs: Pbcs, form_data: FormData
) -> None:
    row = form_data["rows"][0]
    data: FormData = {
        **form_data,
        "rows": [{"headers": [MISSING_MEMBER] * len(row["headers"]), "data": row["data"]}],
    }

    # Not a per-cell rejection: PBCS refuses the request and names the members.
    with pytest.raises(PbcsRequestError, match=f"400.*{MISSING_MEMBER}"):
        pbcs.plan_types.import_data(form_data["gridInfo"]["cubeName"], grid=data)


def test_form_values_written_back_are_unchanged(
    pbcs: Pbcs, form_data: FormData
) -> None:
    setting("PBCS_TEST_ALLOW_WRITES")

    result = pbcs.plan_types.import_data(
        form_data["gridInfo"]["cubeName"], grid=form_data
    )

    assert result["numAcceptedCells"] + result["numRejectedCells"] == cell_count(form_data)
    assert result["numAcceptedCells"] > 0
    assert result.get("numUpdateCells", 0) == 0
