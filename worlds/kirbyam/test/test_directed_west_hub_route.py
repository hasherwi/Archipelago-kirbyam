"""Source/QA-proven 192 -> 801 -> 592; no reverse-route inference."""
from typing import Any, cast

import pytest

from .test_rules import _make_collection_state_room_graph
from ..data import load_json_data

SOURCE = 'REGION_RAINBOW_ROUTE/ROOM_1_HUB_3'
MIDDLE = 'REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE_MIDDLE_PLATFORMS'
LOWER = 'REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE'
TARGET = 'REGION_CABBAGE_CAVERN/ROOM_3_HUB_3'
WEST_RAINBOW = 'Rainbow Route West - Hub Connection'
WEST_CABBAGE = 'Cabbage Cavern West - Hub Connection'


def test_route_preserves_native_chain_in_current_room_graph() -> None:
    rooms = cast(dict[str, Any], load_json_data('regions/rooms.json'))
    assert TARGET not in rooms[SOURCE]['exits']
    assert LOWER in rooms[SOURCE]['exits']
    # Main #914 consolidated the middle platform into Central Circle.
    assert MIDDLE not in rooms
    assert rooms[SOURCE]['locations']['room_sanity']['bit_index'] == 59
    assert rooms[LOWER]['locations']['room_sanity']['bit_index'] == 0
    assert rooms[TARGET]['locations']['room_sanity']['bit_index'] == 219


@pytest.mark.parametrize('order', [(WEST_RAINBOW, WEST_CABBAGE), (WEST_CABBAGE, WEST_RAINBOW)])
def test_actual_route_rules_require_both_native_hub_items(order: tuple[str, str]) -> None:
    world, state = _make_collection_state_room_graph()
    first = world.get_entrance(f'{SOURCE} -> {LOWER}', 1)
    second = world.get_entrance(f'{LOWER} -> {TARGET}', 1)
    assert not first.access_rule(state)
    assert not second.access_rule(state)
    state.add_item('Rainbow Route South - Hub Connection', 1)
    assert not first.access_rule(state)
    assert not second.access_rule(state)
    state.add_item(order[0], 1)
    assert first.access_rule(state) == (order[0] == WEST_RAINBOW)
    assert second.access_rule(state) == (order[0] == WEST_CABBAGE)
    state.add_item(order[1], 1)
    assert first.access_rule(state) and second.access_rule(state)
    for item, gate in [(WEST_RAINBOW, first), (WEST_CABBAGE, second)]:
        state.remove_item(item, 1)
        assert not gate.access_rule(state)
        state.add_item(item, 1)
