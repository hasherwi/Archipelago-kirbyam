"""Join compiled check placement to independent native evidence without inventing reachability."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

from ..data import LocationCategory as Kind, data, load_json_data, validate_check_placement
from ..traversal_data import _room_catalog

ROOT = Path(__file__).resolve().parents[1]
CHEST_KINDS = {Kind.MINOR_CHEST, Kind.MAP_CHEST, Kind.VITALITY_CHEST, Kind.SOUND_PLAYER_CHEST}


def _evidence(name):
    return json.loads((ROOT / "dev-docs" / name).read_text(encoding="utf-8"))


def _unique(rows, field):
    index = {row[field]: row for row in rows}
    if len(rows) != len(index):
        raise ValueError(f"Duplicate native records keyed by {field}")
    return index


def audit():
    validate_check_placement(data)
    rooms = _evidence("native-room-wikirby-map.json")
    inventory = load_json_data("ability_source_inventory.json")
    chests = load_json_data("chest_recovery.json")
    goals = load_json_data("goal_game_doors.json")
    if len({rooms["rom_sha1"], inventory["rom_sha1"], chests["rom_sha1"], goals["usa_sha1"]}) != 1:
        raise ValueError("Check placements must use the same USA ROM revision")
    native = {key: row for row in rooms["rooms"] for key in row["ap_keys"]}
    if len(native) != sum(len(row["ap_keys"]) for row in rooms["rooms"]):
        raise ValueError("Native room evidence has duplicate AP region keys")
    chest_by_key = _unique([row for row in chests["records"] if row["location_key"]], "location_key")
    lever_by_room = {
        row["rooms"][0]: row for row in chests["records"] if not row["location_key"]
        and row["reward"] == 0x63 and len(row["rooms"]) == 1
    }
    if len(lever_by_room) != 4:
        raise ValueError("Expected four distinct retail lever placements")
    goal_by_key = _unique(goals["goals"], "location_key")
    encounter = _evidence("phone-return-native-rooms.json")["encounter_session_slots_by_native_room"]
    hub_bits = _unique(load_json_data("hub_switch_contract.json")["entries"], "location_key")
    switches = _unique([row for row in inventory["placements"] if row["native_name"] == "OBJ_BIG_BUTTON"],
                       "native_room")
    side_overlays = defaultdict(list)
    for row in _room_catalog()[0]:
        if row.get("location") is not None:
            side_overlays[row["location"]].append(row["id"])
    owners = {key: region for region in data.regions.values() for key in region.locations}
    room_sanity = defaultdict(list)
    for region in data.regions.values():
        for target in region.exits:
            if target.endswith("__ROOM_CHECK"):
                room_sanity[target].append(region.name)
    result = []
    keys = set(data.locations)
    if chest_by_key.keys() != {k for k in keys if data.locations[k].category in CHEST_KINDS}:
        raise ValueError("Native recovery and AP chest catalogs cover different exact locations")
    if goal_by_key.keys() != {k for k in keys if data.locations[k].category == Kind.GOAL_GAME}:
        raise ValueError("Native Goal Game and AP catalogs cover different checks")
    for key, loc in sorted(data.locations.items()):
        owner = owners[key]
        room = native.get(loc.parent_region, {})
        native_room = room.get("native_id")
        row = {
            "key": key, "id": loc.location_id, "kind": loc.category.name, "owner": owner.name,
            "role": "goal_event" if loc.category == Kind.GOAL else "ap_check",
            "native_room": native_room,
        }
        if key in side_overlays:
            row["reviewed_location_overlays"] = sorted(side_overlays[key])
        if key in owner.location_requirements:
            row["compact_requirement"] = owner.location_requirements[key]
        if loc.category in CHEST_KINDS:
            chest = chest_by_key[key]
            if key == "MAJOR_CHEST_WORLD_MAP":
                if owner.name != "REGION_GAME_START" or chest["rooms"] != [805]:
                    raise ValueError("Tutorial World Map chest must use the tutorial/start bridge")
                row["native_room"] = 805
            elif native_room not in chest["rooms"]:
                raise ValueError(f"Chest source is not in its compiled region: {key}")
            if loc.category == Kind.MINOR_CHEST and loc.source_rom_offset != int(chest["source"], 16):
                raise ValueError(f"Exact chest source differs from the saved-flag record: {key}")
            row.update(trigger="collect_exact_chest", native_object=chest["source"],
                       native_position=chest["position"], native_save_bit=chest["flag"])
        elif loc.category == Kind.LEVER:
            lever = lever_by_room.pop(native_room)
            row.update(trigger="pull_exact_lever", native_object=lever["source"],
                       native_position=lever["position"], native_chest_slot=lever["flag"],
                       ap_bit=loc.bit_index)
        elif loc.category == Kind.HUB_SWITCH:
            switch, contract = switches.pop(native_room), hub_bits.pop(key)
            if contract["ap_bit_index"] != loc.bit_index:
                raise ValueError(f"Big Switch catalog bit disagreement: {key}")
            row.update(trigger="press_exact_big_switch", native_object=switch["template_address"],
                       native_position=switch["position_pixels"], ap_bit=loc.bit_index,
                       declared_contract_transport_bit=contract.get("runtime_ap_bit_index", loc.bit_index))
        elif loc.category == Kind.BOSS_DEFEAT:
            if encounter.get(str(native_room)) != [loc.bit_index + 1]:
                raise ValueError(f"Area boss encounter slot disagreement: {key}")
            row.update(trigger="defeat_area_boss", encounter_slot=loc.bit_index + 1, ap_bit=loc.bit_index)
        elif loc.category == Kind.GOAL_GAME:
            goal = goal_by_key[key]
            if native_room != goal["source_room"] or loc.bit_index != goal["bit_index"]:
                raise ValueError(f"Goal Game source room or bit disagreement: {key}")
            row.update(trigger="finish_entered_goal_game", door_tiles=[d["source_tiles"] for d in goal["doors"]],
                       destination_rooms=sorted({d["destination_room"] for d in goal["doors"]}),
                       ap_bit=loc.bit_index)
        elif loc.category == Kind.ROOM_SANITY:
            if room["completion_index"] != loc.bit_index:
                raise ValueError(f"Native visit index disagreement: {key}")
            if owner.name.endswith("__ROOM_CHECK"):
                expected = set(room["ap_keys"])
                sources = room_sanity[owner.name]
                if owner.exits or not expected or set(sources) != expected:
                    raise ValueError(f"Room visit requires an exact compartment-only terminal sink: {key}")
                row["counted_compartments"] = sorted(sources)
            elif room["ap_keys"] != [owner.name]:
                raise ValueError(f"Room visit omits or aliases native compartments: {key}")
            row.update(trigger="visit_native_room", native_visit_index=loc.bit_index,
                       enabled="always" if "CoreLandmark" in loc.tags else "room_sanity")
        elif loc.category == Kind.AREA_VISIT:
            if not owner.name.endswith("/MAIN"):
                raise ValueError(f"First visit should use an area summary: {key}")
            row.update(trigger="first_visit_to_native_area", native_area=loc.bit_index)
        elif loc.category == Kind.GOAL:
            if key == "GOAL_HIDDEN_AREA_BOSS":
                row["role"] = "legacy_goal_event"
            row["trigger"] = "selected_goal_requirements"
        else:
            raise ValueError(f"Unaudited check category: {key}")
        if room and len(room["ap_keys"]) > 1 and loc.category in {*CHEST_KINDS, Kind.LEVER, Kind.HUB_SWITCH, Kind.GOAL_GAME}:
            # Coordinates plus matching native room do not establish the side
            # of every obstacle. Keep shared-room cases visible for review.
            row["other_ap_compartments_in_native_room"] = sorted(set(room["ap_keys"]) - {owner.name})
        result.append(row)
    if lever_by_room or switches or hub_bits:
        raise ValueError("Unclaimed native lever or Big Switch")
    events = sorted(
        ({"name": evt.name, "owner": r.name, "paired_check": evt.source_check}
         for r in data.regions.values() for evt in r.events),
        key=lambda r: r["name"],
    )
    return {
        "summary": dict(sorted(Counter(r["kind"] for r in result).items())),
        "rom_sha1": rooms["rom_sha1"], "locations": result, "addressless_region_events": events,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, help="Write per-check placement evidence to this path")
    args = parser.parse_args()
    report = audit()
    if args.json:
        args.json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
