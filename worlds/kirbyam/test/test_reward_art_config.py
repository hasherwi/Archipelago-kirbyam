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

from ..data import LocationCategory, data
from ..locations import KirbyAmLocation
from ..options import AbilityRandomizationMode
from ..reward_art_config import (
    REWARD_ART_CONFIG_MAGIC,
    REWARD_ART_CONFIG_MAX_KEYS,
    REWARD_ART_CONFIG_ROM_OFFSET,
    REWARD_ART_CONFIG_SIZE,
    build_reward_art_config,
    reward_art_location_key,
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


def _keys(payload: bytes) -> tuple[int, ...]:
    assert len(payload) == REWARD_ART_CONFIG_SIZE
    magic, count = struct.unpack_from("<4sI", payload)
    assert magic == REWARD_ART_CONFIG_MAGIC
    assert count <= REWARD_ART_CONFIG_MAX_KEYS
    end = 8 + count * 4
    assert not any(payload[end:])
    return struct.unpack_from(f"<{count}I", payload, 8)


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
        LocationCategory.LEVER: 16,
        LocationCategory.GOAL_GAME: 17,
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
        assert key not in keys, (location.name, keys.get(key))
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
    assert _keys(config) == (0x09000000, 0x09000001, 0x0D000001)


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
    assert _keys(payload) == (0x02000000, 0x0D000001)


def test_empty_config_clears_entire_reserved_window() -> None:
    stride = REWARD_ART_CONFIG_SIZE
    assert len(build_reward_art_config(())) == stride
    assert build_reward_art_config(()) == b"ARV1" + bytes(stride - 4)


def test_python_tokens_match_native_lookup_abi(tmp_path: Path) -> None:
    cc = shutil.which("cc")
    if cc is None:
        pytest.skip("requires a native C compiler")
    item = Item("Local Trap", ItemClassification.trap, 221, 1)
    token = build_reward_art_config((
        _location("MAJOR_CHEST_WORLD_MAP", item),
        _location("HUB_SWITCH_MOONLIGHT", ForeignItem("Outgoing", ItemClassification.trap, 222, 2)),
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
    assert(config.marker == AP_REWARD_ART_MAGIC && config.count == 2u);
    assert(ap_reward_art_from_config(&config, AP_REWARD_KEY(AP_REWARD_MAP_CHEST, 0)) == AP_REWARD_TRAP);
    assert(ap_reward_art_from_config(&config, AP_REWARD_KEY(AP_REWARD_SWITCH, 1)) == AP_REWARD_TRAP);
    assert(ap_reward_art_from_config(&config, AP_REWARD_KEY(AP_REWARD_MAP_CHEST, 1)) == AP_REWARD_GEM);
    assert(ap_reward_art_from_config(&config, AP_REWARD_KEY(AP_REWARD_GOAL, 1)) == AP_REWARD_GEM);
    config.count = AP_REWARD_ART_CAPACITY + 1u;
    assert(ap_reward_art_from_config(&config, AP_REWARD_KEY(AP_REWARD_MAP_CHEST, 0)) == AP_REWARD_GEM);
    config.count = 2u;
    config.marker = 0u;
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
        (1, 3860032, 1, True),
        (2, 3860035, 1, True),
        (3, 3860024, 3, False),
    )
    with ZipFile(archive_path) as archive:
        for slot, expected_item, expected_recipient, should_show_trap in expected_placements:
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
            assert (key in _keys(tokens[REWARD_ART_CONFIG_ROM_OFFSET])) == should_show_trap
