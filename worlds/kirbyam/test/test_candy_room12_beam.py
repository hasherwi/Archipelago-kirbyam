"""The source-backed Bomb Block belongs to the Candy 9-12 chest only."""

from copy import deepcopy
from pathlib import Path

import pytest

from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive
from .support.source_policy import set_rule_test_policy
from .test_mini_traversal import make_world
from .test_traversal import policy
from ..data import data
from ..traversal import CAPABILITY_ABILITIES
from ..traversal_data import room_traversal_graph, room_traversal_targets
from ..traversal_rules import target_applies


ROOM = "REGION_CANDY_CONSTELLATION/ROOM_9_12"
EXIT = ROOM + " -> REGION_CANDY_CONSTELLATION/ROOM_9_13"
LOCATION = "MINOR_CHEST_CANDY_CONSTELLATION_9_12"
TARGET = "bomb_402_candy_chest"


@pytest.mark.parametrize("area_keys", [False, True])
def test_requires_actual_local_beam_not_normal_or_permission(area_keys):
    row = next(row for row in room_traversal_targets("block") if row["id"] == TARGET)
    graph = room_traversal_graph(TARGET, "local_beam", area_keys)
    chest, = graph.required_targets
    normal = policy(0, minny=False)
    wrong_source = policy(1, pool=["Fire"], minny=False)
    assert CAPABILITY_ABILITIES[TARGET] == {"Beam"}
    assert target_applies(row, normal)
    assert not target_applies(row, wrong_source)
    for gating in (False, True):
        assert graph.evaluate(normal, frozenset(), gating).reaches(chest)
        assert not graph.evaluate(wrong_source, frozenset({"Beam Ability"}), gating).reaches(chest)
    assert data.locations[LOCATION].location_id == 3960575


@pytest.mark.parametrize("mode,pool,supported", [(0, None, True), (1, ["Beam"], True), (1, ["Fire"], False)])
def test_world_rule_only_adds_witness_to_this_chest(monkeypatch, mode, pool, supported):
    resolved = policy(mode, pool=pool, minny=False)
    set_rule_test_policy(monkeypatch, lambda *args, **kwargs: resolved.policy)
    world = make_world(mode, False, accessibility="minimal", room_sanity=1, area_keys=0)
    mw = world.multiworld
    state = mw.state
    chest = mw.get_location(data.locations[LOCATION].label, 1)
    visit, = [location for location in mw.get_region(ROOM, 1).locations if location.address == 3961232]
    exit_ = mw.get_entrance(EXIT, 1)
    monkeypatch.setattr(state, "can_reach_region", lambda region, player: False)
    assert chest.access_rule(state) is not supported
    assert visit.access_rule(state)
    assert exit_.access_rule(state)
    monkeypatch.setattr(state, "can_reach_region", lambda region, player: region == ROOM)
    assert chest.access_rule(state)
    assert visit.access_rule(state)
    assert exit_.access_rule(state)


def test_vanilla_source_seed_keeps_candy_chest_in_full_accessibility(tmp_path: Path):
    fixture = tmp_path / "player.yaml"
    fixture.write_text(
        "name: Candy\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n"
        "  ability_randomization_mode: 0\n  ability_gating: 1\n  room_sanity: 1\n"
        "  accessibility: full\n",
        encoding="utf-8",
    )
    archive = generate_archive_from_fixture(fixture, tmp_path / "out", seed=912)
    locations = load_multidata_from_archive(archive)["locations"][1]
    assert 3960575 in locations and 3961232 in locations


@pytest.mark.parametrize("mode", [1, 2])
@pytest.mark.parametrize("gating", [False, True])
@pytest.mark.parametrize("ability,item_code", [("UFO", 3860114), ("Spark", 3860115), ("Missile", 3860125), ("Sword", 3860118), ("Smash", 3860122)])
def test_local_ranged_requires_real_source_and_respects_permission(monkeypatch, mode, gating, ability, item_code):
    row = next(row for row in room_traversal_targets("block") if row["id"] == TARGET)
    graph = room_traversal_graph(TARGET, "local_" + ability.lower(), False)
    chest_node, = graph.required_targets
    resolved = policy(mode, pool=[ability], weight=0, minny=False)
    wrong_source = policy(mode, pool=["Fire"], weight=0, minny=False)
    assert CAPABILITY_ABILITIES[TARGET + "_" + ability.lower()] == {ability}
    assert target_applies(row, resolved)
    assert not target_applies(row, wrong_source)
    assert not graph.evaluate(wrong_source, frozenset({f"{ability} Ability"}), gating).reaches(chest_node)
    assert graph.evaluate(resolved, frozenset(), gating).reaches(chest_node) is (not gating)
    assert graph.evaluate(resolved, frozenset({f"{ability} Ability"}), gating).reaches(chest_node)

    set_rule_test_policy(monkeypatch, lambda *args, **kwargs: resolved.policy)
    world = make_world(mode, gating, accessibility="minimal", room_sanity=0, area_keys=0)
    state = world.multiworld.state
    chest = world.multiworld.get_location(data.locations[LOCATION].label, 1)
    exit_ = world.multiworld.get_entrance(EXIT, 1)
    monkeypatch.setattr(state, "can_reach_region", lambda region, player: region == ROOM)
    assert chest.access_rule(state) is (not gating)
    assert exit_.access_rule(state)
    if gating:
        item = world.create_item(f"{ability} Ability")
        assert item.code == item_code and item.advancement
        state.collect(item, prevent_sweep=True)
        assert chest.access_rule(state)


@pytest.mark.parametrize("pool,weight", [(["Beam", "UFO"], 0), (["UFO"], 100), (["Beam"], 50)])
def test_unverified_completely_random_keeps_legacy_rule(monkeypatch, pool, weight):
    row = next(row for row in room_traversal_targets("block") if row["id"] == TARGET)
    resolved = policy(2, pool=pool, weight=weight, minny=False)
    assert not target_applies(row, resolved)
    set_rule_test_policy(monkeypatch, lambda *args, **kwargs: resolved.policy)
    world = make_world(2, True, accessibility="minimal", room_sanity=0, area_keys=0,
                       ability_randomization_no_ability_weight=weight)
    state = world.multiworld.state
    monkeypatch.setattr(state, "can_reach_region", lambda region, player: region == ROOM)
    chest = world.multiworld.get_location(data.locations[LOCATION].label, 1)
    assert chest.access_rule(state)  # Compatibility, not proof that this profile can open the chest.


@pytest.mark.parametrize("ability", ["Spark", "Missile"])
def test_candy_conditional_progression_only_for_gated_guaranteed_source(ability):
    from ..traversal_rules import candy912_source_is_progression
    from types import SimpleNamespace

    for mode, pool, weight, gating, enabled, expected in (
            (1, [ability], 0, True, True, True),
            (2, [ability], 0, True, True, True),
            (1, [ability], 0, False, True, False),
            (2, [ability, "Fire"], 0, True, True, False),
            (2, [ability], 100, True, True, False),
            (1, [ability], 0, True, False, False)):
        world = SimpleNamespace(
            ENABLE_MINOR_CHESTS=enabled,
            _ability_gating_enabled=lambda: gating,
            _enemy_copy_ability_policy=policy(mode, pool=pool, weight=weight, minny=False).policy,
        )
        assert candy912_source_is_progression(world, ability) is expected


@pytest.mark.parametrize("ability,code", [("Spark", 3860115), ("Missile", 3860125)])
def test_controlled_shuffled_source_full_fill_keeps_permission_outside_own_chest(
        tmp_path, monkeypatch, ability, code):
    import Main
    from BaseClasses import CollectionState

    resolved = policy(1, pool=[ability], weight=0, minny=False)
    set_rule_test_policy(monkeypatch, lambda *args, **kwargs: resolved.policy)
    worlds = []
    main = Main.main

    def capture(*args, **kwargs):
        result = main(*args, **kwargs)
        worlds.append(result)
        return result

    monkeypatch.setattr(Main, "main", capture)
    player = tmp_path / "player.yaml"
    player.write_text(
        "name: Candy\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n"
        "  ability_randomization_mode: 1\n  ability_randomization_no_ability_weight: 0\n"
        "  ability_gating: 1\n  minimum_health: 6\n  maximum_health: 6\n"
        "  accessibility: full\n", encoding="utf-8")
    archive = generate_archive_from_fixture(player, tmp_path / "out", seed=912)
    locations = load_multidata_from_archive(archive)["locations"][1]
    assert locations[3960575][0] != code
    multiworld, = worlds
    assert multiworld.fulfills_accessibility() and multiworld.can_beat_game()
    locations_with_permission = multiworld.find_item_locations(f"{ability} Ability", 1)
    assert locations_with_permission and all(loc.item.advancement for loc in locations_with_permission)
    state = CollectionState(multiworld)
    state.sweep_for_advancements()
    assert state.has(f"{ability} Ability", 1)
    assert multiworld.get_location(data.locations[LOCATION].label, 1).can_reach(state)


@pytest.mark.parametrize("mode,pool,weight,minor_chests,want", [
    (0, None, 0, True, False),
    (1, ["Smash"], 0, True, False),
    (1, ["Fire"], 0, True, True),
    (2, ["Spark"], 0, True, False),
    (2, ["Beam", "Smash"], 0, True, True),
    (2, ["Beam"], 100, True, True),
    (2, ["Beam"], 100, False, False),
])
def test_linked_fuse_policy_only_when_no_stock_witness(mode, pool, weight, minor_chests, want):
    from ..conditional_routes import CANDY_FUSE as candy912_fuse

    original = policy(mode, pool=pool, weight=weight, minny=False).policy
    baseline = deepcopy(original)
    linked = candy912_fuse.needs_linked_fuse(original, minor_chests=minor_chests)
    assert original == baseline and candy912_fuse.SLOT_KEY not in original
    assert linked is want
    row = next(row for row in room_traversal_targets("block") if row["id"] == TARGET)
    graphs = candy912_fuse.target_graphs(row, linked, policy(mode, pool=pool, weight=weight, minny=False))
    expected = (candy912_fuse.graph(),) if want else ()
    if pool == ["Fire"] and want:
        expected += (candy912_fuse.fire_graph(),)
    assert graphs == expected
    assert candy912_fuse.config_bytes(linked) == (
        candy912_fuse.LINKED_CONFIG if want else candy912_fuse.STOCK_CONFIG)
    assert not candy912_fuse.enabled({})
    with pytest.raises(ValueError, match="linked fuse patch contract"):
        candy912_fuse.enabled({candy912_fuse.SLOT_KEY: 1})


@pytest.mark.parametrize("mode,weight", [(0, 0), (1, 0), (2, 0), (2, 100)])
@pytest.mark.parametrize("gating", [0, 1])
def test_generated_full_seed_keeps_exact_chest_and_patch_intent(tmp_path, monkeypatch, mode, weight, gating):
    import Main
    from BaseClasses import CollectionState
    from ..conditional_routes import CANDY_FUSE as candy912_fuse
    from ..traversal import SourcePolicy

    generated = []
    main = Main.main

    def capture(*args, **kwargs):
        world = main(*args, **kwargs)
        generated.append(world)
        return world

    monkeypatch.setattr(Main, "main", capture)
    player = tmp_path / "player.yaml"
    player.write_text(
        "name: Candy\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n"
        f"  ability_randomization_mode: {mode}\n  ability_randomization_no_ability_weight: {weight}\n"
        f"  ability_gating: {gating}\n  room_sanity: 1\n"
        "  accessibility: full\n  minimum_health: 6\n  maximum_health: 6\n",
        encoding="utf-8",
    )
    archive = generate_archive_from_fixture(player, tmp_path / "out", seed=912)
    multidata = load_multidata_from_archive(archive)
    locations = multidata["locations"][1]
    assert 3960575 in locations and 3961232 in locations
    slot_data = multidata["slot_data"][1]
    raw = slot_data["enemy_copy_ability_policy"]
    assert candy912_fuse.SLOT_KEY not in raw
    row = next(row for row in room_traversal_targets("block") if row["id"] == TARGET)
    assert candy912_fuse.enabled(slot_data) is not target_applies(row, SourcePolicy(raw))
    multiworld, = generated
    assert multiworld.fulfills_accessibility() and multiworld.can_beat_game()
    chest = multiworld.get_location(data.locations[LOCATION].label, 1)
    state = CollectionState(multiworld)
    state.sweep_for_advancements()
    assert chest.can_reach(state)
    if candy912_fuse.enabled(slot_data):
        assert not candy912_fuse.graph().placements
        # A Normal-only route: no equipment permission needed once the room is reached.
        monkeypatch.setattr(state, "has", lambda item, player: False)
        monkeypatch.setattr(state, "can_reach_region", lambda name, player: name == ROOM)
        assert chest.access_rule(state)
        monkeypatch.setattr(state, "can_reach_region", lambda name, player: False)
        assert not chest.access_rule(state)


@pytest.mark.parametrize("mode", [1, 2])
def test_supplemental_fire_exact_source_permission_and_linked_scope(mode):
    from ..conditional_routes import CANDY_FUSE as candy912_fuse

    row = {"id": TARGET}
    fire = policy(mode, pool=["Fire"], weight=0, minny=False)
    no_fire = policy(mode, pool=["Sword"], weight=0, minny=False)
    mixed = policy(2, pool=["Fire", "Beam"], weight=0, minny=False)
    fallible = policy(2, pool=["Fire"], weight=20, minny=False)
    normal, graph = candy912_fuse.target_graphs(row, True, fire)
    assert normal is candy912_fuse.graph()
    assert not candy912_fuse.target_graphs(row, candy912_fuse.enabled({}), fire)
    assert not candy912_fuse.target_graphs({"id": "other"}, True, fire)
    for unsupported in (no_fire, mixed, fallible):
        assert candy912_fuse.target_graphs(row, True, unsupported) == (normal,)
    placement, = graph.placements
    assert (placement.identity, placement.node, placement.source_key) == (
        "0x088C5D0C", "candy912_fire:east_doo", "WADDLE_DOO")
    target, = graph.required_targets
    for gating in (False, True):
        assert graph.evaluate(fire, frozenset(), gating).reaches(target) is (not gating)
        assert graph.evaluate(fire, frozenset({"Fire Ability"}), gating).reaches(target)
        assert not graph.evaluate(no_fire, frozenset({"Fire Ability"}), gating).reaches(target)
    assert normal.evaluate(fire, frozenset(), True).reaches("candy912_normal:chest")
