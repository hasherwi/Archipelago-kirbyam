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
def test_hub_receipt_shortcuts_and_eight_distinct_shards(room_sanity):
    world = setup_multiworld(KirbyAmWorld, seed=932, options={
        'room_sanity': room_sanity, 'ability_gating': 0})
    trial = CollectionState(world)
    # Receipt milestones describe shortcuts, not global room-access phases.
    # Physical Moonlight is ID 402; ID 401 is the Rainbow East central shortcut.
    for item_id, label, destination in (
        (3860401, 'Rainbow Route East - Hub Connection',
         'REGION_RAINBOW_ROUTE/ROOM_1_HUB_1'),
        (3860402, 'Moonlight Mansion - Hub Connection',
         'REGION_MOONLIGHT_MANSION/ROOM_2_HUB'),
    ):
        assert data.items[item_id].label == label
        entrance = world.get_entrance(f'{CENTRAL} -> {destination}', 1)
        assert not entrance.access_rule(trial)
        received = trial.copy()
        received.collect(world.worlds[1].create_item(label), True)
        assert entrance.access_rule(received)
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
    for name in ('Moonlight Mansion - Hub Connection',
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


@pytest.mark.parametrize('room_sanity', [0, 1])
@pytest.mark.parametrize('ability_gating', [0, 1])
def test_candy_overland_arrival_does_not_grant_its_central_connection(room_sanity, ability_gating):
    """Preserve the emulator-proven 705->409->427->404->407->401->407->490 route."""
    world = setup_multiworld(KirbyAmWorld, seed=932, options={
        'room_sanity': room_sanity, 'ability_gating': ability_gating})
    state = CollectionState(world)
    state.collect(world.worlds[1].create_item('Moonlight Mansion 2-11 - Lever Wall'), True)
    # This regression concerns topology, not acquisition of each copy ability.
    # The runtime route used normally acquired Missile and Burning with gating off.
    for item in world.itempool:
        if item.name.endswith(' Ability'):
            state.collect(item, True)
    state.sweep_for_advancements()
    hub = 'REGION_CANDY_CONSTELLATION/ROOM_9_HUB'
    assert world.get_region(hub, 1).can_reach(state)
    connection = world.get_entrance(f'{hub} -> {CENTRAL}', 1)
    assert not connection.access_rule(state)
    state.collect(world.worlds[1].create_item('Candy Constellation - Hub Connection'), True)
    assert connection.access_rule(state)
