"""216 accepts only the reviewed statue-backed Burning chest branch."""

from dataclasses import replace
import random
from types import SimpleNamespace
from typing import Any

import pytest
from BaseClasses import CollectionState, ItemClassification

from .. import traversal_rules as rules
from ..data import data
from ..traversal import METAL_BREAKING_ABILITIES, Position, SourcePolicy
from ..traversal_data import graph_items, room_traversal_graph, room_traversal_targets
from .test_metal_goal2 import simulate_burning_gating
from .test_mini_traversal import make_world
from .test_traversal import policy


TARGET = "metal_216_chest"
OWNER = "REGION_PEPPERMINT_PALACE/ROOM_7_19"
LOCATION = "MINOR_CHEST_PEPPERMINT_PALACE_7_19"
CENTRAL = "REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE"
PEPPERMINT = "REGION_PEPPERMINT_PALACE/ROOM_7_HUB_2"
END = "metal_216:chest"
CONNECTIONS = frozenset({"Peppermint Palace East - Hub Connection", "Peppermint Palace West - Hub Connection"})
KEYS = frozenset({"Peppermint Palace - Area Key"})
PERMISSION = frozenset({"Burning Ability"})
WITNESSES = {"central_statues": CENTRAL, "peppermint291_statues": PEPPERMINT}


def target_row() -> dict[str, Any]:
    return next(row for row in room_traversal_targets("metal") if row["id"] == TARGET)


@pytest.mark.parametrize("witness", WITNESSES)
@pytest.mark.parametrize("area_keys", [False, True])
def test_minimal_real291_route_and_exact_missing_guards(
    monkeypatch: pytest.MonkeyPatch, witness: str, area_keys: bool,
) -> None:
    simulate_burning_gating(monkeypatch)
    graph = room_traversal_graph(TARGET, witness, area_keys)
    required = (CONNECTIONS if witness == "central_statues" else frozenset()) | PERMISSION
    if area_keys:
        required |= KEYS if witness == "central_statues" else frozenset()
    resolver = SourcePolicy({"mode": 0})
    assert graph.evaluate(resolver, required, True).reaches(END)
    for missing in required:
        assert not graph.evaluate(resolver, required - {missing}, True).reaches(END), missing
    # No all-hub, Copy Ability Room or unrelated area item is necessary.
    assert graph.access_region == WITNESSES[witness]
    assert not graph.requires_all_hub_switches
    assert graph.starts == (Position("hub_801" if witness == "central_statues" else "hub_291"),)


@pytest.mark.parametrize("mode,statues,pool,weight,finite,retry", [
    (0, False, None, 0, True, True),
    (1, False, ["Hammer"], 0, True, True),
    (1, True, ["Burning"], 0, True, True),
    (1, True, ["Hammer"], 0, False, False),
    (2, False, ["Hammer"], 100, True, True),
    (2, True, ["Burning"], 100, True, True),
    (2, True, ["Burning", "Hammer"], 0, False, True),
    (2, True, ["Burning", "Hammer"], 100, False, True),
    (2, True, ["Hammer"], 0, False, False),
])
def test_exact_statue_policy_and_documented_retouch_only(
    monkeypatch: pytest.MonkeyPatch, mode: int, statues: bool, pool: list[str] | None,
    weight: int, finite: bool, retry: bool,
) -> None:
    simulate_burning_gating(monkeypatch)
    resolver = policy(mode, statues=statues, pool=pool, weight=weight)  # type: ignore[no-untyped-call]
    graph = room_traversal_graph(TARGET, "central_statues")
    owned = CONNECTIONS | PERMISSION | {"Hammer Ability"}
    assert graph.evaluate(resolver, owned, True).reaches(END) is finite
    result = graph.evaluate(resolver, owned, True, allow_documented_retries=True)
    assert result.reaches(END) is retry
    if retry and not finite:
        assert result.retry_assumptions
    # This target is unconditional: unsupported policies cannot fall back to a
    # legacy ungated check. Mode1 feasibility may resample whole policies.
    assert rules.target_applies(target_row(), resolver)
    monkeypatch.setattr(rules, "extra_traversal_targets", lambda: (target_row(),))
    assert rules.static_extra_witness(resolver) is finite


def test_source_identity_and_no_synthetic212_or_local_enemy_credit() -> None:
    graph = room_traversal_graph(TARGET, "central_statues")
    source = next(source for source in graph.placements if source.identity == "0x088C263C")
    assert source.source_key == "STATUE:3538FD" and source.node == "hub_291"
    assert source.renewable and source.retry_evidence
    native = SourcePolicy({"mode": 0})
    assert native.grant(source.source_key, lambda _: True).guaranteed == {"Burning"}
    assert all(source.source_key.startswith("STATUE:") for source in graph.placements)
    assert not any(source.node.startswith("metal_216:") for source in graph.placements)
    assert not any(source.identity == "0x088C103C" for source in graph.placements)
    owned = graph_items(graph) | PERMISSION
    assert not replace(graph, placements=()).evaluate(native, owned, True).reaches(END)
    assert not replace(graph, placements=(replace(source, node=END),)).evaluate(native, owned, True).reaches(END)
    assert not replace(graph, starts=(Position("metal_216:216_right_arrival"),)).evaluate(
        native, owned, True).reaches(END)


@pytest.mark.parametrize("ability", sorted(METAL_BREAKING_ABILITIES | {"Normal"}))
def test_suffix_requires_continuous_burning_and_never_reexports_state(ability: str) -> None:
    graph = room_traversal_graph(TARGET, "central_statues")
    routes = tuple(route for route in graph.routes if route.target.startswith("metal_216:"))
    assert len(routes) == 4
    assert {(route.source, route.target) for route in routes if route.room_transition} == {
        ("hub_291", "metal_216:215_arrival"),
        ("metal_216:215_arrival", "metal_216:212_arrival"),
        ("metal_216:212_arrival", "metal_216:216_right_arrival"),
    }
    final = next(route for route in routes if route.target == END)
    assert final.source == "metal_216:216_right_arrival"
    assert final.capability == "metal" and final.allowed_abilities == frozenset({"Burning"})
    assert all(route.opens is None and not route.recover_dropped_ability and route.uses_object is None
               and not route.preserves_room_instance and not route.resets_room_instance for route in routes)
    assert not any(route.source == END for route in graph.routes)
    isolated = replace(graph, placements=(), routes=routes, starts=(Position("hub_291", ability),))
    result = isolated.evaluate(SourcePolicy({"mode": 0}), frozenset(), True)
    assert result.reaches(END) is (ability == "Burning")
    assert {position.equipped for position in result.positions if position.node == END} <= {"Normal", "Burning"}
    assert any(p.node == END and p.equipped == "Burning" for p in result.positions) is (ability == "Burning")
    underwater = replace(isolated, routes=tuple(
        replace(route, water_state="swimming") if route.capability else route for route in routes))
    assert not underwater.evaluate(SourcePolicy({"mode": 0}), frozenset(), True).reaches(END)


@pytest.mark.parametrize("access", [CENTRAL, PEPPERMINT, None])
def test_one_installed_target_ors_access_alternatives_and_keeps_base_rule(
    monkeypatch: pytest.MonkeyPatch, access: str | None,
) -> None:
    simulate_burning_gating(monkeypatch)
    row = target_row()
    assert row["region"] == OWNER and row["location"] == LOCATION
    assert "requires_guaranteed_source" not in row
    assert len([r for r in room_traversal_targets("metal") if r.get("location") == LOCATION]) == 1
    monkeypatch.setattr(rules, "extra_traversal_targets", lambda: (row,))
    target = SimpleNamespace(access_rule=lambda state: state.base)
    indirect: list[str] = []
    world = SimpleNamespace(
        player=1, _enemy_copy_ability_policy={"mode": 0},
        _ability_gating_enabled=lambda: True, _area_keys_enabled=lambda: True,
        options=SimpleNamespace(ability_randomization_statues=SimpleNamespace(value=False)),
        multiworld=SimpleNamespace(
            get_location=lambda name, player: target, get_region=lambda name, player: name,
            register_indirect_condition=lambda name, entrance: indirect.append(name),
        ),
    )
    rules.install_extra_traversal_rules(world)
    owned = set(CONNECTIONS | KEYS | PERMISSION)
    state = SimpleNamespace(base=True, has=lambda name, player: name in owned,
                            can_reach_region=lambda name, player: name == access)
    assert target.access_rule(state) is (access is not None)
    assert not indirect  # Location rules are evaluated on demand, not entrance fixed-point edges.
    owned.remove("Burning Ability")
    assert not target.access_rule(state)
    owned.add("Burning Ability")
    state.base = False
    assert not target.access_rule(state)


@pytest.mark.parametrize("withheld", ["Burning Ability", "Peppermint Palace West - Hub Connection"])
def test_actual_ap_permission_and_hub_item_cannot_unlock_their_own_chest(
    monkeypatch: pytest.MonkeyPatch, withheld: str,
) -> None:
    simulate_burning_gating(monkeypatch)
    world = make_world(0, 1)  # type: ignore[no-untyped-call]
    multiworld = world.multiworld
    # Isolate independent Central access. No unrelated overland route may make
    # 291 reachable in this deliberately small self-lock fixture.
    for region in multiworld.regions:
        region.exits.clear()
    menu = multiworld.get_region("Menu", 1)
    menu.connect(multiworld.get_region(OWNER, 1))
    menu.connect(multiworld.get_region(CENTRAL, 1))
    target = multiworld.get_location(data.locations[LOCATION].label, 1)
    state = CollectionState(multiworld)
    for name in CONNECTIONS | KEYS | PERMISSION:
        while state.has(name, 1):
            state.remove(world.create_item(name))
        if name != withheld:
            state.collect(world.create_item(name), prevent_sweep=True)
    item = world.create_item(withheld)
    item.classification = ItemClassification.progression  # Future permission contract fixture only.
    target.place_locked_item(item)
    state.sweep_for_advancements(locations=[target])
    assert not target.can_reach(state) and target not in state.advancements
    assert not state.has(withheld, 1)
    state.collect(world.create_item(withheld), prevent_sweep=True)
    assert target.can_reach(state)


def test_chest_binding_keeps_both_ordinary_exits_and_room_check() -> None:
    world = make_world(0, 1, room_sanity=True)  # type: ignore[no-untyped-call]
    room = data.regions[OWNER]
    assert set(room.exits) == {"REGION_PEPPERMINT_PALACE/ROOM_7_18", "REGION_PEPPERMINT_PALACE/ROOM_7_20"}
    state = CollectionState(world.multiworld)
    for destination in room.exits:
        assert world.multiworld.get_entrance(f"{OWNER} -> {destination}", 1).access_rule(state)
    assert data.locations[LOCATION].source_rom_offset == 0x8C1380
    checks = [location for location in world.multiworld.get_region(OWNER, 1).locations
              if location.address == 3961191]
    assert len(checks) == 1 and checks[0].access_rule(state)


@pytest.mark.parametrize("ability,expected", [("Burning", True), ("Hammer", False)])
def test_gating_off_still_requires_actual_physical_burning(ability: str, expected: bool) -> None:
    graph = room_traversal_graph(TARGET, "peppermint291_statues")
    resolver = policy(1, statues=True, pool=[ability])  # type: ignore[no-untyped-call]
    assert graph.evaluate(resolver, frozenset(), False).reaches(END) is expected


def test_disabled_location_category_does_not_install_a_different_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rules, "extra_traversal_targets", lambda: (target_row(),))

    def missing_location(name: str, player: int) -> None:
        assert name == data.locations[LOCATION].label and player == 1
        raise KeyError(name)

    world = SimpleNamespace(
        player=1, _enemy_copy_ability_policy={"mode": 0}, _ability_gating_enabled=lambda: True,
        options=SimpleNamespace(ability_randomization_statues=SimpleNamespace(value=False)),
        multiworld=SimpleNamespace(get_location=missing_location),
    )
    rules.install_extra_traversal_rules(world)


def test_shuffled_selection_resamples_whole_policy_without_rewriting_sources(monkeypatch: pytest.MonkeyPatch) -> None:
    from .. import peg_traversal, wheel_traversal
    from ..ability_randomization import build_enemy_copy_ability_policy

    wrong, good = (build_enemy_copy_ability_policy(random.Random(seed), 1, True, True,
                                                   include_passive_enemies=True) for seed in (0, 1))
    assert {key: value for key, value in wrong.items() if key != "seed"} == {
        key: value for key, value in good.items() if key != "seed"}
    monkeypatch.setattr(peg_traversal, "PEG_ROUTES", ())
    monkeypatch.setattr(wheel_traversal, "static_wheel_witness", lambda _: True)
    monkeypatch.setattr(rules, "extra_traversal_targets", lambda: (target_row(),))
    calls: list[int] = []

    def candidate() -> dict[str, Any]:
        calls.append(1)
        return good

    assert peg_traversal.validate_peg_assignment(wrong, candidate, True, max_attempts=2) is good
    assert calls == [1]
    with pytest.raises(ValueError, match="search budget exhausted"):
        peg_traversal.validate_peg_assignment(wrong, lambda: wrong, True, max_attempts=2)


@pytest.mark.parametrize("accessibility", ["full", "minimal"])
def test_unsupported_statue_policy_rejects_or_stays_closed_without_fallback(
    monkeypatch: pytest.MonkeyPatch, accessibility: str,
) -> None:
    from Options import Accessibility

    monkeypatch.setattr(rules, "extra_traversal_targets", lambda: (target_row(),))
    resolver = policy(1, statues=True, pool=["Hammer"])  # type: ignore[no-untyped-call]
    target = SimpleNamespace(access_rule=lambda state: True)
    world = SimpleNamespace(
        player=1, _enemy_copy_ability_policy=resolver.policy,
        _ability_gating_enabled=lambda: False, _area_keys_enabled=lambda: False,
        options=SimpleNamespace(ability_randomization_statues=SimpleNamespace(value=True),
                                accessibility=Accessibility.from_any(accessibility)),
        multiworld=SimpleNamespace(
            get_location=lambda name, player: target, get_region=lambda name, player: name,
            register_indirect_condition=lambda name, entrance: None,
        ),
    )
    if accessibility == "full":
        with pytest.raises(ValueError, match="No reviewed source witness for metal_216_chest"):
            rules.install_extra_traversal_rules(world)
    else:
        rules.install_extra_traversal_rules(world)
        state = SimpleNamespace(has=lambda name, player: True, can_reach_region=lambda name, player: True)
        assert not target.access_rule(state)
