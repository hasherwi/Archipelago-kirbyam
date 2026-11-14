"""Carrot arrival cannot borrow the Radish side of native room 619 (#1093)."""
import pytest
from BaseClasses import CollectionState, MultiWorld, Region
from .. import KirbyAmWorld
from ..data import data
from ..rules import evaluate_room_logic_requirement

MAIN = 'REGION_RADISH_RUINS/ROOM_8_12'
LEFT = MAIN + '__LOGIC__CARROT_SIDE'
CARROT = 'REGION_CARROT_CASTLE/ROOM_5_06'
RADISH = 'REGION_RADISH_RUINS/ROOM_8_11'

@pytest.mark.parametrize('entry', [CARROT, RADISH])
def test_wall_separates_arrival_sides_until_received(entry):
    mw = MultiWorld(1)
    world = mw.worlds[1] = KirbyAmWorld(mw, 1)
    names = ['Menu', MAIN, LEFT, CARROT, RADISH, MAIN + '__ROOM_CHECK']
    regions = {name: Region(name, 1, mw) for name in names}
    mw.regions.extend(regions.values())
    for name in names[1:]:
        definition = data.regions[name]
        for destination in definition.exits:
            if destination in regions:
                req = definition.exit_requirements.get(destination)
                regions[name].connect(regions[destination], rule=lambda s, req=req:
                                      evaluate_room_logic_requirement(req, s, 1))
    regions['Menu'].connect(regions[entry])
    state = CollectionState(mw)
    assert regions[MAIN + '__ROOM_CHECK'].can_reach(state)
    assert not regions[MAIN + '__ROOM_CHECK'].exits
    if entry == CARROT:
        assert regions[LEFT].can_reach(state)
        assert not regions[MAIN].can_reach(state)
        assert not regions[RADISH].can_reach(state)
    else:
        assert regions[MAIN].can_reach(state)
        assert not regions[LEFT].can_reach(state)
        assert not regions[CARROT].can_reach(state)
    state.collect(world.create_item('Radish Ruins 8-12 - Lever Wall'), prevent_sweep=True)
    assert all(regions[name].can_reach(state) for name in names)


def test_lever_and_activation_remain_on_radish_side():
    assert 'LEVER_RADISH_RUINS_8_12' in data.regions[MAIN].locations
    assert 'LEVER_RADISH_RUINS_8_12' not in data.regions[LEFT].locations
    assert any(event.name == 'Activate Lever - Radish Ruins 8-12' for event in data.regions[MAIN].events)
    assert not data.regions[LEFT].events
    assert LEFT in data.regions[CARROT].exits
    assert MAIN not in data.regions[CARROT].exits
    assert MAIN in data.regions[RADISH].exits
