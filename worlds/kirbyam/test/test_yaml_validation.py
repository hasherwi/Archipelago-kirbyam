from __future__ import annotations

from worlds.kirbyam.data_loader import load_kirbyam_data


def test_names_unique_within_items_and_locations() -> None:
    data = load_kirbyam_data()

    item_names = [row["name"] for row in data.items if "name" in row]
    loc_names = [row["name"] for row in data.locations if "name" in row]
    goal_names = [row["name"] for row in data.goals if "name" in row]

    assert len(item_names) == len(set(item_names)), "Duplicate item names found in items.yaml"
    assert len(loc_names) == len(set(loc_names)), "Duplicate location names found in locations.yaml"
    assert len(goal_names) == len(set(goal_names)), "Duplicate goal names found in goals.yaml"
