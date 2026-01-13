from __future__ import annotations

from typing import Any, Dict, Optional, List

from BaseClasses import Item, ItemClassification, Location, Region, Tutorial
from worlds.AutoWorld import WebWorld, World
from worlds.celeste_open_world import data

from .data_loader import load_kirbyam_data, KirbyAMData
from .id_map import build_id_map
from .logging_utils import log_event, log_debug

GAME_NAME = "Kirby & The Amazing Mirror"

ORIGIN_REGION = "Menu"

def _log_ctx(self) -> dict[str, object]:
    # multiworld.seed_name exists after generation starts; guard defensively
    seed_name = getattr(self.multiworld, "seed_name", None)
    return {
        "player": self.player,
        "seed": seed_name,
        "world": self.game,
        "short_name": self.game,
    }


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
        log_event("generate_early.start", **self._log_ctx())

        self._data = load_kirbyam_data()
        data = self._data

        log_event(
            "generate_early.data_loaded",
            **self._log_ctx(),
            items=len(data.items),
            locations=len(data.locations),
            goals=len(data.goals),
        )

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

        log_event(
            "generate_early.poc_sets",
            **self._log_ctx(),
            poc_items=len(self._poc_item_names),
            poc_locations=len(self._poc_location_names),
        )

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

        # Handle filler items
        filler_candidates = [
            row["name"]
            for row in data.items
            if "poc" in row.get("tags", []) and (row.get("classification") or "").strip().lower() == "filler"
        ]
        if len(filler_candidates) != 1:
            raise ValueError(
                "POC padding requires exactly one item tagged 'poc' with classification 'filler' in items.yaml. "
                f"Found {len(filler_candidates)}: {filler_candidates}"
            )
        self._poc_padding_item_name = filler_candidates[0]
        
        log_event(
            "generate_early.poc_padding_policy",
            **self._log_ctx(),
            padding_item=self._poc_padding_item_name,
        )
        
        log_event("generate_early.done", **self._log_ctx())


    def create_regions(self) -> None:
        log_event("create_regions.start", **self._log_ctx())
        
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
        
        log_debug(
            "create_regions.poc_distribution",
            **self._log_ctx(),
            main_count=len(main_locs),
            branch_count=len(branch_locs),
        )

        for loc_name in main_locs:
            main.locations.append(Location(self.player, loc_name, self.location_name_to_id[loc_name], main))

        for loc_name in branch_locs:
            branch.locations.append(Location(self.player, loc_name, self.location_name_to_id[loc_name], branch))
            
        log_event(
            "create_regions.done",
            **self._log_ctx(),
            regions=3,  # update if you compute dynamically
            poc_locations=len(self._poc_location_names),
        )


    def create_items(self) -> None:
        log_event("create_items.start", **self._log_ctx())
        
        # Start with the POC-tagged items
        pool_names = list(self._poc_item_names)

        # Pad to match POC locations if needed
        needed = len(self._poc_location_names) - len(pool_names)
        if needed > 0:
            assert self._poc_padding_item_name is not None
            pool_names.extend([self._poc_padding_item_name] * needed)

        for item_name in pool_names:
            self.multiworld.itempool.append(self.create_item(item_name))
            
        # If you build pool_names list, log counts
        log_event(
            "create_items.done",
            **self._log_ctx(),
            pool_items=len(pool_names),
            padded= max(0, len(pool_names) - len(self._poc_item_names)),
        )


    def set_rules(self) -> None:
        log_event("set_rules.start", **self._log_ctx())
        self.multiworld.completion_condition[self.player] = lambda state: state.has("Victory", self.player)
        log_event("set_rules.done", **self._log_ctx(), completion="Victory")

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