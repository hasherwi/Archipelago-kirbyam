"""Reconcile location-dependent permissions after real regions exist."""

import json
from pathlib import Path

import pytest
from BaseClasses import CollectionState, ItemClassification
from test.general import setup_multiworld

from .support.source_policy import set_rule_test_policy
from .. import KirbyAmWorld
from ..data import data
from ..traversal import SourcePolicy
from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive
from .test_traversal import policy

ROOT = Path(__file__).parents[1] / 'dev-docs'
CASES = [
    ('Ice', 'MR_FROSTY', 'MINOR_CHEST_MUSIC_NOTE_10', None),
    ('Crash', 'TWISTER', 'MAJOR_CHEST_MUSTARD_MOUNTAIN', 'REGION_RAINBOW_ROUTE/ROOM_1_HUB_4'),
    ('Missile', 'WADDLE_DOO', 'MINOR_CHEST_SPRAY_PAINT_12', 'REGION_CABBAGE_CAVERN/ROOM_3_HUB_2'),
    ('Parasol', 'WADDLE_DOO', 'MINOR_CHEST_SPRAY_PAINT_12', 'REGION_CABBAGE_CAVERN/ROOM_3_HUB_2'),
]


def source_policy(ability):
    if ability == 'Ice':
        return policy(0).policy
    filename = ('mustard-map-crash-acceptance.json' if ability == 'Crash'
                else f'cabbage-{ability.lower()}-acceptance.json')
    return json.loads((ROOT / filename).read_text())['source_policy']


@pytest.mark.parametrize('ability,source,location,access', CASES[:2])
@pytest.mark.parametrize('gating,count', [(1, 1), (1, 3), (0, 1)])
def test_real_generation_starting_ice_and_twister_crash_permissions(
        tmp_path, monkeypatch, ability, source, location, access, gating, count):
    import Main

    generated, region_states = [], []
    main, create_regions = Main.main, KirbyAmWorld.create_regions

    def capture_regions(world):
        create_regions(world)
        region_states.append(world.multiworld.state.count(f'{ability} Ability', world.player))

    def capture_main(*args, **kwargs):
        multiworld = main(*args, **kwargs)
        generated.append(multiworld)
        return multiworld

    monkeypatch.setattr(KirbyAmWorld, 'create_regions', capture_regions)
    monkeypatch.setattr(Main, 'main', capture_main)
    player = tmp_path / 'player.yaml'
    mode, seed = (0, 5) if ability == 'Ice' else (1, 15)
    player.write_text(
        'name: Starting Permission\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n'
        f'  ability_randomization_mode: {mode}\n  ability_randomization_no_ability_weight: 0\n'
        f'  ability_gating: {gating}\n  start_inventory:\n    {ability} Ability: {count}\n'
        '  minimum_health: 1\n  maximum_health: 1\n  accessibility: full\n', encoding='utf-8')
    archive = generate_archive_from_fixture(player, tmp_path / 'out', seed=seed)
    decoded = load_multidata_from_archive(archive)
    resolver = SourcePolicy(decoded['slot_data'][1]['enemy_copy_ability_policy'])
    assert resolver.grant(source, lambda _: True).guaranteed == frozenset({ability})
    if ability == 'Crash':
        assert all(resolver.grant(s, lambda _: True).guaranteed != frozenset({'Crash'})
                   for s in ('FOLEY', 'HOT_HEAD'))  # Exercise only the late Twister/map condition.
    code = KirbyAmWorld.item_name_to_id[f'{ability} Ability']
    assert decoded['precollected_items'][1].count(code) == count
    multiworld, = generated
    assert not multiworld.get_unfilled_locations()
    assert multiworld.can_beat_game() and multiworld.fulfills_accessibility()
    assert region_states == [count if gating else 0]
    starting = [item for item in multiworld.precollected_items[1] if item.name == f'{ability} Ability']
    assert len(starting) == count
    assert all(item.classification == (ItemClassification.progression if gating else ItemClassification.useful)
               for item in starting)
    state = CollectionState(multiworld)
    assert state.count(f'{ability} Ability', 1) == (count if gating else 0)
    state.can_reach_region = lambda name, player: name == access
    chest = multiworld.get_location(data.locations[location].label, 1)
    assert chest.access_rule(state)
    for item in starting:
        state.remove(item)
    assert not state.has(f'{ability} Ability', 1)
    assert chest.access_rule(state) is (not gating)


@pytest.mark.parametrize('ability,source,location,access', CASES)
@pytest.mark.parametrize('scenario', ['enabled', 'gating_off', 'absent', 'wrong_source'])
def test_reconciliation_preserves_predicates_and_existing_counts(
        monkeypatch, ability, source, location, access, scenario):
    from .. import regions

    raw = source_policy(ability) if scenario != 'wrong_source' else policy(1, pool=['Beam']).policy
    set_rule_test_policy(monkeypatch, lambda *args, **kwargs: raw)
    multiworld = setup_multiworld(KirbyAmWorld, steps=('generate_early',), seed=5, options={
        'ability_randomization_mode': raw['mode'], 'ability_gating': int(scenario != 'gating_off'),
        'accessibility': 'minimal',
    })
    world = multiworld.worlds[1]
    if scenario == 'absent':
        create_regions = regions.create_regions

        def without_target(current_world):
            result = create_regions(current_world)
            target = current_world.multiworld.get_location(data.locations[location].label, current_world.player)
            target.parent_region.locations.remove(target)
            return result

        monkeypatch.setattr(regions, 'create_regions', without_target)
    ready = world.create_item(f'{ability} Ability')
    ready.classification = ItemClassification.progression
    multiworld.push_precollected(ready)
    early = [world.create_item(f'{ability} Ability') for _ in range(2)]
    early_ice = ability == 'Ice' and scenario != 'gating_off'
    assert all(item.classification == (ItemClassification.progression if early_ice else ItemClassification.useful)
               for item in early)
    for item in early:
        multiworld.push_precollected(item)
    unrelated = world.create_item('Magic Ability')
    assert unrelated.classification == ItemClassification.useful
    multiworld.push_precollected(unrelated)
    assert multiworld.state.count(f'{ability} Ability', 1) == (3 if early_ice else 1)
    world.create_regions()
    expected = 3 if early_ice or scenario == 'enabled' else 1
    assert multiworld.state.count(f'{ability} Ability', 1) == expected
    assert CollectionState(multiworld).count(f'{ability} Ability', 1) == expected
    assert all(item.advancement is (early_ice or scenario == 'enabled') for item in early)
    assert ready.classification == ItemClassification.progression
    assert unrelated.classification == ItemClassification.useful
    assert not multiworld.state.has('Magic Ability', 1)
    if scenario == 'absent':
        with pytest.raises(KeyError):
            multiworld.get_location(data.locations[location].label, 1)


@pytest.mark.parametrize('ability', ['Ice', 'Missile', 'Parasol'])
def test_disabled_minor_category_does_not_promote_starting_permission(monkeypatch, ability):
    raw = source_policy(ability)
    monkeypatch.setattr(KirbyAmWorld, 'ENABLE_MINOR_CHESTS', False)
    set_rule_test_policy(monkeypatch, lambda *args, **kwargs: raw)
    multiworld = setup_multiworld(KirbyAmWorld, steps=('generate_early',), seed=5, options={
        'ability_randomization_mode': raw['mode'], 'ability_gating': 1, 'accessibility': 'minimal',
    })
    world = multiworld.worlds[1]
    item = world.create_item(f'{ability} Ability')
    multiworld.push_precollected(item)
    world.create_regions()
    assert item.classification == ItemClassification.useful
    assert not multiworld.state.has(item.name, 1)
    assert not CollectionState(multiworld).has(item.name, 1)
