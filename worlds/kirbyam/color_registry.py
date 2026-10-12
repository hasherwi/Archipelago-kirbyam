"""Shared, standard-library-only color registry validation for runtime and build tools."""
import re
from dataclasses import dataclass

_KIRBY_COLOR_ID_MIN = 0
_KIRBY_COLOR_ID_MAX = 253
_COLOR_KEY_PATTERN = re.compile(r"^[a-z_][a-z0-9_]*$")


@dataclass(frozen=True)
class KirbyColor:
    key: str
    color_id: int
    display_name: str
    palettes: tuple[tuple[int, ...], ...] = ()


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
    if type(color_id_raw) is not int:
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

    palettes = ()
    if color_id >= 14:
        if entry.get("native_fallback") != 0:
            raise ValueError("Curated colors require native Pink fallback 0")
        raw = entry.get("palettes")
        if not isinstance(raw, dict) or set(raw) != {"normal", "ufo", "hud"}:
            raise ValueError("Curated colors require normal, ufo and hud palettes")
        rows = []
        for context in ("normal", "ufo", "hud"):
            row = raw[context]
            if (not isinstance(row, list) or len(row) != 16
                    or any(type(word) is not int or not 0 <= word <= 0x7FFF for word in row)
                    or row[0] != 0):
                raise ValueError("Palette must contain 16 RGB555 words with transparent index 0")
            rows.append(tuple(row))
        provenance = entry.get("provenance")
        if not isinstance(provenance, dict) or any(not isinstance(provenance.get(k), str)
                or not provenance[k].strip() for k in ("normal", "ufo", "hud")):
            raise ValueError("Curated palettes require context-specific provenance")
        palettes = tuple(rows)
    elif "palettes" in entry:
        raise ValueError("Native colors must retain native palettes")
    return KirbyColor(key=key, color_id=color_id, display_name=display_name, palettes=palettes)


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


def parse_color_catalog(payload: object) -> tuple[KirbyColor, ...]:
    """Load and validate the color catalog used to build StartingKirbyColor."""
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
    ordered = tuple(sorted(colors, key=lambda color: color.color_id))
    native_keys = ("pink", "yellow", "red", "green", "snow", "carbon", "ocean",
                   "sapphire", "grape", "emerald", "orange", "chocolate", "cherry", "chalk")
    if tuple((c.color_id, c.key) for c in ordered[:14]) != tuple(enumerate(native_keys)):
        raise ValueError("Native color IDs 0..13 must retain their original names")
    if tuple(c.color_id for c in ordered) != tuple(range(len(ordered))):
        raise ValueError("Color IDs must be contiguous")
    return ordered


