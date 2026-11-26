"""One seed-local link for Candy 9-12 when its copy source is not guaranteed."""
from functools import lru_cache
from typing import Any

from .data import data, load_json_data
from .traversal import SourcePolicy, TraversalGraph, compile_traversal_graph
from .traversal_data import room_traversal_targets

TARGET = "bomb_402_candy_chest"
LOCATION = "MINOR_CHEST_CANDY_CONSTELLATION_9_12"
SLOT_KEY = "candy912_linked_west_fuse"
ROM_OFFSET = 0x1006FF8
STOCK_CONFIG = b"\x00" b"19C"
LINKED_CONFIG = b"\x01" b"19C"


def needs_linked_fuse(raw: dict[str, Any], *, minor_chests: bool) -> bool:
    """Decide after all enemy assignments are final, without mutating their policy."""
    from .traversal_rules import target_applies
    if not minor_chests or data.locations[LOCATION].source_rom_offset is None:
        return False
    row = next(row for row in room_traversal_targets("block") if row["id"] == TARGET)
    return not target_applies(row, SourcePolicy(raw))


def enabled(slot_data: dict[str, Any]) -> bool:
    """Missing intent is stock for seeds prepared before this patch."""
    if SLOT_KEY in slot_data and slot_data[SLOT_KEY] is not True:
        raise ValueError("Invalid Candy 9-12 linked fuse patch contract")
    return slot_data.get(SLOT_KEY) is True


def config_bytes(linked: bool) -> bytes:
    return LINKED_CONFIG if linked else STOCK_CONFIG


@lru_cache(maxsize=1)
def graph() -> TraversalGraph:
    witness = load_json_data("candy912_normal_fuse_witness.json")
    if not isinstance(witness, dict):
        raise ValueError("Invalid Candy 9-12 linked fuse witness")
    return compile_traversal_graph(witness)


def target_graphs(row: dict[str, Any], linked: bool) -> tuple[TraversalGraph, ...]:
    return (graph(),) if row["id"] == TARGET and linked else ()
