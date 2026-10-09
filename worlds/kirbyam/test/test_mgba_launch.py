"""World-local launcher/asset export tests. No emulator or real sockets."""
import argparse
import asyncio
import importlib
from pathlib import Path
import sys
from unittest.mock import AsyncMock, Mock, patch
import zipfile

import pytest

from worlds._bizhawk import context
from worlds.LauncherComponents import components
from .. import mgba_launcher as launcher


def test_world_component_preserves_bizhawk_patch_association():
    component = next(c for c in components if c.display_name == "KirbyAM mGBA Client")
    assert component.func is not None
    assert not component.handles_file("seed.apkirbyam")
    assert next(c for c in components if c.display_name == "BizHawk Client").handles_file("seed.apkirbyam")


def test_mgba_patch_keeps_preflight_and_metadata_without_emuhawk(caplog):
    metadata = {"server": "localhost:38281"}
    with patch.object(launcher, "_ensure_base_rom_valid") as preflight, \
            patch.object(context.Patch, "create_rom_file", return_value=(metadata, "seed.gba")), \
            patch.object(context, "_run_game") as run, \
            patch.object(context.settings, "get_settings", side_effect=AssertionError("emulator settings read")), \
            caplog.at_level("INFO", logger="Client"):
        assert launcher._patch_game("seed.apkirbyam") == metadata
    preflight.assert_called_once_with()
    run.assert_not_called()
    assert "seed.gba" in caplog.text


def test_default_bizhawk_patch_still_schedules_existing_launcher():
    with patch.object(context, "_ensure_kirbyam_base_rom_valid"), \
            patch.object(context.Patch, "create_rom_file", return_value=({}, "seed.gba")), \
            patch.object(context, "_run_game", new=Mock(return_value="launch sentinel")) as run, \
            patch.object(context.Utils, "async_start") as start:
        assert context._patch_and_run_game("seed.apkirbyam") == {}
    run.assert_called_once_with("seed.gba")
    start.assert_called_once_with("launch sentinel")


def test_preflight_failure_prevents_patch():
    with patch.object(launcher, "_ensure_base_rom_valid", side_effect=ValueError("wrong base ROM")), \
            patch.object(context.Patch, "create_rom_file") as patch_rom:
        with pytest.raises(ValueError, match="wrong base ROM"):
            launcher._patch_game("seed.apkirbyam")
    patch_rom.assert_not_called()


def test_other_world_patch_rejected_before_preflight():
    with patch.object(launcher, "_ensure_base_rom_valid") as preflight:
        with pytest.raises(ValueError, match="only .apkirbyam"):
            launcher._patch_game("other.apz5")
    preflight.assert_not_called()


@pytest.mark.parametrize("args, patch_file", [([], ""), (["seed.apkirbyam"], "seed.apkirbyam")])
def test_launcher_arguments(args, patch_file):
    result = launcher._get_parser().parse_args([*args, "--connector-dir", "connector"])
    assert result.patch_file == patch_file
    assert result.connector_dir == Path("connector")


def test_export_is_complete_and_idempotent(tmp_path):
    destination = tmp_path / "connector"
    script = launcher.export_connector(destination)
    assert script.name == "connector_bizhawkclient_mgba.lua"
    assert {p.name for p in destination.iterdir()} == {
        "connector_bizhawkclient_mgba.lua", "LICENSE.bhc-substitutes", "README.md", "json.lua", "base64.lua",
    }
    before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in destination.iterdir()}
    assert launcher.export_connector(destination) == script
    assert before == {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in destination.iterdir()}


def test_export_preserves_conflicting_file_without_partial_writes(tmp_path):
    destination = tmp_path / "connector"
    destination.mkdir()
    existing = destination / "json.lua"
    existing.write_text("player edited file")
    with pytest.raises(FileExistsError, match="fresh --connector-dir"):
        launcher.export_connector(destination)
    assert list(destination.iterdir()) == [existing]
    assert existing.read_text() == "player edited file"


def test_missing_dependency_does_not_create_output(tmp_path):
    with patch.object(launcher.Utils, "local_path", return_value=str(tmp_path / "missing.lua")):
        with pytest.raises(FileNotFoundError):
            launcher.export_connector(tmp_path / "output")
    assert not (tmp_path / "output").exists()


def test_missing_world_resource_does_not_create_output(tmp_path):
    with patch.object(launcher.pkgutil, "get_data", return_value=None):
        with pytest.raises(FileNotFoundError, match="resource missing"):
            launcher.export_connector(tmp_path / "output")
    assert not (tmp_path / "output").exists()


def test_export_reads_resources_from_zipped_package(tmp_path, monkeypatch):
    # Exercise the same pkgutil/zipimport mechanism used by installed APWorlds.
    package = "kirby_mgba_zip_fixture"
    archive = tmp_path / "fixture.apworld"
    payloads = {name: f"fixture {name}".encode() for name in launcher._CONNECTOR_FILES}
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr(f"{package}/__init__.py", "")
        for name, content in payloads.items():
            zf.writestr(f"{package}/mgba/{name}", content)
    monkeypatch.syspath_prepend(str(archive))
    importlib.import_module(package)
    try:
        monkeypatch.setattr(launcher, "__package__", package)
        destination = tmp_path / "output"
        launcher.export_connector(destination)
        for name, content in payloads.items():
            assert (destination / name).read_bytes() == content
    finally:
        sys.modules.pop(package, None)


def test_main_forwards_patch_server_without_launching_emulator(tmp_path):
    with patch("CommonClient.gui_enabled", False), \
            patch.object(launcher.Utils, "init_logging"), \
            patch.object(launcher, "export_connector", return_value=tmp_path / "connector.lua"), \
            patch.object(launcher, "_patch_game", return_value={"server": "localhost:38281"}), \
            patch.object(launcher, "_run_client", new_callable=AsyncMock) as run, \
            patch.object(context, "_run_game") as emulator:
        launcher.main("seed.apkirbyam", "--connector-dir", str(tmp_path))
    assert run.await_args.args[0].connect == "localhost:38281"
    emulator.assert_not_called()


def test_export_failure_does_not_start_client(tmp_path):
    with patch("CommonClient.gui_enabled", False), \
            patch.object(launcher.Utils, "init_logging"), \
            patch.object(launcher.Utils, "messagebox") as message, \
            patch.object(launcher, "export_connector", side_effect=FileExistsError("edited connector")), \
            patch.object(launcher, "_run_client", new_callable=AsyncMock) as run:
        launcher.main("--connector-dir", str(tmp_path))
    run.assert_not_called()
    assert "edited connector" in message.call_args.args[1]


@pytest.mark.asyncio
async def test_watcher_failure_closes_transport_and_shuts_down():
    ctx = Mock()
    ctx.exit_event = asyncio.Event()
    ctx.shutdown = AsyncMock()
    with patch("CommonClient.gui_enabled", False), \
            patch("CommonClient.server_loop", new_callable=AsyncMock), \
            patch.object(context, "BizHawkClientContext", return_value=ctx), \
            patch.object(context, "_game_watcher", new_callable=AsyncMock, side_effect=RuntimeError("broken")), \
            patch("worlds._bizhawk.disconnect") as disconnect:
        await launcher._run_client(argparse.Namespace(connect=None, password=None))
    assert ctx.exit_event.is_set()
    disconnect.assert_called_once_with(ctx.bizhawk_ctx)
    ctx.shutdown.assert_awaited_once()


@pytest.mark.parametrize("no_gui, replacement", [(True, "good.gba"), (False, None), (False, "good.gba")])
def test_world_preflight_rejects_or_reprompts(no_gui, replacement):
    from .test_bizhawk_patch_preflight import _KirbyRomFile, _RootSettings
    _KirbyRomFile.validate_calls = []
    _KirbyRomFile.browse_result = replacement
    root = _RootSettings("bad.gba")
    with patch("settings.get_settings", return_value=root), patch("settings.no_gui", no_gui):
        if no_gui or replacement is None:
            with pytest.raises((ValueError, FileNotFoundError)):
                launcher._ensure_base_rom_valid()
            root._save.assert_not_called()
        else:
            launcher._ensure_base_rom_valid()
            assert root.kirby_am_settings.rom_file == "good.gba"
            assert _KirbyRomFile.validate_calls == ["bad.gba", "good.gba"]
            root._save.assert_called_once()


def test_nogui_does_not_open_patch_picker(tmp_path):
    with patch("CommonClient.gui_enabled", True), \
            patch.object(launcher.Utils, "init_logging"), \
            patch.object(launcher.Utils, "open_filename") as picker, \
            patch.object(launcher, "export_connector", return_value=tmp_path / "connector.lua"), \
            patch.object(launcher, "_run_client", new_callable=AsyncMock) as run:
        launcher.main("--nogui", "--connector-dir", str(tmp_path))
    picker.assert_not_called()
    assert run.await_args.args[0].nogui
