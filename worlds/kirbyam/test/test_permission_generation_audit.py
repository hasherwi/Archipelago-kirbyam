"""Reusable all-check smoke matrix for current and future starting permissions.

These finite samples protect generated archives and actual fill, not native
route coverage or a universal seed guarantee. The production starting set is
intentionally read from the supported policy: this does not enable removal.
"""

from collections import Counter
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


# One known accepted minimal seed for every mode/gating pair. The CI safeguard
# lane must exercise playable archives as well as correctly refused unsafe fills.
# Profile1 shuffled/gating0 places the Moonlight connection behind its accepted
# carrier after the708 correction. Keep its refusal below, and require profile0
# for that accepted-output mode/gating pair instead of weakening the guard.
REQUIRED_MINIMAL_ARCHIVES = frozenset({(0, 0, 0), (0, 0, 1), (0, 1, 0), (0, 1, 1), (0, 2, 1), (1, 2, 0)})


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
    assert not gateable.intersection(inventory)
    assert all(inventory[code] == 1 for code in automatic)
    placed = Counter(item[0] for locations in decoded["locations"].values()
                     for item in locations.values() if item[1] == player)
    assert not automatic.intersection(placed)
    assert {code: placed[code] for code in gateable} == {code: int(gating) for code in gateable}
    expected_gate = sum(1 << ABILITY_NAME_TO_ID[name] for name in GATEABLE_ENEMY_COPY_ABILITIES) if gating else 0
    assert _gate_words(archive)[player] == expected_gate  # type: ignore[no-untyped-call]
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
        multiworld, decoded, archive = _generate(  # type: ignore[no-untyped-call]
            monkeypatch, tmp_path, 105100 + profile, [options],
        )
    except KirbyAmCheckAccessibilityError as error:
        # Minimal fill may strand optional progression. Reject before output,
        # not by changing the option or silently treating the selected goal as all checks.
        assert accessibility == "minimal"
        assert (profile, mode, gating) not in REQUIRED_MINIMAL_ARCHIVES, "Known safe minimal archive regressed"
        assert "Try full accessibility" in str(error)
        assert "unreachable from placed progression=" in str(error)
        assert "unavailable even with all inventory=[]" in str(error)
        assert not tuple((tmp_path / "output").glob("*.zip"))
        record_property("generation_outcome", "rejected_unsafe_fill")
        record_property("generation_error", str(error))
        return
    record_property("generation_outcome", "all_checks_reachable")
    audit, elapsed = assert_generation_contract(multiworld, decoded, archive, 1)
    record_property("all_check_audit_seconds", elapsed)
    record_property("inventory_unreachable", audit.inventory_unreachable)
    record_property("progression_unreachable", audit.progression_unreachable)
    assert audit.inventory_unreachable == audit.progression_unreachable == ()


def test_seed105101_refuses_moonlight_connection_behind_its_accepted_carrier(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    original = check_accessibility.validate_all_checks
    inspected: list[bool] = []

    def inspect_dependency(multiworld: MultiWorld, players: Iterable[int]) -> None:
        state = CollectionState(multiworld)
        state.sweep_for_advancements()
        location = multiworld.get_location("Room 2-05", 1)
        assert location.item and location.item.name == "Moonlight Mansion - Hub Connection"
        assert not location.can_reach(state)
        assert not state.has("Moonlight Mansion - Hub Connection", 1)
        assert location.can_reach(multiworld.get_all_state())
        inspected.append(True)
        original(multiworld, players)

    monkeypatch.setattr(check_accessibility, "validate_all_checks", inspect_dependency)
    options = {
        "ability_randomization_mode": 1, "ability_gating": 0, "accessibility": "minimal",
        "ability_randomization_no_ability_weight": 99, "ability_randomization_statues": 1,
        "ability_randomization_passive_enemies": 0, "ability_randomization_minibosses": 1,
        "ability_randomization_boss_spawns": 0, "room_sanity": 1, "area_keys": 0,
    }
    with pytest.raises(KirbyAmCheckAccessibilityError, match="unavailable even with all inventory=\\[\\]"):
        _generate(monkeypatch, tmp_path, 105101, [options])  # type: ignore[no-untyped-call]
    assert inspected == [True]
    assert not tuple((tmp_path / "output").glob("*.zip"))
