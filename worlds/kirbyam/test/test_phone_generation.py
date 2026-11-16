"""Canonical intent tests only; these do not activate a generation profile."""
from pathlib import Path
from typing import Any

import pytest

from ..phone_generation import (
    PHONE_DISABLED_CONFIG, phone_patch_config, validate_phone_patch_intent,
)
from ..phone_protocol import PHONE_ENABLED_CONFIG


@pytest.mark.parametrize("enabled,expected", [(False, PHONE_DISABLED_CONFIG), (True, PHONE_ENABLED_CONFIG)])
def test_exact_phone_intent(enabled: bool, expected: bytes) -> None:
    assert phone_patch_config(enabled) == expected
    assert validate_phone_patch_intent(expected) is expected


@pytest.mark.parametrize("value", [0, 1, None, "on", b"1", [], {}])
def test_phone_intent_rejects_non_boolean_authoring(value: object) -> None:
    with pytest.raises(ValueError, match="boolean"):
        phone_patch_config(value)  # type: ignore[arg-type]


@pytest.mark.parametrize("value", [
    b"", PHONE_DISABLED_CONFIG[:-1], PHONE_DISABLED_CONFIG + b"\0",
    b"APPHN02\0" + bytes(4), b"APPHN01X" + bytes(4), bytes(12),
    b"APPHN01\0\2\0\0\0", b"APPHN01\0\0\1\0\0",
    bytearray(PHONE_DISABLED_CONFIG), memoryview(PHONE_DISABLED_CONFIG), None,
])
def test_phone_intent_rejects_noncanonical_bytes(value: object) -> None:
    with pytest.raises(ValueError, match="invalid Phone patch intent"):
        validate_phone_patch_intent(value)  # type: ignore[arg-type]


@pytest.mark.parametrize("enabled", [False, True])
def test_final_guard_requires_matching_explicit_intent(enabled: bool) -> None:
    from ..phone_generation import PHONE_CONFIG_FILE
    from ..phone_protocol import PHONE_CONFIG_OFFSET
    from ..rom import KirbyAmPatchExtension, KirbyAmProcedurePatch
    patch = KirbyAmProcedurePatch()
    expected = phone_patch_config(enabled)
    patch.write_file(PHONE_CONFIG_FILE, expected)
    rom = bytes(PHONE_CONFIG_OFFSET) + expected
    assert KirbyAmPatchExtension.validate_phone_seed_config(patch, rom) is rom
    for invalid in (rom[:-1], bytes(PHONE_CONFIG_OFFSET) + phone_patch_config(not enabled)):
        with pytest.raises(ValueError, match="differs from seed intent"):
            KirbyAmPatchExtension.validate_phone_seed_config(patch, invalid)


def test_final_guard_rejects_missing_intent_and_is_last() -> None:
    from ..rom import KirbyAmPatchExtension, KirbyAmProcedurePatch
    with pytest.raises(ValueError, match="missing Phone patch intent"):
        KirbyAmPatchExtension.validate_phone_seed_config(KirbyAmProcedurePatch(), b"")
    assert KirbyAmProcedurePatch.procedure[-1] == ("validate_phone_seed_config", [])


@pytest.mark.parametrize("enabled", [False, True])
@pytest.mark.parametrize("area_keys", [False, True])
def test_actual_pool_slot_and_tokens(enabled: bool, area_keys: bool) -> None:
    from test.general import setup_multiworld
    from worlds.Files import APPatchExtension
    from .. import KirbyAmWorld
    from ..phone_generation import PHONE_CONFIG_FILE
    from ..phone_protocol import PHONE_CONFIG_OFFSET, PHONE_ITEM_ID, validate_phone_pairing
    from ..rom import KirbyAmPatchExtension, KirbyAmProcedurePatch, write_tokens
    multiworld = setup_multiworld(KirbyAmWorld, seed=1086, options={
        "phone_progression": enabled, "ability_gating": False, "area_keys": area_keys,
    })
    world = multiworld.worlds[1]
    assert isinstance(world, KirbyAmWorld)
    phone_items = [item for item in multiworld.itempool if item.code == PHONE_ITEM_ID]
    assert len(phone_items) == int(enabled)
    assert all(item.advancement for item in phone_items)
    assert len(multiworld.itempool) == len(multiworld.get_unfilled_locations())
    slot = world.fill_slot_data()
    assert slot["phone_progression"] is enabled
    assert ("Phone a Friend" in slot["unique_items"]) is enabled
    if enabled:
        assert slot["phone_protocol_version"] == 1
        assert slot["starting_phone_access"] is False
    else:
        assert "phone_protocol_version" not in slot and "starting_phone_access" not in slot
    patch = KirbyAmProcedurePatch()
    write_tokens(world, patch)
    assert patch.get_file(PHONE_CONFIG_FILE) == phone_patch_config(enabled)
    from ..enemy_ability_runtime_patch import ENEMY_SOURCE_CONFIG_ROM_OFFSET
    raw = bytearray(ENEMY_SOURCE_CONFIG_ROM_OFFSET + 36)
    raw[PHONE_CONFIG_OFFSET:PHONE_CONFIG_OFFSET + 12] = PHONE_DISABLED_CONFIG
    KirbyAmPatchExtension.validate_production_phone_disabled(patch, bytes(raw))
    result = APPatchExtension.apply_tokens(patch, bytes(raw), "token_data.bin")
    assert KirbyAmPatchExtension.validate_phone_seed_config(patch, result) is result
    config = result[PHONE_CONFIG_OFFSET:PHONE_CONFIG_OFFSET + 12]
    assert config == phone_patch_config(enabled)
    assert validate_phone_pairing(slot, config) == int(enabled)
    with pytest.raises(ValueError):
        validate_phone_pairing(slot, phone_patch_config(not enabled))


@pytest.mark.parametrize("inventory", ["start_inventory"])
def test_disabled_phone_rejects_explicit_start(inventory: str) -> None:
    from test.general import setup_multiworld
    from .. import KirbyAmWorld
    with pytest.raises(ValueError, match="requires phone_progression"):
        setup_multiworld(KirbyAmWorld, options={inventory: {"Phone a Friend": 1}})


@pytest.mark.parametrize("inventory,count", [(None, 0), ("start_inventory", 1), ("start_inventory", 3)])
def test_full_generation_phone_progression(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, inventory: str | None, count: int) -> None:
    import Main
    from ..data import data
    from ..phone_protocol import PHONE_ITEM_ID
    from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive
    generated = []
    original = Main.main

    def capture(*args: Any, **kwargs: Any) -> Any:
        result = original(*args, **kwargs)
        generated.append(result)
        return result

    monkeypatch.setattr(Main, "main", capture)
    player = tmp_path / "phone.yaml"
    player.write_text(
        "name: Phone Progression\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n"
        "  phone_progression: true\n  ability_gating: false\n  ability_randomization_mode: 0\n"
        "  minimum_health: 6\n  maximum_health: 10\n  enemy_health_multiplier: 100\n"
        "  room_sanity: false\n  accessibility: full\n"
        + (f"  {inventory}:\n    Phone a Friend: {count}\n" if inventory else ""))
    archive = generate_archive_from_fixture(player, tmp_path / "out", seed=1086)
    decoded = load_multidata_from_archive(archive)
    import io
    import json
    from zipfile import ZipFile
    from ..phone_generation import PHONE_CONFIG_FILE
    with ZipFile(archive) as outer:
        patches = [name for name in outer.namelist() if name.endswith(".apkirbyam")]
        assert len(patches) == 1
        with ZipFile(io.BytesIO(outer.read(patches[0]))) as patch:
            assert patch.read(PHONE_CONFIG_FILE) == PHONE_ENABLED_CONFIG
            manifest = json.loads(patch.read("archipelago.json"))
            assert manifest["procedure"][1] == ["validate_production_phone_disabled", []]
            assert manifest["procedure"][-1] == ["validate_phone_seed_config", []]
    multiworld, = generated
    assert not multiworld.get_unfilled_locations()
    assert multiworld.can_beat_game() and multiworld.fulfills_accessibility()
    slot = decoded["slot_data"][1]
    assert slot["phone_protocol_version"] == 1
    assert slot["starting_phone_access"] is (inventory is not None)
    assert decoded["precollected_items"][1].count(PHONE_ITEM_ID) == count
    phones = [loc for loc in multiworld.get_filled_locations() if loc.item and loc.item.code == PHONE_ITEM_ID]
    assert len(phones) == 1
    # A normal shuffled Phone must be obtainable without owning Phone already.
    if inventory is None:
        state = multiworld.get_all_state()
        while state.has("Phone a Friend", 1):
            state.remove(phones[0].item)
        assert not state.has("Phone a Friend", 1)
        assert phones[0].can_reach(state)
    chalk = multiworld.get_location(data.locations["MINOR_CHEST_SPRAY_PAINT_14"].label, 1)
    assert chalk.parent_region.name.endswith("ROOM_2_GOAL_2_UPPER_LEFT")


@pytest.mark.parametrize("mutation", ["missing-policy", "source-policy", "health", "mode"])
def test_publication_rechecks_admitted_profile(mutation: str) -> None:
    from test.general import setup_multiworld
    from .. import KirbyAmWorld
    from ..rom import KirbyAmProcedurePatch, write_tokens
    multiworld = setup_multiworld(KirbyAmWorld, seed=1086, options={
        "phone_progression": 1, "ability_gating": 0,
    })
    world = multiworld.worlds[1]
    assert isinstance(world, KirbyAmWorld)
    if mutation == "missing-policy":
        del world._enemy_copy_ability_policy
    elif mutation == "source-policy":
        world._enemy_copy_ability_policy = {"mode": 1}
    elif mutation == "health":
        world.options.minimum_health.value = 1
    else:
        world.options.ability_randomization_mode.value = 1
    patch = KirbyAmProcedurePatch()
    with pytest.raises(ValueError, match="Phone progression"):
        write_tokens(world, patch)
    assert patch.files == {}  # Rejection precedes archive intent and token output.
    with pytest.raises(ValueError, match="Phone progression"):
        world.fill_slot_data()
