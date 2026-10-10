"""Health option, pool, and client contracts for issue #778."""

from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from ..client import KirbyAmClient
from ..health import HealthRange, reconcile_health, resolve_health_range
from ..options import KirbyAmOptions, MaximumHealth, MinimumHealth, OneHitMode, OPTION_GROUPS, RandomizeShards
from .test_item_pool import _build_world_for_create_items, _vitality_item_codes


VALID_RANGES = [
    (minimum, maximum)
    for minimum in range(1, 11)
    for maximum in range(minimum, 11)
]


def test_health_option_defaults_and_registration() -> None:
    assert (MinimumHealth.default, MaximumHealth.default) == (6, 10)
    assert resolve_health_range() == HealthRange(6, 10)
    for name, option in (("minimum_health", MinimumHealth), ("maximum_health", MaximumHealth)):
        assert KirbyAmOptions.type_hints[name] is option
        assert option.range_start == 1
        assert option.range_end == 10
        assert option.from_any(1).value == 1
        assert option.from_any(10).value == 10
        assert any(option in group.options for group in OPTION_GROUPS)
        for invalid in (0, 11):
            with pytest.raises(Exception):
                option.from_any(invalid)


@pytest.mark.parametrize("minimum,maximum", VALID_RANGES)
def test_all_supported_health_ranges(minimum: int, maximum: int) -> None:
    resolved = resolve_health_range(minimum, maximum)
    assert resolved.minimum == minimum
    assert resolved.maximum == maximum
    assert resolved.vitality_count == maximum - minimum


@pytest.mark.parametrize("minimum,maximum,message", [
    (0, 4, "within 1..10"), (7, 11, "within 1..10"),
    (8, 7, "at least minimum_health"),
    ("6", 10, "whole numbers"), (True, 4, "whole numbers"),
])
def test_invalid_health_ranges_are_rejected(minimum, maximum, message) -> None:
    with pytest.raises(ValueError, match=message):
        resolve_health_range(minimum, maximum)


@pytest.mark.parametrize("mode,expected", [(1, HealthRange(1, 1)), (2, HealthRange(1, 5))])
def test_legacy_one_hit_overrides_custom_pair(mode, expected) -> None:
    assert resolve_health_range(10, 1, mode) == expected


@pytest.mark.parametrize("shards", [RandomizeShards.option_vanilla, RandomizeShards.option_completely_random])
@pytest.mark.parametrize("minimum,maximum", VALID_RANGES)
def test_custom_health_pool_contains_exact_unique_counter_prefix(shards, minimum, maximum) -> None:
    world, locations = _build_world_for_create_items(shards, enable_traps=1)
    world.options.minimum_health = SimpleNamespace(value=minimum)
    world.options.maximum_health = SimpleNamespace(value=maximum)
    world.create_items()

    all_counter_codes = _vitality_item_codes()
    expected = Counter({code: 1 for code in sorted(all_counter_codes)[:maximum - minimum]})
    actual = Counter(item.code for item in world.multiworld.itempool if item.code in all_counter_codes)
    assert actual == expected
    assert len(world.multiworld.itempool) == sum(location.item is None for location in locations)
    assert len(all_counter_codes) == 9  # Each upgrade has a unique identity.


@pytest.mark.parametrize("mode,count", [
    (OneHitMode.option_exclude_vitality_counters, 0),
    (OneHitMode.option_include_vitality_counters, 4),
])
def test_one_hit_pool_ignores_custom_pair(mode, count) -> None:
    world, _ = _build_world_for_create_items(RandomizeShards.option_completely_random, one_hit_mode=mode)
    world.options.minimum_health = SimpleNamespace(value=10)
    world.options.maximum_health = SimpleNamespace(value=1)
    world.create_items()
    assert sum(item.code in _vitality_item_codes() for item in world.multiworld.itempool) == count


def test_custom_one_hp_filters_healing_and_health_traps() -> None:
    world, _ = _build_world_for_create_items(RandomizeShards.option_completely_random)
    world.options.minimum_health = SimpleNamespace(value=1)
    world.options.maximum_health = SimpleNamespace(value=1)
    assert not {"Small Food", "Energy Drink", "Hunk of Meat", "Max Tomato"}.intersection(world._active_filler_pool())
    assert "Health Down Trap" not in world._active_trap_pool()
    world.options.minimum_health.value = 6
    world.options.maximum_health.value = 6
    assert "Small Food" in world._active_filler_pool()
    assert "Health Down Trap" in world._active_trap_pool()


@pytest.mark.parametrize("minimum,maximum,vitality,hp,max_hp,expected", [
    (3, 5, 0, 6, 6, (0, 3, 3)),  # Start lower.
    (8, 10, 0, 6, 6, (0, 8, 8)),  # Start higher / native full-health respawn.
    (8, 10, 0, 4, 6, (0, 6, 8)),  # Preserve two points of damage when raising cap.
    (8, 10, 0, 6, 8, (0, 6, 8)),  # Repeated polls cannot heal.
    (8, 10, 1, 7, 7, (1, 9, 9)),  # Native vitality full heal uses a six-HP base.
    (3, 5, 1, 7, 7, (1, 4, 4)),
    (3, 5, 99, 10, 10, (2, 5, 5)),  # Clamp leaked/native excess counters.
    (1, 1, 4, 1, 1, (0, 1, 1)),
    (8, 10, 0, 0, 6, (0, 0, 8)),  # Do not revive.
    (8, 10, 0, -1, 6, (0, -1, 8)),
    (8, 10, 0, -128, 6, (0, -128, 8)),
    (8, 10, 0, 4, 0, (0, 4, 8)),  # Invalid native capacity is not an excuse to heal.
])
def test_health_reconciliation(minimum, maximum, vitality, hp, max_hp, expected) -> None:
    assert reconcile_health(resolve_health_range(minimum, maximum), vitality, hp, max_hp) == expected


@pytest.mark.asyncio
async def test_client_guards_health_snapshot_and_retries_changed_state(mock_bizhawk_context) -> None:
    client = KirbyAmClient()
    client.initialize_client()
    mock_bizhawk_context.slot_data.update(minimum_health=8, maximum_health=10)
    initial = [b"\0\0", b"\x06", b"\x06"]
    dead = [b"\0\0", b"\0", b"\x06"]
    with patch("worlds.kirbyam.client.bizhawk.read", AsyncMock(side_effect=[initial, dead])), \
         patch("worlds.kirbyam.client.bizhawk.guarded_write", AsyncMock(side_effect=[False, True])) as write:
        await client._enforce_health_range(mock_bizhawk_context)
        await client._enforce_health_range(mock_bizhawk_context)
    first = write.await_args_list[0]
    assert first.args[1] == [(0x02020FE1, b"\x08", "System Bus"), (0x02020FE0, b"\x08", "System Bus")]
    assert first.args[2] == [
        (0x02038980, initial[0], "System Bus"),
        (0x02020FE0, initial[1], "System Bus"),
        (0x02020FE1, initial[2], "System Bus"),
    ]
    assert write.await_args_list[1].args[1] == [(0x02020FE1, b"\x08", "System Bus")]


@pytest.mark.asyncio
@pytest.mark.parametrize("slot_data", [
    {}, {"minimum_health": 6, "maximum_health": 10},
    {"minimum_health": 1, "maximum_health": 10},
    {"minimum_health": None, "maximum_health": 10},
])
async def test_client_does_not_touch_default_legacy_or_invalid_ranges(mock_bizhawk_context, slot_data) -> None:
    client = KirbyAmClient()
    client.initialize_client()
    mock_bizhawk_context.slot_data = slot_data
    with patch("worlds.kirbyam.client.bizhawk.read", AsyncMock()) as read, \
         patch("worlds.kirbyam.client.bizhawk.guarded_write", AsyncMock()) as write:
        await client._enforce_health_range(mock_bizhawk_context)
    read.assert_not_awaited()
    write.assert_not_awaited()


@pytest.mark.parametrize("minimum,maximum,mode", [
    (minimum, maximum, "off") for minimum, maximum in VALID_RANGES
] + [(10, 1, "include_vitality_counters"), (10, 1, "exclude_vitality_counters")])
def test_custom_health_yaml_generates_patch_and_slot_data(tmp_path: Path, minimum, maximum, mode) -> None:
    import zipfile
    from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive

    player_file = tmp_path / "health.yaml"
    player_file.write_text(
        "name: Health Test\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n"
        f"  minimum_health: {minimum}\n  maximum_health: {maximum}\n  one_hit_mode: {mode}\n",
        encoding="utf-8",
    )
    archive = generate_archive_from_fixture(player_file, tmp_path / "output", seed=778)
    decoded = load_multidata_from_archive(archive)
    slot_data = decoded["slot_data"][1]
    assert slot_data["minimum_health"] == minimum
    assert slot_data["maximum_health"] == maximum
    expected_mode = {"off": 0, "exclude_vitality_counters": 1, "include_vitality_counters": 2}[mode]
    assert slot_data["one_hit_mode"] == expected_mode
    expected_count = resolve_health_range(minimum, maximum, expected_mode).vitality_count
    item_codes = [item[0] for item in decoded["locations"][1].values()]
    assert sum(code in _vitality_item_codes() for code in item_codes) == expected_count
    with zipfile.ZipFile(archive) as generated:
        assert any(name.endswith(".apkirbyam") for name in generated.namelist())


@pytest.mark.parametrize("minimum,maximum", [(8, 3)])
def test_invalid_health_pair_fails_early_before_generation(minimum: int, maximum: int) -> None:
    world, _ = _build_world_for_create_items(RandomizeShards.option_completely_random)
    world.options.minimum_health = SimpleNamespace(value=minimum)
    world.options.maximum_health = SimpleNamespace(value=maximum)
    with pytest.raises(ValueError, match="maximum_health"):
        world.generate_early()
    assert world.multiworld.itempool == []
