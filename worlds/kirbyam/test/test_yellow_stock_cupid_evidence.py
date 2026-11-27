"""Stock Carrot Yellow physical proof, intentionally not a world-access rule."""
from dataclasses import replace
import json
from pathlib import Path

import pytest

from .. import traversal_data
from ..ability_source_inventory import source_inventory
from ..data import data
from ..traversal import SourcePolicy

CATALOG = Path(__file__).parents[1] / "dev-docs" / "carrot-yellow-cupid-admission.json"
LOCATION = "MINOR_CHEST_SPRAY_PAINT_02"
STOCK = SourcePolicy({"mode": 0})


@pytest.fixture
def catalog():
    return json.loads(CATALOG.read_text(encoding="utf-8"))


@pytest.fixture
def packet(catalog):
    return catalog["stock_witness"]


@pytest.fixture
def graph(packet):
    return traversal_data.compile_room_graph(packet["graph"], {}, advanced=True, require_inventory=True)


def test_exact_award_and_native_source(catalog, packet, graph):
    evidence = packet["evidence"]
    location = data.locations[LOCATION]
    award = catalog["target"]
    assert award["location"] == LOCATION
    assert location.location_id == award["id"]
    assert location.source_rom_offset == int(award["chest_template"], 16) - 0x08000000
    assert location.label == "Carrot Castle 5-16 - Spray Paint #2 Chest"
    assert (award["chest_template"], award["chest_flag"]) == ("0x088D3DD0", 80)
    assert evidence["native_award_confirmed"] and not evidence["ap_acknowledgment"]
    source, = graph.placements
    record = source_inventory()[source.identity]
    assert (record["native_room"], record["position_pixels"], record["source_key"]) == (734, [72, 192], "CUPIE")
    target, = graph.required_targets
    result = graph.evaluate(STOCK, frozenset(), gating=False)
    assert result.reaches(target) and not result.retry_assumptions
    assert graph.access_region is None and not evidence["standard_source_proven"]
    assert any(position.node == target and "Cupid" in position.equipment_outcomes for position in result.positions)


def test_carry_counts_actual_native_room_changes(packet, graph):
    by_node = {node.key: node.room for node in graph.nodes}
    assert [by_node[node.key] for node in graph.nodes] == [734, 719, 719, 720, 734, 720, 730, 730, 730,
                                                          733, 733, 733, 733]
    crossed = sum(by_node[edge.source] != by_node[edge.target] for edge in graph.routes)
    assert crossed == packet["evidence"]["native_room_crossings_after_copy"] == 6
    assert sum(edge.room_transition for edge in graph.routes) == crossed
    mirrors = [edge for edge in packet["graph"]["routes"] if "self-mirror" in edge["evidence"]]
    assert len(mirrors) == packet["evidence"]["same_room_mirror_transitions"] == 3
    assert all(by_node[edge["from"]] == by_node[edge["to"]] for edge in mirrors)
    assert crossed > 3 and packet["evidence"]["carry_tier"] == "advanced"


@pytest.mark.parametrize("capability", ["bomb_733_cupid_upper_from_below", "bomb_733_cupid_lower_from_corridor"])
def test_each_trigger_is_needed(graph, capability):
    target, = graph.required_targets
    blocked = replace(graph, routes=tuple(route for route in graph.routes if route.capability != capability))
    assert not blocked.evaluate(STOCK, frozenset(), gating=False).reaches(target)


def test_permission_does_not_replace_source_or_carry(graph):
    target, = graph.required_targets
    assert not graph.evaluate(STOCK, frozenset(), gating=True).reaches(target)
    assert graph.evaluate(STOCK, frozenset({"Cupid Ability"}), gating=True).reaches(target)
    assert not replace(graph, placements=()).evaluate(STOCK, frozenset({"Cupid Ability"}), gating=True).reaches(target)
    misplaced = replace(graph.placements[0], node=target)
    assert not replace(graph, placements=(misplaced,)).evaluate(STOCK, frozenset(), gating=False).reaches(target)


def test_interrupted_carry_is_not_a_valid_route(graph):
    target, = graph.required_targets
    routes = tuple(replace(route, loses_equipment=True) if route.target.endswith(":entry_730") else route
                   for route in graph.routes)
    assert not replace(graph, routes=routes).evaluate(STOCK, frozenset(), gating=False).reaches(target)
