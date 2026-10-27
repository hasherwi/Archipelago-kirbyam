"""Source/QA-proven 192 -> 801 -> 592; no reverse-route inference."""
import pytest

from .test_rules import _make_collection_state_room_graph
from ..data import load_json_data

SOURCE = 'REGION_RAINBOW_ROUTE/ROOM_1_HUB_3'
MIDDLE = 'REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE_MIDDLE_PLATFORMS'
LOWER = 'REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE'
TARGET = 'REGION_CABBAGE_CAVERN/ROOM_3_HUB_3'
WEST_RAINBOW = 'Rainbow Route West - Hub Connection'
WEST_CABBAGE = 'Cabbage Cavern West - Hub Connection'


def test_route_uses_native_arrival_compartment_and_existing_descent():
    rooms = load_json_data('regions/rooms.json')
    assert TARGET not in rooms[SOURCE]['exits']
    assert LOWER not in rooms[SOURCE]['exits']
    assert MIDDLE in rooms[SOURCE]['exits']
    assert rooms[MIDDLE]['exits'][LOWER] is None
    assert rooms[SOURCE]['room_sanity']['bit_index'] == 59
    assert rooms[LOWER]['locations']['room_sanity']['bit_index'] == 0
    assert rooms[TARGET]['room_sanity']['bit_index'] == 219
    # The reverse claim remains untouched and unproven, not synthesized here.
    assert rooms[TARGET]['exit_requirements'][SOURCE] == {'item': 'Cabbage Cavern Center - Hub Connection'}


@pytest.mark.parametrize('order', [(WEST_RAINBOW, WEST_CABBAGE), (WEST_CABBAGE, WEST_RAINBOW)])
def test_actual_route_rules_require_both_native_hub_items(order):
    world, state = _make_collection_state_room_graph()
    first = world.get_entrance(f'{SOURCE} -> {MIDDLE}', 1)
    descent = world.get_entrance(f'{MIDDLE} -> {LOWER}', 1)
    second = world.get_entrance(f'{LOWER} -> {TARGET}', 1)
    assert descent.access_rule(state)
    assert not first.access_rule(state)
    assert not second.access_rule(state)
    state.add_item('Rainbow Route South - Hub Connection', 1)
    assert not first.access_rule(state)
    assert not second.access_rule(state)
    state.add_item(order[0], 1)
    assert first.access_rule(state) == (order[0] == WEST_RAINBOW)
    assert second.access_rule(state) == (order[0] == WEST_CABBAGE)
    state.add_item(order[1], 1)
    assert first.access_rule(state) and descent.access_rule(state) and second.access_rule(state)
    for item, gate in [(WEST_RAINBOW, first), (WEST_CABBAGE, second)]:
        state.remove_item(item, 1)
        assert not gate.access_rule(state)
        state.add_item(item, 1)
