"""Compile native L return as ordinary Normal-state movement, not a helper call."""

from functools import lru_cache
from typing import NamedTuple

from .data import data, load_json_data


class PhoneReturn(NamedTuple):
    destination: str
    sources: tuple[str, ...]


def _room_id(value: object) -> bool:
    return type(value) is int and 0 < value < 1000


def compile_phone_return(raw: object) -> PhoneReturn:
    if (not isinstance(raw, dict) or type(raw.get("schema")) is not int or raw["schema"] != 1
            or set(raw) != {"schema", "destination_region", "destination_native_room",
                            "room_flag_disallows_return", "encounter_rooms_not_modeled",
                            "stable_normal_sources_by_native_room"}):
        raise ValueError("Unsupported Phone return data schema")
    hub, native_hub = raw.get("destination_region"), raw.get("destination_native_room")
    if (not isinstance(hub, str) or hub not in data.regions or not hub.endswith("/ROOM_1_CENTRAL_CIRCLE")
            or not _room_id(native_hub)):
        raise ValueError("Phone return must land in the Central Circle floor region")
    exclusions: set[int] = set()
    for name in ("room_flag_disallows_return", "encounter_rooms_not_modeled"):
        rooms = raw.get(name)
        if (not isinstance(rooms, list) or any(not _room_id(room) for room in rooms)
                or len(set(rooms)) != len(rooms) or exclusions.intersection(rooms)):
            raise ValueError(f"Invalid Phone return exclusions: {name}")
        exclusions.update(rooms)
    if native_hub not in raw["room_flag_disallows_return"]:
        raise ValueError("Phone return must exclude its native hub room")

    bindings = raw.get("stable_normal_sources_by_native_room")
    if not isinstance(bindings, dict) or not bindings:
        raise ValueError("Missing Phone return source rooms")
    sources: dict[str, None] = {}
    for native, rooms in bindings.items():
        if (not isinstance(native, str) or not native.isascii() or not native.isdecimal()
                or len(native) > 3 or str(int(native)) != native or not _room_id(int(native))
                or int(native) in exclusions):
            raise ValueError(f"Invalid or excluded Phone return room: {native!r}")
        if not isinstance(rooms, list) or not rooms:
            raise ValueError(f"Missing Phone return compartments for native room {native}")
        for room in rooms:
            if (not isinstance(room, str) or room not in data.regions or "/ROOM_" not in room
                    or room.endswith("__ROOM_CHECK") or room.startswith(hub) or room in sources):
                raise ValueError(f"Invalid or duplicate Phone return source: {room!r}")
            sources[room] = None
    return PhoneReturn(hub, tuple(sources))


@lru_cache(maxsize=1)
def phone_return() -> PhoneReturn:
    return compile_phone_return(load_json_data("phone_return.json"))
