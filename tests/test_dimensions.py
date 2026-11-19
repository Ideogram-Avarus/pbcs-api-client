"""DimensionsEndpoint against the PBCS test instance. Read-only requests only.

The plan type and dimension come from the PBCS_TEST_* settings in .env.
"""

from collections.abc import Iterator

import pytest

from conftest import setting
from pbcs_api_client import Pbcs, PbcsRequestError
from pbcs_api_client.endpoints import base
from pbcs_api_client.endpoints.dimensions import Dimension, Member


@pytest.fixture(scope="module")
def plan_type() -> str:
    return setting("PBCS_TEST_PLAN_TYPE")


@pytest.fixture(scope="module")
def dimension_name() -> str:
    return setting("PBCS_TEST_DIMENSION")


@pytest.fixture(scope="module")
def dimension(pbcs: Pbcs, plan_type: str, dimension_name: str) -> Dimension:
    return pbcs.dimensions.get(dimension_name, plan_type=plan_type)


def walk(members: list[Member]) -> Iterator[Member]:
    for member in members:
        yield member
        yield from walk(member.get("children", []))


def test_list_includes_configured_dimension(
    pbcs: Pbcs, plan_type: str, dimension_name: str
) -> None:
    dimensions = pbcs.dimensions.list(plan_type)

    assert dimension_name in [d["name"] for d in dimensions]
    assert all(plan_type in d["usedIn"] for d in dimensions)
    assert all("links" not in d for d in dimensions)


def test_list_fetches_every_page(
    pbcs: Pbcs, plan_type: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    expected = [d["name"] for d in pbcs.dimensions.list(plan_type)]
    monkeypatch.setattr(base, "PAGE_SIZE", 3)

    names = [d["name"] for d in pbcs.dimensions.list(plan_type)]

    assert len(expected) > 3
    assert names == expected


def test_get_returns_member_hierarchy(
    dimension: Dimension, dimension_name: str
) -> None:
    assert dimension["name"] == dimension_name
    assert dimension["children"]
    assert "links" not in dimension

    members = list(walk(dimension["children"]))
    assert all(m["dimName"] == dimension_name for m in members)
    assert {m["generation"] for m in dimension["children"]} == {2}


def test_get_children_point_to_their_parent(dimension: Dimension) -> None:
    for parent in walk(dimension["children"]):
        for child in parent.get("children", []):
            assert child["parentName"] == parent["name"]
            assert child["path"] == f"{parent['path']}/{child['name']}"
            assert child["generation"] == parent["generation"] + 1


def test_get_level_0_members_have_no_children(dimension: Dimension) -> None:
    for member in walk(dimension["children"]):
        assert (member["level"] == 0) == (not member.get("children"))


def test_unknown_dimension_is_rejected_by_pbcs(pbcs: Pbcs, plan_type: str) -> None:
    with pytest.raises(PbcsRequestError, match="404"):
        pbcs.dimensions.get("__pytest_missing__", plan_type=plan_type)


def test_unknown_plan_type_is_rejected_by_pbcs(pbcs: Pbcs) -> None:
    with pytest.raises(PbcsRequestError, match="404"):
        pbcs.dimensions.list("__pytest_missing__")


def test_unknown_alias_table_is_rejected_by_pbcs(
    pbcs: Pbcs, plan_type: str, dimension_name: str
) -> None:
    with pytest.raises(PbcsRequestError, match="400"):
        pbcs.dimensions.get(
            dimension_name, plan_type=plan_type, alias_table="__pytest_missing__"
        )
