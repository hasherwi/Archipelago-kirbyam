"""Versioned physical 100% contract for the USA ROM (issue #204).

Native percentage/AI 10000 alone cannot prove AP physical lever/switch actions.
Keep native completion, acknowledged checks and AP item ownership independent.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .data import data, load_json_data

FULL_COMPLETION_VERSION = 1
FULL_COMPLETION_MARKER_OFFSET = 0x1000010
FULL_COMPLETION_MARKER = b"APFULL01"
PHYSICAL_SAVE_ADDRESS = 0x02028C7C
PHYSICAL_SAVE_TAG = 0x48400000
PHYSICAL_SAVE_MASK = 0x7FFFF
LEGACY_HUB_SAVE_TAG = 0x48530000
LEGACY_HUB_SAVE_MASK = 0x7FFF
MANIFEST: dict[str, Any] = dict(load_json_data("full_completion.json"))
ROOM_INDICES = tuple(room["doors_idx"] for room in MANIFEST["rooms"])
ROOM_REGIONS = tuple(tuple(room["region_keys"]) for room in MANIFEST["rooms"] if room["region_keys"])
PHYSICAL_KEYS = tuple(MANIFEST["physical_location_keys"])
PHYSICAL_IDS = frozenset(data.locations[key].location_id for key in PHYSICAL_KEYS)
REQUIRED_ITEMS = tuple(item for item in data.items.values() if item.tags & {"Shards", "Levers", "HubConnections"})
REQUIRED_ITEM_IDS = frozenset(item.item_id for item in REQUIRED_ITEMS)
READ_KEYS = ("chest_flags", "shards", "room_visits", "world_switches", "save_id", "ai_state", "demo_flags")
NATIVE_READS = tuple((int(MANIFEST["native_addresses"][key]["address"], 16),
                      MANIFEST["native_addresses"][key]["width"], "System Bus") for key in READ_KEYS)
SAVE_ID_ADDRESS = int(MANIFEST["native_addresses"]["save_id"]["address"], 16)


def saved_physical_mask(raw: bytes, auth: bytes) -> int | None:
    """None means a missing/foreign/unsupported save record; never infer checks."""
    if len(raw) != 20 or len(auth) != 16 or raw[:16] != auth:
        return None
    word = int.from_bytes(raw[16:], "little")
    if word & ~PHYSICAL_SAVE_MASK == PHYSICAL_SAVE_TAG:
        return word & PHYSICAL_SAVE_MASK
    if word & ~LEGACY_HUB_SAVE_MASK == LEGACY_HUB_SAVE_TAG:
        return word & LEGACY_HUB_SAVE_MASK
    return None


def merge_acknowledged_levers(raw: bytes, auth: bytes, levers: int) -> bytes:
    """Merge server-confirmed pulls into native RAM; native code owns save timing."""
    existing = saved_physical_mask(raw, auth) or 0
    return auth + (PHYSICAL_SAVE_TAG | existing | ((levers & 15) << 15)).to_bytes(4, "little")


@dataclass(frozen=True)
class CompletionProgress:
    chests: int
    rooms: int
    switches: int
    shards: int
    final_clear: bool

    @property
    def complete(self) -> bool:
        return (self.chests, self.rooms, self.switches, self.shards, self.final_clear) == (84, 272, 15, 8, True)


def native_progress(values: list[bytes]) -> CompletionProgress | None:
    """Exact obligations, never a rounded percentage or compensating spare bit."""
    if len(values) != len(NATIVE_READS) or any(len(value) != spec[1] for value, spec in zip(values, NATIVE_READS)):
        return None
    chests, shards, visits, switches, save, ai, demo = values
    state = int.from_bytes(ai, "little")
    if int.from_bytes(save, "little") > 2 or int.from_bytes(demo, "little") & 0x70 or state < 300:
        return None
    return CompletionProgress(
        (int.from_bytes(chests, "little") & ((1 << 84) - 1)).bit_count(),
        sum(bool(int.from_bytes(visits[index * 2:index * 2 + 2], "little") & 0x8000) for index in ROOM_INDICES),
        sum(bool(int.from_bytes(switches[index:index + 4], "little")) for index in range(0, 60, 4)),
        (int.from_bytes(shards, "little") & 255).bit_count(),
        state in (9999, 10000),
    )


def ownership_complete(item_ids: Iterable[int]) -> bool:
    return REQUIRED_ITEM_IDS.issubset(item_ids)
