"""Kirby-only VERSION recovery; protocol doubles are not emulator acceptance."""
import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest
from worlds import _bizhawk as bh
from ..mgba_transport import KirbyMGBATransport


def attach(ctx: bh.BizHawkContext, reply: bytes, *, self_connected: bool = False) -> Mock:
    reader = asyncio.StreamReader()
    reader.feed_data(reply)
    reader.feed_eof()
    writer = Mock()
    writer.drain = AsyncMock()
    writer.get_extra_info.side_effect = lambda name: (
        ("127.0.0.1", 43055) if self_connected or name == "peername"
        else ("127.0.0.1", 50000)
    )
    ctx.streams = reader, writer
    ctx.connection_status = bh.ConnectionStatus.TENTATIVE
    return writer


def assert_status(ctx: bh.BizHawkContext, expected: bh.ConnectionStatus) -> None:
    assert ctx.connection_status == expected


@pytest.mark.parametrize("reply", [b"VERSION\n", b"garbage\n", b"\xff\n", b"\n"])
def test_invalid_version_disconnects_and_can_recover(reply: bytes) -> None:
    async def run() -> None:
        ctx = KirbyMGBATransport()
        writer = attach(ctx, reply)
        with pytest.raises(bh.RequestFailedError, match="invalid connector VERSION"):
            await bh.get_script_version(ctx)
        writer.close.assert_called_once()
        assert ctx.streams is None
        assert_status(ctx, bh.ConnectionStatus.NOT_CONNECTED)
        attach(ctx, b"1\n")
        assert await bh.get_script_version(ctx) == 1
        assert_status(ctx, bh.ConnectionStatus.CONNECTED)
    asyncio.run(run())


def test_self_connection_is_rejected_before_sending() -> None:
    async def run() -> None:
        ctx = KirbyMGBATransport()
        writer = attach(ctx, b"VERSION\n", self_connected=True)
        with pytest.raises(bh.RequestFailedError, match="self-connected"):
            await bh.get_script_version(ctx)
        writer.write.assert_not_called()
        writer.close.assert_called_once()
        assert_status(ctx, bh.ConnectionStatus.NOT_CONNECTED)
    asyncio.run(run())


def test_absent_connector_then_valid_connection() -> None:
    async def run() -> None:
        ctx = KirbyMGBATransport()
        with patch.object(asyncio, "open_connection", new=AsyncMock(side_effect=ConnectionRefusedError)):
            assert not await bh.connect(ctx)
        assert ctx.streams is None
        attach(ctx, b"1\n")
        streams = ctx.streams
        ctx.streams = None
        with patch.object(asyncio, "open_connection", new=AsyncMock(return_value=streams)):
            assert await bh.connect(ctx)
        assert await bh.get_script_version(ctx) == 1
    asyncio.run(run())


def test_shared_watcher_retries_invalid_handshake_without_exiting() -> None:
    from worlds._bizhawk import context

    async def run() -> None:
        ctx = Mock()
        ctx.bizhawk_ctx = KirbyMGBATransport()
        ctx.exit_event = asyncio.Event()
        ctx.watcher_event = asyncio.Event()
        ctx.watcher_timeout = 0.001
        replies = iter([b"VERSION\n", b"1\n"])

        async def connect(transport: bh.BizHawkContext) -> bool:
            attach(transport, next(replies))
            return True

        async def ping(transport: bh.BizHawkContext) -> None:
            assert transport.connection_status == bh.ConnectionStatus.CONNECTED
            ctx.exit_event.set()
            raise bh.NotConnectedError  # end this bounded watcher test

        with patch.object(context, "connect", side_effect=connect) as connecting, \
                patch.object(context, "ping", side_effect=ping) as pinging:
            await asyncio.wait_for(context._game_watcher(ctx), 1)
        assert connecting.call_count == 2
        assert pinging.call_count == 1
    asyncio.run(run())


def test_numeric_mismatch_and_non_version_requests_keep_shared_behavior() -> None:
    async def run() -> None:
        ctx = KirbyMGBATransport()
        attach(ctx, b"2\n")
        assert await bh.get_script_version(ctx) == 2  # watcher handles incompatibility
        attach(ctx, b"[]\n")
        assert await bh.send_requests(ctx, []) == []
        baseline = bh.BizHawkContext()
        attach(baseline, b"VERSION\n")
        with pytest.raises(ValueError):
            await bh.get_script_version(baseline)  # shared AP is unchanged
    asyncio.run(run())
