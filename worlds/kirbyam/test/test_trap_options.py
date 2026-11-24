"""Per-type exclusions apply to the generated pool without changing filler or RNG semantics."""
import json
from collections import Counter
from types import SimpleNamespace

import pytest

from BaseClasses import PlandoOptions
from Options import OptionError
from test.general import setup_multiworld
from .. import KirbyAmWorld
from ..data import data
from ..options import ExcludeTrapTypes, RandomizeShards
from .test_item_pool import _build_world_for_create_items
from .test_universal_tracker import reconstruct


TRAPS = frozenset(data.available_trap_item_labels)
AUTO_EXCLUDED = frozenset({"Health Down Trap", "Life Down Trap", "Life Wipeout Trap"})


def generated(enabled=1, percentage=100, exclusions=None, automatic=False):
    world, _ = _build_world_for_create_items(
        RandomizeShards.option_completely_random, enable_traps=enabled, trap_fill_percentage=percentage,
    )
    if exclusions is not None:
        world.options.exclude_trap_types = ExcludeTrapTypes.from_any(exclusions)
    if automatic:
        world.options.no_extra_lives = SimpleNamespace(value=True)
        world.options.minimum_health = SimpleNamespace(value=1)
        world.options.maximum_health = SimpleNamespace(value=5)
    world.create_items()
    pool = world.multiworld.itempool
    return tuple(item.name for item in pool), Counter(item.name for item in pool if item.trap)


@pytest.mark.parametrize("selected", [{"Battery Drain Trap"}, {"Bomb Trap", "Hub Teleport Trap"}, TRAPS])
def test_requested_trap_types_never_leak_and_fill_percentage_keeps_quantity(selected):
    exclusions = TRAPS - selected
    full_pool, full_traps = generated(exclusions=[])
    pool, actual = generated(exclusions=exclusions)
    assert actual.keys() == selected
    assert len(pool) == len(full_pool)
    assert actual.total() == full_traps.total()
    quarter = generated(percentage=25, exclusions=exclusions)[1]
    assert quarter.total() == full_traps.total() // 4
    assert quarter.keys() <= selected
    assert generated(exclusions=sorted(exclusions)) == generated(exclusions=sorted(exclusions, reverse=True))


@pytest.mark.parametrize("automatic", [False, True])
def test_empty_eligible_pool_falls_back_to_identical_ordinary_filler(automatic):
    exclusions = TRAPS - AUTO_EXCLUDED if automatic else TRAPS
    assert generated(exclusions=exclusions, automatic=automatic) == generated(
        enabled=0, exclusions=exclusions, automatic=automatic,
    )
    assert not generated(exclusions=exclusions, automatic=automatic)[1]


def test_automatic_exclusions_combine_with_user_and_overall_options():
    assert generated(exclusions=["Bomb Trap"], automatic=True)[1].keys() == {
        "Battery Drain Trap", "Hub Teleport Trap",
    }
    assert not generated(enabled=0, exclusions=["Bomb Trap"])[1]
    assert not generated(percentage=0, exclusions=["Bomb Trap"])[1]
    assert generated() == generated(exclusions=[])  # Legacy deterministic ordered pool.


def test_non_trap_option_key_is_rejected():
    with pytest.raises(OptionError, match="unexpected key"):
        ExcludeTrapTypes.from_any(["Small Food"]).verify(KirbyAmWorld, "Kirby", PlandoOptions.none)


def test_real_generation_and_tracker_roundtrip_selected_and_legacy_seed():
    options = {"enable_traps": 1, "trap_fill_percentage": 100,
               "exclude_trap_types": sorted(TRAPS - {"Bomb Trap"})}
    mw = setup_multiworld(KirbyAmWorld, options=options, seed=1040)
    assert {item.name for item in mw.itempool if item.trap} == {"Bomb Trap"}
    slot = json.loads(json.dumps(mw.worlds[1].fill_slot_data()))
    assert slot["tracker"]["options"]["exclude_trap_types"] == options["exclude_trap_types"]
    rebuilt = reconstruct(slot)
    assert rebuilt.worlds[1].options.exclude_trap_types.value == set(options["exclude_trap_types"])
    assert {item.name for item in rebuilt.itempool if item.trap} == {"Bomb Trap"}
    # The added choice defaults to no exclusions in pre-option schema-1 slots.
    del slot["tracker"]["options"]["exclude_trap_types"]
    rebuilt = reconstruct(slot)
    assert not rebuilt.worlds[1].options.exclude_trap_types.value
    assert {item.name for item in rebuilt.itempool if item.trap} > {"Bomb Trap"}
