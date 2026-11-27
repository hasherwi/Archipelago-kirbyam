"""Exercise the object metadata decoder without distributing a retail ROM."""
import struct

import pytest

from ..tools import extract_object_transition_destinations as extractor


def template(type_id):
    rom = bytearray(0x50)
    rom[0:2] = (1, 0x24)
    rom[12] = type_id
    struct.pack_into("<hh", rom, 6, 656, 272)
    return rom


def test_warp_star_destination_uses_template_fields_not_subtype():
    rom = template(extractor.WARP_STAR)
    rom[14] = 5
    struct.pack_into("<hhH", rom, 0x1A, -4, 17, 195)
    assert extractor.decode_destination(bytes(rom), 0, extractor.WARP_STAR) == (195, [-4, 17])


@pytest.mark.parametrize(("packed", "spawn"), [(0, [0, 0]), (0xF300, [-13, 1]), (0x0004, [0, 1])])
def test_fuse_cannon_reproduces_native_argument_decoding(packed, spawn):
    rom = template(extractor.FUSE_CANNON)
    struct.pack_into("<H", rom, 0x12, 133)
    struct.pack_into("<H", rom, 0x18, packed)
    assert extractor.decode_destination(bytes(rom), 0, extractor.FUSE_CANNON) == (133, spawn)


def test_template_validation_rejects_wrong_type_and_truncation():
    rom = bytes(template(extractor.WARP_STAR))
    with pytest.raises(ValueError, match="Unexpected"):
        extractor.decode_destination(rom, 0, extractor.FUSE_CANNON)
    with pytest.raises(ValueError, match="out of bounds"):
        extractor.decode_destination(rom[:0x23], 0, extractor.WARP_STAR)


def test_join_preserves_source_and_flags_when_target_is_not_populated():
    rom = template(extractor.FUSE_CANNON)
    struct.pack_into("<H", rom, 0x12, 133)
    placement = dict(spawn_table=1, type_id=extractor.FUSE_CANNON, native_room=827,
                     template_address="0x08000000", position_pixels=[656, 272])
    inventory = {"rooms": [{"native_room": 827, "unused_room_slot": False}],
                 "placements": [placement]}
    assert extractor._extract(bytes(rom), inventory) == [{
        "source_native_room": 827, "mechanism": "fuse_cannon", "template_address": "0x08000000",
        "position_pixels": [656, 272], "destination_native_room": 133,
        "destination_is_populated": False, "configured_spawn_arguments": [0, 0],
    }]
    with pytest.raises(ValueError, match="duplicate"):
        extractor._extract(bytes(rom), {**inventory, "placements": [placement, placement]})


def test_pin_rejects_synthetic_input_for_public_evidence():
    with pytest.raises(ValueError, match="size and SHA-1 mismatch"):
        extractor.build_evidence(bytes(template(extractor.WARP_STAR)), {})
