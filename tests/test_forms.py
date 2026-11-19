
"""FormsEndpoint against the PBCS test instance. Read-only requests only.

The form and its dimensions come from the PBCS_TEST_* settings in .env.

Note: sending a page member also updates the page PBCS remembers for this
user on the form, so every test here sends the page explicitly.
"""

from dataclasses import dataclass

import pytest

from conftest import setting
from pbcs_api_client import Pbcs, PbcsRequestError
from pbcs_api_client.endpoints.forms import DisplayMemberAs, FormData


@dataclass(frozen=True)
class FormCase:
    name: str
    page_dimension: str
    page_member: str
    row_dimension: str
    column_dimension: str
    column_member: str

    @property
    def page(self) -> dict[str, str]:
        return {self.page_dimension: self.page_member}


@pytest.fixture(scope="module")
def form() -> FormCase:
    return FormCase(
        name=setting("PBCS_TEST_FORM"),
        page_dimension=setting("PBCS_TEST_PAGE_DIMENSION"),
        page_member=setting("PBCS_TEST_PAGE_MEMBER"),
        row_dimension=setting("PBCS_TEST_ROW_DIMENSION"),
        column_dimension=setting("PBCS_TEST_COLUMN_DIMENSION"),
        column_member=setting("PBCS_TEST_COLUMN_MEMBER"),
    )


def column_members(result: FormData, dimension: str) -> set[str]:
    index = result["gridInfo"]["columnDimNames"].index(dimension)
    return set(result["columns"][index]) - {" "}


def row_members(result: FormData, dimension: str) -> set[str]:
    index = result["gridInfo"]["rowDimNames"].index(dimension)
    return {row["headers"][index] for row in result["rows"]}


def test_discovery_returns_grid_layout_only(pbcs: Pbcs, form: FormCase) -> None:
    result = pbcs.forms.export_data(form.name, fields=["gridInfo"])

    grid = result["gridInfo"]
    assert grid["pageDimNames"] == [form.page_dimension]
    assert form.row_dimension in grid["rowDimNames"]
    assert form.column_dimension in grid["columnDimNames"]
    assert form.page_member in grid["allowedPageMembersByDim"][form.page_dimension]
    assert "rows" not in result


def test_page_member_is_applied(pbcs: Pbcs, form: FormCase) -> None:
    result = pbcs.forms.export_data(form.name, page=form.page)

    assert form.page_member in result["pov"]
    assert result["rows"]
    for row in result["rows"]:
        assert len(row["data"]) == len(result["columns"][0])


def test_filter_on_row_dimension(pbcs: Pbcs, form: FormCase) -> None:
    unfiltered = pbcs.forms.export_data(form.name, page=form.page)
    wanted = sorted(row_members(unfiltered, form.row_dimension))[:2]

    result = pbcs.forms.export_data(
        form.name, page=form.page, filters={form.row_dimension: wanted}
    )

    assert row_members(result, form.row_dimension) == set(wanted)


def test_filter_on_column_dimension(pbcs: Pbcs, form: FormCase) -> None:
    result = pbcs.forms.export_data(
        form.name, page=form.page, filters={form.column_dimension: form.column_member}
    )

    assert column_members(result, form.column_dimension) == {form.column_member}


def test_filters_on_several_dimensions_combine(pbcs: Pbcs, form: FormCase) -> None:
    unfiltered = pbcs.forms.export_data(form.name, page=form.page)
    row_member = sorted(row_members(unfiltered, form.row_dimension))[0]

    result = pbcs.forms.export_data(
        form.name,
        page=form.page,
        filters={
            form.row_dimension: row_member,
            form.column_dimension: form.column_member,
        },
    )

    assert row_members(result, form.row_dimension) == {row_member}
    assert column_members(result, form.column_dimension) == {form.column_member}


def test_unknown_filter_dimension_is_rejected(pbcs: Pbcs, form: FormCase) -> None:
    with pytest.raises(ValueError, match="no row or column dimension"):
        pbcs.forms.export_data(form.name, page=form.page, filters={"NotADim": "X"})


def test_unknown_page_dimension_is_rejected(pbcs: Pbcs, form: FormCase) -> None:
    with pytest.raises(ValueError, match="no page dimension"):
        pbcs.forms.export_data(form.name, page={"NotADim": form.page_member})


@pytest.mark.parametrize("kind", ["unknown member", "member of another dimension"])
def test_invalid_page_member_is_rejected_by_pbcs(
    pbcs: Pbcs, form: FormCase, kind: str
) -> None:
    member = "__pytest_missing__" if kind == "unknown member" else form.column_member

    # Unknown members and members of other dimensions are both HTTP 400.
    with pytest.raises(PbcsRequestError, match="400"):
        pbcs.forms.export_data(form.name, page={form.page_dimension: member})


def test_discovery_with_page_keeps_rows_out(pbcs: Pbcs, form: FormCase) -> None:
    result = pbcs.forms.export_data(
        form.name, page=form.page, fields=["gridInfo", "pov"]
    )

    assert "rows" not in result
    assert result["gridInfo"]["pageDimNames"] == [form.page_dimension]


@pytest.mark.parametrize(
    "display_member_as",
    ["MEMBER_NAME", "MEMBER_NAME_THEN_ALIAS", "ALIAS_THEN_MEMBER_NAME"],
)
def test_display_member_as_is_accepted(
    pbcs: Pbcs, form: FormCase, display_member_as: DisplayMemberAs
) -> None:
    result = pbcs.forms.export_data(
        form.name,
        page=form.page,
        display_member_as=display_member_as,
        member_alias_delimiter="|",
        fields=["rows"],
    )

    headers = [h for row in result["rows"] for h in row["headers"]]
    if display_member_as == "MEMBER_NAME":
        assert not any("|" in h for h in headers)
    else:
        assert all("|" in h for h in headers)


def test_unknown_display_member_as_is_rejected(pbcs: Pbcs, form: FormCase) -> None:
    with pytest.raises(ValueError, match="display_member_as"):
        pbcs.forms.export_data(form.name, display_member_as="ALIAS")  # type: ignore[arg-type]
