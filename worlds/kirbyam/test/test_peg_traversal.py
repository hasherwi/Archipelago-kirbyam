"""Reviewed local peg witnesses and full native census coverage."""

import pytest
from BaseClasses import CollectionState

from ..data import data, load_json_data
from ..peg_traversal import PEG_ROUTES, peg_graph
from ..traversal import SourcePolicy
from .test_mini_traversal import make_world


def test_census_covers_all_fourteen_pegs_without_blanket_room_gates():
    rows = load_json_data("peg_traversal_audit.json")["pegs"]
    assert len(rows) == len({row["id"] for row in rows}) == 14
    assert len({row["native_room"] for row in rows}) == 13
    assert {row["native_room"] for row in rows} == {
        149, 204, 218, 221, 401, 411, 509, 510, 513, 527, 605, 741, 816,
    }
    assert len([row for row in rows if row["native_room"] == 527]) == 2


@pytest.mark.parametrize("mode", [0, 1])
@pytest.mark.parametrize("gating", [False, True])
def test_real_peg_rules_use_same_local_assignment_as_rom(mode, gating):
    world = make_world(mode, gating)
    resolver = SourcePolicy(world._enemy_copy_ability_policy)
    state = CollectionState(world.multiworld)
    for row in PEG_ROUTES:
        if not row["sources"]:
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
    policy_data = dict(make_world(mode, False)._enemy_copy_ability_policy)
    policy_data["ability_randomization_no_ability_weight"] = 100
    policy = SourcePolicy(policy_data, include_statues=False)
    for row in PEG_ROUTES:
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
    raw = dict(make_world(2, True)._enemy_copy_ability_policy)
    raw["ability_randomization_no_ability_weight"] = 100
    policy = SourcePolicy(raw, include_statues=True)
    graph = stone_carry_graph(next(row for row in PEG_ROUTES if row["room"] == 411), False)
    items = frozenset(item for route in graph.routes for item in route.items)
    assert not graph.evaluate(policy, items, True).reaches("target")
    result = graph.evaluate(policy, items, True, allow_documented_retries=True)
    assert result.reaches("target")
    assert result.retry_assumptions


def test_gate_side_reach_does_not_bootstrap_remote_statue():
    from unittest.mock import patch
    from ..peg_traversal import stone_carry_graph
    world = make_world(0, True)
    row = next(row for row in PEG_ROUTES if row["room"] == 411)  # 411 has no local source.
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


def test_assignment_budget_exhaustion_is_diagnostic_not_impossibility(monkeypatch, caplog):
    from .. import peg_traversal, wheel_traversal
    monkeypatch.setattr(wheel_traversal, "static_wheel_witness", lambda *args: True)
    initial = {"mode": 1}
    calls = []
    monkeypatch.setattr(peg_traversal, "SourcePolicy", lambda *args: type("Policy", (), {"mode": 1})())
    monkeypatch.setattr(peg_traversal, "_assignment_has_witness", lambda *args: False)
    result = peg_traversal.validate_peg_assignment(initial, lambda: calls.append(1) or initial, False, 3)
    assert result is initial and len(calls) == 2
    assert "not a proof" in caplog.text


def test_unvalidated_wheel_seed_fails_when_search_budget_exhausted(monkeypatch):
    from .. import peg_traversal, wheel_traversal
    monkeypatch.setattr(wheel_traversal, "static_wheel_witness", lambda *args: False)
    monkeypatch.setattr(peg_traversal, "SourcePolicy", lambda *args: type("Policy", (), {"mode": 1})())
    initial = {"mode": 1, "seed": 123}
    with pytest.raises(ValueError, match="Wheel-source search budget exhausted after 3 attempts"):
        peg_traversal.validate_peg_assignment(initial, lambda: initial, False, 3)
