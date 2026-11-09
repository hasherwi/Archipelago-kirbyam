"""Beginning Notes requires an actual source and the accepted directed Stone carrier."""

from dataclasses import replace
from types import SimpleNamespace
from typing import Any

import pytest
from BaseClasses import CollectionState, ItemClassification

from .. import traversal_rules as rules
from ..data import data, load_json_data
from ..traversal import METAL_BREAKING_ABILITIES, Position, SourcePolicy
from ..traversal_data import graph_items, room_traversal_graph, room_traversal_targets
from .test_metal_room205_statues import simulate_stone_gating
from .test_mini_traversal import make_world
from .test_traversal import policy


TARGET = "metal_537_beginning_notes"
OWNER = "REGION_RAINBOW_ROUTE/ROOM_1_39"
LOCATION = "MINOR_CHEST_MUSIC_NOTE_01"
END = "metal_537:chest"
CENTRAL = "REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE"
HUB190 = "REGION_RAINBOW_ROUTE/ROOM_1_HUB_1"
CONNECTION = "Rainbow Route East - Hub Connection"
PERMISSION = "Stone Ability"


def target_row() -> dict[str, Any]:
    return next(row for row in room_traversal_targets("metal") if row["id"] == TARGET)


@pytest.mark.parametrize("witness,access,start", [
    ("central_statues", CENTRAL, "hub_801"), ("rainbow190_statues", HUB190, "hub_190"),
])
@pytest.mark.parametrize("area_keys", [False, True])
def test_exact_native190_source_and_minimal_independent_access(
    monkeypatch: pytest.MonkeyPatch, witness: str, access: str, start: str, area_keys: bool,
) -> None:
    simulate_stone_gating(monkeypatch)
    graph = room_traversal_graph(TARGET, witness, area_keys)
    owned = frozenset({PERMISSION, CONNECTION} if witness == "central_statues" else {PERMISSION})
    native = SourcePolicy({"mode": 0})
    assert graph.access_region == access and graph.starts == (Position(start),)
    assert graph.evaluate(native, owned, True).reaches(END)
    for missing in owned:
        assert not graph.evaluate(native, owned - {missing}, True).reaches(END), missing
    source = next(s for s in graph.placements if s.identity == "0x088B7CEC")
    assert source.source_key == "STATUE:353900" and source.node == "hub_190"
    assert native.grant(source.source_key, lambda _: True).guaranteed == {"Stone"}
    assert source.renewable and source.retry_evidence
    assert graph.placements == room_traversal_graph("metal_205_to_209_top", "central_statues").placements
    assert all(s.source_key.startswith("STATUE:") for s in graph.placements)
    assert not any(s.node.startswith("metal_537:") for s in graph.placements)
    # Keep all legitimate hub outcomes; no special-case permission-to-equipment bridge.
    for bad in (replace(graph, placements=()),
                replace(graph, placements=(replace(source, node=END),)),
                replace(graph, starts=(Position("metal_537:537_left_arrival"),))):
        assert not bad.evaluate(native, graph_items(graph) | owned, True).reaches(END)


@pytest.mark.parametrize("mode,statues,pool,weight,finite,retry", [
    (0, False, None, 0, True, True), (1, False, ["Burning"], 0, True, True),
    (1, True, ["Stone"], 0, True, True), (1, True, ["Burning"], 0, False, False),
    (2, False, ["Burning"], 100, True, True), (2, True, ["Stone"], 100, True, True),
    (2, True, ["Stone", "Burning"], 100, False, True),
    (2, True, ["Burning"], 0, False, False),
])
def test_policy_is_actual_statue_grant_not_inventory_or_finite_rng(
    mode: int, statues: bool, pool: list[str] | None, weight: int, finite: bool, retry: bool,
) -> None:
    graph = room_traversal_graph(TARGET, "rainbow190_statues")
    resolver = policy(mode, statues=statues, pool=pool, weight=weight)  # type: ignore[no-untyped-call]
    owned = frozenset({PERMISSION, "Burning Ability"})
    assert graph.evaluate(resolver, owned, True).reaches(END) is finite
    result = graph.evaluate(resolver, owned, True, allow_documented_retries=True)
    assert result.reaches(END) is retry
    if retry and not finite:
        assert result.retry_assumptions
    assert rules.target_applies(target_row(), resolver)
    assert "requires_guaranteed_source" not in target_row()


@pytest.mark.parametrize("ability", sorted(METAL_BREAKING_ABILITIES | {"Normal"}))
def test_six_door_carrier_requires_retained_stone_and_exports_no_room_state(ability: str) -> None:
    graph = room_traversal_graph(TARGET, "central_statues")
    suffix = tuple(r for r in graph.routes if r.target.startswith("metal_537:"))
    assert len(suffix) == 7
    isolated = replace(graph, placements=(), routes=suffix, starts=(Position("hub_190", ability),))
    assert isolated.evaluate(SourcePolicy({"mode": 0}), frozenset(), True).reaches(END) is (ability == "Stone")
    rooms = {n.key: n.room for n in graph.nodes}
    assert {(rooms[r.source], rooms[r.target]) for r in suffix if r.room_transition} == {
        (190, 143), (143, 141), (141, 543), (543, 542), (542, 536), (536, 537)}
    final, = (r for r in suffix if r.capability)
    assert final.allowed_abilities == frozenset({"Stone"}) and final.water_state == "dry"
    assert not any(r.source == END for r in graph.routes)
    assert all(r.opens is None and not r.resets_room_instance and not r.preserves_room_instance
               and not r.recover_dropped_ability and r.uses_object is None for r in suffix)
    wet = replace(isolated, routes=tuple(replace(r, water_state="swimming") if r.capability else r for r in suffix))
    assert not wet.evaluate(SourcePolicy({"mode": 0}), frozenset(), True).reaches(END)


@pytest.mark.parametrize("access", [CENTRAL, HUB190, OWNER, None])
def test_location_rule_ors_independent_access_without_gating_room_or_exits(
    monkeypatch: pytest.MonkeyPatch, access: str | None,
) -> None:
    simulate_stone_gating(monkeypatch)
    row = target_row()
    assert row["region"] == OWNER and row["location"] == LOCATION
    monkeypatch.setattr(rules, "extra_traversal_targets", lambda: (row,))
    target = SimpleNamespace(access_rule=lambda state: state.base)
    indirect: list[str] = []
    world = SimpleNamespace(
        player=1, _enemy_copy_ability_policy={"mode": 0},
        _ability_gating_enabled=lambda: True, _area_keys_enabled=lambda: True,
        options=SimpleNamespace(ability_randomization_statues=SimpleNamespace(value=False)),
        multiworld=SimpleNamespace(get_location=lambda name, player: target, get_region=lambda name, player: name,
                                   register_indirect_condition=lambda name, entrance: indirect.append(name)),
    )
    rules.install_extra_traversal_rules(world)
    owned = {CONNECTION, PERMISSION}
    state = SimpleNamespace(base=True, has=lambda name, player: name in owned,
                            can_reach_region=lambda name, player: name == access)
    assert target.access_rule(state) is (access in {CENTRAL, HUB190})
    owned.remove(PERMISSION)
    assert not target.access_rule(state)
    owned.add(PERMISSION)
    state.base = False
    assert not target.access_rule(state)
    rooms = load_json_data("regions/rooms.json")
    assert isinstance(rooms, dict)
    assert rooms[OWNER]["exits"] == {
        "REGION_RAINBOW_ROUTE/ROOM_1_38": None,
        "REGION_RAINBOW_ROUTE/ROOM_1_36_HORIZONTAL": None,
    }
    assert data.locations[LOCATION].location_id == 3960514
    assert rooms[OWNER]["locations"]["room_sanity"] == {
        "included": True, "location_id": 3961005, "bit_index": 14}


@pytest.mark.parametrize("missing", [CONNECTION, PERMISSION])
def test_required_item_at_beginning_notes_cannot_unlock_itself(
    monkeypatch: pytest.MonkeyPatch, missing: str,
) -> None:
    simulate_stone_gating(monkeypatch)
    world = make_world(0, 1)  # type: ignore[no-untyped-call]
    mw = world.multiworld
    for region in mw.get_regions(1):
        region.exits.clear()
    mw.get_region("Menu", 1).connect(mw.get_region(OWNER, 1))
    mw.get_region("Menu", 1).connect(mw.get_region(CENTRAL, 1))
    state = CollectionState(mw)
    for name in {CONNECTION, PERMISSION} - {missing}:
        state.collect(world.create_item(name), prevent_sweep=True)
    while state.has(missing, 1):
        state.remove(world.create_item(missing))
    chest = mw.get_location(data.locations[LOCATION].label, 1)
    item = world.create_item(missing)
    item.classification = ItemClassification.progression
    chest.place_locked_item(item)
    state.sweep_for_advancements(locations=[chest])
    assert not chest.can_reach(state) and not state.has(missing, 1)
    state.collect(world.create_item(missing), prevent_sweep=True)
    assert chest.can_reach(state)
