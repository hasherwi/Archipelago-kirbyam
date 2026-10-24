"""Distinct area-boss goal: options, graph reachability, archives and client protocol."""
from __future__ import annotations

from itertools import combinations
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from NetUtils import ClientStatus
from ..client import KirbyAmClient
from ..data import LocationCategory, data
from ..options import Goal, RequiredAreaBosses
from ..rules import set_rules
from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive
from .test_client import _run_goal_command
from .test_rules import _FakeState, _FakeWorld, _get_completion_fn

BOSS_KEYS = tuple(f"BOSS_DEFEAT_{number}" for number in range(1, 9))
BOSS_IDS = tuple(data.locations[key].location_id for key in BOSS_KEYS)
BOSS_LABELS = tuple(data.locations[key].label for key in BOSS_KEYS)
GOAL_LABEL = "Defeat a Number of Area Bosses"
INVALID_COUNTS: list[Any] = [None, True, False, 0, 9, -1, 3.0, "3", "random", [], {}]


def test_goal_count_option_contract() -> None:
    assert Goal.option_dark_mind == 0
    assert Goal.option_defeat_any_area_boss == 1
    assert Goal.option_defeat_area_boss == 2
    assert Goal.from_text("defeat_area_boss_count").value == 4
    assert 3 not in Goal.options.values()  # Reserved for already-generated hidden seeds.
    assert Goal.default == 0
    assert RequiredAreaBosses.default == 3
    assert RequiredAreaBosses.range_start == 1
    assert RequiredAreaBosses.range_end == 8
    assert len(set(BOSS_IDS)) == 8
    assert set(BOSS_IDS) == {
        loc.location_id for loc in data.locations.values() if loc.category == LocationCategory.BOSS_DEFEAT
    }
    assert data.locations["GOAL_AREA_BOSS_COUNT"].location_id == 3960012


@pytest.mark.parametrize("count", [0, 9, -1])
def test_count_option_rejects_out_of_range(count: int) -> None:
    with pytest.raises(Exception, match="lower than|higher than"):
        RequiredAreaBosses(count)


@pytest.mark.parametrize("count", range(1, 9))
def test_count_rule_and_client_agree_for_every_boss_subset(count: int) -> None:
    world: Any = _FakeWorld(Goal.option_defeat_area_boss_count)
    world.options = SimpleNamespace(goal=Goal(4), required_area_bosses=RequiredAreaBosses(count))
    set_rules(world)
    goal = world.multiworld.get_location(GOAL_LABEL, world.player)
    completion = _get_completion_fn(world)
    assert not completion(_FakeState())
    assert completion(_FakeState({GOAL_LABEL}))
    for other in ("Defeat Dark Mind", "Defeat Any Area Boss", "Defeat Area Boss"):
        assert not completion(_FakeState({other}))
        assert world.multiworld.get_location(other, world.player).access_rule(_FakeState())

    client = KirbyAmClient()
    client.initialize_client()
    for size in range(9):
        for subset in combinations(range(8), size):
            reachable = {BOSS_LABELS[index] for index in subset}
            checked = {BOSS_IDS[index] for index in subset}
            # Unrelated AP checks/items and the final boss cannot increase this count.
            checked.update({3960008, 3960012, 3860001, -1})
            assert goal.access_rule(_FakeState(reachable_locations=reachable)) is (size >= count)
            ctx = SimpleNamespace(checked_locations=checked)
            assert client._area_boss_count_goal_signal_active(ctx, count) is (size >= count)


@pytest.mark.parametrize("count", range(1, 9))
def test_goal_command_displays_count(count: int) -> None:
    noun = "boss" if count == 1 else "bosses"
    assert _run_goal_command({"goal": 4, "required_area_bosses": count,
                              "goal_hidden_area_boss_key": "BOSS_DEFEAT_1"}) == [
        f"Goal: Defeat any {count} distinct area {noun}.",
    ]


@pytest.mark.parametrize("count", INVALID_COUNTS)
@pytest.mark.asyncio
async def test_invalid_count_disables_display_and_completion(mock_bizhawk_context: Any, count: Any) -> None:
    ctx = mock_bizhawk_context
    ctx.slot_data = {"goal": 4, "required_area_bosses": count}
    ctx.checked_locations = set(BOSS_IDS)
    ctx.finished_game = False
    client = KirbyAmClient()
    client.initialize_client()
    # Even a previously latched signal must not bypass validation.
    client._native_goal_signal_seen = True
    await client._maybe_report_goal(ctx, ai_state_override=9999)
    ctx.send_msgs.assert_not_awaited()
    assert not ctx.finished_game
    assert _run_goal_command(ctx.slot_data, expected=False) == [
        "Goal unavailable: required_area_bosses must be an integer from 1 to 8 in slot data.",
    ]


@pytest.mark.parametrize("slot_data", [None, {}, {"goal": 4}, {"goal": 99}, {"goal": True}, {"goal": "4"}])
@pytest.mark.asyncio
async def test_missing_or_unsupported_goal_data_cannot_report_dark_mind(
    mock_bizhawk_context: Any, slot_data: Any,
) -> None:
    ctx = mock_bizhawk_context
    ctx.slot_data = slot_data
    ctx.finished_game = False
    ctx.checked_locations = set(BOSS_IDS)
    client = KirbyAmClient()
    client.initialize_client()
    await client._maybe_report_goal(ctx, ai_state_override=9999)
    ctx.send_msgs.assert_not_awaited()
    assert not ctx.finished_game


@pytest.mark.parametrize("count", range(1, 9))
@pytest.mark.asyncio
async def test_count_completion_waits_for_distinct_acknowledgements_and_deduplicates(
    mock_bizhawk_context: Any, count: int,
) -> None:
    ctx = mock_bizhawk_context
    ctx.slot_data = {"goal": 4, "required_area_bosses": count}
    ctx.checked_locations = set(BOSS_IDS[:count - 1])
    ctx.server_locations = set(BOSS_IDS)
    ctx.finished_game = False
    client = KirbyAmClient()
    client.initialize_client()
    with patch("worlds.kirbyam.client.bizhawk.read", new_callable=AsyncMock) as read, \
            patch("worlds.kirbyam.client.bizhawk.write", new_callable=AsyncMock) as write:
        for _ in range(2):
            await client._maybe_report_goal(ctx, ai_state_override=10000)
        ctx.send_msgs.assert_not_awaited()
        ctx.checked_locations.add(BOSS_IDS[count - 1])
        await client._maybe_report_goal(ctx)
        await client._maybe_report_goal(ctx)
        ctx.send_msgs.assert_awaited_once_with([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}])
        assert ctx.finished_game
        read.assert_not_awaited()
        write.assert_not_awaited()

    # A new client recovers from the server's persisted checks after reconnect.
    client = KirbyAmClient()
    client.initialize_client()
    ctx.finished_game = False
    ctx.send_msgs.reset_mock()
    await client._maybe_report_goal(ctx)
    ctx.send_msgs.assert_awaited_once()
    # A fresh slot cannot inherit the previous signal.
    client.initialize_client()
    ctx.checked_locations = set()
    ctx.finished_game = False
    ctx.send_msgs.reset_mock()
    await client._maybe_report_goal(ctx)
    ctx.send_msgs.assert_not_awaited()


@pytest.mark.asyncio
async def test_count_numeric_goal_waits_for_goal_acknowledgement(mock_bizhawk_context: Any) -> None:
    ctx = mock_bizhawk_context
    goal_id = data.locations["GOAL_AREA_BOSS_COUNT"].location_id
    ctx.slot_data = {"goal": 4, "required_area_bosses": 3}
    ctx.checked_locations = set(BOSS_IDS[:3])
    ctx.server_locations = {*BOSS_IDS, goal_id}
    ctx.finished_game = False
    client = KirbyAmClient()
    client.initialize_client()
    await client._maybe_report_goal(ctx)
    ctx.send_msgs.assert_awaited_once_with([{"cmd": "LocationChecks", "locations": [goal_id]}])
    assert not ctx.finished_game
    ctx.send_msgs.reset_mock()
    ctx.checked_locations.add(goal_id)
    await client._maybe_report_goal(ctx)
    ctx.send_msgs.assert_awaited_once_with([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}])


@pytest.mark.parametrize("goal", [0, 1, 2, 3])
@pytest.mark.parametrize("count", [None, 0, 8, "bad"])
@pytest.mark.asyncio
async def test_existing_goals_ignore_count(mock_bizhawk_context: Any, goal: int, count: Any) -> None:
    ctx = mock_bizhawk_context
    ctx.slot_data = {"goal": goal, "required_area_bosses": count,
                     "goal_configured_area_boss_key": "BOSS_DEFEAT_3",
                     "goal_hidden_area_boss_key": "BOSS_DEFEAT_3"}
    ctx.checked_locations = {BOSS_IDS[0]}
    ctx.server_locations = set()
    ctx.finished_game = False
    client = KirbyAmClient()
    client.initialize_client()
    await client._maybe_report_goal(ctx, ai_state_override=300)
    assert ctx.send_msgs.await_count == (1 if goal == 1 else 0)
    if goal != 1:
        ctx.checked_locations.add(data.locations["BOSS_DEFEAT_3"].location_id)
        await client._maybe_report_goal(ctx, ai_state_override=9999)
        ctx.send_msgs.assert_awaited_once()
    assert ctx.finished_game


@pytest.mark.parametrize("count", range(1, 9))
@pytest.mark.parametrize("rooms", [False, True])
def test_count_goal_generates_archive_with_addressless_event(tmp_path: Path, count: int, rooms: bool) -> None:
    yaml_path = tmp_path / "count.yaml"
    yaml_path.write_text(
        'name: CountTest\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n'
        f'  goal: defeat_area_boss_count\n  required_area_bosses: {count}\n'
        f'  room_sanity: {str(rooms).lower()}\n  shards: {0 if count % 2 else 2}\n'
        f'  ability_gating: {str(bool(count % 2)).lower()}\n  configured_area_boss: random\n',
        encoding="utf-8",
    )
    archive = generate_archive_from_fixture(yaml_path, tmp_path / "output", seed=973 + count)
    decoded = load_multidata_from_archive(archive)
    slot = decoded["slot_data"][1]
    assert slot["goal"] == 4
    assert slot["required_area_bosses"] == count
    assert set(BOSS_IDS) <= set(decoded["locations"][1])
    assert data.locations["GOAL_AREA_BOSS_COUNT"].location_id not in decoded["locations"][1]
    assert "goal_hidden_area_boss_key" not in slot
