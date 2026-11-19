
from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import quote

from ..base import Endpoint
from .types import DisplayMemberAs, FormData, Members


# Oracle documents both spellings, but PBCS rejects the UPPER_SNAKE ones
# ("No DisplayMemberAs option found with the specified value.").
_DISPLAY_MEMBER_AS_LABELS: dict[str, str] = {
    "MEMBER_NAME": "Member Name",
    "MEMBER_NAME_THEN_ALIAS": "Member Name Then Alias",
    "ALIAS_THEN_MEMBER_NAME": "Alias Then Member Name",
}


def _as_list(members: Members) -> list[str]:
    return [members] if isinstance(members, str) else list(members)


class FormsEndpoint(Endpoint):
    def export_data(
        self,
        form: str,
        *,
        page: Mapping[str, str] | None = None,
        filters: Mapping[str, Members] | None = None,
        display_member_as: DisplayMemberAs | None = None,
        member_alias_delimiter: str | None = None,
        force_start_expanded: bool | None = None,
        fields: Sequence[str] | None = None,
    ) -> FormData:
        """Export the data slice defined by a form, as a JSON grid.

        ``page`` maps each page dimension to the member to export, e.g.
        ``{"Entity": "410"}``. Omit it and PBCS uses the page this
        user last selected on the form, which is easy to get wrong.

        ``filters`` maps row or column dimensions to the member(s) to keep,
        e.g. ``{"Account": ["4110", "4120"], "Period": "Jan"}``.
        Members of one dimension are OR'ed; dimensions are AND'ed.

        ``display_member_as`` with a "THEN" option joins member name and
        alias in each header, e.g. ``"410|Sales East"`` with
        ``member_alias_delimiter="|"`` (default ``":"``).

        See ``FormData`` for the response shape.

        PBCS rejects invalid page members (HTTP 400) but silently ignores
        filter members it can't use, returning the unfiltered grid. Only the
        member names are sent, so this method raises ``ValueError`` when a
        dimension in ``page`` or ``filters`` is not on the form.
        """
        params: dict[str, Any] = {}

        if page:
            params["page"] = list(page.values())
        if filters:
            params["filterMembers"] = [
                member
                for members in filters.values()
                for member in _as_list(members)
            ]
        if display_member_as is not None:
            if display_member_as not in _DISPLAY_MEMBER_AS_LABELS:
                raise ValueError(
                    f"display_member_as must be one of "
                    f"{list(_DISPLAY_MEMBER_AS_LABELS)}, got {display_member_as!r}"
                )
            params["displayMemberAs"] = _DISPLAY_MEMBER_AS_LABELS[display_member_as]
        if member_alias_delimiter is not None:
            params["memberAliasDelimiter"] = member_alias_delimiter
        if force_start_expanded is not None:
            params["forceStartExpanded"] = force_start_expanded
        if fields is not None:
            # gridInfo is needed to check the page and filter dimensions.
            params["fields"] = ",".join(dict.fromkeys([*fields, "gridInfo"]))

        result: FormData = self._pbcs.request(
            "GET",
            f"{self._application_path()}/forms/{quote(form, safe='')}/data",
            params=params,
        )

        _check_page(form, result, page)
        _check_filters(form, result, filters)
        return result


def _check_page(
    form: str, result: FormData, page: Mapping[str, str] | None
) -> None:
    if not page:
        return

    grid = result["gridInfo"]
    unknown = set(page) - set(grid["pageDimNames"])
    if unknown:
        raise ValueError(
            f"Form '{form}' has no page dimension(s) {sorted(unknown)}; "
            f"page dimensions are {grid['pageDimNames']}"
        )


def _check_filters(
    form: str, result: FormData, filters: Mapping[str, Members] | None
) -> None:
    if not filters:
        return

    grid = result["gridInfo"]
    dims = [*grid["rowDimNames"], *grid["columnDimNames"]]
    unknown = set(filters) - set(dims)
    if unknown:
        raise ValueError(
            f"Form '{form}' has no row or column dimension(s) "
            f"{sorted(unknown)}; filterable dimensions are {dims}"
        )
