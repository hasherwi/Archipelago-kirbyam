"""Tests for KirbyAM local test server bootstrap helpers."""

import os
import time
from pathlib import Path

import pytest

from .server.start_test_server import _find_latest_archive


def test_find_latest_archive_selects_newest_zip(tmp_path: Path) -> None:
    older = tmp_path / "older.archipelago"
    newest = tmp_path / "newest.zip"
    older.write_bytes(b"old")
    newest.write_bytes(b"new")
    # Ensure deterministic ordering by setting explicit modification times.
    now = time.time()
    os.utime(older, (now - 10, now - 10))
    os.utime(newest, (now, now))

    assert _find_latest_archive(tmp_path) == newest


def test_find_latest_archive_raises_when_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        _find_latest_archive(tmp_path)
