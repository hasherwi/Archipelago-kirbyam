"""The Carrot chute arrival cannot cross its closed wall (#1093/#1094)."""
import pytest
from BaseClasses import CollectionState, MultiWorld, Region
from .. import KirbyAmWorld
from ..data import data
from ..rules import evaluate_room_logic_requirement

MAIN = 'REGION_CARROT_CASTLE/ROOM_5_05'
CHUTE = MAIN + '__LOGIC__CHUTE_SIDE'
ARRIVAL = 'REGION_CARROT_CASTLE/ROOM_5_06'
HUB = 'REGION_CARROT_CASTLE/ROOM_5_HUB'

@pytest.mark.parametrize('entry', [ARRIVAL, HUB])
def test_carrot_wall_separates_both_arrival_directions(entry):
    mw = MultiWorld(1)
    world = mw.worlds[1] = KirbyAmWorld(mw, 1)
    names = ['Menu', MAIN, CHUTE, ARRIVAL, HUB, MAIN + '__ROOM_CHECK']
    regions = {name: Region(name, 1, mw) for name in names}
    mw.regions.extend(regions.values())
    for name in names[1:]:
        definition = data.regions[name]
        for destination in definition.exits:
            if destination in regions:
                req = definition.exit_requirements.get(destination)
                regions[name].connect(regions[destination], rule=lambda state, req=req:
                    evaluate_room_logic_requirement(req, state, 1))
    regions['Menu'].connect(regions[entry])
    state = CollectionState(mw)
    assert regions[MAIN + '__ROOM_CHECK'].can_reach(state)
    assert not regions[MAIN + '__ROOM_CHECK'].exits
    assert regions[CHUTE].can_reach(state) is (entry == ARRIVAL)
    assert regions[MAIN].can_reach(state) is (entry == HUB)
    state.collect(world.create_item('Carrot Castle 5-05 - Lever Wall'), prevent_sweep=True)
    assert all(regions[name].can_reach(state) for name in names)


def test_carrot_lever_credit_stays_outside_chute_pocket():
    assert not data.regions[CHUTE].events
    assert not data.regions[CHUTE].locations
    assert any(event.name == 'Activate Lever - Carrot Castle 5-05'
               for event in data.regions[MAIN].events)
    assert CHUTE in data.regions[ARRIVAL].exits
    assert MAIN not in data.regions[ARRIVAL].exits


def test_all_four_chain_fixture_is_scoped_and_moonlight_does_not_open_other_chains():
    import json
    from pathlib import Path
    fixture = json.loads((Path(__file__).parent / 'data/all-lever-chains-native.json').read_text())
    assert 'not gameplay' in fixture['scope']
    rows = {row['native_room']: row for row in fixture['rooms']}
    assert set(rows) == {170, 619, 743, 824}
    assert all((row['counter_selector'], row['counter_value']) == (1, 1) for row in rows.values())
    assert rows[743]['controlled_chain'] == [[x, y] for x in (8, 9) for y in (5, 6, 7)]
    assert len(rows[743]['other_f2_cells']) == 20
    assert all(not rows[room]['other_f2_cells'] for room in (170, 619, 824))
