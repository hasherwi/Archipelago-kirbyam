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
                "pending_route_acceptance", "existing_normal_bypass", "conditional_source_witness"}
            assert cluster["note"].strip()
            if cluster["status"] == "existing_normal_bypass":
                assert room["native_room"] in {814, 819}
                assert cluster["classification"] == "bypass"


def test_accepted_coverage_links_to_the_exact_conditional_target() -> None:
    from ..traversal_data import room_traversal_targets
    targets = {row["id"]: row for row in room_traversal_targets("metal")}
    for room in read("dev-docs/ordinary-metal-coverage.json")["rooms"]:
        for cluster in room["clusters"]:
            if cluster["status"] != "conditional_source_witness":
                continue
            row = targets[cluster["accepted_target"]]
            assert row["native_room"] == room["native_room"]
            assert row["requires_guaranteed_source"] == cluster["requires_guaranteed_source"]


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
    assert counts == {"CanBreakBlocks": 0, "can_break_block": 137,
                      "can_break_floating_block": 18, "can_break_metal": 8, "can_break_metal_throw": 1}


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
            assert row["proposed_classification"] == cluster["classification"]
            assert row["status"] == "map_role_reviewed"
            assert row["evidence"] and row["limitations"] and row["sources"]
            assert cluster["status"] == "pending_route_acceptance"
            assert "accepted_target" not in cluster
            referenced.add(key)
    assert referenced == set(rows)
    assert review["remaining_route_uncertainties"]
