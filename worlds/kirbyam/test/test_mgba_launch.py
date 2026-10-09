"""mGBA launch selection tests; these do not execute an emulator or adapter."""
from unittest.mock import Mock, patch

import pytest

from worlds._bizhawk import context


def test_mgba_patch_keeps_preflight_and_metadata_without_emuhawk(caplog):
    metadata = {"server": "localhost:38281"}
    with patch.object(context, "_ensure_kirbyam_base_rom_valid") as preflight, \
            patch.object(context.Patch, "create_rom_file", return_value=(metadata, "seed.gba")), \
            patch.object(context, "_run_game") as run, \
            patch.object(context.settings, "get_settings", side_effect=AssertionError("global emulator settings read")), \
            caplog.at_level("INFO", logger="Client"):
        assert context._patch_and_run_game("seed.apkirbyam", "mgba") == metadata
    preflight.assert_called_once_with("seed.apkirbyam")
    run.assert_not_called()
    assert "seed.gba" in caplog.text
    assert "connector_bizhawkclient_mgba.lua" in caplog.text


def test_default_patch_still_schedules_existing_launcher():
    with patch.object(context, "_ensure_kirbyam_base_rom_valid"), \
            patch.object(context.Patch, "create_rom_file", return_value=({}, "seed.gba")), \
            patch.object(context, "_run_game", new=Mock(return_value="launch sentinel")) as run, \
            patch.object(context.Utils, "async_start") as start:
        assert context._patch_and_run_game("seed.apkirbyam") == {}
    run.assert_called_once_with("seed.gba")
    start.assert_called_once_with("launch sentinel")


def test_mgba_preflight_failure_does_not_patch_or_launch():
    with patch.object(context, "_ensure_kirbyam_base_rom_valid", side_effect=ValueError("wrong base ROM")), \
            patch.object(context.Patch, "create_rom_file") as patch_rom, \
            patch.object(context, "_run_game") as run, \
            patch.object(context.Utils, "messagebox") as message:
        assert context._patch_and_run_game("seed.apkirbyam", "mgba") == {}
    patch_rom.assert_not_called()
    run.assert_not_called()
    message.assert_called_once()


@pytest.mark.parametrize("args, emulator, patch_file", [
    ([], "bizhawk", ""),
    (["--emulator", "mgba"], "mgba", ""),
    (["--emulator", "mgba", "seed.apkirbyam"], "mgba", "seed.apkirbyam"),
    (["seed.apkirbyam"], "bizhawk", "seed.apkirbyam"),
])
def test_per_launch_selection(args, emulator, patch_file):
    result = context._get_launch_parser().parse_args(args)
    assert result.emulator == emulator
    assert result.patch_file == patch_file


def test_unknown_emulator_rejected():
    with pytest.raises(SystemExit):
        context._get_launch_parser().parse_args(["--emulator", "other"])
