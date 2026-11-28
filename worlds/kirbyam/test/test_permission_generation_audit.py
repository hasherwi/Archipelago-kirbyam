"""Reusable all-check smoke matrix for current and future starting permissions.

These finite samples protect generated archives and actual fill, not native
route coverage or a universal seed guarantee. The production starting set is
intentionally read from the supported policy: this does not enable removal.
"""

from collections import Counter
import hashlib
import inspect
import json
from pathlib import Path
from time import perf_counter
from typing import Any, Callable, cast
from collections.abc import Iterable

from BaseClasses import CollectionState, MultiWorld

import pytest

from .. import KirbyAmWorld, check_accessibility
from ..check_accessibility import KirbyAmCheckAccessibilityError
from ..peg_traversal import KirbyAmRoom16SourceError, validate_peg_assignment
from ..enemy_ability_data import ABILITY_NAME_TO_ID, GATEABLE_ENEMY_COPY_ABILITIES
from .support.check_accessibility import LocalCheckAudit, audit_local_checks
from .test_cutter_progression import _generate, _gate_words


# These seeds pin the fill outcomes archived before the optional starting mirror
# changed initial item placement. The default-on contract is audited separately.
PROFILES = (
    # weight, statues, passive, minibosses, boss spawns, rooms, keys
    (0, 0, 0, 0, 0, 0, 1),
    (99, 1, 0, 1, 0, 1, 0),
    (100, 1, 1, 1, 1, 1, 1),
)


# Current layouts are accepted only after auditing all placed checks below.
# Historical refusals and a controlled self-lock remain separate regressions.
EXPECTED_REFUSED_MINIMAL_ARCHIVES: frozenset[tuple[int, int, int]] = frozenset()
REQUIRED_MINIMAL_ARCHIVES = frozenset(
    (profile, mode, gating)
    for profile in range(len(PROFILES)) for mode in range(3) for gating in range(2)
) - EXPECTED_REFUSED_MINIMAL_ARCHIVES
# Preserve mandatory accepted-minimal coverage for every mode/gating pair.
assert {(mode, gating) for _, mode, gating in REQUIRED_MINIMAL_ARCHIVES} == {
    (mode, gating) for mode in range(3) for gating in range(2)}
# Shuffled retains native timing; new Completely Random slots carry the
# independently verified Normal timer route, including the 100% no-ability pool.
ROOM16_SOURCE_REFUSALS = frozenset({(2, 1)})


def assert_generation_contract(
    multiworld: MultiWorld, decoded: dict[str, Any], archive: Path, player: int,
) -> tuple[LocalCheckAudit, float]:
    world = cast(KirbyAmWorld, multiworld.worlds[player])
    gating = bool(world.options.ability_gating.value)
    from ..room16_timer import POLICY_KEY, ROM_OFFSET, TIMER_FRAMES
    source_policy = decoded["slot_data"][player]["enemy_copy_ability_policy"]
    expected_timer = TIMER_FRAMES if world.options.ability_randomization_mode.value == 2 else 0
    assert source_policy.get(POLICY_KEY, 0) == expected_timer
    assert _gate_words(archive, ROM_OFFSET, 2)[player] == expected_timer
    gateable = {world.item_name_to_id[f"{name} Ability"] for name in GATEABLE_ENEMY_COPY_ABILITIES}
    inventory = Counter(decoded["precollected_items"][player])
    placed = Counter(item[0] for locations in decoded["locations"].values()
                     for item in locations.values() if item[1] == player)
    assert not gateable.intersection(inventory)
    assert placed[3860501] == 1 and inventory[3860501] == 0
    assert decoded["slot_data"][player]["phone_protocol_version"] == 1
    assert decoded["slot_data"][player]["starting_phone_access"] is False
    assert "phone_progression" not in decoded["slot_data"][player]

    assert {code: placed[code] for code in gateable} == {code: int(gating) for code in gateable}
    expected_gate = sum(1 << ABILITY_NAME_TO_ID[name] for name in GATEABLE_ENEMY_COPY_ABILITIES) if gating else 0
    assert _gate_words(archive)[player] == expected_gate
    assert set(decoded["slot_data"][player]["ability_gateable_abilities"]) == (
        set(GATEABLE_ENEMY_COPY_ABILITIES) if gating else set())
    began = perf_counter()
    audit = audit_local_checks(multiworld, player)
    elapsed = perf_counter() - began
    assert audit.unfilled == ()
    # Record the real all-check audit cost, without a load-sensitive timing gate.
    return audit, elapsed


@pytest.mark.parametrize("mode", [0, 1, 2])
@pytest.mark.parametrize("gating", [0, 1])
@pytest.mark.parametrize("accessibility", ["full", "minimal"])
@pytest.mark.parametrize("profile", range(len(PROFILES)))
def test_generated_all_check_smoke_matrix(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, record_property: Callable[[str, object], None],
    mode: int, gating: int, accessibility: str, profile: int,
) -> None:
    assert inspect.signature(validate_peg_assignment).parameters["max_attempts"].default == 8192
    validate = check_accessibility.validate_all_checks
    audited_worlds = []

    def timed_validation(multiworld: MultiWorld, players: Iterable[int]) -> None:
        audited_worlds.append(multiworld)
        start = perf_counter()
        try:
            validate(multiworld, players)
        finally:
            record_property("production_audit_seconds", perf_counter() - start)

    monkeypatch.setattr(check_accessibility, "validate_all_checks", timed_validation)
    import worlds.kirbyam as kirby

    def timed_source_selection(initial: dict[str, Any], factory: Callable[[], dict[str, Any]],
                               include_statues: bool, **kwargs: Any) -> dict[str, Any]:
        assert kwargs.get("require_all_witnesses") is True
        assert kwargs["max_attempts"] == (16384 if mode == 1 and (
            kwargs.get("require_room16") or kwargs.get("room16_for_completion")) else 8192)
        attempts = 1
        start = perf_counter()

        def counted_factory() -> dict[str, Any]:
            nonlocal attempts
            attempts += 1
            return factory()

        try:
            return validate_peg_assignment(initial, counted_factory, include_statues, **kwargs)
        finally:
            record_property("source_assignment_attempts", attempts)
            record_property("source_assignment_seconds", perf_counter() - start)

    monkeypatch.setattr(kirby, "validate_peg_assignment", timed_source_selection)
    weight, statues, passive, minibosses, bosses, rooms, keys = PROFILES[profile]
    options = {
        "random_starting_mirror": 0,
        "ability_randomization_mode": mode, "ability_gating": gating, "accessibility": accessibility,
        "ability_randomization_no_ability_weight": weight, "ability_randomization_statues": statues,
        "ability_randomization_passive_enemies": passive, "ability_randomization_minibosses": minibosses,
        "ability_randomization_boss_spawns": bosses, "room_sanity": rooms, "area_keys": keys,
    }
    try:
        multiworld, decoded, archive = _generate(
            monkeypatch, tmp_path, 105100 + profile, [options],
        )
    except KirbyAmRoom16SourceError as error:
        assert (profile, mode) in ROOM16_SOURCE_REFUSALS
        assert rooms == 1 and not audited_worlds
        assert "Room 4-16" in str(error)
        assert not tuple((tmp_path / "output").glob("*.zip"))
        record_property("generation_outcome", "rejected_unqualified_room16_before_fill")
        record_property("generation_error", str(error))
        return
    except KirbyAmCheckAccessibilityError as error:
        # Minimal fill may strand optional progression. Reject before output,
        # not by changing the option or silently treating the selected goal as all checks.
        assert accessibility == "minimal"
        assert (profile, mode, gating) in EXPECTED_REFUSED_MINIMAL_ARCHIVES, "Known safe minimal archive regressed"
        assert "Try full accessibility" in str(error)
        assert "unreachable from placed progression=" in str(error)
        assert "unfilled=[]; unavailable even with all inventory=[]" in str(error)
        assert not tuple((tmp_path / "output").glob("*.zip"))
        record_property("generation_outcome", "rejected_unsafe_fill")
        record_property("generation_error", str(error))
        return
    assert (profile, mode) not in ROOM16_SOURCE_REFUSALS, "Unqualified Room16 archive was emitted"
    assert accessibility != "minimal" or (profile, mode, gating) not in EXPECTED_REFUSED_MINIMAL_ARCHIVES
    record_property("generation_outcome", "all_checks_reachable")
    audit, elapsed = assert_generation_contract(multiworld, decoded, archive, 1)
    record_property("all_check_audit_seconds", elapsed)
    record_property("inventory_unreachable", audit.inventory_unreachable)
    record_property("progression_unreachable", audit.progression_unreachable)
    assert audit.inventory_unreachable == audit.progression_unreachable == ()
    if (profile, mode, gating, accessibility) == (1, 0, 1, "minimal"):
        # Regression: this exact archive used to fail closed. Independently
        # replay AP's placed-item spheres and verify every serialized location.
        reached = set()
        for sphere in multiworld.get_spheres():
            if not sphere:  # AP next emits the remainder as an unreachable set.
                break
            reached.update(loc.address for loc in sphere if loc.player == 1 and loc.address is not None)
        assert reached == set(decoded["locations"][1])


def test_seed105101_is_now_safe_after_source_backed_goal_reconstruction(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    # Retain this exact old refusal as an accepted-output regression. The Goal
    # Game slots change the old hub-item placement here into a consumable with no progression effect.
    options = {
        "random_starting_mirror": 0,
        "ability_randomization_mode": 1, "ability_gating": 0, "accessibility": "minimal",
        "ability_randomization_no_ability_weight": 99, "ability_randomization_statues": 1,
        "ability_randomization_passive_enemies": 0, "ability_randomization_minibosses": 1,
        "ability_randomization_boss_spawns": 0, "room_sanity": 1, "area_keys": 0,
    }
    multiworld, decoded, archive = _generate(monkeypatch, tmp_path, 105101, [options])
    location = multiworld.get_location("Room 2-05", 1)
    assert location.item and "Consumable" in location.item.tags and not location.item.advancement
    audit, _ = assert_generation_contract(multiworld, decoded, archive, 1)
    assert audit.inventory_unreachable == audit.progression_unreachable == ()


@pytest.mark.parametrize("mode", [1, 2])
def test_seed105103_replays_old_goal_game_fill_lock_with_current_pool(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, mode: int,
) -> None:
    # This exact historical refusal now generates with the current ability pool.
    options = {
        "random_starting_mirror": 0,
        "ability_randomization_mode": mode, "ability_gating": 1, "accessibility": "minimal",
        "ability_randomization_no_ability_weight": 0, "ability_randomization_statues": 0,
        "ability_randomization_passive_enemies": 0, "ability_randomization_minibosses": 0,
        "ability_randomization_boss_spawns": 0, "room_sanity": 0, "area_keys": 1,
    }
    multiworld, decoded, archive = _generate(monkeypatch, tmp_path, 105103, [options])
    audit, _ = assert_generation_contract(multiworld, decoded, archive, 1)
    assert audit == LocalCheckAudit((), (), ())


@pytest.mark.parametrize("mode,controlled_smash_lock", [(1, False), (1, True), (2, False)],
                         ids=["mode1-original", "mode1-controlled-smash-lock", "mode2-original"])
def test_seed105100_accepts_current_fill_but_refuses_controlled_smash_lock(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, controlled_smash_lock: bool, mode: int,
) -> None:
    original = check_accessibility.validate_all_checks
    inspected: list[bool] = []

    def inspect_dependency(multiworld: MultiWorld, players: Iterable[int]) -> None:
        location = multiworld.get_location("Moonlight Mansion 2-20 - Small Chest", 1)
        assert location.item and not location.item.advancement
        if not controlled_smash_lock:
            actual = audit_local_checks(multiworld, 1)
            assert actual == LocalCheckAudit((), (), ()), actual
            inspected.append(True)
            original(multiworld, players)
            return
        # Reconstruct the original prevention case independently of shuffled
        # fill order. Swap the existing Smash permission behind this source's
        # peg, preserving the pool, then isolate that dependency by supplying
        # every other progression item. This controlled fixture must never emit
        # an archive and does not claim the original seed has these placements.
        smash_location, = [loc for loc in multiworld.get_locations(1)
                           if loc.item and loc.item.name == "Smash Ability"]
        location.item, smash_location.item = smash_location.item, location.item
        assert location.item and smash_location.item
        location.item.location = location
        smash_location.item.location = smash_location
        world = multiworld.worlds[1]
        for loc in multiworld.get_locations(1):
            if (loc.address is not None and loc.item and loc.item.advancement
                    and loc.item.name != "Smash Ability"):
                multiworld.push_precollected(world.create_item(loc.item.name))
        state = CollectionState(multiworld)
        state.sweep_for_advancements()
        assert not state.has("Smash Ability", 1)
        assert not location.can_reach(state)
        assert location.can_reach(multiworld.get_all_state())
        # The selected local source needs this very permission. An otherwise
        # valid peg-breaking permission is not a substitute for its assignment.
        for ability, reaches in (("Stone", False), ("Hammer", False), ("Smash", True)):
            trial = state.copy()
            trial.collect(multiworld.worlds[1].create_item(ability + " Ability"), prevent_sweep=True)
            trial.sweep_for_advancements()
            assert location.can_reach(trial) is reaches
            if reaches:
                assert all(loc.can_reach(trial) for loc in multiworld.get_locations(1)
                           if loc.address is not None)
        inspected.append(True)
        original(multiworld, players)

    monkeypatch.setattr(check_accessibility, "validate_all_checks", inspect_dependency)
    options = {
        "random_starting_mirror": 0,
        "ability_randomization_mode": mode, "ability_gating": 1, "accessibility": "minimal",
        "ability_randomization_no_ability_weight": 0, "ability_randomization_statues": 0,
        "ability_randomization_passive_enemies": 0, "ability_randomization_minibosses": 0,
        "ability_randomization_boss_spawns": 0, "room_sanity": 0, "area_keys": 1,
    }
    if not controlled_smash_lock:
        multiworld, decoded, archive = _generate(monkeypatch, tmp_path, 105100, [options])
        audit, _ = assert_generation_contract(multiworld, decoded, archive, 1)
        assert audit == LocalCheckAudit((), (), ())
    else:
        with pytest.raises(KirbyAmCheckAccessibilityError) as caught:
            _generate(monkeypatch, tmp_path, 105100, [options])
        message = str(caught.value)
        assert "unfilled=[]; unavailable even with all inventory=[]" in message
        assert "Player 1" in message and "Moonlight Mansion 2-20 - Small Chest" in message
        assert not tuple((tmp_path / "output").glob("*.zip"))
    assert inspected == [True]


def test_historical_native105100_refusal_remains_distinct_from_goal_game_fill() -> None:
    historical = json.loads((Path(__file__).parent / "data/green138-generation-contract.json").read_text())["historical_native105100"]
    assert historical["unreachable_count"] == 32
    assert hashlib.sha256(historical["error"].encode()).hexdigest() == historical["error_sha256"] == (
        "a732a9779e2293207d7701f1cb950da1131d3daf3fef1f5a08d46314fc75bb1c")
    assert "unfilled=[]; unavailable even with all inventory=[]" in historical["error"]


@pytest.mark.parametrize("mode,gating,keys", [
    (0, 0, 0), (0, 1, 1), (1, 0, 1), (1, 1, 0), (2, 0, 0), (2, 1, 1),
])
def test_default_starting_mirror_keeps_permission_generation_reachable(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, mode: int, gating: int, keys: int,
) -> None:
    from ..starting_mirror import STARTING_MIRROR_ENTRANCE, STARTING_MIRROR_ITEM
    from ..starting_mirror import TUTORIAL_WORLD_MAP_NAME, starting_mirror_candidates

    # Omit the option: these are new profiles exercising the actual user default,
    # the normal all-check guard, and the archive and ROM token outputs.
    options = {
        "ability_randomization_mode": mode, "ability_gating": gating,
        "accessibility": "full", "area_keys": keys, "room_sanity": 0,
        "ability_randomization_statues": 0,
    }
    multiworld, decoded, archive = _generate(monkeypatch, tmp_path, 520 + keys, [options])
    audit, _ = assert_generation_contract(multiworld, decoded, archive, 1)
    assert audit.inventory_unreachable == audit.progression_unreachable == ()
    slot = decoded["slot_data"][1]
    assert slot["random_starting_mirror"] is True
    reward = slot["tracker"]["starting_mirror_tutorial_item"]
    candidates = starting_mirror_candidates(bool(keys))
    assert reward in candidates
    chest = multiworld.get_location(TUTORIAL_WORLD_MAP_NAME, 1)
    assert chest.item and chest.locked and chest.item.name == reward
    world = multiworld.worlds[1]
    assert world.item_name_to_id[reward] not in decoded["precollected_items"][1]
    assert world.item_name_to_id[STARTING_MIRROR_ITEM] not in decoded["precollected_items"][1]
    state = CollectionState(multiworld)
    assert chest.can_reach(state)
    entrance = multiworld.get_entrance(STARTING_MIRROR_ENTRANCE, 1)
    assert not entrance.can_reach(state)
    state.collect(chest.item, True, chest)
    assert multiworld.get_entrance(candidates[reward], 1).can_reach(state)
    assert entrance.can_reach(state) == (reward == STARTING_MIRROR_ITEM)
