"""Renewable real-hub Stone alternatives share the finite Bonkers target."""

from dataclasses import replace
from types import SimpleNamespace

import pytest
from BaseClasses import CollectionState, ItemClassification

from .. import enemy_ability_data, traversal, traversal_rules as rules
from ..data import data
from ..enemy_ability_data import GATEABLE_ENEMY_COPY_ABILITIES
from ..traversal import METAL_BREAKING_ABILITIES, Position, SourcePolicy
from ..traversal_data import graph_items, room_traversal_graph, room_traversal_targets
from .test_metal_room205 import HUB, MINOR23, OUTER, TARGET, TOP, metal_row
from .test_mini_traversal import make_world
from .test_traversal import policy


CENTRAL = "REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE"
RAINBOW = "REGION_RAINBOW_ROUTE/ROOM_1_HUB_1"
END = "metal_205:209_top"
CONNECTIONS = frozenset({"Rainbow Route East - Hub Connection", "Peppermint Palace East - Hub Connection"})
KEYS = frozenset({"Peppermint Palace - Area Key"})
PERMISSION = frozenset({"Stone Ability"})
WITNESSES = {
    "central_statues": (CENTRAL, "hub_801"),
    "rainbow190_statues": (RAINBOW, "hub_190"),
    "peppermint290_statues": (HUB, "hub_290"),
}


def simulate_stone_gating(monkeypatch: pytest.MonkeyPatch) -> None:
    """Exercise future permission removal without changing production starts."""
    gateable = tuple(sorted(set(GATEABLE_ENEMY_COPY_ABILITIES) | {"Stone"}))
    monkeypatch.setattr(enemy_ability_data, "GATEABLE_ENEMY_COPY_ABILITIES", gateable)
    monkeypatch.setattr(traversal, "GATEABLE_ENEMY_COPY_ABILITIES", gateable)
    monkeypatch.setattr(rules, "GATEABLE_ENEMY_COPY_ABILITIES", gateable)


@pytest.mark.parametrize("witness", WITNESSES)
@pytest.mark.parametrize("area_keys", [False, True])
def test_real190_source_uses_exact_connections_and_independent_start(
    monkeypatch: pytest.MonkeyPatch, witness: str, area_keys: bool,
) -> None:
    simulate_stone_gating(monkeypatch)
    graph = room_traversal_graph(TARGET, witness, area_keys)
    owned = CONNECTIONS | PERMISSION | (KEYS if area_keys else frozenset())
    resolver = SourcePolicy({"mode": 0})
    assert graph.evaluate(resolver, owned, True).reaches(END)
    for missing in owned:
        assert not graph.evaluate(resolver, owned - {missing}, True).reaches(END), missing
    assert graph.access_region == WITNESSES[witness][0]
    assert graph.starts == (Position(WITNESSES[witness][1]),)
    assert not graph.requires_all_hub_switches


@pytest.mark.parametrize("mode,statues,pool,weight,finite,retry", [
    (0, False, None, 0, True, True),
    (1, False, ["Burning"], 0, True, True),
    (1, True, ["Stone"], 0, True, True),
    (1, True, ["Burning"], 0, False, False),
    (2, False, ["Burning"], 100, True, True),
    (2, True, ["Stone"], 100, True, True),
    (2, True, ["Stone", "Burning"], 0, False, True),
    (2, True, ["Stone", "Burning"], 100, False, True),
    (2, True, ["Burning"], 0, False, False),
])
def test_statue_outcomes_and_retry_do_not_promote_a_mixed_finite_source(
    monkeypatch: pytest.MonkeyPatch, mode: int, statues: bool, pool: list[str] | None,
    weight: int, finite: bool, retry: bool,
) -> None:
    simulate_stone_gating(monkeypatch)
    resolver = policy(mode, statues=statues, pool=pool, weight=weight)  # type: ignore[no-untyped-call]
    graph = room_traversal_graph(TARGET, "central_statues")
    owned = CONNECTIONS | PERMISSION | {"Burning Ability"}
    assert graph.evaluate(resolver, owned, True).reaches(END) is finite
    result = graph.evaluate(resolver, owned, True, allow_documented_retries=True)
    assert result.reaches(END) is retry
    if retry and not finite:
        assert result.retry_assumptions
    row = dict(metal_row())
    row["graphs"] = {name: row["graphs"][name] for name in WITNESSES}
    monkeypatch.setattr(rules, "extra_traversal_targets", lambda: (row,))
    assert rules.target_applies(row, resolver)
    assert rules.static_extra_witness(resolver) is finite


def test_actual_statue_identity_no_synthetic_source_or_boss_reacquisition() -> None:
    graph = room_traversal_graph(TARGET, "central_statues")
    source = next(s for s in graph.placements if s.identity == "0x088B7CEC")
    fixture = next(s for s in graph.placements if s.identity == "0x088C0ED0")
    native = SourcePolicy({"mode": 0})
    assert (source.source_key, source.node) == ("STATUE:353900", "hub_190")
    assert source.renewable and source.retry_evidence
    assert native.grant(source.source_key, lambda _: True).guaranteed == {"Stone"}
    assert fixture.source_key == "STATUE:353905"
    assert native.grant(fixture.source_key, lambda _: True).guaranteed == {"Ice"}
    assert all(s.source_key.startswith("STATUE:") and s.renewable for s in graph.placements)
    assert not any(s.node.startswith("metal_205:") for s in graph.placements)
    owned = graph_items(graph) | PERMISSION
    for invalid in (replace(graph, placements=()),
                    replace(graph, placements=(replace(source, node=END),)),
                    replace(graph, starts=(Position("metal_205:stone_floor_launch"),))):
        assert not invalid.evaluate(native, owned, True).reaches(END)


@pytest.mark.parametrize("ability", sorted(METAL_BREAKING_ABILITIES | {"Normal"}))
def test_stone_suffix_is_continuous_and_cannot_start_transformation_underwater(ability: str) -> None:
    graph = room_traversal_graph(TARGET, "central_statues")
    routes = tuple(r for r in graph.routes if r.target.startswith("metal_205:"))
    assert len(routes) == 4
    assert {(r.source, r.target) for r in routes if r.room_transition} == {
        ("hub_290", "metal_205:stone_210_lower"),
        ("metal_205:stone_210_lower", "metal_205:stone_floor_launch"),
        ("metal_205:stone_door_threshold", END),
    }
    metal, = (r for r in routes if r.capability)
    assert metal.allowed_abilities == frozenset({"Stone"}) and metal.water_state == "dry"
    assert not metal.room_transition
    assert all(r.opens is None and not r.recover_dropped_ability and r.uses_object is None
               and not r.preserves_room_instance and not r.resets_room_instance for r in routes)
    assert not any(r.source == END for r in graph.routes)
    isolated = replace(graph, placements=(), routes=routes, starts=(Position("hub_290", ability),))
    result = isolated.evaluate(SourcePolicy({"mode": 0}), frozenset(), True)
    assert result.reaches(END) is (ability == "Stone")
    assert {p.equipped for p in result.positions if p.node == END} <= {"Normal", "Stone"}
    underwater = replace(isolated, routes=tuple(
        replace(r, water_state="swimming") if r.capability else r for r in routes))
    assert not underwater.evaluate(SourcePolicy({"mode": 0}), frozenset(), True).reaches(END)


@pytest.mark.parametrize("access", [CENTRAL, RAINBOW, HUB, OUTER, None])
def test_one_target_ors_four_source_access_alternatives_and_preserves_base_rule(
    monkeypatch: pytest.MonkeyPatch, access: str | None,
) -> None:
    simulate_stone_gating(monkeypatch)
    row = metal_row()
    assert "requires_guaranteed_source" not in row
    assert set(row["graphs"]) == set(WITNESSES) | {"bonkers_carry"}
    assert len([r for r in room_traversal_targets("metal") if r.get("exit") == TOP]) == 1
    monkeypatch.setattr(rules, "extra_traversal_targets", lambda: (row,))
    target = SimpleNamespace(access_rule=lambda state: state.base)
    indirect: set[str] = set()
    world = SimpleNamespace(
        player=1, _enemy_copy_ability_policy={"mode": 0}, _ability_gating_enabled=lambda: True,
        _area_keys_enabled=lambda: True,
        options=SimpleNamespace(ability_randomization_statues=SimpleNamespace(value=False)),
        multiworld=SimpleNamespace(get_entrance=lambda name, player: target, get_region=lambda name, player: name,
                                   register_indirect_condition=lambda name, entrance: indirect.add(name)))
    rules.install_extra_traversal_rules(world)
    owned = set(CONNECTIONS | KEYS | PERMISSION)
    state = SimpleNamespace(base=True, has=lambda name, player: name in owned,
                            can_reach_region=lambda name, player: name == access)
    assert target.access_rule(state) is (access in {CENTRAL, RAINBOW, HUB})
    assert indirect == {CENTRAL, RAINBOW, HUB, OUTER}
    owned.clear()
    owned.add("Hammer Ability")
    assert target.access_rule(state) is (access == OUTER)
    state.base = False
    assert not target.access_rule(state)


@pytest.mark.parametrize("withheld", ["Stone Ability", "Rainbow Route East - Hub Connection"])
def test_actual_ap_source_permission_and_connection_do_not_unlock_their_own_top_check(
    monkeypatch: pytest.MonkeyPatch, withheld: str,
) -> None:
    simulate_stone_gating(monkeypatch)
    world = make_world(0, 1, area_keys=1)  # type: ignore[no-untyped-call]
    mw = world.multiworld
    for region in mw.regions:
        region.exits = [edge for edge in region.exits
                        if region.name == OUTER and edge.connected_region.name == TOP]
    menu = mw.get_region("Menu", 1)
    menu.connect(mw.get_region(OUTER, 1))
    menu.connect(mw.get_region(CENTRAL, 1))
    target = mw.get_location(data.locations[MINOR23].label, 1)
    state = CollectionState(mw)
    for name in CONNECTIONS | KEYS | PERMISSION | {"Hammer Ability"}:
        while state.has(name, 1):
            state.remove(world.create_item(name))
        if name not in {withheld, "Hammer Ability"}:
            state.collect(world.create_item(name), prevent_sweep=True)
    item = world.create_item(withheld)
    item.classification = ItemClassification.progression
    target.place_locked_item(item)
    state.sweep_for_advancements(locations=[target])
    assert not target.can_reach(state) and target not in state.advancements
    assert not state.has(withheld, 1)
    state.collect(world.create_item(withheld), prevent_sweep=True)
    assert target.can_reach(state)


@pytest.mark.parametrize("statues", [False, True])
def test_full_live_boss_pool_keeps_supported_renewable_basis(statues: bool) -> None:
    world = make_world(2, 1, ability_randomization_statues=statues,  # type: ignore[no-untyped-call]
                       ability_randomization_minibosses=True)
    resolver = SourcePolicy(world._enemy_copy_ability_policy, statues)
    bonkers = room_traversal_graph(TARGET, "bonkers_carry")
    owned = graph_items(bonkers) | {"Hammer Ability"}
    assert not bonkers.evaluate(resolver, owned, True, allow_documented_retries=True).reaches(END)
    graph = room_traversal_graph(TARGET, "central_statues")
    owned = graph_items(graph) | PERMISSION
    assert graph.evaluate(resolver, owned, True, allow_documented_retries=True).reaches(END)


@pytest.mark.parametrize("ability,expected", [("Stone", True), ("Burning", False)])
def test_disabled_gating_does_not_create_equipment(ability: str, expected: bool) -> None:
    graph = room_traversal_graph(TARGET, "peppermint290_statues")
    resolver = policy(1, statues=True, pool=[ability])  # type: ignore[no-untyped-call]
    assert graph.evaluate(resolver, frozenset(), False).reaches(END) is expected


@pytest.mark.parametrize("accessibility", ["full", "minimal"])
def test_unsupported_assignment_is_rejected_or_closed_never_legacy_fallback(
    monkeypatch: pytest.MonkeyPatch, accessibility: str,
) -> None:
    from Options import Accessibility

    monkeypatch.setattr(rules, "extra_traversal_targets", lambda: (metal_row(),))
    resolver = policy(1, statues=True, minibosses=True, pool=["Burning"])  # type: ignore[no-untyped-call]
    assert not rules.static_extra_witness(resolver)
    target = SimpleNamespace(access_rule=lambda state: True)
    world = SimpleNamespace(
        player=1, _enemy_copy_ability_policy=resolver.policy, _ability_gating_enabled=lambda: False,
        _area_keys_enabled=lambda: False,
        options=SimpleNamespace(ability_randomization_statues=SimpleNamespace(value=True),
                                accessibility=Accessibility.from_any(accessibility)),
        multiworld=SimpleNamespace(get_entrance=lambda name, player: target, get_region=lambda name, player: name,
                                   register_indirect_condition=lambda name, entrance: None))
    if accessibility == "full":
        with pytest.raises(ValueError, match="No reviewed source witness for metal_205_to_209_top"):
            rules.install_extra_traversal_rules(world)
    else:
        rules.install_extra_traversal_rules(world)
        state = SimpleNamespace(has=lambda name, player: True, can_reach_region=lambda name, player: True)
        assert not target.access_rule(state)
