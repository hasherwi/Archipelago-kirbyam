"""RoomSanity requires a feasible Room16 source before fill, without weakening the gate."""

from random import Random

import pytest

from ..ability_randomization import build_enemy_copy_ability_policy
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
def test_reported_unqualified_first_draw_is_replaced_in_world(monkeypatch, accessibility):
    from .. import ability_randomization
    import worlds.kirbyam as kirby

    first = reported_policy()
    assert not SourcePolicy(first).grant("FOLEY", lambda _: True).guaranteed
    assert not static_room16_witness(SourcePolicy(first))
    attempts = []

    def factory(*args, **kwargs):
        candidate = ability_randomization.build_enemy_copy_ability_policy(*args, **kwargs) if attempts else first
        attempts.append(candidate)
        return candidate

    monkeypatch.setattr(kirby, "build_enemy_copy_ability_policy", factory)
    world = make_world(1, True, room_sanity=1, accessibility=accessibility,
                       ability_randomization_boss_spawns=1, ability_randomization_minibosses=1,
                       ability_randomization_passive_enemies=1, ability_randomization_no_ability_weight=55)
    selected = world._enemy_copy_ability_policy
    assert selected is attempts[-1] and selected is not first
    assert selected["ability_randomization_no_ability_weight"] == 55
    assert world.options.accessibility.current_key == accessibility
    assert world.fill_slot_data()["enemy_copy_ability_policy"] == selected
    assert static_room16_witness(SourcePolicy(selected))
    physical_writes = build_enemy_copy_runtime_patch_writes(selected)
    assert physical_writes[0x35197E] != build_enemy_copy_runtime_patch_writes(first)[0x35197E]
    world.create_items()
    assert world.multiworld.get_location("Room 4-16", 1).can_reach(world.multiworld.get_all_state(False))


@pytest.mark.parametrize("advanced,ability,eligible", [
    (False, "Bomb", True), (False, "UFO", True), (False, "Ice", True),
    (False, "Magic", False), (False, "Crash", False),
    (True, "Magic", True), (True, "Crash", True), (True, "Beam", False),
])
def test_only_admitted_profiles_are_eligible(advanced, ability, eligible):
    assert static_room16_witness(policy(1, pool=[ability]), advanced=advanced) is eligible


@pytest.mark.parametrize("accessibility", ["full", "minimal"])
def test_live_early_error_only_with_roomsanity(accessibility):
    with pytest.raises(KirbyAmRoom16SourceError, match="Room 4-16, but Completely Random"):
        make_world(2, False, room_sanity=1, accessibility=accessibility)
    assert make_world(2, False, room_sanity=0, accessibility=accessibility).options.room_sanity.value == 0


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
