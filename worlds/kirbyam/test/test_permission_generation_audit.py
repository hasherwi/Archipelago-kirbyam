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
from ..peg_traversal import validate_peg_assignment
from ..enemy_ability_data import ABILITY_NAME_TO_ID, GATEABLE_ENEMY_COPY_ABILITIES, starting_copy_abilities
from .support.check_accessibility import LocalCheckAudit, audit_local_checks
from .test_cutter_progression import _generate, _gate_words


PROFILES = (
    # weight, statues, passive, minibosses, boss spawns, rooms, keys
    (0, 0, 0, 0, 0, 0, 1),
    (99, 1, 0, 1, 0, 1, 0),
    (100, 1, 1, 1, 1, 1, 1),
)


# Beam+Ice starts and Goal Game slots change deterministic fill. Classify every retained minimal
# sample explicitly: neither outcome is optional, and no seed is replaced.
EXPECTED_REFUSED_MINIMAL_ARCHIVES = frozenset({
    (0, 1, 0), (0, 2, 0), (2, 2, 1),
})
REQUIRED_MINIMAL_ARCHIVES = frozenset(
    (profile, mode, gating)
    for profile in range(len(PROFILES)) for mode in range(3) for gating in range(2)
) - EXPECTED_REFUSED_MINIMAL_ARCHIVES
# Preserve mandatory accepted-minimal coverage for every mode/gating pair.
assert {(mode, gating) for _, mode, gating in REQUIRED_MINIMAL_ARCHIVES} == {
    (mode, gating) for mode in range(3) for gating in range(2)}


def assert_generation_contract(
    multiworld: MultiWorld, decoded: dict[str, Any], archive: Path, player: int,
) -> tuple[LocalCheckAudit, float]:
    world = cast(KirbyAmWorld, multiworld.worlds[player])
    gating = bool(world.options.ability_gating.value)
    automatic = {world.item_name_to_id[f"{name} Ability"]
                 for name in starting_copy_abilities(world.options.ability_randomization_mode.value)}
    gateable = {world.item_name_to_id[f"{name} Ability"] for name in GATEABLE_ENEMY_COPY_ABILITIES}
    inventory = Counter(decoded["precollected_items"][player])
    assert automatic <= inventory.keys()
    assert gateable.intersection(inventory) == gateable.intersection(automatic)
    assert all(inventory[code] == 1 for code in automatic)
    placed = Counter(item[0] for locations in decoded["locations"].values()
                     for item in locations.values() if item[1] == player)
    assert not automatic.intersection(placed)
    assert {code: placed[code] for code in gateable} == {code: int(gating and code not in automatic) for code in gateable}
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

    def timed_validation(multiworld: MultiWorld, players: Iterable[int]) -> None:
        start = perf_counter()
        try:
            validate(multiworld, players)
        finally:
            record_property("production_audit_seconds", perf_counter() - start)

    monkeypatch.setattr(check_accessibility, "validate_all_checks", timed_validation)
    import worlds.kirbyam as kirby

    def timed_source_selection(initial: dict[str, Any], factory: Callable[[], dict[str, Any]],
                               include_statues: bool, **kwargs: Any) -> dict[str, Any]:
        assert "max_attempts" not in kwargs and kwargs.get("require_all_witnesses") is True
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
        "ability_randomization_mode": mode, "ability_gating": gating, "accessibility": accessibility,
        "ability_randomization_no_ability_weight": weight, "ability_randomization_statues": statues,
        "ability_randomization_passive_enemies": passive, "ability_randomization_minibosses": minibosses,
        "ability_randomization_boss_spawns": bosses, "room_sanity": rooms, "area_keys": keys,
    }
    try:
        multiworld, decoded, archive = _generate(
            monkeypatch, tmp_path, 105100 + profile, [options],
        )
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
    assert accessibility != "minimal" or (profile, mode, gating) not in EXPECTED_REFUSED_MINIMAL_ARCHIVES
    record_property("generation_outcome", "all_checks_reachable")
    audit, elapsed = assert_generation_contract(multiworld, decoded, archive, 1)
    record_property("all_check_audit_seconds", elapsed)
    record_property("inventory_unreachable", audit.inventory_unreachable)
    record_property("progression_unreachable", audit.progression_unreachable)
    assert audit.inventory_unreachable == audit.progression_unreachable == ()


def test_seed105101_is_now_safe_after_source_backed_goal_reconstruction(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    # Retain this exact old refusal as an accepted-output regression. The Goal
    # Game slots change the old hub-item placement here into ordinary filler.
    options = {
        "ability_randomization_mode": 1, "ability_gating": 0, "accessibility": "minimal",
        "ability_randomization_no_ability_weight": 99, "ability_randomization_statues": 1,
        "ability_randomization_passive_enemies": 0, "ability_randomization_minibosses": 1,
        "ability_randomization_boss_spawns": 0, "room_sanity": 1, "area_keys": 0,
    }
    multiworld, decoded, archive = _generate(monkeypatch, tmp_path, 105101, [options])
    location = multiworld.get_location("Room 2-05", 1)
    assert location.item and location.item.name == "Max Tomato"
    audit, _ = assert_generation_contract(multiworld, decoded, archive, 1)
    assert audit.inventory_unreachable == audit.progression_unreachable == ()


def test_seed105103_refuses_new_goal_game_fill_lock(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    # Keep the formerly accepted exact sample: Goal Game slots change its fill
    # into a progression lock, which the unchanged guard must refuse.
    options = {
        "ability_randomization_mode": 1, "ability_gating": 1, "accessibility": "minimal",
        "ability_randomization_no_ability_weight": 0, "ability_randomization_statues": 0,
        "ability_randomization_passive_enemies": 0, "ability_randomization_minibosses": 0,
        "ability_randomization_boss_spawns": 0, "room_sanity": 0, "area_keys": 1,
    }
    with pytest.raises(KirbyAmCheckAccessibilityError) as caught:
        _generate(monkeypatch, tmp_path, 105103, [options])
    message = str(caught.value)
    assert "Player 1" in message and "Cabbage Cavern - Goal Game" in message
    assert "unfilled=[]; unavailable even with all inventory=[]" in message
    assert not tuple((tmp_path / "output").glob("*.zip"))


@pytest.mark.parametrize("controlled_smash_lock", [False, True], ids=["original-fill", "controlled-smash-lock"])
def test_seed105100_accepts_original_and_refuses_controlled_smash_lock(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, controlled_smash_lock: bool,
) -> None:
    original = check_accessibility.validate_all_checks
    inspected: list[bool] = []

    def inspect_dependency(multiworld: MultiWorld, players: Iterable[int]) -> None:
        location = multiworld.get_location("Moonlight Mansion 2-20 - Small Chest", 1)
        assert location.item and location.item.name == "Moonlight Mansion - Map"
        if not controlled_smash_lock:
            # Beam+Ice plus the added slots now accepts this exact unmodified seed.
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
        "ability_randomization_mode": 1, "ability_gating": 1, "accessibility": "minimal",
        "ability_randomization_no_ability_weight": 0, "ability_randomization_statues": 0,
        "ability_randomization_passive_enemies": 0, "ability_randomization_minibosses": 0,
        "ability_randomization_boss_spawns": 0, "room_sanity": 0, "area_keys": 1,
    }
    if not controlled_smash_lock:
        multiworld, decoded, archive = _generate(monkeypatch, tmp_path, 105100, [options])
        audit, _ = assert_generation_contract(multiworld, decoded, archive, 1)
        assert audit.inventory_unreachable == audit.progression_unreachable == ()
        assert inspected == [True]
        return
    with pytest.raises(KirbyAmCheckAccessibilityError) as caught:
        _generate(monkeypatch, tmp_path, 105100, [options])
    message = str(caught.value)
    assert "unfilled=[]; unavailable even with all inventory=[]" in message
    expected = "Moonlight Mansion 2-20 - Small Chest"
    assert "Player 1" in message and expected in message
    assert inspected == [True]
    assert not tuple((tmp_path / "output").glob("*.zip"))


def test_historical_native105100_refusal_remains_distinct_from_goal_game_fill() -> None:
    historical = json.loads((Path(__file__).parent / "data/green138-generation-contract.json").read_text())["historical_native105100"]
    assert historical["unreachable_count"] == 32
    assert hashlib.sha256(historical["error"].encode()).hexdigest() == historical["error_sha256"] == (
        "a732a9779e2293207d7701f1cb950da1131d3daf3fef1f5a08d46314fc75bb1c")
    assert "unfilled=[]; unavailable even with all inventory=[]" in historical["error"]
