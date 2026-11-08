"""Native141 arrival sides and independently sourced, directed metal passages."""

import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from BaseClasses import CollectionState

from .. import traversal_rules as rules
from ..data import data, load_json_data
from ..traversal import METAL_BREAKING_ABILITIES, Position, SourcePolicy
from ..traversal_data import room_traversal_graph, room_traversal_targets
from .test_metal_goal2 import simulate_burning_gating
from .test_mini_traversal import make_world
from .test_traversal import policy


LOWER = "REGION_RAINBOW_ROUTE/ROOM_1_41"
INNER = LOWER + "_UPPER"
TOP = LOWER + "__LOGIC__TOP_MUSTARD"
EAST = LOWER + "__LOGIC__EAST_MOONLIGHT"
CHECK = LOWER + "__ROOM_CHECK"
SIDES = {LOWER, INNER, TOP, EAST, CHECK}
TARGETS = {
    "metal_141_left_forward": ("local", LOWER, INNER, "0x088B78E8", "metal_141:inner"),
    "metal_141_right_forward": ("lower_carry", INNER, EAST, "0x088B78E8", "metal_141:east"),
    "metal_141_left_reverse": ("local", INNER, LOWER, "0x088B7810", "metal_141:lower_return"),
}


def row_for(identity: str) -> dict[str, Any]:
    return next(row for row in room_traversal_targets("metal") if row["id"] == identity)


@pytest.mark.parametrize("identity", TARGETS)
@pytest.mark.parametrize("mode,pool,weight,applies", [
    (0, None, 0, True), (1, ["Burning"], 0, True), (1, ["Smash"], 0, False),
    (2, ["Burning"], 0, True), (2, ["Burning", "Smash"], 0, False),
    (2, ["Burning"], 50, False), (2, ["Burning"], 100, False),
])
def test_policy_permission_and_independent_carrier_access(
    monkeypatch: pytest.MonkeyPatch, identity: str, mode: int,
    pool: list[str] | None, weight: int, applies: bool,
) -> None:
    simulate_burning_gating(monkeypatch)
    resolver = policy(mode, pool=pool, weight=weight)  # type: ignore[no-untyped-call]
    row = row_for(identity)
    assert rules.target_applies(row, resolver) is applies
    monkeypatch.setattr(rules, "extra_traversal_targets", lambda: (row,))
    assert rules.static_extra_witness(resolver)

    def original(state: Any) -> bool:
        return bool(state.base_rule)

    target = SimpleNamespace(access_rule=original)
    indirect: list[tuple[str, Any]] = []
    world = SimpleNamespace(
        player=1, _enemy_copy_ability_policy=resolver.policy,
        _ability_gating_enabled=lambda: True, _area_keys_enabled=lambda: False,
        options=SimpleNamespace(ability_randomization_statues=SimpleNamespace(value=False)),
        multiworld=SimpleNamespace(
            get_entrance=lambda name, player: target, get_region=lambda name, player: name,
            register_indirect_condition=lambda name, entrance: indirect.append((name, entrance)),
        ),
    )
    rules.install_extra_traversal_rules(world)
    owned: set[str] = set()
    access = {LOWER}
    state = SimpleNamespace(
        base_rule=True, has=lambda name, player: name in owned,
        can_reach_region=lambda name, player: name in access,
    )
    if not applies:
        assert target.access_rule is original  # Unknown assignments are not accepted witnesses.
    assert target.access_rule(state) is (not applies)
    owned.add("Burning Ability")
    assert target.access_rule(state)
    access.clear()
    needs_lower_access = identity == "metal_141_right_forward" and applies
    assert target.access_rule(state) is (not needs_lower_access)
    assert [name for name, entrance in indirect] == ([LOWER] if needs_lower_access else [])
    state.base_rule = False
    assert not target.access_rule(state)


@pytest.mark.parametrize("identity", TARGETS)
def test_no_free_equipment_inaccessible_source_or_persistent_opening(
    monkeypatch: pytest.MonkeyPatch, identity: str,
) -> None:
    simulate_burning_gating(monkeypatch)
    witness, owner, destination, source_id, endpoint = TARGETS[identity]
    row = row_for(identity)
    assert (row["region"], row["exit"]) == (owner, destination)
    graph = room_traversal_graph(identity, witness)
    source, = graph.placements
    assert source.identity == source_id and source.source_key == "FLAMER"
    assert not source.renewable and not source.retry_evidence
    assert all(position.equipped == "Normal" for position in graph.starts)
    assert {node.room for node in graph.nodes} == {141}
    assert all(not edge.room_transition and edge.opens is None for edge in graph.routes)
    resolver = SourcePolicy({"mode": 0})
    owned = frozenset({"Burning Ability"})
    assert not graph.evaluate(resolver, frozenset(), True).reaches(endpoint)
    assert graph.evaluate(resolver, owned, True).reaches(endpoint)
    assert not replace(graph, placements=()).evaluate(resolver, owned, True).reaches(endpoint)
    behind = replace(graph, placements=(replace(source, node=endpoint),))
    assert not behind.evaluate(resolver, owned, True).reaches(endpoint)
    backwards = replace(graph, starts=(Position(endpoint),))
    assert not backwards.evaluate(resolver, owned, True).reaches(graph.starts[0].node)


def test_forward_carry_part_reuses_the_same_finite_lower_object() -> None:
    first = room_traversal_graph("metal_141_left_forward", "local")
    second = room_traversal_graph("metal_141_right_forward", "lower_carry")
    assert second.placements == first.placements
    assert second.routes[-len(first.routes):] == first.routes
    assert second.starts == first.starts
    assert second.access_region == LOWER and first.access_region is None
    assert len(first.nodes) == 4 and len(second.nodes) == 6
    assert sum(edge.capability == "metal" for edge in second.routes) == 2


@pytest.mark.parametrize("identity", TARGETS)
@pytest.mark.parametrize("ability", sorted(METAL_BREAKING_ABILITIES))
def test_no_unreviewed_provider_or_swimming_activation(identity: str, ability: str) -> None:
    witness, _, _, _, endpoint = TARGETS[identity]
    graph = room_traversal_graph(identity, witness)
    final = next(edge for edge in graph.routes if edge.target == endpoint)
    assert final.capability == "metal" and final.allowed_abilities == frozenset({"Burning"})
    isolated = replace(graph, placements=(), starts=(Position(final.source, ability),))
    resolver = SourcePolicy({"mode": 0})
    assert isolated.evaluate(resolver, frozenset(), True).reaches(endpoint) is (ability == "Burning")
    wet = replace(isolated, routes=tuple(
        replace(route, water_state="swimming") if route.capability else route for route in isolated.routes))
    assert not wet.evaluate(resolver, frozenset(), True).reaches(endpoint)


@pytest.mark.parametrize("start,without_burning", [
    (LOWER, {LOWER, CHECK}), (INNER, {INNER, TOP, CHECK}),
    (TOP, {TOP, INNER, CHECK}), (EAST, {EAST, TOP, INNER, CHECK}),
])
def test_entry_sides_do_not_grant_lower_source_or_duplicate_room_check(
    monkeypatch: pytest.MonkeyPatch, start: str, without_burning: set[str],
) -> None:
    simulate_burning_gating(monkeypatch)
    world = make_world(0, 1, room_sanity=1)  # type: ignore[no-untyped-call]
    multiworld = world.multiworld
    # Isolate this physical room so unrelated external loops cannot mask a bad
    # internal direction. The actual installed traversal rules remain intact.
    for side in SIDES:
        region = multiworld.get_region(side, 1)
        region.exits = [edge for edge in region.exits
                        if edge.connected_region and edge.connected_region.name in SIDES]
    menu = multiworld.get_region("Menu", 1)
    menu.exits.clear()
    menu.connect(multiworld.get_region(start, 1))
    state = CollectionState(multiworld)
    while state.has("Burning Ability", 1):
        state.remove(world.create_item("Burning Ability"))
    assert {side for side in SIDES if state.can_reach_region(side, 1)} == without_burning
    checks = [location for location in multiworld.get_locations(1) if location.address == 3961020]
    assert len(checks) == 1 and checks[0].parent_region.name == CHECK
    assert checks[0].can_reach(state)
    assert not multiworld.get_region(CHECK, 1).exits
    state.collect(world.create_item("Burning Ability"), prevent_sweep=True)
    assert all(state.can_reach_region(side, 1) for side in SIDES)


def test_native_incoming_overrides_and_unaccepted_door_boundaries() -> None:
    rooms = load_json_data("regions/rooms.json")
    assert isinstance(rooms, dict)
    assert rooms["REGION_MOONLIGHT_MANSION/ROOM_2_16"]["logical_exit_overrides"][LOWER] == "EAST_MOONLIGHT"
    assert rooms["REGION_MUSTARD_MOUNTAIN/ROOM_4_07"]["logical_exit_overrides"][LOWER] == "TOP_MUSTARD"
    assert EAST in data.regions["REGION_MOONLIGHT_MANSION/ROOM_2_16"].exits
    assert TOP in data.regions["REGION_MUSTARD_MOUNTAIN/ROOM_4_07"].exits
    assert LOWER not in data.regions["REGION_MOONLIGHT_MANSION/ROOM_2_16"].exits
    assert LOWER not in data.regions["REGION_MUSTARD_MOUNTAIN/ROOM_4_07"].exits
    assert LOWER in data.regions["REGION_RAINBOW_ROUTE/ROOM_1_40"].exits
    assert LOWER in data.regions["REGION_RAINBOW_ROUTE/ROOM_1_42"].exits
    assert EAST not in data.regions[TOP].exits  # No unproved downward0x0F route.
    assert data.regions[INNER].exit_requirements[TOP] == "can_break_floating_block"
    assert data.regions[EAST].exit_requirements["REGION_MOONLIGHT_MANSION/ROOM_2_16"] == "can_mirra"
    assert data.regions[TOP].exit_requirements["REGION_MUSTARD_MOUNTAIN/ROOM_4_07"] == "can_mirra"
    assert {row_for(identity)["exit"] for identity in TARGETS} == {LOWER, INNER, EAST}


def test_native_records_separate_controlled_paths_and_known_limits() -> None:
    root = Path(__file__).parents[1] / "dev-docs"
    record = json.loads((root / "ordinary-141-directed-burning-acceptance.json").read_text())
    observations = record["tile_observations"]
    assert all(tile["tile"] == 0 for tile in observations["actualbanks141"][:8])
    assert [tile["tile"] for tile in observations["reversebank141"][:8]] == [0] * 4 + [245] * 4
    assert "No native144 transition established" in record["results"]["limits"][0]
    join = json.loads((root / "ordinary-141-lower-arrival-join.json").read_text())
    assert join["fixture"]["native_door_record_rom_offset"] == "0x879858"
    assert all(tile["tile"] == 245 for tile in join["remaining_metal"])
    doors = json.loads((root / "ordinary-141-door-topology.json").read_text())
    incoming = {row["source"]: row["spawn_tile"] for row in doors["incoming"]}
    assert incoming == {143: [43, 19], 144: [43, 9], 543: [3, 14], 545: [34, 4]}


def test_reverse_bomb_crossing_starts_with_fresh_intact_wall() -> None:
    root = Path(__file__).parents[1] / "dev-docs"
    record = json.loads((root / "ordinary-141-reverse-bomb-acceptance.json").read_text())
    observations = record["tile_observations"]
    for key in ("freshreversebomb141", "freshinnerclimb141"):
        assert [tile["tile"] for tile in observations[key]] == [241, 241, 242, 245, 245]
    assert [tile["tile"] for tile in observations["freshbombcross141"]] == [0, 0, 0, 245, 245]
    assert record["segments"][0]["parent_controller_state"] == "actualshaft141"
    assert all(not segment["writes"] for segment in record["segments"])
    end = record["segments"][-1]["checkpoints"][-1]
    assert end["room"] == 141 and end["ability"] == 0 and end["hp"] == 6
    assert (end["x"], end["y"]) == (544.9140625, 56.99609375)
