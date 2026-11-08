"""Native742 evidence integrity only; no production route is accepted here."""

import json
from pathlib import Path


def test_native_acceptance_keeps_mutations_and_outcomes_separate() -> None:
    root = Path(__file__).parents[1] / "dev-docs"
    record = json.loads((root / "ordinary-742-clean-source-acceptance.json").read_text())
    assert record["fixture"]["actual712_door_record_rom_offset"] == "0x884640"
    assert record["source"]["template_bus_address"] == "0x088BD8AC"
    assert record["source"]["table_ability"] == 3
    assert record["entry742"]["native741_door_record_rom_offset"] == "0x884BE2"
    assert record["entry742"]["first_visit"] and record["entry742"]["live_arrival"] == [472, 456.99609375]
    assert record["mechanisms"]["timed_door"]["button_unk18"] == 120
    chest, warp = record["results"]["chest"], record["results"]["warp"]
    assert (chest["native_flag"], chest["before"], chest["after"], chest["final_ability"]) == (17, 0, 2, 0)
    assert chest["template_bus_address"] == "0x088BDD10"
    assert warp["destination"] == 705 and warp["door_record_rom_offset"] == "0x885348"
    assert (warp["final_hp"], warp["final_ability"]) == (2, 3)
    for key in ("metal742", "chestopen742", "warpclimb742"):
        tiles = {(tile["x"], tile["y"]): tile["tile"] for tile in record["observations"][key]["tiles"]}
        assert [tiles[point] for point in [(20, 6), (21, 6), (20, 7), (21, 7)]] == [0, 0, 245, 245]
        assert tiles[19, 12] == tiles[26, 12] == 241
        assert tiles[24, 8] == tiles[25, 8] == 243
    chains = record["chains"]
    assert chains["clean_chest_branch"][0]["parent_controller_state"] == "metal742"
    assert chains["clean_warp_branch"][0]["parent_controller_state"] == "metal742"
    assert all(not segment["writes"] for chain in chains.values() for segment in chain)
    assert chains["clean_warp_branch"][-1]["checkpoints"][-1]["room"] == 705


def test_no_loss_replacement_has_continuous_audit_and_linked_branches() -> None:
    root = Path(__file__).parents[1] / "dev-docs"
    record = json.loads((root / "ordinary-742-no-loss-source-acceptance.json").read_text())
    chains = record["chains"]
    segments = [segment for chain in chains.values() for segment in chain]
    by_name = {segment["segment"]: segment for segment in segments}
    assert len(by_name) == len(segments) == 27
    for segment in segments:
        assert not segment["writes"]
        parent = segment["parent_controller_state"]
        assert parent is None or parent in by_name
        assert all(point["hp"] == 6 for point in segment["checkpoints"])
    audit = {row["segment"]: row for row in record["per_frame_hp_audit"]}
    assert set(audit) == set(by_name) - {"entry741"}
    assert sum(row["frames"] for row in audit.values()) == 5205
    assert all(row["minimum_hp"] == 6 and not row["hp_decreases"] for row in audit.values())
    assert record["source"]["hp"] == record["entry742"]["hp"] == 6
    for target in ("chest", "warp"):
        assert record["results"][target]["final_hp"] == 6
        assert record["results"][target]["final_ability"] == 3
    assert record["results"]["chest"]["after"] == 2
    assert record["results"]["warp"]["destination"] == 705
    assert chains["clean_chest_branch"][0]["parent_controller_state"] == "safe_metal742"
    assert chains["clean_warp_branch"][0]["parent_controller_state"] == "safe_metal742"


def test_native742_doors_preserve_distinct_arrival_sides() -> None:
    root = Path(__file__).parents[1] / "dev-docs"
    record = json.loads((root / "ordinary-742-door-topology.json").read_text())
    incoming = {row["offset"]: row["spawn_tile"] for row in record["native741_doors"]}
    assert incoming == {"0x884a48": [19, 8], "0x884be2": [30, 29]}
    outgoing = {row["offset"]: (row["trigger"], row["destination"], row["spawn_tile"])
                for row in record["native742_doors"]}
    assert outgoing == {"0x885348": ([27, 2], 705, [4, 39]), "0x88554e": ([25, 12], 741, [11, 8])}


def test_all500_uses_the_production_scaler_and_no_loss_actual_outcomes() -> None:
    import hashlib

    root = Path(__file__).parents[1]
    record = json.loads((root / "dev-docs/ordinary-742-all500-acceptance.json").read_text())
    source = (root / "enemy_health_scaling.py").read_bytes()
    git_blob = hashlib.sha1(b"blob " + str(len(source)).encode() + b"\0" + source).hexdigest()
    assert git_blob == record["fixture"]["module_git_blob"]
    chains = record["chains"]
    segments = [segment for chain in chains.values() for segment in chain]
    by_name = {segment["segment"]: segment for segment in segments}
    assert len(by_name) == len(segments) == 31
    for segment in segments:
        assert not segment["writes"]
        parent = segment["parent_controller_state"]
        assert parent is None or parent in by_name
        assert all(point["hp"] == 6 for point in segment["checkpoints"])
    audit = {row["segment"]: row for row in record["per_frame_hp_audit"]}
    assert set(audit) == set(by_name) - {"all500-doo20-entry741"}
    assert sum(row["frames"] for row in audit.values()) == 5463
    assert all(row["minimum_hp"] == 6 and not row["decrease_frames"] for row in audit.values())
    assert chains["chest"][-1]["checkpoints"][-1]["ability"] == 0
    assert chains["warp"][-1]["checkpoints"][-1]["room"] == 705
    assert chains["warp"][-1]["checkpoints"][-1]["ability"] == 3
    assert record["observations"]["all500-chestfinal"]["chest_flag_byte"] == 2
    for observation in record["observations"].values():
        tiles = {(tile["x"], tile["y"]): tile["tile"] for tile in observation["tiles"]}
        assert [tiles[point] for point in [(20, 6), (21, 6), (20, 7), (21, 7)]] == [0, 0, 245, 245]
        assert tiles[19, 12] == tiles[26, 12] == 241
        assert tiles[24, 8] == tiles[25, 8] == 243


def test_joint_completion_uses_same_scaled_visit_without_a_second_copy() -> None:
    root = Path(__file__).parents[1] / "dev-docs"
    parent = json.loads((root / "ordinary-742-all500-acceptance.json").read_text())
    record = json.loads((root / "ordinary-742-all500-combined-checks.json").read_text())
    assert record["fixture"] == parent["fixture"]
    chain = record["chains"]["same_visit_chest_to_warp"]
    assert len(chain) == 8
    previous = parent["chains"]["chest"][-1]["segment"]
    assert previous == "all500-chestfinal"
    for segment in chain:
        assert segment["parent_controller_state"] == previous
        assert not segment["writes"]
        assert all(point["ability"] == 0 and point["hp"] == 6 for point in segment["checkpoints"])
        previous = segment["segment"]
    audit = {row["segment"]: row for row in record["per_frame_hp_audit"]}
    assert set(audit) == {segment["segment"] for segment in chain}
    assert sum(row["frames"] for row in audit.values()) == 1058
    assert all(row["minimum_hp"] == 6 and not row["decrease_frames"] for row in audit.values())
    assert chain[-1]["checkpoints"][-1]["room"] == 705
    assert all(observation["chest_flag_byte"] == 2 for observation in record["observations"].values())
    for name in ("all500-chestfinal", "all500-combinedwarp"):
        tiles = {(tile["x"], tile["y"]): tile["tile"] for tile in record["observations"][name]["tiles"]}
        assert tiles[19, 12] == tiles[26, 12] == 241
        assert tiles[24, 8] == tiles[25, 8] == 243
        assert [tiles[point] for point in [(20, 6), (21, 6), (20, 7), (21, 7)]] == [0, 0, 245, 245]
