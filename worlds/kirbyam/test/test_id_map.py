from __future__ import annotations

from worlds.kirbyam.data_loader import load_kirbyam_data
from worlds.kirbyam.id_map import build_id_map


def test_id_map_no_collisions() -> None:
    data = load_kirbyam_data()

    item_keys = [row["key"] for row in data.items if "key" in row]
    loc_keys = [row["key"] for row in data.locations if "key" in row]

    item_map = build_id_map(item_keys, 23_460_000, "kirbyam:item")
    loc_map = build_id_map(loc_keys, 23_450_000, "kirbyam:location")

    assert len(item_map) == len(set(item_map.values()))
    assert len(loc_map) == len(set(loc_map.values()))
