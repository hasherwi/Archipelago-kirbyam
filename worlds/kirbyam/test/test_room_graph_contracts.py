"""Physical checks must survive changes to the logical room graph."""
from collections import Counter

from ..data import data, load_json_data


def test_logical_room_splits_do_not_duplicate_physical_room_checks():
    rooms = load_json_data("regions/rooms.json")
    bindings = []
    for room in rooms.values():
        metadata = room.get("room_sanity") or (room.get("locations") or {}).get("room_sanity")
        if metadata and metadata.get("included"):
            bindings.append(metadata)
    for field in ("location_id", "bit_index"):
        counts = Counter(binding[field] for binding in bindings)
        assert not {value: count for value, count in counts.items() if count != 1}


def test_every_minor_chest_has_exactly_one_logical_owner():
    counts = Counter(key for region in data.regions.values() for key in region.locations)
    minor_keys = {key for key, location in data.locations.items()
                  if key.startswith("MINOR_CHEST_") and location.source_rom_offset is not None}
    assert len(minor_keys) == 65
    assert {key: counts[key] for key in minor_keys} == dict.fromkeys(minor_keys, 1)
