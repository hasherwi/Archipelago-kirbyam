"""ROM-free generation/token boundary checks for the unaccepted Phone gate.

The synthetic buffer models the shipping disabled Phone configuration only.
These checks invoke the production Phone validator around serialized tokens.
They do not apply the base BSDIFF, validate a real ROM, or prove native helper
routes in an emulator.
"""
from pathlib import Path
from typing import Any

import pytest

from test.general import setup_multiworld
from worlds.Files import APPatchExtension, APTokenTypes
from .. import KirbyAmWorld
from ..data import data
from ..enemy_ability_data import GATEABLE_ENEMY_COPY_ABILITIES
from ..traversal import CAPABILITY_ABILITIES
from ..traversal_data import compile_room_graph, graph_items, load_room_traversal
from ..enemy_ability_runtime_patch import ENEMY_SOURCE_CONFIG_ROM_OFFSET
from ..options import AbilityRandomizationMode
from ..phone_protocol import PHONE_CONFIG_OFFSET, PHONE_ITEM_ID, PHONE_MARKER, validate_phone_pairing
from ..rom import KirbyAmPatchExtension, KirbyAmProcedurePatch, write_tokens


DISABLED_PHONE_CONFIG = PHONE_MARKER + bytes(4)


@pytest.fixture(scope="module")
def synthetic_post_base() -> bytes:
    """Share immutable synthetic bytes, never a ROM or a BSDIFF reconstruction."""
    # The adjacent 36-byte enemy-source config is the last current token write.
    # Cover its full range so apply_tokens cannot append an out-of-range write.
    buffer = bytearray(ENEMY_SOURCE_CONFIG_ROM_OFFSET + 36)
    buffer[PHONE_CONFIG_OFFSET:PHONE_CONFIG_OFFSET + 12] = DISABLED_PHONE_CONFIG
    return bytes(buffer)


def _assert_phone_disabled(
        patch: KirbyAmProcedurePatch, slot_data: dict[str, Any], synthetic_post_base: bytes) -> None:
    KirbyAmPatchExtension.validate_production_phone_disabled(patch, synthetic_post_base)
    patched = APPatchExtension.apply_tokens(patch, synthetic_post_base, "token_data.bin")
    assert KirbyAmPatchExtension.validate_production_phone_disabled(patch, patched) is patched
    assert len(patched) == len(synthetic_post_base)
    config = patched[PHONE_CONFIG_OFFSET:PHONE_CONFIG_OFFSET + 12]
    # Pairing alone accepts absent markers for legacy ROMs, so require exact
    # bytes as well: destroying the marker must not hide an accidental write.
    assert config == DISABLED_PHONE_CONFIG, "seed tokens changed disabled Phone configuration"
    assert validate_phone_pairing(slot_data, config) == 0


@pytest.mark.parametrize("ability_gating", [0, 1])
@pytest.mark.parametrize("area_keys", [0, 1])
@pytest.mark.parametrize("room_sanity", [0, 1])
@pytest.mark.parametrize("ability_randomization_mode", [
    AbilityRandomizationMode.option_off,
    AbilityRandomizationMode.option_shuffled,
    AbilityRandomizationMode.option_completely_random,
], ids=["off", "shuffled", "completely_random"])
@pytest.mark.parametrize("ability_randomization_statues", [0, 1])
def test_production_generation_does_not_enable_phone_without_route_acceptance(
        ability_gating: int, area_keys: int, room_sanity: int,
        ability_randomization_mode: int, ability_randomization_statues: int,
        synthetic_post_base: bytes) -> None:
    multiworld = setup_multiworld(KirbyAmWorld, seed=1086, options={
        "ability_gating": ability_gating, "area_keys": area_keys, "room_sanity": room_sanity,
        "ability_randomization_mode": ability_randomization_mode,
        "ability_randomization_statues": ability_randomization_statues,
    })
    world = multiworld.worlds[1]
    assert isinstance(world, KirbyAmWorld)
    slot_data = world.fill_slot_data()
    # Main's source-aware starts and the inactive Phone boundary must coexist.
    assert [item.name for item in multiworld.precollected_items[1]
            if item.name.endswith(" Ability")] == ["Beam Ability"]
    assert tuple(slot_data["ability_gateable_abilities"]) == (
        GATEABLE_ENEMY_COPY_ABILITIES if ability_gating else ())
    assert "Phone a Friend" not in world.item_name_to_id
    assert "starting_phone_access" not in slot_data
    assert not any("phone" in name.lower() for name in KirbyAmWorld.options_dataclass.type_hints)
    assert "Phone a Friend" not in slot_data.get("unique_items", ())
    assert all(item.code != PHONE_ITEM_ID for item in multiworld.precollected_items[1])
    assert PHONE_ITEM_ID not in data.items
    assert all(item.code != PHONE_ITEM_ID for item in multiworld.itempool)
    assert "phone_protocol_version" not in slot_data
    assert len(multiworld.itempool) == len(multiworld.get_unfilled_locations())

    patch = KirbyAmProcedurePatch()
    write_tokens(world, patch)  # Includes the production token binary serialization.
    _assert_phone_disabled(patch, slot_data, synthetic_post_base)

    source = Path(__file__).resolve().parents[1] / "kirby_ap_payload" / "phone.c"
    assert 'gApPhoneConfig = {"APPHN01", 0u}' in source.read_text()


@pytest.mark.parametrize("relative_offset,payload", [
    (8, b"\1\0\0\0"),
    (0, b"X"),
], ids=["enable", "corrupt-marker"])
def test_phone_guard_rejects_enabling_or_corrupting_tokens(
        relative_offset: int, payload: bytes, synthetic_post_base: bytes) -> None:
    """Negative controls mutate serialized tokens, never production code or a ROM."""
    multiworld = setup_multiworld(KirbyAmWorld, seed=1086)
    world = multiworld.worlds[1]
    assert isinstance(world, KirbyAmWorld)
    patch = KirbyAmProcedurePatch()
    write_tokens(world, patch)
    patch.write_token(APTokenTypes.WRITE, PHONE_CONFIG_OFFSET + relative_offset, payload)
    patch.write_file("token_data.bin", patch.get_token_binary())

    with pytest.raises(ValueError, match="production Phone must remain disabled"):
        _assert_phone_disabled(patch, world.fill_slot_data(), synthetic_post_base)


def test_production_traversal_has_no_phone_helper_provider_or_requirement() -> None:
    """Keep helper observations out of active source-aware progression logic."""
    assert not any("phone" in capability.lower() or "helper" in capability.lower()
                   for capability in CAPABILITY_ABILITIES)
    assert all("Phone a Friend" not in abilities for abilities in CAPABILITY_ABILITIES.values())
    targets, sources, parts = load_room_traversal({
        name: {"traversal": region.traversal} for name, region in data.regions.items()
    })
    assert targets  # Exercise the real merged catalog, not an empty stand-in.
    for target in targets:
        assert target["kind"] != "phone"
        for definition in target["graphs"].values():
            graph = compile_room_graph(definition, sources, area_keys=True, graph_parts=parts)
            assert "Phone a Friend" not in graph_items(graph), target["id"]
