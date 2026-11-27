"""Validate canonical pool data and pin its established generation behavior."""
from copy import deepcopy

import pytest

from BaseClasses import ItemClassification
from ..data import data, load_json_data
from ..item_pool_policy import ITEM_POOL_POLICY, parse_item_pool_policy
from ..narcolepsy import NARCOLEPSY_ITEM_NAME
from ..random_teleport import RANDOM_TELEPORT_ITEM_NAME


def test_written_policy_preserves_seeded_picker_and_legacy_trap_order():
    policy = ITEM_POOL_POLICY
    assert policy.filler_for(maximum_health_is_one=False, no_extra_lives=False) == (
        ("1 Up", "Small Food", "Energy Drink", "Hunk of Meat", "Cell Phone Battery",
         "Max Tomato", "Invincibility Candy"),
        (15, 14, 17, 9, 25, 15, 5),
    )
    assert policy.filler_for(maximum_health_is_one=True, no_extra_lives=False)[0] == (
        "1 Up", "Cell Phone Battery", "Invincibility Candy",
    )
    battery = data.item_key_to_id["BATTERY"]
    assert (battery, 25) in policy.weighted_filler
    assert data.items[battery].classification == ItemClassification.useful

    for version in (0, 1, 2):
        withheld = {RANDOM_TELEPORT_ITEM_NAME} if version < 2 else set()
        if version < 1:
            withheld.add(NARCOLEPSY_ITEM_NAME)
        assert policy.traps_for(
            minimum_health_is_one=False, no_extra_lives=False, catalog_version=version, player_excluded_labels=set(),
        ) == tuple(l for l in data.available_trap_item_labels if l not in withheld)
    assert policy.traps_for(
        minimum_health_is_one=True, no_extra_lives=False, catalog_version=2, player_excluded_labels={"Bomb Trap"},
    ) == tuple(l for l in data.available_trap_item_labels if l not in {"Bomb Trap", "Health Down Trap"})


def test_written_policy_binds_each_original_boss_to_exact_shard():
    assert ITEM_POOL_POLICY.vanilla_boss_shards == tuple(
        (f"BOSS_DEFEAT_{n}", 3860001 + n) for n in range(1, 9)
    )


@pytest.mark.parametrize(("mutate", "error"), [
    (lambda p: p["weighted_filler"][0].update(weight=True), "positive integer"),
    (lambda p: p["weighted_filler"].pop(), "every Filler-tagged item exactly once"),
    (lambda p: p["filler_exclusions"]["no_extra_lives"].append("Life Down Trap"), "unknown item key"),
    (lambda p: p["trap_exclusions"]["no_extra_lives"].append("1_UP"), "ineligible"),
    (lambda p: p["trap_catalog_introduced_in"].update(TRAP_NARCOLEPSY=2), "published tracker versions"),
    (lambda p: p["pool_exclusions"].update(area_keys_off={"tag": "Maps"}), "AreaKeys"),
    (lambda p: p["vanilla_boss_shards"][0].update(check="MAJOR_CHEST_MUSTARD_MOUNTAIN"), "boss-defeat check"),
    (lambda p: p["vanilla_boss_shards"][0].update(item="SHARD_2"), "every boss check and shard exactly once"),
    (lambda p: p["vanilla_boss_shards"][0].update(item="MAP_MUSTARD_MOUNTAIN"), "every boss check and shard exactly once"),
])
def test_item_pool_policy_rejects_invalid_catalog_references(mutate, error):
    raw = deepcopy(load_json_data("item_pool_policy.json"))
    mutate(raw)
    with pytest.raises(ValueError, match=error):
        parse_item_pool_policy(raw)
