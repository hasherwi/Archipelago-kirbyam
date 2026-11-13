"""Validate retained observed outcomes, not a fresh native emulator replay."""

import json
from pathlib import Path

from ..client import KirbyAmClient
from ..data import data
from ..enemy_ability_data import ABILITY_NAME_TO_ID
from ..traversal import SourcePolicy

EVIDENCE = Path(__file__).parents[1] / "dev-docs" / "rainbow-green-source-runtime.json"
POSITIVES = ("accepted100-1hp", "accepted100-6hp", "accepted500-1hp", "accepted500-6hp")
CONTROLS = ("control-no-target-attack", "control-both-triggers")


def test_exact_native_source_entry_chest_and_policy():
    evidence = json.loads(EVIDENCE.read_text())
    source = evidence["source"]
    assert (source["template"], source["source_key"], source["type"], source["native_room"]) == (
        "0x088B9F90", "SPARKY", 25, 138)
    assert source["original_position"] == [496, 88]
    assert source["ability_id"] == ABILITY_NAME_TO_ID["Spark"] == 15
    assert source["source_policy"]["mode"] == 0
    assert SourcePolicy(source["source_policy"]).grant("SPARKY", lambda _: True).guaranteed == frozenset({"Spark"})
    access = evidence["access"]
    assert access["region"] == "REGION_RAINBOW_ROUTE/ROOM_1_27_UPPER_LEFT"
    assert (access["fixture_room"], access["destination_room"], access["door_source_tile"]) == (532, 138, [2, 3])
    target = evidence["target"]
    assert target["region"] == data.locations[target["location_key"]].parent_region == "REGION_RAINBOW_ROUTE/ROOM_1_28"
    assert target["location_key"] == "MINOR_CHEST_SPRAY_PAINT_04"
    assert target["lower_f1"] == [36, 13] and target["upper_f1"] == [37, 12]
    assert target["chest_template"] == "0x088B9FD8" and target["chest_flag"] == 7
    assert KirbyAmClient()._build_minor_chest_source_ptr_map()[0x8B9FD8] == target["location_id"] == 3960503
    assert evidence["configuration"]["ability_gating"] is False
    assert evidence["configuration"]["area_keys"] is False
    assert evidence["configuration"]["generation_seed"] == 138
    assert evidence["clearing_pause"]["start_frame"] == 3287 and evidence["clearing_pause"]["frames"] == 300


def test_observed_outcomes_preserve_hp_source_carry_and_write_boundary():
    evidence = json.loads(EVIDENCE.read_text())
    assert set(evidence["runs"]) == set(POSITIVES + CONTROLS)
    raw = evidence["source"]["source_policy"]
    expected_writes = {
        0x0203B064: 0, 0x0203B068: 0, 0x0203B06C: 0, 0x0203B070: 55,
        0x0203B074: sum(1 << ABILITY_NAME_TO_ID[name] for name in raw["allowed_abilities"]),
        0x0203B0B0: 0, 0x0203B0B4: 0, 0x0203B078: 0,
    }
    for run in evidence["runs"].values():
        assert run["hp_min"] == run["hp_max"] == run["hp"]
        sampled = run["sampled_outcomes"]
        assert sampled["first_gameplay_frame"] == 1085
        assert run["hp_samples"] == sampled["last_gameplay_frame"] - 1085 + 1
        assert all(sampled[key] for key in (
            "all_hp_preserved", "all_spark_retained", "all_helpers_absent", "all_natural_gating_off"))
        assert sampled["spark_retained_from_frame"] == 1544
        assert run["gameplay_ram_writes"] == run["state_restores"] == 0
        assert run["server_submission"] is False
        writes = run["configuration_writes"]
        assert len(writes) == 8
        assert {int(w["address"], 16): int.from_bytes(bytes.fromhex(w["value"]), "little")
                for w in writes} == expected_writes
        assert all(w["frame"] == 1085 and w["size"] == 4 and not w["guard_failed"]
                   and w["origin"] == "KirbyAmClient._sync_enemy_copy_ability_runtime_config" for w in writes)
        source, = run["source_observations"]
        assert int(source["template"], 16) == 0x088B9F90
        assert source["native_copy_field"] == 15 and source["type"] == 25
        assert source["hp"] == (4 if run["enemy_health_percent"] == 100 else 20)
        assert all(len(run[key]) == 64 for key in ("rom_sha256", "result_sha256", "per_frame_sha256"))
    assert {(evidence["runs"][name]["hp"], evidence["runs"][name]["enemy_health_percent"])
            for name in POSITIVES} == {(1, 100), (6, 100), (1, 500), (6, 500)}
    for name in POSITIVES:
        run = evidence["runs"][name]
        assert run["sampled_outcomes"]["upper_intact_in_138"]
        changes = {point["frame"]: point for point in run["changes"]}
        assert changes[1085]["room"] == 532 and changes[1085]["ability"] == 0
        assert changes[1302]["room"] == 138 and changes[1302]["ability"] == 0
        assert changes[1544]["ability"] == 15
        assert changes[3755]["lower"] == 0 and changes[3755]["upper"] == 0xF1
        assert changes[3989]["chest7"] and changes[3989]["event_counter"] == 1
        assert run["final"]["spray4"] is False
        assert int(run["event_ring"][0], 16) == 0x088B9FD8
        assert run["client_messages"] == [{"cmd": "LocationChecks", "locations": [3960503]}]


def test_matched_negative_controls_and_provenance_are_not_just_expectations():
    evidence = json.loads(EVIDENCE.read_text())
    inputs = evidence["controller_inputs"]
    assert inputs["columns"] == ["start", "frames", "keys"]
    assert [3287, 300, 2] in inputs["positive"]
    expected_control = [[start, frames, 0 if start == 3749 else keys]
                        for start, frames, keys in inputs["positive"]]
    assert inputs["no-target-attack"] == expected_control
    assert [row for row in inputs["both-triggers"] if row[0] < 3749] == [
        row for row in inputs["positive"] if row[0] < 3749]
    for name in CONTROLS:
        run = evidence["runs"][name]
        assert (run["hp"], run["enemy_health_percent"]) == (1, 500)
        assert run["rom_sha256"] == evidence["runs"]["accepted500-1hp"]["rom_sha256"]
        assert not run["final"]["chest7"] and run["final"]["event_counter"] == 0
        assert run["client_messages"] == [] and all(int(ptr, 16) == 0 for ptr in run["event_ring"])
    no_attack = evidence["runs"]["control-no-target-attack"]["final"]
    assert no_attack["lower"] == no_attack["upper"] == 0xF1
    both = evidence["runs"]["control-both-triggers"]
    assert both["final"]["lower"] == both["final"]["upper"] == 0
    trigger, = [point for point in both["changes"] if point["frame"] == 3774]
    assert trigger["lower"] == trigger["upper"] == 0  # Not strict upper-first.
    assert evidence["target"]["blocking_cell_positions"][:2] == [[38, 14], [38, 15]]
    assert both["final"]["blocking_cells"][:2] == [0x0D, 0x0D]
    provenance = evidence["provenance"]
    assert provenance["acceptance_sha256"] == "f3af360c536451bfb809ce6de95e04b2aa6ae638f7f9b04dfe41b288ec84a905"
    assert provenance["production_rebuild_byte_identical"]
    assert all(len(digest) == 64 for digest in provenance["artifact_sha256"].values())
    assert "50-99% and 101-499%" in " ".join(evidence["limits"])
    assert all(private not in EVIDENCE.read_text() for private in ("/home/", "/Users/", "C:\\"))
