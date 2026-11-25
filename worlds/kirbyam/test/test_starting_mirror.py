"""End-to-end AP world generation contracts for the tutorial mirror reward."""
from collections import Counter

import pytest

from BaseClasses import CollectionState
from test.general import setup_multiworld
from .. import KirbyAmWorld
from ..options import OPTION_GROUPS, RandomStartingMirror
from ..starting_mirror import (
    STARTING_MIRROR_ENTRANCE, STARTING_MIRROR_ITEM, TUTORIAL_WORLD_MAP_NAME,
    starting_mirror_candidates,
)

STEPS = ("generate_early", "create_regions", "create_items", "set_rules", "generate_basic")


def test_starting_mirror_defaults_and_eligible_routes():
    from ..data import data

    assert STARTING_MIRROR_ITEM == "Room 1-01 Mirror - Hub Connection"
    assert KirbyAmWorld.item_name_to_id[STARTING_MIRROR_ITEM] == 3860416
    assert "HubConnections" in data.items[3860416].tags
    assert RandomStartingMirror.default == 1
    assert any(group.name == "Make the game more random" and RandomStartingMirror in group.options for group in OPTION_GROUPS)
    assert set(starting_mirror_candidates(True)) == {
        STARTING_MIRROR_ITEM,
        "Rainbow Route East - Hub Connection",
        "Rainbow Route South - Hub Connection",
        "Rainbow Route West - Hub Connection",
    }
    assert set(starting_mirror_candidates(False)) == set(starting_mirror_candidates(True)) | {
        "Moonlight Mansion - Hub Connection",
        "Peppermint Palace East - Hub Connection",
        "Cabbage Cavern East - Hub Connection",
        "Cabbage Cavern West - Hub Connection",
    }


@pytest.mark.parametrize("keys", [0, 1])
@pytest.mark.parametrize("selected", range(8))
def test_each_eligible_tutorial_reward_opens_route(monkeypatch, keys, selected):
    candidates = starting_mirror_candidates(bool(keys))
    if selected >= len(candidates):
        pytest.skip("Area Keys exclude destinations that also need a key")
    reward = tuple(candidates)[selected]
    original = KirbyAmWorld._place_tutorial_hub_connection

    def choose_for_target(world, locations):
        world._starting_mirror_tutorial_item = reward
        return original(world, locations)

    monkeypatch.setattr(KirbyAmWorld, "_place_tutorial_hub_connection", choose_for_target)
    multiworld = setup_multiworld([KirbyAmWorld], steps=STEPS, seed=520,
                                  options={"random_starting_mirror": 1, "area_keys": keys, "room_sanity": 0})
    world = multiworld.worlds[1]
    chest = multiworld.get_location(TUTORIAL_WORLD_MAP_NAME, 1)
    assert chest.locked and chest.item.name == reward and chest.item.advancement
    items = Counter(item.name for item in multiworld.itempool)
    assert not items[reward]
    assert items[STARTING_MIRROR_ITEM] == int(reward != STARTING_MIRROR_ITEM)
    assert reward not in {item.name for item in multiworld.precollected_items[1]}
    assert len(multiworld.itempool) == len(multiworld.get_unfilled_locations())
    state = CollectionState(multiworld)
    start = multiworld.get_entrance(STARTING_MIRROR_ENTRANCE, 1)
    chosen = multiworld.get_entrance(candidates[reward], 1)
    assert chest.can_reach(state) and not start.access_rule(state) and not chosen.access_rule(state)
    state.collect(chest.item, True, chest)
    assert chosen.can_reach(state)
    assert start.can_reach(state) == (reward == STARTING_MIRROR_ITEM)
    state.collect(world.create_item(STARTING_MIRROR_ITEM), True)
    assert start.can_reach(state)
    assert world.fill_slot_data()["tracker"]["starting_mirror_tutorial_item"] == reward


def test_option_off_preserves_unlocked_mirror_and_randomized_chest():
    multiworld = setup_multiworld([KirbyAmWorld], steps=STEPS, seed=520, options={"random_starting_mirror": 0})
    assert multiworld.get_entrance(STARTING_MIRROR_ENTRANCE, 1).can_reach(CollectionState(multiworld))
    assert multiworld.get_location(TUTORIAL_WORLD_MAP_NAME, 1).item is None
    assert all(item.name != STARTING_MIRROR_ITEM for item in multiworld.itempool)


def test_board_only_object_preserves_the_native_central_list():
    import struct

    from ..kirby_ap_payload.patch_rom import (
        CENTRAL_NATIVE_PRELOAD, CENTRAL_NATIVE_TEMPLATES, CENTRAL_NATIVE_TEMPLATE_COUNT,
        CENTRAL_OBJECT_LIST_INFO, CENTRAL_TEMPLATE_SIZE, STARTING_MIRROR_OBJECT_MARKER,
        STARTING_MIRROR_OBJECT_SIZE, build_starting_mirror_object_writes,
    )

    rom = bytearray(CENTRAL_OBJECT_LIST_INFO + 12)
    struct.pack_into("<III", rom, CENTRAL_OBJECT_LIST_INFO,
                     0x08000000 + CENTRAL_NATIVE_TEMPLATES, 0x08000000 + CENTRAL_NATIVE_PRELOAD, 0x088B4CBC)
    for index in range(CENTRAL_NATIVE_TEMPLATE_COUNT):
        offset = CENTRAL_NATIVE_TEMPLATES + index * CENTRAL_TEMPLATE_SIZE
        rom[offset:offset + 4] = bytes((1, CENTRAL_TEMPLATE_SIZE, 0, index))
    rom[CENTRAL_NATIVE_PRELOAD:CENTRAL_NATIVE_PRELOAD + 5] = bytes((0x65, 0x8C, 0x8E, 0x98, 0xFF))
    address = 0x09004500
    reserved = STARTING_MIRROR_OBJECT_MARKER.ljust(STARTING_MIRROR_OBJECT_SIZE, b"\0")

    writes = build_starting_mirror_object_writes(rom, address, reserved)
    objects = writes[address - 0x08000000]
    length = CENTRAL_NATIVE_TEMPLATE_COUNT * CENTRAL_TEMPLATE_SIZE
    assert objects[:length] == rom[CENTRAL_NATIVE_TEMPLATES:CENTRAL_NATIVE_TEMPLATES + length]
    assert struct.unpack_from("<hh", objects, length + 6) == (312, 240)
    assert objects[length + 12] == 0x99
    end = length + CENTRAL_TEMPLATE_SIZE
    assert objects[end:end + 2] == b"\0\0"
    assert objects[-8:] == bytes((0x65, 0x8C, 0x8E, 0x98, 0x99, 0xFF, 0, 0))
    assert writes[CENTRAL_OBJECT_LIST_INFO] == struct.pack("<II", address, address + len(objects) - 8)

    rom[CENTRAL_OBJECT_LIST_INFO] ^= 1
    with pytest.raises(SystemExit, match="Unexpected Central Circle object-list pointers"):
        build_starting_mirror_object_writes(rom, address, reserved)


@pytest.mark.parametrize("keys", [0, 1])
def test_generated_archive_places_one_starting_route_without_precollect(tmp_path, keys):
    from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive

    player = tmp_path / "player.yaml"
    player.write_text(
        "name: Starting Mirror\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n"
        f"  random_starting_mirror: true\n  area_keys: {keys}\n  room_sanity: 0\n  shards: 2\n",
        encoding="utf-8",
    )
    decoded = load_multidata_from_archive(
        generate_archive_from_fixture(player, tmp_path / "output", seed=520 + keys)
    )
    slot = decoded["slot_data"][1]
    assert slot["random_starting_mirror"]
    reward = slot["tracker"]["starting_mirror_tutorial_item"]
    assert reward in starting_mirror_candidates(bool(keys))
    reward_id = KirbyAmWorld.item_name_to_id[reward]
    locations = decoded["locations"][1]
    assert locations[3960209][:2] == (reward_id, 1)
    assert reward_id not in decoded["precollected_items"][1]
    assert sum(item[0] == reward_id for item in locations.values()) == 1
    assert sum(item[0] == KirbyAmWorld.item_name_to_id[STARTING_MIRROR_ITEM]
               for item in locations.values()) == 1
