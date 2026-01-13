from __future__ import annotations

from typing import Any, Dict, Optional, List

from BaseClasses import Item, ItemClassification, Location, Region, Tutorial
from worlds.AutoWorld import WebWorld, World
from worlds.celeste_open_world import data

from .data_loader import load_kirbyam_data, KirbyAMData
from .id_map import build_id_map

GAME_NAME = "Kirby & The Amazing Mirror"

ORIGIN_REGION = "Menu"


class KirbyAMWebWorld(WebWorld):
    game = GAME_NAME
    game_info_languages = ["en"]
    tutorials = [
        Tutorial(
            tutorial_name="Setup Guide",
            description="How to set up and play Kirby & The Amazing Mirror in Archipelago (POC).",
            language="English",
            file_name="setup_en.md",
            link="setup/en",
            authors=["Harrison"]
        )
    ]
    bug_report_page = None


class KirbyAMWorld(World):
    _data: KirbyAMData
    _poc_location_names: List[str]
    _poc_item_names: List[str]
    
    game = GAME_NAME
    web = KirbyAMWebWorld()

    origin_region_name = ORIGIN_REGION
    
    # Deterministic base IDs. Do not change once you have public releases.
    _base_location_id = 23_450_000
    _base_item_id = 23_460_000

    # These are populated from YAML in generate_early()
    item_name_to_id: Dict[str, int] = {}
    location_name_to_id: Dict[str, int] = {}
    
    @staticmethod
    def _class_from_str(value: str | None) -> ItemClassification:
        if not value:
            return ItemClassification.filler
        v = value.strip().lower()
        if v == "progression":
            return ItemClassification.progression
        if v == "useful":
            return ItemClassification.useful
        if v == "trap":
            return ItemClassification.trap
        # default
        return ItemClassification.filler

    def generate_early(self) -> None:
        self._data = load_kirbyam_data()
        data = self._data

        # Build key->id maps FIRST
        item_key_to_id = build_id_map(
            (row["key"] for row in data.items if "key" in row),
            base_id=23_460_000,
            namespace="kirbyam:item",
        )
        loc_key_to_id = build_id_map(
            (row["key"] for row in data.locations if "key" in row),
            base_id=23_450_000,
            namespace="kirbyam:location",
        )

        # Then build name->id maps from those
        self.item_name_to_id = {row["name"]: item_key_to_id[row["key"]] for row in data.items if "key" in row and "name" in row}
        self.location_name_to_id = {row["name"]: loc_key_to_id[row["key"]] for row in data.locations if "key" in row and "name" in row}

        # Then compute POC lists
        self._poc_location_names = [row["name"] for row in data.locations if "poc" in row.get("tags", []) and "name" in row]
        self._poc_item_names = [row["name"] for row in data.items if "poc" in row.get("tags", []) and "name" in row]

        if not self._poc_location_names:
            raise ValueError("No locations tagged 'poc' found in locations.yaml")
        if not self._poc_item_names:
            raise ValueError("No items tagged 'poc' found in items.yaml")

        # Validate that POC names exist in the maps we just built
        missing_loc_ids = [n for n in self._poc_location_names if n not in self.location_name_to_id]
        missing_item_ids = [n for n in self._poc_item_names if n not in self.item_name_to_id]
        if missing_loc_ids:
            raise ValueError(f"POC locations missing from location_name_to_id: {missing_loc_ids}")
        if missing_item_ids:
            raise ValueError(f"POC items missing from item_name_to_id: {missing_item_ids}")
        
        poc_loc_count = len(self._poc_location_names)
        poc_item_count = len(self._poc_item_names)

        if poc_item_count != poc_loc_count:
            raise ValueError(
                "POC requires item count == location count. "
                f"poc_items={poc_item_count} poc_locations={poc_loc_count}. "
                "Tag additional items/locations with 'poc' to fix."
            )

    def create_regions(self) -> None:
        menu = Region(self.origin_region_name, self.player, self.multiworld)
        self.multiworld.regions.append(menu)

        victory_event = Location(self.player, "Victory", None, menu)
        victory_event.place_locked_item(self._create_event_item("Victory"))
        menu.locations.append(victory_event)

        main = Region("Main Area", self.player, self.multiworld)
        branch = Region("Test Branch", self.player, self.multiworld)
        
        self.multiworld.regions.append(main)
        self.multiworld.regions.append(branch)

        menu.connect(main, "To Main Area")
        main.connect(branch, "To Test Branch")
        
        # POC locations in Main Area.
        #
        # These are intentionally minimal and exist to validate:
        # - name->id mapping from YAML
        # - region/location registration
        # - basic seed generation
        #
        # Once Phase 2 starts, this section will be replaced by data-driven region
        # construction and real location placement.

        data = self._data
        poc_locations = self._poc_location_names

        missing = [n for n in poc_locations if n not in self.location_name_to_id]
        if missing:
            raise ValueError(f"POC locations missing from locations.yaml: {missing}")
        
        if not poc_locations:
            raise ValueError("No locations tagged 'poc' found in locations.yaml")

        # Example: first N go in Main Area, remainder in Test Branch
        split = max(1, len(poc_locations) // 2)
        main_locs = poc_locations[:split]
        branch_locs = poc_locations[split:]

        for loc_name in main_locs:
            main.locations.append(Location(self.player, loc_name, self.location_name_to_id[loc_name], main))

        for loc_name in branch_locs:
            branch.locations.append(Location(self.player, loc_name, self.location_name_to_id[loc_name], branch))

    def create_items(self) -> None:
        for item_name in self._poc_item_names:
            self.multiworld.itempool.append(self.create_item(item_name))

    def set_rules(self) -> None:
        self.multiworld.completion_condition[self.player] = lambda state: state.has("Victory", self.player)

    def create_item(self, name: str) -> Item:
        item_id = self.item_name_to_id[name]

        # Look up classification from YAML (default filler)
        row = next((r for r in self._data.items if r["name"] == name), None)
        classification = self._class_from_str(row.get("classification") if row else None)

        return Item(name, classification, item_id, self.player)

    def _create_event_item(self, name: str) -> Item:
        return Item(name, ItemClassification.progression, None, self.player)

    def fill_slot_data(self) -> Dict[str, Any]:
        # Keep minimal until the BizHawk client is implemented.
        return {}