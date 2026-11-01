"""Default-on Area Keys can be disabled without weakening unrelated gates."""
from collections import Counter
from types import SimpleNamespace

import pytest

from BaseClasses import CollectionState
from Options import DefaultOnToggle
from test.general import setup_multiworld
from .. import KirbyAmWorld
from ..area_keys import AREA_KEY_LABELS, FALLBACK_STARTING_AREA_KEY_LABEL
from ..options import AreaKeys, OPTION_GROUPS


def test_area_keys_option_is_default_on_in_easier_group():
    assert issubclass(AreaKeys, DefaultOnToggle)
    assert AreaKeys.default == 1
    assert AreaKeys.display_name == "Area Keys"
    assert [group.name for group in OPTION_GROUPS if AreaKeys in group.options] == ["Make the game easier"]
    legacy = KirbyAmWorld.__new__(KirbyAmWorld)
    legacy.options = SimpleNamespace()
    assert legacy._area_keys_enabled()


@pytest.mark.parametrize("room_sanity", [0, 1])
@pytest.mark.parametrize("shards", [0, 2])
def test_area_keys_off_rebalances_pool_without_losing_other_progression(room_sanity, shards):
    worlds = [setup_multiworld(KirbyAmWorld, seed=908, options={
        "area_keys": enabled, "room_sanity": room_sanity, "shards": shards,
        "enable_traps": 0,
    }) for enabled in (0, 1)]
    off, on = worlds
    for mw, enabled in zip(worlds, (False, True)):
        world = mw.worlds[1]
        keys = [item for item in mw.itempool if item.name in AREA_KEY_LABELS]
        owned = [item for item in mw.precollected_items[1] if item.name in AREA_KEY_LABELS]
        assert len(keys) + len(owned) == (8 if enabled else 0)
        assert len(mw.itempool) == len(mw.get_unfilled_locations(1))
        slot = world.fill_slot_data()
        assert slot["area_keys"] is enabled
        if not enabled:
            assert slot["starting_area_key_bitfield"] == 0
        assert len([item for item in mw.itempool if item.name.endswith(" - Hub Connection")]) == 15
    assert len(off.itempool) == len(on.itempool)
    off_progression = Counter(item.name for item in off.itempool if item.advancement)
    on_progression = Counter(item.name for item in on.itempool
                             if item.advancement and item.name not in AREA_KEY_LABELS)
    assert off_progression == on_progression


@pytest.mark.parametrize("explicit_key", [False, True])
def test_area_keys_off_skips_fallback_but_preserves_explicit_start_inventory(explicit_key):
    mw = setup_multiworld(KirbyAmWorld, seed=908, options={"area_keys": 0})
    world = mw.worlds[1]
    if explicit_key:
        world.push_precollected(world.create_item(FALLBACK_STARTING_AREA_KEY_LABEL))
    before = list(mw.precollected_items[1])
    # Even a deliberately unavailable start must not synthesize a disabled key.
    for location in mw.get_locations(1):
        location.access_rule = lambda state: False
    world.generate_basic()
    assert mw.precollected_items[1] == before
    assert not any(item.name in AREA_KEY_LABELS for item in mw.itempool)
    assert world.fill_slot_data()["starting_area_key_bitfield"] == 0


def test_area_keys_off_removes_destination_gate_and_keeps_hub_and_dimension_gates():
    mw = setup_multiworld(KirbyAmWorld, seed=908, options={"area_keys": 0, "ability_gating": 0})
    world = mw.worlds[1]
    state = CollectionState(mw)
    overland = mw.get_entrance(
        "REGION_RAINBOW_ROUTE/ROOM_1_13_LOWER -> REGION_CABBAGE_CAVERN/ROOM_3_04", 1)
    assert overland.access_rule(state)
    hub = mw.get_entrance(
        "REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE -> REGION_MOONLIGHT_MANSION/ROOM_2_HUB", 1)
    assert not hub.access_rule(state)
    state.collect(world.create_item("Moonlight Mansion - Hub Connection"), True)
    assert hub.access_rule(state)
    lever = mw.get_entrance(
        "REGION_MOONLIGHT_MANSION/ROOM_2_11 -> REGION_MOONLIGHT_MANSION/ROOM_2_11_AFTER_LEVER", 1)
    assert not lever.access_rule(state)
    state.collect(world.create_item("Moonlight Mansion 2-11 - Lever Wall"), True)
    assert lever.access_rule(state)
    dimension = mw.get_entrance("REGION_RAINBOW_ROUTE/MAIN -> REGION_DIMENSION_MIRROR/MAIN", 1)
    assert not dimension.access_rule(state)
    for item in mw.itempool:
        if "Mirror Shard" in item.name:
            state.collect(item, True)
    assert dimension.access_rule(state)


@pytest.mark.parametrize("goal", [0, 1, 2])
def test_disabled_area_keys_generate_complete_archives(tmp_path, goal):
    from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive

    player = tmp_path / "player.yaml"
    player.write_text(
        "name: No Area Keys\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n"
        f"  area_keys: false\n  goal: {goal}\n  shards: 2\n  room_sanity: {goal % 2}\n",
        encoding="utf-8",
    )
    archive = generate_archive_from_fixture(player, tmp_path / "output", seed=908 + goal)
    decoded = load_multidata_from_archive(archive)
    assert decoded["slot_data"][1]["area_keys"] is False
    assert decoded["slot_data"][1]["starting_area_key_bitfield"] == 0
    assert not any(3860041 <= item[0] <= 3860048 for item in decoded["locations"][1].values())
