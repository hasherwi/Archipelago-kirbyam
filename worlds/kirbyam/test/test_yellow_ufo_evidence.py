"""Validate sanitized recorded outcomes, not a fresh native emulator replay."""

import json
from pathlib import Path

from ..client import KirbyAmClient
from ..data import data
from ..traversal import SourcePolicy

EVIDENCE = Path(__file__).parents[1] / "dev-docs" / "carrot-yellow-ufo-source-runtime.json"


def evidence():
    return json.loads(EVIDENCE.read_text())


def test_exact_source_policy_access_and_sole_chest():
    e = evidence()
    assert e["model"] == {
        "target": "bomb_733_yellow", "access_region": "REGION_CARROT_CASTLE/ROOM_5_14",
        "access_native_room": 720, "owner_region": "REGION_CARROT_CASTLE/ROOM_5_16"}
    target = e["target"]
    assert target["location"] == "MINOR_CHEST_SPRAY_PAINT_02"
    assert data.locations[target["location"]].parent_region == e["model"]["owner_region"]
    assert KirbyAmClient()._build_minor_chest_source_ptr_map()[0x8D3DD0] == target["location_id"] == 3960501
    assert (target["native_room"], target["native_chest_bit"], target["suppressed_native_spray_bit"]) == (733, 80, 1)
    assert target["lower_f1"] == [21, 6] and target["upper_f1"] == [18, 2]
    policy = e["source_policy"]
    assert policy["mode"] == 1 and len(policy["allowed_abilities"]) == 25
    assert policy["seed"] == 5662892934360856578 and e["production_seed"] == 8
    assert policy["ability_randomization_no_ability_weight"] == 0
    assert SourcePolicy(policy).grant("SPARKY", lambda _: True).guaranteed == frozenset({"UFO"})
    assert [s["template"] for s in e["source_instances"]] == ["0x088D4FC0", "0x088D4F9C"]
    assert [s["coordinate"] for s in e["source_instances"]] == [[344, 296], [344, 664]]
    assert e["source_observations"] == {
        "type": 25, "native_copy_field": 14, "hp_by_enemy_health_percent": {"100": 4, "500": 20}}


def test_normal_ingress_is_directed_and_discard_is_explicit():
    e = evidence()
    a = e["access"]
    assert a["fixture_room"] == 719 and a["fixture_position"] == [232, 56]
    assert [(t["source"], t["destination"]) for t in a["native_ingress"]] == [
        (719, 720), (720, 734), (734, 720), (720, 730)]
    assert [t["spawn_tile"] for t in a["native_ingress"]] == [[119, 8], [14, 5], [11, 8], [29, 4]]
    assert a["transition_frames"] == [1172, 3844, 4136, 4313]
    assert not a["left720_chain_activated"] and not a["left720_trigger_activated"]
    phases = e["full_route_ability_phases"]
    assert [p["frame"] for p in phases] == [1085, 5450, 6830, 6994]
    assert "Select discard" in phases[2]["ability"]
    assert "lower original" in phases[3]["ability"] and "intact until final" in phases[3]["ability"]


def test_all_sixteen_new_cases_and_twelve_qualified_earlier_cases():
    e = evidence()
    rows = e["accepted_cases"]
    assert len(rows) == 16 and all(r["passed"] for r in rows)
    expected = {(hp, health) for hp in (1, 6) for health in (100, 500)}
    for scenario in ("ingress", "positive", "no-target-attack", "medium-charge"):
        assert {(r["hp"], r["enemy_health_multiplier"]) for r in rows if r["scenario"] == scenario} == expected
    for hp, health in expected:
        matched = [r for r in rows if r["family"] == "full"
                   and (r["hp"], r["enemy_health_multiplier"]) == (hp, health)]
        assert len({r["rom_sha256"] for r in matched}) == 1
    earlier = e["earlier_left_arrival_packet"]
    assert "left-arrival" in earlier["qualification"]
    assert len(earlier["accepted_cases"]) == 12
    for scenario in ("positive", "no-target-attack", "medium-charge"):
        assert {(r["hp"], r["enemy_health_multiplier"]) for r in earlier["accepted_cases"]
                if r["scenario"] == scenario} == expected
    for r in rows + earlier["accepted_cases"]:
        f = r["final"]
        assert r["hp_min"] == r["hp_max"] == r["hp"] == f["hp"] == f["max_hp"]
        assert r["hp_sample_count"] == f["frame"] - 1085 + 1
        assert r["configuration_write_count"] == 8
        assert r["gameplay_ram_writes"] == r["state_restores"] == 0
        assert (f["ai"], f["humans"], f["mode"], f["gate_mask"]) == (0, 1, 1, 0)
        assert not f["native_spray1"]
        assert all(len(r[k]) == 64 and int(r[k], 16) >= 0 for k in ("rom_sha256", "per_frame_sha256"))
        positive = r["scenario"] == "positive"
        assert f["chest80"] is positive and f["event_counter"] == int(positive)
        assert r["client_messages"] == ([{"cmd": "LocationChecks", "locations": [3960501]}] if positive else [])
        if r["scenario"] == "ingress":
            assert f["room"] == 730 and f["ability"] == 0 and f["frame"] == 4357
        else:
            assert f["room"] == 733 and f["ability"] == 14 and f["upper"] == 241
            assert f["lower"] == (0 if positive else 241)
            assert f["blocking_cells"] == [0 if positive else 242] * 6
        if r["family"] == "earlier-left-arrival":
            assert int(r["event_ring"][0], 16) == (0x088D3DD0 if positive else 0)


def test_target_window_controls_provenance_and_write_boundary():
    e = evidence()
    inputs = e["controller_inputs"]
    schedule = inputs["full_positive"]
    assert [8071, 160, 2] in schedule and [6829, 1, 4] in schedule and [6520, 180, 0] in schedule
    assert all(start + frames == following[0] for (start, frames, _), following in zip(schedule, schedule[1:]))
    assert schedule[-1][0] + schedule[-1][1] == 8671
    assert inputs["target_window_controls"] == {
        "no-target-attack": [[8071, 160, 0]], "medium-charge": [[8071, 90, 2], [8161, 70, 0]]}
    target = e["target"]
    assert (target["lower_trigger_cleared_frame"], target["physical_chest_event_frame"]) == (8257, 8613)
    config = e["configuration"]
    assert config["configuration_frame"] == 1085 and config["configuration_write_count"] == 8
    assert config["configuration_writer"] == "KirbyAmClient._sync_enemy_copy_ability_runtime_config"
    assert all(config[k] is False for k in ("server_submission", "helpers", "ability_gating", "area_keys"))
    for packet in e["provenance"].values():
        assert all(len(digest) == 64 and int(digest, 16) >= 0 for digest in packet.values())
    assert e["provenance"]["earlier_packet_sha256"]["compact-result.json"] == (
        "e3e636497337efc0ec1b5f9302f1bb5362142b46a90d3d7307e3124ea31f18b3")
    assert all(private not in EVIDENCE.read_text() for private in ("/home/", "/Users/", "C:\\"))
    assert "not exhaustive impossibility" in " ".join(e["limits"])
