"""Source-level reconstruction tests; optional upstream UT core integration."""
import io
import json
import logging
from collections import Counter
from unittest.mock import patch

import pytest
from BaseClasses import CollectionState
from NetUtils import NetworkItem
from test.general import setup_multiworld, gen_steps
from worlds.AutoWorld import call_all
from .. import KirbyAmWorld
from ..options import KirbyAmOptions


def reconstruct(slot):
    mw = setup_multiworld(KirbyAmWorld, steps=(), seed=999999)
    mw.re_gen_passthrough = {KirbyAmWorld.game: KirbyAmWorld.interpret_slot_data(slot)}
    mw.generation_is_fake = True
    with patch('worlds.kirbyam.build_enemy_copy_ability_policy', side_effect=AssertionError('rerolled')):
        for step in gen_steps:
            call_all(mw, step)
    return mw


def snapshot(mw, names):
    state = CollectionState(mw)
    for name in names:
        state.collect(mw.worlds[1].create_item(name), True)
    state.sweep_for_advancements(locations=[loc for loc in mw.get_locations() if loc.address is None])
    return ({loc.address for loc in mw.get_reachable_locations(state, 1) if loc.address is not None},
            mw.completion_condition[1](state))


@pytest.mark.parametrize('mode,rooms,keys,goal', [(0, 0, 1, 0), (1, 1, 1, 1), (2, 0, 0, 2), (1, 0, 0, 4),
                                                        (0, 1, 1, 5), (1, 0, 0, 5)])
def test_roundtrip_resolved_options_graph_inventory_and_progression(mode, rooms, keys, goal):
    original = setup_multiworld(KirbyAmWorld, seed=1054, options={
        'ability_randomization_mode': mode, 'room_sanity': rooms, 'area_keys': keys,
        'goal': goal, 'configured_area_boss': 'random', 'shards': 'random',
        'starting_kirby_color': 'random', 'advanced_logic': 1,
        'start_with_all_maps': 1, 'ability_gating': 1,
    })
    slot = json.loads(json.dumps(original.worlds[1].fill_slot_data()))
    assert slot["tracker"]["version"] == 2
    rebuilt = reconstruct(slot)
    a, b = original.worlds[1], rebuilt.worlds[1]
    for name in KirbyAmOptions.__annotations__:
        assert getattr(a.options, name).value == getattr(b.options, name).value
    assert a._enemy_copy_ability_policy == b._enemy_copy_ability_policy
    assert a._get_resolved_configured_area_boss_goal_key() == b._get_resolved_configured_area_boss_goal_key()
    assert (Counter(i.name for i in original.precollected_items[1])
            == Counter(i.name for i in rebuilt.precollected_items[1]))

    def topology(mw):
        return sorted((e.name, e.connected_region.name if e.connected_region else None)
                      for r in mw.regions for e in r.exits)
    assert topology(original) == topology(rebuilt)
    assert ({(loc.name, loc.address) for loc in original.get_locations()}
            == {(loc.name, loc.address) for loc in rebuilt.get_locations()})
    received = []
    assert snapshot(original, received) == snapshot(rebuilt, received)
    for item in original.itempool:
        if item.advancement:
            received.append(item.name)
            assert snapshot(original, received) == snapshot(rebuilt, received)


@pytest.mark.parametrize("version", [None, 1, 99, True, 2.0, "2"])
def test_unsupported_tracker_versions_are_rejected(version):
    with pytest.raises(ValueError, match="Update the KirbyAM APWorld and generate a new seed"):
        KirbyAmWorld.interpret_slot_data({"tracker": {"version": version}})


@pytest.mark.parametrize("slot", [
    {}, {"tracker": None}, {"tracker": {"version": 2, "options": []}},
    {"tracker": {"version": 2, "options": {}}},
])
def test_missing_or_malformed_tracker_data_fails_explicitly(slot):
    with pytest.raises(ValueError, match="tracker|Tracker"):
        KirbyAmWorld.interpret_slot_data(slot)


@pytest.mark.parametrize("mode", [1, 2])
def test_tracker_schema_distinguishes_fixed_copy_room_statues(mode):
    from ..traversal_data import graph_items
    from ..wheel_traversal import COPY_ROOM_REGION, RACE_ENTRANCE, wheel_graph

    original = setup_multiworld(KirbyAmWorld, seed=1054, options={
        "ability_randomization_mode": mode,
        "ability_randomization_statues": 1,
        "ability_gating": 1,
        "area_keys": 0,
    })
    slot = json.loads(json.dumps(original.worlds[1].fill_slot_data()))
    assert slot["tracker"]["version"] == 2
    legacy = json.loads(json.dumps(slot))
    legacy["tracker"]["version"] = 1
    with pytest.raises(ValueError, match="Update the KirbyAM APWorld and generate a new seed"):
        reconstruct(legacy)

    restored = reconstruct(slot)
    assert restored.worlds[1]._enemy_copy_ability_policy == original.worlds[1]._enemy_copy_ability_policy
    for mw in (original, restored):
        world = mw.worlds[1]
        state = CollectionState(mw)
        access = "Copy Ability Room Access"
        for item in (graph_items(wheel_graph(True)) - {access}) | {"Wheel Ability"}:
            state.collect(world.create_item(item), prevent_sweep=True)
        entrance = mw.get_entrance(RACE_ENTRANCE, 1)
        with patch.object(state, "can_reach_region", side_effect=lambda region, _p: region == COPY_ROOM_REGION):
            assert not entrance.access_rule(state)
            state.collect(world.create_item(access), prevent_sweep=True)
            assert entrance.access_rule(state)
            state.remove(world.create_item("Wheel Ability"))
            assert not entrance.access_rule(state)


def test_shuffled_statue_spoiler_names_copy_room_exception():
    world = setup_multiworld(KirbyAmWorld, seed=1054, options={
        "ability_randomization_mode": 1,
        "ability_randomization_statues": 1,
    }).worlds[1]
    spoiler = io.StringIO()
    world.write_spoiler(spoiler)
    text = spoiler.getvalue()
    assert "Enemy and World Statue Copy Ability Shuffle (Copy Ability Room excluded)" in text
    assert "Wheel Statue" in text


def test_upstream_ut_core_history_checks_and_reconnect():
    core_module = pytest.importorskip('worlds.tracker.TrackerCore', reason='install upstream UT to run its actual core')
    from worlds.tracker import DeferredEntranceMode
    original = setup_multiworld(KirbyAmWorld, seed=1054, options={'room_sanity': 1, 'ability_randomization_mode': 1})
    slot = json.loads(json.dumps(original.worlds[1].fill_slot_data()))
    mw = reconstruct(slot)
    starts = list(original.precollected_items[1])
    # This is UT's run_generator cleanup, not an invented starting-item grant.
    mw.precollected_items[1] = [i for i in mw.precollected_items[1] if i.code is None]
    core = core_module.TrackerCore(logging.getLogger(__name__), False, False)
    core.multiworld, core.player_id, core.slot = mw, 1, 1
    core.enforce_deferred_connections = DeferredEntranceMode.default
    core.hide_excluded = False
    core.output_format = 'Location'
    core.sorting_priorities = {group.value: n for n, group in enumerate(core_module.TrackerLogLineGroup)}
    missing = {loc.address for loc in mw.get_locations() if loc.address is not None}
    core.set_missing_locations(missing)
    history = [NetworkItem(i.code, -2, 0, i.classification) for i in starts]
    history += [NetworkItem(i.code, -1, 2, i.classification) for i in original.itempool if i.advancement]
    for end in (len(starts), len(history), len(history)):
        core.set_items_received(history[:end])
        result = core.updateTracker()
        received_names = [original.worlds[1].item_id_to_name[i.item] for i in history[len(starts):end]]
        expected, goal = snapshot(original, received_names)
        assert set(core.locations_available) == expected
        assert mw.completion_condition[1](result.state) == goal
        assert result.all_items == Counter(original.worlds[1].item_id_to_name[i.item] for i in history[:end])
    checked = next(iter(core.locations_available))
    core.set_missing_locations(missing - {checked})
    assert checked not in {mw.worlds[1].location_name_to_id[n] for n in core.updateTracker().in_logic_locations}
    core.disconnect()
    assert core.multiworld is None and core.player_id is None


@pytest.mark.parametrize("mode,rooms", [("shuffled", "false"), ("off", "true")])
def test_real_ut_yamlless_generation_and_spheres(tmp_path, monkeypatch, mode, rooms):
    """Real Generate/Main + upstream UT initialization/core; no sockets or GUI."""
    import sys
    import Generate
    import Main
    core_module = pytest.importorskip('worlds.tracker.TrackerCore')
    from worlds.tracker import DeferredEntranceMode
    players = tmp_path / 'players'
    players.mkdir()
    (players / 'player.yaml').write_text(f'''name: UT1054
game: Kirby & The Amazing Mirror
Kirby & The Amazing Mirror:
  ability_randomization_mode: {mode}
  configured_area_boss: random
  goal: random
  shards: random
  room_sanity: {rooms}
  area_keys: true
  ability_gating: {str(mode != "off").lower()}
  exclude_locations:
    - Rainbow Route 1-06 (Lower) - Small Chest
  start_inventory:
    Sword Ability: 2
    Phone a Friend: 1
    Cell Phone Battery: 2
    Copy Ability Room Access: 1
    Moonlight Mansion - Hub Connection: 1
''')
    monkeypatch.setattr(sys, 'argv', ['Generate.py', '--player_files_path', str(players), '--seed', '1054'])
    args = Generate.mystery_argparse()
    args.weights_file_path = args.meta_file_path = None
    args.skip_output = True
    original = Main.main(*Generate.main(args))
    slot = json.loads(json.dumps(original.worlds[1].fill_slot_data()))
    core = core_module.TrackerCore(logging.getLogger(__name__), False, False)
    priorities = {group.value: n for n, group in enumerate(core_module.TrackerLogLineGroup)}
    monkeypatch.setattr(core, '_set_host_settings', lambda: (
        str(tmp_path / 'no-yaml'), 'Location', False, False,
        DeferredEntranceMode.default, False, priorities, 'location'))
    monkeypatch.setattr(core, 'cached_multiworlds', [])
    monkeypatch.setattr(core, 'cached_slot_data', [])
    core.set_slot_params(KirbyAmWorld.game, 1, 'UT1054', 0)
    core.initalize_tracker_core(KirbyAmWorld, slot)
    assert core.multiworld is not None, core.gen_error
    assert (core.get_current_world().options.exclude_locations.value
            == original.worlds[1].options.exclude_locations.value)
    missing = {loc.address for loc in original.get_locations() if loc.address is not None}
    history = [NetworkItem(i.code, -2, 0, i.classification) for i in original.precollected_items[1]]
    state = CollectionState(original)
    while missing:
        state.sweep_for_advancements(locations=[loc for loc in original.get_locations() if loc.address is None])
        expected = {loc.address for loc in original.get_reachable_locations(state, 1) if loc.address in missing}
        core.set_missing_locations(missing.copy())
        core.set_items_received(history.copy())
        result = core.updateTracker()
        assert set(core.locations_available) == expected
        assert original.completion_condition[1](state) == core.multiworld.completion_condition[1](result.state)
        if not expected:
            break
        for address in expected:
            location = next(loc for loc in original.get_locations() if loc.address == address)
            item = location.item
            state.collect(item, True)
            history.append(NetworkItem(item.code, address, 1, item.classification))
        missing -= expected
    assert original.completion_condition[1](state)
    # Reconnect invokes real initialization with cached slot data and full history.
    core.disconnect()
    core.set_slot_params(KirbyAmWorld.game, 1, 'UT1054', 0)
    core.initalize_tracker_core(KirbyAmWorld, slot)
    core.set_missing_locations(missing)
    core.set_items_received(history)
    result = core.updateTracker()
    assert slot['tracker']['precollected_items']['Sword Ability'] == 2
    assert slot['tracker']['precollected_items']['Phone a Friend'] == 1
    assert result.all_items == Counter(original.worlds[1].item_id_to_name[i.item] for i in history)
    assert result.all_items['Cell Phone Battery'] >= 2
    assert core.multiworld.completion_condition[1](result.state)

    # UT's exclusion display switch must survive YAML-less initialization too.
    core.hide_excluded = True
    core.set_missing_locations({loc.address for loc in original.get_locations() if loc.address is not None})
    result = core.updateTracker()
    assert 'Rainbow Route 1-06 (Lower) - Small Chest' not in result.in_logic_locations
    core.hide_excluded = False
    result = core.updateTracker()
    assert 'Rainbow Route 1-06 (Lower) - Small Chest' in result.in_logic_locations


@pytest.mark.parametrize("key", ["enemy_copy_ability_policy", "goal_configured_area_boss_key",
                                 "starting_kirby_color", "starting_kirby_color_name", "inventory"])
def test_incomplete_resolved_payload_is_rejected(key):
    world = setup_multiworld(KirbyAmWorld, seed=1054).worlds[1]
    slot = json.loads(json.dumps(world.fill_slot_data()))
    if key == "inventory":
        del slot["tracker"]["precollected_items"]
    else:
        del slot[key]
    with pytest.raises(ValueError, match="Missing Kirby tracker"):
        reconstruct(slot)


@pytest.mark.parametrize('qualified', [False, True])
@pytest.mark.parametrize('starting_phone', [False, True])
def test_phone_profile_and_ownership_roundtrip(qualified, starting_phone):
    """Source graph parity for both Phone route profiles and inventory origins."""
    from ..phone_traversal import PHONE, ENTRANCE, validate_phone_profile
    original = setup_multiworld(KirbyAmWorld, seed=1054, options={
        'ability_randomization_mode': 0 if qualified else 1,
        'ability_gating': 0 if qualified else 1,
        'minimum_health': 6, 'maximum_health': 10,
        'enemy_health_multiplier': 100, 'room_sanity': 1,
    })
    if starting_phone:
        original.worlds[1].push_precollected(original.worlds[1].create_item(PHONE))
    slot = json.loads(json.dumps(original.worlds[1].fill_slot_data()))
    rebuilt = reconstruct(slot)
    assert original.worlds[1]._phone_route_signature == rebuilt.worlds[1]._phone_route_signature
    states = []
    for mw in (original, rebuilt):
        world = mw.worlds[1]
        assert validate_phone_profile(world, require_policy=True) is qualified
        assert sum(item.name == PHONE for item in mw.precollected_items[1]) == int(starting_phone)
        state = CollectionState(mw)
        for item in original.itempool:
            if item.advancement and item.name != PHONE:
                state.collect(world.create_item(item.name), True)
        state.sweep_for_advancements()
        assert mw.get_entrance(ENTRANCE, 1).can_reach(state) is starting_phone
        if not starting_phone:
            state.collect(world.create_item(PHONE), True)
        assert state.count(PHONE, 1) == 1
        assert mw.get_entrance(ENTRANCE, 1).can_reach(state)
        states.append({loc.name for loc in mw.get_reachable_locations(state, 1)})
    assert states[0] == states[1]
