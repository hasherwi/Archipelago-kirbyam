"""Exact native590 retouch alternative, not finite-enemy or broad switch credit."""
from copy import deepcopy
from types import SimpleNamespace

import pytest
from BaseClasses import CollectionState

from .. import conditional_routes as profiles
from .. import traversal_rules as rules
from ..traversal_data import _validate_conditional_routes
from .support.check_accessibility import LocalCheckAudit, audit_local_checks
from .test_cutter_progression import _generate
from .test_traversal import policy

NAME = profiles.MUSTARD_MAP_LIVE_CUTTER
HUB = "REGION_RAINBOW_ROUTE/ROOM_1_HUB_4"
MAP = "Mustard Mountain Map - Big Chest"
PROFILE = {
    "ability_randomization_mode": 2,
    "ability_randomization_statues": 1,
    "ability_randomization_no_ability_weight": 100,
    "area_keys": 0,
    "ability_gating": 0,
    "room_sanity": 0,
    "enemy_health_multiplier": 100,
    "minimum_health": 6,
    "one_hit_mode": 0,
}


@pytest.mark.parametrize("delta", [
    {}, {"ability_gating": 1}, {"area_keys": 1}, {"room_sanity": 1},
    {"ability_randomization_mode": 1}, {"ability_randomization_statues": 0},
    {"ability_randomization_no_ability_weight": 99},
    {"enemy_health_multiplier": 500}, {"minimum_health": 1}, {"one_hit_mode": 1},
    {"ability_randomization_statues": True},
])
def test_fixed_profile_qualification_and_source_mask(delta):
    world = SimpleNamespace(options=SimpleNamespace(**{**PROFILE, **delta}))
    live = policy(2, statues=True, weight=100, pool=["Cutter", "Sword"])
    assert profiles.mustard_map_live_cutter_enabled(world, live) is (not delta)
    assert not profiles.mustard_map_live_cutter_enabled(world, policy(2, statues=True, weight=99))
    assert not profiles.mustard_map_live_cutter_enabled(world, policy(2, statues=False, weight=100))
    assert not profiles.mustard_map_live_cutter_enabled(world, policy(2, statues=True, weight=100, pool=["Sword"]))


def test_graph_uses_one_retouched_statue_two_doors_and_no_reset():
    row, _ = profiles.contract(NAME)
    graph = profiles.graph(NAME)
    source, = graph.placements
    assert (source.source_key, source.identity) == ("STATUE:353903", "0x088B6908")
    assert source.renewable and source.retry_evidence
    assert graph.access_region == HUB
    nodes = {node.key: node.room for node in graph.nodes}
    assert [(nodes[r.source], nodes[r.target]) for r in graph.routes if r.room_transition] == [(590, 534), (534, 310)]
    assert all(not route.resets_room_instance and route.opens is None for route in graph.routes)
    live = policy(2, statues=True, weight=100, pool=["Cutter", "Sword"])
    assert not rules.target_applies(row, live)
    assert not rules.graph_succeeds(graph, live, frozenset(), False, retries=False)
    assert rules.graph_succeeds(graph, live, frozenset(), False, retries=True)
    assert not rules.graph_succeeds(graph, live, frozenset(), True, retries=True)
    assert rules.graph_succeeds(graph, live, frozenset({"Cutter Ability"}), True, retries=True)
    for resolver in (policy(0), policy(2, statues=False, weight=100),
                     policy(2, statues=True, weight=100, pool=["Sword"])):
        assert not rules.graph_succeeds(graph, resolver, frozenset(), False, retries=True)


@pytest.mark.parametrize("mutate", ["western_statue", "reset_loop", "wrong_map", "loosened_profile"])
def test_authoring_rejects_unwitnessed_profile_or_physical_graph(mutate):
    row = deepcopy(profiles.contract(NAME)[0])
    profile, = row["conditional_routes"]
    graph = profile["witnesses"][0]["graph"]
    if mutate == "western_statue":
        graph["sources"][0]["inventory_id"] = "room:590/template:0x088B6830"
    elif mutate == "reset_loop":
        graph["routes"][0].update(room_instance="reset", reset_evidence="invalid")
    elif mutate == "wrong_map":
        row["location"] = "MAJOR_CHEST_CARROT_CASTLE"
    else:
        profile["activation"]["fixture_options"]["ability_gating"] = 1
    with pytest.raises(ValueError, match="conditional statue|conditional route activation"):
        _validate_conditional_routes(row, set())


def test_real_seed_1259_installs_exact_route_and_generates_archive(monkeypatch, tmp_path):
    mw, multidata, archive = _generate(monkeypatch, tmp_path, 1259, [PROFILE])
    world = mw.worlds[1]
    live = rules.SourcePolicy.for_world(world, world._enemy_copy_ability_policy)
    row, _ = profiles.contract(NAME)
    assert profiles.mustard_map_live_cutter_enabled(world, live)
    assert not rules.target_applies(row, live)
    assert archive.is_file() and 3960205 in multidata["locations"][1]
    assert audit_local_checks(mw, 1) == LocalCheckAudit((), (), ())
    state = CollectionState(mw)
    target = mw.get_location(MAP, 1)
    state.can_reach_region = lambda name, player: name == target.parent_region.name
    assert not target.access_rule(state)
    state.can_reach_region = lambda name, player: name == HUB
    assert target.access_rule(state)
