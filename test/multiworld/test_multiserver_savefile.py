"""CLI save-path isolation through real Context persistence and restart."""
from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

import MultiServer


@pytest.mark.asyncio
@pytest.mark.parametrize("explicit_path,disable_save", [(False, False), (True, False), (True, True)])
async def test_main_loads_and_saves_the_selected_path_across_restart(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, explicit_path: bool, disable_save: bool,
) -> None:
    multidata = tmp_path / "seed.archipelago"
    default_save = multidata.with_suffix(".apsave")
    selected_save = tmp_path / "isolated" / "chosen.apsave" if explicit_path else default_save
    selected_save.parent.mkdir(exist_ok=True)
    sentinel = b"another server owns the default save"
    if explicit_path:
        default_save.write_bytes(sentinel)
    if disable_save:
        selected_save.write_bytes(b"existing selected save must remain untouched")

    # World decoding and listener lifecycle are unrelated to save-path routing.
    # Keep Context.init_save/get_save/set_save/_save real, including disk I/O.
    def load(ctx: MultiServer.Context, filename: str, embedded: bool) -> None:
        ctx.data_filename = filename
        ctx.connect_names = {"save-path-test": (0, 1)}

    monkeypatch.setattr(MultiServer.Context, "load", load)
    monkeypatch.setattr(MultiServer.Context, "_start_async_saving", lambda self: None)
    monkeypatch.setattr(MultiServer.Utils, "init_logging", lambda **kwargs: None)
    monkeypatch.setattr(MultiServer.websockets, "serve", AsyncMock())
    monkeypatch.setattr(asyncio.get_running_loop(), "add_signal_handler", lambda *args: None)
    argv = ["MultiServer.py", str(multidata), "--host", "127.0.0.1", "--port", "0"]
    if explicit_path:
        argv += ["--savefile", str(selected_save)]
    if disable_save:
        argv.append("--disable_save")
    monkeypatch.setattr("sys.argv", argv)
    args = MultiServer.parse_args()
    args.auto_shutdown = 0
    seen: list[int] = []

    async def console(ctx: MultiServer.Context) -> None:
        count = ctx.stored_data.get("save_path_restart_probe", 0)
        seen.append(count)
        ctx.stored_data["save_path_restart_probe"] = count + 1
        assert ctx.save(True) is not disable_save
        ctx.exit_event.set()

    monkeypatch.setattr(MultiServer, "console", console)
    await MultiServer.main(args)
    assert selected_save.is_file()
    if explicit_path:
        assert default_save.read_bytes() == sentinel
    await MultiServer.main(args)
    assert seen == ([0, 0] if disable_save else [0, 1])
    if disable_save:
        assert selected_save.read_bytes() == b"existing selected save must remain untouched"
    if explicit_path:
        assert default_save.read_bytes() == sentinel
