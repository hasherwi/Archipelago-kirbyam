"""Capture the Flag generation and the actual Kirby client command entry point."""
from __future__ import annotations

from base64 import b64encode
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from BaseClasses import CollectionState
from worlds._bizhawk.context import AuthStatus, BizHawkClientCommandProcessor
from NetUtils import ClientStatus, decode, encode

from .. import KirbyAmWorld
from ..capture_the_flag import FLAG_SLOT_KEY, GOAL_EVENT, LOCATION_NAMES, eligible_locations, resolve_flag
from ..client import KirbyAmClient, _build_kirbyam_command_processor
from ..completion import PHYSICAL_CHECK_NAMES, PHYSICAL_IDS
from ..options import Goal, RANDOM_AREA_BOSS_SLOT_KEY
from ..tracker import validate_tracker_data
from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive


ROM_AUTH = b"test-rom-auth456"


def make_context(goal: int, active: set[int], checked: set[int], **slot_fields):
    return SimpleNamespace(
        game=KirbyAmClient.game, slot_data={"goal": goal, **slot_fields},
        server=SimpleNamespace(socket=SimpleNamespace(closed=False)),
        checked_locations=checked, missing_locations=active - checked, server_locations=active,
        auth=b64encode(ROM_AUTH).decode(), team=0, slot=1, finished_game=False, send_msgs=AsyncMock(), items_received=[],
        server_seed_name="current-seed", connected_identity=("current-seed", 0, 1),
        auth_status=AuthStatus.AUTHENTICATED, bizhawk_ctx=object(),
    )


def run_command(ctx, command="/goal", expected=True):
    processor = _build_kirbyam_command_processor(BizHawkClientCommandProcessor)(ctx)
    with patch.object(processor, "output") as output:
        assert processor(command) is expected
    ctx.send_msgs.assert_not_awaited()
    return [call.args[0] for call in output.call_args_list]


@pytest.mark.parametrize("remaining", [99, 11, 10, 1, 0])
def test_full_completion_progress(remaining: int) -> None:
    missing = set(sorted(PHYSICAL_IDS, reverse=True)[:remaining])
    # Acknowledged optional checks and pending local checks must not affect the tally.
    other = next(location for location in LOCATION_NAMES if location not in PHYSICAL_IDS)
    ctx = make_context(Goal.option_full_completion, set(PHYSICAL_IDS) | {other},
                       (set(PHYSICAL_IDS) - missing) | {other})
    ctx.locations_checked = missing.copy()
    names = sorted((PHYSICAL_CHECK_NAMES[location] for location in missing), key=str.casefold)
    expected = f"{len(PHYSICAL_IDS) - remaining}/{len(PHYSICAL_IDS)} checks done."
    if remaining > 10:
        expected += f" Have you checked {names[0]}?"
    elif remaining:
        expected += " Here's what's left: " + ", ".join(names)
    assert run_command(ctx) == [expected]
    assert not ctx.finished_game


def test_full_completion_does_not_use_stale_checks_after_disconnect() -> None:
    target = min(PHYSICAL_IDS)
    ctx = make_context(Goal.option_full_completion, set(PHYSICAL_IDS), {target})
    assert run_command(ctx)[0].startswith("1/99 checks done.")
    ctx.server.socket.closed = True
    assert "checks done" not in run_command(ctx)[0]
    ctx.server = SimpleNamespace(socket=SimpleNamespace(closed=False))
    ctx.auth_status = AuthStatus.PENDING
    assert "checks done" not in run_command(ctx)[0]
    reconnected = make_context(Goal.option_full_completion, set(PHYSICAL_IDS), set())
    assert run_command(reconnected)[0].startswith("0/99 checks done.")
    reconnected.missing_locations.remove(target)  # incomplete server snapshot
    assert "checks done" not in run_command(reconnected)[0]


def test_flag_reveal_is_explicit_and_local() -> None:
    target = min(LOCATION_NAMES)
    ctx = make_context(Goal.option_capture_the_flag, {target}, set(), **{FLAG_SLOT_KEY: target})
    plain = run_command(ctx)[0]
    assert LOCATION_NAMES[target] not in plain and "/goal reveal" in plain and "spoiler" in plain
    assert run_command(ctx, "/goal reveal") == [f"Capture the Flag location: {LOCATION_NAMES[target]}"]
    assert LOCATION_NAMES[target] not in run_command(ctx, "/goal yes", False)[0]
    ctx.auth_status = AuthStatus.PENDING
    assert "waiting" in run_command(ctx, "/goal reveal", False)[0]
    ctx.auth_status = AuthStatus.AUTHENTICATED
    ctx.connected_identity = ("old-seed", 0, 1)
    assert "waiting" in run_command(ctx, "/goal reveal", False)[0]
    ctx.connected_identity = ("current-seed", 0, 1)
    ctx.slot_data[FLAG_SLOT_KEY] = True
    assert "unavailable" in run_command(ctx, "/goal reveal", False)[0]


@pytest.mark.parametrize("legacy", [False, True])
def test_random_boss_spoiler_requires_explicit_command(legacy) -> None:
    fields = ({"goal_hidden_area_boss_key": "BOSS_DEFEAT_5"} if legacy else
              {RANDOM_AREA_BOSS_SLOT_KEY: True, "goal_configured_area_boss_key": "BOSS_DEFEAT_5"})
    ctx = make_context(3 if legacy else Goal.option_defeat_area_boss, {3960004}, set(), **fields)
    plain = run_command(ctx)[0]
    assert "Wiz" not in plain and "Peppermint Palace" not in plain
    assert "/goal reveal" in plain and "spoiler" in plain
    assert run_command(ctx, "/goal reveal") == ["Goal: Defeat Wiz (Peppermint Palace)."]
    ctx.slot = None
    assert "waiting" in run_command(ctx, "/goal reveal", False)[0]


def test_fixed_boss_still_named_without_reveal() -> None:
    ctx = make_context(Goal.option_defeat_area_boss, {3960004}, set(),
                       goal_configured_area_boss_key="BOSS_DEFEAT_5")
    assert run_command(ctx) == ["Goal: Defeat Wiz (Peppermint Palace)."]
    assert "Usage:" in run_command(ctx, "/goal reveal", False)[0]


@pytest.mark.asyncio
async def test_flag_requires_physical_proof_in_addition_to_server_ack(tmp_path, monkeypatch) -> None:
    import Utils
    monkeypatch.setattr(Utils.user_path, "cached_path", str(tmp_path), raising=False)
    # A real map poll decoding a native hook bit, not a delivery receipt.
    from ..data import LocationCategory, data
    location = next(loc for loc in data.locations.values()
                    if loc.category == LocationCategory.MAP_CHEST and loc.bit_index is not None)
    target = location.location_id
    unrelated = next(key for key in LOCATION_NAMES if key != target)
    assert location.bit_index is not None
    ctx = make_context(Goal.option_capture_the_flag, {target, unrelated}, {target}, **{FLAG_SLOT_KEY: target})
    ctx.items_received = [(100, target, 2, 0)]
    ctx.locations_checked = {target}
    client = KirbyAmClient()
    client.initialize_client()
    client._health_rom_auth = ROM_AUTH
    with patch.object(client, "_display_client_message", new_callable=AsyncMock):
        # !collect / !release provides exactly this AP state, including ACK.
        await client._maybe_report_goal(ctx, ai_state_override=10000)
        ctx.send_msgs.assert_not_awaited()
        assert not ctx.finished_game
        with patch("worlds.kirbyam.client.bizhawk.read", new_callable=AsyncMock) as read, patch(
                "worlds.kirbyam.client.bizhawk.guarded_read", new_callable=AsyncMock) as guard:
            read.return_value = [(1 << location.bit_index).to_bytes(4, "little")]
            guard.return_value = None  # a foreign ROM may not record this proof
            await client._poll_major_chest_locations(ctx)
            await client._maybe_report_goal(ctx)
            ctx.send_msgs.assert_not_awaited()
            guard.return_value = []
            await client._poll_major_chest_locations(ctx)
            await client._maybe_report_goal(ctx)

        assert ctx.finished_game
        ctx.send_msgs.assert_awaited_once_with([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}])
        await client._maybe_report_goal(ctx)
        assert ctx.send_msgs.await_count == 1

    # Proof survives a fresh client/reconnect but cannot cross seeds.
    for seed, complete in [("different-seed", False), ("current-seed", True)]:
        fresh = make_context(Goal.option_capture_the_flag, {target, unrelated}, {target}, **{FLAG_SLOT_KEY: target})
        fresh.server_seed_name = seed
        fresh.connected_identity = (seed, 0, 1)
        client = KirbyAmClient()
        client.initialize_client()
        client._health_rom_auth = ROM_AUTH
        with patch.object(client, "_display_client_message", new_callable=AsyncMock):
            await client._maybe_report_goal(fresh)
        assert fresh.finished_game is complete


def test_generated_random_boss_keeps_hidden_intent_in_slot_data(tmp_path) -> None:
    fixture = tmp_path / "boss.yaml"
    fixture.write_text("name: BossTest\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n"
                       "  goal: defeat_area_boss\n  configured_area_boss: random\n", encoding="utf-8")
    archive = generate_archive_from_fixture(fixture, tmp_path / "boss-out", seed=367)
    slot_data = decode(encode(load_multidata_from_archive(archive)["slot_data"][1]))
    assert slot_data[RANDOM_AREA_BOSS_SLOT_KEY] is True
    key = slot_data["goal_configured_area_boss_key"]
    assert key.startswith("BOSS_DEFEAT_")
    assert type(slot_data["configured_area_boss"]) is int


def test_fixed_seed_archive_persists_a_reachable_enabled_flag(tmp_path) -> None:
    target_ids = []
    yaml = tmp_path / "player.yaml"
    yaml.write_text("""
name: FlagTest
game: Kirby & The Amazing Mirror
Kirby & The Amazing Mirror:
  goal: capture_the_flag
  room_sanity: false
  exclude_locations:
    - Tutorial World Map - Big Chest
""", encoding="utf-8")
    resolve = KirbyAmWorld.finalize_multiworld

    def verify(world):
        resolve(world)
        target_id = world._flag_location_id
        assert target_id is not None
        target = world.multiworld.get_location(LOCATION_NAMES[target_id], world.player)
        event = world.multiworld.get_location(GOAL_EVENT, world.player)
        assert target in eligible_locations(world)
        assert target.item is not None and target.item.location is target
        assert event.address is None
        assert world.multiworld.can_beat_game()
        assert not world.multiworld.has_beaten_game(CollectionState(world.multiworld))
        state = CollectionState(world.multiworld)
        state.sweep_for_advancements()
        assert event.can_reach(state)
        assert world.multiworld.has_beaten_game(state)
        assert all(loc.address != target.address for loc in world.multiworld.get_unfilled_locations(world.player))

    with patch.object(KirbyAmWorld, "finalize_multiworld", verify):
        for attempt in range(2):
            archive = generate_archive_from_fixture(yaml, tmp_path / str(attempt), seed=367)
            multidata = load_multidata_from_archive(archive)
            slot_data = multidata["slot_data"][1]
            assert slot_data["goal"] == Goal.option_capture_the_flag
            validate_tracker_data(decode(encode(slot_data)))
            target = slot_data[FLAG_SLOT_KEY]
            assert target in multidata["locations"][1]
            assert LOCATION_NAMES[target] != "Tutorial World Map - Big Chest"
            target_ids.append(target)
    assert target_ids[0] == target_ids[1]

def test_resolve_flag_ignores_self_locked_and_excluded_candidates(tmp_path) -> None:
    # Inspect a real graph with real placements: make a target require an
    # event item available only at that same target. An all-items reachability
    # query would let it nominate itself.
    yaml = tmp_path / "test.yaml"
    yaml.write_text("name: Kirby\ngame: Kirby & The Amazing Mirror\n"
                    "Kirby & The Amazing Mirror:\n  goal: capture_the_flag\n", encoding="utf-8")
    finalize = KirbyAmWorld.finalize_multiworld

    def test_then_finalize(world):
        eligible = eligible_locations(world)
        target = next(loc for loc in eligible if loc.item and not loc.item.advancement and not loc.locked)
        original_item, original_rule = target.item, target.access_rule
        target.item = world.create_event("Flag validation test token")
        target.access_rule = lambda state: state.has("Flag validation test token", world.player)
        try:
            with patch.object(world.random, "choice", wraps=world.random.choice) as choose:
                assert resolve_flag(world) != target.address
                candidates = choose.call_args.args[0]
                assert target.address not in candidates
                assert candidates == sorted(candidates)
        finally:
            target.item, target.access_rule = original_item, original_rule
        finalize(world)

    with patch.object(KirbyAmWorld, "finalize_multiworld", test_then_finalize):
        generate_archive_from_fixture(yaml, tmp_path / "out", seed=367)


@pytest.mark.asyncio
async def test_acknowledged_flag_does_not_synthesize_its_lever_pull() -> None:
    from ..data import LocationCategory, data
    target = next(loc.location_id for loc in data.locations.values() if loc.category == LocationCategory.LEVER)
    ctx = make_context(Goal.option_capture_the_flag, {target}, {target}, **{FLAG_SLOT_KEY: target})
    client = KirbyAmClient()
    client.initialize_client()
    client._health_rom_auth = ROM_AUTH
    client._lever_checked_session = client._authenticated_session_key(ctx)
    with patch("worlds.kirbyam.client.bizhawk.read", new_callable=AsyncMock) as read, patch(
            "worlds.kirbyam.client.bizhawk.guarded_write", new_callable=AsyncMock) as write:
        await client._reconcile_lever_activations(ctx)
        read.assert_not_awaited()
        write.assert_not_awaited()


@pytest.mark.asyncio
async def test_cold_reload_recovers_native_boss_flag_without_offline_client(tmp_path, monkeypatch) -> None:
    import Utils
    from ..capture_the_flag import BOSS_FLAG_CONFIG_ROM_OFFSET, boss_flag_config
    from ..completion import (PHYSICAL_SAVE_ADDRESS, PHYSICAL_SAVE_BOSS_FLAG_TAG, PHYSICAL_SAVE_V3_TAG,
                              SAVE_ID_ADDRESS, merge_acknowledged_levers, saved_boss_flag)
    from ..data import data
    monkeypatch.setattr(Utils.user_path, "cached_path", str(tmp_path), raising=False)
    location = data.locations["BOSS_DEFEAT_2"]
    target = location.location_id
    config = boss_flag_config(target)
    assert config == b"CFB" + bytes([location.bit_index])
    ctx = make_context(Goal.option_capture_the_flag, {target}, set(), **{FLAG_SLOT_KEY: target})
    client = KirbyAmClient()
    client.initialize_client()
    client._health_rom_auth = ROM_AUTH
    client._display_client_message = AsyncMock()

    # Offline battle followed by an ordinary native save and a cold boot:
    # volatile hook bits and the local proof journal both start empty.
    selected = ROM_AUTH + (PHYSICAL_SAVE_BOSS_FLAG_TAG | (1 << 20)).to_bytes(4, "little")
    restored = merge_acknowledged_levers(selected, ROM_AUTH, 4)
    assert saved_boss_flag(restored, ROM_AUTH)
    cosmetic_only = ROM_AUTH + (PHYSICAL_SAVE_V3_TAG | (1 << 20)).to_bytes(4, "little")
    foreign = b"other-rom-auth16" + selected[16:]
    cases = [(cosmetic_only, bytes(2), config), (foreign, bytes(2), config),
             (restored, bytes(2), b"CFB\xff"), (restored, b"\x03\x00", config),
             (restored, bytes(2), config)]
    for record, save_id, rom_config in cases:
        async def guard(_emu, reads, guards):
            if reads:
                assert reads == [(PHYSICAL_SAVE_ADDRESS, 20, "System Bus"), (SAVE_ID_ADDRESS, 2, "System Bus")]
                assert (BOSS_FLAG_CONFIG_ROM_OFFSET, config, "ROM") in guards
                return [record, save_id] if rom_config == config else None
            return []

        with patch("worlds.kirbyam.client.bizhawk.read", new_callable=AsyncMock, return_value=[bytes(4)]), patch(
                "worlds.kirbyam.client.bizhawk.guarded_read", side_effect=guard):
            await client._poll_boss_defeat_locations(ctx)
            await client._maybe_report_goal(ctx)
        if (record, save_id, rom_config) != cases[-1]:
            ctx.send_msgs.assert_not_awaited()
    # Recovered physical proof sends the real check; goal still waits for AP.
    ctx.send_msgs.assert_awaited_once_with([{"cmd": "LocationChecks", "locations": [target]}])
    assert not ctx.finished_game
    ctx.checked_locations.add(target)
    ctx.missing_locations.remove(target)
    await client._maybe_report_goal(ctx)
    assert ctx.finished_game
    assert ctx.send_msgs.await_args.args[0] == [{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}]
