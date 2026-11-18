"""Exact-profile admission must not turn permission or owner access into a source."""
from copy import deepcopy
from dataclasses import replace
import hashlib
import json

import pytest
from BaseClasses import CollectionState
from test.general import setup_multiworld

from .. import KirbyAmWorld, yellow_cupid as y
from ..data import data
from ..rom import KirbyAmProcedurePatch, write_tokens
from ..traversal import SourcePolicy


def make_world(**options):
    return setup_multiworld(KirbyAmWorld, seed=14, options={**y.PROFILE, **options}).worlds[1]


@pytest.mark.parametrize("room_sanity", [0, 1])
@pytest.mark.parametrize("ability_gating", [0, 1])
def test_real_profile_requires_independent_source_access_not_owner_or_inventory(room_sanity, ability_gating):
    world = make_world(room_sanity=room_sanity, ability_gating=ability_gating)
    assert y.validate_profile(world)
    target = world.multiworld.get_location(data.locations[y.LOCATION].label, 1)
    state = CollectionState(world.multiworld)
    state.can_reach_region = lambda name, player: name == y.OWNER
    for item in ("Cupid Ability", "Phone a Friend", "UFO Ability"):
        state.collect(world.create_item(item), prevent_sweep=True)
    assert not target.access_rule(state)
    state.can_reach_region = lambda name, player: name == y.SOURCE_REGION
    assert target.access_rule(state)
    for item in ("Cupid Ability", "Phone a Friend", "UFO Ability"):
        state.remove(world.create_item(item))
    assert target.access_rule(state) is (not ability_gating)
    if ability_gating:
        for item in ("Phone a Friend", "UFO Ability"):
            state.collect(world.create_item(item), prevent_sweep=True)
        assert not target.access_rule(state)
        state.collect(world.create_item("Cupid Ability"), prevent_sweep=True)
        assert target.access_rule(state)
    room_checks = [loc for loc in world.multiworld.get_locations(1)
                   if loc.parent_region.name == y.OWNER and (loc.key or "").startswith("ROOM_")]
    assert len(room_checks) == room_sanity
    assert all(loc.access_rule(state) for loc in room_checks)


@pytest.mark.parametrize("gating", [False, True])
def test_two_distinct_finite_sources_and_normal_ladder_are_required(gating):
    world = make_world()
    policy = SourcePolicy(world._enemy_copy_ability_policy)
    graph = y.graph()
    owned = frozenset({"Cupid Ability"}) if gating else frozenset()
    target, = graph.required_targets
    assert graph.access_region == y.SOURCE_REGION
    assert [p.identity for p in graph.placements] == ["0x088D4FC0", "0x088D4F9C"]
    assert all(not p.renewable and not p.retry_evidence for p in graph.placements)
    result = graph.evaluate(policy, owned, gating)
    assert result.reaches(target) and not result.retry_assumptions
    assert all({p.identity for p in graph.placements} <= position.consumed
               for position in result.positions if position.node == "bomb_733_yellow:lower_carry")
    upper, lower = graph.placements
    for sources in ((), (upper,), (lower,), (upper, replace(lower, identity=upper.identity))):
        assert not replace(graph, placements=sources).evaluate(policy, owned, gating).reaches(target)
    for source in (upper, lower):
        sources = tuple(replace(p, node=target) if p == source else p for p in graph.placements)
        assert not replace(graph, placements=sources).evaluate(policy, owned, gating).reaches(target)
    assert any(r.required_equipment == frozenset({"Normal"}) and r.target == lower.node
               for r in graph.routes)
    assert all(not r.recover_dropped_ability for r in graph.routes)
    assert [r.capability for r in graph.routes if r.capability] == [
        "bomb_733_cupid_upper_from_below", "bomb_733_cupid_lower_from_corridor"]


@pytest.mark.parametrize("field,value", [
    ("ability_gating", 2),
    ("enemy_health_multiplier", 500), ("area_keys", 1),
    ("ability_randomization_statues", 1), ("advanced_logic", 1),
    ("ability_randomization_mode", 2),
])
def test_profile_changes_cannot_retain_an_installed_witness(field, value):
    world = make_world()
    getattr(world.options, field).value = value
    with pytest.raises(ValueError, match="Yellow Cupid profile changed"):
        y.validate_profile(world)
    del world._yellow_cupid_signature
    assert not y.validate_profile(world)


def test_same_cupid_outcome_does_not_qualify_another_policy():
    world = make_world()
    raw = deepcopy(world._enemy_copy_ability_policy)
    for seed in range(1000):
        raw["seed"] = seed
        if SourcePolicy(raw).grant("SPARKY", lambda _: True).guaranteed == {"Cupid"}:
            break
    else:
        raise AssertionError("No alternate Cupid assignment")
    assert hashlib.sha256(json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()).hexdigest() != y.POLICY_SHA256
    world._enemy_copy_ability_policy = raw
    with pytest.raises(ValueError, match="Yellow Cupid profile changed"):
        y.validate_profile(world)
    del world._yellow_cupid_signature
    assert not y.validate_profile(world)
    assert y.target_graphs(world, {"id": y.TARGET, "region": y.OWNER,
                                  "native_room": 733, "location": y.LOCATION}) == ()


def test_becoming_qualified_after_rules_does_not_publish_missing_chest_guard():
    world = make_world(enemy_health_multiplier=500)
    assert not y.validate_profile(world)
    world.options.enemy_health_multiplier.value = 100
    with pytest.raises(ValueError, match="Yellow Cupid profile changed"):
        y.validate_profile(world)


@pytest.mark.parametrize("field,value", [("id", "bomb_138_green"), ("native_room", 730),
                                        ("region", y.SOURCE_REGION), ("location", "MINOR_CHEST_MUSIC_NOTE_06")])
def test_witness_cannot_attach_to_another_target(field, value):
    world = make_world()
    row = {"id": y.TARGET, "region": y.OWNER, "native_room": 733, "location": y.LOCATION}
    assert y.target_graphs(world, row)
    row[field] = value
    assert not y.target_graphs(world, row)


@pytest.mark.parametrize("publication", ["slot", "tokens", "pre_output"])
def test_changed_area_key_profile_is_rejected_before_publication(publication):
    world = make_world()
    world.options.area_keys.value = 1
    with pytest.raises(ValueError, match="Yellow Cupid profile changed"):
        if publication == "slot":
            world.fill_slot_data()
        elif publication == "tokens":
            write_tokens(world, KirbyAmProcedurePatch(player=1, player_name="Profile"))
        else:
            KirbyAmWorld.stage_pre_output(world.multiworld)


def test_disabled_minor_chests_and_unrelated_targets_do_not_gain_rules(monkeypatch):
    monkeypatch.setattr(KirbyAmWorld, "ENABLE_MINOR_CHESTS", False)
    world = make_world()
    assert not y.validate_profile(world)
    assert all(loc.key != y.LOCATION for loc in world.multiworld.get_locations(1))
    assert y.target_graphs(world, {"id": "switch_310_mustard_map"}) == ()


@pytest.mark.parametrize("room_sanity", [0, 1])
@pytest.mark.parametrize("ability_gating", [0, 1])
def test_real_generation_keeps_yellow_source_guard_and_room16_refusal(monkeypatch, tmp_path, room_sanity, ability_gating):
    from .. import check_accessibility
    from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive

    options = {**y.PROFILE, "room_sanity": room_sanity, "ability_gating": ability_gating}
    yaml = tmp_path / "profile.yaml"
    yaml.write_text("name: CupidProfile1087\ngame: Kirby & The Amazing Mirror\n"
                    "Kirby & The Amazing Mirror:\n" + "".join(f"  {k}: {v}\n" for k, v in options.items()))
    inspected = []
    validate = check_accessibility.validate_all_checks

    def inspect(multiworld, players):
        world = multiworld.worlds[1]
        assert y.validate_profile(world)
        target = multiworld.get_location(data.locations[y.LOCATION].label, 1)
        state = CollectionState(multiworld)
        state.can_reach_region = lambda name, player: name == y.OWNER
        assert not target.access_rule(state)
        state.can_reach_region = lambda name, player: name == y.SOURCE_REGION
        assert target.access_rule(state) is (not ability_gating)
        state.collect(world.create_item("Cupid Ability"), prevent_sweep=True)
        assert target.access_rule(state)
        assert target.can_reach(multiworld.get_all_state())
        assert SourcePolicy(world._enemy_copy_ability_policy).grant("FOLEY", lambda _: True).guaranteed == {"Burning"}
        inspected.append(True)
        return validate(multiworld, players)

    monkeypatch.setattr(check_accessibility, "validate_all_checks", inspect)
    output = tmp_path / "output"
    if room_sanity:
        with pytest.raises(check_accessibility.KirbyAmCheckAccessibilityError,
                           match=r"unavailable even with all inventory=\['Room 4-16'\]"):
            generate_archive_from_fixture(yaml, output, seed=14)
        assert not tuple(output.glob("*.zip"))
    else:
        archive = generate_archive_from_fixture(yaml, output, seed=14)
        slot = load_multidata_from_archive(archive)["slot_data"][1]
        assert slot["minimum_health"] == slot["maximum_health"] == 6
        assert not slot["room_sanity"]
        assert hashlib.sha256(json.dumps(slot["enemy_copy_ability_policy"], sort_keys=True,
                                        separators=(",", ":")).encode()).hexdigest() == y.POLICY_SHA256
    assert inspected


@pytest.mark.parametrize("original,replacement", [(0, 1), (1, 0)])
def test_gating_change_still_requires_reinstalling_rules(original, replacement):
    world = make_world(ability_gating=original)
    assert y.validate_profile(world)
    world.options.ability_gating.value = replacement
    with pytest.raises(ValueError, match="Yellow Cupid profile changed"):
        y.validate_profile(world)
    del world._yellow_cupid_signature
    assert y.validate_profile(world)


@pytest.mark.parametrize("one_hit", [0, 1, 2])
def test_player_health_does_not_replace_finite_cupid_sources(one_hit):
    world = make_world()
    world.options.minimum_health.value = 1
    world.options.maximum_health.value = 10
    world.options.one_hit_mode.value = one_hit
    assert y.validate_profile(world)
    target = world.multiworld.get_location(data.locations[y.LOCATION].label, 1)
    state = CollectionState(world.multiworld)
    state.can_reach_region = lambda name, player: name == y.OWNER
    assert not target.access_rule(state)
    state.can_reach_region = lambda name, player: name == y.SOURCE_REGION
    assert target.access_rule(state)
