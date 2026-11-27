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
                     for region in world.regions for exit in region.exits
                     if not exit.name.endswith("(Phone L)"))
    assert actual == Counter((row["from_region"], row["to_region"]) for row in report["edges"])


def test_summary_and_check_sinks_do_not_count_as_native_crossings():
    report = build_inventory()
    native = report["nodes"]
    assert native["REGION_COPY_ABILITY_ROOM/MAIN"]["native_room"] == 970
    assert native[CIRCLE]["native_room"] == 801
    assert not report["rainbow_summary_has_central_bridge"]
    assert report["rainbow_summary_incoming_physical_compartments"]
    for row in report["edges"]:
        source, target = row["from_region"], row["to_region"]
        a, b = native[source]["native_room"], native[target]["native_room"]
        if row["kind"] == "cross_native_room_candidate":
            assert a is not None and b is not None and a != b
        elif row["kind"] == "same_native_room_candidate":
            assert a is not None and a == b
        assert source != MAIN, f"Rainbow area summary must be a sink, not a route to {target}"
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
        "matching_room_pair": 459, "multiple_tile_doors": 57, "no_tile_match": 32,
    }
    candidates = [edge for edge in report["edges"]
                  if edge["from_region"] == "REGION_MOONLIGHT_MANSION/ROOM_2_14_UPPER"
                  and edge["to_region"].endswith("ROOM_2_15__LOGIC__UPPER_RETURN")]
    assert [door["arrival_tile"] for door in candidates[0]["retail_tile_door_candidates"]] == [[19, 8], [30, 29]]
    assert not report["nodes"][CIRCLE]["phone_return_room_flag"]
    assert report["nodes"]["REGION_RAINBOW_ROUTE/ROOM_1_08"]["phone_return_room_flag"]


def test_reconciliation_preserves_unresolved_routes_and_exact_landing_evidence():
    report = build_inventory()
    assert report["retail_door_reconciliation_counts"] == {
        "configured_non_tile": 7, "reviewed_parallel_ports": 12, "object_and_tile_candidates": 1, "pinned_tile_door": 36, "pinned_tile_group": 1,
        "shared_landing": 13, "single_tile_candidate": 452, "source_backed_boss_return": 8,
        "witnessed_non_tile": 18,
    }
    edges = {(row["from_region"].split("/")[-1], row["to_region"].split("/")[-1]): row
             for row in report["edges"] if row["kind"] == "cross_native_room_candidate"}

    def reviewed(source, target):
        return edges[source, target]["door_reconciliation"]

    assert reviewed("ROOM_2_14_UPPER", "ROOM_2_15__LOGIC__UPPER_RETURN")["door"]["arrival_tile"] == [19, 8]
    assert reviewed("ROOM_2_14", "ROOM_2_15")["door"]["arrival_tile"] == [30, 29]
    assert reviewed("ROOM_2_01_BOTTOM_RIGHT", "ROOM_2_11_DEAD_END")["door"]["trigger_tile"] == [28, 28]
    assert reviewed("ROOM_3_03__LOGIC__UPPER_LEFT", "ROOM_3_04_SUB")["door"]["trigger_tile"] == [5, 2]
    assert reviewed("ROOM_1_32", "ROOM_1_33_LEFT")["mechanism"] == "fuse_cannon"
    assert reviewed("ROOM_1_WARP", "ROOM_2_ENTRY")["mechanism"] == "warp_star"
    assert "arrival_tile" not in reviewed("ROOM_1_WARP", "ROOM_2_ENTRY")
    assert reviewed("ROOM_1_GOAL_2", "ROOM_1_CENTRAL_CIRCLE")["via_native_room"] == 980
    assert reviewed("ROOM_1_GOAL_2", "ROOM_1_CENTRAL_CIRCLE")["evidence"] == "goal-game-phone-successor.json"
    assert reviewed("ROOM_2_BOSS", "ROOM_1_CENTRAL_CIRCLE")["status"] == "source_backed_boss_return"
    assert len(edges["ROOM_5_06", "ROOM_5_05__LOGIC__CHUTE_SIDE"]["retail_tile_door_candidates"]) == 12
    assert reviewed("ROOM_5_06", "ROOM_5_05__LOGIC__CHUTE_SIDE") == {"status": "shared_landing"}

def test_carrot_compartments_keep_separate_native_landings():
    report = build_inventory()
    edges = {(row["from_region"].split("/")[-1], row["to_region"].split("/")[-1]): row
             for row in report["edges"] if row["kind"] == "cross_native_room_candidate"}
    lower = "ROOM_5_13__LOGIC__ENTRY_FROM_5_07"
    upper = "ROOM_5_13__LOGIC__ENTRY_FROM_5_14"
    assert edges["ROOM_5_07", lower]["door_reconciliation"]["door"]["arrival_tile"] == [13, 14]
    assert edges[lower, "ROOM_5_07"]["door_reconciliation"]["door"]["trigger_tile"] == [13, 13]
    assert edges[upper, "ROOM_5_14"]["door_reconciliation"]["door"]["trigger_tile"] == [2, 4]
    assert {tuple(door["arrival_tile"]) for door in
            edges["ROOM_5_14", upper]["retail_tile_door_candidates"]} == {(14, 5)}


def test_unsubstantiated_legacy_room_pairs_cannot_create_shortcuts():
    report = build_inventory()
    edges = [(row["from_region"], row["to_region"]) for row in report["edges"]]
    def has(source, target):
        return any(a.split("/")[-1] == source and b.split("/")[-1] == target for a, b in edges)
    assert not has("ROOM_0_02", "ROOM_0_01")
    assert not has("ROOM_6_06", "ROOM_6_05__LOGIC__ENTRY_FROM_6_04_OR_6_06")
    assert not has("ROOM_6_05__LOGIC__ENTRY_FROM_6_04_OR_6_06", "ROOM_6_04")
    assert not has("ROOM_6_23", "ROOM_6_05__LOGIC__ENTRY_FROM_6_23")
    assert not has("ROOM_5_WARP", "ROOM_5_13__LOGIC__ENTRY_FROM_5_18_OR_5_WARP")
    assert has("ROOM_5_WARP", "ROOM_7_04")
    assert has("ROOM_5_07", "ROOM_5_13__LOGIC__ENTRY_FROM_5_07")
    assert has("ROOM_5_14", "ROOM_5_13__LOGIC__ENTRY_FROM_5_14")


def test_olive_upper_and_lower_entries_keep_separate_destinations():
    report = build_inventory()
    edges = {(row["from_region"].split("/")[-1], row["to_region"].split("/")[-1]): row
             for row in report["edges"] if row["kind"] == "cross_native_room_candidate"}
    upper = "ROOM_6_05_SUBROOM"
    lower = "ROOM_6_05__LOGIC__ENTRY_FROM_6_04_OR_6_06"
    assert edges["ROOM_6_04", upper]["door_reconciliation"]["door"]["trigger_tile"] == [73, 6]
    assert edges["ROOM_6_04", upper]["door_reconciliation"]["door"]["arrival_tile"] == [2, 6]
    assert edges["ROOM_6_04", lower]["door_reconciliation"]["door"]["trigger_tile"] == [73, 18]
    assert edges["ROOM_6_04", lower]["door_reconciliation"]["door"]["arrival_tile"] == [3, 18]
    assert edges[upper, "ROOM_6_07"]["door_reconciliation"]["door"]["trigger_tile"] == [14, 14]
    assert edges[lower, "ROOM_6_06"]["door_reconciliation"]["door"]["trigger_tile"] == [43, 2]
    cannon = edges["ROOM_6_07", "ROOM_6_05__LOGIC__ENTRY_FROM_6_07"]
    assert cannon["door_reconciliation"]["status"] == "configured_non_tile"
    assert cannon["configured_transition_object"]["template_address"] == "0x088CD65C"
    assert cannon["configured_transition_object"]["configured_spawn_arguments"] == [27, 1]
    assert edges["ROOM_5_WARP", "ROOM_7_04"]["configured_transition_object"]["destination_native_room"] == 222
    control = edges["ROOM_1_32", "ROOM_1_33_LEFT"]
    assert control["door_reconciliation"]["status"] == "witnessed_non_tile"
    assert control["configured_transition_object"]["configured_spawn_arguments"] == [6, 1]

def test_distinct_compartment_pins_preserve_current_directions():
    report = build_inventory()
    edges = {(row["from_region"].split("/")[-1], row["to_region"].split("/")[-1]): row
             for row in report["edges"] if row["kind"] == "cross_native_room_candidate"}

    def result(source, target):
        return edges[source, target]["door_reconciliation"]

    assert result("ROOM_1_02", "ROOM_1_03_UPPER")["door"]["arrival_tile"] == [4, 4]
    assert result("ROOM_1_02", "ROOM_1_03_LOWER")["door"]["arrival_tile"] == [4, 9]
    assert result("ROOM_3_14", "ROOM_3_15_LOWER_ENTRY")["door"]["trigger_tile"] == [69, 17]
    assert result("ROOM_3_14", "ROOM_3_15_UPPER_ENTRY")["door"]["trigger_tile"] == [69, 5]
    assert result("ROOM_4_12", "ROOM_4_13")["door"]["arrival_tile"] == [30, 39]
    assert result("ROOM_4_12", "ROOM_4_13__LOGIC__CANNON_LEFT")["door"]["arrival_tile"] == [13, 36]
    assert result("ROOM_4_14", "ROOM_4_BOSS")["door"]["trigger_tile"] == [12, 2]
    assert result("ROOM_4_14__LOGIC__CANNON_LEFT", "ROOM_4_BOSS")["door"]["trigger_tile"] == [3, 2]
    assert result("ROOM_7_12", "ROOM_7_06")["door"]["arrival_tile"] == [18, 3]
    assert result("ROOM_7_12", "ROOM_7_06__LOGIC__HAPPY_NOTES_ENTRY")["door"]["arrival_tile"] == [27, 2]
    assert result("ROOM_2_20", "ROOM_2_GOAL_2")["door"]["arrival_tile"] == [59, 13]
    water = result("ROOM_2_20", "ROOM_2_GOAL_2_BOTTOM_RIGHT")
    assert water["status"] == "pinned_tile_group"
    assert {tuple(door["trigger_tile"]) for door in water["doors"]} == {
        (x, y) for x in (0, 1) for y in range(26, 30)}
    assert {tuple(door["arrival_tile"]) for door in water["doors"]} == {(60, 19)}


def test_candy_13_arrivals_do_not_borrow_each_others_exit():
    report = build_inventory()
    prefix = "REGION_CANDY_CONSTELLATION/ROOM_9_"
    lower = prefix + "13"
    upper = lower + "__LOGIC__UPPER_WARP"
    sink = lower + "__ROOM_CHECK"
    assert report["nodes"][lower]["native_room"] == report["nodes"][upper]["native_room"] == 419
    edges = {(row["from_region"], row["to_region"]): row for row in report["edges"]}
    for comp, arrival, own_exit, other_exit in (
        (lower, [3, 15], prefix + "CHEST_3", prefix + "WARP"),
        (upper, [3, 4], prefix + "WARP", prefix + "CHEST_3"),
    ):
        assert edges[prefix + "12", comp]["door_reconciliation"]["door"]["arrival_tile"] == arrival
        assert (comp, own_exit) in edges
        assert (comp, other_exit) not in edges
        assert (comp, sink) in edges
    assert (lower, upper) not in edges and (upper, lower) not in edges
    assert not any(source == sink for source, _ in edges)


def test_peppermint_10_channels_own_only_their_reviewed_objectives():
    prefix = "REGION_PEPPERMINT_PALACE/ROOM_7_"
    left = prefix + "10"
    middle = left + "__LOGIC__CENTER_WARP"
    right = left + "__LOGIC__RIGHT_SPRAY"
    sink = left + "__ROOM_CHECK"
    report = build_inventory()
    edges = {(row["from_region"], row["to_region"]): row for row in report["edges"]}
    from ..data import data
    for comp, arrival in ((left, [17, 29]), (middle, [23, 29]), (right, [29, 29])):
        assert edges[prefix + "09", comp]["door_reconciliation"]["door"]["arrival_tile"] == arrival
        assert set(data.regions[comp].exits) == ({sink, prefix + "WARP"} if comp == middle else {sink})
    assert set(data.regions[left].locations) == {
        "MINOR_CHEST_PEPPERMINT_PALACE_7_10_OBJECT_02", "MINOR_CHEST_PEPPERMINT_PALACE_7_10_OBJECT_03"}
    assert data.regions[right].locations == ["MINOR_CHEST_SPRAY_PAINT_09"]
    assert not data.regions[middle].locations
    assert data.regions[sink].locations == ["ROOM_SANITY_7_10"]

def test_parallel_ports_keep_both_native_directions_and_state_limits():
    edges = {(row["from_region"].split("/")[-1], row["to_region"].split("/")[-1]): row
             for row in build_inventory()["edges"] if row["kind"] == "cross_native_room_candidate"}
    water = edges["ROOM_7_14", "ROOM_7_16"]
    assert len(water["retail_tile_door_candidates"]) == 16
    assert water["door_reconciliation"]["status"] == "reviewed_parallel_ports"
    assert len(water["door_reconciliation"]["arrival_geometry"]) == 4
    # An optimistic join does not make the strict sets equal.
    rainbow = edges["ROOM_1_17", "ROOM_1_18"]["door_reconciliation"]["arrival_geometry"]
    assert rainbow[0]["strict"]["exits"] == [172]
    assert rainbow[1]["strict"]["exits"] == [175, 508]
    assert rainbow[0]["optimistic"]["exits"] == rainbow[1]["optimistic"]["exits"]
    cannon = edges["ROOM_4_13__LOGIC__CANNON_LEFT", "ROOM_4_14__LOGIC__CANNON_LEFT"]
    assert cannon["door_reconciliation"]["status"] == "configured_non_tile"
    assert cannon["configured_transition_object"]["configured_spawn_arguments"] == [2, 1]
    mirror = edges["ROOM_4_13", "ROOM_4_14"]
    assert mirror["door_reconciliation"]["status"] == "single_tile_candidate"
    assert "configured_transition_object" not in mirror
    radish = edges["ROOM_8_16", "ROOM_8_17"]
    assert radish["door_reconciliation"]["status"] == "object_and_tile_candidates"
    assert radish["retail_tile_door_candidates"] and radish["configured_transition_object"]
