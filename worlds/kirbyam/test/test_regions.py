from __future__ import annotations

from .bases import KirbyAMTestBase


class TestKirbyAMRegions(KirbyAMTestBase):
    def test_origin_region_exists(self) -> None:
        self.world_setup()
        region_names = {r.name for r in self.multiworld.regions if r.player == self.player}
        assert "Menu" in region_names
        
    def test_minimal_regions_exist(self) -> None:
        self.world_setup()
        region_names = {r.name for r in self.multiworld.regions if r.player == self.player}
        assert "Main Area" in region_names
        assert "Test Branch" in region_names
    
    def test_branch_reachable_with_no_items(self) -> None:
        self.world_setup()
        state = self.multiworld.state
        assert state.can_reach("Test Branch", "Region", self.player)


