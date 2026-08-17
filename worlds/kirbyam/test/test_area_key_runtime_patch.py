"""Focused runtime and ROM-patch contract tests for Area Keys (Issue #42)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


WORLD_DIR = Path(__file__).resolve().parents[1]
PATCH_ROM_PATH = WORLD_DIR / "kirby_ap_payload" / "patch_rom.py"
PATCH_ROM_SPEC = importlib.util.spec_from_file_location("kirbyam_area_key_patch_rom", PATCH_ROM_PATH)
if PATCH_ROM_SPEC is None or PATCH_ROM_SPEC.loader is None:
    raise RuntimeError(f"Failed to load patch_rom module from {PATCH_ROM_PATH}")
patch_rom = importlib.util.module_from_spec(PATCH_ROM_SPEC)
PATCH_ROM_SPEC.loader.exec_module(patch_rom)


def test_area_key_runtime_address_follows_existing_mailbox_words() -> None:
    addresses = json.loads((WORLD_DIR / "data" / "addresses.json").read_text(encoding="utf-8"))
    transport = addresses["ram"]["transport"]

    assert transport["starting_kirby_color_applied"] == "0x0203B0B8"
    assert transport["lever_activation_flags"] == "0x0203B0BC"
    assert transport["area_key_bitfield_runtime"] == "0x0203B0C0"


def test_payload_uses_native_destination_area_and_new_item_range() -> None:
    payload = (WORLD_DIR / "kirby_ap_payload" / "ap_payload.c").read_text(encoding="utf-8")

    assert "#define AP_AREA_KEY_BITFIELD_RUNTIME (*(volatile uint32_t*)(AP_BASE + 0xC0u))" in payload
    assert "#define KIRBY_ROOM_AREA_INFO_TABLE_ADDR 0x08D6CD0Cu" in payload
    assert "source_area != KIRBY_NATIVE_AREA_UNKNOWN" in payload
    assert "destination_area >= 1u" in payload
    assert "destination_area <= 8u" in payload
    assert "AP_AREA_KEY_BITFIELD_RUNTIME >> (destination_area + 1u)" in payload
    assert "KIRBY_ITEM_ID_BASE_OFFSET + 41u" in payload
    assert "KIRBY_ITEM_ID_BASE_OFFSET + 48u" in payload


def test_payload_has_separate_visual_and_pre_mutation_functional_guards() -> None:
    payload = (WORLD_DIR / "kirby_ap_payload" / "ap_payload.c").read_text(encoding="utf-8")

    assert "uint32_t ap_transition_allowed(uint16_t source_room, uint16_t destination_room)" in payload
    assert "uint32_t ap_prepare_automatic_transition(void *kirby, uint32_t collision_flags)" in payload
    assert "uint8_t ap_on_button_special_transition(void *kirby)" in payload
    assert "static uint8_t ap_button_transition_is_locked(void *kirby)" in payload
    assert "#define KIRBY_STRUCT_CONTACT_OBJECT_OFFSET 0x6Cu" in payload
    assert "#define KIRBY_OBJECT_DESTINATION_ROOM_OFFSET 0x63u" in payload
    assert "uint8_t ap_on_explicit_room_transition(" in payload
    assert "uint32_t ap_on_query_special_door_state(" in payload
    assert "return ap_transition_allowed(room_id, destination_room);" in payload
    assert "return KIRBY_SPECIAL_DOOR_VISITED_FN(room_id, destination_room, spawn_x, spawn_y);" in payload
    assert "ap_is_warp_room_doors_idx" not in payload


def test_rooms_json_native_area_contract_is_complete_and_collision_free() -> None:
    expected = patch_rom.load_expected_native_area_by_doors_idx()

    assert len(expected) == 263
    assert expected[0] == 0
    assert expected[80] == 1
    assert expected[189] == 2
    assert expected[169] == 8


def test_native_area_contract_fails_on_runtime_mapping_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(patch_rom, "ROOM_AREA_INFO_TABLE_OFFSET", 0x00)
    monkeypatch.setattr(patch_rom, "ROOM_PROPS_TABLE_OFFSET", 0x20)
    monkeypatch.setattr(patch_rom, "ROOM_PROPS_STRIDE", 0x08)
    monkeypatch.setattr(patch_rom, "ROOM_PROPS_DOORS_IDX_OFFSET", 0x04)
    monkeypatch.setattr(patch_rom, "ROOM_AREA_INFO_AREA_OFFSET", 0x02)
    monkeypatch.setattr(patch_rom, "ROOM_AREA_INFO_COUNT", 1)
    monkeypatch.setattr(
        patch_rom,
        "load_expected_native_area_by_doors_idx",
        lambda: {7: 1},
    )

    rom = bytearray(0x80)
    rom[0:4] = (0x08000040).to_bytes(4, "little")
    rom[0x42] = 2
    rom[0x24:0x26] = (7).to_bytes(2, "little")

    with pytest.raises(SystemExit, match="native/AP room mapping drift"):
        patch_rom.validate_area_key_native_area_contract(rom)


def test_automatic_transition_guard_preserves_window_and_control_flow() -> None:
    hook_target = 0x0815E400
    guard = patch_rom.build_automatic_transition_guard_bytes(hook_target)

    assert len(guard) == 16
    assert guard[:4] == bytes.fromhex("28 46 31 46")
    assert patch_rom.decode_thumb_bl_target(0x0803FE14, guard[4:8]) == hook_target
    assert guard[8:] == bytes.fromhex("00 28 1E D0 C0 46 C0 46")


def test_automatic_transition_guard_rejects_retail_byte_drift() -> None:
    offset = patch_rom.AUTOMATIC_TRANSITION_GUARD_OFFSET
    rom = bytearray(offset + len(patch_rom.AUTOMATIC_TRANSITION_GUARD_ORIGINAL))
    rom[offset:offset + len(patch_rom.AUTOMATIC_TRANSITION_GUARD_ORIGINAL)] = (
        patch_rom.AUTOMATIC_TRANSITION_GUARD_ORIGINAL
    )
    patch_rom.validate_exact_rom_bytes(
        rom,
        offset,
        patch_rom.AUTOMATIC_TRANSITION_GUARD_ORIGINAL,
        "Area Key automatic-transition guard",
    )

    rom[offset] ^= 0x01
    with pytest.raises(SystemExit, match="does not match the verified retail bytes"):
        patch_rom.validate_exact_rom_bytes(
            rom,
            offset,
            patch_rom.AUTOMATIC_TRANSITION_GUARD_ORIGINAL,
            "Area Key automatic-transition guard",
        )


def _synthetic_area_key_callsite_rom(*, omit_one_button_call: bool = False) -> bytearray:
    rom_base = 0x08000000
    counts_and_targets = (
        (
            patch_rom.EXPECTED_SPECIAL_DOOR_STATE_CALLSITES,
            patch_rom.ORIGINAL_SPECIAL_DOOR_STATE_FN_ADDR,
        ),
        (
            patch_rom.EXPECTED_BUTTON_SPECIAL_TRANSITION_CALLSITES - int(omit_one_button_call),
            patch_rom.ORIGINAL_BUTTON_SPECIAL_TRANSITION_FN_ADDR,
        ),
        (
            patch_rom.EXPECTED_EXPLICIT_ROOM_TRANSITION_CALLSITES,
            patch_rom.ORIGINAL_EXPLICIT_ROOM_TRANSITION_FN_ADDR,
        ),
    )
    offset = 0xC0
    rom = bytearray(0x400)
    for count, target in counts_and_targets:
        for _ in range(count):
            rom[offset:offset + 4] = patch_rom.thumb_bl_bytes(rom_base + offset, target)
            offset += 4
        offset += 4
    return rom


def test_area_key_callsite_discovery_requires_all_three_exact_call_families() -> None:
    visual, button, explicit = patch_rom.discover_area_key_callsites(
        _synthetic_area_key_callsite_rom(),
        0x08000000,
    )

    assert len(visual) == 5
    assert len(button) == 28
    assert len(explicit) == 8


def test_area_key_callsite_discovery_fails_when_one_button_hook_is_missing() -> None:
    with pytest.raises(SystemExit, match="expected exactly 28 button special-transition callsites"):
        patch_rom.discover_area_key_callsites(
            _synthetic_area_key_callsite_rom(omit_one_button_call=True),
            0x08000000,
        )


def test_protocol_documents_area_key_runtime_allocation_and_item_ids() -> None:
    protocol = (WORLD_DIR / "PROTOCOL.md").read_text(encoding="utf-8")

    assert "0x0203B0C0" in protocol
    assert "bits `2..9`" in protocol
    assert "3860041 - 3860048" in protocol
    assert "variants `0xA`/`9` for boarded area doors" in protocol
    assert "`3`/`2` for regular mirrors" in protocol
