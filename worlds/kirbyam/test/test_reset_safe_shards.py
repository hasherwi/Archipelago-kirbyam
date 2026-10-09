"""Shard grant and boss-transition contracts; SRAM integrity has executable tests."""

import re
import sys
import os

# Prevent stdlib types module shadowing
_SCRIPT_DIR = os.path.realpath(os.path.dirname(__file__))
_WORLD_DIR = os.path.realpath(os.path.dirname(_SCRIPT_DIR))
for path_entry in list(sys.path):
    resolved = os.path.realpath(path_entry or os.getcwd())
    if resolved == _WORLD_DIR:
        sys.path.remove(path_entry)

import pytest  # noqa: E402






def test_payload_tracks_major_chest_checks_separately_from_native_maps() -> None:
    """Verify big chest openings feed transport checks while AP map items unlock native maps."""
    payload_path = os.path.join(_WORLD_DIR, "kirby_ap_payload", "ap_payload.c")

    with open(payload_path, 'r') as f:
        content = f.read()

    assert "AP_MAJOR_CHEST_FLAGS" in content, "Major chest transport register should be defined"
    assert "ap_on_collect_big_chest" in content, "Big chest hook target should exist"
    assert "ap_set_major_chest_flag(area_id)" in content, "Big chest hook should set transport check flags"
    assert "if (area_id == 0u)" in content, (
        "Big chest hook should preserve native world-map unlock for tutorial chest"
    )
    assert "ap_unlock_area_map" in content, "Payload should unlock native maps on AP item receipt"
    assert "KIRBY_BIG_CHEST_FLAGS" in content, "Native big chest map bitfield should still be addressable"


def test_payload_tracks_vitality_chest_checks_and_ap_vitality_apply() -> None:
    """Verify vitality chest checks and AP vitality grants use dedicated payload paths."""
    payload_path = os.path.join(_WORLD_DIR, "kirby_ap_payload", "ap_payload.c")

    with open(payload_path, 'r') as f:
        content = f.read()

    assert "AP_VITALITY_CHEST_FLAGS" in content, "Vitality chest transport register should be defined"
    assert "ap_on_collect_vitality_chest" in content, "Vitality chest hook target should exist"
    assert "ap_set_vitality_chest_flag_for_room" in content, "Vitality chest room mapping helper should exist"
    assert "ap_grant_vitality_counter" in content, "AP vitality grant helper should exist"
    assert "KIRBY_ITEM_ID_BASE_OFFSET + 18u" in content, "Vitality AP item IDs should be handled"


def test_payload_tracks_exact_minor_chest_events() -> None:
    """Verify small chest collection records exact source pointers before native persistence."""
    payload_path = os.path.join(_WORLD_DIR, "kirby_ap_payload", "ap_payload.c")

    with open(payload_path, 'r') as f:
        content = f.read()

    assert "AP_MINOR_CHEST_EVENT_COUNTER" in content, "Minor chest event counter should be defined"
    assert "AP_MINOR_CHEST_EVENT_RING_BASE" in content, "Minor chest event ring base should be defined"
    assert "ap_on_collect_small_chest" in content, "Minor chest hook target should exist"
    assert "ap_record_minor_chest_source_ptr(source_ptr);" in content, (
        "Minor chest hook should record the exact source pointer before sending checks"
    )
    assert "ap_collect_small_chest_native(chest_index);" in content, (
        "Minor chest hook must preserve the native small-chest persistence write"
    )


def test_payload_suppresses_native_rewards_for_exact_ap_minor_chests() -> None:
    """The suppression table must match the active source-backed checks exactly."""
    import json

    payload_path = os.path.join(_WORLD_DIR, "kirby_ap_payload", "ap_payload.c")
    locations_path = os.path.join(_WORLD_DIR, "data", "locations.json")
    with open(payload_path, "r", encoding="utf-8") as f:
        payload = f.read()
    with open(locations_path, "r", encoding="utf-8") as f:
        locations = json.load(f)

    table_match = re.search(
        r"AP_OWNED_MINOR_CHEST_SOURCE_PTRS\[\]\s*=\s*\{([^}]+)\}",
        payload,
        re.DOTALL,
    )
    assert table_match is not None, "Payload must define AP-owned minor chest sources"
    payload_sources = {
        int(address, 16)
        for address in re.findall(r"0x([0-9A-Fa-f]+)u", table_match.group(1))
    }
    expected_sources = {
        0x08000000 + int(location["source_rom_offset"], 16)
        for location in locations.values()
        if location.get("category") == "MINOR_CHEST" and location.get("source_rom_offset")
    }

    assert len(expected_sources) == 65
    assert payload_sources == expected_sources
    assert "AP_MINOR_CHEST_ITEM_SUPPRESSION_MARKER" in payload
    assert "ap_on_minor_chest_reward_popup" in payload
    assert "chest_obj_ptr + 0xE0u) = KIRBY_MINOR_CHEST_NO_NATIVE_ITEM" in payload


def test_payload_preserves_full_native_small_chest_flag_range() -> None:
    """Chest flag 82 is valid in the native 128-bit small-chest array."""
    payload_path = os.path.join(_WORLD_DIR, "kirby_ap_payload", "ap_payload.c")
    with open(payload_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "if (chest_index >= 128u)" in content
    assert "if (chest_index >= 80u)" not in content

def test_payload_vitality_items_are_replay_guarded_per_unique_item() -> None:
    """Vitality AP item IDs should be idempotent so reconnect/reset replay does not grant duplicates."""
    payload_path = os.path.join(_WORLD_DIR, "kirby_ap_payload", "ap_payload.c")

    with open(payload_path, 'r') as f:
        content = f.read()

    assert "AP_DELIVERED_VITALITY_ITEM_BITS" in content, "Vitality replay-guard bitfield should be defined"
    assert "vitality_index" in content, "Vitality handler should derive per-item index"
    assert "vitality_mask" in content, "Vitality handler should derive per-item bit mask"
    assert "AP_DELIVERED_VITALITY_ITEM_BITS |= vitality_mask" in content, (
        "Vitality item handling should mark items as applied"
    )
    assert "AP_DELIVERED_VITALITY_ITEM_BITS = 0u;" in content, (
        "Mailbox initialization should clear vitality replay-guard state"
    )
    assert "KIRBY_MAX_VITALITY_COUNTERS" in content, (
        "Payload should define a hard cap for AP vitality counter grants"
    )
    assert "KIRBY_ITEM_ID_BASE_OFFSET + 101u" in content, "Ability unlock AP item lower bound should be handled"
    assert "KIRBY_ITEM_ID_BASE_OFFSET + 131u" in content, "Ability unlock AP item upper bound should be handled"


def test_payload_tracks_ability_gate_and_unlock_masks() -> None:
    payload_path = os.path.join(_WORLD_DIR, "kirby_ap_payload", "ap_payload.c")

    with open(payload_path, 'r') as f:
        content = f.read()

    assert "AP_ABILITY_GATE_MASK" in content, "Ability gate transport mask should be defined"
    assert "AP_ABILITY_UNLOCK_MASK" in content, "Ability unlock transport mask should be defined"
    assert "ap_is_locked_gated_ability" in content, "Payload should centralize gateability lock checks"
    assert "ap_select_random_allowed_ability_excluding" in content, (
        "Payload should reroll away from locked gated abilities in completely-random mode"
    )


def test_payload_tracks_sound_player_chest_checks_and_ap_unlock_apply() -> None:
    """Verify Sound Player chest checks are AP-owned and unlock only on AP item receipt."""
    payload_path = os.path.join(_WORLD_DIR, "kirby_ap_payload", "ap_payload.c")

    with open(payload_path, 'r') as f:
        content = f.read()

    assert "AP_SOUND_PLAYER_CHEST_FLAGS" in content, "Sound Player chest transport register should be defined"
    assert "ap_on_collect_sound_player_chest" in content, "Sound Player chest hook target should exist"
    assert "ap_set_sound_player_chest_flag(0u)" in content, "Sound Player chest hook should set AP check bit"
    assert "ap_apply_native_collection_reward(" in content, (
        "Fixed collection hooks must preserve grants only for non-AP sources"
    )
    assert "ap_on_collect_spray_paint_chest" in content, (
        "Spray Paint grants must be intercepted separately from popup rewards"
    )
    assert "KIRBY_COLLECT_SOUND_PLAYER_FN(0u)" in content, "AP Sound Player item should apply native unlock"
    assert "KIRBY_ITEM_ID_BASE_OFFSET + 25u" in content, "Sound Player AP item ID should be handled"


def test_payload_tracks_hub_switch_checks_from_world_map_unlocks() -> None:
    """Verify hub-switch transport is driven by persisted world-props unlock bits.

    Decomp reference (katam): `sub_08039ED4` dispatches unlock callbacks from
    `gUnk_0834BD94` using `ldrh [task, #8]`. The AP hook must read the same
    halfword and map enum WorldMapDoor values to AP hub-switch bit order while
    ignoring non-unlock values (e.g., `WORLDMAP_NO_UNLOCK` = 0). Canonical state
    must come from persisted world-props unlock bits (`sub_08002888(..., 2, ...)`) as
    written by WorldMapUnlockSave, not from callback dispatch timing alone.
    """
    payload_path = os.path.join(_WORLD_DIR, "kirby_ap_payload", "ap_payload.c")

    with open(payload_path, 'r') as f:
        content = f.read()

    assert "AP_HUB_SWITCH_FLAGS" in content, "Hub switch transport register should be defined"
    assert "ap_set_hub_switch_flag" in content, "Hub switch flag helper should exist"
    assert "ap_try_map_worldmap_door_to_hub_switch_bit" in content, "Hub switch door-to-bit mapper should exist"
    assert "ap_is_hub_unlock_persisted" in content, "Payload should probe persisted world-props unlock state"
    assert "ap_sync_hub_switch_flags_from_world_props" in content, (
        "Payload should continuously sync hub-switch flags from persisted world-props unlock bits"
    )
    assert "ap_on_world_map_unlock_call" in content, "World-map unlock hook target should exist"
    assert "task_ptr + 0x08u" in content, "Hook should read the world-map unlock task index at +0x08"
    assert "unlock_fn();" in content, "Hook should preserve native unlock callback behavior"
    assert "KIRBY_WORLD_PROPS_ENTRY_FN" in content, "Payload should reference sub_08002888 world-props accessor"
    assert "#include \"generated_hub_switch_worldmap_cases.inc\"" in content, (
        "Hub switch world-map mapping should come from generated contract include"
    )

    hook_match = re.search(
        r"void\s+ap_on_world_map_unlock_call[^{]*\{(?P<body>.*?)^}",
        content,
        flags=re.DOTALL | re.MULTILINE,
    )
    assert hook_match is not None, "ap_on_world_map_unlock_call definition must exist"
    hook_body = hook_match.group("body")

    assert "door_index = *(volatile uint16_t*)(task_ptr + 0x08u);" in hook_body, (
        "Hook should read world-map unlock index from task +0x08"
    )
    assert "ap_try_map_worldmap_door_to_hub_switch_bit(" in hook_body, (
        "Hook should translate world-map door index before setting AP hub-switch bit"
    )
    assert "unlock_fn();" in hook_body, "Hook should call the native unlock callback"
    assert hook_body.index("unlock_fn();") < hook_body.index("ap_set_hub_switch_flag(ap_hub_switch_bit);")
    assert "ap_is_hub_unlock_persisted(world_props_unlock_index)" in hook_body, (
        "Hook should only fast-path set AP hub-switch bit when persisted world-props state is visible"
    )
    assert "if (ap_try_map_worldmap_door_to_hub_switch_bit(" in hook_body, (
        "Hook should ignore NO_UNLOCK/unknown world-map door indices"
    )
    assert "ap_set_hub_switch_flag(ap_hub_switch_bit);" in hook_body, (
        "Hook should set AP hub-switch bit only after successful door-index translation"
    )

    include_path = os.path.join(_WORLD_DIR, "kirby_ap_payload", "generated_hub_switch_worldmap_cases.inc")
    assert os.path.exists(include_path), "Generated hub-switch include should exist"

    with open(include_path, "r") as f:
        include_content = f.read()

    assert "case 1u: /* WORLDMAP_MOONLIGHT_MANSION */" in include_content, (
        "Generated include should include Moonlight world-map door case"
    )
    assert "*out_bit = 11u;" in include_content, (
        "Generated include should map Moonlight world-map door to AP bit 11"
    )
    assert "*out_world_props_unlock_index = 2u;" in include_content, (
        "Generated include should map Moonlight world-map door to persisted world-props unlock index 2"
    )
    assert "case 11u: /* WORLDMAP_PEPPERMINT_PALACE_EAST */" in include_content, (
        "Generated include should include Peppermint East world-map door case"
    )
    assert "*out_bit = 10u;" in include_content, (
        "Generated include should map Peppermint East world-map door to AP bit 10"
    )


def test_hub_switch_contract_generator_uses_canonical_source() -> None:
    generator_path = os.path.join(_WORLD_DIR, "tools", "generate_hub_switch_contract.py")
    contract_path = os.path.join(_WORLD_DIR, "data", "hub_switch_contract.json")

    with open(generator_path, "r") as f:
        generator_content = f.read()

    assert "hub_switch_contract.json" in generator_content, (
        "Hub-switch generator must source mappings from canonical hub_switch_contract.json"
    )
    assert os.path.exists(contract_path), "Canonical hub_switch_contract.json should exist"






def test_boss_defeat_hook_preserves_native_shard_state() -> None:
    """Verify ap_on_boss_defeat_collect_shard records AP flag AND updates native shard state.

    Issue #380: suppressing native CollectShard left gTreasures.shardField stale,
    causing the post-cutscene game-state machine to leave the screen permanently
    white.  The hook must replicate CollectShard semantics (write KIRBY_SHARD_FLAGS
    and persist to SRAM) in addition to setting the AP boss-defeat transport flag.
    Source: d:\\kirbyam-extras\\katam\\src\\code_0801C6F8.c (sub_0801D948 / sub_0801D584).
    """
    payload_path = os.path.join(_WORLD_DIR, "kirby_ap_payload", "ap_payload.c")

    with open(payload_path, "r") as f:
        content = f.read()

    # The hook must still record the AP boss-defeat flag.
    # Restrict all checks to the ap_on_boss_defeat_collect_shard body so the
    # test cannot pass by matching the same strings in ap_apply_item or any
    # other function.
    match = re.search(
        r"void\s+ap_on_boss_defeat_collect_shard[^{]*\{(?P<body>.*?)^}",
        content,
        flags=re.DOTALL | re.MULTILINE,
    )
    assert match is not None, "ap_on_boss_defeat_collect_shard definition must exist in ap_payload.c"
    hook_body = match.group(0)

    assert "ap_set_boss_defeat_flag(boss_index)" in hook_body, \
        "Boss hook must call ap_set_boss_defeat_flag to signal the AP location check"

    # The hook must also replicate CollectShard: write the native EWRAM shard bitfield.
    assert "KIRBY_SHARD_FLAGS = new_shard_flags" in hook_body, \
        "Boss hook must write KIRBY_SHARD_FLAGS so post-cutscene state machine sees valid shard state"

    # Native save flow owns persistence; the executable save-integrity test
    # exercises this hook without permitting any direct SRAM byte changes.


def test_boss_defeat_hook_sets_scrub_delay() -> None:
    """Verify ap_on_boss_defeat_collect_shard sets AP_SHARD_SCRUB_DELAY (Issue #478).

    The scrub delay holds off the per-frame KIRBY_SHARD_FLAGS clamp so the
    post-boss cutscene state machine can read the temporary native write without
    triggering the white-screen regression from Issue #380.
    """
    payload_path = os.path.join(_WORLD_DIR, "kirby_ap_payload", "ap_payload.c")

    with open(payload_path, "r") as f:
        content = f.read()

    match = re.search(
        r"void\s+ap_on_boss_defeat_collect_shard[^{]*\{(?P<body>.*?)^}",
        content,
        flags=re.DOTALL | re.MULTILINE,
    )
    assert match is not None, "ap_on_boss_defeat_collect_shard definition must exist"
    hook_body = match.group(0)

    assert "AP_SHARD_SCRUB_DELAY" in hook_body, \
        "Boss hook must set AP_SHARD_SCRUB_DELAY to hold off shard scrub during cutscene"
    assert "SHARD_BOSS_CUTSCENE_FRAMES" in hook_body, \
        "Boss hook must assign SHARD_BOSS_CUTSCENE_FRAMES to AP_SHARD_SCRUB_DELAY"
    assert "AP_BOSS_TEMP_SHARD_BITFIELD" in hook_body, \
        "Boss hook must mark temporary boss shard bits for state-driven scrub"


def test_ap_apply_item_shard_path_writes_delivered_bitfield() -> None:
    """Verify ap_apply_item shard path writes AP_DELIVERED_SHARD_BITFIELD (Issue #478).

    AP_DELIVERED_SHARD_BITFIELD is the authority for which shard bits are
    AP-owned.  Only ap_apply_item() may set bits in it; boss-defeat must not.
    """
    payload_path = os.path.join(_WORLD_DIR, "kirby_ap_payload", "ap_payload.c")

    with open(payload_path, "r") as f:
        content = f.read()

    # Extract ap_apply_item body
    match = re.search(
        r"uint8_t\s+ap_apply_item[^{]*\{(?P<body>.*?)^}",
        content,
        flags=re.DOTALL | re.MULTILINE,
    )
    assert match is not None, "ap_apply_item definition must exist in ap_payload.c"
    apply_body = match.group(0)

    assert "AP_DELIVERED_SHARD_BITFIELD" in apply_body, \
        "ap_apply_item shard path must write AP_DELIVERED_SHARD_BITFIELD"

    # Boss hook must NOT write AP_DELIVERED_SHARD_BITFIELD
    match_boss = re.search(
        r"void\s+ap_on_boss_defeat_collect_shard[^{]*\{(?P<body>.*?)^}",
        content,
        flags=re.DOTALL | re.MULTILINE,
    )
    assert match_boss is not None, "ap_on_boss_defeat_collect_shard definition must exist"
    assert "AP_DELIVERED_SHARD_BITFIELD" not in match_boss.group(0), \
        "Boss hook must NOT write AP_DELIVERED_SHARD_BITFIELD; it is AP-delivery-only"


def test_ap_poll_mailbox_contains_shard_scrub_logic() -> None:
    """Verify ap_poll_mailbox_c contains the per-frame KIRBY_SHARD_FLAGS scrub (Issue #478).

    Once AP_SHARD_SCRUB_DELAY reaches 0, the scrub clamps KIRBY_SHARD_FLAGS to
    AP_DELIVERED_SHARD_BITFIELD so that HasShard() / NumShardsCollected() gate
    checks reflect only AP-delivered shards.
    """
    payload_path = os.path.join(_WORLD_DIR, "kirby_ap_payload", "ap_payload.c")

    with open(payload_path, "r") as f:
        content = f.read()

    match = re.search(
        r"void\s+ap_poll_mailbox_c[^{]*\{(?P<body>.*?)^}",
        content,
        flags=re.DOTALL | re.MULTILINE,
    )
    assert match is not None, "ap_poll_mailbox_c definition must exist in ap_payload.c"
    poll_body = match.group(0)

    # Strip line comments and normalize whitespace to reduce formatting brittleness.
    poll_body_code_only = re.sub(r'//[^\n]*', '', poll_body)
    poll_body_norm = re.sub(r'\s+', ' ', poll_body_code_only)

    assert "AP_SHARD_SCRUB_DELAY" in poll_body_norm, \
        "ap_poll_mailbox_c must reference AP_SHARD_SCRUB_DELAY for the scrub countdown"
    assert "AP_DELIVERED_SHARD_BITFIELD" in poll_body_norm, \
        "ap_poll_mailbox_c must read AP_DELIVERED_SHARD_BITFIELD to clamp KIRBY_SHARD_FLAGS"
    assert "AP_MAILBOX_INIT_COOKIE" in poll_body_norm, \
        "ap_poll_mailbox_c must validate mailbox init cookie before shard scrub logic"
    assert "AP_MAILBOX_INIT_COOKIE_VALUE" in poll_body_norm, \
        "ap_poll_mailbox_c must compare against AP_MAILBOX_INIT_COOKIE_VALUE"
    assert re.search(r"AP_DELIVERED_SHARD_BITFIELD\s*=\s*\(uint32_t\)\s*native_shards_boot", poll_body_norm), \
        "ap_poll_mailbox_c must seed AP_DELIVERED_SHARD_BITFIELD from native shard state on init"
    assert "AP_BOSS_TEMP_SHARD_BITFIELD" in poll_body_norm, \
        "ap_poll_mailbox_c must track temporary boss shard bits"
    assert "AI_KIRBY_STATE" in poll_body_norm, \
        "ap_poll_mailbox_c must gate scrub release on gameplay-state resume"
    assert "DEMO_PLAYBACK_FLAGS" in poll_body_norm, \
        "ap_poll_mailbox_c gameplay gate must account for title-demo playback"
    assert re.search(r"AP_DELIVERED_SHARD_BITFIELD\s*=\s*\(uint32_t\)\s*native_shards", poll_body_norm), \
        "ap_poll_mailbox_c must be able to seed AP_DELIVERED_SHARD_BITFIELD from native saved shards"
    # Native save flow persists the scrubbed EWRAM state.


def test_ap_hook_preserves_register_context_without_r4_temp_restore() -> None:
    """Verify the hook preserves full context and does not rebuild LR through r4."""
    hook_path = os.path.join(_WORLD_DIR, "kirby_ap_payload", "ap_hook.s")
    assert os.path.exists(hook_path), "ap_hook.s should exist in kirby_ap_payload"

    with open(hook_path, 'r') as f:
        content = f.read()

    # Strip // line comments so comment text cannot trigger false positives/negatives.
    code_only = re.sub(r'//[^\n]*', '', content)
    # Normalize runs of spaces/tabs to a single space.
    normalized = re.sub(r'[ \t]+', ' ', code_only)

    assert re.search(r'\bpush\s*\{r0-r3,\s*lr\}', normalized), \
        "Hook should save scratch registers and lr"
    assert re.search(r'\bbl\s+ap_poll_mailbox_c\b', normalized), \
        "Hook should call ap_poll_mailbox_c"
    assert re.search(r'\bpop\s*\{r0-r3\}', normalized), \
        "Hook should restore scratch registers before replaying overwritten instructions"
    assert re.search(r'\bmov\s+r7\s*,\s*r9\b', normalized), \
        "Hook should replay overwritten instruction mov r7, r9"
    assert re.search(r'\bmov\s+r6\s*,\s*r8\b', normalized), \
        "Hook should replay overwritten instruction mov r6, r8"
    assert re.search(r'\bpop\s*\{pc\}', normalized), \
        "Hook should return by popping the saved lr into pc"
    assert not re.search(r'\bpop\s*\{[^}]*\br4\b[^}]*\}', normalized, re.IGNORECASE), \
        "Hook must not use r4 as a temporary restore register"
    assert not re.search(r'\bmov\s+lr\s*,\s*r4\b', normalized, re.IGNORECASE), \
        "Hook must not rebuild lr through r4"


def test_copy_ability_reroll_hook_reads_object2_type_field() -> None:
    """Regression: source type must come from Object2.type (+0x82), not ObjectBase header bytes."""
    payload_path = os.path.join(_WORLD_DIR, "kirby_ap_payload", "ap_payload.c")

    with open(payload_path, "r") as f:
        content = f.read()

    match = re.search(
        r"void\s+ap_on_request_copy_ability_transition[^{]*\{(?P<body>.*?)^}",
        content,
        flags=re.DOTALL | re.MULTILINE,
    )
    assert match is not None, "ap_on_request_copy_ability_transition definition must exist"
    hook_body = match.group(0)

    assert "OBJECT2_TYPE_OFFSET 0x82u" in content, \
        "Payload must define Object2.type offset constant as +0x82"
    assert "uint8_t source_type" in hook_body, \
        "Reroll hook must load source_type as an 8-bit object type"
    assert "source_obj_ptr + OBJECT2_TYPE_OFFSET" in hook_body, \
        "Reroll hook must read source type from Object2.type field"
    assert "AP_ABILITY_REROLL_SOURCE_KIND" in content, \
        "Payload must expose reroll source-kind telemetry register"
    assert "AP_ABILITY_REROLL_CALLSITE_PC" in content, \
        "Payload must expose reroll callsite telemetry register"
    assert "AP_ABILITY_REROLL_KIRBY_INDEX" in content, \
        "Payload must expose reroll Kirby-index telemetry register"
    assert "AP_ABILITY_REROLL_SOURCE_KIND = source_kind" in hook_body, \
        "Reroll hook must write source-kind discriminator telemetry"
    assert "AP_ABILITY_REROLL_CALLSITE_PC = caller_pc" in hook_body, \
        "Reroll hook must write caller PC discriminator telemetry"
    assert "AP_ABILITY_REROLL_KIRBY_INDEX = kirby_index" in hook_body, \
        "Reroll hook must write Kirby index telemetry"
    assert "mov %0, lr" in hook_body, \
        "Reroll hook must snapshot lr before any BL clobbers the caller return address"
    assert "caller_lr_snapshot" in hook_body, \
        "Reroll hook should capture caller lr into a normal variable before helper calls"
    assert "ABILITY_REROLL_SOURCE_KIND_OBJECT2_TYPE" in content, \
        "Payload should define explicit source-kind enum values"
    assert "uint16_t source_type = *(volatile uint16_t*)(source_obj_ptr + 0u);" not in hook_body, \
        "Reroll hook must not read source_type from ObjectBase header at +0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


def test_statue_ability_lock_hook_sanitizes_transitioning_ability() -> None:
    """Regression: statues write Kirby::transitioningAbility directly at +0xDD."""
    payload_path = os.path.join(_WORLD_DIR, "kirby_ap_payload", "ap_payload.c")
    with open(payload_path, "r") as f:
        content = f.read()

    assert "KIRBY_TRANSITIONING_ABILITY_OFFSET 0xDDu" in content
    match = re.search(
        r"void\s+ap_on_start_copy_ability_transition[^{]*\{(?P<body>.*?)^}",
        content,
        flags=re.DOTALL | re.MULTILINE,
    )
    assert match is not None
    body = match.group(0)
    assert "ap_is_locked_gated_ability(pending_ability)" in body
    assert "pending_flags & (uint8_t)~KIRBY_ABILITY_MASK" in body
    assert "KIRBY_START_ABILITY_TRANSITION_FN(kirby)" in body
