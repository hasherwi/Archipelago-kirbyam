"""Verify the complete Kirby ROM-smoke wheelhouse before offline installation."""
import argparse
import hashlib
import json
from pathlib import Path


def verify(directory: Path, manifest: Path) -> None:
    expected: dict[str, str] = json.loads(manifest.read_text(encoding="utf-8"))
    if not expected or any(Path(name).name != name or not name.endswith(".whl") for name in expected):
        raise ValueError("manifest must contain wheel basenames")
    actual = {path.name for path in directory.iterdir()}
    if actual != set(expected):
        raise ValueError("wheelhouse contains missing or unexpected artifacts")
    for name, digest in expected.items():
        path = directory / name
        if path.is_symlink() or not path.is_file():
            raise ValueError("wheel must be a regular file")
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError(f"SHA-256 mismatch: {name}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    verify(args.directory, args.manifest)


if __name__ == "__main__":
    main()
