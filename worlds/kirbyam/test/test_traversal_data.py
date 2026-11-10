"""Contracts for reviewed room-owned traversal data, separate from ability providers."""

from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace

import pytest

from ..traversal import CAPABILITY_ABILITIES, Grant
from ..traversal_data import (
    compile_room_graph, load_room_traversal, room_traversal_graph, room_traversal_targets,
)

OWNER = "REGION_RAINBOW_ROUTE/ROOM_1_06_LOWER_MID"
HUB = "REGION_RAINBOW_ROUTE/ROOM_1_HUB_1"
CENTRAL = "REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE"


@pytest.fixture
def payload():
    return {
        "version": 1, "status": "reviewed",
        "nodes": [{"id": "pre", "native_room": 108}, {"id": "post", "native_room": 108}],
        "routes": [{"from": "pre", "to": "post", "capability": "wheel_race", "evidence": "reviewed route"}],
        "sources": [{"id": "test-wheelie", "node": "pre", "source_key": "WHEELIE",
                     "acquisition_evidence": "reviewed acquisition"}],
        "starts": ["pre"], "required_targets": ["post"],
    }


@pytest.fixture
def rooms(payload):
    return {OWNER: {"traversal": {"version": 1, "targets": [{
        "id": "test-wheel", "kind": "wheel", "native_room": 108,
        "exit": "REGION_RAINBOW_ROUTE/ROOM_1_06_LOWER_CHEST",
        "graphs": {"local": payload},
    }]}}}


def test_minimal_reviewed_schema_loads_without_mutation(rooms):
    original = deepcopy(rooms)
    targets, sources, parts = load_room_traversal(rooms)
    assert len(targets) == 1
    assert targets[0]["region"] == OWNER
    assert sources == {}
    assert parts == {}
    assert rooms == original


@pytest.mark.parametrize("version", [0, 2, "1", None])
def test_unknown_room_schema_version(rooms, version):
    rooms[OWNER]["traversal"]["version"] = version
    with pytest.raises(ValueError):
        load_room_traversal(rooms)


def test_unknown_owner(rooms):
    rooms["UNKNOWN_REGION"] = rooms.pop(OWNER)
    with pytest.raises(ValueError):
        load_room_traversal(rooms)


@pytest.mark.parametrize("field,value", [
    ("kind", "unknown"), ("exit", "UNKNOWN_EXIT"),
    ("native_room", 99999), ("graphs", {}),
])
def test_invalid_target(rooms, field, value):
    rooms[OWNER]["traversal"]["targets"][0][field] = value
    with pytest.raises(ValueError):
        load_room_traversal(rooms)


def test_unknown_location(rooms):
    target = rooms[OWNER]["traversal"]["targets"][0]
    target.pop("exit")
    target["location"] = "UNKNOWN_LOCATION"
    with pytest.raises(ValueError):
        load_room_traversal(rooms)


def test_duplicate_targets(rooms):
    targets = rooms[OWNER]["traversal"]["targets"]
    targets.append(deepcopy(targets[0]))
    with pytest.raises(ValueError, match="Duplicate.*target"):
        load_room_traversal(rooms)


def test_duplicate_source_sets(rooms, payload):
    definition = {"native_room": 108, "sources": payload["sources"]}
    rooms[OWNER]["traversal"]["source_sets"] = {"duplicate": definition}
    rooms[HUB] = {"traversal": {"version": 1, "source_sets": {"duplicate": definition}}}
    with pytest.raises(ValueError, match="Duplicate.*source set"):
        load_room_traversal(rooms)


@pytest.mark.parametrize("field,value", [
    ("version", 2), ("status", "unreviewed"),
    ("starts", ["unknown"]), ("required_targets", ["unknown"]),
    ("access", {"region": "UNKNOWN_REGION"}),
    ("access", {"region": HUB, "all_hub_switches": "yes"}),
])
def test_invalid_graph(payload, field, value):
    payload[field] = value
    with pytest.raises(ValueError):
        compile_room_graph(payload, {})


@pytest.mark.parametrize("field,value", [
    ("source_key", "UNKNOWN_SOURCE"), ("node", "unknown"),
    ("acquisition_evidence", ""), ("renewable", True),
    ("retry_evidence", "not renewable"),
])
def test_invalid_acquisition(payload, field, value):
    payload["sources"][0][field] = value
    with pytest.raises(ValueError):
        compile_room_graph(payload, {})


@pytest.mark.parametrize("update", [
    {"evidence": ""}, {"room_instance": "reset"},
    {"from": "unknown"}, {"to": "unknown"},
    {"capability": "unknown"}, {"allowed_abilities": ["Stone"]},
    {"allowed_abilities": []},
])
def test_invalid_route_or_missing_proof(payload, update):
    payload["routes"][0].update(update)
    with pytest.raises(ValueError):
        compile_room_graph(payload, {})


def test_source_set_must_exist_and_match_native_room(payload):
    payload["source_sets"] = [{"id": "shared", "node": "pre"}]
    with pytest.raises(ValueError, match="Unknown.*source set"):
        compile_room_graph(payload, {})
    with pytest.raises(ValueError, match="native room"):
        compile_room_graph(payload, {"shared": {"native_room": 190, "sources": payload["sources"]}})


def test_source_set_expansion_preserves_identity_and_inputs(payload):
    placement = payload.pop("sources")[0]
    placement.pop("node")
    sets = {"shared": {"native_room": 108, "sources": [placement]}}
    payload["source_sets"] = [{"id": "shared", "node": "pre"}]
    original = deepcopy((payload, sets))
    graph = compile_room_graph(payload, sets)
    assert graph.placements[0].identity == "test-wheelie"
    assert graph.placements[0].node == "pre"
    assert not graph.placements[0].renewable
    assert graph.placements[0].retry_evidence is None
    assert (payload, sets) == original


def test_target_catalog_counts_and_provider_separation():
    assert {kind: len(room_traversal_targets(kind)) for kind in ("mini", "peg", "wheel")} == {
        "mini": 6, "peg": 11, "wheel": 1,
    }
    assert {row["native_room"] for row in room_traversal_targets("mini")} == {134, 312, 321, 736}
    assert CAPABILITY_ABILITIES == {
        "mini_corridor": frozenset({"Mini"}), "wheel_race": frozenset({"Wheel"}),
        "peg": frozenset({"Stone", "Hammer", "Smash", "Master"}),
        "fuse": frozenset({"Fire", "Burning", "Bomb", "Laser", "UFO", "Master", "Hammer", "Crash"}),
        "rope": frozenset({"Cutter", "Sword", "Cupid", "Smash", "Master"}),
        "metal": frozenset({"Hammer", "Stone", "Throw", "Burning", "Missile", "UFO", "Smash", "Master"}),
        "bomb_110_room9": frozenset({"Spark"}),
        "bomb_110_room9_underwater_sword": frozenset({"Sword"}),
        "bomb_138_green": frozenset({"Spark"}),
        "bomb_733_yellow_ufo_top_charge": frozenset({"UFO"}),
        "bomb_517_chocolate": frozenset({"Beam", "Spark", "Ice", "Smash"}),
        "bomb_719_room13": frozenset({"Beam"}),
        "switch_533_bomb_placement": frozenset({"Bomb"}),
        "switch_533_ufo_top_charge": frozenset({"UFO"}),
        "switch_310_ufo_top_charge": frozenset({"UFO"}),
        "frozen_enemy_hit": frozenset({"Ice"}),
        "underwater_block_hit": frozenset({"Normal", "Parasol", "Hammer", "Sword", "Master"}),
    }


@pytest.mark.parametrize("target_id,native_room", [
    ("mini_321_lower", 321), ("mini_312_warp", 312),
    ("mini_736_chest", 736), ("mini_134_ocean_spray", 134),
    ("mini_321_cross_to_right", 321), ("mini_321_right_lower", 321),
])
def test_mini_exact_directed_topology(target_id, native_room):
    graph = room_traversal_graph(target_id, "local")
    assert {(node.key, node.room) for node in graph.nodes} == {
        (f"{target_id}:{part}", native_room) for part in ("arrival", "source", "target", "bypass")
    }
    assert {(r.source, r.target, r.capability) for r in graph.routes} == {
        (f"{target_id}:arrival", f"{target_id}:source", None),
        (f"{target_id}:source", f"{target_id}:target", "mini_corridor"),
        (f"{target_id}:arrival", f"{target_id}:bypass", None),
    }
    assert graph.required_targets == {f"{target_id}:target"}
    assert graph.access_region is None
    assert not graph.requires_all_hub_switches


@pytest.mark.parametrize("witness,rooms,access,switches", [
    ("local", [140, 108, 110, 108], "REGION_RAINBOW_ROUTE/ROOM_1_07", False),
    ("statues", [970, 801, 190, 140, 108, 110, 108], "REGION_COPY_ABILITY_ROOM/MAIN", False),
])
def test_wheel_exact_directed_topology_and_access(witness, rooms, access, switches):
    graph = room_traversal_graph("wheel_108_chest", witness)
    names = [f"step{i}" for i in range(len(rooms))] + ["chest"]
    assert [(node.key, node.room) for node in graph.nodes] == list(zip(names, rooms + [108]))
    assert [(r.source, r.target) for r in graph.routes] == list(zip(names, names[1:]))
    assert [r.capability for r in graph.routes] == [None] * (len(rooms) - 1) + ["wheel_race"]
    assert [r.resets_room_instance for r in graph.routes] == [False] * (len(rooms) - 2) + [True, False]
    assert graph.required_targets == {"chest"}
    assert graph.access_region == access
    assert graph.requires_all_hub_switches is switches
    assert all(start.equipped == "Normal" for start in graph.starts)


def test_area_keys_are_option_dependent_without_losing_hub_requirements():
    hubs = {"Candy Constellation - Hub Connection", "Rainbow Route East - Hub Connection"}
    for enabled in (False, True):
        graph = room_traversal_graph("peg_411_4_3", "carry", area_keys=enabled)
        assert [(r.source, r.target) for r in graph.routes] == [
            ("190", "801"), ("801", "490"), ("490", "411"), ("411", "target"),
        ]
        for route in graph.routes[:-1]:
            assert route.items == hubs | ({"Candy Constellation - Area Key"} if enabled else set())
        assert graph.routes[-1].items == frozenset()
        assert graph.routes[-1].allowed_abilities == {"Hammer", "Smash", "Stone"}
        assert graph.access_region == HUB
        assert not graph.requires_all_hub_switches


def test_shared_statues_keep_physical_identity_across_witnesses():
    wheel = room_traversal_graph("wheel_108_chest", "statues")
    peg = room_traversal_graph("peg_149_35_18", "statues")
    expected_wheel = ("0x088D6078", "STATUE:353904")
    for graph in (wheel, peg):
        identities = {(p.identity, p.source_key) for p in graph.placements}
        assert len(identities) == 19
        assert expected_wheel in identities
        assert all(p.renewable and p.retry_evidence for p in graph.placements)
    assert {(p.identity, p.source_key) for p in wheel.placements} == {
        (p.identity, p.source_key) for p in peg.placements
    }


def test_documented_retries_are_false_by_default():
    class RandomWheelPolicy:
        def grant(self, key, permitted):
            return Grant(frozenset({"Wheel", "Stone"}), randomized=True, can_fail=True)

    graph = room_traversal_graph("wheel_108_chest", "hub_statues")
    owned = frozenset(item for route in graph.routes for item in route.items)
    result = graph.evaluate(RandomWheelPolicy(), owned, False)
    assert not result.reaches("chest")
    assert not result.retry_assumptions
    conditional = graph.evaluate(RandomWheelPolicy(), owned, False, allow_documented_retries=True)
    assert conditional.reaches("chest")
    assert conditional.retry_assumptions


@pytest.mark.parametrize("target_id,path", [
    ("peg_149_35_18", [190, 143, 145, 146, 147, 148, 149]),
    ("peg_510_7_7", [592, 528, 513, 509, 510]),
    ("peg_513_4_7", [592, 528, 513]),
    ("peg_527_56_16", [592, 528, 527]),
    ("peg_527_18_13", [592, 528, 527]),
    ("peg_816_26_3", [592, 801, 191, 890, 811, 830, 810, 802, 816]),
    ("peg_204_62_4", [190, 801, 290, 210, 227, 204]),
    ("peg_221_41_12", [190, 801, 290, 291, 215, 212, 216, 217, 221]),
    ("peg_605_12_24", [592, 690, 611, 601, 605]),
    ("peg_401_28_30", [190, 801, 490, 407, 401]),
    ("peg_411_4_3", [190, 801, 490, 411]),
])
def test_peg_carry_and_local_exact_directed_topology(target_id, path):
    graph = room_traversal_graph(target_id, "carry")
    names = [str(room) for room in path] + ["target"]
    assert [(node.key, node.room) for node in graph.nodes] == list(zip(names, path + [path[-1]]))
    assert [(r.source, r.target) for r in graph.routes] == list(zip(names, names[1:]))
    assert [r.capability for r in graph.routes] == [None] * (len(path) - 1) + ["peg"]
    assert graph.routes[-1].opens == target_id
    assert graph.required_targets == {"target"}
    assert graph.access_region == (HUB if path[0] == 190 else "REGION_CABBAGE_CAVERN/ROOM_3_HUB_3")
    assert not graph.requires_all_hub_switches
    local = room_traversal_graph(target_id, "local")
    assert {(node.key, node.room) for node in local.nodes} == {
        ("approach", path[-1]), ("target", path[-1]),
    }
    assert [(r.source, r.target, r.capability, r.opens) for r in local.routes] == [
        ("approach", "target", "peg", target_id),
    ]
    assert local.access_region is None
    assert not local.requires_all_hub_switches


@pytest.mark.parametrize("access", [None, [], {"region": HUB, "unexpected": True}, {"all_hub_switches": True}])
def test_access_schema_rejects_unsupported_prerequisites(payload, access):
    payload["access"] = access
    with pytest.raises(ValueError):
        compile_room_graph(payload, {})


def test_source_set_retry_override_requires_renewability(payload):
    placement = payload.pop("sources")[0]
    placement.pop("node")
    payload["source_sets"] = [{"id": "shared", "node": "pre", "retry_evidence": "unproved retry"}]
    with pytest.raises(ValueError, match="renewable"):
        compile_room_graph(payload, {"shared": {"native_room": 108, "sources": [placement]}})


@pytest.mark.parametrize("kind,target_id", [("mini", "mini_312_warp"), ("peg", "peg_401_28_30")])
def test_local_installers_honor_access_metadata_and_dependencies(monkeypatch, kind, target_id):
    from .. import mini_traversal, peg_traversal
    from ..traversal_data import HUB_SWITCH_LABELS, graph_access_regions

    row = next(row for row in room_traversal_targets(kind) if row["id"] == target_id)
    graph = replace(room_traversal_graph(target_id, "local"),
                    access_region=CENTRAL, requires_all_hub_switches=True)
    target = SimpleNamespace(access_rule=lambda state: True)
    dependencies = set()
    reached = {"region": False, "switches": False}
    switch = SimpleNamespace(can_reach=lambda state: reached["switches"])
    multiworld = SimpleNamespace(
        get_entrance=lambda name, player: target,
        get_region=lambda name, player: name,
        get_location=lambda name, player: switch,
        register_indirect_condition=lambda region, entrance: dependencies.add(region),
    )
    world = SimpleNamespace(
        player=1, multiworld=multiworld, _enemy_copy_ability_policy={"mode": 0},
        options=SimpleNamespace(ability_randomization_statues=SimpleNamespace(value=False)),
        _ability_gating_enabled=lambda: False, _area_keys_enabled=lambda: False,
    )
    if kind == "mini":
        monkeypatch.setattr(mini_traversal, "mini_routes", lambda: ((row, graph),))
        mini_traversal.install_mini_rules(world)
    else:
        monkeypatch.setattr(peg_traversal, "PEG_ROUTES", (row,))
        monkeypatch.setattr(peg_traversal, "peg_graph", lambda row: graph)
        monkeypatch.setattr(peg_traversal, "carry_graphs", lambda row, keys: ())
        peg_traversal.install_peg_rules(world)
    state = SimpleNamespace(has=lambda name, player: True,
                            can_reach_region=lambda name, player: reached["region"])
    assert len(HUB_SWITCH_LABELS) == 15
    assert dependencies == graph_access_regions(graph)
    assert not target.access_rule(state)
    reached["region"] = True
    assert not target.access_rule(state)
    reached["switches"] = True
    assert target.access_rule(state)


@pytest.mark.parametrize("key", ["room_transition", "recover_dropped_ability"])
def test_transition_flags_require_real_booleans(payload, key):
    payload["routes"][0][key] = "false"
    with pytest.raises(ValueError, match="boolean"):
        compile_room_graph(payload, {})


def test_renewability_requires_real_boolean(payload):
    payload["sources"][0].update(renewable="false", renewable_evidence="not actually renewable")
    with pytest.raises(ValueError, match="boolean"):
        compile_room_graph(payload, {})


@pytest.mark.parametrize("value", [None, 0, 1, "false"])
def test_optional_route_flag_requires_boolean(rooms, value):
    rooms[OWNER]["traversal"]["targets"][0]["required_for_generation"] = value
    with pytest.raises(ValueError, match="required_for_generation"):
        load_room_traversal(rooms)


def test_optional_route_requires_bypass_evidence(rooms):
    target = rooms[OWNER]["traversal"]["targets"][0]
    target["required_for_generation"] = False
    with pytest.raises(ValueError, match="independent bypass"):
        load_room_traversal(rooms)
    target["optional_route_evidence"] = "Reviewed independent ordinary bypass to all AP targets"
    load_room_traversal(rooms)
