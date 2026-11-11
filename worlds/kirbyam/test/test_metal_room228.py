"""Joint finite-Hammer witness shares one fail-closed target with renewable970."""

from dataclasses import replace

import pytest

from ..data import data
from ..traversal import METAL_BREAKING_ABILITIES, Position, SourcePolicy, TraversalGraph
from ..traversal_data import room_traversal_graph, room_traversal_targets
from .test_traversal import policy


OWNER = "REGION_PEPPERMINT_PALACE/ROOM_7_09"
LOCATION = "MINOR_CHEST_PEPPERMINT_PALACE_7_09"
END = "metal_228:chest"


def joint_graph() -> TraversalGraph:
    return room_traversal_graph("metal_228_chest", "bonkers_joint")


def test_one_fail_closed_target_leaves_rope_check_and_ordinary_exits_unchanged() -> None:
    row, = (row for row in room_traversal_targets("metal") if row["id"] == "metal_228_chest")
    assert set(row["graphs"]) == {"bonkers_joint", "copy_room_statues"}
    assert row["location"] == LOCATION and "requires_guaranteed_source" not in row
    assert LOCATION in data.regions[OWNER].locations
    assert "MINOR_CHEST_PEPPERMINT_PALACE_7_09_OBJECT_02" in data.regions[OWNER].locations
    assert set(data.regions[OWNER].exits) == {"REGION_PEPPERMINT_PALACE/ROOM_7_10"}


def test_joint_graph_reuses_exact205_prefix_and_one_finite_source() -> None:
    graph = joint_graph()
    prefix = room_traversal_graph("metal_205_to_209_top", "bonkers_carry")
    prefix_nodes = {node.key for node in prefix.nodes}
    assert tuple(node for node in graph.nodes if node.key in prefix_nodes) == prefix.nodes
    assert tuple(route for route in graph.routes if route.target in prefix_nodes) == prefix.routes
    assert graph.starts == prefix.starts and graph.access_region == prefix.access_region
    assert graph.placements == prefix.placements
    assert len(graph.nodes) == 9 and len(graph.routes) == 8
    source, = graph.placements
    assert source.identity == "0x088BF730" and source.source_key == "BONKERS"
    assert not source.renewable and not source.retry_evidence
    assert not any(s.node.startswith("metal_228:") for s in graph.placements)
    result = graph.evaluate(SourcePolicy({"mode": 0}), frozenset({"Hammer Ability"}), True)
    assert result.reaches("metal_205:209_top") and result.reaches(END)
    finals = [p for p in result.positions if p.node == END and p.equipped == "Hammer"]
    assert finals and all(p.consumed == {source.identity} and not p.opened for p in finals)
    assert not any(route.source == END for route in graph.routes)


@pytest.mark.parametrize("mode,minibosses,pool,weight,expected", [
    (0, True, None, 0, True), (1, False, ["Stone"], 0, True), (2, False, ["Stone"], 100, True),
    (1, True, ["Hammer"], 0, True), (1, True, ["Stone"], 0, False),
    (2, True, ["Hammer"], 0, True), (2, True, ["Hammer", "Stone"], 0, False),
    (2, True, ["Hammer"], 50, False), (2, True, ["Hammer"], 100, False),
])
def test_joint_finite_policy_is_not_a_renewable_or_permission_only_grant(
    mode: int, minibosses: bool, pool: list[str] | None, weight: int, expected: bool,
) -> None:
    graph = joint_graph()
    resolver = policy(mode, minibosses=minibosses, pool=pool, weight=weight)
    assert graph.evaluate(resolver, frozenset({"Hammer Ability", "Stone Ability"}), True,
                          allow_documented_retries=True).reaches(END) is expected
    assert not graph.evaluate(resolver, frozenset(), True, allow_documented_retries=True).reaches(END)


def test_no_source_behind_target_or_reacquisition_after_dropping() -> None:
    graph = joint_graph()
    source, = graph.placements
    resolver = SourcePolicy({"mode": 0})
    owned = frozenset({"Hammer Ability"})
    for invalid in (replace(graph, placements=()),
                    replace(graph, placements=(replace(source, node=END),)),
                    replace(graph, starts=(Position("metal_205:209_top"),)),
                    replace(graph, starts=(Position("metal_228:205_water_return"),))):
        assert not invalid.evaluate(resolver, owned, True).reaches(END)


@pytest.mark.parametrize("ability", sorted(METAL_BREAKING_ABILITIES | {"Normal"}))
def test_exact_joint_suffix_accepts_only_retained_hammer(ability: str) -> None:
    graph = joint_graph()
    isolated = replace(graph, placements=(), starts=(Position("metal_205:209_top", ability),))
    assert isolated.evaluate(SourcePolicy({"mode": 0}), frozenset(), True).reaches(END) is (ability == "Hammer")
    suffix = [r for r in graph.routes if r.target.startswith("metal_228:")]
    assert len(suffix) == 3
    assert all(r.opens is None and not r.resets_room_instance and not r.preserves_room_instance
               and not r.recover_dropped_ability and r.uses_object is None for r in suffix)
    metal, = (r for r in suffix if r.capability)
    assert metal.capability == "metal" and metal.water_state == "dry"
    assert metal.allowed_abilities == frozenset({"Hammer"}) and not metal.room_transition
    assert {r.target for r in suffix} == {"metal_228:205_water_return", "metal_228:228_lower_arrival", END}


def test_finite_hammer_pool_gate_filter_does_not_credit_mixed_equipment() -> None:
    graph = joint_graph()
    resolver = policy(2, pool=['Hammer', 'Stone'], weight=0)
    assert graph.evaluate(resolver, frozenset({'Hammer Ability'}), True).reaches(END)
    assert not graph.evaluate(resolver, frozenset({'Hammer Ability', 'Stone Ability'}), True).reaches(END)
    assert not graph.evaluate(resolver, frozenset({'Stone Ability'}), True).reaches(END)
