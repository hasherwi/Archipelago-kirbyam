"""Native Hub endpoints gate traversal independently of physical switch checks."""
import json
from pathlib import Path

import pytest

from BaseClasses import CollectionState
from test.general import setup_multiworld
from .. import KirbyAmWorld
from ..data import data
from .test_rules import _make_collection_state_room_graph

EVIDENCE = json.loads((Path(__file__).parent / 'data/hub_native_edges.json').read_text())
CENTRAL = 'REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE'


@pytest.mark.parametrize('edge', EVIDENCE)
def test_each_native_edge_requires_its_own_item(edge):
    world, state = _make_collection_state_room_graph()
    source, destination = edge['source_keys'][0], edge['destination_keys'][0]
    if edge['room'] == 801 and edge['destination'] in (590, 490):
        source += '_UPPER_PLATFORMS'
    if edge['room'] == 590 and edge['destination'] == 801:
        destination += '_UPPER_PLATFORMS'
    entrance = world.get_entrance(f'{source} -> {destination}', 1)
    assert not entrance.access_rule(state)
    label = data.items[edge['item']].label
    state.add_item(label, 1)
    assert entrance.access_rule(state)
    state.remove_item(label, 1)
    assert not entrance.access_rule(state)


@pytest.mark.parametrize('room_sanity', [0, 1])
def test_central_receipt_layer_and_eight_distinct_shards(room_sanity):
    world = setup_multiworld(KirbyAmWorld, seed=932, options={
        'room_sanity': room_sanity, 'ability_gating': 0})
    state = CollectionState(world)
    def reachable(s):
        s.sweep_for_advancements()
        return {l.name for l in world.get_locations() if l.address is not None and l.can_reach(s)}
    initial = reachable(state)
    # Native slot 1 is the physical Moonlight mirror. Its legacy item label is
    # Rainbow Route East; this test follows the audited endpoint, not the label.
    for item_id in (3860402, 3860404, 3860406, 3860408, 3860410, 3860412, 3860414):
        trial = state.copy()
        trial.collect(world.worlds[1].create_item(data.items[item_id].label), True)
        assert reachable(trial) == initial
    trial = state.copy()
    trial.collect(world.worlds[1].create_item('Rainbow Route South - Hub Connection'), True)
    assert len(reachable(trial)) > len(initial)
    dimension = world.get_entrance('REGION_RAINBOW_ROUTE/MAIN -> REGION_DIMENSION_MIRROR/MAIN', 1)
    shards = [item for item in world.itempool if 'Mirror Shard' in item.name]
    assert len(shards) == 8
    for item in shards[:-1]:
        trial.collect(item, True)
    trial.collect(shards[0], True)  # duplicates cannot substitute for the eighth
    assert not dimension.access_rule(trial)
    trial.collect(shards[-1], True)
    assert dimension.access_rule(trial)


@pytest.mark.parametrize('room_sanity', [0, 1])
@pytest.mark.parametrize('ability_gating', [0, 1])
def test_moonlight_arrival_cannot_cross_olive_lever_wall(room_sanity, ability_gating):
    world = setup_multiworld(KirbyAmWorld, seed=932, options={
        'room_sanity': room_sanity, 'ability_gating': ability_gating})
    state = CollectionState(world)
    for name in ('Rainbow Route East - Hub Connection',
                 'Moonlight Mansion 2-11 - Lever Wall',
                 'Olive Ocean - Hub Connection'):
        state.collect(world.worlds[1].create_item(name), True)
    state.sweep_for_advancements()

    olive = 'REGION_OLIVE_OCEAN/ROOM_6_13'
    entry = world.get_region(olive + '__LOGIC__ENTRY_FROM_MOONLIGHT', 1)
    assert entry.can_reach(state)
    assert not world.get_region(olive, 1).can_reach(state)
    assert not world.get_region('REGION_OLIVE_OCEAN/ROOM_6_12', 1).can_reach(state)
    assert not world.get_region('REGION_OLIVE_OCEAN/ROOM_6_HUB', 1).can_reach(state)
    assert not world.get_region('REGION_CABBAGE_CAVERN/ROOM_3_HUB_1', 1).can_reach(state)
    assert not world.get_location(data.locations['LEVER_OLIVE_OCEAN_6_13'].label, 1).can_reach(state)
    # Entering the physical room does set its one RoomSanity bit. The shared
    # check must remain a sink, not an escape into the other compartment.
    check = world.get_region(olive + '__ROOM_CHECK', 1)
    assert check.can_reach(state)
    assert not data.regions[check.name].exits
    assert all(exit.connected_region.name == 'REGION_OLIVE_OCEAN/MAIN' for exit in check.exits)
    assert len(check.locations) == room_sanity
    assert world.get_region('REGION_MOONLIGHT_MANSION/ROOM_2_12_RIGHT', 1).can_reach(state)

    state.collect(world.worlds[1].create_item('Olive Ocean 6-13 - Lever Wall'), True)
    state.sweep_for_advancements()
    assert world.get_region(olive, 1).can_reach(state)
    assert world.get_region('REGION_OLIVE_OCEAN/ROOM_6_12', 1).can_reach(state)
    assert world.get_region('REGION_CABBAGE_CAVERN/ROOM_3_HUB_1', 1).can_reach(state)
