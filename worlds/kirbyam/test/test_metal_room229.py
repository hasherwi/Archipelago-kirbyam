"""Only229's left1Up uses the joint, source-backed retained-Hammer itinerary."""

from dataclasses import replace
from types import SimpleNamespace
from typing import Any

import pytest
from BaseClasses import CollectionState

from .. import traversal_rules as rules
from ..data import data
from ..traversal import METAL_BREAKING_ABILITIES, Position, SourcePolicy
from ..traversal_data import graph_items, room_traversal_graph, room_traversal_targets
from .test_metal_room228_statues import ACCESS, AREA_KEY, BONKERS_REGION, CONNECTION, PERMISSION, SOURCE_REGION
from .test_mini_traversal import make_world
from .test_traversal import policy


TARGET = "metal_229_left1up"
END = "metal_229:left_chest"
OWNER = "REGION_PEPPERMINT_PALACE/ROOM_7_10"
LOCATION = "MINOR_CHEST_PEPPERMINT_PALACE_7_10_OBJECT_02"
WITNESSES = ("bonkers_joint", "copy_room_statues")


def row_for() -> dict[str, Any]:
    return next(row for row in room_traversal_targets("metal") if row["id"] == TARGET)


def test_exact_left_target_does_not_regate_other_checks_or_create_compartments() -> None:
    row = row_for()
    assert row["location"] == LOCATION and row["region"] == OWNER and row["native_room"] == 229
    assert set(row["graphs"]) == set(WITNESSES) and "requires_guaranteed_source" not in row
    region = data.regions[OWNER]
    assert data.locations[LOCATION].location_id == 3960593
    assert data.locations["MINOR_CHEST_SPRAY_PAINT_09"].location_id == 3960508
    assert data.locations["MINOR_CHEST_PEPPERMINT_PALACE_7_10_OBJECT_03"].location_id == 3960594
    assert set(region.exits) == {"REGION_PEPPERMINT_PALACE/ROOM_7_WARP"}
    assert not any(name.startswith(OWNER + "__") for name in data.regions)
    # This assertion preserves existing topology, not a new native cross-channel acceptance.
    assert region.location_requirements.get(LOCATION) is None
    assert region.location_requirements.get("MINOR_CHEST_SPRAY_PAINT_09") is None
    assert region.location_requirements.get("MINOR_CHEST_PEPPERMINT_PALACE_7_10_OBJECT_03") is None
    assert len(region.locations) == 4
    assert not any(r.get("location") in {"MINOR_CHEST_SPRAY_PAINT_09",
                   "MINOR_CHEST_PEPPERMINT_PALACE_7_10_OBJECT_03"}
                   or r.get("exit") == "REGION_PEPPERMINT_PALACE/ROOM_7_WARP"
                   for r in room_traversal_targets("metal"))


@pytest.mark.parametrize("witness,nodes,routes,sources", [
    ("bonkers_joint", 11, 10, 1), ("copy_room_statues", 15, 14, 19),
])
@pytest.mark.parametrize("keys", [False, True])
def test_complete228_prefix_is_reused_without_new_sources_or_equipped_starts(
    witness: str, nodes: int, routes: int, sources: int, keys: bool,
) -> None:
    prefix = room_traversal_graph("metal_228_chest", witness, keys)
    graph = room_traversal_graph(TARGET, witness, keys)
    prefix_nodes = {n.key for n in prefix.nodes}
    assert tuple(n for n in graph.nodes if n.key in prefix_nodes) == prefix.nodes
    assert tuple(r for r in graph.routes if r.target in prefix_nodes) == prefix.routes
    assert graph.placements == prefix.placements and graph.starts == prefix.starts
    assert graph.access_region == prefix.access_region
    assert (len(graph.nodes), len(graph.routes), len(graph.placements)) == (nodes, routes, sources)
    assert all(p.equipped == "Normal" for p in graph.starts)
    assert graph.required_targets == {END}
    assert not any(r.source == END for r in graph.routes)
    assert graph_items(graph) == graph_items(prefix)
    owned = graph_items(graph) | {PERMISSION}
    result = graph.evaluate(SourcePolicy({"mode": 0}), owned, True)
    assert all(result.reaches(n) for n in ("metal_205:209_top", "metal_228:chest", END))
    finals = [p for p in result.positions if p.node == END and p.equipped == "Hammer"]
    assert finals and all(not p.opened for p in finals)
    if witness == "bonkers_joint":
        assert all(p.consumed == {"0x088BF730"} for p in finals)
    for invalid in (replace(graph, placements=()),
                    replace(graph, starts=(Position("metal_228:chest"),)),
                    replace(graph, starts=(Position("metal_229:left_arrival"),))):
        assert not invalid.evaluate(SourcePolicy({"mode": 0}), owned, True).reaches(END)


@pytest.mark.parametrize("ability", sorted(METAL_BREAKING_ABILITIES | {"Normal"}))
def test_atomic_timed_switch_and_left_attack_do_not_export_permanent_openings(ability: str) -> None:
    graph = room_traversal_graph(TARGET, "bonkers_joint")
    isolated = replace(graph, placements=(), starts=(Position("metal_228:chest", ability),))
    assert isolated.evaluate(SourcePolicy({"mode": 0}), frozenset(), True).reaches(END) is (ability == "Hammer")
    carrier, metal = (r for r in graph.routes if r.target.startswith("metal_229:"))
    assert carrier.source == "metal_228:chest" and carrier.room_transition
    assert metal.source == "metal_229:left_arrival" and not metal.room_transition
    assert metal.capability == "metal" and metal.allowed_abilities == frozenset({"Hammer"})
    assert metal.water_state == "dry"
    for route in (carrier, metal):
        assert route.opens is None and route.uses_object is None
        assert not route.preserves_room_instance and not route.resets_room_instance
        assert not route.recover_dropped_ability


@pytest.mark.parametrize("witness", WITNESSES)
@pytest.mark.parametrize("mode,statues,minibosses,pool,weight", [
    (0, False, False, None, 0), (1, False, False, ["Stone"], 100),
    (1, True, True, ["Hammer"], 0), (1, True, True, ["Stone"], 0),
    (2, False, True, ["Hammer", "Stone"], 0), (2, True, True, ["Hammer", "Stone"], 0),
    (2, True, True, ["Hammer", "Stone"], 100), (2, True, True, ["Stone"], 0),
])
@pytest.mark.parametrize("gating,retries", [(False, False), (True, False), (False, True), (True, True)])
def test_joint_extension_preserves_actual_policy_and_renewal_requirements(
    witness: str, mode: int, statues: bool, minibosses: bool, pool: list[str] | None,
    weight: int, gating: bool, retries: bool,
) -> None:
    graph = room_traversal_graph(TARGET, witness, True)
    prefix = room_traversal_graph("metal_228_chest", witness, True)
    resolver = policy(mode, statues=statues, minibosses=minibosses, pool=pool,  # type: ignore[no-untyped-call]
                      weight=weight)
    for owned in (graph_items(graph) | {PERMISSION}, graph_items(graph)):
        result = graph.evaluate(resolver, owned, gating, allow_documented_retries=retries)
        previous = prefix.evaluate(resolver, owned, gating, allow_documented_retries=retries)
        assert result.reaches(END) == previous.reaches("metal_228:chest")
        assert frozenset(p for p in result.positions if not p.node.startswith("metal_229:")) == previous.positions
        assert result.retry_assumptions == previous.retry_assumptions


@pytest.mark.parametrize("access", [SOURCE_REGION, BONKERS_REGION, OWNER, None])
def test_generic229_access_never_supplies_equipment_or_the_left_arrival(
    monkeypatch: pytest.MonkeyPatch, access: str | None,
) -> None:
    monkeypatch.setattr(rules, "extra_traversal_targets", lambda: (row_for(),))
    location = SimpleNamespace(access_rule=lambda state: state.base)
    world = SimpleNamespace(
        player=1, _enemy_copy_ability_policy={"mode": 0}, _ability_gating_enabled=lambda: True,
        _area_keys_enabled=lambda: True,
        options=SimpleNamespace(ability_randomization_statues=SimpleNamespace(value=False)),
        multiworld=SimpleNamespace(get_location=lambda name, player: location,
                                   get_region=lambda name, player: name))
    rules.install_extra_traversal_rules(world)
    owned = {ACCESS, CONNECTION, AREA_KEY, PERMISSION}
    state = SimpleNamespace(base=True, has=lambda name, player: name in owned,
                            can_reach_region=lambda name, player: name == access)
    assert location.access_rule(state) is (access in {SOURCE_REGION, BONKERS_REGION})
    owned.remove(PERMISSION)
    assert not location.access_rule(state)
    owned.add(PERMISSION)
    state.base = False
    assert not location.access_rule(state)


@pytest.mark.parametrize("withheld", [ACCESS, CONNECTION, AREA_KEY, PERMISSION])
def test_actual229_location_cannot_unlock_its_own_copy_room_source(withheld: str) -> None:
    world = make_world(0, 1, area_keys=1)  # type: ignore[no-untyped-call]
    mw = world.multiworld
    for region in mw.regions:
        region.exits.clear()
    menu = mw.get_region("Menu", 1)
    menu.connect(mw.get_region(OWNER, 1))
    menu.connect(mw.get_region(SOURCE_REGION, 1))
    target = mw.get_location(data.locations[LOCATION].label, 1)
    state = CollectionState(mw)
    for name in {ACCESS, CONNECTION, AREA_KEY, PERMISSION}:
        while state.has(name, 1):
            state.remove(world.create_item(name))
        if name != withheld:
            state.collect(world.create_item(name), prevent_sweep=True)
    target.place_locked_item(world.create_item(withheld))
    state.sweep_for_advancements(locations=[target])
    assert not target.can_reach(state) and target not in state.advancements and not state.has(withheld, 1)
    state.collect(world.create_item(withheld), prevent_sweep=True)
    assert target.can_reach(state)
