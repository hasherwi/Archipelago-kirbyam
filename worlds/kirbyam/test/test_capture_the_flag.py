"""Capture the Flag generation and the actual Kirby client command entry point."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from BaseClasses import CollectionState
from worlds._bizhawk.context import BizHawkClientCommandProcessor
from NetUtils import ClientStatus, decode, encode

from .. import KirbyAmWorld
from ..capture_the_flag import FLAG_SLOT_KEY, GOAL_EVENT, LOCATION_NAMES, eligible_locations, resolve_flag
from ..client import KirbyAmClient, _build_kirbyam_command_processor
from ..completion import PHYSICAL_CHECK_NAMES, PHYSICAL_IDS
from ..options import Goal
from ..tracker import validate_tracker_data
from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive


def make_context(goal: int, active: set[int], checked: set[int], **slot_fields):
    return SimpleNamespace(
        game=KirbyAmClient.game, slot_data={"goal": goal, **slot_fields},
        server=SimpleNamespace(socket=SimpleNamespace(closed=False)),
        checked_locations=checked, missing_locations=active - checked, server_locations=active,
        auth="slot-auth", team=0, slot=1, finished_game=False, send_msgs=AsyncMock(), items_received=[],
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
    reconnected = make_context(Goal.option_full_completion, set(PHYSICAL_IDS), set())
    assert run_command(reconnected)[0].startswith("0/99 checks done.")
    reconnected.missing_locations.remove(target)  # incomplete server snapshot
    assert "checks done" not in run_command(reconnected)[0]


def test_flag_reveal_is_explicit_and_local() -> None:
    target = min(LOCATION_NAMES)
    ctx = make_context(Goal.option_capture_the_flag, {target}, set(), **{FLAG_SLOT_KEY: target})
    assert LOCATION_NAMES[target] not in run_command(ctx)[0]
    assert run_command(ctx, "/goal reveal") == [f"Capture the Flag location: {LOCATION_NAMES[target]}"]
    assert LOCATION_NAMES[target] not in run_command(ctx, "/goal yes", False)[0]
    ctx.slot_data[FLAG_SLOT_KEY] = True
    assert "unavailable" in run_command(ctx, "/goal reveal", False)[0]


@pytest.mark.asyncio
async def test_only_server_acknowledgement_of_flag_finishes_goal() -> None:
    target, unrelated = sorted(LOCATION_NAMES)[:2]
    ctx = make_context(Goal.option_capture_the_flag, {target, unrelated}, {unrelated}, **{FLAG_SLOT_KEY: target})
    ctx.items_received = [(100, target, 2, 0)]
    ctx.locations_checked = {target}  # client sent a check, but AP has not acknowledged it yet
    client = KirbyAmClient()
    client.initialize_client()
    with patch.object(client, "_display_client_message", new_callable=AsyncMock):
        await client._maybe_report_goal(ctx, ai_state_override=10000)
        ctx.send_msgs.assert_not_awaited()
        assert not ctx.finished_game
        # A fresh connection sees the acknowledged flag even if the item was sent remotely.
        fresh = make_context(Goal.option_capture_the_flag, {target, unrelated}, {target}, **{FLAG_SLOT_KEY: target})
        for _ in range(2):
            await client._maybe_report_goal(fresh)
        fresh.send_msgs.assert_awaited_once_with([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}])
        assert fresh.finished_game


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
