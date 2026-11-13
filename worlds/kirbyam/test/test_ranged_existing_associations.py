"""Exact documentary joins to existing evidence; no ROM or new native witness."""

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from .evidence_helpers import canonical_text_bytes

ROOT = Path(__file__).parents[1] / "dev-docs"


def read(name: str) -> dict[str, Any]:
    result: dict[str, Any] = json.loads(canonical_text_bytes(ROOT / name))
    return result


def validate(association: dict[str, Any], census: dict[str, Any], acceptance: dict[str, Any]) -> None:
    assert association["status"] == "documentary_existing_evidence_association_only"
    assert association["native_room"] == 228
    for key in ("accounting_change", "new_native_evidence", "new_target_or_witness", "policy_fallback_change"):
        assert association[key] is False
    assert association["outcome"]["location_id"] == 3960593
    assert association["outcome"]["target"] == "metal_229_left1up"
    assert association["health_percent"] == [100, 500]
    assert (association["actual_hp"], association["ability"], association["grab"]) == (6, 17, 0)
    assert association["initial_collision_sha256"] == (
        "56532c5fe675ab903093ff23ed5fb89ef98a6b815cd13339fa57fe4f4f4a1603")
    expected = [("228:27,7", "bomb27", 27, 7), ("228:12,11", "bomb12", 12, 11)]
    assert len(association["associations"]) == 2
    room, = (r for r in census["tile_targets"] if r["native_room"] == 228)
    assert sorted(r["health_percent"] for r in acceptance["acceptances"]) == [100, 500]
    for item, (group, segment, x, y) in zip(association["associations"], expected):
        assert (item["group"], item["segment"]) == (group, segment)
        changes = [{"x": x, "y": y, "before": 241, "after": 0},
                   {"x": x, "y": y + 1, "before": 242, "after": 0}]
        assert item["mutations"] == changes
        assert {"tile": "0xF1", "x": x, "y": y} in room["targets"]
        mutation = next(r for r in room["related_mutation_records"] if (r["x"], r["y"]) == (x, y))
        assert (mutation["kind"], mutation["attribute"], mutation["replacement"]) == (1, "0xF1", "0x00")
        for run in acceptance["acceptances"]:
            assert run["initial_collision_sha256"] == association["initial_collision_sha256"]
            assert run["accepted_left1up"] and run["runtime_writes"] == []
            record, = (s for s in run["segments"] if s["name"] == segment)
            assert record["collision_changes"] == changes
            assert record["minimum_hp"] == record["initial"]["hp"] == record["final"]["hp"] == 6
            assert record["abilities"] == [17] and record["grab_values"] == [0]
            assert run["final"]["room"] == 229 and run["final"]["flag33"] == 2
            assert run["final"]["flag32"] == run["final"]["flag34"] == 0
    assert acceptance["parent_finite_228_blob"] == "d050d3a81c862617fc45cf8fde2a6c61d158d5bd"
    assert acceptance["matching_renewable_229_suffix_blob"] == "9f96dfb3a558f59efe130d8b2abb6aecb0d94291"
    limits = acceptance["inherited_finite_source_qualification"]
    assert "not a new combined Bonkers fight/capture replay" in limits["source"]
    assert "Hammer statue" in limits["inherited_fixture"]
    assert "post-defeat release fixture" in limits["inherited_fixture"]
    assert "not a full generated AP seed or direct1HP replay" in limits["health"]
    assert "no change to Spray32, food34, Warp or generic229" in acceptance["scope"]


def test_existing_associations_match_current_census_and_both_acceptances() -> None:
    association = read("ranged-existing-evidence-associations.json")
    assert set(association["sources"]) == {
        "ranged-static-target-census.json", "ordinary-229-finite-hammer-left1up-acceptance.json"}
    for name, pin in association["sources"].items():
        assert hashlib.sha256(canonical_text_bytes(ROOT / name)).hexdigest() == pin["canonical_text_sha256"]
    validate(association, read("ranged-static-target-census.json"),
             read("ordinary-229-finite-hammer-left1up-acceptance.json"))


@pytest.mark.parametrize("mutation", ["count", "outcome", "cell", "fingerprint", "health500", "missing500",
                                      "grab", "census", "fixture"])
def test_association_rejects_scope_or_evidence_drift(mutation: str) -> None:
    association = copy.deepcopy(read("ranged-existing-evidence-associations.json"))
    census = read("ranged-static-target-census.json")
    acceptance = read("ordinary-229-finite-hammer-left1up-acceptance.json")
    run = next(r for r in acceptance["acceptances"] if r["health_percent"] == 500)
    segment = next(s for s in run["segments"] if s["name"] == "bomb12")
    if mutation == "count":
        association["accounting_change"] = True
    elif mutation == "outcome":
        association["outcome"]["location_id"] = 3960592
    elif mutation == "cell":
        segment["collision_changes"][1]["after"] = 80
    elif mutation == "fingerprint":
        run["initial_collision_sha256"] = "0" * 64
    elif mutation == "health500":
        segment["minimum_hp"] = 1
    elif mutation == "missing500":
        acceptance["acceptances"].remove(run)
    elif mutation == "grab":
        segment["grab_values"] = [1]
    elif mutation == "census":
        room = next(r for r in census["tile_targets"] if r["native_room"] == 228)
        room["targets"].remove({"tile": "0xF1", "x": 12, "y": 11})
    else:
        acceptance["inherited_finite_source_qualification"]["inherited_fixture"] = "ordinary source"
    with pytest.raises(AssertionError):
        validate(association, census, acceptance)
