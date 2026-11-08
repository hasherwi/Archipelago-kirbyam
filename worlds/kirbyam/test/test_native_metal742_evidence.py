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
