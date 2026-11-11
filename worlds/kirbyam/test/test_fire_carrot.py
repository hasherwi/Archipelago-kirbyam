"""Finite Fire719 source/carry/combo, never inventory-as-equipment or room-wide credit."""

from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from BaseClasses import CollectionState, ItemClassification
from Options import Accessibility
from test.general import setup_multiworld

from .. import KirbyAmWorld, traversal_rules as rules
from ..data import data
from ..enemy_ability_data import GATEABLE_ENEMY_COPY_ABILITIES
from ..traversal import CAPABILITY_CONSUMED_ABILITIES, Position, SourcePolicy, compile_traversal_graph
from ..traversal_data import _validate_target, room_traversal_graph, room_traversal_targets
from .support.source_policy import set_rule_test_policy
from .test_mini_traversal import make_world
from .test_traversal import policy

TARGET = "bomb_719_room13"
OWNER = "REGION_CARROT_CASTLE/ROOM_5_07"
UPSTREAM = "REGION_CARROT_CASTLE/ROOM_5_05"
EXIT = "REGION_CARROT_CASTLE/ROOM_5_13__LOGIC__ENTRY_FROM_5_07"
CAPABILITY = "bomb_719_fire_breath"
EVIDENCE = Path(__file__).resolve().parents[1] / "dev-docs/carrot-room7-fire-acceptance.json"
POLICIES = [
    (1, ["Fire"], 0, True), (2, ["Fire"], 0, True), (1, ["Bomb"], 0, False),
    (2, ["Fire", "Beam"], 0, False), (2, ["Fire", "Fighter"], 0, False),
    (2, ["Fire"], 50, False), (2, ["Fire"], 100, False),
]


def target_row():
    return next(row for row in room_traversal_targets("block") if row["id"] == TARGET)


def fire_graph(area_keys=False):
    return room_traversal_graph(TARGET, "room5_fire_entry", area_keys)


@pytest.mark.parametrize("mode,pool,weight,applies", POLICIES)
@pytest.mark.parametrize("gating", [False, True])
@pytest.mark.parametrize("area_keys", [False, True])
@pytest.mark.parametrize("statues", [False, True])
def test_conditional_raw_policy_preserves_original_rule_and_independent_access(
        monkeypatch, mode, pool, weight, applies, gating, area_keys, statues):
    resolver = policy(mode, pool=pool, weight=weight, statues=statues, minny=False)
    row = target_row()
    monkeypatch.setattr(rules, "extra_traversal_targets", lambda: (row,))
    assert rules.target_applies(row, resolver) is applies
    assert rules.static_extra_witness(resolver)

    def original_rule(state):
        return state.base_rule

    target = SimpleNamespace(access_rule=original_rule)
    looked_up, dependencies = [], []

    def get_entrance(name, player):
        looked_up.append((name, player))
        return target

    world = SimpleNamespace(
        player=1, _enemy_copy_ability_policy=resolver.policy,
        _ability_gating_enabled=lambda: gating, _area_keys_enabled=lambda: area_keys,
        options=SimpleNamespace(ability_randomization_statues=SimpleNamespace(value=statues),
                                accessibility=Accessibility(Accessibility.option_full)),
        multiworld=SimpleNamespace(get_entrance=get_entrance, get_region=lambda name, player: name,
                                   register_indirect_condition=lambda region, edge: dependencies.append(region)),
    )
    rules.install_extra_traversal_rules(world)
    assert looked_up == ([(f"{OWNER} -> {EXIT}", 1)] if applies else [])
    assert dependencies == ([UPSTREAM] if applies else [])
    if not applies:
        assert target.access_rule is original_rule
    owned = set()
    state = SimpleNamespace(base_rule=True, has=lambda item, player: item in owned,
                            can_reach_region=lambda name, player: name in {OWNER, EXIT})
    assert target.access_rule(state) is (not applies)
    owned.add("Fire Ability")
    assert target.access_rule(state) is (not applies)
    state.can_reach_region = lambda name, player: name == UPSTREAM
    assert target.access_rule(state)
    owned.clear()
    assert target.access_rule(state) is (not applies or not gating)
    state.base_rule = False
    assert not target.access_rule(state)


@pytest.mark.parametrize("mode,pool,weight,applies", POLICIES)
@pytest.mark.parametrize("gating", [0, 1])
@pytest.mark.parametrize("area_keys", [0, 1])
@pytest.mark.parametrize("statues", [0, 1])
@pytest.mark.parametrize("room_sanity,minor_chests", [(0, False), (1, True)])
def test_actual_world_only_normalized_lower_entry_and_unchanged_fire_classification(
        monkeypatch, mode, pool, weight, applies, gating, area_keys, statues, room_sanity, minor_chests):
    resolver = policy(mode, pool=pool, weight=weight, statues=statues, minny=False)
    set_rule_test_policy(monkeypatch, lambda *args, **kwargs: resolver.policy)
    monkeypatch.setattr(KirbyAmWorld, "ENABLE_MINOR_CHESTS", minor_chests)
    world = make_world(mode, gating, accessibility="minimal", area_keys=area_keys,
                       ability_randomization_statues=statues, room_sanity=room_sanity,
                       ability_randomization_no_ability_weight=weight)
    target = world.multiworld.get_entrance(f"{OWNER} -> {EXIT}", 1)
    assert target.connected_region.name == EXIT
    state = CollectionState(world.multiworld)
    state.can_reach_region = lambda name, player: name == UPSTREAM
    assert target.access_rule(state) is (not applies or not gating)
    item = world.create_item("Fire Ability")
    assert item.classification == ItemClassification.progression
    assert "Fire" in GATEABLE_ENEMY_COPY_ABILITIES
    state.collect(item, prevent_sweep=True)
    assert state.has("Fire Ability", 1) and target.access_rule(state)
    state.remove(item)
    assert not state.has("Fire Ability", 1)
    assert target.access_rule(state) is (not applies or not gating)
    state.collect(item, prevent_sweep=True)
    for accessible in (OWNER, EXIT):
        state.can_reach_region = lambda name, player, accessible=accessible: name == accessible
        assert target.access_rule(state) is (not applies)
    owner = world.multiworld.get_region(OWNER, 1)
    assert all(edge.access_rule(state) for edge in owner.exits if edge is not target)
    assert all(location.access_rule(state) for location in owner.locations)
    other = world.multiworld.get_region("REGION_CARROT_CASTLE/ROOM_5_14", 1)
    notes, = [edge for edge in other.exits if "ROOM_5_13" in edge.name]
    assert notes.connected_region.name != EXIT and notes.access_rule(state)
    area = world.multiworld.get_entrance(
        "REGION_RAINBOW_ROUTE/ROOM_1_13_LOWER -> REGION_CABBAGE_CAVERN/ROOM_3_04", 1)
    assert area.access_rule(state) is (not area_keys)
    state.collect(world.create_item("Cabbage Cavern - Area Key"), prevent_sweep=True)
    assert area.access_rule(state)


@pytest.mark.parametrize("gating", [False, True])
@pytest.mark.parametrize("area_keys", [False, True])
def test_finite_source_actual_carry_and_retained_fire(gating, area_keys):
    graph = fire_graph(area_keys)
    assert graph.access_region == UPSTREAM
    assert graph.required_guaranteed_source == ("WADDLE_DOO", "Fire")
    assert len(graph.starts) == 1 and graph.starts[0].equipped == "Normal"
    rooms = {node.key: node.room for node in graph.nodes}
    assert rooms[graph.starts[0].node] == 170
    source, = graph.placements
    assert rooms[source.node] == 719
    assert (source.identity, source.source_key, source.renewable) == ("0x088D3BF4", "WADDLE_DOO", False)
    assert not source.retry_evidence
    assert [(rooms[r.source], rooms[r.target]) for r in graph.routes if r.room_transition] == [(170, 719)]
    assert [r.capability for r in graph.routes if r.capability] == [CAPABILITY]
    assert all(r.opens is None and not r.recover_dropped_ability for r in graph.routes)
    assert [r.resets_room_instance for r in graph.routes] == [True, False, False, False]
    assert CAPABILITY not in CAPABILITY_CONSUMED_ABILITIES
    resolver = SourcePolicy(json.loads(EVIDENCE.read_text())["source_policy"])
    owned = frozenset({"Fire Ability"})
    target, = graph.required_targets
    result = graph.evaluate(resolver, owned, gating)
    assert result.reaches(target) and not result.retry_assumptions
    assert any(p.equipped == "Fire" for p in result.positions if p.node == target)
    # Dropping after arrival is legal; every arrival still consumed the one source.
    assert all(p.consumed == frozenset({source.identity}) and not p.opened
               for p in result.positions if p.node == target)
    assert graph.evaluate(resolver, frozenset(), gating).reaches(target) is (not gating)
    assert not replace(graph, placements=()).evaluate(resolver, owned, gating).reaches(target)
    behind = replace(graph, placements=(replace(source, node=target),))
    assert not behind.evaluate(resolver, owned, gating).reaches(target)
    cut = replace(graph, routes=tuple(r for r in graph.routes if r.target != source.node))
    assert not cut.evaluate(resolver, owned, gating).reaches(target)
    spent = replace(graph, starts=(Position(source.node, "Normal", consumed=frozenset({source.identity})),))
    assert not spent.evaluate(resolver, owned, gating).reaches(target)
    assert graph.routes[2].required_equipment == graph.routes[-1].required_equipment == frozenset({"Fire"})
    for wrong in ("Beam", "Fighter", "Spark", "Bomb"):
        assert not graph.evaluate(policy(1, pool=[wrong]), owned | {f"{wrong} Ability"}, gating).positions


@pytest.mark.parametrize("pool,weight", [
    (["Fire", "Beam"], 0), (["Fire", "Fighter"], 0), (["Fire", "Sword"], 0),
    (["Fire"], 50), (["Fire"], 100)])
@pytest.mark.parametrize("gating", [False, True])
@pytest.mark.parametrize("retries", [False, True])
def test_raw_mixed_source_cannot_become_guaranteed_by_inventory_filter(pool, weight, gating, retries):
    for owned in (frozenset({"Fire Ability"}), frozenset(f"{a} Ability" for a in pool)):
        result = fire_graph().evaluate(policy(2, pool=pool, weight=weight), owned, gating,
                                       allow_documented_retries=retries)
        assert not result.positions and not result.retry_assumptions


@pytest.mark.parametrize("mutation", ["swimming", "wrong_room"])
def test_kernel_and_compiler_reject_widened_attack(mutation):
    graph = fire_graph()
    route = next(r for r in graph.routes if r.capability)
    raw = deepcopy(target_row()["graphs"]["room5_fire_entry"])
    if mutation == "swimming":
        raw["routes"][-1]["water_state"] = "swimming"
        graph = replace(graph, routes=tuple(replace(r, water_state="swimming") if r == route else r
                                            for r in graph.routes))
    else:
        for node in raw["nodes"]:
            if node["native_room"] == 719:
                node["native_room"] = 517
        graph = replace(graph, nodes=tuple(replace(n, room=517) if n.room == 719 else n for n in graph.nodes))
    with pytest.raises(ValueError, match="native room"):
        compile_traversal_graph(raw)
    with pytest.raises(ValueError, match="native room"):
        graph.evaluate(policy(1, pool=["Fire"]), frozenset({"Fire Ability"}), True)


def test_four_or_alternatives_exact_target_and_preserved_prior_graphs():
    row = target_row()
    assert set(row["graphs"]) == {
        "room5_entry", "room5_fighter_entry", "room5_sword_entry", "room5_fire_entry"}
    expected = json.loads(EVIDENCE.read_text())["preserved_graph_sha256"]
    assert set(expected) == {"room5_entry", "room5_fighter_entry", "room5_sword_entry"}
    for key, digest in expected.items():
        assert hashlib.sha256(json.dumps(row["graphs"][key], sort_keys=True).encode()).hexdigest() == digest
    for ability in ("Beam", "Fighter", "Sword", "Fire"):
        resolver = policy(1, pool=[ability])
        assert rules.target_applies(row, resolver)
        outcomes = [rules.graph_succeeds(g, resolver, frozenset({f"{ability} Ability"}), True, retries=True)
                    for g in rules.target_graphs(row, False)]
        assert outcomes == [ability == "Beam", ability == "Fighter", ability == "Sword", ability == "Fire"]
    assert rules.target_applies(row, policy())  # Native Beam assignment is unchanged.
    for key, wrong in [("id", "bomb_other"), ("native_room", 517), ("kind", "switch"),
                       ("region", UPSTREAM), ("exit", "REGION_CARROT_CASTLE/ROOM_5_14")]:
        altered = deepcopy(row)
        altered[key] = wrong
        with pytest.raises(ValueError, match="reviewed Carrot entry"):
            _validate_target(altered)
    owners = [(r["id"], key) for r in room_traversal_targets("block") for key, g in r["graphs"].items()
              if any(route.get("capability") == CAPABILITY for route in g["routes"])]
    assert owners == [(TARGET, "room5_fire_entry")]
    assert data.items[3860101].classification == ItemClassification.progression


@pytest.mark.parametrize("gating,source", [(1, "Fire"), (0, "Fire"), (1, "Bomb")])
def test_start_inventory_is_already_owned_before_regions_without_promotion(monkeypatch, gating, source):
    resolver = policy(1, pool=[source])
    set_rule_test_policy(monkeypatch, lambda *args, **kwargs: resolver.policy)
    multiworld = setup_multiworld(KirbyAmWorld, steps=("generate_early",), seed=18, options={
        "ability_randomization_mode": 1, "ability_gating": gating, "accessibility": "minimal"})
    world = multiworld.worlds[1]
    starting = [world.create_item("Fire Ability") for _ in range(3)]
    for item in starting:
        assert item.classification == ItemClassification.progression
        multiworld.push_precollected(item)
    assert multiworld.state.count("Fire Ability", 1) == 3
    world.create_regions()
    assert multiworld.state.count("Fire Ability", 1) == CollectionState(multiworld).count("Fire Ability", 1) == 3
    for item in starting:
        multiworld.state.remove(item)
    assert not multiworld.state.has("Fire Ability", 1)


@pytest.mark.parametrize("gating,area_keys,health,room_sanity,count", [
    (1, 0, 100, 0, 0), (1, 1, 500, 1, 1), (1, 0, 250, 0, 3), (0, 0, 100, 1, 1)])
def test_normal_full_pool_seed18_fill_start_inventory_and_accessibility(
        tmp_path, monkeypatch, gating, area_keys, health, room_sanity, count):
    import Main
    from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive
    generated, before_regions, after_regions = [], [], []
    main, create_regions = Main.main, KirbyAmWorld.create_regions

    def capture_regions(world):
        before_regions.append(world.multiworld.state.count("Fire Ability", world.player))
        create_regions(world)
        after_regions.append(world.multiworld.state.count("Fire Ability", world.player))

    def capture_main(*args, **kwargs):
        multiworld = main(*args, **kwargs)
        generated.append(multiworld)
        return multiworld

    monkeypatch.setattr(KirbyAmWorld, "create_regions", capture_regions)
    monkeypatch.setattr(Main, "main", capture_main)
    player = tmp_path / "player.yaml"
    player.write_text("name: Fire719\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n"
                      "  ability_randomization_mode: 1\n  ability_randomization_no_ability_weight: 0\n"
                      "  minimum_health: 1\n  maximum_health: 1\n"
                      f"  ability_gating: {gating}\n  area_keys: {area_keys}\n"
                      f"  enemy_health_multiplier: {health}\n  room_sanity: {room_sanity}\n"
                      f"  start_inventory:\n    Fire Ability: {count}\n  accessibility: full\n", encoding="utf-8")
    archive = generate_archive_from_fixture(player, tmp_path / "out", seed=18)
    decoded = load_multidata_from_archive(archive)
    raw = decoded["slot_data"][1]["enemy_copy_ability_policy"]
    assert len(raw["allowed_abilities"]) == 25
    assert SourcePolicy(raw).grant("WADDLE_DOO", lambda _: True).guaranteed == frozenset({"Fire"})
    assert raw["seed"] == 2395008880317811979
    assert decoded["precollected_items"][1].count(3860101) == count
    assert before_regions == after_regions == [count]
    multiworld, = generated
    assert not multiworld.get_unfilled_locations()
    assert multiworld.can_beat_game() and multiworld.fulfills_accessibility()
    state = CollectionState(multiworld)
    assert state.count("Fire Ability", 1) == count
    state.can_reach_region = lambda name, player: name == UPSTREAM
    target = multiworld.get_entrance(f"{OWNER} -> {EXIT}", 1)
    assert target.access_rule(state) is (bool(count) or not gating)
    starting = [i for i in multiworld.precollected_items[1] if i.name == "Fire Ability"]
    for item in starting:
        state.remove(item)
    assert not state.has("Fire Ability", 1)
    assert target.access_rule(state) is (not gating)


@pytest.mark.parametrize("mode,gating,categories,area_keys", [(1, 1, 0, 0), (1, 0, 0, 1), (2, 1, 0, 1)])
def test_fire_only_generated_source_policy_fill(tmp_path, monkeypatch, mode, gating, categories, area_keys):
    import Main
    from ..ability_randomization import build_enemy_copy_ability_policy
    from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive

    def fire_only(*args, **kwargs):
        return build_enemy_copy_ability_policy(*args, **kwargs, whitelist=["Fire"])

    generated = []
    main = Main.main

    def capture(*args, **kwargs):
        multiworld = main(*args, **kwargs)
        generated.append(multiworld)
        return multiworld

    monkeypatch.setattr("worlds.kirbyam.build_enemy_copy_ability_policy", fire_only)
    monkeypatch.setattr(Main, "main", capture)
    player = tmp_path / "player.yaml"
    player.write_text(
        "name: Fire719Source\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n"
        f"  ability_randomization_mode: {mode}\n  ability_gating: {gating}\n  area_keys: {area_keys}\n"
        f"  ability_randomization_statues: {categories}\n  ability_randomization_minibosses: {categories}\n"
        f"  ability_randomization_boss_spawns: {categories}\n  ability_randomization_minny: {categories}\n"
        f"  ability_randomization_passive_enemies: {categories}\n"
        "  ability_randomization_no_ability_weight: 0\n  minimum_health: 1\n  maximum_health: 1\n"
        "  enemy_health_multiplier: 500\n  room_sanity: 1\n  accessibility: full\n", encoding="utf-8")
    archive = generate_archive_from_fixture(player, tmp_path / "out", seed=18)
    decoded = load_multidata_from_archive(archive)
    raw = decoded["slot_data"][1]["enemy_copy_ability_policy"]
    assert list(raw["allowed_abilities"]) == ["Fire"]
    assert SourcePolicy(raw).grant("WADDLE_DOO", lambda _: True).guaranteed == frozenset({"Fire"})
    multiworld, = generated
    assert not multiworld.get_unfilled_locations()
    assert multiworld.can_beat_game() and multiworld.fulfills_accessibility()
    state = CollectionState(multiworld)
    state.can_reach_region = lambda name, player: name == UPSTREAM
    target = multiworld.get_entrance(f"{OWNER} -> {EXIT}", 1)
    assert target.access_rule(state) is (not gating)
    state.collect(multiworld.worlds[1].create_item("Fire Ability"), prevent_sweep=True)
    assert target.access_rule(state)
