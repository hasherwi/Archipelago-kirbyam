from __future__ import annotations

from worlds.kirbyam.data_loader import load_kirbyam_data
from .bases import KirbyAMTestBase


class TestKirbyAMPOCItems(KirbyAMTestBase):
    def test_has_poc_items_in_yaml(self) -> None:
        data = load_kirbyam_data()
        poc_items = [row["name"] for row in data.items if "poc" in row.get("tags", [])]
        assert len(poc_items) > 0, "No items tagged 'poc' in items.yaml"

    def test_itempool_contains_all_poc_items(self) -> None:
        self.world_setup()

        data = load_kirbyam_data()
        expected = {row["name"] for row in data.items if "poc" in row.get("tags", []) and "name" in row}

        pool = {item.name for item in self.multiworld.itempool if item.player == self.player}

        missing = expected - pool
        assert not missing, f"POC items missing from itempool: {sorted(missing)}"
