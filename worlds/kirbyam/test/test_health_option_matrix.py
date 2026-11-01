"""Finite health/pool combinations; no emulator or unrestricted AP option claim."""

import logging

from collections import Counter
from itertools import product
from types import SimpleNamespace

import pytest

from BaseClasses import ItemClassification
from ..health import resolve_health_range
from .test_health_range import VALID_RANGES
from .test_item_pool import _build_world_for_create_items, _vitality_item_codes


@pytest.fixture
def quiet_pool_logs():
    previous = logging.root.manager.disable
    logging.disable(logging.CRITICAL)
    try:
        yield
    finally:
        logging.disable(previous)


@pytest.mark.parametrize("minimum,maximum,mode", list(product(range(1, 11), range(1, 11), range(3))))
def test_entire_health_input_domain(minimum, maximum, mode):
    valid = mode != 0 or (minimum <= maximum)
    if not valid:
        with pytest.raises(ValueError):
            resolve_health_range(minimum, maximum, mode)
        return
    resolved = resolve_health_range(minimum, maximum, mode)
    expected = (minimum, maximum) if mode == 0 else ((1, 1) if mode == 1 else (1, 5))
    assert (resolved.minimum, resolved.maximum) == expected


@pytest.mark.parametrize("minimum,maximum", VALID_RANGES)
@pytest.mark.parametrize("shards,no_lives,maps,gating", list(product((0, 2), range(2), range(2), range(2))))
def test_health_pool_all_percentages_and_modifiers(minimum, maximum, shards, no_lives, maps, gating, quiet_pool_logs):
    # Disabled traps make their percentage immaterial; test that branch once.
    # Enabled traps exhaust every integer percentage, including rounding edges.
    for traps, percentage in [(0, 100)] + [(1, value) for value in range(101)]:
        world, locations = _build_world_for_create_items(
            shards, start_with_all_maps=maps, enable_traps=traps, trap_fill_percentage=percentage,
        )
        world.options.minimum_health = SimpleNamespace(value=minimum)
        world.options.maximum_health = SimpleNamespace(value=maximum)
        world.options.no_extra_lives.value = no_lives
        world.options.ability_gating = SimpleNamespace(value=gating)
        world.create_items()
        pool = world.multiworld.itempool
        context = (minimum, maximum, shards, no_lives, maps, gating, traps, percentage)
        assert len(pool) == sum(loc.item is None for loc in locations), context
        vitality = _vitality_item_codes()
        assert Counter(item.code for item in pool if item.code in vitality) == Counter(
            sorted(vitality)[:maximum - minimum]
        ), context
        filler = [item for item in pool if item.classification == ItemClassification.filler]
        trap_items = [item for item in pool if item.classification == ItemClassification.trap]
        disposable_count = len(filler) + len(trap_items)
        assert len(trap_items) == (disposable_count * percentage // 100 if traps else 0), context
        assert all(item.name in world._active_filler_pool() for item in filler), context
        assert all(item.name in world._active_trap_pool() for item in trap_items), context
        if maximum == 1:
            assert not {"Small Food", "Energy Drink", "Hunk of Meat", "Max Tomato"}.intersection(
                item.name for item in pool
            ), context
        if minimum == 1:
            assert "Health Down Trap" not in {item.name for item in pool}, context
        if no_lives:
            assert "1 Up" not in {item.name for item in pool}, context


@pytest.mark.parametrize("minimum,maximum", VALID_RANGES)
@pytest.mark.parametrize("scenario", range(12))
def test_health_cross_option_archive_generation(tmp_path, minimum, maximum, scenario):
    """Cross every health range with 12 mixed scenarios, not a Cartesian proof."""
    from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive

    player = tmp_path / "player.yaml"
    player.write_text(
        "name: Health Matrix\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n"
        f"  minimum_health: {minimum}\n  maximum_health: {maximum}\n"
        f"  goal: {scenario % 3}\n  configured_area_boss: {scenario % 8}\n"
        f"  shards: {(scenario % 2) * 2}\n  room_sanity: {scenario % 2}\n"
        f"  ability_gating: {(scenario // 2) % 2}\n"
        f"  start_with_all_maps: {(scenario // 3) % 2}\n"
        f"  no_extra_lives: {(scenario // 2) % 2}\n"
        f"  enable_traps: {(scenario // 3) % 2}\n"
        f"  trap_fill_percentage: {(0, 1, 25, 99, 100)[scenario % 5]}\n"
        f"  death_link: {scenario % 2}\n"
        f"  enemy_health_multiplier: {(50, 100, 500)[scenario % 3]}\n"
        f"  ability_randomization_mode: {(scenario // 4) % 3}\n"
        f"  ability_randomization_no_ability_weight: {(0, 50, 100)[scenario % 3]}\n"
        f"  ability_randomization_boss_spawns: {scenario % 2}\n"
        f"  ability_randomization_minibosses: {(scenario // 2) % 2}\n"
        f"  ability_randomization_minny: {(scenario // 3) % 2}\n"
        f"  ability_randomization_passive_enemies: {(scenario // 4) % 2}\n"
        f"  ability_randomization_statues: {(scenario // 5) % 2}\n",
        encoding="utf-8",
    )
    archive = generate_archive_from_fixture(player, tmp_path / "output", seed=934 + scenario)
    decoded = load_multidata_from_archive(archive)
    slot_data = decoded["slot_data"][1]
    assert (slot_data["minimum_health"], slot_data["maximum_health"]) == (minimum, maximum)
    vitality = _vitality_item_codes()
    assert Counter(item[0] for item in decoded["locations"][1].values() if item[0] in vitality) == Counter(
        sorted(vitality)[:maximum - minimum]
    )
