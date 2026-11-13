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
from .test_cutter_progression import CUTTER, _generate, _gate_words


PROFILES = (
    # weight, statues, passive, minibosses, boss spawns, rooms, keys
    (0, 0, 0, 0, 0, 0, 1),
    (99, 1, 0, 1, 0, 1, 0),
    (100, 1, 1, 1, 1, 1, 1),
)


# Finite accepted samples after Beam-only starts and the source-backed goal rules.
# These are historical Beam-only classifications; the current Beam+Ice sets
# below explicitly add profile0 shuffled/gating1 acceptance.
# These tables describe merged main a58d792, before the ranged catalog union.
HISTORICAL_MAIN_REQUIRED = frozenset({(0, 0, 0), (0, 0, 1), (0, 1, 0), (0, 2, 0), (0, 2, 1)})
HISTORICAL_MAIN_REFUSED = frozenset({(0, 1, 1), (1, 2, 0)})
# Historical core09 refused this exact sample with 32 stranded checks.
# Current Beam+Ice ordering accepts it; retain the old error as history.
COMBINED_CORE09 = (0, 0, 1)
REQUIRED_MINIMAL_ARCHIVES = HISTORICAL_MAIN_REQUIRED | {(0, 1, 1)}
EXPECTED_REFUSED_MINIMAL_ARCHIVES = HISTORICAL_MAIN_REFUSED - {(0, 1, 1)}


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
        assert (profile, mode, gating) not in REQUIRED_MINIMAL_ARCHIVES, "Known safe minimal archive regressed"
        assert "Try full accessibility" in str(error)
        assert "unreachable from placed progression=" in str(error)
        assert "unavailable even with all inventory=[]" in str(error)
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
    if (profile, mode, gating, accessibility) == (*COMBINED_CORE09, "minimal"):
        check_accessibility.validate_all_checks(multiworld, [1])
        state = CollectionState(multiworld)
        assert not state.has("Cutter Ability", 1)
        assert CUTTER not in decoded["precollected_items"][1]
        state.sweep_for_advancements()
        checks = [loc for loc in multiworld.get_locations(1) if loc.address is not None]
        assert len(checks) == 124
        assert all(loc.item is not None and loc.can_reach(state) for loc in checks)
        assert multiworld.completion_condition[1](state)
        cutter, = [loc for loc in checks if loc.item and loc.item.name == "Cutter Ability"]
        assert cutter.name == "Mustard Mountain Map - Big Chest" and cutter.can_reach(state)
        assert state.has("Cutter Ability", 1)


def test_seed105101_is_now_safe_after_source_backed_goal_reconstruction(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    # This exact old refusal is intentionally retained as an accepted-output
    # regression. The new item ordering places Rainbow East here, not Moonlight.
    options = {
        "ability_randomization_mode": 1, "ability_gating": 0, "accessibility": "minimal",
        "ability_randomization_no_ability_weight": 99, "ability_randomization_statues": 1,
        "ability_randomization_passive_enemies": 0, "ability_randomization_minibosses": 1,
        "ability_randomization_boss_spawns": 0, "room_sanity": 1, "area_keys": 0,
    }
    multiworld, decoded, archive = _generate(monkeypatch, tmp_path, 105101, [options])
    location = multiworld.get_location("Room 2-05", 1)
    assert location.item and location.item.name == "Rainbow Route East - Hub Connection"
    audit, _ = assert_generation_contract(multiworld, decoded, archive, 1)
    assert audit.inventory_unreachable == audit.progression_unreachable == ()


def test_seed105103_beam_ice_start_refuses_exact_placed_strands(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    # Previously accepted Beam-only sample; current required shuffled/gated
    # acceptance is seed105100. This seed must now fail before archive output.
    options = {
        "ability_randomization_mode": 1, "ability_gating": 1, "accessibility": "minimal",
        "ability_randomization_no_ability_weight": 0, "ability_randomization_statues": 0,
        "ability_randomization_passive_enemies": 0, "ability_randomization_minibosses": 0,
        "ability_randomization_boss_spawns": 0, "room_sanity": 0, "area_keys": 1,
    }
    with pytest.raises(KirbyAmCheckAccessibilityError) as caught:
        _generate(monkeypatch, tmp_path, 105103, [options])
    line = str(caught.value).splitlines()[-1]
    assert "unfilled=[]; unavailable even with all inventory=[]" in line
    assert hashlib.sha256(line.encode()).hexdigest() == "6b232eafe9e64ce915bde372a8c52484a040ccf380d408d7b0dfd189b5adc029"
    assert not tuple((tmp_path / "output").glob("*.zip"))
    assert {(mode, gating) for _, mode, gating in REQUIRED_MINIMAL_ARCHIVES} == {
        (mode, gating) for mode in range(3) for gating in range(2)}


def test_seed105100_beam_ice_start_accepts_shuffled_gated_minimal(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    # Beam-only previously stranded Smash behind its own peg. Beam+Ice changes
    # the deterministic fill; require the new accepted archive, not either result.
    options = {
        "ability_randomization_mode": 1, "ability_gating": 1, "accessibility": "minimal",
        "ability_randomization_no_ability_weight": 0, "ability_randomization_statues": 0,
        "ability_randomization_passive_enemies": 0, "ability_randomization_minibosses": 0,
        "ability_randomization_boss_spawns": 0, "room_sanity": 0, "area_keys": 1,
    }
    multiworld, decoded, archive = _generate(monkeypatch, tmp_path, 105100, [options])
    audit, _ = assert_generation_contract(multiworld, decoded, archive, 1)
    assert audit.inventory_unreachable == audit.progression_unreachable == ()
    location = multiworld.get_location("Carrot Castle - Boss Defeat", 1)
    assert location.item and location.item.name == "Smash Ability"


def test_historical_native105100_refusal_remains_distinct_from_current_requirement() -> None:
    historical = json.loads((Path(__file__).parent / "data/green138-generation-contract.json").read_text())[
        "historical_native105100"]
    assert historical["unreachable_count"] == 32
    assert hashlib.sha256(historical["error"].encode()).hexdigest() == historical["error_sha256"] == (
        "a732a9779e2293207d7701f1cb950da1131d3daf3fef1f5a08d46314fc75bb1c")
    assert "unfilled=[]; unavailable even with all inventory=[]" in historical["error"]
    assert COMBINED_CORE09 in REQUIRED_MINIMAL_ARCHIVES
    assert COMBINED_CORE09 not in EXPECTED_REFUSED_MINIMAL_ARCHIVES
    assert HISTORICAL_MAIN_REQUIRED == frozenset({(0, 0, 0), (0, 0, 1), (0, 1, 0), (0, 2, 0), (0, 2, 1)})
    assert HISTORICAL_MAIN_REFUSED == frozenset({(0, 1, 1), (1, 2, 0)})
    assert EXPECTED_REFUSED_MINIMAL_ARCHIVES == frozenset({(1, 2, 0)})
