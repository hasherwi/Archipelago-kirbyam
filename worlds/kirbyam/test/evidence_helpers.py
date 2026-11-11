"""Portable integrity checks for tracked text evidence inputs."""

from pathlib import Path


def canonical_text_bytes(path: Path) -> bytes:
    """Undo Git checkout CRLF conversion, preserving all other source bytes."""
    return path.read_bytes().replace(b"\r\n", b"\n")
