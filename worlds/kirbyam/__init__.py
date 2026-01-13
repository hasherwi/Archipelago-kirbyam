from __future__ import annotations

from typing import Any, Dict, Optional

from BaseClasses import Item, ItemClassification, Location, Region, Tutorial
from worlds.AutoWorld import WebWorld, World

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
    
    game = GAME_NAME
    web = KirbyAMWebWorld()

    origin_region_name = ORIGIN_REGION
    
    # Deterministic base IDs. Do not change once you have public releases.
    _base_location_id = 23_450_000
    _base_item_id = 23_460_000

    # These are populated from YAML in generate_early()
    item_name_to_id: Dict[str, int] = {}
    location_name_to_id: Dict[str, int] = {}

    def generate_early(self) -> None:
        """
        Load canonical YAML and build deterministic name->id maps.
        This runs early in generation and will fail fast if YAML is invalid.
        """
        self._data = load_kirbyam_data()
        data = self._data

        # Build stable ID maps by YAML key, then convert to name->id (AP expects names).
        item_keys = [key for row in data.items if (key := row.get("key")) is not None]
        loc_keys = [key for row in data.locations if (key := row.get("key")) is not None]

        item_key_to_id = build_id_map(item_keys, self._base_item_id, "kirbyam:item")
        loc_key_to_id = build_id_map(loc_keys, self._base_location_id, "kirbyam:location")

        # Canonical identifier is YAML "key".
        # Archipelago requires name->id maps; IDs are deterministically derived from keys to remain stable across name tweaks.
        self.item_name_to_id = {name: item_key_to_id[key] for row in data.items if (name := row.get("name")) is not None and (key := row.get("key")) is not None}
        self.location_name_to_id = {name: loc_key_to_id[key] for row in data.locations if (name := row.get("name")) is not None and (key := row.get("key")) is not None}

        # Ensure our POC names exist in YAML (optional but strongly recommended).
        # This prevents drift between POC code and data files.
        required_items = {"Test Progression", "Test Filler"}
        required_locations = {"Test Location 1", "Test Location 2"}

        missing_items = required_items.difference(self.item_name_to_id.keys())
        missing_locations = required_locations.difference(self.location_name_to_id.keys())

        if missing_items:
            raise ValueError(f"POC requires these items to exist in items.yaml: {sorted(missing_items)}")
        if missing_locations:
            raise ValueError(f"POC requires these locations to exist in locations.yaml: {sorted(missing_locations)}")

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
        poc_locations = [name for row in data.locations if "poc" in row.get("tags", []) and (name := row.get("name")) is not None]

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
        # POC item pool: 2 items for 2 locations
        self.multiworld.itempool.append(self.create_item("Test Progression"))
        self.multiworld.itempool.append(self.create_item("Test Filler"))

    def set_rules(self) -> None:
        self.multiworld.completion_condition[self.player] = lambda state: state.has("Victory", self.player)

    def create_item(self, name: str) -> Item:
        item_id = self.item_name_to_id[name]
        classification = ItemClassification.filler
        if name == "Test Progression":
            classification = ItemClassification.progression
        return Item(name, classification, item_id, self.player)

    def _create_event_item(self, name: str) -> Item:
        return Item(name, ItemClassification.progression, None, self.player)

    def fill_slot_data(self) -> Dict[str, Any]:
        # Keep minimal until the BizHawk client is implemented.
        return {}