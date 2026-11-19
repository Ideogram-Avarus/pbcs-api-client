
from typing import NotRequired, TypedDict


class DimensionSummary(TypedDict):
    """A dimension as listed by ``DimensionsEndpoint.list``."""

    name: str
    """Dimension name, e.g. ``"Entity"``."""
    alias: NotRequired[str]
    """Alias in the default alias table, e.g. ``"Entities"``. Absent when
    the dimension has none."""
    id: str
    """Unique ID, e.g. ``"b657a117-26f4-4539-bb36-ce5a13e86631"``."""
    path: str
    """``"/"`` followed by the name, e.g. ``"/Entity"``."""
    displayPath: str
    dimName: str
    """Same as ``name``."""
    dimType: str
    """Kind of dimension, e.g. ``"Account"``, ``"Period"``, ``"Year"``,
    ``"Scenario"``, ``"Version"``, ``"Entity"`` or ``"Custom"``."""
    density: str
    """``"Dense"`` or ``"Sparse"``."""
    level: int
    """Depth of the hierarchy below the dimension, e.g. ``3``."""
    generation: int
    """Always ``1`` for a dimension."""
    numMembers: int
    """Number of members, e.g. ``140``."""
    usedIn: list[str]
    """Plan types that use the dimension, e.g. ``["Plan1", "Plan2"]``."""
    approvalDimType: str
    """Role in approvals, e.g. ``"None"``, ``"Primary"`` or ``"Context"``."""
    baseDimension: bool
    enforceSecurity: bool
    """Whether member access permissions apply."""
    evaluationOrder: int
    """Position in the plan type's evaluation order, e.g. ``2``."""
    objectType: str
    """Always ``"Dimension"``."""
    objectTypeId: int
    modified: str
    """When the dimension was last changed, as PBCS formats it, e.g.
    ``"10/8/26 2:18 PM"``."""
    modifiedBy: str
    """User who last changed the dimension, e.g. ``"user@example.com"``."""


class Member(TypedDict):
    """A member in ``Dimension.children``, with its own ``children``.

    The keys depend on the dimension type: Account members also have
    ``accountType``, ``timeBalance`` and ``skipValue``, for example. Only the
    keys PBCS has been seen to return are listed here.
    """

    name: str
    """Member name, e.g. ``"410"``."""
    alias: NotRequired[str]
    """Alias in the requested alias table, e.g. ``"Sales East"``. Absent
    when the member has none."""
    description: NotRequired[str]
    id: str
    """Unique ID, e.g. ``"1ad12c5a-b1f8-495d-a212-afbf4b431258"``."""
    path: str
    """Member names from the dimension down, e.g. ``"/Entity/Total/410"``."""
    displayPath: str
    aliasPath: str
    """Aliases from the dimension down, using the name where a member has no
    alias, e.g. ``"/Entity/Total Entities/Sales East"``."""
    dimName: str
    """Dimension of the member, e.g. ``"Entity"``."""
    parentId: str
    """``id`` of the parent member, or of the dimension for top members."""
    parentName: str
    """Name of the parent member, e.g. ``"Total"``, or the dimension name for
    top members."""
    oldName: str
    """Name before the latest rename; same as ``name`` if never renamed."""
    children: NotRequired[list["Member"]]
    """Child members, in outline order. Absent on level 0 members."""
    level: int
    """``0`` for members without children, increasing towards the top."""
    generation: int
    """``2`` for top members (the dimension is ``1``), increasing
    downwards."""
    usedIn: list[str]
    """Plan types the member is used in, e.g. ``["Plan1"]``."""
    objectType: str
    """Kind of member, e.g. ``"Account"``, ``"Entity"``, or
    ``"User Defined Member"`` in custom dimensions."""
    objectTypeId: int
    dataStorage: str
    """E.g. ``"Store Data"``, ``"Never Share"``, ``"Dynamic Calc"``,
    ``"Dynamic Calc and Store"``, ``"Label Only"`` or ``"Shared"``."""
    dataType: str
    """E.g. ``"Unspecified"``, ``"Currency"``, ``"Percentage"``, ``"Text"``
    or ``"Enumeration"``."""
    consolidationOperator: str
    """Operator used to roll up into the parent, e.g. ``"+"``, ``"-"`` or
    ``"~"`` (ignore)."""
    twoPass: bool
    hasMbrFormula: bool
    formula: NotRequired[str]
    """Member formula, e.g. ``'"Units" * "Price";'``. Absent without one."""
    effectiveFormula: NotRequired[str]
    """Formula that applies, own or inherited, e.g. ``"#MISSING;"``."""
    udas: NotRequired[list[str]]
    """User-defined attributes, e.g. ``["NEGATIVE"]``."""
    accountType: NotRequired[str]
    """Account members only, e.g. ``"Revenue"``, ``"Expense"`` or
    ``"Asset"``."""
    timeBalance: NotRequired[str]
    """Account members only, e.g. ``"None"``, ``"First"`` or ``"Balance"``."""
    skipValue: NotRequired[str]
    """Account members only, e.g. ``"None"``, ``"Missing"`` or ``"Zeros"``."""
    valid: bool
    invalidDueToValidIntersection: bool


class Dimension(DimensionSummary):
    """A dimension with its whole member hierarchy, returned by
    ``DimensionsEndpoint.get``.

    Walking every member::

        def walk(members: list[Member]) -> Iterator[Member]:
            for member in members:
                yield member
                yield from walk(member.get("children", []))

        level0 = [m["name"] for m in walk(dim["children"]) if m["level"] == 0]
    """

    children: list[Member]
    """Top members of the dimension, each with its own ``children``."""
    valid: bool
    invalidDueToValidIntersection: bool
