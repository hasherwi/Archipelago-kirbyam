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
    assert transport["transition_event_counter_runtime"] == "0x0203B0C4"
    assert transport["transition_event_ring_runtime"] == "0x0203B0C8"
    assert transport["transition_event_telemetry_cookie_runtime"] == "0x0203B130"


def test_warp_star_guard_denies_before_native_boarding_mutates_state() -> None:
    payload = (WORLD_DIR / "kirby_ap_payload" / "ap_payload.c").read_text(encoding="utf-8")
    guard_start = payload.index("uint32_t ap_on_warp_star_transition(")
    guard_end = payload.index("__attribute__((used)) uint32_t ap_on_query_special_door_state", guard_start)
    guard = payload[guard_start:guard_end]

    predicate = guard.index("ap_transition_allowed(source_room, destination_room)")
    denial = guard.index("return 0u;", predicate)
    native_boarding = guard.index("KIRBY_WARP_STAR_TRANSITION_FN(warp_star, human_only)", denial)
    assert predicate < denial < native_boarding
    assert "KIRBY_WARP_STAR_TRANSITION_FN(warp_star, human_only);" in guard
    assert "kirby->roomId" not in guard
    assert "KIRBY_WARP_STAR_DESTINATION_ROOM_OFFSET" in guard
    assert "AP_AREA_KEY_BITFIELD_RUNTIME >> (destination_area + 1u)" in payload


def test_warp_star_destination_gate_semantics() -> None:
    # This source-level contract model covers the destination-key semantics; it is not emulator proof.
    payload = (WORLD_DIR / "kirby_ap_payload" / "ap_payload.c").read_text(encoding="utf-8")
    assert "source_area != destination_area" in payload
    assert "destination_area >= 1u" in payload
    assert "destination_area <= 8u" in payload
    assert "AP_AREA_KEY_BITFIELD_RUNTIME >> (destination_area + 1u)" in payload

    def transition_allowed(source_area: int, destination_area: int, key_mask: int) -> bool:
        if source_area == 0xFF or source_area == destination_area:
            return True
        if not 1 <= destination_area <= 8:
            return True
        return bool(key_mask & (1 << (destination_area + 1)))

    assert not transition_allowed(1, 2, 0)  # first Area 1 -> Area 2 star, no keys
    assert not transition_allowed(1, 2, 1 << 2)  # Area 1 key does not satisfy Area 2
    assert transition_allowed(1, 2, 1 << 3)  # Area 2 key permits boarding
    assert transition_allowed(2, 2, 0)  # same-area travel retains retail behavior
    assert transition_allowed(2, 0, 0)  # return to Rainbow Route remains open


def test_warp_star_guard_preserves_cpu_passenger_call_contract() -> None:
    payload = (WORLD_DIR / "kirby_ap_payload" / "ap_payload.c").read_text(encoding="utf-8")
    guard_start = payload.index("uint32_t ap_on_warp_star_transition(")
    guard_end = payload.index("__attribute__((used)) uint32_t ap_on_query_special_door_state", guard_start)
    guard = payload[guard_start:guard_end]

    assert "uint32_t human_only" in guard
    assert guard.count("KIRBY_WARP_STAR_TRANSITION_FN(warp_star, human_only)") == 3
    assert "warp_star_addr + KIRBY_WARP_STAR_KIRBY_PTR_OFFSET" in guard


def test_cannon_guard_denies_before_native_boarding_eligibility_call() -> None:
    payload = (WORLD_DIR / "kirby_ap_payload" / "ap_payload.c").read_text(encoding="utf-8")
    guard_start = payload.index("uint8_t ap_on_cannon_board_transition(void *kirby)")
    guard_end = payload.index("/*\n * Warp stars bypass", guard_start)
    guard = payload[guard_start:guard_end]

    check = guard.index("ap_transition_allowed(source_room, destination_room)")
    denial = guard.index("if (allowed == 0u) return 0u;", check)
    native = guard.index("return KIRBY_CANNON_BOARD_FN(kirby);", denial)
    assert check < denial < native
    assert "*(volatile uint16_t*)(cannon_addr + 0xBAu)" in guard


def test_unknown83_transport_guard_checks_before_pending_room_and_spawn_writes() -> None:
    payload = (WORLD_DIR / "kirby_ap_payload" / "ap_payload.c").read_text(encoding="utf-8")
    start = payload.index("void ap_on_unknown83_transport_update(void *object2)")
    end = payload.index("/* Mirror Shards use", start)
    guard = payload[start:end]

    decision = guard.index("ap_transition_allowed(source_room, destination_room)")
    allowed = guard.index("if (allowed != 0u)", decision)
    pending_room = guard.index("*(volatile uint16_t*)(kirby_addr + 0x106u) = destination_room", allowed)
    spawn = guard.index("*(volatile int16_t*)(kirby_addr + 0x108u)", allowed)
    assert decision < allowed < pending_room < spawn
    assert "ap_log_transition_attempt(" not in guard
    assert "#define KIRBY_NUM_KIRBYS_ADDR    0x0203AD44u" in payload


def test_button_transition_telemetry_matches_native_human_up_condition() -> None:
    payload = (WORLD_DIR / "kirby_ap_payload" / "ap_payload.c").read_text(encoding="utf-8")
    start = payload.index("uint8_t ap_on_button_special_transition(void *kirby)")
    end = payload.index("uint8_t ap_on_explicit_room_transition(", start)
    guard = payload[start:end]

    native_passthrough = guard.index("return KIRBY_BUTTON_TRANSITION_FN(kirby);")
    attempt_predicate = guard.index("player_id >= human_player_count || (movement_state & 0x40u) == 0u")
    destination = guard.index("ap_button_transition_destination(kirby, &destination_room)")
    telemetry = guard.index("ap_log_transition_attempt(source_room, destination_room, 5u, allowed")
    denial = guard.index("if (allowed == 0u)", telemetry)
    native_allowed = guard.index("return KIRBY_BUTTON_TRANSITION_FN(kirby);", native_passthrough + 1)
    assert attempt_predicate < native_passthrough < destination < telemetry < denial < native_allowed
    assert "#define KIRBY_NUM_HUMAN_PLAYERS_ADDR 0x0203AD30u" in payload
    assert "#define KIRBY_STRUCT_MOVEMENT_STATE_OFFSET 0x118u" in payload

    def native_attempt(player_id: int, human_count: int, movement_state: int) -> bool:
        return player_id < human_count and bool(movement_state & 0x40)

    assert not native_attempt(0, 1, 0)  # standing at the door without Up
    assert not native_attempt(1, 1, 0x40)  # AI Kirby cannot initiate the transition
    assert native_attempt(0, 1, 0x40)  # human holding Up is a real attempt


def test_explicit_transition_telemetry_requires_matching_player_tile_and_spawn() -> None:
    payload = (WORLD_DIR / "kirby_ap_payload" / "ap_payload.c").read_text(encoding="utf-8")
    start = payload.index("uint8_t ap_on_explicit_room_transition(")
    end = payload.index("/* sub_080510EC", start)
    guard = payload[start:end]

    helper = payload[payload.index("static uint8_t ap_current_special_tile_destination("):start]
    assert "out_spawn_x" in helper and "out_spawn_y" in helper
    attempt = guard.index("KIRBY_NUM_HUMAN_PLAYERS_ADDR")
    up = guard.index("KIRBY_STRUCT_MOVEMENT_STATE_OFFSET")
    source_tile = guard.index("ap_current_special_tile_destination(")
    destination_match = guard.index("tile_destination_room == destination_room")
    spawn_x_match = guard.index("tile_spawn_x == spawn_x")
    spawn_y_match = guard.index("tile_spawn_y == spawn_y")
    telemetry = guard.index("ap_log_transition_attempt(source_room, destination_room, 0u, allowed")
    denied = guard.index("if (allowed == 0u)", telemetry)
    assert attempt < up < source_tile < destination_match < spawn_x_match < spawn_y_match < telemetry < denied
    assert "return KIRBY_EXPLICIT_TRANSITION_FN(kirby, destination_room, spawn_x, spawn_y);" in guard

    def should_report(is_human: bool, holding_up: bool, destination_matches: bool,
                      spawn_matches: bool) -> bool:
        return is_human and holding_up and destination_matches and spawn_matches

    assert not should_report(False, True, True, True)  # follower/AI helper call
    assert not should_report(True, False, True, True)  # idle player
    assert not should_report(True, True, False, True)  # unrelated scripted target
    assert not should_report(True, True, True, False)  # wrong spawn point
    assert should_report(True, True, True, True)  # real denied attempt still logs


def test_synthetic_rom_fixture_supplies_complete_patch_smoke_contract() -> None:
    fixture_path = Path(__file__).resolve().parents[3] / ".github" / "scripts" / "create_kirbyam_dummy_rom.py"
    fixture_spec = importlib.util.spec_from_file_location("kirbyam_dummy_rom_fixture", fixture_path)
    if fixture_spec is None or fixture_spec.loader is None:
        raise RuntimeError(f"Failed to load ROM fixture generator from {fixture_path}")
    fixture = importlib.util.module_from_spec(fixture_spec)
    fixture_spec.loader.exec_module(fixture)

    rom = fixture.build_dummy_rom()
    assert len(rom) == 0x1000000
    offset = patch_rom.AUTOMATIC_TRANSITION_GUARD_OFFSET
    assert rom[offset:offset + len(patch_rom.AUTOMATIC_TRANSITION_GUARD_ORIGINAL)] == (
        patch_rom.AUTOMATIC_TRANSITION_GUARD_ORIGINAL
    )
    unknown83_offset = patch_rom.UNKNOWN83_CALLBACK_POINTER_OFFSET
    assert rom[unknown83_offset:unknown83_offset + 4] == patch_rom.UNKNOWN83_CALLBACK_POINTER_ORIGINAL
    patch_rom.validate_area_key_native_area_contract(rom)
    visual, button, explicit, warp_star = patch_rom.discover_area_key_callsites(rom, 0x08000000)
    cannon_board = patch_rom.discover_cannon_board_callsites(rom, 0x08000000)
    assert len(visual) == 5
    assert len(button) == 28
    assert len(explicit) == 8
    assert len(warp_star) == 3
    mirror_shard = patch_rom.discover_mirror_shard_callback_pointers(rom)
    assert mirror_shard == [0x0001C6BC]
    assert cannon_board == [0x00121C46, 0x00121C9E, 0x00121CF6, 0x00121D54]


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
    assert "static uint8_t ap_button_transition_destination(void *kirby, uint16_t *out_destination_room)" in payload
    assert "#define KIRBY_STRUCT_CONTACT_OBJECT_OFFSET 0x6Cu" in payload
    assert "#define KIRBY_OBJECT_DESTINATION_ROOM_OFFSET 0x63u" in payload
    assert "uint8_t ap_on_explicit_room_transition(" in payload
    assert "uint32_t ap_on_warp_star_transition(void *warp_star, uint32_t human_only)" in payload
    assert "uint8_t ap_on_cannon_board_transition(void *kirby)" in payload
    assert "void ap_on_unknown83_transport_update(void *object2)" in payload
    assert "void ap_on_mirror_shard_update(void *shard)" in payload
    assert "uint32_t ap_on_query_special_door_state(" in payload
    assert "return ap_transition_allowed(room_id, destination_room);" in payload
    assert "return KIRBY_SPECIAL_DOOR_VISITED_FN(room_id, destination_room, spawn_x, spawn_y);" in payload
    assert "ap_is_warp_room_doors_idx" not in payload


def test_mirror_shard_denial_precedes_native_state_transition() -> None:
    payload = (WORLD_DIR / "kirby_ap_payload" / "ap_payload.c").read_text(encoding="utf-8")
    start = payload.index("void ap_on_mirror_shard_update(void *shard)")
    end = payload.index("/*\n * Warp stars bypass", start)
    guard = payload[start:end]

    check = guard.index("ap_transition_allowed(source_room, destination_room)")
    denial = guard.index("if (allowed == 0u) return;", check)
    native = guard.index("KIRBY_MIRROR_SHARD_UPDATE_FN(shard);", denial)
    assert check < denial < native


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
        (
            patch_rom.EXPECTED_WARP_STAR_TRANSITION_CALLSITES,
            patch_rom.ORIGINAL_WARP_STAR_TRANSITION_FN_ADDR,
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


def test_area_key_callsite_discovery_requires_all_four_exact_call_families() -> None:
    visual, button, explicit, warp_star = patch_rom.discover_area_key_callsites(
        _synthetic_area_key_callsite_rom(),
        0x08000000,
    )

    assert len(visual) == 5
    assert len(button) == 28
    assert len(explicit) == 8
    assert len(warp_star) == 3


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
