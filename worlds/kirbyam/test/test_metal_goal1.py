"""Bounded native557 source/move witness; other assignments remain unvalidated."""

import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from BaseClasses import CollectionState
from Options import Accessibility

from .. import traversal_rules as rules
from ..data import data
from ..traversal import METAL_BREAKING_ABILITIES, Position, SourcePolicy
from ..traversal_data import room_traversal_graph, room_traversal_targets
from .test_mini_traversal import make_world
from .test_traversal import policy


TARGET = "metal_557_goal1_tomato"
LOCATION = "MINOR_CHEST_RAINBOW_ROUTE_1_GOAL_1_OBJECT_01"
OWNER = "REGION_RAINBOW_ROUTE/ROOM_1_GOAL_1"


def target_row() -> dict[str, Any]:
    return next(row for row in room_traversal_targets("metal") if row["id"] == TARGET)


@pytest.mark.parametrize("mode,minibosses,pool,weight,applies", [
    (0, True, None, 0, True),
    (1, False, ["Burning"], 0, True),
    (2, False, ["Burning"], 100, True),
    (1, True, ["Smash"], 0, True),
    (1, True, ["Burning"], 0, False),
    (2, True, ["Smash"], 0, True),
    (2, True, ["Smash", "Burning"], 0, False),
    (2, True, ["Smash"], 50, False),
    (2, True, ["Smash"], 100, False),
])
@pytest.mark.parametrize("gating", [False, True])
@pytest.mark.parametrize("enabled", [False, True])
@pytest.mark.parametrize("minimal", [False, True])
def test_partial_source_binding_matrix(
    monkeypatch: pytest.MonkeyPatch, mode: int, minibosses: bool, pool: list[str] | None,
    weight: int, applies: bool, gating: bool, enabled: bool, minimal: bool,
) -> None:
    resolver = policy(mode, minibosses=minibosses, pool=pool, weight=weight)  # type: ignore[no-untyped-call]
    row = target_row()
    monkeypatch.setattr(rules, "extra_traversal_targets", lambda: (row,))
    assert rules.target_applies(row, resolver) is applies
    assert rules.static_extra_witness(resolver)

    def original_rule(state: Any) -> bool:
        return bool(state.base_rule)

    target = SimpleNamespace(access_rule=original_rule)

    def get_location(name: str, player: int) -> Any:
        assert name == data.locations[LOCATION].label and player == 1
        if not enabled:
            raise KeyError("Disabled minor chests")
        return target

    world = SimpleNamespace(
        player=1, _enemy_copy_ability_policy=resolver.policy,
        _ability_gating_enabled=lambda: gating, _area_keys_enabled=lambda: False,
        options=SimpleNamespace(
            ability_randomization_statues=SimpleNamespace(value=False),
            accessibility=Accessibility(Accessibility.option_minimal if minimal else Accessibility.option_full),
        ), multiworld=SimpleNamespace(get_location=get_location),
    )
    rules.install_extra_traversal_rules(world)
    if not applies or not enabled:
        assert target.access_rule is original_rule  # Unreviewed is not synonymous with impossible or proven.
    owned: set[str] = set()
    state = SimpleNamespace(base_rule=True, has=lambda item, player: item in owned)
    assert target.access_rule(state) is (not (applies and enabled and gating))
    owned.add("Smash Ability")
    assert target.access_rule(state)
    state.base_rule = False
    assert not target.access_rule(state)


def test_local_witness_has_no_equipment_start_retry_or_persistent_opening() -> None:
    graph = room_traversal_graph(TARGET, "local")
    assert len(graph.nodes) == 4 and len(graph.routes) == 3 and len(graph.placements) == 1
    assert {node.room for node in graph.nodes} == {557}
    assert graph.starts == (Position(TARGET + ":entry"),)
    assert graph.required_targets == {TARGET + ":chest"}
    source, = graph.placements
    assert source.source_key == "MASTER_HAND" and source.identity == "0x088B9358"
    assert source.node == TARGET + ":arena"
    assert not source.renewable and not source.retry_evidence
    assert all(route.opens is None and not route.room_transition for route in graph.routes)
    attack, = [route for route in graph.routes if route.capability]
    assert attack.capability == "metal" and attack.allowed_abilities == frozenset({"Smash"})
    assert attack.water_state == "dry" and attack.uses_object is None
    assert not graph.evaluate(SourcePolicy({"mode": 0}), frozenset(), True).reaches(TARGET + ":chest")
    assert graph.evaluate(SourcePolicy({"mode": 0}), frozenset({"Smash Ability"}), True).reaches(TARGET + ":chest")


def test_source_behind_metal_or_inaccessible_arena_cannot_bootstrap_chest() -> None:
    graph = room_traversal_graph(TARGET, "local")
    owned = frozenset({"Smash Ability"})
    resolver = SourcePolicy({"mode": 0})
    no_source = replace(graph, placements=())
    assert not no_source.evaluate(resolver, owned, True).reaches(TARGET + ":chest")
    misplaced = replace(graph, placements=(replace(graph.placements[0], node=TARGET + ":chest"),))
    assert not misplaced.evaluate(resolver, owned, True).reaches(TARGET + ":chest")
    disconnected = replace(graph, routes=graph.routes[1:])
    assert not disconnected.evaluate(resolver, owned, True).reaches(TARGET + ":chest")
    wrong_entry = replace(graph, starts=(Position(TARGET + ":launch"),))
    assert not wrong_entry.evaluate(resolver, owned, True).reaches(TARGET + ":chest")


@pytest.mark.parametrize("gating", [0, 1])
def test_real_world_rule_is_local_to_chest_not_goal_door(gating: int) -> None:
    world = make_world(0, gating)  # type: ignore[no-untyped-call]
    state = CollectionState(world.multiworld)
    target = world.multiworld.get_location(data.locations[LOCATION].label, 1)
    assert target.access_rule(state) is (not gating)
    state.collect(world.create_item("Smash Ability"), prevent_sweep=True)
    assert target.access_rule(state)
    assert not target.can_reach(state)  # This witness never grants entry to the room.
    exit_ = world.multiworld.get_entrance(OWNER + " -> REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE", 1)
    assert exit_.access_rule(CollectionState(world.multiworld))


def test_acceptance_record_keeps_source_and_isolated_ap_collection_separate() -> None:
    path = Path(__file__).parents[1] / "dev-docs/ordinary-557-smash-acceptance.json"
    evidence = json.loads(path.read_text())
    assert evidence["target"] == LOCATION and evidence["room"] == 557
    assert "not a combined Master Hand acquisition replay" in evidence["evidence_level"]
    source = evidence["native_source_contract"]
    assert source["object_template_rom_offset"] == "0x8B9358" and source["ability_table_u16"] == 22
    assert evidence["entry_approach"]["native_transition"]["source_room"] == 556
    isolated = evidence["isolated_smash_to_chest"]
    assert "synthetic essence" in isolated["fixture_changes"][-1]
    assert isolated["run"]["writes"] == []
    chest = isolated["observations"][-1]
    assert chest["native_flag"] == 6 and chest["event_counter"] == 1
    assert chest["event_ring_first"] == "0x088B9280"
    assert isolated["observations"][-2]["remaining_tile"] == [10, 18]


@pytest.mark.parametrize("ability", sorted(METAL_BREAKING_ABILITIES))
def test_this_launch_only_admits_its_reviewed_smash_move(ability: str) -> None:
    graph = room_traversal_graph(TARGET, "local")
    isolated = replace(graph, placements=(), starts=(Position(TARGET + ":launch", ability),))
    result = isolated.evaluate(SourcePolicy({"mode": 0}), frozenset(), True)
    assert result.reaches(TARGET + ":chest") is (ability == "Smash")
    swimming = replace(isolated, routes=tuple(
        replace(route, water_state="swimming") if route.capability else route for route in isolated.routes))
    assert not swimming.evaluate(SourcePolicy({"mode": 0}), frozenset(), True).reaches(TARGET + ":chest")


def test_chest_side_does_not_create_an_unreviewed_reverse_route() -> None:
    graph = room_traversal_graph(TARGET, "local")
    reverse = replace(graph, starts=(Position(TARGET + ":chest"),))
    result = reverse.evaluate(SourcePolicy({"mode": 0}), frozenset(), True)
    assert not result.reaches(TARGET + ":arena")
    assert not result.reaches(TARGET + ":entry")


def test_smash_unlock_in_its_own_chest_cannot_collect_itself() -> None:
    world = make_world(0, 1)  # type: ignore[no-untyped-call]
    multiworld = world.multiworld
    target = multiworld.get_location(data.locations[LOCATION].label, 1)
    target.place_locked_item(world.create_item("Smash Ability"))
    # Isolate the local check from unrelated world-entry requirements. Actual
    # source policy and installed chest access rule are unchanged.
    multiworld.get_region("Menu", 1).connect(multiworld.get_region(OWNER, 1))
    state = CollectionState(multiworld)
    assert state.can_reach_region(OWNER, 1)
    assert not state.has("Smash Ability", 1)
    state.sweep_for_advancements(locations=[target])
    assert not state.has("Smash Ability", 1)
    assert not target.can_reach(state)
    assert target not in state.advancements
    state.collect(world.create_item("Smash Ability"), prevent_sweep=True)
    assert target.can_reach(state)
    state.sweep_for_advancements(locations=[target])
    assert target in state.advancements
