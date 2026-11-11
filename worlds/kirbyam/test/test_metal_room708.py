"""708 source-backed terminal plans must not union C's two sides or fresh arrivals."""

from dataclasses import replace
from types import SimpleNamespace
from typing import Any

import pytest
from BaseClasses import CollectionState, ItemClassification

from .. import traversal_rules as rules
from ..data import data, load_json_data
from ..traversal import METAL_BREAKING_ABILITIES, Position, SourcePolicy
from ..traversal_data import graph_items, room_traversal_graph, room_traversal_targets
from .test_metal_goal2 import simulate_burning_gating
from .test_metal_room707 import CENTRAL, CABBAGE, CONNECTIONS, KEYS, PERMISSION
from .test_mini_traversal import make_world
from .test_traversal import policy


LEFT = "REGION_MOONLIGHT_MANSION/ROOM_2_01"
UPPER, RIGHT = LEFT + "_UPPER_PLATFORM", LEFT + "_PAST_METAL_BLOCKS"
BOTTOM_LEFT, BOTTOM_RIGHT = LEFT + "_BOTTOM_LEFT", LEFT + "_BOTTOM_RIGHT"
RIGHT_TOP, CHECK = LEFT + "__LOGIC__RIGHT_TOP", LEFT + "__ROOM_CHECK"
LOWER706 = "REGION_MOONLIGHT_MANSION/ROOM_2_03_LOWER"
MAIN743 = "REGION_MOONLIGHT_MANSION/ROOM_2_11"
DEAD743 = MAIN743 + "_DEAD_END"
SIDES = {LEFT, UPPER, RIGHT, BOTTOM_LEFT, BOTTOM_RIGHT, RIGHT_TOP, CHECK}
TARGETS = {
    "metal_708_forward": (LEFT, RIGHT, "metal_708:706_lower_door"),
    "metal_708_743_main": (RIGHT, BOTTOM_LEFT, "metal_708:743_main_door"),
    "metal_708_743_dead_end": (RIGHT, BOTTOM_RIGHT, "metal_708:743_dead_end_door"),
}


def target_row(identity: str) -> dict[str, Any]:
    return next(row for row in room_traversal_targets("metal") if row["id"] == identity)


@pytest.mark.parametrize("identity", TARGETS)
@pytest.mark.parametrize("witness,access", [("central_statues", CENTRAL), ("cabbage592_statues", CABBAGE)])
@pytest.mark.parametrize("area_keys", [False, True])
def test_actual_source_and_independent_hub_guards(
    monkeypatch: pytest.MonkeyPatch, identity: str, witness: str, access: str, area_keys: bool,
) -> None:
    simulate_burning_gating(monkeypatch)
    graph = room_traversal_graph(identity, witness, area_keys)
    endpoint = TARGETS[identity][2]
    owned = CONNECTIONS | PERMISSION
    if area_keys:
        owned |= KEYS if witness == "central_statues" else KEYS - {"Cabbage Cavern - Area Key"}
    native = SourcePolicy({"mode": 0})
    assert graph.access_region == access
    assert graph.starts == (Position("hub_801" if witness == "central_statues" else "hub_592"),)
    assert graph.evaluate(native, owned, True).reaches(endpoint)
    for missing in owned:
        assert not graph.evaluate(native, owned - {missing}, True).reaches(endpoint), missing
    prefix = room_traversal_graph("metal_707_to_712", witness, area_keys)
    assert graph.placements == prefix.placements
    assert all(not source.node.startswith("metal_708:") for source in graph.placements)
    source = next(source for source in graph.placements if source.identity == "0x088CEFC8")
    assert source.source_key == "STATUE:3538FD" and source.renewable
    assert native.grant("STATUE:353902", lambda _: True).guaranteed == {"Bomb"}
    for bad in (replace(graph, placements=()),
                replace(graph, placements=(replace(source, node=endpoint),)),
                replace(graph, starts=(Position("metal_708:upper_left_arrival"),))):
        assert not bad.evaluate(native, graph_items(graph) | PERMISSION, True).reaches(endpoint)


@pytest.mark.parametrize("identity", TARGETS)
@pytest.mark.parametrize("mode,statues,pool,weight,finite,retry", [
    (0, False, None, 0, True, True), (1, False, ["Hammer"], 0, True, True),
    (1, True, ["Burning"], 0, True, True), (1, True, ["Hammer"], 0, False, False),
    (2, False, ["Hammer"], 100, True, True), (2, True, ["Burning"], 100, True, True),
    (2, True, ["Burning", "Hammer"], 50, False, True),
    (2, True, ["Hammer"], 0, False, False),
])
def test_actual_statue_policy_without_legacy_fallback(
    identity: str, mode: int, statues: bool, pool: list[str] | None,
    weight: int, finite: bool, retry: bool,
) -> None:
    graph = room_traversal_graph(identity, "central_statues")
    resolver = policy(mode, statues=statues, pool=pool, weight=weight)  # type: ignore[no-untyped-call]
    owned = CONNECTIONS | PERMISSION | {"Hammer Ability"}
    assert graph.evaluate(resolver, owned, True).reaches(TARGETS[identity][2]) is finite
    result = graph.evaluate(resolver, owned, True, allow_documented_retries=True)
    assert result.reaches(TARGETS[identity][2]) is retry
    if retry and not finite:
        assert result.retry_assumptions
    assert rules.target_applies(target_row(identity), resolver)


@pytest.mark.parametrize("identity", TARGETS)
@pytest.mark.parametrize("ability", sorted(METAL_BREAKING_ABILITIES | {"Normal"}))
def test_entire_branch_keeps_burning_and_is_terminal(identity: str, ability: str) -> None:
    graph = room_traversal_graph(identity, "central_statues")
    endpoint = TARGETS[identity][2]
    suffix = tuple(route for route in graph.routes if route.target.startswith("metal_708:"))
    assert len(suffix) == 3
    isolated = replace(graph, placements=(), routes=suffix, starts=(Position("hub_790", ability),))
    assert isolated.evaluate(SourcePolicy({"mode": 0}), frozenset(), True).reaches(endpoint) is (ability == "Burning")
    final, = (r for r in suffix if r.capability)
    assert final.source == "metal_708:upper_left_arrival" and final.target == endpoint
    assert final.capability == "metal" and final.allowed_abilities == frozenset({"Burning"})
    assert not any(r.source == endpoint for r in graph.routes)
    assert all(r.opens is None and not r.resets_room_instance and not r.preserves_room_instance
               and not r.recover_dropped_ability and r.uses_object is None for r in suffix)


@pytest.mark.parametrize("identity", TARGETS)
@pytest.mark.parametrize("access", [CENTRAL, CABBAGE, RIGHT_TOP, None])
def test_installed_branch_uses_one_or_target_not_generic_room_access(
    monkeypatch: pytest.MonkeyPatch, identity: str, access: str | None,
) -> None:
    simulate_burning_gating(monkeypatch)
    row = target_row(identity)
    assert (row["region"], row["exit"]) == TARGETS[identity][:2]
    assert "requires_guaranteed_source" not in row
    monkeypatch.setattr(rules, "extra_traversal_targets", lambda: (row,))
    target = SimpleNamespace(access_rule=lambda state: state.base)
    indirect: list[str] = []
    world = SimpleNamespace(
        player=1, _enemy_copy_ability_policy={"mode": 0},
        _ability_gating_enabled=lambda: True, _area_keys_enabled=lambda: True,
        options=SimpleNamespace(ability_randomization_statues=SimpleNamespace(value=False)),
        multiworld=SimpleNamespace(get_entrance=lambda name, player: target, get_region=lambda name, player: name,
                                   register_indirect_condition=lambda name, entrance: indirect.append(name)),
    )
    rules.install_extra_traversal_rules(world)
    owned = set(CONNECTIONS | KEYS | PERMISSION)
    state = SimpleNamespace(base=True, has=lambda name, player: name in owned,
                            can_reach_region=lambda name, player: name == access)
    assert target.access_rule(state) is (access in {CENTRAL, CABBAGE})
    assert set(indirect) == {CENTRAL, CABBAGE}
    owned.remove("Burning Ability")
    assert not target.access_rule(state)
    owned.add("Burning Ability")
    state.base = False
    assert not target.access_rule(state)


@pytest.mark.parametrize("start", sorted(SIDES - {CHECK}))
def test_room_check_sink_cannot_restore_closed_or_unreviewed_routes(start: str) -> None:
    world = make_world(0, 1, room_sanity=1)  # type: ignore[no-untyped-call]
    mw = world.multiworld
    for name in SIDES:
        region = mw.get_region(name, 1)
        region.exits = [edge for edge in region.exits if edge.connected_region.name in SIDES]
    mw.get_region("Menu", 1).exits.clear()
    mw.get_region("Menu", 1).connect(mw.get_region(start, 1))
    state = CollectionState(mw)
    expected = {LEFT, UPPER, CHECK} if start in {LEFT, UPPER} else {start, CHECK}
    assert {name for name in SIDES if state.can_reach_region(name, 1)} == expected
    check, = (loc for loc in mw.get_locations(1) if loc.address == 3961062)
    assert check.can_reach(state) and check.parent_region.name == CHECK
    assert not mw.get_region(CHECK, 1).exits


def test_exact_arrival_and_return_edges_do_not_cross_c_divider() -> None:
    rooms = load_json_data("regions/rooms.json")
    assert isinstance(rooms, dict)
    assert rooms[LOWER706]["logical_exit_overrides"] == {LEFT: "RIGHT_TOP"}
    assert RIGHT_TOP in data.regions[LOWER706].exits and LEFT not in data.regions[LOWER706].exits
    assert set(data.regions[RIGHT_TOP].exits) == {LOWER706, CHECK}
    assert set(data.regions[BOTTOM_LEFT].exits) == {MAIN743, CHECK}
    assert set(data.regions[BOTTOM_RIGHT].exits) == {DEAD743, CHECK}
    assert BOTTOM_LEFT in data.regions[MAIN743].exits
    assert BOTTOM_RIGHT in data.regions[DEAD743].exits
    # The new native join uses retained Burning. Do not export it as a generic
    # Normal shortcut from arbitrary main-room or after-lever access.
    assert DEAD743 not in data.regions[MAIN743].exits
    assert not data.regions[DEAD743].locations
    assert not data.regions[DEAD743].events
    assert set(rooms[MAIN743]["locations"]) == {"room_sanity", "LEVER_MOONLIGHT_MANSION_2_11"}
    assert rooms[MAIN743]["locations"]["room_sanity"] == {
        "included": True, "location_id": 3961072, "bit_index": 82}
    assert rooms[MAIN743]["events"] == ["Activate Lever - Moonlight Mansion 2-11"]
    assert rooms[MAIN743 + "_AFTER_LEVER"]["locations"] == {}
    assert LEFT not in data.regions[RIGHT].exits
    assert rooms[LEFT]["locations"]["room_sanity"] == {
        "included": True, "location_id": 3961062, "bit_index": 72}


@pytest.mark.parametrize("start", [MAIN743, MAIN743 + "_AFTER_LEVER"])
def test_arbitrary_main_or_after_lever_access_does_not_grant_dead_end(start: str) -> None:
    world = make_world(0, 1, room_sanity=1)  # type: ignore[no-untyped-call]
    mw = world.multiworld
    allowed = SIDES | {MAIN743, DEAD743, MAIN743 + "_AFTER_LEVER"}
    for region in mw.get_regions(1):
        region.exits = [edge for edge in region.exits
                        if region.name in allowed and edge.connected_region.name in allowed]
    mw.get_region("Menu", 1).connect(mw.get_region(start, 1))
    state = CollectionState(mw)
    assert state.can_reach_region(start, 1)
    assert not state.can_reach_region(DEAD743, 1)
    assert not state.can_reach_region(BOTTOM_RIGHT, 1)


@pytest.mark.parametrize("missing", [
    "Burning Ability", "Moonlight Mansion - Hub Connection", "Cabbage Cavern West - Hub Connection",
])
def test_required_permission_or_hub_item_cannot_be_borrowed_from743(
    monkeypatch: pytest.MonkeyPatch, missing: str,
) -> None:
    simulate_burning_gating(monkeypatch)
    world = make_world(0, 1)  # type: ignore[no-untyped-call]
    mw = world.multiworld
    allowed = SIDES | {MAIN743, DEAD743, LOWER706}
    for region in mw.get_regions(1):
        region.exits = [edge for edge in region.exits
                        if region.name in allowed and edge.connected_region.name in allowed]
    menu = mw.get_region("Menu", 1)
    menu.connect(mw.get_region(LEFT, 1))
    menu.connect(mw.get_region(CENTRAL, 1))
    state = CollectionState(mw)
    for name in CONNECTIONS | KEYS | PERMISSION:
        if name != missing:
            state.collect(world.create_item(name), prevent_sweep=True)
    while state.has(missing, 1):
        state.remove(world.create_item(missing))
    downstream = mw.get_location(data.locations["LEVER_MOONLIGHT_MANSION_2_11"].label, 1)
    item = world.create_item(missing)
    item.classification = ItemClassification.progression
    downstream.place_locked_item(item)
    state.sweep_for_advancements(locations=[downstream])
    assert not state.can_reach_region(MAIN743, 1)
    assert not state.has(missing, 1) and downstream not in state.advancements
    state.collect(world.create_item(missing), prevent_sweep=True)
    assert state.can_reach_region(MAIN743, 1) and downstream.can_reach(state)
