"""All statue slots/targets and procedure integration; no retail ROM required."""
import random
import struct

import pytest

from ..ability_randomization import build_enemy_copy_ability_policy
from ..enemy_ability_data import ABILITY_NAME_TO_ID, VALID_ENEMY_COPY_ABILITIES
from ..enemy_ability_runtime_patch import build_enemy_copy_runtime_patch_writes
from ..statue_art import (
    ANIM_INFO_OFFSET, ANIM_POINTER_OFFSET, CUSTOM_STATUE_ABILITIES,
    GRANT_TABLE_OFFSET, NATIVE_ANIM_TABLE_OFFSET, NATIVE_SCRIPT_OFFSET,
    NATIVE_STATUE_ABILITIES, NATIVE_VARIANTS, ROM_BASE, STATUE_VISUAL_MODE_FILE,
    TILES_BASE, apply_statue_visuals, encode_statue_tiles, load_statue_pixels,
)
from ..rom import KirbyAmPatchExtension, KirbyAmProcedurePatch, write_tokens
from .test_rom_tokens import _DummyPatch, _make_world


def native_fixture() -> bytes:
    rom = bytearray(0x1010000)
    struct.pack_into('<6I', rom, 0x3B909C, 0x08448574, 0x084789C4, 0x084BA240,
                     0x084BB0EC, ROM_BASE + TILES_BASE, 0x08869B6C)
    struct.pack_into('<I', rom, ANIM_POINTER_OFFSET, ROM_BASE + NATIVE_ANIM_TABLE_OFFSET)
    for i in range(31):
        struct.pack_into('<I', rom, NATIVE_ANIM_TABLE_OFFSET + i * 4,
                         ROM_BASE + NATIVE_SCRIPT_OFFSET + i * 36)
    struct.pack_into('<9i', rom, NATIVE_SCRIPT_OFFSET + 11 * 36,
                     -2, 429, 16, -1, 103349, 4, 1, 11, -4)
    struct.pack_into('<HHHHhh', rom, 0x476564 + 11 * 12, 44, 1, 16, 16, 8, 8)
    for i, (name, variant) in enumerate(zip(NATIVE_STATUE_ABILITIES, NATIVE_VARIANTS)):
        rom[GRANT_TABLE_OFFSET + i] = ABILITY_NAME_TO_ID[name]
        struct.pack_into('<HBB', rom, ANIM_INFO_OFFSET + i * 4, 0x384, variant, 0)
    # Sentinel covers Master Sword AnimInfo and data immediately after grants.
    rom[ANIM_INFO_OFFSET + 76:ANIM_INFO_OFFSET + 80] = b'\xc3\x02\x04\x00'
    rom[GRANT_TABLE_OFFSET + 19:GRANT_TABLE_OFFSET + 23] = b'MSTR'
    return bytes(rom)


@pytest.mark.parametrize('ability', VALID_ENEMY_COPY_ABILITIES)
@pytest.mark.parametrize('mode', [1, 2])
def test_every_slot_and_ability(mode: int, ability: str) -> None:
    original = bytearray(native_fixture())
    original[GRANT_TABLE_OFFSET:GRANT_TABLE_OFFSET + 19] = bytes([ABILITY_NAME_TO_ID[ability]]) * 19
    rom = apply_statue_visuals(bytes(original), mode)
    table = struct.unpack_from('<I', rom, ANIM_POINTER_OFFSET)[0] - ROM_BASE
    assert rom[table:table + 124] == original[NATIVE_ANIM_TABLE_OFFSET:NATIVE_ANIM_TABLE_OFFSET + 124]
    expected = (37 if mode == 2 else
                dict(zip(NATIVE_STATUE_ABILITIES, NATIVE_VARIANTS)).get(
                    ability, 31 + CUSTOM_STATUE_ABILITIES.index(ability)
                    if ability in CUSTOM_STATUE_ABILITIES else -1))
    for i in range(19):
        assert struct.unpack_from('<HBB', rom, ANIM_INFO_OFFSET + i * 4) == (0x384, expected, 0)
    # Nothing else in the original image, including grants, Master Sword,
    # payload, gating, runtime masks, or any non-statue art, may change.
    restored = bytearray(rom[:len(original)])
    restored[ANIM_POINTER_OFFSET:ANIM_POINTER_OFFSET + 4] = original[ANIM_POINTER_OFFSET:ANIM_POINTER_OFFSET + 4]
    restored[ANIM_INFO_OFFSET:ANIM_INFO_OFFSET + 76] = original[ANIM_INFO_OFFSET:ANIM_INFO_OFFSET + 76]
    assert restored == original
    pixels = load_statue_pixels()
    for i, name in enumerate(CUSTOM_STATUE_ABILITIES):
        script = struct.unpack_from('<I', rom, table + (31 + i) * 4)[0] - ROM_BASE
        commands = struct.unpack_from('<9i', rom, script)
        assert commands[:4] == (-2, 429, 16, -1)
        assert commands[5:] == (4, 1, 11, -4)
        tile = TILES_BASE + commands[4] * 32
        assert tile >= len(original)
        assert rom[tile:tile + 128] == encode_statue_tiles(pixels[name])


@pytest.mark.parametrize('mode', [0, 1, 2])
@pytest.mark.parametrize('enabled', [False, True])
def test_generation_procedure_mode_matrix(mode: int, enabled: bool) -> None:
    world = _make_world(mode, randomize_statues=enabled)
    world._enemy_copy_ability_policy = build_enemy_copy_ability_policy(
        random.Random(824), mode, include_boss_spawns=True, include_minibosses=True)
    patch = _DummyPatch()
    write_tokens(world, patch)  # type: ignore[arg-type]
    assert patch.files[STATUE_VISUAL_MODE_FILE] == bytes([mode if enabled else 0])
    original = bytearray(native_fixture())
    for _, offset, data in patch.token_writes:
        original[offset:offset + len(data)] = data
    result = KirbyAmPatchExtension.apply_statue_art(
        type('Files', (), {'get_file': lambda self, name: patch.files[name]})(),  # type: ignore[arg-type]
        bytes(original), STATUE_VISUAL_MODE_FILE)
    assert (result == original) == (not enabled or mode == 0)
    steps = [name for name, _ in KirbyAmProcedurePatch.procedure]
    assert steps.index('apply_tokens') < steps.index('apply_statue_art') < steps.index('finalize_health_header')


@pytest.mark.parametrize('mode', [1, 2])
def test_real_assignment_matches_grants(mode: int) -> None:
    policy = build_enemy_copy_ability_policy(
        random.Random(824), mode, include_boss_spawns=True, include_minibosses=True)
    writes = build_enemy_copy_runtime_patch_writes(policy, include_statues=True)
    original = bytearray(native_fixture())
    for offset, value in writes.items():
        original[offset] = value
    result = apply_statue_visuals(bytes(original), mode)
    expected = {ABILITY_NAME_TO_ID[name]: variant
                for name, variant in zip(NATIVE_STATUE_ABILITIES, NATIVE_VARIANTS)}
    expected.update({ABILITY_NAME_TO_ID[name]: 31 + i
                     for i, name in enumerate(CUSTOM_STATUE_ABILITIES[:-1])})
    for i in range(19):
        assert result[ANIM_INFO_OFFSET + i * 4 + 2] == (37 if mode == 2 else expected[writes[GRANT_TABLE_OFFSET + i]])


@pytest.mark.parametrize('offset', [
    ANIM_INFO_OFFSET, ANIM_POINTER_OFFSET, NATIVE_ANIM_TABLE_OFFSET,
    GRANT_TABLE_OFFSET, 0x3B909C, 0x476564 + 11 * 12,
    NATIVE_SCRIPT_OFFSET + 11 * 36,
])
def test_reject_changed_native_contract(offset: int) -> None:
    rom = bytearray(native_fixture())
    rom[offset] = 255
    with pytest.raises(ValueError):
        apply_statue_visuals(bytes(rom), 1)


def test_reject_repatch_and_bad_modes() -> None:
    rom = native_fixture()
    assert apply_statue_visuals(rom, 0) is rom
    with pytest.raises(ValueError):
        apply_statue_visuals(apply_statue_visuals(rom, 1), 1)
    with pytest.raises(ValueError):
        apply_statue_visuals(rom, 3)
    with pytest.raises(ValueError):
        apply_statue_visuals(b'', 1)


def test_pixel_encoding_roundtrip_and_distinct_art() -> None:
    sprites = load_statue_pixels()
    assert len(set(encode_statue_tiles(rows) for rows in sprites.values())) == 7
    for rows in sprites.values():
        tiles = encode_statue_tiles(rows)
        assert len(tiles) == 128
        for y in range(16):
            for x in range(16):
                byte = tiles[(y // 8 * 2 + x // 8) * 32 + y % 8 * 4 + x % 8 // 2]
                assert (byte >> (x % 2 * 4)) & 15 == int(rows[y][x].replace('.', '0'), 16)


def test_native_metadata_matches_independent_retail_table_order() -> None:
    assert NATIVE_STATUE_ABILITIES == (
        'Beam', 'Burning', 'Laser', 'Fire', 'Stone', 'Fighter', 'Bomb', 'Tornado',
        'Wheel', 'Ice', 'Spark', 'Missile', 'Smash', 'Throw', 'Hammer', 'Parasol',
        'Sword', 'Cutter', 'Cupid')
    assert NATIVE_VARIANTS == (*range(11, 26), 29, 26, 27, 28)


@pytest.mark.parametrize('mutation', ['missing', 'gba_pointer', 'duplicate', 'bad_variant', 'bad_info'])
def test_native_metadata_validation(mutation: str) -> None:
    import json
    import pkgutil
    from ..statue_art import parse_native_statues
    raw = pkgutil.get_data('worlds.kirbyam', 'data/abilities.json')
    assert raw is not None
    data = json.loads(raw)
    beam = data['Beam']['native_regular_statue']
    if mutation == 'missing':
        del data['Cook']['native_regular_statue']
    elif mutation == 'gba_pointer':
        beam['grant_rom_offset'] = '0x083538FC'
    elif mutation == 'duplicate':
        data['Cook']['native_regular_statue'] = beam.copy()
    elif mutation == 'bad_variant':
        beam['animation_variant'] = 30
    else:
        beam['animation_info_rom_offset'] = '0x3536E8'  # Master Sword
    with pytest.raises(ValueError):
        parse_native_statues(data)
