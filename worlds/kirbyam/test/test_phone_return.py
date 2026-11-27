"""Keep native L movement independent of the Phone helper and carry graphs."""

from copy import deepcopy
import json
from pathlib import Path

import pytest
from BaseClasses import CollectionState
from test.general import setup_multiworld

from .. import KirbyAmWorld
from ..data import data, load_json_data
from ..phone_return import compile_phone_return, phone_return


EVIDENCE = Path(__file__).resolve().parents[1] / "dev-docs"
DRY = "REGION_RAINBOW_ROUTE/ROOM_1_HUB_1"
WET = "REGION_RAINBOW_ROUTE/ROOM_1_06_LOWER_MID"
HUB = "REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE"
MOON_HUB = "REGION_MOONLIGHT_MANSION/ROOM_2_HUB"


def test_runtime_table_matches_native_flags_and_physical_compartments():
    native = json.loads((EVIDENCE / "phone-return-native-rooms.json").read_text(encoding="utf-8"))
    catalog = json.loads((EVIDENCE / "native-room-wikirby-map.json").read_text(encoding="utf-8"))
    assert native["rom_sha1"] == catalog["rom_sha1"]
    active_encounter_rooms = set(map(int, native["encounter_session_slots_by_native_room"]))
    allowed_rooms = set(native["eligible_native_rooms"])
    assert len(allowed_rooms) == 262
    expected = {str(row["native_id"]): row["ap_keys"] for row in catalog["rooms"]
                if row["native_id"] in allowed_rooms - active_encounter_rooms and row["ap_keys"]}
    raw = load_json_data("phone_return.json")
    assert isinstance(raw, dict)
    assert raw["stable_normal_sources_by_native_room"] == expected
    assert raw["room_flag_disallows_return"] == native["room_flag_disallows_return"]
    assert set(raw["encounter_rooms_not_modeled"]) == allowed_rooms & active_encounter_rooms
    assert raw["destination_native_room"] == native["destination_native_room"] == 801
    assert HUB in next(row["ap_keys"] for row in catalog["rooms"] if row["native_id"] == 801)
    assert not native["phone_item_required"] and not native["battery_charge_required"]
    assert len(expected) == 254 and len(phone_return().sources) == 340


@pytest.mark.parametrize("defect", ["sink", "encounter", "duplicate", "wrong_landing", "invented_charge"])
def test_invalid_phone_return_data_fails_closed(defect):
    raw = deepcopy(load_json_data("phone_return.json"))
    rooms = raw["stable_normal_sources_by_native_room"]
    if defect == "sink":
        rooms["190"].append("REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE__ROOM_CHECK")
    elif defect == "encounter":
        rooms["129"] = ["REGION_RADISH_RUINS/ROOM_8_BOSS"]
    elif defect == "duplicate":
        rooms["190"].append(rooms["190"][0])
    elif defect == "wrong_landing":
        raw["destination_region"] += "_UPPER_PLATFORMS"
    else:
        raw["battery_charge_required"] = True
    with pytest.raises(ValueError, match="Phone return"):
        compile_phone_return(raw)


def make_world():
    return setup_multiworld(KirbyAmWorld, steps=("generate_early", "create_regions", "set_rules"), seed=1197,
                            options={"area_keys": True, "random_starting_mirror": True, "room_sanity": True})


def test_runtime_installs_only_conservative_one_way_sources():
    mw = make_world()
    sources = {edge.parent_region.name for edge in mw.get_entrances(1) if edge.name.endswith("(Phone L)")}
    assert sources == set(phone_return().sources)
    for source in sources:
        edge = mw.get_entrance(f"{source} -> Central Circle (Phone L)", 1)
        assert edge.connected_region is mw.get_region(HUB, 1)
        assert not any(edge.name.endswith("(Phone L)") for edge in edge.connected_region.exits)
    assert sources.isdisjoint({"Menu", "REGION_GAME_START", "REGION_COPY_ABILITY_ROOM/MAIN",
                               "REGION_MOONLIGHT_MANSION/ROOM_2_BOSS", HUB,
                               HUB + "_UPPER_PLATFORMS"})
    assert all(not name.endswith(("__ROOM_CHECK", "/MAIN")) for name in sources)


@pytest.mark.parametrize("source", [DRY, WET])
def test_isolated_arrival_can_return_with_no_items_but_cannot_open_locked_mirrors(source):
    mw = make_world()
    world = mw.worlds[1]
    menu = mw.get_region("Menu", 1)
    start = mw.get_entrance("Start Game", 1)
    start.access_rule = lambda _: False
    origin = mw.get_region(source, 1)
    menu.connect(origin, "Test isolated arrival")
    origin.exits = [edge for edge in origin.exits if edge.name.endswith("(Phone L)")]
    state = CollectionState(mw)
    assert origin.can_reach(state)
    assert mw.get_region(HUB, 1).can_reach(state)
    for dest in (MOON_HUB, "REGION_RAINBOW_ROUTE/ROOM_1_01", "REGION_COPY_ABILITY_ROOM/MAIN"):
        gate = mw.get_entrance(f"{HUB} -> {dest}", 1)
        assert not gate.access_rule(state)
    name = data.regions[HUB].exit_requirements[MOON_HUB]["item"]
    state.collect(world.create_item(name), prevent_sweep=True)
    state.collect(world.create_item("Moonlight Mansion - Area Key"), prevent_sweep=True)
    assert mw.get_entrance(f"{HUB} -> {MOON_HUB}", 1).can_reach(state)
    origin.exits[0].access_rule = lambda _: False
    assert not mw.get_region(HUB, 1).can_reach(CollectionState(mw))


@pytest.mark.parametrize("source", ["REGION_COPY_ABILITY_ROOM/MAIN", "REGION_MOONLIGHT_MANSION/ROOM_2_BOSS"])
def test_isolated_ineligible_room_cannot_use_phone_return(source):
    mw = make_world()
    mw.get_entrance("Start Game", 1).access_rule = lambda _: False
    room = mw.get_region(source, 1)
    room.exits = [edge for edge in room.exits if edge.name.endswith("(Phone L)")]
    mw.get_region("Menu", 1).connect(room, "Test isolated ineligible arrival")
    state = CollectionState(mw)
    assert room.can_reach(state)
    assert not mw.get_region(HUB, 1).can_reach(state)


@pytest.mark.parametrize(("seed", "keys", "random_start"), [(1197, 0, 0), (773, 1, 1)])
def test_accessible_seed_fill_unchanged_when_the_hub_is_already_reachable(
        monkeypatch, tmp_path, seed, keys, random_start):
    from .. import regions
    from ..phone_return import PhoneReturn
    from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive

    fixture = tmp_path / "player.yaml"
    fixture.write_text("name: PhoneReturn\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n"
                       f"  area_keys: {keys}\n  random_starting_mirror: {random_start}\n"
                       "  room_sanity: 1\n", encoding="utf-8")
    after = load_multidata_from_archive(generate_archive_from_fixture(fixture, tmp_path / "after", seed))
    with monkeypatch.context() as context:
        context.setattr(regions, "phone_return", lambda: PhoneReturn(HUB, ()))
        before = load_multidata_from_archive(generate_archive_from_fixture(fixture, tmp_path / "before", seed))
    for key in ("locations", "precollected_items", "slot_data", "checks_in_area"):
        assert after[key] == before[key]
