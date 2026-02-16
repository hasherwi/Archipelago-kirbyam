import typing

from BaseClasses import Item


class ItemData(typing.NamedTuple):
    code: int
    progression: bool = True


class ChecksFinderItem(Item):
    game: str = "ChecksFinder"


item_table = {
    "Map Width": ItemData(80000),
    "Map Height": ItemData(80001),
    "Map Bombs": ItemData(80002),
}

lookup_id_to_name: dict[int, str] = {data.code: item_name for item_name, data in item_table.items()}
