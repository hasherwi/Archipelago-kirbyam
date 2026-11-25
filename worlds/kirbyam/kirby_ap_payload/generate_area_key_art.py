"""Convert exact 16×16 key source cell grids to shared GBA OBJ bank F.

Usage (Pillow needed for this development-only regeneration step):
    python kirby_ap_payload/generate_area_key_art.py
"""
from __future__ import annotations

import struct
from pathlib import Path

from collectible_art import BANK_F, _rgb, _to_tiles
from PIL import Image

ASSET_NAMES = (
    "01-rainbow-route.png", "02-moonlight-mansion.png", "03-cabbage-cavern.png",
    "04-mustard-mountain.png", "05-carrot-castle.png", "06-olive-ocean.png",
    "07-peppermint-palace.png", "08-radish-ruins.png", "09-candy-constellation.png", "10-copy-ability-room.png",
)
ART_DIR = Path(__file__).resolve().parents[1] / "dev-docs" / "assets" / "area-keys-1139"
MARKER = b"APKEY01\0"
USED_KEYS = (1 << len(ASSET_NAMES)) - 1
BANK_F_RGB888 = tuple(tuple((v << 3) | (v >> 2) for v in _rgb(c)) for c in BANK_F)


def key_tiles(path: Path) -> bytes:
    with Image.open(path) as source:
        if source.mode != "RGBA" or source.size != (1600, 1600):
            raise ValueError(f"Unexpected source sprite geometry: {path.name}")
        cells = source.resize((16, 16), Image.Resampling.NEAREST)
        if cells.resize(source.size, Image.Resampling.NEAREST).tobytes() != source.tobytes():
            raise ValueError(f"Nonuniform source pixel cell: {path.name}")
    def palette_index(rgba: tuple[int, int, int, int]) -> int:
        r, g, b, alpha = rgba
        if alpha < 128:
            return 0
        candidates: range | tuple[int, ...] = range(1, 16)
        if path.name == "10-copy-ability-room.png" and r - b >= 24 and r >= g + 10:
            # Preserve the gold shaft and rim as warm colors: unrestricted RGB
            # distance selects the same pink used for lavender highlights.
            candidates = (2, 3, 4, 6, 15)
        return min(candidates, key=lambda index: sum(
            w * (c - p) ** 2 for c, p, w in zip((r, g, b), BANK_F_RGB888[index], (3, 4, 2))
        ))
    return _to_tiles([palette_index(pixel) for pixel in cells.getdata()])


def build_table() -> bytes:
    tiles = [key_tiles(ART_DIR / filename) for filename in ASSET_NAMES]
    if not all(any(image) for image in tiles) or len(set(tiles)) != len(ASSET_NAMES):
        raise ValueError("Area Key assets must be visibly distinct and nonempty")
    return MARKER + struct.pack("<I", USED_KEYS) + b"".join(tiles)


if __name__ == "__main__":
    Path(__file__).with_name("area_key_reward_art.bin").write_bytes(build_table())
