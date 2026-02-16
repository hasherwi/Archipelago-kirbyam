import typing


class RegionRow(typing.NamedTuple):
    name: str
    itemReq: str
    connections: list[str]
    resources: list[str]


class ResourceRow(typing.NamedTuple):
    name: str
