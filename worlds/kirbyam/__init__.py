from __future__ import annotations

from typing import Any, Dict, Optional

from BaseClasses import Item, ItemClassification, Location, Region, Tutorial
from worlds.AutoWorld import WebWorld, World


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

    # Minimal stable ID mappings for POC
    # Keep these stable once published (clients/trackers will depend on them).
    _base_location_id = 12_345_000
    _base_item_id = 12_346_000

    # Note: event locations/items (Victory) do not need numeric IDs.
    location_name_to_id = {
        "Test Location 1": _base_location_id + 1,
        "Test Location 2": _base_location_id + 2,
    }

    item_name_to_id = {
        "Test Progression": _base_item_id + 1,
        "Test Filler": _base_item_id + 2,
    }

    def create_regions(self) -> None:
        menu = Region(self.origin_region_name, self.player, self.multiworld)
        main = Region("Main Area", self.player, self.multiworld)

        # Connect Menu -> Main Area
        menu_to_main = menu.connect(main, "To Main Area")
        # No rule: always accessible for POC

        # Add two test locations in Main Area
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

        # Add completion event location in Menu (not part of mapping)
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
        # Minimal completion: require the event item "Victory"
        self.multiworld.completion_condition[self.player] = lambda state: state.has("Victory", self.player)

    def create_item(self, name: str) -> Item:
        item_id = self.item_name_to_id[name]
        classification = ItemClassification.filler
        if name == "Test Progression":
            classification = ItemClassification.progression
        return Item(name, classification, item_id, self.player)

    def _create_event_item(self, name: str) -> Item:
        # Event items typically have no numeric ID; they exist only in the current multiworld context.
        return Item(name, ItemClassification.progression, None, self.player)

    def fill_slot_data(self) -> Dict[str, Any]:
        # Keep minimal until the BizHawk client is implemented.
        return {}
