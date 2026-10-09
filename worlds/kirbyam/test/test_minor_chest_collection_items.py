"""Fixed minor-chest source, item-pool, mailbox, and executable ROM contracts."""

from __future__ import annotations

from collections import Counter
import json
import os
from pathlib import Path
import shutil
import subprocess
from unittest.mock import AsyncMock, Mock, patch

import pytest

from BaseClasses import CollectionState, ItemClassification, MultiWorld, Region

from .. import KirbyAmWorld
from ..client import KirbyAmClient
from ..data import data
from ..options import RandomizeShards
from .test_item_pool import _build_world_for_create_items

_WORLD = Path(__file__).resolve().parents[1]
_COLLECTION_ITEMS = [
    (f"SPRAY_PAINT_{number:02}", 3860199 + number, 0x13 + number,
     f"MINOR_CHEST_SPRAY_PAINT_{number:02}", 3960499 + number)
    for number in range(1, 15)
] + [
    (f"MUSIC_SHEET_{number:02}", 3860213 + number, 0x28 + number,
     f"MINOR_CHEST_MUSIC_NOTE_{number:02}", 3960513 + number)
    for number in range(1, 11)
]


@pytest.mark.parametrize("entry, spray_reachable, vitality_reachable", [
    ("ROOM_9_01", True, False),
    ("ROOM_9_09", False, True),
])
def test_candy_collection_compartments_remain_isolated(
    entry: str, spray_reachable: bool, vitality_reachable: bool,
) -> None:
    """Exercise the loaded graph with only one physical entrance available.

    Pin the left/right ownership without allowing a longer external route to
    conceal an accidental connection through the unsplit physical parent.
    Native geometry/provenance is recorded in minor-chest-collection-items.md.
    """
    prefix = "REGION_CANDY_CONSTELLATION/"
    parent = prefix + "ROOM_9_CHEST_2"
    names = [prefix + "ROOM_9_01", prefix + "ROOM_9_09", parent,
             parent + "__LOGIC__ENTRY_FROM_9_01", parent + "__LOGIC__ENTRY_FROM_9_09"]
    multiworld = MultiWorld(1)
    multiworld.worlds[1] = KirbyAmWorld(multiworld, 1)
    regions = {name: Region(name, 1, multiworld) for name in ["Menu", *names]}
    multiworld.regions.extend(regions.values())
    for name in names:
        definition = data.regions[name]
        for destination in definition.exits:
            if destination in regions:
                regions[name].connect(regions[destination])
        regions[name].add_locations({
            key: data.locations[key].location_id for key in definition.locations
        })
    regions["Menu"].connect(regions[prefix + entry])
    state = CollectionState(multiworld)
    assert multiworld.get_location("MINOR_CHEST_SPRAY_PAINT_06", 1).can_reach(state) is spray_reachable
    assert multiworld.get_location("VITALITY_CHEST_CANDY_CONSTELLATION", 1).can_reach(state) is vitality_reachable
    assert not regions[parent].can_reach(state)


def test_candy_source_preserves_historical_identity_and_split_parent() -> None:
    location = data.locations["MINOR_CHEST_SPRAY_PAINT_06"]
    assert location.location_id == 3960505
    assert location.default_item == 3860205
    assert location.source_rom_offset == 0x008C5EA0
    assert location.parent_region == (
        "REGION_CANDY_CONSTELLATION/ROOM_9_CHEST_2__LOGIC__ENTRY_FROM_9_01"
    )
    assert "MINOR_CHEST_SPRAY_PAINT_06" not in data.regions[
        "REGION_CANDY_CONSTELLATION/ROOM_9_CHEST_2"
    ].locations


@pytest.mark.parametrize("item_key,item_id,reward_id,location_key,location_id", _COLLECTION_ITEMS)
def test_fixed_collection_identity_matches_exact_manifest_source(
    item_key: str, item_id: int, reward_id: int, location_key: str, location_id: int,
) -> None:
    manifest = json.loads((_WORLD / "data/minor_chest_manifest.json").read_text(encoding="utf-8"))
    sources = [entry for entry in manifest["entries"] if entry["native_reward_id"] == reward_id]
    assert len(sources) == 1
    source = sources[0]
    item = data.items[item_id]
    location = data.locations[location_key]
    assert data.item_key_to_id[item_key] == item_id
    assert item.classification == ItemClassification.useful
    assert "Unique" in item.tags
    assert location.location_id == location_id
    if location_key in {"MINOR_CHEST_MUSIC_NOTE_06"}:
        assert location.source_rom_offset is None  # physical compartment known; AP mapping is unresolved
        return
    assert location.default_item == item_id
    assert location.source_rom_offset == int(source["rom_offset"], 16)
    assert source["candidate_ap_room_keys"] == [location.parent_region.split("__LOGIC__", 1)[0]]
    assert location.bit_index is None  # ownership is never physical check identity
    assert "ExactEventLocation" in location.tags
    assert "NativeRewardCollection" in location.tags


@pytest.mark.parametrize("shard_mode", [RandomizeShards.option_vanilla, RandomizeShards.option_completely_random])
def test_fixed_collection_items_appear_once_without_changing_filler_capacity(shard_mode: int) -> None:
    world, locations = _build_world_for_create_items(shard_mode)
    world.create_items()
    counts = Counter(item.code for item in world.multiworld.itempool)
    assert {item_id: counts[item_id] for _, item_id, *_ in _COLLECTION_ITEMS} == {
        item_id: (0 if item_id in {3860219} else 1) for _, item_id, *_ in _COLLECTION_ITEMS
    }
    # New 23 locations consume exactly the 23 active unique useful items.
    assert len(world.multiworld.itempool) == sum(loc.item is None for loc in locations)


@pytest.mark.asyncio
@pytest.mark.parametrize("item_id", [entry[1] for entry in _COLLECTION_ITEMS])
async def test_fixed_collection_item_is_written_to_standard_mailbox(mock_bizhawk_context, item_id: int) -> None:
    client = KirbyAmClient()
    client.initialize_client()
    mock_bizhawk_context.items_received = [Mock(item=item_id, player=2)]
    with patch("worlds.kirbyam.client.bizhawk.read", new_callable=AsyncMock) as read, \
            patch("worlds.kirbyam.client.bizhawk.write", new_callable=AsyncMock) as write:
        read.return_value = [bytes(4), bytes(4), (123).to_bytes(4, "little")]
        await client._deliver_items(mock_bizhawk_context)
    write.assert_awaited_once()
    assert write.await_args is not None
    writes = dict((address, value) for address, value, _domain in write.await_args.args[1])
    assert writes[data.transport_ram_addresses["incoming_item_id"]] == item_id.to_bytes(4, "little")
    assert writes[data.transport_ram_addresses["incoming_item_flag"]] == (1).to_bytes(4, "little")
    assert client._delivery_pending is True


@pytest.mark.asyncio
@pytest.mark.parametrize("location_key", [
    entry[3] for entry in _COLLECTION_ITEMS if entry[1] not in {3860219}
])
async def test_fixed_collection_source_reports_only_its_physical_check(mock_bizhawk_context, location_key: str) -> None:
    client = KirbyAmClient()
    client.initialize_client()
    location = data.locations[location_key]
    assert location.source_rom_offset is not None
    ring = (0x08000000 + location.source_rom_offset).to_bytes(4, "little") + bytes(28)
    with patch("worlds.kirbyam.client.bizhawk.read", new_callable=AsyncMock) as read:
        read.return_value = [(1).to_bytes(4, "little"), ring]
        await client._poll_minor_chest_locations(mock_bizhawk_context)
    mock_bizhawk_context.send_msgs.assert_awaited_once_with([
        {"cmd": "LocationChecks", "locations": [location.location_id]},
    ])


def test_collection_runtime_policy_executes(tmp_path: Path) -> None:
    compiler = None if os.name == "nt" else shutil.which("cc") or shutil.which("clang") or shutil.which("gcc")
    if compiler is None:
        pytest.skip("no native C compiler available for collection payload contract")
    harness = r'''
#include "minor_chest_runtime_logic.h"
#define CHECK(value, code) do { if (!(value)) return code; } while (0)
int main(void) {
    uint32_t i, spray = 0x80000000u, music = 0x40000000u;
    for (i = 0; i < 14u; ++i) {
        uint32_t before = spray;
        CHECK(ap_apply_collection_item(200u + i, &spray, &music), 1);
        CHECK(spray == (before | (1u << i)), 2);
        CHECK(music == 0x40000000u, 3);
        CHECK(ap_apply_collection_item(200u + i, &spray, &music), 4);
        CHECK(spray == (before | (1u << i)), 5);
    }
    for (i = 0; i < 10u; ++i) {
        uint32_t before = music;
        CHECK(ap_apply_collection_item(214u + i, &spray, &music), 6);
        CHECK(music == (before | (1u << (i + 1u))), 7);
        CHECK((music & 1u) == 0u, 8); /* Sheets never unlock Sound Player. */
        CHECK(ap_apply_collection_item(214u + i, &spray, &music), 9);
        CHECK(music == (before | (1u << (i + 1u))), 10);
    }
    CHECK(spray == 0x80003FFFu && music == 0x400007FEu, 11);
    music |= 1u; /* Receiving/replaying sheets also preserves Sound Player. */
    CHECK(ap_apply_collection_item(214u, &spray, &music) && music == 0x400007FFu, 12);
    for (i = 0; i < 300u; ++i) {
        if (i >= 200u && i <= 223u) continue;
        CHECK(!ap_apply_collection_item(i, &spray, &music), 13);
        CHECK(spray == 0x80003FFFu && music == 0x400007FFu, 14);
    }
    CHECK(!ap_apply_collection_item(0xFFFFFFFFu, &spray, &music), 15);
    for (i = 0; i < 14u; ++i) {
        uint32_t native = 0x80000000u;
        ap_apply_native_collection_reward(&native, i, 14u, 1u);
        CHECK(native == 0x80000000u, 16);
        ap_apply_native_collection_reward(&native, i, 14u, 0u);
        CHECK(native == (0x80000000u | (1u << i)), 17);
    }
    for (i = 1; i <= 10u; ++i) {
        uint32_t native = 1u;
        ap_apply_native_collection_reward(&native, i, 11u, 1u);
        CHECK(native == 1u, 18);
        ap_apply_native_collection_reward(&native, i, 11u, 0u);
        CHECK(native == (1u | (1u << i)), 19);
    }
    spray = 0u;
    ap_apply_native_collection_reward(&spray, 14u, 14u, 0u);
    ap_apply_native_collection_reward(&spray, 32u, 64u, 0u);
    ap_apply_native_collection_reward(&spray, 0xFFFFFFFFu, 14u, 0u);
    CHECK(spray == 0u, 20);
    return 0;
}
'''
    source = tmp_path / "collection.c"
    executable = tmp_path / "collection"
    source.write_text(harness, encoding="utf-8")
    compiled = subprocess.run([
        compiler, "-std=c99", "-Wall", "-Wextra", "-Werror", "-I", str(_WORLD / "kirby_ap_payload"),
        str(source), "-o", str(executable),
    ], capture_output=True, text=True, check=False)
    assert compiled.returncode == 0, compiled.stdout + compiled.stderr
    executed = subprocess.run([str(executable)], capture_output=True, text=True, check=False)
    assert executed.returncode == 0, f"collection contract check {executed.returncode}: {executed.stderr}"


def test_collection_helpers_are_wired_to_real_payload_and_popup_preserves_registers() -> None:
    payload = (_WORLD / "kirby_ap_payload/ap_payload.c").read_text(encoding="utf-8")
    assert '#include "minor_chest_runtime_logic.h"' in payload
    assert "ap_apply_collection_item(ap_item_id - KIRBY_ITEM_ID_BASE_OFFSET," in payload
    assert payload.count("ap_apply_native_collection_reward(") == 2
    assert "&KIRBY_SPRAY_PAINT_FLAGS, reward_index, 14u" in payload
    assert "&KIRBY_MUSIC_PLAYER_AND_SHEETS_FLAGS, reward_index, 11u" in payload
    assert "&& *(volatile uint16_t*)(chest_obj_ptr + 0xE0u) <= 5u" in payload
    bridge = (_WORLD / "kirby_ap_payload/ap_hook.s").read_text(encoding="utf-8")
    assert "push {r1-r3, lr}" in bridge
    assert "pop {r1-r3}" in bridge
    assert "ldr r4, [r2, #0x4C]" in bridge
    assert "adds r0, r4, #0" in bridge


@pytest.mark.asyncio
@pytest.mark.parametrize("source_ptr", [0x088D3E64])
async def test_deferred_collection_sources_never_report_ap_checks(mock_bizhawk_context, source_ptr: int) -> None:
    client = KirbyAmClient()
    client.initialize_client()
    ring = source_ptr.to_bytes(4, "little") + bytes(28)
    with patch("worlds.kirbyam.client.bizhawk.read", new_callable=AsyncMock) as read:
        read.return_value = [(1).to_bytes(4, "little"), ring]
        await client._poll_minor_chest_locations(mock_bizhawk_context)
    mock_bizhawk_context.send_msgs.assert_not_awaited()


@pytest.mark.parametrize("entry,reachable", [
    ("ROOM_5_07", True),
    ("ROOM_5_14", False),
    ("ROOM_5_12", False),
    ("ROOM_5_18", False),
    ("ROOM_5_WARP", False),
])
def test_carrot_lower_chest_requires_verified_entry(entry: str, reachable: bool) -> None:
    """An isolated entrance must not collect across native 734's solid divider."""
    prefix = "REGION_CARROT_CASTLE/"
    parent = prefix + "ROOM_5_13"
    entries = ["ROOM_5_07", "ROOM_5_14", "ROOM_5_12", "ROOM_5_18", "ROOM_5_WARP"]
    names = [parent, *(prefix + name for name in entries),
             *(name for name in data.regions if name.startswith(parent + "__LOGIC__"))]
    multiworld = MultiWorld(1)
    multiworld.worlds[1] = KirbyAmWorld(multiworld, 1)
    regions = {name: Region(name, 1, multiworld) for name in ["Menu", *names]}
    multiworld.regions.extend(regions.values())
    for name in names:
        definition = data.regions[name]
        # Restrict to entering/leaving 5-13; unrelated external routes would
        # conceal which compartment owns the chest.
        for destination in definition.exits:
            if destination in regions and (name.startswith(parent) or destination.startswith(parent)):
                regions[name].connect(regions[destination])
        regions[name].add_locations({key: data.locations[key].location_id for key in definition.locations})
    regions["Menu"].connect(regions[prefix + entry])
    state = CollectionState(multiworld)
    assert multiworld.get_location("MINOR_CHEST_CARROT_CASTLE_5_13_OBJECT_02", 1).can_reach(state) is reachable
    assert not regions[parent].can_reach(state)
    assert not any("MINOR_CHEST_MUSIC_NOTE_06" in data.regions[name].locations for name in names)
    assert data.locations["MINOR_CHEST_MUSIC_NOTE_06"].source_rom_offset is None


def test_carrot_compartment_assignment_matches_pinned_native_evidence() -> None:
    evidence = json.loads((_WORLD / "dev-docs/carrot-room-evidence.json").read_text())
    rooms = {room["native_room_id"]: room for room in evidence["rooms"]}
    assert rooms[719]["ap_room_keys"] == ["REGION_CARROT_CASTLE/ROOM_5_07"]
    assert rooms[720]["ap_room_keys"] == ["REGION_CARROT_CASTLE/ROOM_5_14"]
    assert rooms[734]["ap_room_keys"] == ["REGION_CARROT_CASTLE/ROOM_5_13"]
    for native_id, spawn in [(719, [13, 14]), (720, [14, 5])]:
        entries = [t for t in rooms[native_id]["transitions"] if t["destination_room"] == 734]
        assert entries and all(t["destination_spawn_tiles"] == spawn for t in entries)
    assert {tuple(e["chest_position_pixels"]) for e in rooms[734]["completion_entries"]} == {
        (128, 120), (72, 264),
    }
    assert data.locations["MINOR_CHEST_CARROT_CASTLE_5_13_OBJECT_02"].parent_region.endswith(
        "__LOGIC__ENTRY_FROM_5_07"
    )
