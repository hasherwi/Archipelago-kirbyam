"""Finite Sparky carry and exact upper-left access for the optional Green Paint."""

import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from BaseClasses import CollectionState, ItemClassification
from test.general import setup_multiworld

from .. import KirbyAmWorld, traversal_rules as rules
from ..data import data
from ..traversal import Grant, SourcePolicy
from ..traversal_data import room_traversal_graph, room_traversal_targets
from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive
from .test_mini_traversal import make_world
from .test_traversal import policy

OWNER = "REGION_RAINBOW_ROUTE/ROOM_1_28"
UPSTREAM = "REGION_RAINBOW_ROUTE/ROOM_1_27_UPPER_LEFT"
TARGET = "bomb_138_green"
CHEST = "MINOR_CHEST_SPRAY_PAINT_04"
EVIDENCE = Path(__file__).parents[1] / "dev-docs" / "rainbow-green-source-runtime.json"
POLICIES = [
    (0, None, 0, True), (1, ["Spark"], 0, True), (1, ["Beam"], 0, False),
    (2, ["Spark"], 0, True), (2, ["Spark", "Beam"], 0, False),
    (2, ["Spark"], 50, False), (2, ["Spark"], 100, False), (2, None, 0, False),
]


def target_row():
    return next(row for row in room_traversal_targets("block") if row["id"] == TARGET)


@pytest.mark.parametrize("mode,pool,weight,applies", POLICIES)
@pytest.mark.parametrize("gating", [0, 1])
@pytest.mark.parametrize("statues", [0, 1])
def test_actual_world_guaranteed_source_policy_and_classification(
        monkeypatch, mode, pool, weight, applies, gating, statues):
    resolver = policy(mode, pool=pool, weight=weight, statues=statues, minny=False)
    # Deliberately restricted policy fixtures isolate rule wiring. They do not
    # assert a fully accessible generation or randomized native replay.
    monkeypatch.setattr("worlds.kirbyam.build_enemy_copy_ability_policy", lambda *a, **kw: resolver.policy)
    world = make_world(mode, gating, accessibility="minimal", ability_randomization_statues=statues,
                       ability_randomization_no_ability_weight=weight)
    assert rules.target_applies(target_row(), SourcePolicy(world._enemy_copy_ability_policy, bool(statues))) is applies
    chest = world.multiworld.get_location(data.locations[CHEST].label, 1)
    state = CollectionState(world.multiworld)
    # Owner, generic room 532 and upper-right are not the proved entry.
    state.can_reach_region = lambda name, player: name in {
        OWNER, "REGION_RAINBOW_ROUTE/ROOM_1_27", "REGION_RAINBOW_ROUTE/ROOM_1_27_UPPER_RIGHT"}
    assert chest.access_rule(state) is (not applies)
    state.collect(world.create_item("Spark Ability"), prevent_sweep=True)
    assert chest.access_rule(state) is (not applies)
    state.can_reach_region = lambda name, player: name == UPSTREAM
    assert chest.access_rule(state)
    state.remove(world.create_item("Spark Ability"))
    assert chest.access_rule(state) is (not applies or not gating)
    assert world.create_item("Spark Ability").classification == (
        ItemClassification.progression if applies and gating else ItemClassification.useful)


@pytest.mark.parametrize("grant", [
    Grant(frozenset()), Grant(frozenset({"Normal"})), Grant(frozenset({"Unknown"})),
    Grant(frozenset({"Spark", "Beam"}), randomized=True),
    Grant(frozenset({"Spark"}), randomized=True, can_fail=True),
])
def test_uncertain_source_grants_retain_prior_partial_behavior(grant):
    assert not rules.target_applies(target_row(), SimpleNamespace(grant=lambda *args: grant))


@pytest.mark.parametrize("gating", [False, True])
@pytest.mark.parametrize("area_keys", [False, True])
def test_finite_source_and_equipment_are_required(gating, area_keys):
    graph = room_traversal_graph(TARGET, "upper_left_entry", area_keys)
    resolver = SourcePolicy(json.loads(EVIDENCE.read_text())["source"]["source_policy"])
    row = target_row()
    assert (row["region"], row["native_room"], row["location"]) == (OWNER, 138, CHEST)
    assert "exit" not in row
    assert graph.access_region == UPSTREAM
    assert all(start.equipped == "Normal" for start in graph.starts)
    assert [(node.key.rsplit(":", 1)[-1], node.room) for node in graph.nodes] == [
        ("upper_left", 532), ("arrival", 138), ("source", 138), ("chest", 138)]
    source, = graph.placements
    assert (source.identity, source.source_key, source.renewable, source.retry_evidence) == (
        "0x088B9F90", "SPARKY", False, None)
    assert [route.capability for route in graph.routes] == [None, None, TARGET]
    assert all(route.opens is None and not route.items and not route.recover_dropped_ability for route in graph.routes)
    assert [route.resets_room_instance for route in graph.routes] == [True, False, False]
    target, = graph.required_targets
    owned = frozenset({"Spark Ability"})
    assert graph.evaluate(resolver, frozenset(), gating).reaches(target) is (not gating)
    assert graph.evaluate(resolver, owned, gating).reaches(target)
    assert not replace(graph, placements=()).evaluate(resolver, owned, gating).reaches(target)
    behind = replace(graph, placements=(replace(source, node=target),))
    assert not behind.evaluate(resolver, owned, gating).reaches(target)
    for unsupported in (policy(1, pool=["Beam"]), policy(2, pool=["Spark", "Beam"]),
                        policy(2, pool=["Spark"], weight=50), policy(2, pool=["Spark"], weight=100)):
        result = graph.evaluate(unsupported, owned, gating, allow_documented_retries=True)
        assert not result.reaches(target) and not result.retry_assumptions


@pytest.mark.parametrize("gating", [0, 1])
@pytest.mark.parametrize("area_keys", [0, 1])
@pytest.mark.parametrize("statues", [0, 1])
@pytest.mark.parametrize("room_sanity", [0, 1])
@pytest.mark.parametrize("minor_chests", [False, True])
def test_optional_chest_preserves_exits_room_sanity_and_area_keys(
        monkeypatch, gating, area_keys, statues, room_sanity, minor_chests):
    monkeypatch.setattr(KirbyAmWorld, "ENABLE_MINOR_CHESTS", minor_chests)
    raw = json.loads(EVIDENCE.read_text())["source"]["source_policy"]
    monkeypatch.setattr("worlds.kirbyam.build_enemy_copy_ability_policy", lambda *a, **kw: raw)
    multiworld = setup_multiworld(KirbyAmWorld, steps=("generate_early",), seed=138, options={
        "ability_randomization_mode": 0, "ability_gating": gating, "area_keys": area_keys,
        "ability_randomization_statues": statues, "room_sanity": room_sanity,
        "accessibility": "minimal",
    })
    world = multiworld.worlds[1]
    world.create_regions()
    world.set_rules()
    state = CollectionState(multiworld)
    state.can_reach_region = lambda name, player: name == OWNER
    if minor_chests:
        chest = multiworld.get_location(data.locations[CHEST].label, 1)
        assert (chest.address, chest.parent_region.name) == (3960503, OWNER)
        assert not chest.access_rule(state)
        state.collect(world.create_item("Spark Ability"), prevent_sweep=True)
        assert not chest.access_rule(state)
        state.remove(world.create_item("Spark Ability"))
        state.can_reach_region = lambda name, player: name == UPSTREAM
        assert chest.access_rule(state) is (not gating)
        state.collect(world.create_item("Spark Ability"), prevent_sweep=True)
        assert chest.access_rule(state)
        state.remove(world.create_item("Spark Ability"))
        assert chest.access_rule(state) is (not gating)
    else:
        with pytest.raises(KeyError):
            multiworld.get_location(data.locations[CHEST].label, 1)
    # Existing mandatory Room8 rule uses this same source policy, even without
    # optional paint. No blanket classification or source eligibility change.
    assert world.create_item("Spark Ability").classification == (
        ItemClassification.progression if gating else ItemClassification.useful)
    state.can_reach_region = lambda name, player: name == OWNER
    owner = multiworld.get_region(OWNER, 1)
    assert all(entrance.access_rule(state) for entrance in owner.exits)
    checks = [loc for loc in multiworld.get_locations(1)
              if loc.parent_region.name.startswith(OWNER) and loc.address != 3960503]
    assert len(checks) == room_sanity
    assert all(loc.access_rule(state) for loc in checks)
    incoming = multiworld.get_entrance(f"{UPSTREAM} -> {OWNER}", 1)
    assert incoming.access_rule(state)
    area = multiworld.get_entrance(
        "REGION_RAINBOW_ROUTE/ROOM_1_13_LOWER -> REGION_CABBAGE_CAVERN/ROOM_3_04", 1)
    assert area.access_rule(state) is (not area_keys)
    state.collect(world.create_item("Cabbage Cavern - Area Key"), prevent_sweep=True)
    assert area.access_rule(state)


@pytest.mark.parametrize("gating,area_keys,statues,room_sanity", [(0, 0, 0, 0), (1, 0, 0, 0), (1, 1, 1, 1)])
def test_actual_full_generation_at_one_hp(tmp_path, monkeypatch, gating, area_keys, statues, room_sanity):
    import Main

    generated = []
    main = Main.main

    def capture_world(*args, **kwargs):
        multiworld = main(*args, **kwargs)
        generated.append(multiworld)
        return multiworld

    monkeypatch.setattr(Main, "main", capture_world)
    player = tmp_path / "player.yaml"
    player.write_text(
        "name: Green\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n"
        f"  ability_randomization_mode: 0\n  ability_gating: {gating}\n  area_keys: {area_keys}\n"
        f"  ability_randomization_statues: {statues}\n  room_sanity: {room_sanity}\n"
        "  minimum_health: 1\n  maximum_health: 1\n  accessibility: full\n", encoding="utf-8")
    archive = generate_archive_from_fixture(player, tmp_path / "out", seed=138)
    decoded = load_multidata_from_archive(archive)
    raw = decoded["slot_data"][1]["enemy_copy_ability_policy"]
    assert raw["mode"] == 0
    assert SourcePolicy(raw).grant("SPARKY", lambda _: True).guaranteed == frozenset({"Spark"})
    assert decoded["locations"][1][3960503]
    multiworld, = generated
    assert not multiworld.get_unfilled_locations()
    assert multiworld.can_beat_game()
    assert multiworld.fulfills_accessibility()
    world = multiworld.worlds[1]
    state = CollectionState(multiworld)
    state.can_reach_region = lambda name, player: name == UPSTREAM
    chest = multiworld.get_location(data.locations[CHEST].label, 1)
    assert chest.access_rule(state) is (not gating)
    state.collect(world.create_item("Spark Ability"), prevent_sweep=True)
    assert chest.access_rule(state)
