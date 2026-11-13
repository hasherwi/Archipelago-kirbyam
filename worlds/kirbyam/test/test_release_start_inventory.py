"""Release contract: physical source logic replaces forced Stone/Burning starts.

These tests intentionally require the reviewed release inventory delta. They do
not alter defaults with monkeypatches, and do not prove route soundness by themselves.
"""
from argparse import Namespace
from collections import Counter
from typing import cast

import pytest
from BaseClasses import CollectionState, ItemClassification, MultiWorld

from .. import KirbyAmWorld
from ..items import KirbyAmItem
from ..enemy_ability_data import (
    ABILITY_NAME_TO_ID, GATEABLE_ENEMY_COPY_ABILITIES,
    LEGACY_SLOT_GATEABLE_ABILITIES, STARTING_COPY_ABILITIES,
    resolve_slot_gateable_abilities, starting_copy_abilities,
)


def early_world(mode: int, gating: bool, explicit: dict[str, int] | None = None) -> KirbyAmWorld:
    """Mirror Main: generate_early, explicit start inventory, then regions/rules."""
    multiworld = MultiWorld(1)
    multiworld.game[1] = KirbyAmWorld.game
    multiworld.player_name = {1: 'Release starts'}
    multiworld.set_seed(773)
    args = Namespace()
    options = {'ability_randomization_mode': mode, 'ability_gating': gating,
               'accessibility': 'minimal', 'start_inventory': explicit or {}}
    for name, option in KirbyAmWorld.options_dataclass.type_hints.items():
        setattr(args, name, {1: option.from_any(options.get(name, option.default))})
    multiworld.set_options(args)
    world = multiworld.worlds[1]
    assert isinstance(world, KirbyAmWorld)
    multiworld.state = CollectionState(multiworld)
    world.generate_early()
    for name, count in world.options.start_inventory.value.items():
        for _ in range(count):
            multiworld.push_precollected(multiworld.create_item(name, 1))
    return world


def test_release_catalog_preserves_legacy_receipt_protocol() -> None:
    assert STARTING_COPY_ABILITIES == ('Beam', 'Burning', 'Cutter', 'Mini', 'Stone', 'Wheel')
    assert len(LEGACY_SLOT_GATEABLE_ABILITIES) == 22
    legacy = sum(1 << ABILITY_NAME_TO_ID[n] for n in LEGACY_SLOT_GATEABLE_ABILITIES)
    current = sum(1 << ABILITY_NAME_TO_ID[n] for n in GATEABLE_ENEMY_COPY_ABILITIES)
    assert legacy == 0x03FFFE76
    assert current == 0x03FFFF7E
    assert len(GATEABLE_ENEMY_COPY_ABILITIES) == 24
    assert set(GATEABLE_ENEMY_COPY_ABILITIES) == set(LEGACY_SLOT_GATEABLE_ABILITIES) | {'Stone', 'Burning'}
    empty_values: tuple[object, ...] = (None, [], '', (), 0)
    for empty in empty_values:
        assert resolve_slot_gateable_abilities(empty) == LEGACY_SLOT_GATEABLE_ABILITIES
    assert resolve_slot_gateable_abilities(list(GATEABLE_ENEMY_COPY_ABILITIES)) == GATEABLE_ENEMY_COPY_ABILITIES


@pytest.mark.parametrize('mode', [0, 1, 2])
@pytest.mark.parametrize('gating', [False, True])
def test_beam_and_ice_forced_and_exact_ability_pool(mode: int, gating: bool) -> None:
    assert starting_copy_abilities(mode) == ('Beam', 'Ice')
    world = early_world(mode, gating)
    before = Counter(i.name for i in world.multiworld.precollected_items[1] if 'Abilities' in cast(KirbyAmItem, i).tags)
    assert before == {'Beam Ability': 1, 'Ice Ability': 1}
    assert world.multiworld.state.count('Ice Ability', 1) == 1
    ice = world.create_item('Ice Ability')
    assert world.remove(world.multiworld.state, ice)
    assert not world.multiworld.state.has('Ice Ability', 1)
    assert world.collect(world.multiworld.state, ice)
    assert world.multiworld.state.count('Ice Ability', 1) == 1
    for ability in ('Stone', 'Burning'):
        item = world.create_item(ability + ' Ability')
        assert item.classification == ItemClassification.progression
        assert world.multiworld.state.count(item.name, 1) == 0
    world.create_regions()
    world.set_rules()
    world.create_items()
    ability_pool = [i for i in world.multiworld.itempool if 'Abilities' in cast(KirbyAmItem, i).tags]
    assert len(ability_pool) == (23 if gating else 0)
    assert Counter(i.name for i in ability_pool) == (
        Counter({n + ' Ability': 1 for n in GATEABLE_ENEMY_COPY_ABILITIES if n != 'Ice'}) if gating else Counter())
    assert Counter(i.name for i in world.multiworld.precollected_items[1]
                   if 'Abilities' in cast(KirbyAmItem, i).tags) == before
    slot = world.fill_slot_data()
    assert tuple(slot['ability_gateable_abilities']) == (GATEABLE_ENEMY_COPY_ABILITIES if gating else ())


@pytest.mark.parametrize('mode', [0, 1, 2])
def test_explicit_starts_additive_main_order_and_multiplicity(mode: int) -> None:
    explicit = {'Beam Ability': 2, 'Stone Ability': 3, 'Burning Ability': 2, 'Ice Ability': 3}
    world = early_world(mode, True, explicit)
    actual = Counter(i.name for i in world.multiworld.precollected_items[1] if 'Abilities' in cast(KirbyAmItem, i).tags)
    assert actual == explicit  # No additional automatic copy of an explicit Beam or Ice.
    for name in ('Stone Ability', 'Burning Ability', 'Ice Ability'):
        assert world.multiworld.state.count(name, 1) == explicit[name]
    world.create_regions()
    world.set_rules()
    world.create_items()
    for name in ('Stone Ability', 'Burning Ability', 'Ice Ability'):
        assert world.multiworld.state.count(name, 1) == explicit[name]
    # Explicit start_inventory is additive, unlike start_inventory_from_pool.
    pool = Counter(i.name for i in world.multiworld.itempool if 'Abilities' in cast(KirbyAmItem, i).tags)
    assert pool['Stone Ability'] == pool['Burning Ability'] == 1
    assert pool['Ice Ability'] == 0
    assert sum(pool.values()) == 23
