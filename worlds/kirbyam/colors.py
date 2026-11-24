"""Color option/source-of-truth helpers for Kirby & The Amazing Mirror."""

from __future__ import annotations

from functools import lru_cache
from random import Random

from .data import load_json_data

STARTING_KIRBY_COLOR_RANDOM_PER_ROOM_OPTION = 254
COLOR_CONFIG_MAGIC = 0xC0100000
COLOR_CATALOG_VERSION = 4
COLOR_EXTENSION_MARKERS = {2: b"APCOL02\0", 3: b"APCOL03\0", 4: b"APCOL04\0"}
_LEGACY_COLOR_CATALOG_MAX = {2: 18, 3: 26}


def color_catalog_max_id(version: object) -> int:
    """Restrict the selected and per-room colors to the matching seed catalog."""
    if type(version) is not int:
        return 13
    if version == COLOR_CATALOG_VERSION:
        return max(kirby_color_name_by_id())
    return _LEGACY_COLOR_CATALOG_MAX.get(version, 13)


def color_catalog_marker(version: object) -> bytes | None:
    """Read an extension marker only for a known curated catalog version."""
    return COLOR_EXTENSION_MARKERS.get(version) if type(version) is int else None


def encode_color_config(color_id: int, per_room: bool) -> int:
    if type(color_id) is not int or color_id not in kirby_color_name_by_id():
        raise ValueError("Unsupported Kirby color ID")
    return COLOR_CONFIG_MAGIC | (0x100 if per_room else 0) | color_id


from .color_registry import KirbyColor, parse_color_catalog


@lru_cache(maxsize=1)
def load_kirby_colors() -> tuple[KirbyColor, ...]:
    return parse_color_catalog(load_json_data("colors.json"))


@lru_cache(maxsize=1)
def kirby_color_name_by_id() -> dict[int, str]:
    return {color.color_id: color.display_name for color in load_kirby_colors()}


def resolve_kirby_color(choice_value: int, rng: Random | None = None) -> KirbyColor:
    """Resolve an already-parsed StartingKirbyColor value to color metadata."""
    colors = load_kirby_colors()
    if choice_value == STARTING_KIRBY_COLOR_RANDOM_PER_ROOM_OPTION:
        if rng is None:
            raise ValueError("Room-transition random Kirby color requires a seeded world RNG.")
        return rng.choice(colors)

    for color in colors:
        if color.color_id == choice_value:
            return color

    raise ValueError(f"Unsupported Kirby color choice id: {choice_value}")


def choose_different_kirby_color(
    current_color_id: int, rng: Random, *, native_only: bool = False,
    max_color_id: int | None = None,
) -> KirbyColor:
    """Choose a supported color whose ID differs from *current_color_id*."""
    colors = load_kirby_colors()
    if current_color_id not in {color.color_id for color in colors}:
        raise ValueError(f"Unsupported current Kirby color id: {current_color_id}")

    candidates = tuple(color for color in colors if color.color_id != current_color_id
                       and (not native_only or color.color_id < 14)
                       and (max_color_id is None or color.color_id <= max_color_id))
    if not candidates:
        raise ValueError("Kirby color data must contain at least two supported colors.")
    return rng.choice(candidates)


def kirby_color_names_for_docs() -> str:
    return ", ".join(color.display_name for color in load_kirby_colors())
