"""Finite Bonkers carrier and conservative native205/209/210 check compartments."""

from dataclasses import replace
from types import SimpleNamespace
from typing import Any

import pytest
from BaseClasses import CollectionState

from .. import traversal_rules as rules
from ..data import data, load_json_data
from ..traversal import METAL_BREAKING_ABILITIES, Position, SourcePolicy
from ..traversal_data import room_traversal_graph, room_traversal_targets
from .test_mini_traversal import make_world
from .test_traversal import policy


PREFIX = "REGION_PEPPERMINT_PALACE/"
OUTER, TOP, MAIN, ENTRY, HUB = (PREFIX + key for key in (
    "ROOM_7_07", "ROOM_7_CHEST", "ROOM_7_05", "ROOM_7_03", "ROOM_7_HUB_1"))
WATER = OUTER + "__LOGIC__WATER_RETURN"
UPPER, LOWER, BOTTOM = (TOP + "__LOGIC__" + key for key in ("UPPER_ENTRY", "LOWER_MAP", "BOTTOM_MINOR"))
SNOW = MAIN + "__LOGIC__SNOW_HALL"
CHECKS = {parent + "__ROOM_CHECK" for parent in (OUTER, TOP, MAIN)}
SIDES = {OUTER, TOP, MAIN, WATER, UPPER, LOWER, BOTTOM, SNOW} | CHECKS
TARGET = "metal_205_to_209_top"
MINOR23 = "MINOR_CHEST_PEPPERMINT_PALACE_7_CHEST_OBJECT_01"
MINOR24 = "MINOR_CHEST_PEPPERMINT_PALACE_7_CHEST_OBJECT_02"


def metal_row() -> dict[str, Any]:
    return next(row for row in room_traversal_targets("metal") if row["id"] == TARGET)


@pytest.mark.parametrize("mode,minibosses,pool,weight,applies", [
    (0, True, None, 0, True), (1, False, ["Burning"], 0, True), (2, False, ["Burning"], 100, True),
    (1, True, ["Hammer"], 0, True), (1, True, ["Burning"], 0, False),
    (2, True, ["Hammer"], 0, True), (2, True, ["Hammer", "Burning"], 0, False),
    (2, True, ["Hammer"], 50, False), (2, True, ["Hammer"], 100, False),
])
def test_fail_closed_finite_bonkers_policy_permission_and_independent_entry(
    monkeypatch: pytest.MonkeyPatch, mode: int, minibosses: bool, pool: list[str] | None,
    weight: int, applies: bool,
) -> None:
    resolver = policy(mode, minibosses=minibosses, pool=pool, weight=weight)  # type: ignore[no-untyped-call]
    # Isolate the finite branch: a separately reviewed renewable statue path
    # must not be mistaken for a guarantee from a mixed Bonkers outcome.
    row = dict(metal_row())
    row["graphs"] = {"bonkers_carry": row["graphs"]["bonkers_carry"]}
    assert rules.target_applies(row, resolver)
    assert "requires_guaranteed_source" not in row
    monkeypatch.setattr(rules, "extra_traversal_targets", lambda: (row,))
    assert rules.static_extra_witness(resolver) is applies

    def original(state: Any) -> bool:
        return bool(state.base_rule)

    target = SimpleNamespace(access_rule=original)
    indirect: list[str] = []
    world = SimpleNamespace(
        player=1, _enemy_copy_ability_policy=resolver.policy,
        _ability_gating_enabled=lambda: True, _area_keys_enabled=lambda: False,
        options=SimpleNamespace(ability_randomization_statues=SimpleNamespace(value=False)),
        multiworld=SimpleNamespace(
            get_entrance=lambda name, player: target, get_region=lambda name, player: name,
            register_indirect_condition=lambda region, entrance: indirect.append(region)),
    )
    if not applies:
        with pytest.raises(ValueError, match="No reviewed source witness for metal_205_to_209_top"):
            rules.install_extra_traversal_rules(world)
        return
    rules.install_extra_traversal_rules(world)
    owned: set[str] = set()
    access = {OUTER}
    state = SimpleNamespace(base_rule=True, has=lambda item, player: item in owned,
                            can_reach_region=lambda name, player: name in access)
    assert target.access_rule(state) is (not applies)
    owned.add("Hammer Ability")
    assert target.access_rule(state)
    access.clear()
    assert target.access_rule(state) is (not applies)
    assert indirect == ([OUTER] if applies else [])
    state.base_rule = False
    assert not target.access_rule(state)


def test_hammer_uses_actual_finite_source_before_floor_and_preserves_carrier() -> None:
    graph = room_traversal_graph(TARGET, "bonkers_carry")
    resolver = SourcePolicy({"mode": 0})
    owned = frozenset({"Hammer Ability"})
    source, = graph.placements
    assert source.identity == "0x088BF730" and source.source_key == "BONKERS"
    assert source.node == "metal_205:defeated_bonkers_arena"
    assert not source.renewable and not source.retry_evidence
    assert graph.access_region == OUTER
    assert graph.starts == (Position("metal_205:outer"),)
    assert len(graph.nodes) == 6 and len(graph.routes) == 5
    assert not graph.evaluate(resolver, frozenset(), True).reaches("metal_205:209_top")
    result = graph.evaluate(resolver, owned, True)
    assert result.reaches("metal_205:209_top")
    assert any(p.node == "metal_205:209_top" and p.equipped == "Hammer" for p in result.positions)
    assert all(edge.opens is None for edge in graph.routes)
    assert not any(edge.source == "metal_205:209_top" for edge in graph.routes)
    for blocked in (replace(graph, placements=()),
                    replace(graph, placements=(replace(source, node="metal_205:209_top"),)),
                    replace(graph, starts=(Position("metal_205:floor_launch"),))):
        assert not blocked.evaluate(resolver, owned, True).reaches("metal_205:209_top")
    assert not replace(graph, starts=(Position("metal_205:209_top", "Hammer"),)).evaluate(
        resolver, owned, True).reaches("metal_205:outer")


@pytest.mark.parametrize("ability", sorted(METAL_BREAKING_ABILITIES | {"Normal"}))
def test_low_floor_move_admits_only_reviewed_hammer_and_is_explicitly_dry(ability: str) -> None:
    graph = room_traversal_graph(TARGET, "bonkers_carry")
    isolated = replace(graph, placements=(), starts=(Position("metal_205:floor_launch", ability),))
    resolver = SourcePolicy({"mode": 0})
    assert isolated.evaluate(resolver, frozenset(), True).reaches("metal_205:209_top") is (ability == "Hammer")
    metal, = (edge for edge in graph.routes if edge.capability)
    assert metal.capability == "metal" and metal.allowed_abilities == frozenset({"Hammer"})
    assert not metal.room_transition
    assert metal.water_state == "dry"


@pytest.mark.parametrize("identity,witness,access,endpoint,nodes", [
    ("normal_210_to_209_upper", "205_arena_approach", OUTER, "normal_210:209_upper", 4),
    ("normal_208_to_209_bottom", "hub290_approach", HUB, "normal_208:bottom209", 3),
])
def test_normal_entries_require_real_prefix_access_without_copy_or_mutation_credit(
    monkeypatch: pytest.MonkeyPatch, identity: str, witness: str, access: str, endpoint: str, nodes: int,
) -> None:
    graph = room_traversal_graph(identity, witness)
    assert graph.access_region == access and len(graph.nodes) == nodes
    assert not graph.placements
    assert all(not edge.capability and edge.opens is None for edge in graph.routes)
    assert graph.evaluate(SourcePolicy({"mode": 0}), frozenset(), True).reaches(endpoint)
    row = next(row for row in room_traversal_targets("block") if row["id"] == identity)
    assert "requires_guaranteed_source" not in row
    monkeypatch.setattr(rules, "extra_traversal_targets", lambda: (row,))
    target = SimpleNamespace(access_rule=lambda state: True)
    indirect: list[str] = []
    world = SimpleNamespace(
        player=1, _enemy_copy_ability_policy={"mode": 0}, _ability_gating_enabled=lambda: True,
        _area_keys_enabled=lambda: False,
        options=SimpleNamespace(ability_randomization_statues=SimpleNamespace(value=False)),
        multiworld=SimpleNamespace(get_entrance=lambda name, player: target, get_region=lambda name, player: name,
                                   register_indirect_condition=lambda name, entrance: indirect.append(name)))
    rules.install_extra_traversal_rules(world)
    accessible: set[str] = set()
    state = SimpleNamespace(has=lambda item, player: False,
                            can_reach_region=lambda name, player: name in accessible)
    assert not target.access_rule(state)
    accessible.add(access)
    assert target.access_rule(state) and indirect == [access]


def test_normal_boss_door_reuses_geometry_without_acquiring_unused_fixture_hammer() -> None:
    metal = room_traversal_graph(TARGET, "bonkers_carry")
    normal = room_traversal_graph("normal_210_to_209_upper", "205_arena_approach")
    assert normal.routes[-2:] == metal.routes[-2:]
    assert normal.starts == metal.starts
    assert not normal.placements


@pytest.mark.parametrize("start,reachable", [
    (TOP, {TOP, WATER, TOP + "__ROOM_CHECK", OUTER + "__ROOM_CHECK"}),
    (BOTTOM, {BOTTOM, TOP + "__ROOM_CHECK"}),
    (LOWER, {LOWER, TOP + "__ROOM_CHECK"}),
    (SNOW, {SNOW, LOWER, MAIN + "__ROOM_CHECK", TOP + "__ROOM_CHECK"}),
    (UPPER, {UPPER, SNOW, LOWER, MAIN + "__ROOM_CHECK", TOP + "__ROOM_CHECK"}),
    (WATER, {WATER, OUTER + "__ROOM_CHECK"}),
    (OUTER, {OUTER, MAIN, UPPER, SNOW, LOWER} | CHECKS),
])
def test_actual_installed_compartments_do_not_borrow_bottom_or_hallway_access(
    start: str, reachable: set[str],
) -> None:
    world = make_world(0, 1, room_sanity=1)  # type: ignore[no-untyped-call]
    mw = world.multiworld
    for name in SIDES:
        region = mw.get_region(name, 1)
        region.exits = [edge for edge in region.exits if edge.connected_region.name in SIDES]
    menu = mw.get_region("Menu", 1)
    menu.exits.clear()
    menu.connect(mw.get_region(start, 1))
    state = CollectionState(mw)
    assert not state.has("Hammer Ability", 1)
    assert {name for name in SIDES if state.can_reach_region(name, 1)} == reachable
    for sink in CHECKS:
        assert not mw.get_region(sink, 1).exits
    if start == OUTER:
        target = mw.get_location(data.locations[MINOR23].label, 1)
        target.place_locked_item(world.create_item("Hammer Ability"))
        state.sweep_for_advancements()
        assert not target.can_reach(state) and not state.has("Hammer Ability", 1)
        state.collect(world.create_item("Hammer Ability"), prevent_sweep=True)
        assert target.can_reach(state)
        assert {name for name in SIDES if state.can_reach_region(name, 1)} == reachable | {TOP, WATER}


def test_native_arrival_routing_stable_check_ownership_and_omitted_joins() -> None:
    rooms = load_json_data("regions/rooms.json")
    assert isinstance(rooms, dict)
    assert rooms[MAIN]["logical_exit_overrides"][TOP] == "UPPER_ENTRY"
    assert rooms[ENTRY]["logical_exit_overrides"][TOP] == "BOTTOM_MINOR"
    assert UPPER in data.regions[MAIN].exits and TOP not in data.regions[MAIN].exits
    assert BOTTOM in data.regions[ENTRY].exits and TOP not in data.regions[ENTRY].exits
    expected = {MINOR23: (TOP, 3960587), MINOR24: (BOTTOM, 3960588),
                "MAJOR_CHEST_PEPPERMINT_PALACE": (LOWER, 3960202),
                "MINOR_CHEST_SPRAY_PAINT_05": (SNOW, 3960504)}
    for location, (owner, number) in expected.items():
        assert data.locations[location].location_id == number
        assert [name for name, region in data.regions.items() if location in region.locations] == [owner]
    assert set(data.regions[SNOW].exits) == {LOWER, MAIN + "__ROOM_CHECK"}
    assert set(data.regions[TOP].exits) == {WATER, TOP + "__ROOM_CHECK"}
    for branch in (BOTTOM, LOWER):
        assert set(data.regions[branch].exits) <= CHECKS
    assert set(data.regions[WATER].exits) == {PREFIX + "ROOM_7_11", OUTER + "__ROOM_CHECK"}
    for parent, number, bit in ((OUTER, 3961175, 89), (TOP, 3961178, 92), (MAIN, 3961179, 93)):
        room_check, = [data.locations[key] for key in data.regions[parent + "__ROOM_CHECK"].locations]
        assert (room_check.location_id, room_check.bit_index) == (number, bit)
