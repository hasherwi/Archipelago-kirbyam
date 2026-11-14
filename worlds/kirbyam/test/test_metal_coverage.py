"""The ordinary-metal worklist must cover every native F5 cluster and AP owner."""

import json
from pathlib import Path
from typing import Any

from ..data import LocationCategory, data


ROOT = Path(__file__).parents[1]


def read(relative: str) -> Any:
    return json.loads((ROOT / relative).read_text())


def native_clusters() -> dict[int, dict[str, tuple[int, list[int]]]]:
    result: dict[int, dict[str, tuple[int, list[int]]]] = {}
    for room in read("docs/metal-tile-inventory.json")["rooms"]:
        pending = {(tile["x"], tile["y"]) for tile in room["tiles"] if tile["tile"] == "0xf5"}
        if not pending:
            continue
        clusters = {}
        while pending:
            seed = min(pending)
            pending.remove(seed)
            queue, reached = [seed], {seed}
            while queue:
                x, y = queue.pop()
                neighbors = {(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)} & pending
                queue.extend(neighbors)
                reached |= neighbors
                pending -= neighbors
            xs, ys = [point[0] for point in reached], [point[1] for point in reached]
            identity = f"{room['room']}:{min(xs)},{min(ys)}"
            assert identity not in clusters
            clusters[identity] = (len(reached), [min(xs), min(ys), max(xs), max(ys)])
        result[room["room"]] = clusters
    return result


def test_coverage_matrix_accounts_for_every_f5_component_exactly_once() -> None:
    expected = native_clusters()
    matrix = read("dev-docs/ordinary-metal-coverage.json")
    actual = {}
    for room in matrix["rooms"]:
        clusters = {cluster["id"]: (cluster["tile_count"], cluster["bounds"]) for cluster in room["clusters"]}
        assert len(clusters) == len(room["clusters"])
        assert room["native_room"] not in actual
        actual[room["native_room"]] = clusters
    assert actual == expected
    assert len(actual) == 33
    assert sum(map(len, actual.values())) == 81
    assert sum(count for clusters in actual.values() for count, bounds in clusters.values()) == 358


def test_matrix_preserves_current_ap_checks_and_compartment_exits() -> None:
    mapping = {row["native_id"]: row for row in read("dev-docs/native-room-wikirby-map.json")["rooms"]}
    for room in read("dev-docs/ordinary-metal-coverage.json")["rooms"]:
        expected = set(mapping[room["native_room"]]["ap_keys"])
        expected |= {key + "__ROOM_CHECK" for key in list(expected) if key + "__ROOM_CHECK" in data.regions}
        assert {part["region"] for part in room["ap_compartments"]} == expected
        for part in room["ap_compartments"]:
            source = data.regions[part["region"]]
            assert set(part["item_checks"]) == {
                key for key in source.locations if data.locations[key].category != LocationCategory.ROOM_SANITY}
            assert part["room_sanity"] == any(
                data.locations[key].category == LocationCategory.ROOM_SANITY for key in source.locations)
            assert set(part["exits"]) == set(source.exits)


def test_every_cluster_has_an_explicit_status_without_inventing_gate_acceptance() -> None:
    matrix = read("dev-docs/ordinary-metal-coverage.json")
    for room in matrix["rooms"]:
        for cluster in room["clusters"]:
            assert cluster["classification"] in matrix["categories"]
            assert cluster["status"] in {
                "pending_route_acceptance", "existing_normal_bypass", "conditional_source_witness",
                "reviewed_source_witness", "existing_mechanism_witness"}
            assert cluster["note"].strip()
            if cluster["status"] == "existing_normal_bypass":
                assert room["native_room"] in {502, 529, 532, 736, 814, 819}
                assert cluster["classification"] == "bypass"


def test_beam_only_release_has_no_pending_mandatory_metal_cluster() -> None:
    """Keep the native evidence census separate from generated graph feasibility."""
    from ..enemy_ability_data import starting_copy_abilities

    assert all(starting_copy_abilities(mode) == ("Beam", "Ice") for mode in range(3))
    for room in read("dev-docs/ordinary-metal-coverage.json")["rooms"]:
        for cluster in room["clusters"]:
            assert cluster["classification"] != "unknown", cluster["id"]
            if cluster["classification"] in {"ap_exit", "ap_target"}:
                assert cluster["status"] in {"reviewed_source_witness", "existing_mechanism_witness"}, cluster["id"]
            elif cluster["classification"] == "bypass":
                assert cluster["status"] == "existing_normal_bypass", cluster["id"]
            else:
                assert cluster["classification"] in {"scenery_no_required_passage", "optional_non_ap_pickup"}
                assert cluster["status"] == "pending_route_acceptance"


def test_accepted_coverage_links_to_the_exact_conditional_target() -> None:
    from ..traversal_data import room_traversal_graph, room_traversal_targets
    targets = {row["id"]: row for row in room_traversal_targets("metal")}
    for room in read("dev-docs/ordinary-metal-coverage.json")["rooms"]:
        for cluster in room["clusters"]:
            if cluster["status"] not in {"conditional_source_witness", "reviewed_source_witness"}:
                continue
            identities = cluster.get("accepted_targets") or [cluster["accepted_target"]]
            assert identities and len(identities) == len(set(identities))
            for identity in identities:
                row = targets[identity]
                # The accepted target may be across a door (205 floor -> 209).
                # Pin the actual metal action to the inventoried obstacle room.
                for witness in row["graphs"]:
                    graph = room_traversal_graph(identity, witness)
                    native_rooms = {node.key: node.room for node in graph.nodes}
                    bypasses = cluster.get("bypass_witnesses", {})
                    if witness in bypasses.get(identity, []):
                        assert cluster["id"] == "141:5,7" and identity == "metal_141_left_reverse"
                        assert set(bypasses[identity]) == {"central_statues", "rainbow190_statues"}
                        assert graph.access_region is not None
                        assert not any(route.capability == "metal" for route in graph.routes)
                        assert any(route.capability == "ordinary_block_hit"
                                   and native_rooms[route.source] == 141 for route in graph.routes)
                    else:
                        assert any(route.capability == "metal"
                                   and native_rooms[route.source] == room["native_room"]
                                   for route in graph.routes)
                    assert {native_rooms[target] for target in graph.required_targets} == {row["native_room"]}
                if cluster["status"] == "conditional_source_witness":
                    assert row["requires_guaranteed_source"] == cluster["requires_guaranteed_source"]
                else:
                    assert "requires_guaranteed_source" not in row
                    assert "requires_guaranteed_source" not in cluster


def test_placeholder_summary_includes_aliases_without_declaring_metal_gates() -> None:
    audit = read("dev-docs/ordinary-metal-coverage.json")["legacy_block_placeholder_audit"]
    counts = dict.fromkeys(audit["counts"], 0)

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
        elif isinstance(value, str) and value in counts:
            counts[value] += 1

    for path in (ROOT / "data").rglob("*.json"):
        visit(json.loads(path.read_text()))
    assert counts == audit["counts"]
    assert counts == {"CanBreakBlocks": 0, "can_break_block": 139,
                      "can_break_floating_block": 20, "can_break_metal": 6, "can_break_metal_throw": 0}


def test_map_role_review_does_not_promote_route_acceptance() -> None:
    matrix = read("dev-docs/ordinary-metal-coverage.json")
    review = read("dev-docs/" + matrix["role_review_record"])
    rows = {row["cluster_id"]: row for row in review["updates"]}
    assert len(rows) == len(review["updates"]) == 47
    referenced = set()
    for room in matrix["rooms"]:
        for cluster in room["clusters"]:
            if "role_review_cluster_id" not in cluster:
                continue
            key = cluster["role_review_cluster_id"]
            assert key == cluster["id"]
            row = rows[key]
            assert row["native_room"] == room["native_room"]
            historical_role = cluster.get("role_review_classification", cluster["classification"])
            assert row["proposed_classification"] == historical_role
            assert row["status"] == "map_role_reviewed"
            assert row["evidence"] and row["limitations"] and row["sources"]
            if cluster["status"] in {"existing_normal_bypass", "existing_mechanism_witness"}:
                # The map role itself remains unchanged. Later, separately
                # audited fresh native routes establish the directed bypass.
                assert cluster["accepted_evidence"]
                assert all((ROOT / "dev-docs" / path).is_file() for path in cluster["accepted_evidence"])
            else:
                assert cluster["status"] == "pending_route_acceptance"
            assert "accepted_target" not in cluster
            referenced.add(key)
    assert referenced == set(rows)
    assert review["remaining_route_uncertainties"]
