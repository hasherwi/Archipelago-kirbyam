"""Pack Aarcayne Art's approved sprites into the existing bank-F color palette."""
from pathlib import Path
import sys

from PIL import Image

from world_statue_assets import BANK_F, _rgb, _to_tiles

ROOT = Path(__file__).resolve()
ASSETS = ROOT.parents[1] / "dev-docs" / "assets" / "ability-statues"
OUTPUT = ROOT.with_name("custom_statue_art.bin")
NAMES = ("Sleep", "Cook", "UFO", "Magic", "Mini", "Crash", "Question")


def pack() -> bytes:
    colors = [tuple(v * 255 / 31 for v in _rgb(c)) for c in BANK_F]
    frames = []
    for name in NAMES:
        with Image.open(ASSETS / f"{name}_Statue.png") as source:
            if source.size != (16, 16):
                raise ValueError(f"{name} must be exactly 16x16")
            rgba = list(source.convert("RGBA").getdata())
        indices = [0 if p[3] < 128 else min(range(1, 16), key=lambda i:
                    sum(w * (a - b) ** 2 for w, a, b in zip((3, 4, 2), p[:3], colors[i])))
                   for p in rgba]
        frames.append(_to_tiles(indices))
    if len(set(frames)) != len(NAMES) or not all(map(any, frames)):
        raise ValueError("Custom statue frames must be distinct and nonempty")
    return b"APSTA01\0" + b"".join(frames)


if __name__ == "__main__":
    data = pack()
    if "--check" in sys.argv:
        if OUTPUT.read_bytes() != data:
            raise SystemExit("Custom statue rows are stale; regenerate them")
    else:
        OUTPUT.write_bytes(data)
