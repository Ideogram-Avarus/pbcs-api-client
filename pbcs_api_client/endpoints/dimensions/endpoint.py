
from typing import Any
from urllib.parse import quote

from ..base import Endpoint
from .types import Dimension, DimensionSummary


class DimensionsEndpoint(Endpoint):
    def list(self, plan_type: str) -> list[DimensionSummary]:
        """Dimensions of a plan type of the application.

        ``plan_type`` is the plan type (cube) name, e.g. ``"Plan1"``. PBCS
        has no request for the dimensions of the whole application.

        See ``DimensionSummary`` for each item. Use ``get`` for a dimension's
        members.
        """
        items = self._get_all_pages(
            f"{self._plan_type_path(plan_type)}/dimensions"
        )
        for item in items:
            item.pop("links", None)
        return items

    def get(
        self,
        dimension: str,
        *,
        plan_type: str,
        alias_table: str | None = None,
    ) -> Dimension:
        """A dimension with its whole member hierarchy, in one request.

        ``dimension`` is the dimension name, e.g. ``"Entity"``, and
        ``plan_type`` a plan type that uses it, e.g. ``"Plan1"``.

        ``alias_table`` picks the alias table for ``alias`` and ``aliasPath``,
        e.g. ``"English"``; PBCS uses its default table otherwise.

        See ``Dimension`` for the response shape. PBCS returns HTTP 404 for
        an unknown dimension or plan type, and HTTP 400 for an unknown alias
        table.
        """
        params: dict[str, Any] = {}
        if alias_table is not None:
            params["aliasTableName"] = alias_table

        result = self._pbcs.request(
            "GET",
            f"{self._plan_type_path(plan_type)}/dimensions/{quote(dimension, safe='')}",
            params=params,
        )
        result.pop("links", None)
        return result
