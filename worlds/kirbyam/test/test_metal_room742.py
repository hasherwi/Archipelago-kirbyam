"""Native742 clean source carry and disjoint dirty/unknown upper arrival."""

from dataclasses import replace
from types import SimpleNamespace
from typing import Any

import pytest
from BaseClasses import CollectionState, ItemClassification

from .. import traversal_rules as rules
from ..data import data, load_json_data
from ..traversal import METAL_BREAKING_ABILITIES, Node, Placement, Position, Route, SourcePolicy
from ..traversal_data import room_traversal_graph, room_traversal_targets
from .test_metal_goal2 import simulate_burning_gating
from .test_mini_traversal import make_world
from .test_traversal import policy


ACCESS = "REGION_MOONLIGHT_MANSION/ROOM_2_13"
SOURCE = "REGION_MOONLIGHT_MANSION/ROOM_2_14"
RETURN_SOURCE = SOURCE + "_UPPER"
LOWER = "REGION_MOONLIGHT_MANSION/ROOM_2_15"
UPPER = LOWER + "__LOGIC__UPPER_RETURN"
CHECK = LOWER + "__ROOM_CHECK"
WARP = "REGION_MOONLIGHT_MANSION/ROOM_2_WARP"
LOCATION = "MINOR_CHEST_MOONLIGHT_MANSION_2_15_OBJECT_01"
PREFIX = "metal_742:"
TARGETS = {"metal_742_sparerib": "clean_chest", "metal_742_lower_to_warp": "clean_warp"}


def row_for(identity: str) -> dict[str, Any]:
    return next(row for row in room_traversal_targets("metal") if row["id"] == identity)


@pytest.mark.parametrize("identity", TARGETS)
@pytest.mark.parametrize("mode,pool,weight,applies", [
    (0, None, 0, True), (1, ["Burning"], 0, True), (1, ["Hammer"], 0, False),
    (2, ["Burning"], 0, True), (2, ["Burning", "Hammer"], 0, False),
    (2, ["Burning"], 50, False), (2, ["Burning"], 100, False),
])
def test_local_source_permission_and_independent712_access(
    monkeypatch: pytest.MonkeyPatch, identity: str, mode: int,
    pool: list[str] | None, weight: int, applies: bool,
) -> None:
    simulate_burning_gating(monkeypatch)
    resolver = policy(mode, pool=pool, weight=weight)  # type: ignore[no-untyped-call]
    row = row_for(identity)
    assert rules.target_applies(row, resolver)
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
            get_location=lambda name, player: target, get_entrance=lambda name, player: target,
            get_region=lambda name, player: name,
            register_indirect_condition=lambda name, entrance: indirect.append((name, entrance)),
        ),
    )
    rules.install_extra_traversal_rules(world)
    owned = {"Hammer Ability"}  # Keep both live-pool outcomes permitted when testing a finite grant.
    access = {ACCESS}
    state = SimpleNamespace(
        base_rule=True, has=lambda name, player: name in owned,
        can_reach_region=lambda name, player: name in access,
    )
    assert target.access_rule is not original
    assert not target.access_rule(state)
    owned.add("Burning Ability")
    assert target.access_rule(state) is applies
    access.clear()
    assert not target.access_rule(state)
    expected = {ACCESS, "REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE",
                "REGION_CABBAGE_CAVERN/ROOM_3_HUB_3"} if "exit" in row else set()
    assert {name for name, entrance in indirect} == expected
    state.base_rule = False
    assert not target.access_rule(state)


@pytest.mark.parametrize("identity", TARGETS)
def test_source_prefix_is_finite_and_cannot_be_bootstrapped(
    monkeypatch: pytest.MonkeyPatch, identity: str,
) -> None:
    simulate_burning_gating(monkeypatch)
    graph = room_traversal_graph(identity, "clean_carry")
    endpoint = PREFIX + TARGETS[identity]
    source, = graph.placements
    assert source.identity == "0x088BD8AC" and source.source_key == "FLAMER"
    assert source.node == PREFIX + "741_main_source"
    assert not source.renewable and not source.retry_evidence
    assert graph.starts == (Position(PREFIX + "741_arrival"),)
    assert graph.access_region == ACCESS
    assert {node.room for node in graph.nodes} == {741, 742}
    assert len(graph.nodes) == 4 and len(graph.routes) == 3
    crossings = [route for route in graph.routes if route.room_transition]
    assert len(crossings) == 1 and crossings[0].target == PREFIX + "clean_lower"
    assert all(not route.preserves_room_instance and not route.resets_room_instance for route in graph.routes)
    assert all(route.opens is None and route.uses_object is None for route in graph.routes)
    resolver = SourcePolicy({"mode": 0})
    owned = frozenset({"Burning Ability"})
    assert graph.evaluate(resolver, owned, True).reaches(endpoint)
    assert not graph.evaluate(resolver, frozenset(), True).reaches(endpoint)
    for blocked in (
        replace(graph, placements=()),
        replace(graph, placements=(replace(source, node=endpoint),)),
        replace(graph, starts=(Position(PREFIX + "clean_lower"),)),
        replace(graph, starts=(Position(PREFIX + "741_arrival", consumed=frozenset({source.identity})),)),
    ):
        assert not blocked.evaluate(resolver, owned, True).reaches(endpoint)


def test_two_independent_terminal_sequences_share_one_source_prefix() -> None:
    chest = room_traversal_graph("metal_742_sparerib", "clean_carry")
    warp = room_traversal_graph("metal_742_lower_to_warp", "clean_carry")
    assert chest.placements == warp.placements and chest.starts == warp.starts
    assert chest.routes[1:] == warp.routes[1:]
    assert chest.required_targets == frozenset({PREFIX + "clean_chest"})
    assert warp.required_targets == frozenset({PREFIX + "clean_warp"})
    for identity in TARGETS:
        action = row_for(identity)["graphs"]["clean_carry"]["routes"][0]
        assert "ordinary-742-all500-combined-checks.json" in action["metal_evidence"]["Burning"]
    assert PREFIX + "clean_warp" not in {node.key for node in chest.nodes}
    assert PREFIX + "clean_chest" not in {node.key for node in warp.nodes}
    # Distinct terminal outcomes cannot splice clean plans or export equipment.
    # The durable-enemy chest continuation actually ends Normal; the abstract
    # terminal success is never a reusable equipped-Burning postcondition.
    for graph in (chest, warp):
        assert not any(edge.source in graph.required_targets for edge in graph.routes)
        assert len([edge for edge in graph.routes if edge.capability]) == 1
        endpoint, = graph.required_targets
        final = next(edge for edge in graph.routes if edge.target == endpoint)
        assert final.source == PREFIX + "clean_lower"
        reverse = replace(graph, starts=(Position(endpoint, "Burning"),))
        assert not reverse.evaluate(SourcePolicy({"mode": 0}), frozenset(), True).reaches(PREFIX + "clean_lower")


@pytest.mark.parametrize("identity", TARGETS)
@pytest.mark.parametrize("ability", sorted(METAL_BREAKING_ABILITIES))
def test_exact_atomic_burning_sequence_only(identity: str, ability: str) -> None:
    graph = room_traversal_graph(identity, "clean_carry")
    endpoint = PREFIX + TARGETS[identity]
    final = next(edge for edge in graph.routes if edge.target == endpoint)
    assert final.capability == "metal" and final.allowed_abilities == frozenset({"Burning"})
    isolated = replace(graph, placements=(), starts=(Position(final.source, ability),))
    resolver = SourcePolicy({"mode": 0})
    assert isolated.evaluate(resolver, frozenset(), True).reaches(endpoint) is (ability == "Burning")
    wet = replace(isolated, routes=tuple(
        replace(edge, water_state="swimming") if edge.capability else edge for edge in isolated.routes))
    assert not wet.evaluate(resolver, frozenset(), True).reaches(endpoint)


@pytest.mark.parametrize("lifetime", ["unknown", "preserve", "reset"])
@pytest.mark.parametrize("identity", TARGETS)
def test_dirty_return_never_becomes_clean_via_instance_flags(identity: str, lifetime: str) -> None:
    graph = room_traversal_graph(identity, "clean_carry")
    # Hypothetical mutation edges test representation only, not native acceptance.
    # They must never be copied into production as physical movement evidence.
    dirty_nodes = (
        Node("outer_changed", 742), Node("inner_door", 742),
        Node("upper_source", 741), Node("return_unknown", 742),
    )
    dirty_routes = (
        Route(PREFIX + "clean_lower", "outer_changed"),
        Route("outer_changed", "inner_door"),
        Route("inner_door", "upper_source", room_transition=True),
        Route("upper_source", "return_unknown", room_transition=True,
              preserves_room_instance=lifetime == "preserve", resets_room_instance=lifetime == "reset"),
    )
    expanded = replace(
        graph, nodes=graph.nodes + dirty_nodes, routes=graph.routes + dirty_routes,
        placements=graph.placements + (Placement("upper_source", "FLAMER", identity="0x088BDA38"),),
    )
    resolver = SourcePolicy({"mode": 0})
    owned = frozenset(f"{ability} Ability" for ability in METAL_BREAKING_ABILITIES)
    for start in ("outer_changed", "inner_door", "upper_source", "return_unknown"):
        result = replace(expanded, starts=(Position(start, "Burning"),)).evaluate(resolver, owned, True)
        assert not any(position.node.startswith(PREFIX + "clean_") for position in result.positions)
    without_inner_action = replace(
        expanded, routes=tuple(edge for edge in expanded.routes if edge.source != "outer_changed"),
        starts=(Position("outer_changed", "Burning"),),
    )
    assert not without_inner_action.evaluate(resolver, owned, True).reaches("inner_door")


@pytest.mark.parametrize("start", [LOWER, UPPER])
def test_ap_arrivals_share_only_single_room_check_sink(monkeypatch: pytest.MonkeyPatch, start: str) -> None:
    simulate_burning_gating(monkeypatch)
    world = make_world(0, 1, room_sanity=1)  # type: ignore[no-untyped-call]
    multiworld = world.multiworld
    sides = {LOWER, UPPER, CHECK, WARP}
    for side in sides:
        region = multiworld.get_region(side, 1)
        region.exits = [edge for edge in region.exits
                        if edge.connected_region and edge.connected_region.name in sides]
    menu = multiworld.get_region("Menu", 1)
    menu.exits.clear()
    menu.connect(multiworld.get_region(start, 1))
    state = CollectionState(multiworld)
    target = multiworld.get_location(data.locations[LOCATION].label, 1)
    # Even every permission cannot turn an upper arrival into the independent712
    # clean plan, and merely reaching lower742 does not invent that plan either.
    for ability in METAL_BREAKING_ABILITIES:
        item_name = ability + " Ability"
        if item_name in world.item_name_to_id:
            state.collect(world.create_item(item_name), prevent_sweep=True)
    assert not state.can_reach_region(ACCESS, 1)
    assert not target.can_reach(state)
    assert not state.can_reach_region(UPPER if start == LOWER else LOWER, 1)
    checks = [location for location in multiworld.get_locations(1) if location.address == 3961069]
    assert len(checks) == 1 and checks[0].parent_region.name == CHECK
    assert checks[0].can_reach(state) and not multiworld.get_region(CHECK, 1).exits
    # Upper->Warp remains explicitly unvalidated legacy behavior. It does not
    # join the clean chest plan or imply a room reset.
    assert state.can_reach_region(WARP, 1) is (start == UPPER)


def test_actual_native_arrivals_and_legacy_unknown_upper_exit() -> None:
    rooms = load_json_data("regions/rooms.json")
    assert isinstance(rooms, dict)
    assert rooms[RETURN_SOURCE]["logical_exit_overrides"][LOWER] == "UPPER_RETURN"
    assert data.regions[SOURCE].exits == [LOWER]
    assert data.regions[RETURN_SOURCE].exits == [UPPER]
    assert LOWER + "_UPPER_LEDGE_SPAWN" not in data.regions
    assert data.regions[UPPER].exit_requirements[WARP] == "can_break_metal"
    assert LOWER not in data.regions[UPPER].exits
    assert data.regions[LOWER].exit_requirements[RETURN_SOURCE] == {
        "all": ["can_fly", "can_break_floating_block"]}
    assert data.locations[LOCATION].source_rom_offset == 0x8BDD10
    assert data.locations[LOCATION].location_id == 3960585
    assert row_for("metal_742_sparerib")["location"] == LOCATION
    assert row_for("metal_742_lower_to_warp")["exit"] == WARP


@pytest.mark.parametrize("room_sanity", [0, 1])
def test_independent712_precedes_every_first742_visit(room_sanity: int) -> None:
    world = make_world(0, 1, room_sanity=room_sanity)  # type: ignore[no-untyped-call]
    multiworld = world.multiworld
    assert world.origin_region_name == "Menu"
    assert {edge.connected_region.name for edge in multiworld.get_region("Menu", 1).exits} == {"REGION_GAME_START"}

    def structural_reach(blocked: set[str]) -> set[str]:
        # Ignore all access rules: aliases, summary links and even legacy exits
        # must not provide an earlier dirty742 visit before independent712.
        seen = {world.origin_region_name}
        pending = [world.origin_region_name]
        while pending:
            for edge in multiworld.get_region(pending.pop(), 1).exits:
                if edge.connected_region is None:
                    continue
                destination = edge.connected_region.name
                if destination not in blocked and destination not in seen:
                    seen.add(destination)
                    pending.append(destination)
        return seen

    downstream = {SOURCE, RETURN_SOURCE, LOWER, UPPER, CHECK, WARP}
    assert downstream | {ACCESS} <= structural_reach(set())  # Nonvacuous.
    assert not downstream & structural_reach({ACCESS})
    assert ACCESS in structural_reach(downstream)
    assert {edge.parent_region.name for edge in multiworld.get_region(ACCESS, 1).entrances} == {
        "REGION_MOONLIGHT_MANSION/ROOM_2_04_PAST_SWITCH_WALL"}


def test_future_burning_cannot_unlock_its_own_chest(monkeypatch: pytest.MonkeyPatch) -> None:
    simulate_burning_gating(monkeypatch)
    world = make_world(0, 1)  # type: ignore[no-untyped-call]
    multiworld = world.multiworld
    target = multiworld.get_location(data.locations[LOCATION].label, 1)
    item = world.create_item("Burning Ability")
    item.classification = ItemClassification.progression  # Fixture only; production starts/classification unchanged.
    target.place_locked_item(item)
    menu = multiworld.get_region("Menu", 1)
    menu.exits.clear()
    menu.connect(multiworld.get_region(ACCESS, 1))
    state = CollectionState(multiworld)
    while state.has("Burning Ability", 1):
        state.remove(world.create_item("Burning Ability"))
    assert state.can_reach_region(LOWER, 1)
    state.sweep_for_advancements(locations=[target])
    assert not state.has("Burning Ability", 1) and not target.can_reach(state)
    assert target not in state.advancements
    state.collect(world.create_item("Burning Ability"), prevent_sweep=True)
    assert target.can_reach(state)
    state.sweep_for_advancements(locations=[target])
    assert target in state.advancements
