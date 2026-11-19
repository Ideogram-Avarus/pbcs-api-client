
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

if TYPE_CHECKING:
    from ..pbcs import Pbcs

PLANNING_API = "HyperionPlanning/rest/v3"

# Items per request when fetching every page of a collection.
PAGE_SIZE = 500


class Endpoint:
    """Base class for endpoint groups.

    Subclass it, add methods that call ``self._pbcs.request(...)``,
    then create it in ``Pbcs.__init__``.
    """

    def __init__(self, pbcs: "Pbcs") -> None:
        self._pbcs = pbcs

    def _application_path(self) -> str:
        """Planning API path of the application set on ``Pbcs``."""
        application = self._pbcs.application
        if application is None:
            raise ValueError(
                f"{type(self).__name__} needs an application: "
                "pass application=... to Pbcs"
            )
        return f"{PLANNING_API}/applications/{quote(application, safe='')}"

    def _plan_type_path(self, plan_type: str) -> str:
        """Planning API path of a plan type (cube) of the application."""
        return f"{self._application_path()}/plantypes/{quote(plan_type, safe='')}"

    def _get_all_pages(
        self, path: str, params: dict[str, Any] | None = None
    ) -> list[Any]:
        """``items`` from every page of a collection that pages with
        ``offset``/``limit`` and reports ``hasMore``."""
        items: list[Any] = []
        while True:
            page = self._pbcs.request(
                "GET",
                path,
                params={**(params or {}), "offset": len(items), "limit": PAGE_SIZE},
            )
            # PBCS leaves out "items" when nothing matches.
            page_items: list[Any] = page.get("items", [])
            items.extend(page_items)
            if not page.get("hasMore") or not page_items:
                return items
