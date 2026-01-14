from __future__ import annotations

from worlds.kirbyam.data_loader import load_kirbyam_data
from .bases import KirbyAMTestBase


class TestKirbyAMPOCSmoke(KirbyAMTestBase):
    def test_can_generate(self) -> None:
        self.world_setup()

    def test_completion_condition_exists(self) -> None:
        self.world_setup()
        assert self.multiworld.completion_condition[self.player] is not None

    def test_has_expected_locations(self) -> None:
        self.world_setup()

        data = load_kirbyam_data()
        expected = {
            row["name"]
            for row in data.locations
            if "poc" in row.get("tags", []) and "name" in row
        }

        world_locs = {loc.name for loc in self.multiworld.get_locations(self.player)}
        missing = expected - world_locs
        assert not missing, f"POC locations missing from world: {sorted(missing)}"
