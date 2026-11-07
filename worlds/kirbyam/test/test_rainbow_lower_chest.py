"""The native room 108 chest is below the one-way upper route (#1032)."""
import pytest
from BaseClasses import CollectionState
from test.general import setup_multiworld
from .. import KirbyAmWorld
from ..data import data, load_json_data
from ..wheel_traversal import RACE_ENTRANCE

KEY = 'MINOR_CHEST_RAINBOW_ROUTE_1_06_UPPER'  # Preserve the existing slot-data key.
PREFIX = 'REGION_RAINBOW_ROUTE/ROOM_1_06_'


def test_native_chest_identity_and_compartment():
    chest = data.locations[KEY]
    assert chest.location_id == 3960567
    assert chest.parent_region == PREFIX + 'LOWER_CHEST'
    assert chest.label == 'Rainbow Route 1-06 (Lower) - Small Chest'
    locations = load_json_data('locations.json')
    assert locations[KEY]['source_rom_offset'] == '0x008B7288'
    recovery = load_json_data('chest_recovery.json')
    native = next(row for row in recovery['records'] if row['location_key'] == KEY)
    assert (native['source'], native['flag'], native['position'], native['rooms']) == (
        '0x008B7288', 4, [40, 216], [108])
    rooms = load_json_data('regions/rooms.json')
    assert KEY not in rooms[PREFIX + 'UPPER']['locations']
    assert rooms[PREFIX + 'LOWER_CHEST']['locations'][KEY] is None
    assert rooms[PREFIX + 'LOWER_MID']['exits'][PREFIX + 'LOWER_CHEST'] == 'can_wheel'
    assert PREFIX + 'LOWER_MID' not in rooms[PREFIX + 'UPPER']['exits']


@pytest.mark.parametrize('room_sanity', [0, 1])
@pytest.mark.parametrize('ability_gating', [0, 1])
@pytest.mark.parametrize('ability_randomization_mode', [0, 1, 2])
def test_upper_entry_hub_receipts_and_alternate_routes(room_sanity, ability_gating, ability_randomization_mode):
    mw = setup_multiworld(KirbyAmWorld, seed=1032, options={
        'room_sanity': room_sanity, 'ability_gating': ability_gating,
        'ability_randomization_mode': ability_randomization_mode})
    world = mw.worlds[1]
    chest = mw.get_location(data.locations[KEY].label, 1)

    def state_with(names):
        state = CollectionState(mw)
        for name in names:
            state.collect(world.create_item(name), True)
        state.sweep_for_advancements(locations=[loc for loc in mw.get_locations(1) if not loc.address])
        return state

    def assert_lower_path(state):
        # This regression checks entry topology. The new source-aware speed rule
        # separately requires obtainable Wheel, rather than a hub receipt alone.
        assert mw.get_region(PREFIX + 'LOWER_MID', 1).can_reach(state)
        speed_rule = mw.get_entrance(RACE_ENTRANCE, 1).access_rule
        assert chest.can_reach(state) == speed_rule(state)

    empty = state_with([])
    assert mw.get_region(PREFIX + 'UPPER', 1).can_reach(empty)
    assert not chest.can_reach(empty)
    assert not chest.can_reach(state_with(['Moonlight Mansion - Hub Connection']))
    for direction in ('East', 'West', 'North'):
        state = state_with([f'Rainbow Route {direction} - Hub Connection'])
        assert_lower_path(state)
    # Do not encode the report as a mandatory Rainbow-hub item requirement:
    # other unlocked overland routes may legitimately enter the lower cave.
    alternate = state_with([item.name for item in mw.itempool
                            if not (item.name.startswith('Rainbow Route ')
                                    and item.name.endswith('Hub Connection'))])
    assert_lower_path(alternate)
    assert_lower_path(state_with([
        'Carrot Castle - Area Key', 'Carrot Castle - Hub Connection',
        'Peppermint Palace - Area Key', 'Peppermint Palace East - Hub Connection',
    ]))
