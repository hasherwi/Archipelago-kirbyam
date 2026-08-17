"""Color option/source-of-truth helpers for Kirby & The Amazing Mirror."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from random import Random

from .data import load_json_data

STARTING_KIRBY_COLOR_RANDOM_PER_ROOM_OPTION = 254
_KIRBY_COLOR_ID_MIN = 0
_KIRBY_COLOR_ID_MAX = 13
_COLOR_KEY_PATTERN = re.compile(r"^[a-z_][a-z0-9_]*$")


@dataclass(frozen=True)
class KirbyColor:
    key: str
    color_id: int
    display_name: str


def _parse_kirby_color_entry(entry: object) -> KirbyColor:
    """Validate one colors.json record and normalize it into immutable metadata."""
    if not isinstance(entry, dict):
        raise ValueError("Each Kirby color entry must be a JSON object.")

    key_raw = entry.get("key")
    if not isinstance(key_raw, str):
        raise ValueError(f"Kirby color entry has non-string key: {key_raw!r}")
    key = key_raw.strip().lower()
    if not key:
        raise ValueError("Kirby color entry is missing a non-empty 'key'.")
    if _COLOR_KEY_PATTERN.fullmatch(key) is None:
        raise ValueError(
            f"Kirby color '{key}' has an invalid key format. "
            "Expected [a-z_][a-z0-9_]*."
        )

    color_id_raw = entry.get("id")
    if not isinstance(color_id_raw, int):
        raise ValueError(f"Kirby color '{key}' has a non-integer id: {color_id_raw!r}")
    color_id = int(color_id_raw)
    if not _KIRBY_COLOR_ID_MIN <= color_id <= _KIRBY_COLOR_ID_MAX:
        raise ValueError(
            f"Kirby color '{key}' id {color_id} is out of supported range "
            f"{_KIRBY_COLOR_ID_MIN}..{_KIRBY_COLOR_ID_MAX}."
        )

    display_name_raw = entry.get("name")
    if not isinstance(display_name_raw, str):
        raise ValueError(f"Kirby color '{key}' has non-string display name: {display_name_raw!r}")
    display_name = display_name_raw.strip()
    if not display_name:
        raise ValueError(f"Kirby color '{key}' is missing a display name.")

    return KirbyColor(key=key, color_id=color_id, display_name=display_name)


def _validate_unique_color(
    color: KirbyColor,
    *,
    seen_keys: set[str],
    seen_ids: set[int],
) -> None:
    """Reject duplicate option keys/IDs before dynamic Choice construction."""
    if color.key in seen_keys:
        raise ValueError(f"Duplicate Kirby color key in colors.json: {color.key}")
    if color.color_id in seen_ids:
        raise ValueError(f"Duplicate Kirby color id in colors.json: {color.color_id}")
    seen_keys.add(color.key)
    seen_ids.add(color.color_id)


def _validate_required_pink(colors: list[KirbyColor]) -> None:
    """Keep native Pink fixed at ID 0, which is the world option default."""
    pink = next((color for color in colors if color.key == "pink"), None)
    if pink is None or pink.color_id != 0:
        raise ValueError("Kirby color data must include pink with id 0.")


@lru_cache(maxsize=1)
def load_kirby_colors() -> tuple[KirbyColor, ...]:
    """Load and validate the color catalog used to build StartingKirbyColor."""
    payload = load_json_data("colors.json")
    if not isinstance(payload, dict):
        raise ValueError("Kirby color data must be a JSON object.")

    raw_colors = payload.get("colors", [])
    if not isinstance(raw_colors, list) or not raw_colors:
        raise ValueError("Kirby color data must define a non-empty 'colors' list.")

    colors: list[KirbyColor] = []
    seen_keys: set[str] = set()
    seen_ids: set[int] = set()
    for entry in raw_colors:
        color = _parse_kirby_color_entry(entry)
        _validate_unique_color(color, seen_keys=seen_keys, seen_ids=seen_ids)
        colors.append(color)

    _validate_required_pink(colors)
    return tuple(sorted(colors, key=lambda color: color.color_id))


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


def choose_different_kirby_color(current_color_id: int, rng: Random) -> KirbyColor:
    """Choose a supported color whose ID differs from *current_color_id*."""
    colors = load_kirby_colors()
    if current_color_id not in {color.color_id for color in colors}:
        raise ValueError(f"Unsupported current Kirby color id: {current_color_id}")

    candidates = tuple(color for color in colors if color.color_id != current_color_id)
    if not candidates:
        raise ValueError("Kirby color data must contain at least two supported colors.")
    return rng.choice(candidates)


def kirby_color_names_for_docs() -> str:
    return ", ".join(color.display_name for color in load_kirby_colors())
