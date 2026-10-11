"""World-local mGBA entry point; reuse AP's unmodified BizHawk protocol client."""
from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path
import pkgutil
from typing import Any

import Utils

logger = logging.getLogger("Client")
_CONNECTOR_FILES = ("connector_bizhawkclient_mgba.lua", "LICENSE.bhc-substitutes", "README.md")


def export_connector(destination: Path) -> Path:
    """Materialize zipped APWorld assets beside AP's existing Lua dependencies.

    Never replace different existing files: the player may have edited them or
    chosen a directory holding another connector version. Choose a fresh directory
    to upgrade. Read all inputs and detect conflicts before creating output files.
    """
    package = __package__
    if not package:
        raise RuntimeError("Run the world launcher through Archipelago or python -m")
    contents: dict[str, bytes] = {}
    for name in _CONNECTOR_FILES:
        data = pkgutil.get_data(package, f"mgba/{name}")
        if data is None:
            raise FileNotFoundError(f"KirbyAM mGBA resource missing: {name}")
        contents[name] = data
    for name in ("base64.lua", "json.lua"):
        contents[name] = Path(Utils.local_path("data", "lua", name)).read_bytes()
    for name, data in contents.items():
        target = destination / name
        if target.exists() and target.read_bytes() != data:
            raise FileExistsError(f"Refusing to replace {target}; select a fresh --connector-dir")
    destination.mkdir(parents=True, exist_ok=True)
    for name, data in contents.items():
        target = destination / name
        if not target.exists():
            # Exclusive creation also protects a file created after the preflight.
            with target.open("xb") as output:
                output.write(data)
    return destination / _CONNECTOR_FILES[0]


def _get_parser() -> argparse.ArgumentParser:
    from CommonClient import get_base_parser
    parser = get_base_parser()
    parser.add_argument("patch_file", default="", nargs="?", help="KirbyAM .apkirbyam patch (optional)")
    parser.add_argument("--connector-dir", type=Path, default=None,
                        help="Export the connector here; use a fresh directory when upgrading")
    return parser


def _patch_game(patch_file: str) -> dict[str, Any]:
    import Patch
    if not patch_file.lower().endswith(".apkirbyam"):
        raise ValueError("The KirbyAM mGBA launcher accepts only .apkirbyam patches")
    _ensure_base_rom_valid()
    metadata, output_file = Patch.create_rom_file(patch_file)
    logger.info("Patched ROM ready: %s. Open it manually in mGBA.", output_file)
    return metadata


def _ensure_base_rom_valid() -> None:
    # Keep Kirby-specific preflight inside the APWorld; stock AP need not carry
    # this fork's helper in the shared BizHawk context module.
    import settings
    cfg = settings.get_settings()
    kirby_settings = cfg.kirby_am_settings
    rom_cls = getattr(type(kirby_settings), "KirbyAmRomFile")
    rom_path = str(kirby_settings.rom_file)
    try:
        rom_cls.validate(rom_path)
    except (ValueError, FileNotFoundError, OSError):
        if settings.no_gui:
            raise
        replacement = rom_cls(rom_path).browse()
        if replacement is None:
            raise FileNotFoundError("KirbyAM base ROM validation failed; no replacement selected")
        rom_cls.validate(str(replacement))
        kirby_settings.rom_file = replacement
        cfg.save()


async def _run_client(args: argparse.Namespace) -> None:
    from CommonClient import gui_enabled, server_loop
    from worlds._bizhawk import disconnect
    from worlds._bizhawk.context import BizHawkClientContext, _game_watcher
    ctx = BizHawkClientContext(args.connect, args.password)
    ctx.server_task = asyncio.create_task(server_loop(ctx), name="ServerLoop")
    if gui_enabled and not getattr(args, "nogui", False):
        ctx.run_gui()
    ctx.run_cli()
    watcher_task = asyncio.create_task(_game_watcher(ctx), name="GameWatcher")
    try:
        await watcher_task
    except Exception:
        logger.exception("KirbyAM mGBA client watcher failed")
    finally:
        ctx.exit_event.set()
        disconnect(ctx.bizhawk_ctx)
        await ctx.shutdown()


def main(*launch_args: str) -> None:
    """Patch/export through world-local code; never launch or reconfigure an emulator."""
    import colorama
    from CommonClient import gui_enabled
    args = _get_parser().parse_args(launch_args)
    Utils.init_logging("KirbyAMmGBAClient", exception_logger="Client")
    colorama.just_fix_windows_console()
    try:
        if not args.patch_file and gui_enabled and not getattr(args, "nogui", False):
            args.patch_file = Utils.open_filename(
                "KirbyAM patch (cancel to connect without patching)",
                [("KirbyAM patch", (".apkirbyam",))],
            ) or ""
        connector_dir = args.connector_dir or Path(Utils.user_path("kirbyam", "mgba-connector"))
        connector = export_connector(connector_dir)
        if args.patch_file:
            metadata = _patch_game(args.patch_file)
            if "server" in metadata:
                args.connect = metadata["server"]
        logger.info("KirbyAM mGBA mode: open the patched ROM and load %s in Tools > Scripting.", connector)
        logger.info("Use mGBA 0.10+ with scripting and only one connector instance. Notices appear in the "
                    "Archipelago Connector text panel, not over the game image. Shared transport logs still "
                    "use the name BizHawk; protocol 1 does not identify the emulator.")
        asyncio.run(_run_client(args))
    except Exception as exc:
        logger.exception("KirbyAM mGBA startup failed")
        Utils.messagebox("KirbyAM mGBA startup failed", str(exc), True)
    finally:
        colorama.deinit()


if __name__ == "__main__":
    import sys
    main(*sys.argv[1:])
