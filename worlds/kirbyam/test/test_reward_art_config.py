"""Seed reward art follows final physical placement, not delivery or recipient."""
from __future__ import annotations

from pathlib import Path
import shutil
import struct
import subprocess
from typing import Any, cast

from BaseClasses import Item, ItemClassification, Location
import pytest
from worlds.Files import APTokenTypes

from ..data import LocationCategory, data, load_json_data
from ..items import KirbyAmItem
from ..locations import KirbyAmLocation
from ..options import AbilityRandomizationMode
from ..reward_art_config import (
    REWARD_ART_CONFIG_MAGIC,
    REWARD_ART_CONFIG_MAX_KEYS,
    REWARD_ART_CONFIG_ROM_OFFSET,
    REWARD_ART_CONFIG_SIZE,
    REWARD_ART_CONFIG_VARIANT_OFFSET,
    build_reward_art_config,
    reward_art_location_key,
)
from ..reward_art_types import (
    KIRBY_CONSUMABLE_ART_BY_ITEM_CODE,
    KIRBY_NATIVE_ART_BY_ITEM_CODE,
    KIRBY_STATUE_ART_BY_ITEM_CODE,
    RewardArt,
    reward_art_for_item,
)
from ..rom import KirbyAmProcedurePatch, write_tokens
from .test_rom_tokens import _make_world


class ForeignItem(Item):
    game = "Different Game"


def _location(key: str, item: Item | None = None) -> KirbyAmLocation:
    metadata = data.locations[key]
    loc = KirbyAmLocation(1, metadata.label, metadata.location_id, key=key)
    if item is not None:
        loc.place_locked_item(item)
    return loc


def _variants(payload: bytes) -> dict[int, RewardArt]:
    assert len(payload) == REWARD_ART_CONFIG_SIZE
    magic, count = struct.unpack_from("<4sI", payload)
    assert magic == REWARD_ART_CONFIG_MAGIC
    assert count <= REWARD_ART_CONFIG_MAX_KEYS
    key_end = 8 + count * 4
    art_start = REWARD_ART_CONFIG_VARIANT_OFFSET
    art_end = art_start + count
    assert not any(payload[key_end:art_start])
    assert not any(payload[art_end:])
    keys = struct.unpack_from(f"<{count}I", payload, 8)
    assert list(keys) == sorted(set(keys))
    return {key: RewardArt(art) for key, art in zip(keys, payload[art_start:art_end])}


def test_location_families_have_disjoint_native_identities() -> None:
    expected_categories = {
        LocationCategory.BOSS_DEFEAT: 2,
        LocationCategory.MAP_CHEST: 9,
        LocationCategory.VITALITY_CHEST: 10,
        LocationCategory.SOUND_PLAYER_CHEST: 11,
        LocationCategory.ROOM_SANITY: 12,
        LocationCategory.HUB_SWITCH: 13,
        LocationCategory.MINOR_CHEST: 14,
        LocationCategory.AREA_VISIT: 15,
        LocationCategory.LEVER: 3,
        LocationCategory.GOAL_GAME: 4,
    }
    keys: dict[int, str] = {}
    by_category: set[LocationCategory] = set()
    for location in data.locations.values():
        key = reward_art_location_key(location)
        category = location.category
        if category not in expected_categories:
            assert key is None
            continue
        index = location.source_rom_offset if category == LocationCategory.MINOR_CHEST else location.bit_index
        assert index is not None and key == (expected_categories[category] << 24) | index
        assert key and key not in keys, (location.name, keys.get(key))
        keys[key] = location.name
        by_category.add(category)
    assert by_category == expected_categories.keys()
    assert len(keys) <= REWARD_ART_CONFIG_MAX_KEYS


def test_config_includes_outgoing_cross_game_traps_and_ignores_non_traps() -> None:
    local_trap = _location("MAJOR_CHEST_WORLD_MAP", Item("Local Trap", ItemClassification.trap, 221, 1))
    outgoing_trap = _location("MAJOR_CHEST_RAINBOW_ROUTE", ForeignItem("Outgoing Trap", ItemClassification.trap, 222, 2))
    mixed_trap = _location("HUB_SWITCH_MOONLIGHT", ForeignItem(
        "Trap With Extra Flag", ItemClassification.trap | ItemClassification.useful, 223, 2,
    ))
    ordinary = _location("SOUND_PLAYER_CHEST", ForeignItem("Outgoing Useful", ItemClassification.useful, 224, 2))
    unresolved = _location("BOSS_DEFEAT_1")
    event = _location("BOSS_DEFEAT_2", Item("Not a network item", ItemClassification.trap, None, 1))
    logical_goal = _location("GOAL_DARK_MIND", Item("Unused Goal", ItemClassification.trap, 221, 1))
    unknown = KirbyAmLocation(1, "Unknown", 12345, key="MISSING")
    unknown.place_locked_item(Item("Trap", ItemClassification.trap, 221, 1))
    foreign_check = Location(2, "Foreign check", 3960209)
    foreign_check.place_locked_item(Item("Incoming Trap", ItemClassification.trap, 221, 1))
    placements = [outgoing_trap, ordinary, logical_goal, local_trap, event, unresolved, mixed_trap, unknown, foreign_check]
    config = build_reward_art_config(placements)
    assert config == build_reward_art_config(reversed(placements))
    assert _variants(config) == dict.fromkeys((0x09000000, 0x09000001, 0x0D000001), RewardArt.TRAP)


def test_trap_cosmetics_are_written_as_production_seed_tokens() -> None:
    world = _make_world(AbilityRandomizationMode.option_off)
    patch = KirbyAmProcedurePatch()
    local_trap = _location("BOSS_DEFEAT_1", Item("Local Trap", ItemClassification.trap, 221, 1))
    outgoing_trap = _location("HUB_SWITCH_MOONLIGHT", ForeignItem("Outgoing Trap", ItemClassification.trap, 222, 2))
    write_tokens(cast(Any, world), patch, filled_locations=(outgoing_trap, local_trap))
    blob = patch.get_file("token_data.bin")
    count, = struct.unpack_from("<I", blob)
    pos = 4
    writes: list[bytes] = []
    for _ in range(count):
        kind, offset, length = struct.unpack_from("<BII", blob, pos)
        pos += 9
        if offset == REWARD_ART_CONFIG_ROM_OFFSET:
            assert kind == APTokenTypes.WRITE
            writes.append(blob[pos:pos + length])
        pos += length
    assert pos == len(blob)
    payload, = writes
    assert _variants(payload) == dict.fromkeys((0x02000000, 0x0D000001), RewardArt.TRAP)


def test_empty_config_clears_entire_reserved_window() -> None:
    stride = REWARD_ART_CONFIG_SIZE
    assert len(build_reward_art_config(())) == stride
    assert build_reward_art_config(()) == b"ARV3" + bytes(stride - 4)


def test_python_tokens_match_native_lookup_abi(tmp_path: Path) -> None:
    cc = shutil.which("cc")
    if cc is None:
        pytest.skip("requires a native C compiler")
    item = Item("Local Trap", ItemClassification.trap, 221, 1)
    token = build_reward_art_config((
        _location("MAJOR_CHEST_WORLD_MAP", item),
        _location("HUB_SWITCH_MOONLIGHT", ForeignItem("Outgoing", ItemClassification.trap, 222, 2)),
        _location("LEVER_MOONLIGHT_MANSION_2_11", KirbyAmItem("Max Tomato", ItemClassification.filler, 3860028, 1)),
        _location("GOAL_GAME_1_GOAL_2", KirbyAmItem("1 Up", ItemClassification.filler, 3860001, 1)),
        _location("BOSS_DEFEAT_1", KirbyAmItem("Music Sheet #10", ItemClassification.useful, 3860223, 1)),
        _location("BOSS_DEFEAT_2", KirbyAmItem("Phone a Friend", ItemClassification.progression, 3860501, 1)),
        _location("BOSS_DEFEAT_3", KirbyAmItem(
            "Moonlight Mansion - Hub Connection", ItemClassification.progression, 3860402, 1,
        )),
        _location("BOSS_DEFEAT_4", KirbyAmItem(
            "Moonlight Mansion 2-11 - Lever Wall", ItemClassification.progression, 3860037, 1,
        )),
        _location("BOSS_DEFEAT_5", KirbyAmItem("Burning Ability", ItemClassification.progression, 3860103, 1)),
        _location("BOSS_DEFEAT_6", KirbyAmItem("Parasol Ability", ItemClassification.progression, 3860105, 1)),
    ))
    (tmp_path / "abi.bin").write_bytes(token)
    source = tmp_path / "native.c"
    source.write_text(r'''
#include <assert.h>
#include <stdio.h>
#include "reward_art_config.h"

int main(void) {
    struct ApRewardArtConfig config;
    FILE *f = fopen("abi.bin", "rb");
    assert(f && fread(&config, 1, sizeof(config), f) == sizeof(config));
    fclose(f);
    assert(config.marker == AP_REWARD_ART_MAGIC && config.count == 10u);
    assert(ap_reward_art_from_config(&config, AP_REWARD_KEY(AP_REWARD_MAP_CHEST, 0)) == AP_REWARD_TRAP);
    assert(ap_reward_art_from_config(&config, AP_REWARD_KEY(AP_REWARD_SWITCH, 1)) == AP_REWARD_TRAP);
    assert(ap_reward_art_from_config(&config, AP_REWARD_KEY(AP_REWARD_MAP_CHEST, 1)) == AP_REWARD_GEM);
    assert(ap_reward_art_from_config(&config, AP_REWARD_KEY(AP_REWARD_GOAL, 1)) == 2u);
    assert(ap_reward_art_from_config(&config, AP_REWARD_KEY(AP_REWARD_LEVER, 0)) == 6u);
    assert(ap_reward_art_from_config(&config, AP_REWARD_KEY(AP_REWARD_BOSS, 0)) == 43u);
    assert(ap_reward_art_from_config(&config, AP_REWARD_KEY(AP_REWARD_BOSS, 1)) == 45u);
    assert(ap_reward_art_from_config(&config, AP_REWARD_KEY(AP_REWARD_BOSS, 2)) == 46u);
    assert(ap_reward_art_from_config(&config, AP_REWARD_KEY(AP_REWARD_BOSS, 3)) == 47u);
    assert(ap_reward_art_from_config(&config, AP_REWARD_KEY(AP_REWARD_BOSS, 4)) == 49u);
    assert(ap_reward_art_from_config(&config, AP_REWARD_KEY(AP_REWARD_BOSS, 5)) == 66u);
    assert(ap_reward_art_from_config(&config, 0u) == AP_REWARD_GEM);
    config.count = AP_REWARD_ART_CAPACITY + 1u;
    assert(ap_reward_art_from_config(&config, AP_REWARD_KEY(AP_REWARD_MAP_CHEST, 0)) == AP_REWARD_GEM);
    config.count = 10u;
    config.marker = 0x32565241u; /* Older packed ARV2 data is not interpreted as ARV3. */
    assert(ap_reward_art_from_config(&config, AP_REWARD_KEY(AP_REWARD_MAP_CHEST, 0)) == AP_REWARD_GEM);
    config.marker = AP_REWARD_ART_MAGIC;
    config.variants[8] = 0xFFu;
    assert(ap_reward_art_from_config(&config, AP_REWARD_KEY(AP_REWARD_MAP_CHEST, 0)) == AP_REWARD_GEM);
    return 0;
}
''')
    executable = tmp_path / "native"
    include = Path(__file__).resolve().parents[1] / "kirby_ap_payload"
    subprocess.run([cc, "-std=c11", "-Wall", "-Wextra", "-Werror", "-I", str(include),
                    "-o", str(executable), str(source)], check=True)
    subprocess.run([str(executable)], check=True, cwd=tmp_path)


def test_same_generated_seed_uses_each_slots_physical_placements(tmp_path: Path) -> None:
    """Exercise Generate -> Fill -> generate_output, including an outgoing trap."""
    from io import BytesIO
    from zipfile import ZipFile
    import Generate
    import Main
    from .support.integration_generation import load_multidata_from_archive

    players = tmp_path / "players"
    players.mkdir()
    output = tmp_path / "output"
    output.mkdir()
    common = (
        "game: Kirby & The Amazing Mirror\n"
        "Kirby & The Amazing Mirror:\n"
        "  ability_gating: false\n"
        "  area_keys: false\n"
        "  ability_randomization_mode: 0\n"
        "  room_sanity: false\n"
        "  random_starting_mirror: false\n"
    )
    (players / "1.yaml").write_text("name: Trap One\n" + common + (
        "  enable_traps: true\n"
        "  trap_fill_percentage: 100\n"
        "  plando_items:\n"
        "    - item: Health Down Trap\n"
        "      location: Tutorial World Map - Big Chest\n"
        "      force: true\n"
        "    - item: Battery Drain Trap\n"
        "      location: Tutorial World Map - Big Chest\n"
        "      world: Trap Two\n"
        "      force: true\n"
    ))
    (players / "2.yaml").write_text("name: Trap Two\n" + common + (
        "  enable_traps: true\n"
        "  trap_fill_percentage: 100\n"
    ))
    (players / "3.yaml").write_text("name: Ordinary Three\n" + common + (
        "  enable_traps: false\n"
        "  plando_items:\n"
        "    - item: Rainbow Route - Map\n"
        "      location: Tutorial World Map - Big Chest\n"
        "      force: true\n"
    ))

    options = Generate.mystery_argparse([
        "--multi", "3", "--seed", "1086", "--plando", "items",
        "--player_files_path", str(players), "--outputpath", str(output),
    ])
    options.weights_file_path = None
    options.meta_file_path = None
    Main.main(*Generate.main(options))
    archive_path, = output.glob("*.zip")

    location = data.locations["MAJOR_CHEST_WORLD_MAP"]
    key = reward_art_location_key(location)
    slots = load_multidata_from_archive(archive_path)["locations"]
    expected_placements = (
        (1, 3860032, 1, RewardArt.TRAP),
        (2, 3860035, 1, RewardArt.TRAP),
        (3, 3860024, 3, RewardArt.MAP_RAINBOW),
    )
    with ZipFile(archive_path) as archive:
        for slot, expected_item, expected_recipient, expected_art in expected_placements:
            placed_item, recipient, _ = slots[slot][location.location_id]
            assert (placed_item, recipient) == (expected_item, expected_recipient)
            name, = (n for n in archive.namelist() if n.endswith(".apkirbyam") and f"_P{slot}_" in n)
            with ZipFile(BytesIO(archive.read(name))) as patch:
                token_data = patch.read("token_data.bin")
            pos = 4
            tokens = {}
            for _ in range(struct.unpack_from("<I", token_data)[0]):
                kind, offset, length = struct.unpack_from("<BII", token_data, pos)
                pos += 9
                if kind == APTokenTypes.WRITE:
                    tokens[offset] = token_data[pos:pos + length]
                pos += length
            art = _variants(tokens[REWARD_ART_CONFIG_ROM_OFFSET]).get(key, RewardArt.GEM)
            assert art == expected_art


@pytest.mark.parametrize("code,art", KIRBY_NATIVE_ART_BY_ITEM_CODE.items())
def test_native_art_requires_exact_known_local_kirby_item(code: int, art: RewardArt) -> None:
    name = data.items[code].label
    local = _location("BOSS_DEFEAT_1", KirbyAmItem(name, ItemClassification.filler, code, 1))
    outbound = _location("BOSS_DEFEAT_2", KirbyAmItem(name, ItemClassification.filler, code, 2))
    foreign = _location("BOSS_DEFEAT_3", ForeignItem(name, ItemClassification.filler, code, 1))
    mixed_trap = _location("BOSS_DEFEAT_4", KirbyAmItem(
        name, ItemClassification.trap | ItemClassification.useful, code, 1,
    ))
    assert _variants(build_reward_art_config((local, outbound, foreign, mixed_trap))) == {
        0x02000000: art,
        0x02000003: RewardArt.TRAP,
    }


def test_unknown_local_kirby_item_and_unsupported_item_keep_generic() -> None:
    class UnknownKirbyItem(Item):
        game = "Kirby & The Amazing Mirror"

    unknown = _location("BOSS_DEFEAT_1", UnknownKirbyItem("Unknown", ItemClassification.filler, 999999, 1))
    area_key = _location("BOSS_DEFEAT_2", KirbyAmItem(
        "Moonlight Mansion - Area Key", ItemClassification.progression, 3860041, 1,
    ))
    ability = _location("BOSS_DEFEAT_3", KirbyAmItem("Sleep Ability", ItemClassification.progression, 3860111, 1))
    copy_room = _location("BOSS_DEFEAT_4", KirbyAmItem(
        "Copy Ability Room Access", ItemClassification.progression, 3860500, 1,
    ))
    assert _variants(build_reward_art_config((unknown, area_key, ability, copy_room))) == {
        0x02000002: RewardArt.ABILITY_SLEEP,
    }


def test_consumable_art_registry_matches_the_seven_native_items() -> None:
    assert {art: data.items[code].label for code, art in KIRBY_CONSUMABLE_ART_BY_ITEM_CODE.items()} == {
        RewardArt.ONE_UP: "1 Up",
        RewardArt.FOOD: "Small Food",
        RewardArt.DRINK: "Energy Drink",
        RewardArt.MEAT: "Hunk of Meat",
        RewardArt.TOMATO: "Max Tomato",
        RewardArt.CANDY: "Invincibility Candy",
        RewardArt.BATTERY: "Cell Phone Battery",
    }


def test_native_art_registry_matches_the_curated_areas_and_complete_item_families() -> None:
    native = KIRBY_NATIVE_ART_BY_ITEM_CODE
    areas = ("Rainbow Route", "Moonlight Mansion", "Cabbage Cavern", "Mustard Mountain",
             "Carrot Castle", "Olive Ocean", "Peppermint Palace", "Radish Ruins", "Candy Constellation")
    assert len(native) == 104
    for area_index, label in enumerate(areas, 9):
        (code,) = (code for code, art in native.items() if art == area_index)
        assert data.items[code].label == f"{label} - Map"
    for index in range(14):
        assert data.items[3860200 + index].label == f"Spray Paint #{index + 1}"
        assert native[3860200 + index] == 20 + index
    for index in range(10):
        assert data.items[3860214 + index].label == f"Music Sheet #{index + 1}"
        assert native[3860214 + index] == 34 + index
    assert {code for code, art in native.items() if art == RewardArt.VITALITY} == {
        3860018, 3860019, 3860020, 3860021, 3860224, 3860225, 3860226, 3860227, 3860228
    }
    assert {code for code, art in native.items() if art == RewardArt.SHARD} == set(range(3860002, 3860010))
    assert native[3860025] == RewardArt.SOUND_PLAYER
    assert {code for code, art in native.items() if art == RewardArt.PHONE} == {3860501}
    assert {code for code, art in native.items() if art == RewardArt.HUB_SWITCH} == set(range(3860401, 3860417))
    assert {code for code, art in native.items() if art == RewardArt.LEVER_WALL} == set(range(3860037, 3860041))


def test_generated_seed_preserves_variant_identity_across_treasure_and_access_families(tmp_path: Path) -> None:
    from io import BytesIO
    from zipfile import ZipFile

    import Generate
    import Main
    from .support.integration_generation import load_multidata_from_archive

    placements = (
        ("MAJOR_CHEST_WORLD_MAP", 3860012, RewardArt.MAP_CANDY),
        ("HUB_SWITCH_MOONLIGHT", 3860018, RewardArt.VITALITY),
        ("LEVER_MOONLIGHT_MANSION_2_11", 3860025, RewardArt.SOUND_PLAYER),
        ("ROOM_SANITY_1_CENTRAL_CIRCLE", 3860213, RewardArt.PAINT_14),
        ("BOSS_DEFEAT_1", 3860223, RewardArt.SHEET_10),
        ("AREA_VISIT_1_RAINBOW_ROUTE", 3860002, RewardArt.SHARD),
        ("ROOM_SANITY_1_01", 3860037, RewardArt.LEVER_WALL),
        ("ROOM_SANITY_1_02", 3860415, RewardArt.HUB_SWITCH),
        ("ROOM_SANITY_1_04", 3860501, RewardArt.PHONE),
    )
    players = tmp_path / "players"
    players.mkdir()
    output = tmp_path / "output"
    output.mkdir()
    fixture = players / "treasures.yaml"
    yaml = (
        "name: Treasure Families\n"
        "game: Kirby & The Amazing Mirror\n"
        "Kirby & The Amazing Mirror:\n"
        "  ability_gating: false\n"
        "  area_keys: false\n"
        "  ability_randomization_mode: 0\n"
        "  room_sanity: true\n"
        "  random_starting_mirror: false\n"
        "  plando_items:\n"
    )
    for key, item_code, _ in placements:
        yaml += (f"    - item: '{data.items[item_code].label}'\n"
                 f"      location: '{data.locations[key].label}'\n"
                 "      force: true\n")
    fixture.write_text(yaml)
    options = Generate.mystery_argparse([
        "--multi", "1", "--seed", "1086", "--plando", "items",
        "--player_files_path", str(players), "--outputpath", str(output),
    ])
    options.weights_file_path = None
    options.meta_file_path = None
    Main.main(*Generate.main(options))
    archive_path, = output.glob("*.zip")
    slot = load_multidata_from_archive(archive_path)["locations"][1]
    with ZipFile(archive_path) as archive:
        name, = (name for name in archive.namelist() if name.endswith(".apkirbyam"))
        with ZipFile(BytesIO(archive.read(name))) as patch:
            token_data = patch.read("token_data.bin")

    pos = 4
    for _ in range(struct.unpack_from("<I", token_data)[0]):
        kind, offset, length = struct.unpack_from("<BII", token_data, pos)
        pos += 9
        if kind == APTokenTypes.WRITE and offset == REWARD_ART_CONFIG_ROM_OFFSET:
            break
        pos += length
    else:
        pytest.fail("Generated archive is missing ARV3 reward art token")
    variants = _variants(token_data[pos:pos + length])
    for key, item_code, art in placements:
        location = data.locations[key]
        assert slot[location.location_id][:2] == (item_code, 1)
        assert variants[reward_art_location_key(location)] == art


def test_ability_art_registry_matches_native_statue_subtypes_only() -> None:
    inventory = load_json_data("ability_source_inventory.json")
    statue_abilities = {
        (row["type_id"], row["subtype1"]): row["native_grant"]
        for row in inventory["placements"]
        if row["source_type"] == "statue" and row["native_room"] == 970
    }
    vanilla_names_to_runtime_id = load_json_data("abilities.json")
    native = KIRBY_STATUE_ART_BY_ITEM_CODE
    assert len(native) == len(statue_abilities) == 19

    # Retail 0x2D1 variants 11–29 are grouped by object families 1, 2, 4,
    # 3, not numeric order of the native object type IDs.
    first_retail_variant = {146: 11, 147: 19, 148: 29, 149: 26}
    for (native_type, subtype), name in statue_abilities.items():
        retail_variant = first_retail_variant[native_type] + subtype
        art = 48 + retail_variant - 11
        code = 3860100 + vanilla_names_to_runtime_id[name]["runtime_ability_id"]
        assert native[code] == art
        assert KIRBY_NATIVE_ART_BY_ITEM_CODE[code] == art
        assert data.items[code].label == f"{name} Ability"

    assert (146, 1, "Burning", 291, "0x088C263C") in {
        (row["type_id"], row["subtype1"], row["native_grant"], row["native_room"], row["template_address"])
        for row in inventory["placements"]
        if row["source_type"] == "statue"
    }
    nonstatue = {"Sleep": 11, "Cook": 12, "UFO": 14, "Magic": 21, "Mini": 23, "Crash": 24}
    for name, runtime_id in nonstatue.items():
        ap_code = 3860100 + runtime_id
        assert ap_code not in native
        item = KirbyAmItem(f"{name} Ability", ItemClassification.progression, ap_code, 1)
        assert reward_art_for_item(item, 1) == RewardArt[f"ABILITY_{name.upper()}"]
    assert 3860126 not in native  # Master stand/sword is not a CopyAbilityObject.


def test_generated_burning_and_sleep_use_their_statue_sprites(tmp_path: Path) -> None:
    from io import BytesIO
    from zipfile import ZipFile
    import Generate
    import Main
    from .support.integration_generation import load_multidata_from_archive

    players = tmp_path / "players"
    players.mkdir()
    output = tmp_path / "output"
    output.mkdir()
    (players / "1.yaml").write_text(
        'name: Statue Ability\n'
        'game: Kirby & The Amazing Mirror\n'
        'Kirby & The Amazing Mirror:\n'
        '  ability_gating: true\n'
        '  ability_randomization_mode: 0\n'
        '  area_keys: false\n'
        '  room_sanity: true\n'
        '  accessibility: full\n'
        '  enable_traps: false\n'
        '  random_starting_mirror: false\n'
        '  plando_items:\n'
        '    - item: Burning Ability\n'
        '      location: Tutorial World Map - Big Chest\n'
        '      force: true\n'
        '    - item: Sleep Ability\n'
        '      location: Rainbow Route - First Visit\n'
        '      force: true\n'
    )
    options = Generate.mystery_argparse([
        "--multi", "1", "--seed", "1086", "--plando", "items",
        "--player_files_path", str(players), "--outputpath", str(output),
    ])
    options.weights_file_path = None
    options.meta_file_path = None
    Main.main(*Generate.main(options))
    archive_path, = output.glob("*.zip")
    slot = load_multidata_from_archive(archive_path)["locations"][1]
    with ZipFile(archive_path) as archive:
        name, = (name for name in archive.namelist() if name.endswith(".apkirbyam"))
        with ZipFile(BytesIO(archive.read(name))) as patch:
            token_data = patch.read("token_data.bin")
    pos = 4
    for _ in range(struct.unpack_from("<I", token_data)[0]):
        kind, offset, length = struct.unpack_from("<BII", token_data, pos)
        pos += 9
        if kind == APTokenTypes.WRITE and offset == REWARD_ART_CONFIG_ROM_OFFSET:
            break
        pos += length
    else:
        pytest.fail("Generated archive is missing the ARV3 reward art token")
    variants = _variants(token_data[pos:pos + length])
    chest = data.locations["MAJOR_CHEST_WORLD_MAP"]
    area = data.locations["AREA_VISIT_1_RAINBOW_ROUTE"]
    assert slot[chest.location_id][:2] == (3860103, 1)
    assert slot[area.location_id][:2] == (3860111, 1)
    assert variants[reward_art_location_key(chest)] == RewardArt.ABILITY_BURNING
    assert variants[reward_art_location_key(area)] == RewardArt.ABILITY_SLEEP


def test_hub_connection_art_tracks_item_catalog_tags() -> None:
    from ..data import data
    from ..reward_art_types import KIRBY_NATIVE_ART_BY_ITEM_CODE, RewardArt

    hub_ids = {code for code, item in data.items.items() if "HubConnections" in item.tags}
    assert hub_ids
    assert {code for code, art in KIRBY_NATIVE_ART_BY_ITEM_CODE.items()
            if art == RewardArt.HUB_SWITCH} == hub_ids
