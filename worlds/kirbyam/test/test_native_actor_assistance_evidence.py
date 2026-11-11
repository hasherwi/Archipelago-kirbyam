"""Exact-trace actor audit, not a universal claim about native AI effects."""

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from .evidence_helpers import canonical_text_bytes


ROOT = Path(__file__).parents[1]


def audit() -> dict[str, Any]:
    raw = canonical_text_bytes(ROOT / "dev-docs" / "ordinary-metal-actor-assistance-audit.json")
    assert hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() == (
        "f8e2b955c16c26aecf3d15457a0c65c2470be161")
    result: dict[str, Any] = json.loads(raw)
    return result


def assert_no_global_ai_effects(changes: list[dict[str, Any]]) -> None:
    for change in changes:
        assert len(change["actors"]) == 4
        assert all(ability not in {12, 21, 24} for _, ability in change["actors"][1:])


@pytest.mark.parametrize("health,count,frames", [(100, 5, 9182), (500, 29, 20627)])
def test_published_stone_boss_damage_is_owned_by_player_one(health: int, count: int, frames: int) -> None:
    record = audit()["stone_boxer"][str(health)]
    assert record["frames"] == frames
    live = [event for event in record["events"] if event["before"] > 0]
    assert record["live_boss_damage_event_count"] == len(live) == count
    # Preserve the disclosed post-zero decrease, but do not count corpse state as combat.
    assert record["post_zero_lifecycle_decreases_included"] == len(record["events"]) - len(live) == 1
    previous_hp = 40 if health == 100 else 200
    for event in live:
        assert event["before"] == previous_hp and 0 <= event["after"] < previous_hp
        attack = event["attack"]
        assert (attack["parent"], attack["kirby2"], attack["room"]) == ("0x2020ee0", "0x0", 210)
        assert attack["damage"] in {4, 10}
        assert event["kirby_room_ability_at_drop"][0] == [210, 8]
        previous_hp = event["after"]
    assert previous_hp == 0
    assert_no_global_ai_effects(record["actor_change_log"])
    final = record["final"]
    assert final["hp_drops"] == [] and final["minhp"] == 6 and final["flag23"] == 128
    assert (final["final"]["room"], final["final"]["ability"]) == (209, 8)


@pytest.mark.parametrize("trace,room,ability,flag18", [
    ("hammer228", 228, 17, 0), ("burning743lever", 180, 0, 4),
    ("burning743joint", 708, 3, 0), ("burning708exit706", 706, 3, 0),
])
@pytest.mark.parametrize("health", [100, 500])
def test_carrier_actor_history_excludes_identified_remote_assistance(
    trace: str, room: int, ability: int, flag18: int, health: int,
) -> None:
    record, = (r for r in audit()["carriers"] if (r["trace"], r["percent"]) == (trace, health))
    assert record["ai_magic_cook_crash_frame_count"] == record["same_room_ai_frames_after_boot"] == 0
    assert_no_global_ai_effects(record["actor_change_log"])
    final = record["final"]
    assert final["hp_decreases"] == [] and final["minhp_after_boot"] == 6
    assert (final["final"]["room"], final["final"]["ability"], final["flag18"]) == (room, ability, flag18)
    if trace == "hammer228":
        assert (final["flag23"], final["flag30"]) == (128, 64)
