"""Verify the topology census against the actual generated AP graph."""
from collections import Counter

from test.general import setup_solo_multiworld

from .. import KirbyAmWorld
from ..tools.audit_room_topology import CIRCLE, MAIN, build_inventory


def test_room_inventory_matches_generated_regions_and_edges():
    report = build_inventory()
    world = setup_solo_multiworld(KirbyAmWorld, seed=914)
    assert set(report["nodes"]) == {region.name for region in world.regions}
    actual = Counter((region.name, exit.connected_region.name)
                     for region in world.regions for exit in region.exits)
    assert actual == Counter((row["from_region"], row["to_region"]) for row in report["edges"])


def test_summary_and_check_sinks_do_not_count_as_native_crossings():
    report = build_inventory()
    native = report["nodes"]
    assert native["REGION_COPY_ABILITY_ROOM/MAIN"]["native_room"] == 970
    assert native[CIRCLE]["native_room"] == 801
    assert report["rainbow_summary_has_central_bridge"]
    assert report["rainbow_summary_incoming_physical_compartments"]
    for row in report["edges"]:
        source, target = row["from_region"], row["to_region"]
        a, b = native[source]["native_room"], native[target]["native_room"]
        if row["kind"] == "cross_native_room_candidate":
            assert a is not None and b is not None and a != b
        elif row["kind"] == "same_native_room_candidate":
            assert a is not None and a == b
        if source == MAIN and target == CIRCLE:
            assert row["kind"] == "area_summary_bridge"
        assert native[source]["kind"] != "room_check_sink"


def test_room_check_feeders_keep_their_own_area_summary_link():
    report = build_inventory()
    edges = report["edges"]
    fan_in = {(row["from_region"], row["to_region"]) for row in edges
              if row["kind"] == "area_summary_fan_in"}
    for row in edges:
        if row["kind"] == "room_check_sink_link":
            source = row["from_region"]
            assert (source, source.split("/", 1)[0] + "/MAIN") in fan_in


def test_retail_join_counts_candidates_not_verified_paths():
    report = build_inventory()
    assert report["retail_cross_room_pair_counts"] == {
        "matching_room_pair": 459, "multiple_tile_doors": 54, "no_tile_match": 48,
    }
    candidates = [edge for edge in report["edges"]
                  if edge["from_region"] == "REGION_MOONLIGHT_MANSION/ROOM_2_14_UPPER"
                  and edge["to_region"].endswith("ROOM_2_15__LOGIC__UPPER_RETURN")]
    assert [door["arrival_tile"] for door in candidates[0]["retail_tile_door_candidates"]] == [[19, 8], [30, 29]]
    assert not report["nodes"][CIRCLE]["phone_return_room_flag"]
    assert report["nodes"]["REGION_RAINBOW_ROUTE/ROOM_1_08"]["phone_return_room_flag"]
