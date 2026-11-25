"""The joint228 carrier starts from actual item-gated970 statues, never its fixture."""

from dataclasses import replace
from types import SimpleNamespace
from typing import Any

import pytest
from BaseClasses import CollectionState

from .. import traversal_rules as rules
from ..data import data
from ..traversal import Position, SourcePolicy
from ..traversal_data import graph_items, room_traversal_graph, room_traversal_targets
from .test_metal_room228 import END, LOCATION, OWNER
from .test_mini_traversal import make_world
from .test_traversal import policy


TARGET = "metal_228_chest"
SOURCE_REGION = "REGION_COPY_ABILITY_ROOM/MAIN"
BONKERS_REGION = "REGION_PEPPERMINT_PALACE/ROOM_7_07"
ACCESS = "Copy Ability Room Access"
CONNECTION = "Peppermint Palace East - Hub Connection"
AREA_KEY = "Peppermint Palace - Area Key"
PERMISSION = "Hammer Ability"


def row_for() -> dict[str, Any]:
    return next(row for row in room_traversal_targets("metal") if row["id"] == TARGET)


@pytest.mark.parametrize("keys", [False, True])
def test_independent970_access_does_not_replace_item_connection_permission_or_key(keys: bool) -> None:
    graph = room_traversal_graph(TARGET, "copy_room_statues", keys)
    owned = frozenset({ACCESS, CONNECTION, PERMISSION} | ({AREA_KEY} if keys else set()))
    resolver = SourcePolicy({"mode": 0})
    assert graph.access_region == SOURCE_REGION and graph.starts == (Position("metal_228:970"),)
    assert not graph.requires_all_hub_switches
    assert graph_items(graph) == owned - {PERMISSION}
    assert graph.evaluate(resolver, owned, True).reaches(END)
    for missing in owned:
        assert not graph.evaluate(resolver, owned - {missing}, True).reaches(END), missing


def test_only_real970_sources_are_present_with_original_outcomes_and_renewal() -> None:
    graph = room_traversal_graph(TARGET, "copy_room_statues")
    assert len(graph.placements) == 19 and len(graph.nodes) == 13 and len(graph.routes) == 12
    assert all(s.node == "metal_228:970" and s.renewable and s.retry_evidence for s in graph.placements)
    assert all(s.requirements == {ACCESS} for s in graph.placements)
    source, = (s for s in graph.placements if s.identity == "0x088D5FA0")
    assert source.source_key == "STATUE:35390A"
    resolver = SourcePolicy({"mode": 0})
    assert resolver.grant(source.source_key, lambda _: True).guaranteed == {"Hammer"}
    assert not any(s.identity in {"0x088C0ED0", "0x088BF730", "0x088BF7E4"} for s in graph.placements)
    assert {n.room for n in graph.nodes} == {970, 801, 290, 210, 227, 204, 203, 205, 209, 228}
    assert all(r.opens is None and not r.resets_room_instance and not r.preserves_room_instance
               and not r.recover_dropped_ability for r in graph.routes)
    assert not any(r.source == END for r in graph.routes)
    owned = graph_items(graph) | {PERMISSION}
    for invalid in (replace(graph, placements=()),
                    replace(graph, placements=(replace(source, node=END),)),
                    replace(graph, starts=(Position("metal_228:290"),))):
        assert not invalid.evaluate(resolver, owned, True).reaches(END)


@pytest.mark.parametrize("mode,statues,pool,weight", [
    (0, False, None, 0), (1, False, ["Burning"], 0), (1, True, ["Hammer"], 0),
    (1, True, ["Stone"], 0), (2, False, ["Stone"], 100), (2, True, ["Hammer"], 100),
    (2, True, ["Hammer", "Stone"], 0), (2, True, ["Hammer", "Stone"], 100),
    (2, True, ["Stone"], 0),
])
def test_room970_native_hammer_never_depends_on_world_pool_or_retry(
    mode: int, statues: bool, pool: list[str] | None, weight: int,
) -> None:
    graph = room_traversal_graph(TARGET, "copy_room_statues")
    resolver = policy(mode, statues=statues, pool=pool, weight=weight)
    owned = graph_items(graph) | {PERMISSION, "Stone Ability"}
    for retries in (False, True):
        result = graph.evaluate(resolver, owned, True, allow_documented_retries=retries)
        assert result.reaches(END) and not result.retry_assumptions
        assert not graph.evaluate(resolver, owned - {PERMISSION}, True,
                                  allow_documented_retries=retries).reaches(END)


@pytest.mark.parametrize("access", [SOURCE_REGION, BONKERS_REGION, OWNER, None])
def test_one_target_ors_independent_sources_and_preserves_base_rule(
    monkeypatch: pytest.MonkeyPatch, access: str | None,
) -> None:
    row = row_for()
    monkeypatch.setattr(rules, "extra_traversal_targets", lambda: (row,))
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
    owned.remove(ACCESS)
    assert location.access_rule(state) is (access == BONKERS_REGION)
    state.base = False
    assert not location.access_rule(state)


@pytest.mark.parametrize("withheld", [ACCESS, CONNECTION, AREA_KEY, PERMISSION])
def test_actual_ap228_check_cannot_unlock_its_own_source_access(withheld: str) -> None:
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
    assert not target.can_reach(state) and target not in state.advancements
    assert not state.has(withheld, 1)
    state.collect(world.create_item(withheld), prevent_sweep=True)
    assert target.can_reach(state)


@pytest.mark.parametrize("statues", [False, True])
def test_full_live_miniboss_pool_retains_renewable_basis(statues: bool) -> None:
    world = make_world(2, 1, ability_randomization_statues=statues,  # type: ignore[no-untyped-call]
                       ability_randomization_minibosses=True)
    resolver = SourcePolicy(world._enemy_copy_ability_policy, statues)
    finite = room_traversal_graph(TARGET, "bonkers_joint")
    assert not finite.evaluate(resolver, frozenset({PERMISSION}), True,
                               allow_documented_retries=True).reaches(END)
    renewable = room_traversal_graph(TARGET, "copy_room_statues")
    assert renewable.evaluate(resolver, graph_items(renewable) | {PERMISSION}, True,
                              allow_documented_retries=True).reaches(END)


@pytest.mark.parametrize("accessibility", ["full", "minimal"])
def test_unsupported_outside_policy_keeps_only_the_independent_fixed_room_witness(
    monkeypatch: pytest.MonkeyPatch, accessibility: str,
) -> None:
    from Options import Accessibility

    row = row_for()
    monkeypatch.setattr(rules, "extra_traversal_targets", lambda: (row,))
    resolver = policy(1, statues=True, minibosses=True, pool=["Stone"])  # type: ignore[no-untyped-call]
    assert rules.static_extra_witness(resolver)
    location = SimpleNamespace(access_rule=lambda state: True)
    world = SimpleNamespace(
        player=1, _enemy_copy_ability_policy=resolver.policy, _ability_gating_enabled=lambda: False,
        _area_keys_enabled=lambda: False,
        options=SimpleNamespace(ability_randomization_statues=SimpleNamespace(value=True),
                                accessibility=Accessibility.from_any(accessibility)),
        multiworld=SimpleNamespace(get_location=lambda name, player: location))
    rules.install_extra_traversal_rules(world)
    def reaches(region: str, owns_access: bool) -> bool:
        return location.access_rule(SimpleNamespace(
            has=lambda name, player: name != ACCESS or owns_access,
            can_reach_region=lambda name, player: name == region,
        ))

    assert reaches(SOURCE_REGION, True)
    assert not reaches(SOURCE_REGION, False)
    assert not reaches(BONKERS_REGION, True)
