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
    resolve_slot_gateable_abilities,
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


def test_missing_slot_catalog_uses_current_gates() -> None:
    for missing in (None, [], '', (), 0):
        assert resolve_slot_gateable_abilities(missing) == GATEABLE_ENEMY_COPY_ABILITIES
    assert len(GATEABLE_ENEMY_COPY_ABILITIES) == 25
    assert sum(1 << ABILITY_NAME_TO_ID[n] for n in GATEABLE_ENEMY_COPY_ABILITIES) == 0x03FFFFFE


@pytest.mark.parametrize('mode', [0, 1, 2])
@pytest.mark.parametrize('gating', [False, True])
def test_no_automatic_ability_starts_and_exact_gated_pool(mode: int, gating: bool) -> None:
    world = early_world(mode, gating)
    before = Counter(i.name for i in world.multiworld.precollected_items[1] if 'Abilities' in cast(KirbyAmItem, i).tags)
    assert not before
    assert world.multiworld.state.count('Ice Ability', 1) == 0
    assert world.multiworld.state.count('Beam Ability', 1) == 0
    for ability in ('Stone', 'Burning'):
        item = world.create_item(ability + ' Ability')
        assert item.classification == ItemClassification.progression
        assert world.multiworld.state.count(item.name, 1) == 0
    world.create_regions()
    world.set_rules()
    world.create_items()
    ability_pool = [i for i in world.multiworld.itempool if 'Abilities' in cast(KirbyAmItem, i).tags]
    assert len(ability_pool) == (25 if gating else 0)
    assert Counter(i.name for i in ability_pool) == (
        Counter({n + ' Ability': 1 for n in GATEABLE_ENEMY_COPY_ABILITIES}) if gating else Counter())
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
    for item in world.multiworld.precollected_items[1]:
        if item.name not in explicit:
            continue
        expected = explicit[item.name] if item.advancement else 0
        assert world.multiworld.state.count(item.name, 1) == expected
    world.create_regions()
    world.set_rules()
    world.create_items()
    for item in world.multiworld.precollected_items[1]:
        if item.name not in explicit:
            continue
        expected = explicit[item.name] if item.advancement else 0
        assert world.multiworld.state.count(item.name, 1) == expected
    # Explicit start_inventory is additive, unlike start_inventory_from_pool.
    pool = Counter(i.name for i in world.multiworld.itempool if 'Abilities' in cast(KirbyAmItem, i).tags)
    assert pool['Stone Ability'] == pool['Burning Ability'] == 1
    assert pool['Ice Ability'] == 1
    assert pool['Beam Ability'] == 1
    assert sum(pool.values()) == 25
