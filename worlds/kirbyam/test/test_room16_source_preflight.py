"""RoomSanity and the completion goal cannot skip the native Room16 visit."""

from random import Random

import pytest

from ..ability_randomization import build_enemy_copy_ability_policy
from ..data import LocationCategory, data
from ..enemy_ability_runtime_patch import build_enemy_copy_runtime_patch_writes
from ..peg_traversal import KirbyAmRoom16SourceError, validate_peg_assignment
from ..traversal import SourcePolicy
from ..traversal_rules import static_room16_witness
from .test_mini_traversal import make_world
from .test_traversal import policy


def reported_policy() -> dict:
    raw = build_enemy_copy_ability_policy(Random(0), 1, True, True, include_passive_enemies=True,
                                          no_ability_weight=55)
    raw["seed"] = 11594085988372860574
    return raw


@pytest.mark.parametrize("accessibility", ["full", "minimal"])
@pytest.mark.parametrize("goal,room_sanity", [("dark_mind", 1), ("full_completion", 0), ("full_completion", 1)])
def test_reported_unqualified_first_draw_is_repaired_in_world(monkeypatch, accessibility, goal, room_sanity):
    from ..enemy_ability_runtime_patch import SHUFFLE_SOURCE_SWAPS
    import worlds.kirbyam as kirby

    first = reported_policy()
    assert not SourcePolicy(first).grant("FOLEY", lambda _: True).guaranteed
    assert not static_room16_witness(SourcePolicy(first))
    attempts = []

    def factory(*args, **kwargs):
        assert not attempts, "Standard Shuffle must not redraw the policy"
        attempts.append(first)
        return first

    monkeypatch.setattr(kirby, "build_enemy_copy_ability_policy", factory)
    world = make_world(1, True, goal=goal, room_sanity=room_sanity, accessibility=accessibility,
                       ability_randomization_boss_spawns=1, ability_randomization_minibosses=1,
                       ability_randomization_passive_enemies=1, ability_randomization_no_ability_weight=55)
    selected = world._enemy_copy_ability_policy
    assert len(attempts) == 1 and selected is not first
    assert selected["seed"] == first["seed"] and selected[SHUFFLE_SOURCE_SWAPS]
    assert selected["ability_randomization_no_ability_weight"] == 55
    assert world.options.accessibility.current_key == accessibility
    assert world.fill_slot_data()["enemy_copy_ability_policy"] == selected
    assert static_room16_witness(SourcePolicy(selected))
    physical_writes = build_enemy_copy_runtime_patch_writes(selected)
    assert physical_writes[0x35197E] != build_enemy_copy_runtime_patch_writes(first)[0x35197E]
    world.create_items()
    multiworld = world.multiworld
    state = multiworld.get_all_state()
    assert state.can_reach_region("REGION_MUSTARD_MOUNTAIN/ROOM_4_16", 1)
    ap_rooms = {loc.location_id for loc in data.locations.values()
                if loc.category == LocationCategory.ROOM_SANITY}
    expected_rooms = ap_rooms if room_sanity else {loc.location_id for loc in data.locations.values()
                                                 if "CoreLandmark" in loc.tags}
    assert {loc.address for loc in multiworld.get_locations(1)} & ap_rooms == expected_rooms
    if room_sanity:
        assert multiworld.get_location("Room 4-16", 1).can_reach(state)
    else:
        with pytest.raises(KeyError):
            multiworld.get_location("Room 4-16", 1)
    if goal == "full_completion":
        assert multiworld.get_location("100% Game Completion", 1).can_reach(state)


@pytest.mark.parametrize("advanced,ability,eligible", [
    (False, "Bomb", True), (False, "UFO", True), (False, "Ice", True),
    (False, "Magic", False), (False, "Crash", False),
    (True, "Magic", True), (True, "Crash", True), (True, "Beam", False),
])
def test_only_admitted_profiles_are_eligible(advanced, ability, eligible):
    assert static_room16_witness(policy(1, pool=[ability]), advanced=advanced) is eligible


@pytest.mark.parametrize("accessibility", ["full", "minimal"])
@pytest.mark.parametrize("room_sanity", [0, 1])
@pytest.mark.parametrize("goal", ["dark_mind", "full_completion"])
@pytest.mark.parametrize("gating", [0, 1])
def test_live_timer_patch_preserves_full_completion(accessibility, room_sanity, goal, gating):
    from ..room16_timer import POLICY_KEY, TIMER_FRAMES, timer_bytes
    world = make_world(2, gating, goal=goal, room_sanity=room_sanity, accessibility=accessibility)
    raw = world._enemy_copy_ability_policy
    assert raw[POLICY_KEY] == TIMER_FRAMES
    assert timer_bytes(raw) == TIMER_FRAMES.to_bytes(2, "little")
    assert not SourcePolicy(raw).grant("FOLEY", lambda _: True).guaranteed
    assert static_room16_witness(SourcePolicy(raw))
    world.create_items()
    state = world.multiworld.get_all_state()
    assert state.can_reach_region("REGION_MUSTARD_MOUNTAIN/ROOM_4_16", 1)
    if room_sanity:
        assert world.multiworld.get_location("Room 4-16", 1).can_reach(state)
    if goal == "full_completion":
        assert world.multiworld.get_location("100% Game Completion", 1).can_reach(state)
    assert world.fill_slot_data()["enemy_copy_ability_policy"] == raw


@pytest.mark.parametrize("room_sanity", [0, 1])
def test_full_completion_still_rejects_unqualified_shuffled(room_sanity):
    with pytest.raises(KirbyAmRoom16SourceError, match="100% no-ability weight"):
        make_world(1, False, goal="full_completion", room_sanity=room_sanity,
                   ability_randomization_no_ability_weight=100)


def test_native_foley_unchanged_and_shuffled_search_is_bounded():
    native = policy(0).policy
    assert validate_peg_assignment(native, lambda: pytest.fail("Off cannot reroll"), False,
                                   require_room16=True) is native
    initial = reported_policy()
    draws = []

    def factory():
        draws.append(None)
        return initial

    with pytest.raises(KirbyAmRoom16SourceError, match="after 3 attempts"):
        validate_peg_assignment(initial, factory, False, 3, require_all_witnesses=False, require_room16=True)
    assert len(draws) == 2
    assert validate_peg_assignment(initial, factory, False, require_all_witnesses=False) is initial
    assert len(draws) == 2
    with pytest.raises(KirbyAmRoom16SourceError, match="100% no-ability weight"):
        validate_peg_assignment(dict(initial, ability_randomization_no_ability_weight=100),
                                lambda: pytest.fail("Cannot reroll 100% no-ability"), False, require_room16=True)
