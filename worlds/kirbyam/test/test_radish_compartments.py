"""Directed compartment contracts; no claim of emulator acceptance."""
import struct

import pytest

from ..data import data
from ..tools.verify_radish_compartments import component, decompress_rl, incoming_start, verify

PREFIX = 'REGION_RADISH_RUINS/ROOM_'


def test_radish_chest_is_only_in_lower_room_seven_compartment():
    key = 'MINOR_CHEST_RADISH_RUINS_8_07_OBJECT_01'
    lower = PREFIX + '8_07__LOGIC__ENTRY_FROM_8_04'
    upper = PREFIX + '8_07__LOGIC__ENTRY_FROM_8_09'
    assert data.locations[key].parent_region == lower
    assert [r.name for r in data.regions.values() if key in r.locations] == [lower]
    assert data.regions[lower].exits == [PREFIX + '8_04', PREFIX + '8_07__ROOM_CHECK']
    assert data.regions[upper].exits == [PREFIX + '8_08', PREFIX + '8_07__ROOM_CHECK']
    assert not data.regions[PREFIX + '8_07__ROOM_CHECK'].exits
    assert data.regions[PREFIX + '8_04'].exits.count(lower) == 1


def test_radish_phantom_shortcuts_are_absent():
    for source in ('8_18', '8_21', '8_23', '8_GOAL_1', '8_03'):
        assert all(not destination.startswith(PREFIX + '8_07') for destination in data.regions[PREFIX + source].exits)
    # The chest corridor is not reachable from the upper corridor through its room check.
    upper = PREFIX + '8_07__LOGIC__ENTRY_FROM_8_09'
    assert PREFIX + '8_07__LOGIC__ENTRY_FROM_8_04' not in data.regions[upper].exits


def test_overapproximation_does_not_cross_solid_boundary():
    grid = bytes([0, 255, 0, 13, 13, 13, 0, 29, 0])
    assert component(grid, 3, (0, 0)) == {(0, 0), (1, 0), (2, 0)}
    assert component(grid, 3, (0, 2)) == {(0, 2), (1, 2), (2, 2)}
    with pytest.raises(ValueError):
        component(grid, 3, (0, 1))


def test_rl_decoder_accepts_runs_and_literals_and_rejects_overrun():
    assert decompress_rl(struct.pack('<I', (5 << 8) | 0x30) + bytes([0x80, 13, 1, 0, 255]), 0, 5) == bytes([13, 13, 13, 0, 255])
    with pytest.raises(ValueError, match='overrun'):
        decompress_rl(struct.pack('<I', (2 << 8) | 0x30) + bytes([0x80, 13]), 0, 2)
    with pytest.raises(ValueError):
        verify(b'not a ROM')


@pytest.mark.parametrize('spawn,expected', [((4, 12), (3, 11)), ((3, 3), (2, 2)),
                                          ((4, 6), (3, 5)), ((78, 9), (77, 8))])
def test_incoming_native_record_conversion(spawn, expected):
    from .test_room_evidence import fixture_rom
    rom = fixture_rom()  # Synthetic decoder fixture, not captured ROM bytes.
    struct.pack_into('<HBB', rom, 0x408, 623, *spawn)
    assert incoming_start(rom, 0, 0x400, 623, spawn) == expected


@pytest.mark.parametrize('destination,spawn,message', [
    (624, (4, 12), 'destination'),
    (623, (5, 12), 'spawn'),
    (623, (4, 13), 'spawn'),
])
def test_incoming_rejects_changed_native_record(destination, spawn, message):
    from .test_room_evidence import fixture_rom
    rom = fixture_rom()
    struct.pack_into('<HBB', rom, 0x408, destination, *spawn)
    with pytest.raises(ValueError, match=message):
        incoming_start(rom, 0, 0x400, 623, (4, 12))


def test_incoming_rejects_record_outside_source_transition_list():
    from .test_room_evidence import fixture_rom
    with pytest.raises(ValueError, match='Missing incoming transition'):
        incoming_start(fixture_rom(), 0, 0x500, 623, (4, 12))
