from __future__ import annotations

from typing import Any, Dict

from BaseClasses import Item, ItemClassification, Location, Region, Tutorial
from worlds.AutoWorld import WebWorld, World

from .data_loader import load_kirbyam_data
from .id_map import build_id_map

GAME_NAME = "Kirby & The Amazing Mirror"


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
    game = GAME_NAME
    web = KirbyAMWebWorld()

    origin_region_name = "Menu"
    
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
        data = load_kirbyam_data()

        # Build stable ID maps by YAML key, then convert to name->id (AP expects names).
        item_keys = [key for row in data.items if (key := row.get("key")) is not None]
        loc_keys = [key for row in data.locations if (key := row.get("key")) is not None]

        item_key_to_id = build_id_map(item_keys, self._base_item_id, "kirbyam:item")
        loc_key_to_id = build_id_map(loc_keys, self._base_location_id, "kirbyam:location")

        # Convert key->id to name->id using YAML "name"
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
        main = Region("Main Area", self.player, self.multiworld)

        # Connect Menu -> Main Area
        menu.connect(main, "To Main Area")

        # POC locations (IDs now come from YAML-generated mapping)
        main.locations.append(
            Location(
                self.player,
                "Test Location 1",
                self.location_name_to_id["Test Location 1"],
                main,
            )
        )
        main.locations.append(
            Location(
                self.player,
                "Test Location 2",
                self.location_name_to_id["Test Location 2"],
                main,
            )
        )

        # Victory event location (event locations/items do not need numeric IDs)
        victory_event = Location(self.player, "Victory", None, menu)
        victory_event.place_locked_item(self._create_event_item("Victory"))
        menu.locations.append(victory_event)

        self.multiworld.regions.append(menu)
        self.multiworld.regions.append(main)

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