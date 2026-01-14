from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from BaseClasses import Item, ItemClassification, Location, Region, Tutorial
from worlds.AutoWorld import WebWorld, World

from .data_loader import KirbyAMData, load_kirbyam_data
from .id_map import build_id_map
from .logging_utils import log_event

GAME_NAME = "Kirby & The Amazing Mirror"
ORIGIN_REGION = "Menu"

# ----------------------------
# POC constants (names must match YAML)
# ----------------------------
POC_ITEM_MAX_HP_UP_NAME = "Max Health Up"
POC_ITEM_PHONE_CHARGE_NAME = "Cell Phone Charge"

# Optional: if your YAML includes these keys, we’ll use them.
POC_LOC_ROOM_CHECK_KEY = "poc_room_check"
POC_LOC_GOAL_ROOM_KEY = "poc_goal_room"


@dataclass(frozen=True)
class _LocationSpec:
    name: str
    ap_id: int
    room_value_na: int


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
            authors=["Harrison"],
        )
    ]
    bug_report_page = None


class KirbyAMWorld(World):
    """
    Playable POC:
      - room-based location check
      - room-based goal
      - items: Max Health Up + Cell Phone Charge filler
      - Pattern B Victory: Victory is an EVENT LOCATION (address None) with an EVENT ITEM (code None)
        that becomes reachable when the goal-room location is reachable.
    """

    _data: KirbyAMData
    _poc_location_names: List[str]
    _poc_item_names: List[str]
    _poc_padding_item_name: Optional[str]

    _poc_room_check: Optional[_LocationSpec] = None
    _poc_goal_room: Optional[_LocationSpec] = None

    game = GAME_NAME
    web = KirbyAMWebWorld()
    origin_region_name = ORIGIN_REGION

    _base_location_id = 23_450_000
    _base_item_id = 23_460_000

    # Required by AutoWorld metaclass. Do not mutate these dicts in-place.
    item_name_to_id: Dict[str, int] = {}
    location_name_to_id: Dict[str, int] = {}

    def _log_ctx(self) -> dict[str, object]:
        return {
            "player": getattr(self, "player", None),
            "player_name": (
                getattr(self.multiworld, "player_name", {}).get(self.player)
                if getattr(self, "multiworld", None)
                else None
            ),
            "seed": getattr(self.multiworld, "seed_name", None) if getattr(self, "multiworld", None) else None,
            "game": getattr(self, "game", None),
            "world_id": id(self),
        }

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
        return ItemClassification.filler

    def _find_location_row_by_key_optional(self, key: str) -> Optional[dict[str, object]]:
        for row in self._data.locations:
            if str(row.get("key")) == key:
                return row
        return None

    def _require_room_value_na(self, row: dict[str, object], *, context: str) -> int:
        # New shape: prefer explicit `value`
        v = row.get("value")
        if isinstance(v, int):
            return v

        # Backward-compatible fallback: treat addresses.na as the room-id trigger if present.
        addresses = row.get("addresses")
        if isinstance(addresses, dict):
            na_val = addresses.get("na")
            if isinstance(na_val, int):
                return na_val

        raise ValueError(f"{context}: expected an int room trigger via 'value' (preferred) or addresses.na (fallback)")

    def _select_playable_poc_rows(self) -> tuple[dict[str, object], dict[str, object]]:
        """
        Select (room_check_row, goal_row).

        Priority:
          1) exact keys: poc_room_check / poc_goal_room (if present)
          2) tagged POC locations (deterministic ordering)
        """
        room_check_row = self._find_location_row_by_key_optional(POC_LOC_ROOM_CHECK_KEY)
        goal_row = self._find_location_row_by_key_optional(POC_LOC_GOAL_ROOM_KEY)
        if room_check_row and goal_row:
            return room_check_row, goal_row

        poc_rows = [r for r in self._data.locations if "poc" in (r.get("tags") or [])]
        if len(poc_rows) < 2:
            raise ValueError("Playable POC requires at least 2 locations tagged 'poc' in locations.yaml")

        # Deterministic fallback: sort by key then pick first as room-check, second as goal
        poc_rows_sorted = sorted(poc_rows, key=lambda r: str(r.get("key") or ""))
        return dict(poc_rows_sorted[0]), dict(poc_rows_sorted[1])

    def generate_early(self) -> None:
        log_event("generate_early.start", **self._log_ctx())

        self._data = load_kirbyam_data()
        data = self._data

        # ensure instance-local dicts (AutoWorld requires presence at class-level)
        self.item_name_to_id = dict(self.item_name_to_id)
        self.location_name_to_id = dict(self.location_name_to_id)

        log_event(
            "generate_early.data_loaded",
            **self._log_ctx(),
            items=len(data.items),
            locations=len(data.locations),
            goals=len(data.goals),
        )

        item_key_to_id = build_id_map(
            (row["key"] for row in data.items if "key" in row),
            base_id=self._base_item_id,
            namespace="kirbyam:item",
        )
        loc_key_to_id = build_id_map(
            (row["key"] for row in data.locations if "key" in row),
            base_id=self._base_location_id,
            namespace="kirbyam:location",
        )

        self.item_name_to_id = {
            str(row["name"]): item_key_to_id[str(row["key"])]
            for row in data.items
            if "key" in row and "name" in row
        }
        self.location_name_to_id = {
            str(row["name"]): loc_key_to_id[str(row["key"])]
            for row in data.locations
            if "key" in row and "name" in row
        }

        self._poc_location_names = [
            str(row["name"])
            for row in data.locations
            if "poc" in row.get("tags", []) and "name" in row
        ]
        self._poc_item_names = [
            str(row["name"])
            for row in data.items
            if "poc" in row.get("tags", []) and "name" in row
        ]

        if not self._poc_location_names:
            raise ValueError("No locations tagged 'poc' found in locations.yaml")
        if not self._poc_item_names:
            raise ValueError("No items tagged 'poc' found in items.yaml")

        # Padding item policy: exactly one filler candidate tagged poc
        filler_candidates = [
            str(row["name"])
            for row in data.items
            if "poc" in row.get("tags", [])
            and (str(row.get("classification") or "")).strip().lower() == "filler"
            and "name" in row
        ]
        if len(filler_candidates) != 1:
            raise ValueError(
                "POC padding requires exactly one item tagged 'poc' with classification 'filler' in items.yaml. "
                f"Found {len(filler_candidates)}: {filler_candidates}"
            )
        self._poc_padding_item_name = filler_candidates[0]

        # Select the two playable POC locations and parse room triggers
        room_check_row, goal_row = self._select_playable_poc_rows()

        room_check_name = str(room_check_row.get("name"))
        goal_name = str(goal_row.get("name"))

        if room_check_name not in self.location_name_to_id:
            raise ValueError(f"POC room-check location name not in location_name_to_id: {room_check_name}")
        if goal_name not in self.location_name_to_id:
            raise ValueError(f"POC goal location name not in location_name_to_id: {goal_name}")

        self._poc_room_check = _LocationSpec(
            name=room_check_name,
            ap_id=self.location_name_to_id[room_check_name],
            room_value_na=self._require_room_value_na(room_check_row, context="POC room-check location"),
        )
        self._poc_goal_room = _LocationSpec(
            name=goal_name,
            ap_id=self.location_name_to_id[goal_name],
            room_value_na=self._require_room_value_na(goal_row, context="POC goal location"),
        )

        # Ensure required item names exist for the playable POC
        for req_item in (POC_ITEM_MAX_HP_UP_NAME, POC_ITEM_PHONE_CHARGE_NAME):
            if req_item not in self.item_name_to_id:
                raise ValueError(f"Missing required POC item name in items.yaml: {req_item} (tag it with [poc])")

        log_event(
            "generate_early.poc_playable_contract",
            **self._log_ctx(),
            room_check_name=self._poc_room_check.name,
            room_check_id=self._poc_room_check.ap_id,
            room_check_room_value_na=self._poc_room_check.room_value_na,
            goal_room_name=self._poc_goal_room.name,
            goal_room_id=self._poc_goal_room.ap_id,
            goal_room_value_na=self._poc_goal_room.room_value_na,
            padding_item=self._poc_padding_item_name,
        )

        log_event("generate_early.done", **self._log_ctx())

    def create_regions(self) -> None:
        log_event("create_regions.start", **self._log_ctx())

        # Regions expected by your test suite (keep minimal)
        menu = Region(self.origin_region_name, self.player, self.multiworld)
        main = Region("Main Area", self.player, self.multiworld)
        branch = Region("Test Branch", self.player, self.multiworld)

        self.multiworld.regions += [menu, main, branch]

        # Connections (branch reachable with no items)
        menu.connect(main, "To Main Area")
        main.connect(branch, "To Test Branch")

        # Pattern B: Victory is an EVENT LOCATION (address None) with an EVENT ITEM (code None).
        # It becomes reachable once the goal-room location is reachable.
        victory_loc = Location(self.player, "Victory", None, menu)
        victory_loc.access_rule = lambda state: state.can_reach(self._poc_goal_room.name, "Location", self.player)  # type: ignore[union-attr]
        victory_loc.place_locked_item(self._create_event_item("Victory"))
        menu.locations.append(victory_loc)

        # Register all POC-tagged locations from YAML into Main Area (keep it simple for now).
        for loc_name in self._poc_location_names:
            main.locations.append(Location(self.player, loc_name, self.location_name_to_id[loc_name], main))

        log_event(
            "create_regions.done",
            **self._log_ctx(),
            regions=3,
            poc_locations=len(self._poc_location_names),
            victory_location="Victory",
        )

    def create_items(self) -> None:
        log_event("create_items.start", **self._log_ctx())

        pool_names = list(self._poc_item_names)
        if not pool_names:
            raise ValueError("No items tagged 'poc' found in items.yaml")

        # Pad up to match number of POC locations (excluding Victory event, which is locked).
        needed = len(self._poc_location_names) - len(pool_names)
        if needed > 0:
            if not self._poc_padding_item_name:
                raise ValueError("Missing _poc_padding_item_name but padding is required")
            pool_names.extend([self._poc_padding_item_name] * needed)

        for item_name in pool_names:
            self.multiworld.itempool.append(self.create_item(item_name))

        log_event(
            "create_items.done",
            **self._log_ctx(),
            pool_items=len(pool_names),
            padded=max(0, needed),
        )

    def set_rules(self) -> None:
        log_event("set_rules.start", **self._log_ctx())

        # Completion is owning the Victory EVENT ITEM.
        self.multiworld.completion_condition[self.player] = lambda state: state.has("Victory", self.player)

        log_event("set_rules.done", **self._log_ctx(), completion="Victory")

    def create_item(self, name: str) -> Item:
        item_id = self.item_name_to_id[name]
        row = next((r for r in self._data.items if str(r.get("name")) == name), None)
        classification = self._class_from_str(str(row.get("classification")) if row and row.get("classification") else None)
        return Item(name, classification, item_id, self.player)

    def _create_event_item(self, name: str) -> Item:
        return Item(name, ItemClassification.progression, None, self.player)

    def fill_slot_data(self) -> Dict[str, Any]:
        # Client will consume these to map room triggers -> AP location ids.
        # Keep this stable as you expand ram.yaml.
        return {
            "poc": {
                "room_check": {
                    "location_name": self._poc_room_check.name,      # type: ignore[union-attr]
                    "location_id": self._poc_room_check.ap_id,       # type: ignore[union-attr]
                    "room_value_na": self._poc_room_check.room_value_na,  # type: ignore[union-attr]
                },
                "goal": {
                    "location_name": self._poc_goal_room.name,       # type: ignore[union-attr]
                    "location_id": self._poc_goal_room.ap_id,        # type: ignore[union-attr]
                    "room_value_na": self._poc_goal_room.room_value_na,  # type: ignore[union-attr]
                },
                "victory_event_location": "Victory",
                "items": {
                    "max_health_up": POC_ITEM_MAX_HP_UP_NAME,
                    "phone_charge": POC_ITEM_PHONE_CHARGE_NAME,
                },
            }
        }
