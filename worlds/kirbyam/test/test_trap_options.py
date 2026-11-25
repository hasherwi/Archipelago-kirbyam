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
from ..narcolepsy import NARCOLEPSY_ITEM_NAME, NARCOLEPSY_TRAP_CATALOG_VERSION
from ..random_teleport import RANDOM_TELEPORT_ITEM_NAME, TRAP_CATALOG_VERSION
from ..tracker import validate_tracker_data
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
        "Battery Drain Trap", "Hub Teleport Trap", "Narcolepsy", "Random Teleport Trap",
    }
    assert not generated(enabled=0, exclusions=["Bomb Trap"])[1]
    assert not generated(percentage=0, exclusions=["Bomb Trap"])[1]
    assert generated() == generated(exclusions=[])  # Legacy deterministic ordered pool.


def test_non_trap_option_key_is_rejected():
    with pytest.raises(OptionError, match="unexpected key"):
        ExcludeTrapTypes.from_any(["Small Food"]).verify(KirbyAmWorld, "Kirby", PlandoOptions.none)


@pytest.mark.parametrize("invalid", [[True], [0], [None], [["Bomb Trap"]], ["Bomb Trap", 0]])
def test_non_string_yaml_trap_key_raises_option_error(invalid):
    with pytest.raises(OptionError, match="Exclude Trap Types expects trap names as strings"):
        ExcludeTrapTypes.from_any(invalid)


@pytest.mark.parametrize("invalid", ["Bomb Trap", None, True, {}, [True], [0], ["Small Food"], ["bomb trap"]])
def test_invalid_present_tracker_exclusions_fail_closed(invalid):
    slot = setup_multiworld(KirbyAmWorld, seed=1040).worlds[1].fill_slot_data()
    slot["tracker"]["options"]["exclude_trap_types"] = invalid
    with pytest.raises(ValueError, match="exclude_trap_types"):
        validate_tracker_data(slot)


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
    # The added choice defaults to no exclusions in earlier schema-1 slots.
    del slot["tracker"]["options"]["exclude_trap_types"]
    with pytest.raises(ValueError, match="Missing Kirby tracker exclude_trap_types"):
        reconstruct(slot)
    del slot["tracker"]["trap_catalog_version"]
    rebuilt = reconstruct(slot)
    assert not rebuilt.worlds[1].options.exclude_trap_types.value
    assert {item.name for item in rebuilt.itempool if item.trap} > {"Bomb Trap"}


def test_narcolepsy_is_selectable_and_new_tracker_catalog_roundtrips():
    legacy_labels = TRAPS - {NARCOLEPSY_ITEM_NAME}
    options = {"enable_traps": 1, "trap_fill_percentage": 100,
               "exclude_trap_types": sorted(legacy_labels)}
    assert generated(exclusions=options["exclude_trap_types"])[1].keys() == {NARCOLEPSY_ITEM_NAME}
    assert NARCOLEPSY_ITEM_NAME not in generated(exclusions=[NARCOLEPSY_ITEM_NAME])[1]
    mw = setup_multiworld(KirbyAmWorld, options=options, seed=1113)
    slot = json.loads(json.dumps(mw.worlds[1].fill_slot_data()))
    assert slot["tracker"]["trap_catalog_version"] == TRAP_CATALOG_VERSION
    assert {item.name for item in reconstruct(slot).itempool if item.trap} == {NARCOLEPSY_ITEM_NAME}


def test_earlier_tracker_slot_replays_old_catalog_and_rejects_unknown_version():
    options = {"enable_traps": 1, "trap_fill_percentage": 100, "exclude_trap_types": ["Bomb Trap"]}
    mw = setup_multiworld(KirbyAmWorld, options=options, seed=1040)
    slot = mw.worlds[1].fill_slot_data()
    del slot["tracker"]["trap_catalog_version"]
    legacy = reconstruct(slot)
    assert "trap_catalog_version" not in legacy.worlds[1].fill_slot_data()["tracker"]
    assert {item.name for item in legacy.itempool if item.trap} == TRAPS - {NARCOLEPSY_ITEM_NAME, RANDOM_TELEPORT_ITEM_NAME, "Bomb Trap"}
    slot["tracker"]["options"]["exclude_trap_types"] = [NARCOLEPSY_ITEM_NAME]
    with pytest.raises(ValueError, match="without its trap catalog version"):
        validate_tracker_data(slot)
    for invalid in (False, True, 0, 3, "1", None):
        slot["tracker"]["trap_catalog_version"] = invalid
        with pytest.raises(ValueError, match="Unsupported Kirby tracker trap catalog"):
            validate_tracker_data(slot)


def test_random_teleport_is_excludable_and_prior_catalog_stays_versioned():
    options = {"enable_traps": 1, "trap_fill_percentage": 100,
               "exclude_trap_types": sorted(TRAPS - {RANDOM_TELEPORT_ITEM_NAME})}
    assert generated(exclusions=options["exclude_trap_types"])[1].keys() == {RANDOM_TELEPORT_ITEM_NAME}
    assert not generated(enabled=0, exclusions=options["exclude_trap_types"])[1]
    assert RANDOM_TELEPORT_ITEM_NAME not in generated(exclusions=[RANDOM_TELEPORT_ITEM_NAME])[1]
    slot = setup_multiworld(KirbyAmWorld, seed=696, options=options).worlds[1].fill_slot_data()
    assert {item.name for item in reconstruct(slot).itempool if item.trap} == {RANDOM_TELEPORT_ITEM_NAME}
    slot["tracker"]["trap_catalog_version"] = NARCOLEPSY_TRAP_CATALOG_VERSION
    assert not any(item.trap for item in reconstruct(slot).itempool)
