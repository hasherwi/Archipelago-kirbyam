from __future__ import annotations

from worlds.kirbyam.data_loader import load_kirbyam_data


def _assert_unique(values: list[str], message: str) -> None:
    assert len(values) == len(set(values)), message


def test_keys_unique_and_non_empty() -> None:
    data = load_kirbyam_data()

    item_keys = [row["key"] for row in data.items if "key" in row]
    loc_keys = [row["key"] for row in data.locations if "key" in row]
    goal_keys = [row["key"] for row in data.goals if "key" in row]

    _assert_unique(item_keys, "Duplicate keys found in items.yaml")
    _assert_unique(loc_keys, "Duplicate keys found in locations.yaml")
    _assert_unique(goal_keys, "Duplicate keys found in goals.yaml")


def test_names_unique_within_each_file() -> None:
    data = load_kirbyam_data()

    item_names = [row["name"] for row in data.items if "name" in row]
    loc_names = [row["name"] for row in data.locations if "name" in row]
    goal_names = [row["name"] for row in data.goals if "name" in row]

    _assert_unique(item_names, "Duplicate item names found in items.yaml (breaks name->id mapping)")
    _assert_unique(loc_names, "Duplicate location names found in locations.yaml (breaks name->id mapping)")
    _assert_unique(goal_names, "Duplicate goal names found in goals.yaml")
