"""Source-backed installer contracts independent of any particular room path."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from .. import traversal_rules as rules
from ..traversal import Node, Placement, Position, Route, SourcePolicy, TraversalGraph


@pytest.fixture
def graph():
    return TraversalGraph(
        (Node("source", 126), Node("done", 126)),
        (Route("source", "done", "fuse"),),
        (Placement("source", "HOT_HEAD", requirements=frozenset({"Source access item"})),),
        (Position("source"),), frozenset({"done"}), access_region="Independent source",
    )


@pytest.fixture
def setup(monkeypatch, graph):
    target = SimpleNamespace(access_rule=lambda state: state.base_rule)
    dependencies = []
    world = SimpleNamespace(
        player=1, _enemy_copy_ability_policy={"mode": 0},
        _ability_gating_enabled=lambda: True, _area_keys_enabled=lambda: True,
        options=SimpleNamespace(ability_randomization_statues=SimpleNamespace(value=False)),
        multiworld=SimpleNamespace(
            get_entrance=lambda name, player: target,
            get_region=lambda name, player: name,
            register_indirect_condition=lambda region, entrance: dependencies.append((region, entrance)),
        ),
    )
    row = {"id": "test-fuse", "kind": "fuse", "region": "Owner", "exit": "Exit", "graphs": {"local": {}}}
    monkeypatch.setattr(rules, "extra_traversal_targets", lambda: (row,))
    monkeypatch.setattr(rules, "target_graphs", lambda row, area_keys, **kwargs: (graph,))
    items = set()
    state = SimpleNamespace(base_rule=True, accessible=False)
    state.has = lambda item, player: item in items
    state.can_reach_region = lambda region, player: state.accessible
    return world, target, state, items, dependencies, row


def test_installer_requires_source_item_permission_and_independent_access(setup):
    world, target, state, items, dependencies, _ = setup
    rules.install_extra_traversal_rules(world)
    assert not target.access_rule(state)
    items.add("Fire Ability")
    assert not target.access_rule(state)
    items.add("Source access item")
    assert not target.access_rule(state)
    state.accessible = True
    assert target.access_rule(state)
    items.remove("Source access item")
    assert not target.access_rule(state)
    assert dependencies == [("Independent source", target)]


def test_installer_preserves_existing_rule(setup):
    world, target, state, items, _, _ = setup
    rules.install_extra_traversal_rules(world)
    state.accessible = True
    items.update({"Fire Ability", "Source access item"})
    assert target.access_rule(state)
    state.base_rule = False
    assert not target.access_rule(state)


def test_graph_uses_all_required_targets_not_one_magic_name(graph):
    graph = replace(graph, nodes=graph.nodes + (Node("other", 126),), required_targets=frozenset({"done", "other"}))
    owned = frozenset({"Source access item", "Fire Ability"})
    assert not rules.graph_succeeds(graph, SourcePolicy({"mode": 0}), owned, True, retries=False)
    graph = replace(graph, routes=graph.routes + (Route("done", "other"),))
    assert rules.graph_succeeds(graph, SourcePolicy({"mode": 0}), owned, True, retries=False)


def test_multiple_incomplete_witnesses_do_not_merge(monkeypatch, setup, graph):
    world, _, _, _, _, _ = setup
    nodes = graph.nodes + (Node("other", 126),)
    first = replace(graph, nodes=nodes, required_targets=frozenset({"done", "other"}))
    second = replace(first, routes=(Route("source", "other", "fuse"),))
    monkeypatch.setattr(rules, "target_graphs", lambda row, area_keys, **kwargs: (first, second))
    assert not rules.static_extra_witness(SourcePolicy({"mode": 0}))
    with pytest.raises(ValueError, match="No reviewed source witness"):
        rules.install_extra_traversal_rules(world)


def test_optional_route_fails_closed_without_rejecting_world(monkeypatch, setup, graph):
    world, target, state, items, _, row = setup
    row["required_for_generation"] = False
    monkeypatch.setattr(rules, "target_graphs", lambda row, area_keys, **kwargs: (replace(graph, placements=()),))
    assert rules.static_extra_witness(SourcePolicy({"mode": 0}))
    rules.install_extra_traversal_rules(world)
    items.update({"Fire Ability", "Source access item"})
    state.accessible = True
    assert not target.access_rule(state)


def test_area_key_option_is_passed_to_graph_compiler(monkeypatch, setup, graph):
    world, _, _, _, _, _ = setup
    received = []
    monkeypatch.setattr(rules, "target_graphs", lambda row, area_keys, **kwargs: received.append(area_keys) or (graph,))
    rules.install_extra_traversal_rules(world)
    world._area_keys_enabled = lambda: False
    rules.install_extra_traversal_rules(world)
    assert received == [True, False]


def test_disabled_optional_location_does_not_install_or_validate(monkeypatch, setup):
    world, _, _, _, _, row = setup
    row.pop("exit")
    row["location"] = "LOCATION_TEST"
    monkeypatch.setattr(rules.data, "locations", {"LOCATION_TEST": SimpleNamespace(label="Test location")})

    def missing(*args):
        raise KeyError("disabled")

    world.multiworld.get_location = missing
    monkeypatch.setattr(rules, "target_graphs", lambda *args: pytest.fail("Disabled location evaluated"))
    rules.install_extra_traversal_rules(world)


def test_location_rule_uses_same_source_requirements(monkeypatch, setup):
    world, target, state, items, dependencies, row = setup
    row.pop("exit")
    row["location"] = "LOCATION_TEST"
    monkeypatch.setattr(rules.data, "locations", {"LOCATION_TEST": SimpleNamespace(label="Test location")})
    world.multiworld.get_location = lambda name, player: target
    rules.install_extra_traversal_rules(world)
    items.update({"Fire Ability", "Source access item"})
    state.accessible = True
    assert target.access_rule(state)
    items.remove("Fire Ability")
    assert not target.access_rule(state)
    assert not dependencies


def test_complete_alternatives_on_one_target_are_or_not_separate_and_rules(monkeypatch, setup, graph):
    # Synthetic second source validates composition only, not a Phone or room witness.
    world, target, state, items, _, _ = setup
    alternative = replace(graph, placements=(Placement('source', 'FOLEY'),))
    monkeypatch.setattr(rules, 'target_graphs', lambda row, area_keys, **kwargs: (graph, alternative))
    rules.install_extra_traversal_rules(world)
    state.accessible = True
    items.add('Bomb Ability')
    assert target.access_rule(state)  # No Fire or first source-access item required.
    items.clear()
    items.update({'Fire Ability', 'Source access item'})
    assert target.access_rule(state)  # No Bomb required for the other complete graph.
    items.clear()
    assert not target.access_rule(state)
