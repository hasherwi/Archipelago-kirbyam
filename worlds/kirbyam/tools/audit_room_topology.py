"""Classify the compiled solver graph without assuming physical door evidence."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any

from ..data import data
from ..traversal_data import _room_catalog, room_traversal_graph

ROOT = Path(__file__).resolve().parents[1]
DOOR_INVENTORY = ROOT / "dev-docs/native-tile-door-inventory.json"
PHONE_INVENTORY = ROOT / "dev-docs/phone-return-native-rooms.json"
MAIN = "REGION_RAINBOW_ROUTE/MAIN"
CIRCLE = "REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE"


def build_inventory() -> dict[str, Any]:
    catalog = json.loads((ROOT / "dev-docs/native-room-wikirby-map.json").read_text(encoding="utf-8"))
    native: dict[str, int] = {}
    for room in catalog["rooms"]:
        for ap_key in room["ap_keys"]:
            if ap_key in native:
                raise ValueError(f"AP compartment has multiple native room bindings: {ap_key}")
            native[ap_key] = room["native_id"]
    if not native.keys() <= data.regions.keys():
        raise ValueError("Native room inventory references an uncompiled AP region")

    def node_kind(name: str) -> str:
        if name in native:
            return "native_compartment"
        if name.endswith("__ROOM_CHECK"):
            return "room_check_sink"
        if name in {"Menu", "REGION_GAME_START"}:
            return "start"
        if name.endswith("/MAIN"):
            return "area_summary"
        raise ValueError(f"Unclassified Kirby AP region: {name}")

    nodes = {key: {"kind": node_kind(key), "native_room": native.get(key)}
             for key in sorted(set(data.regions) | {"Menu"})}
    edges: list[dict[str, Any]] = []

    def append(source: str, destination: str, *, generated: bool = False) -> None:
        src_kind, dst_kind = nodes[source]["kind"], nodes[destination]["kind"]
        if dst_kind == "room_check_sink":
            category = "room_check_sink_link"
        elif generated and dst_kind == "area_summary":
            category = "area_summary_fan_in"
        elif "start" in (src_kind, dst_kind):
            category = "start_or_tutorial_bridge"
        elif "area_summary" in (src_kind, dst_kind):
            category = "area_summary_bridge"
        elif native[source] == native[destination]:
            category = "same_native_room_candidate"
        else:
            category = "cross_native_room_candidate"
        edges.append({"from_region": source, "to_region": destination,
                      "kind": category, "generated_by_region_builder": generated})

    authored = {(key, dest) for key, row in data.regions.items() for dest in row.exits}
    for source, dest in sorted(authored):
        append(source, dest)
    for source in sorted(data.regions):
        if ("/ROOM_" in source and nodes[source]["kind"] != "room_check_sink"
                and (area := source.split("/", 1)[0] + "/MAIN") in data.regions):
            append(source, area, generated=True)
    append("Menu", "REGION_GAME_START", generated=True)
    for edge in edges:
        # A reverse AP edge is catalog metadata, not proof of a physical reverse door.
        edge["authored_reverse"] = (edge["to_region"], edge["from_region"]) in authored

    door_data = json.loads(DOOR_INVENTORY.read_text(encoding="utf-8"))
    phone_data = json.loads(PHONE_INVENTORY.read_text(encoding="utf-8"))
    for evidence in (door_data, phone_data):
        if evidence["rom_sha1"] != catalog["rom_sha1"]:
            raise ValueError("Kirby topology joins require the same retail ROM")
    eligible = set(phone_data["eligible_native_rooms"])
    ineligible = set(phone_data["room_flag_disallows_return"])
    populated = {room["native_id"] for room in catalog["rooms"]}
    if eligible & ineligible or eligible | ineligible != populated:
        raise ValueError("Incomplete or contradictory native Phone flag catalog")
    for node in nodes.values():
        room_id = node["native_room"]
        if room_id is not None:
            node["phone_return_room_flag"] = room_id in eligible
            node["phone_encounter_slots"] = phone_data["encounter_session_slots_by_native_room"].get(str(room_id), [])

    pair_counts: Counter[str] = Counter()
    for edge in edges:
        if edge["kind"] != "cross_native_room_candidate":
            continue
        origin, target = native[edge["from_region"]], native[edge["to_region"]]
        matches = [door for door in door_data["doors_by_source_native_room"].get(str(origin), [])
                   if door["to_native_room"] == target]
        edge["retail_tile_door_candidates"] = matches
        pair_counts["no_tile_match" if not matches else "matching_room_pair" if len(matches) == 1
                    else "multiple_tile_doors"] += 1

    witnesses = []
    for row in _room_catalog()[0]:
        for name in sorted(row["graphs"]):
            graph = room_traversal_graph(row["id"], name)
            rooms = {node.key: node.room for node in graph.nodes}
            crossings = sum(rooms[route.source] != rooms[route.target] for route in graph.routes)
            implicit = sum(rooms[route.source] != rooms[route.target] and not route.room_transition
                           for route in graph.routes)
            same_id_transitions = [{"from_node": route.source, "to_node": route.target,
                                    "native_room": rooms[route.source]}
                                   for route in graph.routes
                                   if route.room_transition and rooms[route.source] == rooms[route.target]]
            witnesses.append({"target": row["id"], "witness": name, "cross_native_edges": crossings,
                              "cross_native_edges_without_explicit_flag": implicit,
                              "explicit_same_native_transitions": same_id_transitions})
    return {
        "schema": 1,
        "scope": "Compiled solver structure, not proof that a native door is traversable.",
        "native_catalog": {"populated_rooms": len(catalog["rooms"]),
                           "normalized_compartments": len(native)},
        "region_counts": dict(sorted(Counter(node["kind"] for node in nodes.values()).items())),
        "edge_counts": dict(sorted(Counter(edge["kind"] for edge in edges).items())),
        "rainbow_summary_incoming_physical_compartments": sorted(
            edge["from_region"] for edge in edges
            if edge["to_region"] == MAIN and nodes[edge["from_region"]]["kind"] == "native_compartment"),
        "rainbow_summary_has_central_bridge": (MAIN, CIRCLE) in authored,
        "retail_cross_room_pair_counts": dict(sorted(pair_counts.items())),
        "nodes": nodes,
        "edges": edges,
        "reviewed_witnesses": witnesses,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(build_inventory(), indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
