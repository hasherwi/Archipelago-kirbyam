"""Sanitized Sword719 packet contracts, not additional native emulator runs."""

import json

from ..enemy_ability_data import ABILITY_NAME_TO_ID
from ..enemy_ability_runtime_patch import build_enemy_copy_runtime_patch_writes, build_enemy_source_runtime_config
from ..traversal import CAPABILITY_ABILITIES, ROOM_SCOPED_ATTACK_WATER_STATES, ROOM_SCOPED_CAPABILITIES, SourcePolicy
from .test_sword_carrot import CAPABILITY, EVIDENCE, EXIT, OWNER, TARGET


def evidence():
    return json.loads(EVIDENCE.read_text(encoding="utf-8"))


def test_full_pool_seed4_exact_finite_source_and_target_only():
    e = evidence()
    raw = e["source_policy"]
    assert e["generation_seed"] == 4 and raw["seed"] == 14749067020901597923
    assert raw["mode"] == 1 and raw["mapping_style"] == "per_enemy_type"
    assert set(raw["allowed_abilities"]) == set(ABILITY_NAME_TO_ID) - {"Normal", "Master", "Wait"}
    assert SourcePolicy(raw).grant("WADDLE_DOO", lambda _: True).guaranteed == frozenset({"Sword"})
    assert build_enemy_copy_runtime_patch_writes(raw)[0x3517FE] == 18
    assert int.from_bytes(build_enemy_source_runtime_config(raw)[4:8], "little") & (1 << 18)
    source = e["source"]
    assert source["template"] == "0x088D3BF4" and source["native_xy"] == [568, 456]
    assert source["finite"] and source["native_room"] == 719 and source["normal_start_room"] == 170
    assert source["observation"] == {"frame": 1198, "room": 719, "type": 18, "copy": 7,
                                     "x": 568.0, "y": 453.99609375}
    assert (e["target"]["id"], e["target"]["region"], e["target"]["exit"]) == (TARGET, OWNER, EXIT)
    assert e["target"]["f1"] == [1, 14] and e["target"]["linked_f2_count"] == 15
    assert CAPABILITY_ABILITIES[CAPABILITY] == frozenset({"Sword"})
    assert ROOM_SCOPED_CAPABILITIES[CAPABILITY] == 719 and ROOM_SCOPED_ATTACK_WATER_STATES[CAPABILITY] == "dry"


def test_startup_configuration_fences_and_native_gating_limits():
    e = evidence()
    setup, shared = e["setup"], e["shared_run_facts"]
    assert setup["normal_entry_fixture_only"] and setup["blank_battery_before_first_frame"]
    no_gameplay_changes = ("ability_gating", "area_keys", "gameplay_ram_writes", "runtime_rom_writes",
                           "state_restores", "equipment_edits", "source_renewals", "phone_inputs",
                           "helper_contribution")
    assert not any(setup[k] for k in no_gameplay_changes)
    assert shared["frames"] == [1085, 3393] and shared["retained_sword_from"] == 1420
    assert shared["helpers_stay_101"] and shared["ai"] == 0 and shared["humans"] == 1
    assert shared["ingress"] == {"frame": 1188, "room": 719, "x": 680.0, "y": 456.99609375, "ability": 0}
    diffs = setup["fixture_byte_differences"]
    assert len(diffs) == 15
    assert setup["fixture_allowed_ranges"] == [["0x2D8CB8", "0x2D8CC0"], ["0x2D8CD0", "0x2D8CF0"]]
    assert all(0x2D8CB8 <= int(d["offset"], 16) < 0x2D8CC0 or 0x2D8CD0 <= int(d["offset"], 16) < 0x2D8CF0
               for d in diffs)
    writes = shared["client_config_writes"]
    assert len(writes) == 8
    assert all(w["frame"] == 1085 and w["size"] == 4 and not w["guard_failed"]
               and w["origin"] == "KirbyAmClient._sync_enemy_copy_ability_runtime_config" for w in writes)
    raw = e["source_policy"]
    expected = {0x0203B064: 1, 0x0203B068: raw["seed"] & 0xFFFFFFFF, 0x0203B06C: raw["seed"] >> 32,
                0x0203B070: 0, 0x0203B074: sum(1 << ABILITY_NAME_TO_ID[n] for n in raw["allowed_abilities"]),
                0x0203B0B0: 0, 0x0203B0B4: 0, 0x0203B078: 0}
    assert {int(w["address"], 16): int.from_bytes(bytes.fromhex(w["value"]), "little") for w in writes} == expected
    assert any("host tests, not additional native replays" in limit for limit in e["limits"])
    assert any("intermediate multipliers not independently replayed" in limit for limit in e["limits"])


def test_all_eight_endpoint_runs_and_three_tap_omission_controls():
    e = evidence()
    runs = e["runs"]
    assert len(runs) == 8
    assert {(r["hp"], r["enemy_health_percent"], r["positive"]) for r in runs} == {
        (hp, health, positive) for hp in (1, 6) for health in (100, 500) for positive in (True, False)}
    for run in runs:
        assert run["hp_min"] == run["final"]["hp"] == run["hp"]
        assert run["final"]["ability"] == 18 and run["final"]["frame"] == 3393
        assert run["final"]["room"] == (734 if run["positive"] else 719)
        if run["positive"]:
            assert run["target_frame"] == 3114 and run["all_f2_clear_frame"] == 3150 and run["arrival_frame"] == 3284
            assert run["input_changes_vs_positive"] == []
            assert [run["final"]["x"], run["final"]["y"]] == [200.0, 216.99609375]
            assert run["hashes"]["commands.json"] == e["private_artifact_sha256"]["combo-inputs.json"]
        else:
            assert run["target_frame"] is run["all_f2_clear_frame"] is run["arrival_frame"] is None
            assert run["input_changes_vs_positive"] == [3093, 3102, 3106]
            assert [run["final"]["x"], run["final"]["y"]] == [86.0, 232.99609375]
        assert set(run["hashes"]) == {"commands.json", "states.json", "changes.json", "health.json",
                                      "tile-deltas.json", "runtime.json", "blank.sav"}
        assert all(len(h) == 64 and int(h, 16) >= 0 for h in run["hashes"].values())
    assert len(e["matched_controls"]) == 4
    for control in e["matched_controls"].values():
        assert control == {"identical_every_frame_through": 3093,
                           "changed_only_three_B_frames": [3093, 3102, 3106],
                           "result": "positive734;control719,sealed"}
    assert e["identical_positive_player_trajectory_all_four_endpoints"]


def test_local_sword_first_contact_geometry_and_chain_attribution():
    combo = evidence()["native_combo"]
    assert combo["target_b_taps"] == [3093, 3102, 3106] and combo["pose"] == [86, 232.99609375]
    assert combo["repeated_slash_start"] == 3110 and combo["target_frame"] == 3114
    assert combo["player_animation"] == 111 and combo["player_header"] == 5
    assert combo["target_animations"] == [0, 52, 53, 111]
    assert combo["landing_wave_tasks_in_positive_traces"] == 0
    assert int(combo["landing_wave_task"], 16) == 0x08080130
    weapon, chain = combo["weapon"], combo["chain"]
    assert int(weapon["task_fn"], 16) == 0x080753CD and int(weapon["parent"], 16) == 0x02020EE0
    assert int(weapon["object"], 16) == int(chain["parent"], 16) == 0x03003D18
    assert int(chain["task_fn"], 16) == 0x0800E27D
    assert weapon["anim_id"] == 0x98 and weapon["variant"] == 0
    assert weapon["scan_box"] == [14, -12, 55, 1] and weapon["sprite_box"] == [-55, -12, -14, 1]
    assert int(weapon["flags"], 16) == 0xA2084101 and int(weapon["mask"], 16) == 0xB3002003
    assert combo["integer_scan_rectangle"] == [31, 220, 72, 233]
    changes = [(row["frame"], cell) for row in combo["tile_deltas"] for cell in row["changes"]]
    assert [(frame, c["x"], c["y"], c["after"]) for frame, c in changes if c["before"] == 0xF1] == [
        (3114, 1, 14, 0xFF)]
    assert sum(c["before"] == 0xF2 for _, c in changes) == 15
    assert max(frame for frame, c in changes if c["before"] == 0xF2) == combo["all_f2_clear_frame"] == 3150
    assert sum(c["before"] == 0xF0 for _, c in changes) == 8
    assert all(frame <= 2223 for frame, c in changes if c["before"] == 0xF0)
    assert combo["arrival"] == {"frame": 3284, "room": 734, "x": 200.0, "y": 216.99609375, "ability": 18}


def test_sword_specific_carry_does_not_depend_on_killing_big_waddle():
    carry = evidence()["carry_big_waddle"]
    assert [carry["100"][str(f)]["hp"] for f in (2785, 2786)] == [2, -3]
    assert carry["500"]["2785"]["hp"] == 10
    assert all(carry["500"][str(f)]["hp"] == 5 for f in (2786, 2822, 2882, 2942, 2962))
    assert all(not (int(carry["500"][str(f)]["flags"], 16) & 0x1000) for f in (2786, 2822, 2882, 2942, 2962))


def test_immutable_raw_identities_and_publication_boundary():
    e = evidence()
    assert e["source_commit"] == "2fc41e31e99ba612777c9916a0b7f6eaf867555d"
    assert e["native_commit"] == "7d969fbce14fdc838d2c1ea01389717fb96c3189"
    hashes = e["private_artifact_sha256"]
    assert hashes["acceptance.json"] == "42fca243109af3d364684ed66eb308aff7a10b51992a0753c5860c9c7aced1e3"
    assert hashes["combo-inputs.json"] == "ba02a405f3f7df6afd0c4598ebd9df5206baee84499da12d228e1d12e59d2ceb"
    assert hashes["REPORT.md"] == "7304386010f41edcc29fe40b4ec3383043d9f57173e69cbb062afa1a15bb7d8d"
    assert hashes["FINAL-SHA256SUMS"] == "2b1d95a7b704469e18cf5fe5bdc86359d923a2ba6c1df0ffa3641386748b25f8"
    assert len(e["builds"]) == 4
    for build in e["builds"].values():
        assert build["options"]["ability_gating"] == 0
        assert set(build["sha256"]) == {"production.apkirbyam", "production.gba", "fixture.gba", "base_patch.bsdiff4"}
        assert all(len(h) == 64 and int(h, 16) >= 0 for h in build["sha256"].values())
    for path in (EVIDENCE, EVIDENCE.with_name("carrot-room7-sword-witness.md")):
        assert all(private not in path.read_text(encoding="utf-8") for private in ("/home/", "/Users/", "C:\\"))
