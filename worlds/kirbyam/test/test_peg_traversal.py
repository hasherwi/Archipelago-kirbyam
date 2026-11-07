"""Reviewed local peg witnesses and full native census coverage."""

import pytest
from pathlib import Path
import re
from BaseClasses import CollectionState

from ..data import data
from ..peg_traversal import PEG_ROUTES, peg_graph
from ..traversal import SourcePolicy
from .test_mini_traversal import make_world


def test_census_covers_all_fourteen_pegs_without_blanket_room_gates():
    document = Path(__file__).parents[1] / "docs" / "traversal-logic.md"
    ids = re.findall(r"^#### `(peg_[0-9_]+)`$", document.read_text(encoding="utf-8"), re.MULTILINE)
    assert len(ids) == len(set(ids)) == 14
    assert len({key.split("_")[1] for key in ids}) == 13
    assert {int(key.split("_")[1]) for key in ids} == {
        149, 204, 218, 221, 401, 411, 509, 510, 513, 527, 605, 741, 816,
    }
    assert len([key for key in ids if key.startswith("peg_527_")]) == 2
    assert len(PEG_ROUTES) == 11
    assert set(ids) - {row["id"] for row in PEG_ROUTES} == {
        "peg_218_9_33", "peg_509_32_2", "peg_741_27_13",
    }


@pytest.mark.parametrize("mode", [0, 1])
@pytest.mark.parametrize("gating", [False, True])
def test_real_peg_rules_use_same_local_assignment_as_rom(mode, gating):
    world = make_world(mode, gating)
    resolver = SourcePolicy(world._enemy_copy_ability_policy)
    state = CollectionState(world.multiworld)
    for row in PEG_ROUTES:
        if not peg_graph(row).placements:
            continue
        graph = peg_graph(row)
        owned = frozenset(
            item.name for item in world.multiworld.precollected_items[1]
        )
        expected = graph.evaluate(resolver, owned, gating).reaches("target")
        if row["exit"]:
            target = world.multiworld.get_entrance(f"{row['region']} -> {row['exit']}", 1)
        else:
            target = world.multiworld.get_location(data.locations[row["location"]].label, 1)
        assert target.access_rule(state) == expected
        for name in ("Hammer Ability", "Smash Ability"):
            state.collect(world.create_item(name), prevent_sweep=True)
        full_owned = owned | {"Hammer Ability", "Smash Ability"}
        assert target.access_rule(state) == graph.evaluate(resolver, full_owned, gating).reaches("target")
        for name in ("Hammer Ability", "Smash Ability"):
            state.remove(world.create_item(name))


def test_local_peg_rules_do_not_gate_unrelated_exits():
    world = make_world(0, True)
    state = CollectionState(world.multiworld)
    for source, destination in [
        ("REGION_CANDY_CONSTELLATION/ROOM_9_06", "REGION_CANDY_CONSTELLATION/ROOM_9_07"),
        ("REGION_PEPPERMINT_PALACE/ROOM_7_22", "REGION_PEPPERMINT_PALACE/ROOM_7_15"),
        ("REGION_PEPPERMINT_PALACE/ROOM_7_22", "REGION_PEPPERMINT_PALACE/ROOM_7_20"),
    ]:
        assert world.multiworld.get_entrance(f"{source} -> {destination}", 1).access_rule(state)


@pytest.mark.parametrize("mode", [0, 1, 2])
def test_fixed_statue_carry_requires_connections_and_preserves_stone(mode):
    from ..peg_traversal import stone_carry_graph
    from ..ability_randomization import build_enemy_copy_ability_policy
    import random
    policy_data = build_enemy_copy_ability_policy(random.Random(773), mode, False, False)
    policy_data["ability_randomization_no_ability_weight"] = 100
    policy = SourcePolicy(policy_data, include_statues=False)
    for row in PEG_ROUTES:
        if row["native_room"] == 149:  # The reviewed hub carry through the 143 rope needs Smash, tested separately.
            continue
        graph = stone_carry_graph(row, True)
        items = frozenset(item for route in graph.routes for item in route.items)
        assert not graph.evaluate(policy, frozenset(), True).reaches("target")
        assert graph.evaluate(policy, items, True).reaches("target")
        for item in items:
            assert not graph.evaluate(policy, items - {item}, True).reaches("target")


def test_happy_notes_compartment_is_one_way():
    world = make_world(0, True)
    main = world.multiworld.get_region("REGION_PEPPERMINT_PALACE/ROOM_7_06", 1)
    upper = world.multiworld.get_region("REGION_PEPPERMINT_PALACE/ROOM_7_06__LOGIC__HAPPY_NOTES_ENTRY", 1)
    assert any(exit.connected_region is main for exit in upper.exits)
    assert not any(exit.connected_region is upper for exit in main.exits)


def test_random_statue_retry_is_explicit_and_does_not_use_enemy_weight():
    from ..peg_traversal import stone_carry_graph
    from ..ability_randomization import build_enemy_copy_ability_policy
    import random
    raw = build_enemy_copy_ability_policy(random.Random(773), 2, False, False)
    raw["ability_randomization_no_ability_weight"] = 100
    policy = SourcePolicy(raw, include_statues=True)
    graph = stone_carry_graph(next(row for row in PEG_ROUTES if row["native_room"] == 411), False)
    items = frozenset(item for route in graph.routes for item in route.items)
    assert not graph.evaluate(policy, items, True).reaches("target")
    result = graph.evaluate(policy, items, True, allow_documented_retries=True)
    assert result.reaches("target")
    assert result.retry_assumptions


def test_gate_side_reach_does_not_bootstrap_remote_statue():
    from unittest.mock import patch
    from ..peg_traversal import stone_carry_graph
    world = make_world(0, True)
    row = next(row for row in PEG_ROUTES if row["native_room"] == 411)  # 411 has no local source.
    graph = stone_carry_graph(row, world._area_keys_enabled())
    state = CollectionState(world.multiworld)
    for item in {item for route in graph.routes for item in route.items}:
        state.collect(world.create_item(item), prevent_sweep=True)
    target = world.multiworld.get_entrance(f"{row['region']} -> {row['exit']}", 1)
    with patch.object(state, "can_reach_region", return_value=False):
        assert not target.access_rule(state)
    with patch.object(state, "can_reach_region", return_value=True):
        assert target.access_rule(state)


def test_weight100_static_assignments_are_resampled_without_forcing_outputs():
    import random
    from ..ability_randomization import build_enemy_copy_ability_policy
    from ..peg_traversal import _assignment_has_witness, validate_peg_assignment
    rng = random.Random(939)

    def factory():
        return build_enemy_copy_ability_policy(rng, 1, False, False, no_ability_weight=100)

    selected = validate_peg_assignment(factory(), factory, True)
    policy = SourcePolicy(selected, include_statues=True)
    assert all(_assignment_has_witness(row, policy) for row in PEG_ROUTES)
    assert selected["ability_randomization_no_ability_weight"] == 100


def test_assignment_budget_exhaustion_is_diagnostic_not_impossibility(monkeypatch):
    from .. import peg_traversal, wheel_traversal
    monkeypatch.setattr(wheel_traversal, "static_wheel_witness", lambda *args: True)
    initial = {"mode": 1}
    calls = []
    monkeypatch.setattr(peg_traversal, "SourcePolicy", lambda *args: type("Policy", (), {"mode": 1})())
    monkeypatch.setattr(peg_traversal, "_assignment_has_witness", lambda *args: False)
    with pytest.raises(ValueError, match="peg-source search budget exhausted after 3 attempts") as error:
        peg_traversal.validate_peg_assignment(initial, lambda: calls.append(1) or initial, False, 3)
    assert len(calls) == 2
    assert "does not prove" in str(error.value)


def test_unvalidated_wheel_seed_fails_when_search_budget_exhausted(monkeypatch):
    from .. import peg_traversal, wheel_traversal
    monkeypatch.setattr(wheel_traversal, "static_wheel_witness", lambda *args: False)
    monkeypatch.setattr(peg_traversal, "SourcePolicy", lambda *args: type("Policy", (), {"mode": 1})())
    initial = {"mode": 1, "seed": 123}
    with pytest.raises(ValueError, match="Wheel-source search budget exhausted after 3 attempts"):
        peg_traversal.validate_peg_assignment(initial, lambda: initial, False, 3)


@pytest.mark.parametrize("entry,gets_chest,gets_lower_exit", [
    ("_UPPER_ENTRY", False, True),
    ("_LOWER_ENTRY", True, True),
    ("__LOGIC__FROM_3_13", False, False),
])
def test_515_native_arrivals_keep_chest_and_exit_direction(entry, gets_chest, gets_lower_exit):
    from BaseClasses import MultiWorld, Region
    from .. import KirbyAmWorld
    from ..rules import evaluate_room_logic_requirement
    base = "REGION_CABBAGE_CAVERN/ROOM_3_15"
    lower_exit = "REGION_CABBAGE_CAVERN/ROOM_3_16"
    return_exit = "REGION_CABBAGE_CAVERN/ROOM_3_13_LOWER"
    names = [base + suffix for suffix in ("", "_UPPER_ENTRY", "_LOWER_ENTRY",
                                          "__LOGIC__LOWER_CHEST", "__LOGIC__FROM_3_13", "__ROOM_CHECK")]
    mw = MultiWorld(1)
    mw.worlds[1] = KirbyAmWorld(mw, 1)
    regions = {name: Region(name, 1, mw) for name in ["Menu", *names, lower_exit, return_exit]}
    mw.regions.extend(regions.values())
    for name in names:
        definition = data.regions[name]
        for destination in definition.exits:
            if destination in regions:
                requirement = definition.exit_requirements.get(destination)
                regions[name].connect(regions[destination], rule=lambda state, requirement=requirement:
                                      evaluate_room_logic_requirement(requirement, state, 1))
    regions["Menu"].connect(regions[base + entry])
    state = CollectionState(mw)
    assert regions[base + "__LOGIC__LOWER_CHEST"].can_reach(state) == gets_chest
    assert regions[lower_exit].can_reach(state) == gets_lower_exit
    assert regions[return_exit].can_reach(state)


def test_527_peg_only_gates_lower_door():
    from unittest.mock import patch
    world = make_world(0, True)
    state = CollectionState(world.multiworld)
    source = "REGION_CABBAGE_CAVERN/ROOM_3_14"
    upper = world.multiworld.get_entrance(source + " -> REGION_CABBAGE_CAVERN/ROOM_3_15_UPPER_ENTRY", 1)
    lower = world.multiworld.get_entrance(source + " -> REGION_CABBAGE_CAVERN/ROOM_3_15_LOWER_ENTRY", 1)
    with patch.object(state, "can_reach_region", return_value=False):
        assert upper.access_rule(state)
        assert not lower.access_rule(state)
    state.collect(world.create_item("Cabbage Cavern - Area Key"), prevent_sweep=True)
    with patch.object(state, "can_reach_region", return_value=True):
        assert upper.access_rule(state) and lower.access_rule(state)


def make_isolated_fixed_peg_world(room):
    from unittest.mock import patch
    from .. import peg_traversal
    row = next(row for row in PEG_ROUTES if row["native_room"] == room)
    with patch.object(peg_traversal, "PEG_ROUTES", (row,)), \
            patch("worlds.kirbyam.wheel_traversal.install_wheel_rules"):
        return make_world(2, True, ability_randomization_no_ability_weight=100,
                          ability_randomization_statues=False)


@pytest.mark.parametrize("room", [204, 510, 513, 527, 605])
def test_new_carriers_cannot_bootstrap_disconnected_source_hub(room):
    world = make_isolated_fixed_peg_world(room)
    row = next(row for row in PEG_ROUTES if row["native_room"] == room)
    hub = ("REGION_RAINBOW_ROUTE/ROOM_1_HUB_1" if room == 204
           else "REGION_CABBAGE_CAVERN/ROOM_3_HUB_3")
    for entrance in world.multiworld.get_region(hub, 1).entrances:
        entrance.access_rule = lambda state: False
    state = CollectionState(world.multiworld)
    for name in world.item_name_to_id:
        state.collect(world.create_item(name), prevent_sweep=True)
    assert not state.can_reach_region(hub, 1)
    if row["exit"]:
        target = world.multiworld.get_entrance(f"{row['region']} -> {row['exit']}", 1)
    else:
        target = world.multiworld.get_location(data.locations[row["location"]].label, 1)
    assert not target.access_rule(state)


def test_513_reverse_bomb_bypass_does_not_unlock_forward_peg():
    from unittest.mock import patch
    world = make_isolated_fixed_peg_world(513)
    upper = "REGION_CABBAGE_CAVERN/ROOM_3_13"
    lower = upper + "_LOWER"
    forward = world.multiworld.get_entrance(upper + " -> " + lower, 1)
    reverse = world.multiworld.get_entrance(lower + " -> " + upper, 1)
    state = CollectionState(world.multiworld)
    with patch.object(state, "can_reach_region", return_value=False):
        assert reverse.access_rule(state)
        assert not forward.access_rule(state)
    state.collect(world.create_item("Cabbage Cavern - Area Key"), prevent_sweep=True)
    with patch.object(state, "can_reach_region", return_value=True):
        assert forward.access_rule(state) and reverse.access_rule(state)


@pytest.mark.parametrize("mode", [0, 1, 2])
def test_149_room970_carrier_stays_unavailable(mode):
    import random
    from ..ability_randomization import build_enemy_copy_ability_policy
    from ..peg_traversal import stone_carry_graph
    raw = build_enemy_copy_ability_policy(random.Random(773), mode, False, False, no_ability_weight=100)
    row = next(row for row in PEG_ROUTES if row["native_room"] == 149)
    late = stone_carry_graph(row, True, statue_room=True)
    items = frozenset(item for route in late.routes for item in route.items) | {"Smash Ability"}
    assert late.unavailable_reason
    for include_statues in (False, True):
        assert not late.evaluate(SourcePolicy(raw, include_statues), items, True,
                                 allow_documented_retries=True).reaches("target")


@pytest.mark.parametrize("mode", [1, 2])
def test_149_hub_statues_need_actual_smash_permission_and_access(mode):
    from unittest.mock import patch
    from ..traversal_data import room_traversal_graph
    world = make_world(mode, True, ability_randomization_no_ability_weight=100,
                       ability_randomization_statues=True)
    graph = room_traversal_graph("peg_149_35_18", "hub_statues", True)
    state = CollectionState(world.multiworld)
    for name in {item for route in graph.routes for item in route.items} | {"Smash Ability"}:
        state.collect(world.create_item(name), prevent_sweep=True)
    target = world.multiworld.get_location(data.locations["MINOR_CHEST_MOONLIGHT_MANSION_2_20"].label, 1)
    with patch.object(state, "can_reach_region", return_value=False):
        assert not target.access_rule(state)
    with patch.object(state, "can_reach_region", return_value=True):
        assert target.access_rule(state)
        state.remove(world.create_item("Smash Ability"))
        assert not target.access_rule(state)


@pytest.mark.parametrize('first_valid_attempt', [1122, 1782])
def test_default_joint_search_preserves_stream_beyond_old_budget(monkeypatch, first_valid_attempt):
    from copy import deepcopy
    import random
    from types import SimpleNamespace
    from .. import peg_traversal, traversal_rules, wheel_traversal

    rng = random.Random(1032)
    candidates = [{'mode': 1, 'seed': rng.getrandbits(32), 'ordinal': n}
                  for n in range(first_valid_attempt + 1)]
    original = deepcopy(candidates)
    policy_inputs = []
    wheel_checks = []
    extra_checks = []
    draws = []

    def policy(candidate, include_statues):
        assert include_statues is False
        policy_inputs.append(candidate)
        return SimpleNamespace(mode=1, candidate=candidate)

    def factory():
        draws.append(len(draws) + 1)
        return candidates[draws[-1]]

    def wheel_witness(policy):
        wheel_checks.append(policy.candidate['ordinal'])
        return policy.candidate['ordinal'] >= 1024

    def extra_witness(policy):
        extra_checks.append(policy.candidate['ordinal'])
        return policy.candidate['ordinal'] >= first_valid_attempt - 1

    monkeypatch.setattr(peg_traversal, 'SourcePolicy', policy)
    monkeypatch.setattr(wheel_traversal, 'static_wheel_witness', wheel_witness)
    monkeypatch.setattr(peg_traversal, '_assignment_has_witness', lambda row, policy: True)
    monkeypatch.setattr(traversal_rules, 'static_extra_witness', extra_witness)
    selected = peg_traversal.validate_peg_assignment(candidates[0], factory, False)
    assert selected is candidates[first_valid_attempt - 1]
    assert draws == list(range(1, first_valid_attempt))
    assert wheel_checks == list(range(first_valid_attempt))
    assert extra_checks == list(range(1024, first_valid_attempt))
    assert all(actual is expected for actual, expected in zip(policy_inputs, candidates))
    assert len(policy_inputs) == first_valid_attempt
    assert candidates == original
