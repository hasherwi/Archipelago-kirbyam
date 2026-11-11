"""Batafire source, defeat boundary and the isolated native176 Burning move."""

import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from BaseClasses import CollectionState, ItemClassification

from .. import traversal, traversal_rules as rules
from ..data import data
from ..enemy_ability_data import GATEABLE_ENEMY_COPY_ABILITIES
from ..traversal import METAL_BREAKING_ABILITIES, Position, SourcePolicy
from ..traversal_data import room_traversal_graph, room_traversal_targets
from .test_mini_traversal import make_world
from .test_traversal import policy


TARGET = "metal_176_goal2_drink"
LOCATION = "MINOR_CHEST_RAINBOW_ROUTE_1_GOAL_2_OBJECT_01"
OWNER = "REGION_RAINBOW_ROUTE/ROOM_1_GOAL_2"


def simulate_burning_gating(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the later permission contract without changing production options."""
    gateable = tuple(sorted(set(GATEABLE_ENEMY_COPY_ABILITIES) | {"Burning"}))
    monkeypatch.setattr(traversal, "GATEABLE_ENEMY_COPY_ABILITIES", gateable)
    monkeypatch.setattr(rules, "GATEABLE_ENEMY_COPY_ABILITIES", gateable)


@pytest.mark.parametrize("mode,minibosses,pool,weight,applies", [
    (0, True, None, 0, True),
    (1, False, ["Smash"], 0, True),
    (2, False, ["Smash"], 100, True),
    (1, True, ["Burning"], 0, True),
    (1, True, ["Smash"], 0, False),
    (2, True, ["Burning"], 0, True),
    (2, True, ["Burning", "Smash"], 0, False),
    (2, True, ["Burning"], 50, False),
    (2, True, ["Burning"], 100, False),
])
@pytest.mark.parametrize("simulate_future_gate", [False, True])
def test_batafire_policy_and_permission_binding(
    monkeypatch: pytest.MonkeyPatch, mode: int, minibosses: bool, pool: list[str] | None,
    weight: int, applies: bool, simulate_future_gate: bool,
) -> None:
    if simulate_future_gate:
        simulate_burning_gating(monkeypatch)
    resolver = policy(mode, minibosses=minibosses, pool=pool, weight=weight)
    row = next(row for row in room_traversal_targets("metal") if row["id"] == TARGET)
    assert rules.target_applies(row, resolver)  # All assignments now require a reviewed OR witness.
    monkeypatch.setattr(rules, "extra_traversal_targets", lambda: (row,))
    assert rules.static_extra_witness(resolver)

    def original(state: Any) -> bool:
        return bool(state.base_rule)

    target = SimpleNamespace(access_rule=original)
    world = SimpleNamespace(
        player=1, _enemy_copy_ability_policy=resolver.policy,
        _ability_gating_enabled=lambda: True, _area_keys_enabled=lambda: False,
        options=SimpleNamespace(ability_randomization_statues=SimpleNamespace(value=False)),
        multiworld=SimpleNamespace(get_location=lambda name, player: target),
    )
    rules.install_extra_traversal_rules(world)
    owned: set[str] = set()
    state = SimpleNamespace(base_rule=True, has=lambda item, player: item in owned,
                            can_reach_region=lambda region, player: False)
    assert not target.access_rule(state)  # Burning permission is now gated in production.
    owned.add("Burning Ability")
    assert target.access_rule(state) is ("Burning" in resolver.grant(
        "BATAFIRE", lambda ability: ability == "Burning").guaranteed)
    owned.add("Smash Ability")
    assert target.access_rule(state) is applies  # Mixed finite outcomes remain uncertain.
    state.base_rule = False
    assert not target.access_rule(state)


def test_source_and_defeat_approach_cannot_be_skipped(monkeypatch: pytest.MonkeyPatch) -> None:
    simulate_burning_gating(monkeypatch)
    graph = room_traversal_graph(TARGET, "local")
    resolver = SourcePolicy({"mode": 0})
    owned = frozenset({"Burning Ability"})
    assert graph.starts == (Position(TARGET + ":entry"),)
    assert len(graph.nodes) == 4 and len(graph.routes) == 3
    source, = graph.placements
    assert source.node == TARGET + ":defeated_arena"
    assert source.source_key == "BATAFIRE" and source.identity == "0x088BAE50"
    assert not source.renewable and not source.retry_evidence
    assert all(not edge.room_transition and edge.opens is None for edge in graph.routes)
    assert not graph.evaluate(resolver, frozenset(), True).reaches(TARGET + ":chest")
    assert graph.evaluate(resolver, owned, True).reaches(TARGET + ":chest")
    for blocked in (
        replace(graph, placements=()),
        replace(graph, placements=(replace(source, node=TARGET + ":chest"),)),
        replace(graph, routes=graph.routes[1:]),
        replace(graph, starts=(Position(TARGET + ":launch"),)),
    ):
        assert not blocked.evaluate(resolver, owned, True).reaches(TARGET + ":chest")


@pytest.mark.parametrize("ability", sorted(METAL_BREAKING_ABILITIES))
def test_only_reviewed_dry_burning_sequence(ability: str) -> None:
    graph = room_traversal_graph(TARGET, "local")
    isolated = replace(graph, placements=(), starts=(Position(TARGET + ":launch", ability),))
    resolver = SourcePolicy({"mode": 0})
    assert isolated.evaluate(resolver, frozenset(), True).reaches(TARGET + ":chest") is (ability == "Burning")
    swimming = replace(isolated, routes=tuple(
        replace(edge, water_state="swimming") if edge.capability else edge for edge in isolated.routes))
    assert not swimming.evaluate(resolver, frozenset(), True).reaches(TARGET + ":chest")
    reverse = replace(graph, starts=(Position(TARGET + ":chest"),))
    assert not reverse.evaluate(resolver, frozenset(), True).reaches(TARGET + ":defeated_arena")


def test_simulated_future_burning_unlock_cannot_unlock_its_own_chest(monkeypatch: pytest.MonkeyPatch) -> None:
    simulate_burning_gating(monkeypatch)
    world = make_world(0, 1)
    multiworld = world.multiworld
    target = multiworld.get_location(data.locations[LOCATION].label, 1)
    item = world.create_item("Burning Ability")
    assert item.classification == ItemClassification.progression
    target.place_locked_item(item)
    multiworld.get_region("Menu", 1).connect(multiworld.get_region(OWNER, 1))
    state = CollectionState(multiworld)
    while state.has("Burning Ability", 1):
        state.remove(world.create_item("Burning Ability"))
    assert state.can_reach_region(OWNER, 1)
    state.sweep_for_advancements(locations=[target])
    assert not state.has("Burning Ability", 1) and not target.can_reach(state)
    assert target not in state.advancements
    exit_ = multiworld.get_entrance(OWNER + " -> REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE", 1)
    assert exit_.access_rule(state)
    state.collect(world.create_item("Burning Ability"), prevent_sweep=True)
    assert target.can_reach(state)
    state.sweep_for_advancements(locations=[target])
    assert target in state.advancements


def test_acceptance_discloses_post_defeat_boundary_substitute() -> None:
    path = Path(__file__).parents[1] / "dev-docs/ordinary-176-burning-acceptance.json"
    record = json.loads(path.read_text())
    assert record["target"] == LOCATION and record["room"] == 176
    assert "NOT a combined actual Batafire defeat/acquisition replay" in record["evidence_level"]
    assert record["entry_approach"]["transition"]["source_room"] == 175
    assert all(run["writes"] == [] for run in record["entry_approach"]["runs"])
    source = record["native_source_contract"]
    assert source["ability_table_rom_offset"] == "0x351BD6" and source["ability_table_u16"] == 3
    boundary = record["arena_release_contract"]
    assert boundary["shared_room_state_slot"] == 1 and boundary["native_unk22"] == 2
    fields = source["native_template_fields"]
    assert fields == {"unk2": 0, "unk3": 6, "unk4": 1}
    assert fields["unk2"] or fields["unk3"] != 31
    assert fields["unk4"] == boundary["native_template_fields"]["unk4"] == 1
    assert "clamped atx248" in boundary["negative_control"]
    isolated = record["isolated_post_defeat_burning_to_chest"]
    assert "not a tested defeat event" in isolated["fixture_changes"][-1]
    assert isolated["run"]["writes"] == []
    assert isolated["observations"][-2]["metal_remaining"] == 0
    chest = isolated["observations"][-1]
    assert chest["native_flag"] == 9 and chest["event_counter"] == 1
    assert chest["event_ring_first"] == "0x088BAEE0"
