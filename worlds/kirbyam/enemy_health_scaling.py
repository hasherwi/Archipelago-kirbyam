"""Generation-time enemy-health scaling for Kirby & The Amazing Mirror.

The retail game sources enemy HP from three ROM tables and calculates the
enemy-meter fill using three fixed-point conversion tables. Scaling both sets
keeps game behavior and the visible meter on the same per-seed scale without
patching live Object2::unk80 values or adding runtime hooks.

Offsets below are file offsets for the supported North American ROM and match
the KatAM decomp symbols:

* gUnk_08351530 @ 0x351530: 27 miniboss/boss rows x 4 difficulty columns.
* gUnk_08351608 @ 0x351608: 4 Dark Mind form-1 rows x 4 difficulty columns.
* gUnk_08351648 @ 0x351648: Object2 metadata; regular-enemy HP is +0x04 in
  each 0x18-byte record. Only object types 0x00..0x37 are regular enemies;
  0x38 begins the native miniboss/boss range and uses the dedicated table.
* gUnk_083513E8 @ 0x3513E8: regular-enemy meter coefficients, one per type.
* gUnk_08351458 @ 0x351458: miniboss/boss meter coefficients, 27 rows x 4
  human-player difficulty columns.
* gUnk_08351628 @ 0x351628: Dark Mind form-1 meter coefficients, 4 rows x 4
  human-player difficulty columns.

All health values are native signed 16-bit little-endian integers. Zero and
negative values are treated as non-health/sentinel data and are left untouched.
"""

ENEMY_HEALTH_MULTIPLIER_MIN = 50
ENEMY_HEALTH_MULTIPLIER_MAX = 500
ENEMY_HEALTH_MULTIPLIER_DEFAULT = 100

BOSS_HEALTH_TABLE_OFFSET = 0x00351530
BOSS_HEALTH_ROW_COUNT = 27
BOSS_HEALTH_DIFFICULTY_COUNT = 4

DARK_MIND_FORM1_HEALTH_TABLE_OFFSET = 0x00351608
DARK_MIND_FORM1_ROW_COUNT = 4
DARK_MIND_FORM1_HEALTH_DIFFICULTY_COUNT = 4

REGULAR_ENEMY_TABLE_OFFSET = 0x00351648
REGULAR_ENEMY_ENTRY_SIZE = 0x18
REGULAR_ENEMY_HP_OFFSET = 0x04
REGULAR_ENEMY_COUNT = 0x38

_S16_SIZE = 2
_MAX_SIGNED_16 = 0x7FFF
_MAX_UNSIGNED_16 = 0xFFFF

REGULAR_ENEMY_METER_TABLE_OFFSET = 0x003513E8
REGULAR_ENEMY_METER_ENTRY_COUNT = 0x38

BOSS_METER_TABLE_OFFSET = 0x00351458
BOSS_METER_ROW_COUNT = 27
BOSS_METER_DIFFICULTY_COUNT = 4

DARK_MIND_FORM1_METER_TABLE_OFFSET = 0x00351628
DARK_MIND_FORM1_METER_ROW_COUNT = 4
DARK_MIND_FORM1_METER_DIFFICULTY_COUNT = 4


def scale_hp_value(vanilla_hp: int, percent: int) -> int:
    """Scale one positive native HP value using deterministic half-up rounding.

    Non-positive inputs are sentinel/non-health values and pass through exactly.
    The result is clamped to signed-16-bit range because Object2 health and the
    source tables use signed 16-bit storage in the native game.
    """
    if not ENEMY_HEALTH_MULTIPLIER_MIN <= percent <= ENEMY_HEALTH_MULTIPLIER_MAX:
        raise ValueError(
            "enemy health multiplier must be within "
            f"{ENEMY_HEALTH_MULTIPLIER_MIN}..{ENEMY_HEALTH_MULTIPLIER_MAX}: {percent}"
        )
    if vanilla_hp <= 0:
        return vanilla_hp

    scaled = (vanilla_hp * percent + 50) // 100
    return min(_MAX_SIGNED_16, max(1, scaled))


def _read_s16(rom: bytes | bytearray, offset: int) -> int:
    return int.from_bytes(rom[offset:offset + _S16_SIZE], "little", signed=True)


def _write_s16(rom: bytearray, offset: int, value: int) -> None:
    rom[offset:offset + _S16_SIZE] = value.to_bytes(_S16_SIZE, "little", signed=True)


def _read_u16(rom: bytes | bytearray, offset: int) -> int:
    return int.from_bytes(rom[offset:offset + _S16_SIZE], "little")


def _write_u16(rom: bytearray, offset: int, value: int) -> None:
    rom[offset:offset + _S16_SIZE] = value.to_bytes(_S16_SIZE, "little")


def _scale_s16_table(rom: bytearray, offset: int, entry_count: int, percent: int) -> None:
    for index in range(entry_count):
        entry_offset = offset + index * _S16_SIZE
        native_hp = _read_s16(rom, entry_offset)
        scaled_hp = scale_hp_value(native_hp, percent)
        if scaled_hp != native_hp:
            _write_s16(rom, entry_offset, scaled_hp)


def _scale_meter_coefficients(rom: bytearray, offset: int, entry_count: int, percent: int) -> None:
    """Adjust Q8.8 meter coefficients by the inverse of the HP multiplier.

    sub_08034E14 computes the fill as ceil(current_hp * coefficient / 256).
    When HP is multiplied by *percent*, divide the coefficient by the same
    ratio so the meter continues to represent the fraction of maximum HP.
    Keep nonzero coefficients nonzero so a low-precision entry still responds
    to damage after rounding.
    """
    for index in range(entry_count):
        entry_offset = offset + index * _S16_SIZE
        native_coefficient = _read_u16(rom, entry_offset)
        if native_coefficient == 0:
            continue

        scaled = (native_coefficient * 100 + percent // 2) // percent
        scaled = min(_MAX_UNSIGNED_16, max(1, scaled))
        if scaled != native_coefficient:
            _write_u16(rom, entry_offset, scaled)


def _required_rom_size() -> int:
    last_regular_hp = (
        REGULAR_ENEMY_TABLE_OFFSET
        + (REGULAR_ENEMY_COUNT - 1) * REGULAR_ENEMY_ENTRY_SIZE
        + REGULAR_ENEMY_HP_OFFSET
    )
    return last_regular_hp + _S16_SIZE


def scale_enemy_health_tables(rom: bytes, percent: int) -> bytes:
    """Return *rom* with enemy HP and health-meter coefficients scaled.

    This runs after KirbyAM's shared bsdiff base patch is applied. It therefore
    scales the actual bytes used by the generated ROM and avoids duplicating
    copyrighted vanilla HP tables inside the world package.
    """
    # Validate even for the no-op case so malformed patch metadata never passes
    # silently simply because it happened to encode the default.
    scale_hp_value(1, percent)

    required_size = _required_rom_size()
    if len(rom) < required_size:
        raise ValueError(
            f"ROM is too small for KirbyAM enemy-health tables: "
            f"{len(rom):#x} < {required_size:#x}"
        )
    if percent == ENEMY_HEALTH_MULTIPLIER_DEFAULT:
        return rom

    scaled_rom = bytearray(rom)

    # ObjType38To52 uses this table for all minibosses/bosses except Dark Mind
    # form 1, which uses its own subtype-indexed table immediately below.
    _scale_s16_table(
        scaled_rom,
        BOSS_HEALTH_TABLE_OFFSET,
        BOSS_HEALTH_ROW_COUNT * BOSS_HEALTH_DIFFICULTY_COUNT,
        percent,
    )
    _scale_s16_table(
        scaled_rom,
        DARK_MIND_FORM1_HEALTH_TABLE_OFFSET,
        DARK_MIND_FORM1_ROW_COUNT * DARK_MIND_FORM1_HEALTH_DIFFICULTY_COUNT,
        percent,
    )

    # Object types 0x00..0x37 are regular enemies. At 0x38 the game switches
    # to the boss table above, so never interpret later Object2 metadata fields
    # as regular-enemy HP.
    for object_type in range(REGULAR_ENEMY_COUNT):
        hp_offset = (
            REGULAR_ENEMY_TABLE_OFFSET
            + object_type * REGULAR_ENEMY_ENTRY_SIZE
            + REGULAR_ENEMY_HP_OFFSET
        )
        native_hp = _read_s16(scaled_rom, hp_offset)
        scaled_hp = scale_hp_value(native_hp, percent)
        if scaled_hp != native_hp:
            _write_s16(scaled_rom, hp_offset, scaled_hp)

    # The native HUD routine sub_08034E14 converts current HP into a percentage
    # using these tables. Scale the coefficients inversely so the meter tracks
    # the scaled maximum HP instead of reaching empty at vanilla HP.
    _scale_meter_coefficients(
        scaled_rom,
        REGULAR_ENEMY_METER_TABLE_OFFSET,
        REGULAR_ENEMY_METER_ENTRY_COUNT,
        percent,
    )
    _scale_meter_coefficients(
        scaled_rom,
        BOSS_METER_TABLE_OFFSET,
        BOSS_METER_ROW_COUNT * BOSS_METER_DIFFICULTY_COUNT,
        percent,
    )
    _scale_meter_coefficients(
        scaled_rom,
        DARK_MIND_FORM1_METER_TABLE_OFFSET,
        DARK_MIND_FORM1_METER_ROW_COUNT * DARK_MIND_FORM1_METER_DIFFICULTY_COUNT,
        percent,
    )

    return bytes(scaled_rom)
