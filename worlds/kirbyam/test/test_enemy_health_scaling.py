from types import SimpleNamespace
from typing import cast

import pytest

from worlds.Files import APProcedurePatch, AutoPatchExtensionRegister

from ..enemy_health_scaling import (
    BOSS_HEALTH_DIFFICULTY_COUNT,
    BOSS_HEALTH_ROW_COUNT,
    BOSS_HEALTH_TABLE_OFFSET,
    DARK_MIND_FORM1_HEALTH_DIFFICULTY_COUNT,
    DARK_MIND_FORM1_HEALTH_TABLE_OFFSET,
    DARK_MIND_FORM1_ROW_COUNT,
    ENEMY_HEALTH_MULTIPLIER_DEFAULT,
    ENEMY_HEALTH_MULTIPLIER_MAX,
    ENEMY_HEALTH_MULTIPLIER_MIN,
    REGULAR_ENEMY_COUNT,
    REGULAR_ENEMY_ENTRY_SIZE,
    REGULAR_ENEMY_HP_OFFSET,
    REGULAR_ENEMY_TABLE_OFFSET,
    scale_enemy_health_tables,
    scale_hp_value,
)
from ..options import EnemyHealthMultiplier, KirbyAmOptions, OPTION_GROUPS
from ..rom import (
    ENEMY_HEALTH_MULTIPLIER_FILE,
    KirbyAmPatchExtension,
    KirbyAmProcedurePatch,
)


def _write_s16(rom: bytearray, offset: int, value: int) -> None:
    rom[offset:offset + 2] = value.to_bytes(2, "little", signed=True)


def _read_s16(rom: bytes, offset: int) -> int:
    return int.from_bytes(rom[offset:offset + 2], "little", signed=True)


def _fixture_rom() -> bytearray:
    # Include one record beyond the regular-enemy range so tests can prove that
    # object type 0x38 metadata is never treated as regular-enemy HP.
    size = REGULAR_ENEMY_TABLE_OFFSET + (REGULAR_ENEMY_COUNT + 1) * REGULAR_ENEMY_ENTRY_SIZE
    return bytearray(size)


@pytest.mark.parametrize(
    ("native_hp", "percent", "expected"),
    [
        (3, 150, 5),
        (7, 150, 11),
        (40, 50, 20),
        (40, 100, 40),
        (40, 200, 80),
        (0, 500, 0),
        (-1, 500, -1),
        (0x7FFF, 500, 0x7FFF),
    ],
)
def test_scale_hp_value(native_hp: int, percent: int, expected: int) -> None:
    assert scale_hp_value(native_hp, percent) == expected


@pytest.mark.parametrize("percent", [ENEMY_HEALTH_MULTIPLIER_MIN - 1, ENEMY_HEALTH_MULTIPLIER_MAX + 1])
def test_scale_hp_value_rejects_out_of_range_multiplier(percent: int) -> None:
    with pytest.raises(ValueError, match="enemy health multiplier"):
        scale_hp_value(10, percent)


def test_scale_enemy_health_tables_scales_each_native_source_and_preserves_boundaries() -> None:
    rom = _fixture_rom()

    boss_last = BOSS_HEALTH_TABLE_OFFSET + (BOSS_HEALTH_ROW_COUNT * BOSS_HEALTH_DIFFICULTY_COUNT - 1) * 2
    dark_mind_last = (
        DARK_MIND_FORM1_HEALTH_TABLE_OFFSET
        + (DARK_MIND_FORM1_ROW_COUNT * DARK_MIND_FORM1_HEALTH_DIFFICULTY_COUNT - 1) * 2
    )
    regular_first = REGULAR_ENEMY_TABLE_OFFSET + REGULAR_ENEMY_HP_OFFSET
    regular_last = (
        REGULAR_ENEMY_TABLE_OFFSET
        + (REGULAR_ENEMY_COUNT - 1) * REGULAR_ENEMY_ENTRY_SIZE
        + REGULAR_ENEMY_HP_OFFSET
    )
    first_non_regular = (
        REGULAR_ENEMY_TABLE_OFFSET
        + REGULAR_ENEMY_COUNT * REGULAR_ENEMY_ENTRY_SIZE
        + REGULAR_ENEMY_HP_OFFSET
    )

    _write_s16(rom, BOSS_HEALTH_TABLE_OFFSET, 40)
    _write_s16(rom, boss_last, 80)
    _write_s16(rom, DARK_MIND_FORM1_HEALTH_TABLE_OFFSET, 32)
    _write_s16(rom, dark_mind_last, 56)
    _write_s16(rom, regular_first, 3)
    _write_s16(rom, regular_last, 7)
    _write_s16(rom, first_non_regular, 1234)

    # Non-HP bytes in a regular metadata record must survive exactly.
    rom[REGULAR_ENEMY_TABLE_OFFSET + 6:REGULAR_ENEMY_TABLE_OFFSET + 10] = b"\xAA\xBB\xCC\xDD"

    scaled = scale_enemy_health_tables(bytes(rom), 150)

    assert _read_s16(scaled, BOSS_HEALTH_TABLE_OFFSET) == 60
    assert _read_s16(scaled, boss_last) == 120
    assert _read_s16(scaled, DARK_MIND_FORM1_HEALTH_TABLE_OFFSET) == 48
    assert _read_s16(scaled, dark_mind_last) == 84
    assert _read_s16(scaled, regular_first) == 5
    assert _read_s16(scaled, regular_last) == 11
    assert _read_s16(scaled, first_non_regular) == 1234
    assert scaled[REGULAR_ENEMY_TABLE_OFFSET + 6:REGULAR_ENEMY_TABLE_OFFSET + 10] == b"\xAA\xBB\xCC\xDD"


def test_scale_enemy_health_tables_preserves_sentinel_values() -> None:
    rom = _fixture_rom()
    _write_s16(rom, BOSS_HEALTH_TABLE_OFFSET, -1)
    _write_s16(rom, DARK_MIND_FORM1_HEALTH_TABLE_OFFSET, 0)
    regular_first = REGULAR_ENEMY_TABLE_OFFSET + REGULAR_ENEMY_HP_OFFSET
    _write_s16(rom, regular_first, -7)

    scaled = scale_enemy_health_tables(bytes(rom), 300)

    assert _read_s16(scaled, BOSS_HEALTH_TABLE_OFFSET) == -1
    assert _read_s16(scaled, DARK_MIND_FORM1_HEALTH_TABLE_OFFSET) == 0
    assert _read_s16(scaled, regular_first) == -7


def test_all_four_boss_difficulty_columns_scale_together() -> None:
    rom = _fixture_rom()
    native = [40, 52, 64, 76]
    for column, hp in enumerate(native):
        _write_s16(rom, BOSS_HEALTH_TABLE_OFFSET + column * 2, hp)

    scaled = scale_enemy_health_tables(bytes(rom), 200)

    assert [
        _read_s16(scaled, BOSS_HEALTH_TABLE_OFFSET + column * 2)
        for column in range(BOSS_HEALTH_DIFFICULTY_COUNT)
    ] == [80, 104, 128, 152]


def test_vanilla_multiplier_is_byte_identical() -> None:
    rom = bytes(_fixture_rom())
    assert scale_enemy_health_tables(rom, ENEMY_HEALTH_MULTIPLIER_DEFAULT) is rom


def test_too_small_rom_is_rejected() -> None:
    with pytest.raises(ValueError, match="ROM is too small"):
        scale_enemy_health_tables(b"\0" * 0x100, 200)


def test_enemy_health_option_contract_and_group() -> None:
    assert EnemyHealthMultiplier.range_start == ENEMY_HEALTH_MULTIPLIER_MIN
    assert EnemyHealthMultiplier.range_end == ENEMY_HEALTH_MULTIPLIER_MAX
    assert EnemyHealthMultiplier.default == ENEMY_HEALTH_MULTIPLIER_DEFAULT
    assert EnemyHealthMultiplier.from_any(250).value == 250
    assert KirbyAmOptions.type_hints["enemy_health_multiplier"] is EnemyHealthMultiplier

    harder_group = next(group for group in OPTION_GROUPS if group.name == "Make the game harder")
    assert EnemyHealthMultiplier in harder_group.options


def test_enemy_health_scaling_procedure_runs_after_base_patch_before_tokens() -> None:
    steps = [step for step, _ in KirbyAmProcedurePatch.procedure]
    assert steps.index("apply_bsdiff4") < steps.index("apply_enemy_health_scaling")
    assert steps.index("apply_enemy_health_scaling") < steps.index("apply_tokens")

    scaling_step = next(args for step, args in KirbyAmProcedurePatch.procedure if step == "apply_enemy_health_scaling")
    assert scaling_step == [ENEMY_HEALTH_MULTIPLIER_FILE]
    assert AutoPatchExtensionRegister.get_handler(KirbyAmProcedurePatch.game) is KirbyAmPatchExtension


def test_patch_extension_reads_seed_multiplier_and_scales_rom() -> None:
    rom = _fixture_rom()
    _write_s16(rom, BOSS_HEALTH_TABLE_OFFSET, 10)
    caller = SimpleNamespace(
        get_file=lambda name: (175).to_bytes(2, "little")
        if name == ENEMY_HEALTH_MULTIPLIER_FILE
        else b""
    )

    scaled = KirbyAmPatchExtension.apply_enemy_health_scaling(
        cast(APProcedurePatch, caller),
        bytes(rom),
        ENEMY_HEALTH_MULTIPLIER_FILE,
    )
    assert _read_s16(scaled, BOSS_HEALTH_TABLE_OFFSET) == 18


def test_patch_extension_rejects_malformed_multiplier_metadata() -> None:
    caller = SimpleNamespace(get_file=lambda _name: b"\x64")

    with pytest.raises(ValueError, match="exactly 2 bytes"):
        KirbyAmPatchExtension.apply_enemy_health_scaling(
            cast(APProcedurePatch, caller),
            bytes(_fixture_rom()),
            ENEMY_HEALTH_MULTIPLIER_FILE,
        )
