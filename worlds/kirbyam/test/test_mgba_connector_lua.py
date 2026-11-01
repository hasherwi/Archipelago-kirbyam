"""Execute the mGBA socket lifecycle regression harness when Lua is installed."""

from pathlib import Path
import shutil
import subprocess

import pytest


def test_mgba_connector_socket_lifecycle() -> None:
    lua = shutil.which("lua") or shutil.which("lua5.4") or shutil.which("lua5.3")
    if lua is None:
        pytest.skip("Lua interpreter is not installed")
    root = Path(__file__).resolve().parents[3]
    result = subprocess.run(
        [lua, "worlds/kirbyam/tools/test_mgba_connector.lua"],
        cwd=root, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
