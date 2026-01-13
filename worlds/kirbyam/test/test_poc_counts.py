from __future__ import annotations

from worlds.kirbyam.data_loader import load_kirbyam_data


def test_poc_item_count_matches_poc_location_count() -> None:
    data = load_kirbyam_data()
    poc_items = [row["name"] for row in data.items if "poc" in row.get("tags", [])]
    poc_locations = [row["name"] for row in data.locations if "poc" in row.get("tags", [])]

    assert len(poc_items) == len(poc_locations), (
        f"POC requires item count == location count "
        f"(poc_items={len(poc_items)}, poc_locations={len(poc_locations)})"
    )
