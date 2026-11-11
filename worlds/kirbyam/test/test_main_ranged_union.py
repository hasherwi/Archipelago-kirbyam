"""Merged main/ranged behavior, without claiming new native gameplay evidence."""
from copy import deepcopy
from types import SimpleNamespace
from typing import Any

import pytest

from Options import Accessibility
from .. import traversal_rules as rules
from ..traversal import compile_traversal_graph
from ..traversal_data import graph_items, room_traversal_graph, room_traversal_targets
from .test_traversal import policy
from .support.normal110_history import before_normal110

TARGET = 'frozen_825_sound_effects'


@pytest.mark.parametrize('witness,grant,permission', [
    ('local', 'Ice', 'Ice'), ('ufo_entry', 'UFO', 'UFO'),
    ('central_statues', 'Fire', 'Ice'), ('peppermint290_statues', 'Fire', 'Ice'),
])
@pytest.mark.parametrize('keys', [False, True])
@pytest.mark.parametrize('gating', [False, True])
def test_one_installed_goal2_rule_ors_all_four_independent_sources(
    monkeypatch: pytest.MonkeyPatch, witness: str, grant: str, permission: str, keys: bool, gating: bool,
) -> None:
    row, = [r for r in room_traversal_targets('block') if r['id'] == TARGET]
    assert 'requires_guaranteed_source' not in row
    assert len(row['graphs']) == 4
    monkeypatch.setattr(rules, 'extra_traversal_targets', lambda: (row,))
    resolver = policy(1, pool=[grant])
    target = SimpleNamespace(access_rule=lambda state: state.base_rule)
    world = SimpleNamespace(
        player=1, _enemy_copy_ability_policy=resolver.policy,
        _ability_gating_enabled=lambda: gating, _area_keys_enabled=lambda: keys,
        options=SimpleNamespace(ability_randomization_statues=SimpleNamespace(value=False),
                                accessibility=Accessibility(Accessibility.option_minimal)),
        multiworld=SimpleNamespace(get_location=lambda *_: target),
    )
    rules.install_extra_traversal_rules(world)
    graph = room_traversal_graph(TARGET, witness, keys)
    owned = set(graph_items(graph)) | {permission + ' Ability'}
    state = SimpleNamespace(base_rule=True, has=lambda item, _: item in owned,
                            can_reach_region=lambda name, _: name == graph.access_region)
    # Removing all other alternatives must still leave this branch sufficient.
    assert target.access_rule(state)
    owned.discard(permission + ' Ability')
    assert target.access_rule(state) is (not gating)
    owned.add(permission + ' Ability')
    if graph.access_region is not None:
        state.can_reach_region = lambda *_: False
        assert not target.access_rule(state)
    state.base_rule = False
    assert not target.access_rule(state)


@pytest.mark.parametrize('grant', ['Fire', 'Ice', 'UFO'])
def test_goal2_no_source_or_permission_fails_closed(monkeypatch: pytest.MonkeyPatch, grant: str) -> None:
    row = next(r for r in room_traversal_targets('block') if r['id'] == TARGET)
    monkeypatch.setattr(rules, 'extra_traversal_targets', lambda: (row,))
    resolver = policy(1, pool=[grant], statues=True)
    target = SimpleNamespace(access_rule=lambda state: True)
    world = SimpleNamespace(
        player=1, _enemy_copy_ability_policy=resolver.policy,
        _ability_gating_enabled=lambda: True, _area_keys_enabled=lambda: False,
        options=SimpleNamespace(ability_randomization_statues=SimpleNamespace(value=True),
                                accessibility=Accessibility(Accessibility.option_minimal)),
        multiworld=SimpleNamespace(get_location=lambda *_: target),
    )
    rules.install_extra_traversal_rules(world)
    state = SimpleNamespace(has=lambda *_: False, can_reach_region=lambda *_: False)
    assert not target.access_rule(state)


@pytest.mark.parametrize('witness,ability', [('local', 'Ice'), ('ufo_entry', 'UFO')])
def test_finite_goal2_conditions_are_raw_singletons(witness: str, ability: str) -> None:
    row = next(r for r in room_traversal_targets('block') if r['id'] == TARGET)
    payload = deepcopy(row['graphs'][witness])
    assert payload['requires_guaranteed_source'] == {'source_key': 'MR_FROSTY', 'ability': ability}
    payload['requires_guaranteed_source'] = {'source_key': 'MR_FROSTY', 'abilities': [ability]}
    with pytest.raises(ValueError, match='source'):
        compile_traversal_graph(payload)


@pytest.mark.parametrize('count', [0, 1, 3])
def test_main_order_ice_precollection_does_not_double_collect(count: int) -> None:
    from argparse import Namespace
    from BaseClasses import CollectionState, ItemClassification, MultiWorld
    from .. import KirbyAmWorld
    multiworld = MultiWorld(1)
    multiworld.game[1] = KirbyAmWorld.game
    multiworld.player_name = {1: 'Combined Ice lifecycle'}
    multiworld.set_seed(773)
    args = Namespace()
    overrides = {'ability_randomization_mode': 0, 'ability_gating': True,
                 'start_inventory': {'Ice Ability': count}, 'accessibility': 'minimal'}
    for name, option in KirbyAmWorld.options_dataclass.type_hints.items():
        setattr(args, name, {1: option.from_any(overrides.get(name, option.default))})
    multiworld.set_options(args)
    world = multiworld.worlds[1]
    multiworld.state = CollectionState(multiworld)
    world.generate_early()
    for _ in range(count):
        item = world.create_item('Ice Ability')
        assert item.classification == ItemClassification.progression
        multiworld.push_precollected(item)
    assert multiworld.state.count('Ice Ability', 1) == count
    world.create_regions()
    world.set_rules()
    assert multiworld.state.count('Ice Ability', 1) == count
    assert len([item for item in multiworld.precollected_items[1] if item.name == 'Ice Ability']) == count


def test_all_catalog_entries_match_the_two_reviewed_parents() -> None:
    import hashlib
    import json
    from pathlib import Path
    from ..data import load_json_data

    root = Path(__file__).resolve().parents[1]
    pins = json.loads((root / 'dev-docs/main-ranged-union-catalog.json').read_text())
    catalogs: dict[str, dict[str, Any]] = {'targets': {}, 'graph_parts': {}, 'source_sets': {}}
    rooms = load_json_data('regions/rooms.json')
    assert isinstance(rooms, dict)
    for region, room in rooms.items():
        traversal = room.get('traversal', {})
        for row in traversal.get('targets', []):
            assert row['id'] not in catalogs['targets']
            catalogs['targets'][row['id']] = before_normal110({'region': region, **row})
        for kind in ('graph_parts', 'source_sets'):
            for key, value in traversal.get(kind, {}).items():
                assert key not in catalogs[kind]
                catalogs[kind][key] = value
    for kind, entries in catalogs.items():
        actual = {key: hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
                  for key, value in entries.items()}
        assert actual == pins[kind]
