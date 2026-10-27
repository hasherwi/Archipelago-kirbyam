"""Synthetic native evidence tests; no commercial ROM fixture."""
import struct
import pytest
from ..tools import trace_hub_objects as evidence


def fixture():
    rom = bytearray(evidence.COLLISION_ATTRIBUTES + 1024)
    struct.pack_into('<4BH', rom, 32, 1, 0, 12, 3, 18)
    rom[48] = 255
    struct.pack_into('<4BH2xHBBB', rom, 50, 3, 255, 12, 3, 14, 801, 8, 12, 1)
    struct.pack_into('<I', rom, evidence.COLLISION_ATTRIBUTES + 1020, 0x4000)
    return rom


def test_state_selection():
    rom = fixture()
    result = evidence.trace_state(rom, evidence.records(rom, 32), 12, 3, 0)
    assert (result['closed_record'], result['open_record']) == (32, 50)
    assert (result['destination_room'], result['spawn_tiles']) == (801, [8, 12])
    assert result['zero_unlock'] == 'closed; no mutation'


@pytest.mark.parametrize('x,y,attribute', [(3, 12, 0), (12, 3, 1), (12, 4, 0)])
def test_wrong_lookup(x, y, attribute):
    rom = fixture()
    with pytest.raises(ValueError, match='Missing or ambiguous'):
        evidence.trace_state(rom, evidence.records(rom, 32), x, y, attribute)


def test_duplicate_lookup():
    rom = fixture()
    entries = evidence.records(rom, 32)
    with pytest.raises(ValueError, match='ambiguous'):
        evidence.trace_state(rom, entries + entries, 12, 3, 0)


@pytest.mark.parametrize('offset,value,message', [(48, 1, 'not a transition'), (50, 2, 'Expected open')])
def test_invalid_mutation(offset, value, message):
    rom = fixture()
    rom[offset] = value
    with pytest.raises(ValueError, match=message):
        evidence.trace_state(rom, evidence.records(rom, 32), 12, 3, 0)


@pytest.mark.parametrize('data,expected', [
    (b'\x30\x04\0\0\x81\x07', b'\x07' * 4),
    (b'\x30\x03\0\0\x02abc', b'abc'),
])
def test_rl(data, expected):
    assert evidence.decompress_rl(data, 0, len(expected)) == expected


@pytest.mark.parametrize('data,size', [(b'', 3), (b'\x10\x03\0\0', 3),
                                       (b'\x30\x03\0\0\x81\x07', 3),
                                       (b'\x30\x03\0\0\x02a', 3), (b'\x30\x03\0\0', 4)])
def test_invalid_rl(data, size):
    with pytest.raises(ValueError):
        evidence.decompress_rl(data, 0, size)


@pytest.mark.parametrize('offset,value', [(32, 4), (36, 0)])
def test_invalid_record(offset, value):
    rom = fixture()
    rom[offset] = value
    with pytest.raises(ValueError, match='Unsupported'):
        evidence.records(rom, 32)


def test_wrong_rom():
    with pytest.raises(ValueError, match='unmodified USA'):
        evidence.build_evidence(bytes(0x1000000), {'entries': []})
