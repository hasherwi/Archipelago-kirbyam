#!/usr/bin/env python3
"""Validate the derived legacy metal audit without nonbundled extraction files.

Default mode checks published JSON structure, registry grants and F5 inventory.
Optional --rom reads an already-owned, unchanged USA ROM locally to re-extract
only the audited assertions. It writes no bytes, grids, graphics or ROM files.
This is not a traversal/controller proof. Python 3.10+, standard library only.
"""
from __future__ import annotations
import argparse
from collections import Counter, deque
import hashlib
import importlib.util
import json
from pathlib import Path
import re
from types import ModuleType
from typing import Any, cast

JsonObject = dict[str, Any]

USA_SHA1 = "274b102b6d940f46861a92b4e65f89a51815c12c"
NATIVE_REVISION = "7d969fbce14fdc838d2c1ea01389717fb96c3189"
EXPECTED_COUNTS = {141: 3, 205: 1, 707: 1, 708: 2, 742: 2}
ROM_BASE = 0x08000000


def read(path: Path) -> JsonObject:
    return cast(JsonObject, json.loads(path.read_text(encoding="utf-8-sig")))


def require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError(message)


def collect_sources(audit: JsonObject) -> dict[tuple[int, str], JsonObject]:
    found: dict[tuple[int, str], JsonObject] = {}
    for row in audit["edges"].values():
        for source in row.get("source_candidates", []):
            identity = source.get("object_address")
            if identity:
                key = (source["native_room"], identity)
                if key in found:
                    require(found[key]["source_key"] == source["source_key"], "Conflicting source identity")
                found[key] = source
    return found


def validate_published(audit: JsonObject, world: Path, maps: JsonObject, check_current: bool) -> JsonObject:
    require(audit["native_revision"] == NATIVE_REVISION, "Unexpected native revision")
    require(audit["rom_sha1"] == USA_SHA1, "Unexpected source-ROM identity")
    edges = audit["edges"]
    require(len(edges) == 9, "Historical audit must contain exactly nine edges")
    require(Counter(row["native_room"] for row in edges.values()) == EXPECTED_COUNTS, "Unexpected native edge counts")
    inventory = read(world / "docs/metal-tile-inventory.json")
    f5 = {row["room"]: {(t["x"], t["y"]) for t in row["tiles"] if t["tile"] == "0xf5"}
          for row in inventory["rooms"]}
    enemies = read(world / "data/enemies.json")
    current = read(world / "data/regions/rooms.json")
    seen_clusters: dict[str, set[tuple[int, int]]] = {}
    for edge, row in edges.items():
        owner, separator, target = edge.partition(" -> ")
        require(separator and owner.startswith("REGION_") and target.startswith("REGION_"), "Malformed AP edge key")
        require("can_break_metal" in json.dumps(row["legacy_requirement"]), "Missing historical metal requirement")
        tiles = {tuple(x) for x in row["barrier"]["tiles"]}
        require(tiles and len(tiles) == len(row["barrier"]["tiles"]), "Empty or duplicate barrier tiles")
        require(tiles <= f5[row["native_room"]], f"Barrier is not in published F5 inventory: {edge}")
        cluster = row["barrier"]["cluster"]
        if cluster in seen_clusters:
            require(seen_clusters[cluster] == tiles, "Inconsistent shared F5 bank")
        seen_clusters[cluster] = tiles
        require(row["wiki_url"].startswith("https://wikirby.com/"), "Missing public room source")
        if check_current:
            require(owner in current and current[owner].get("exits", {}).get(target) == row["legacy_requirement"],
                    f"Current AP edge changed since historical audit: {edge}")
        for source in row.get("source_candidates", []):
            key = source["source_key"]
            if key.startswith("STATUE:"):
                require(re.fullmatch(r"STATUE:[0-9A-F]{6}", key), "Malformed statue slot")
            else:
                require(key in enemies, f"Unknown source registry key: {key}")
                require(enemies[key]["default_ability"] == source["native_grant"], f"Wrong native grant: {key}")
    require(len(seen_clusters) == 6, "Expected six physical F5 banks across nine directed edges")
    expected_maps = {141, 205, 704, 706, 707, 708, 712, 740, 741, 742}
    require({m["native_room"] for m in maps["maps"]} == expected_maps and len(maps["maps"]) == 10,
            "Missing or duplicated inspected map reference")
    for m in maps["maps"]:
        require(f"oldid={m['article_revision']}" in m["article_revision_url"], "Article revision URL mismatch")
        require(m["map_url"].startswith("https://cdn.wikirby.com/") and re.fullmatch(r"[0-9a-f]{64}", m["map_sha256"]),
                "Map URL/hash is missing")
    return {
        "historical_edges": len(edges), "f5_banks": len(seen_clusters),
        "named_sources": len(collect_sources(audit)),
        "inspected_map_references": 10, "current_binding_comparison": check_current,
    }


def load_scanner(world: Path) -> ModuleType:
    path = world / "tools/scan_metal_tiles.py"
    spec = importlib.util.spec_from_file_location("legacy_audit_scanner", path)
    if spec is None or spec.loader is None:
        raise ValueError("Cannot load published collision scanner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_native_room(rom: bytes, s: ModuleType, room: int, cache: dict[int, JsonObject]) -> JsonObject:
    if room in cache:
        return cache[room]
    props = s.unpack(rom, "<20H", s.ROOM_PROPS + room * 40)
    require(props[12] < s.TABLE_COUNT and props[13] < s.TABLE_COUNT and props[16] < s.TABLE_COUNT,
            "Native room table index is out of range")
    fg = s.pointer(rom, s.FOREGROUND_TABLE + props[12] * 4)
    width, height = s.unpack(rom, "<HH", fg)
    width //= 2
    height //= 2
    head = s.pointer(rom, s.SOLIDITY_TABLE + props[13] * 4)
    grid = s.decompress_rl(rom, s.pointer(rom, head), width * height)
    records = s.records(rom, s.pointer(rom, head + 4))
    doors = {}
    mutations = {}
    for r in records:
        if r["kind"] == 3:
            destination, x, y = s.unpack(rom, "<HBB", r["offset"] + 8)
            doors[r["offset"]] = (r["x"], r["y"], destination, x, y)
        else:
            value = s.unpack(rom, "<B", r["offset"] + (16 if r["kind"] == 1 else 12))[0]
            mutations[(r["x"], r["y"], r["attribute"])] = value
    cursor = s.pointer(rom, s.pointer(rom, 0xD637AC + props[16] * 4))
    objects = {}
    for _ in range(4096):
        kind, size = s.unpack(rom, "<BB", cursor)
        if kind == 0:
            break
        require(size >= 2 and cursor + size <= len(rom), "Malformed object list")
        if kind == 1:
            require(size >= 36, "Short object template")
            x, y = s.unpack(rom, "<hh", cursor + 6)
            typ = s.unpack(rom, "<B", cursor + 12)[0]
            grant = s.unpack(rom, "<H", 0x35164E + 24 * typ)[0]
            objects[cursor] = (x, y, typ, grant)
        cursor += size
    else:
        raise ValueError("Unterminated object list")
    result = dict(width=width, height=height, grid=grid, doors=doors, objects=objects, mutations=mutations)
    cache[room] = result
    return result


def collision_tile(n: JsonObject, xy: tuple[int, int]) -> int:
    x, y = xy
    require(0 <= x < n["width"] and 0 <= y < n["height"], "Out-of-range assertion")
    return int(n["grid"][y * n["width"] + x])


def bomb_component(rom: bytes, s: ModuleType, n: JsonObject, start: tuple[int, int]) -> set[tuple[int, int]]:
    reached, q = {start}, deque([start])
    while q:
        x, y = q.popleft()
        for xy in [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]:
            xx, yy = xy
            if not (0 <= xx < n["width"] and 0 <= yy < n["height"]):
                continue
            attr = s.unpack(rom, "<I", s.COLLISION_ATTRIBUTES + collision_tile(n, xy) * 4)[0]
            if attr & 0x40 and xy not in reached:
                reached.add(xy)
                q.append(xy)
    return reached


def validate_rom(audit: JsonObject, world: Path, path: Path) -> JsonObject:
    rom = path.read_bytes()
    require(len(rom) == 0x1000000 and hashlib.sha1(rom).hexdigest() == USA_SHA1,
            "Expected an already-owned, unmodified USA ROM with the pinned SHA-1; no alternate ROM accepted")
    s = load_scanner(world)
    cache: dict[int, JsonObject] = {}

    def native(room: int) -> JsonObject:
        return read_native_room(rom, s, room, cache)

    abilities = read(world / "data/abilities.json")
    for (room, address), source in collect_sources(audit).items():
        obj = native(room)["objects"].get(int(address, 16) - ROM_BASE)
        require(obj is not None, f"Source template not found: {room}/{address}")
        if "spawn_pixels" in source:
            require(list(obj[:2]) == source["spawn_pixels"], f"Source position mismatch: {address}")
        if not source["source_key"].startswith("STATUE:"):
            expected = abilities[source["native_grant"]]["runtime_ability_id"]
            require(obj[3] == expected, f"Native ability table mismatch: {address}")
    incoming_count = 0
    for row in audit["edges"].values():
        n = native(row["native_room"])
        for x, y in row["barrier"]["tiles"]:
            require(n["grid"][y * n["width"] + x] == 0xF5, "F5 coordinate mismatch")
        if "exit" in row:
            x = row["exit"]
            actual = n["doors"].get(int(x["record"], 16) - ROM_BASE)
            require(actual == (*x["trigger_tiles"], x["destination"], *x["arrival_tiles"]), "Exit endpoint mismatch")
        for x in row.get("incoming", []):
            off = int(x["offset"], 16)
            if off >= ROM_BASE:
                off -= ROM_BASE
            actual = native(x["source"])["doors"].get(off)
            require(actual == (*x["trigger"], x["destination"], *x["spawn_tile"]), "Incoming endpoint mismatch")
            incoming_count += 1
    n = native(742)

    outer, inner = bomb_component(rom, s, n, (19, 12)), bomb_component(rom, s, n, (26, 12))
    require(not outer & inner, "742 Bomb components are not distinct")
    expected = {(24, 8): 0x0D, (25, 8): 0x0D, (22, 13): 0x0F, (28, 13): 0x0F}
    expected.update({(x, 9): 0x1D for x in range(22, 29)})
    expected.update({(x, y): 0 for x in (22, 28) for y in range(10, 13)})
    for xy, value in expected.items():
        require(xy in outer and n["mutations"].get((*xy, collision_tile(n, xy))) == value,
                f"742 outer mutation mismatch: {xy}")
    require(inner == {(26, 12), (25, 12), (25, 11)}, "Unexpected 742 inner Bomb component")
    require(n["mutations"].get((25, 12, collision_tile(n, (25, 12)))) == 0xFF, "742 inner door reveal mismatch")
    require(n["mutations"].get((25, 11, collision_tile(n, (25, 11)))) == 0, "742 inner clearance mismatch")
    for x in range(23, 28):
        for y in (13, 14):
            require(collision_tile(n, (x, y)) == 0x0D, "742 center floor mismatch")
    return {
        "source_sha1": USA_SHA1, "native_rooms_read": len(cache),
        "incoming_record_assertions": incoming_count, "742_components_disjoint": True,
        "scope": ("Coordinates, source table values, door records and bounded mutation assertions only; "
                  "no physics or gameplay proof."),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--world", required=True, type=Path, help="Path to the published worlds/kirbyam directory")
    p.add_argument("--audit", type=Path, help="Defaults to WORLD/dev-docs/legacy-metal-exit-audit.json")
    p.add_argument("--map-references", type=Path, help="Defaults beside this script")
    p.add_argument("--check-current-bindings", action="store_true",
                   help="Fail if current AP edges differ from this historical baseline")
    p.add_argument("--rom", type=Path, help="Optional local already-owned unchanged USA ROM; never downloaded")
    a = p.parse_args()
    audit = read(a.audit or a.world / "dev-docs/legacy-metal-exit-audit.json")
    maps = read(a.map_references or Path(__file__).with_name("legacy-metal-public-map-references.json"))
    out = {"published_assertions": validate_published(audit, a.world, maps, a.check_current_bindings)}
    out["native_reextraction"] = validate_rom(audit, a.world, a.rom) if a.rom else {
        "status": "NOT RUN: no --rom supplied",
        "limitation": ("Default mode does not independently verify native object offsets, doors, "
                       "tile mutation values or movement."),
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
