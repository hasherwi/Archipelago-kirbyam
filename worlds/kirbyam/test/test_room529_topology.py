"""Native529 fresh arrivals preserve the directed upper-left Bomb boundary."""

from itertools import product
import json
from pathlib import Path

import pytest
from BaseClasses import CollectionState

from ..data import LocationCategory, data, load_json_data
from .test_mini_traversal import make_world


PREFIX = "REGION_CABBAGE_CAVERN/"
MAIN = PREFIX + "ROOM_3_03"
UPPER_LEFT = MAIN + "__LOGIC__UPPER_LEFT"
CHECK = MAIN + "__ROOM_CHECK"
LOWER_523 = PREFIX + "ROOM_3_01"
RIGHT_512 = PREFIX + "ROOM_3_04"
LEFT_512 = PREFIX + "ROOM_3_04_SUB"
SIDES = {MAIN, UPPER_LEFT, CHECK, LOWER_523, RIGHT_512, LEFT_512}


@pytest.mark.parametrize("start", [MAIN, LOWER_523, RIGHT_512, UPPER_LEFT, LEFT_512])
@pytest.mark.parametrize("gating,room_sanity", tuple(product(range(2), repeat=2)))
def test_fresh_arrival_can_return_but_cannot_borrow_an_opened_upper_left_layout(
    start: str, gating: int, room_sanity: int,
) -> None:
    world = make_world(0, gating, room_sanity=room_sanity)  # type: ignore[no-untyped-call]
    mw = world.multiworld
    for side in SIDES:
        region = mw.get_region(side, 1)
        region.exits = [edge for edge in region.exits if edge.connected_region.name in SIDES]
    menu = mw.get_region("Menu", 1)
    menu.exits.clear()
    menu.connect(mw.get_region(start, 1))
    state = CollectionState(mw)
    for item, count in tuple(state.prog_items[1].items()):
        for _ in range(count):
            state.remove(world.create_item(item))
    assert not +state.prog_items[1]
    expected = {LEFT_512, UPPER_LEFT, CHECK} if start in {LEFT_512, UPPER_LEFT} else SIDES
    assert {side for side in SIDES if state.can_reach_region(side, 1)} == expected
    checks = [loc for loc in mw.get_locations(1) if loc.address == 3961090]
    assert len(checks) == room_sanity
    if checks:
        assert checks[0].parent_region.name == CHECK
        assert checks[0].can_reach(state)
    assert not mw.get_region(CHECK, 1).exits
    # Ownership cannot turn a conservative fresh-upper-left compartment into
    # an accepted attack direction or restore the former generic arrival.
    for item in ("Burning Ability", "Stone Ability", "Hammer Ability", "Missile Ability"):
        state.collect(world.create_item(item), prevent_sweep=True)
    assert {side for side in SIDES if state.can_reach_region(side, 1)} == expected


def test_only_native512_sub_arrival_is_redirected_and_check_identity_is_unchanged() -> None:
    rooms = load_json_data("regions/rooms.json")
    assert isinstance(rooms, dict)
    assert rooms[LEFT_512]["logical_exit_overrides"] == {MAIN: "UPPER_LEFT"}
    assert MAIN not in data.regions[LEFT_512].exits
    assert UPPER_LEFT in data.regions[LEFT_512].exits
    assert MAIN in data.regions[RIGHT_512].exits
    assert MAIN in data.regions[LOWER_523].exits
    assert set(data.regions[MAIN].exits) == {LOWER_523, RIGHT_512, UPPER_LEFT, CHECK}
    assert set(data.regions[UPPER_LEFT].exits) == {LEFT_512, CHECK}
    assert rooms[MAIN]["exits"] == {
        LOWER_523: "can_swim", RIGHT_512: "can_swim", UPPER_LEFT: "can_swim"}
    assert rooms[MAIN]["locations"]["room_sanity"] == {
        "included": True, "location_id": 3961090, "bit_index": 185}
    checks = [loc for loc in data.locations.values() if loc.location_id == 3961090]
    assert len(checks) == 1 and checks[0].category == LocationCategory.ROOM_SANITY
    assert checks[0].bit_index == 185
    assert not data.regions[MAIN].locations and not data.regions[UPPER_LEFT].locations
    assert data.regions[CHECK].locations == [checks[0].name]
    assert not data.regions[CHECK].exits


def test_cluster_coverage_is_directional_not_a_universal_normal_or_metal_claim() -> None:
    path = Path(__file__).parents[1] / "dev-docs/ordinary-metal-coverage.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    room = next(row for row in record["rooms"] if row["native_room"] == 529)
    assert {row["region"] for row in room["ap_compartments"]} == {MAIN, UPPER_LEFT, CHECK}
    for row in room["ap_compartments"]:
        assert set(row["exits"]) == set(data.regions[row["region"]].exits)
    assert {row["id"] for row in room["clusters"]} == {"529:8,5", "529:12,18"}
    for cluster in room["clusters"]:
        assert cluster["status"] == "existing_normal_bypass" and cluster["classification"] == "bypass"
        assert cluster["accepted_directions"] == [
            "lower_to_upper_right", "upper_right_to_lower", "lower_to_upper_left", "upper_left_return_to_512_sub"]
        assert cluster["excluded_directions"] == ["fresh_upper_left_to_lower", "fresh_upper_left_to_upper_right"]
        assert "accepted_target" not in cluster and "requires_guaranteed_source" not in cluster
