from __future__ import annotations

from .bases import KirbyAMTestBase


class TestKirbyAMRegions(KirbyAMTestBase):
    def test_origin_region_exists(self) -> None:
        self.world_setup()
        region_names = {r.name for r in self.multiworld.regions if r.player == self.player}
        assert "Menu" in region_names
