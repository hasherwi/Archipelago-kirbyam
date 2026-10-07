from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "enumerate_minor_chests.py"
_spec = importlib.util.spec_from_file_location("enumerate_minor_chests", MODULE_PATH)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"Unable to load module spec from {MODULE_PATH}")
_enumerate_minor_chests = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_enumerate_minor_chests)


def test_resolve_amr_entry_rom_offset_prefers_direct_match() -> None:
    payload = bytes.fromhex("80ff02000006")
    raw_addr = 0x200
    fragment_addr = raw_addr + _enumerate_minor_chests.AMR_OBJECT_TEMPLATE_FRAGMENT_OFFSET
    rom = bytearray(0x1000)
    rom[fragment_addr:fragment_addr + len(payload)] = payload

    resolved, mode = _enumerate_minor_chests.resolve_amr_entry_rom_offset(raw_addr, bytes(rom), payload)

    assert resolved == raw_addr
    assert mode == "direct"


def test_resolve_amr_entry_rom_offset_uses_jp_to_us_shift() -> None:
    payload = bytes.fromhex("80ff02000006")
    raw_addr = 0x300
    shifted_addr = raw_addr + _enumerate_minor_chests.AMR_JP_TO_US_ROM_SHIFT
    fragment_addr = shifted_addr + _enumerate_minor_chests.AMR_OBJECT_TEMPLATE_FRAGMENT_OFFSET
    rom = bytearray(fragment_addr + len(payload) + 0x20)
    rom[fragment_addr:fragment_addr + len(payload)] = payload

    resolved, mode = _enumerate_minor_chests.resolve_amr_entry_rom_offset(raw_addr, bytes(rom), payload)

    assert resolved == shifted_addr
    assert mode == "jp_to_us_shift"


def test_resolve_amr_entry_rom_offset_returns_template_base_not_fragment() -> None:
    payload = bytes.fromhex("80ff02000006")
    template_base = 0x400
    fragment = template_base + _enumerate_minor_chests.AMR_OBJECT_TEMPLATE_FRAGMENT_OFFSET
    rom = bytearray(0x1000)
    rom[template_base:template_base + len(payload)] = payload

    with pytest.raises(ValueError, match="Unable to resolve AMR SmallChest address"):
        _enumerate_minor_chests.resolve_amr_entry_rom_offset(template_base, bytes(rom), payload)

    rom[template_base:template_base + len(payload)] = bytes(len(payload))
    rom[fragment:fragment + len(payload)] = payload
    resolved, _ = _enumerate_minor_chests.resolve_amr_entry_rom_offset(template_base, bytes(rom), payload)

    assert resolved == template_base


def test_parse_groomprops_uses_room_object_list_index_at_plus_20() -> None:
    room_entry = 7
    room_base = _enumerate_minor_chests.ROOM_PROPS_ROM_BASE + (
        room_entry * _enumerate_minor_chests.ROOM_PROPS_STRIDE
    )
    rom = bytearray(_enumerate_minor_chests.ROOM_PROPS_ROM_BASE + _enumerate_minor_chests.ROOM_PROPS_SIZE)
    rom[room_base + 0x20:room_base + 0x22] = (0x1234).to_bytes(2, "little")
    rom[room_base + 0x22:room_base + 0x24] = (0x5678).to_bytes(2, "little")
    rom[room_base + 0x24:room_base + 0x26] = (0x9ABC).to_bytes(2, "little")

    room = _enumerate_minor_chests.parse_groomprops(bytes(rom))[room_entry]

    assert room["object_list_idx"] == 0x1234
    assert room["doors_idx"] == 0x9ABC
    assert "object_list2_idx" not in room


def test_decode_amr_small_chest_fragment_uses_reward_byte_two_and_flag_byte_five() -> None:
    # Auxiliary bytes are intentionally nonzero: they can encode 1-Up variants.
    fields = _enumerate_minor_chests.decode_amr_small_chest_fragment(bytes.fromhex("80ff02000152"))

    assert fields["reward_id"] == 2
    assert fields["native_treasure_id"] == 0
    assert fields["entry_aux_hi"] == 1
    assert fields["native_chest_flag_index"] == 0x52


def test_decode_amr_small_chest_fragment_rejects_wrong_width() -> None:
    with pytest.raises(ValueError, match="Expected 6-byte AMR fragment"):
        _enumerate_minor_chests.decode_amr_small_chest_fragment(b"short")


@pytest.mark.parametrize("reward_id", range(6))
def test_reward_ids_zero_through_five_are_consumable_pool_entries(reward_id: int) -> None:
    reward_path, can_yield_1up, possible_rewards = _enumerate_minor_chests.classify_reward_profile(
        "unknown",
        reward_id,
    )

    assert reward_path == "non_collection_consumable_pool"
    assert can_yield_1up is True
    assert "1-Up" in possible_rewards


def test_consumable_reward_id_takes_precedence_over_collection_table_guess() -> None:
    reward_path, can_yield_1up, possible_rewards = _enumerate_minor_chests.classify_reward_profile(
        "music_sheet",
        0,
    )

    assert reward_path == "non_collection_consumable_pool"
    assert can_yield_1up is True
    assert "1-Up" in possible_rewards


def test_collection_reward_is_classified_after_consumable_reward_ids() -> None:
    reward_path, can_yield_1up, possible_rewards = _enumerate_minor_chests.classify_reward_profile(
        "music_sheet",
        6,
    )

    assert reward_path == "collection_reward"
    assert can_yield_1up is False
    assert possible_rewards == []


def test_item_field_semantics_collection_reward_is_not_object_name_lookup() -> None:
    name, is_direct = _enumerate_minor_chests.item_field_semantics(
        0x0D,
        "collection_reward",
        {0x0D: "Blockin"},
    )

    assert is_direct is False
    assert name.startswith("ROM-byte=0x0D")
    assert "Blockin" not in name


def test_item_field_semantics_collection_reward_takes_precedence_for_zero_item_id() -> None:
    name, is_direct = _enumerate_minor_chests.item_field_semantics(
        0x00,
        "collection_reward",
        {0x00: "Waddle Dee"},
    )

    assert is_direct is False
    assert name.startswith("ROM-byte=0x00")
    assert "sentinel/no direct chest grant" not in name

