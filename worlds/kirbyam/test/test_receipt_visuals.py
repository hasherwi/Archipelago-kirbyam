"""Visual acknowledgements require new remote-world delivery, not history."""
import asyncio
from struct import pack, unpack
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from NetUtils import NetworkItem
from ..reward_art_types import KIRBY_NATIVE_ART_BY_ITEM_CODE, RewardArt
from ..receipt_visuals import (
    VISUAL_ART_BITS, VISUAL_FRAME_MASK, VISUAL_GEM, VISUAL_LIMIT, VISUAL_MAILBOX, VISUAL_MAX_OPCODE, VISUAL_REJECTED,
    VISUAL_ROM_MARKER, VISUAL_TRAP, ReceiptVisuals, visual_for_remote_receipt,
)
from .test_receipt_journal import Mailbox, drain, make_client, receipt_env, tick  # noqa: F401


def item(location, player=2, flags=0):
    return NetworkItem(3860107, location, player, flags)


@pytest.mark.parametrize(("location", "player", "flags", "visual"), [
    (7, 2, 0, VISUAL_GEM), (7, 2, 3, VISUAL_GEM), (7, 2, 5, VISUAL_TRAP),
    (-2, 0, 1, 0), (-1, 2, 4, 0), (7, 1, 0, 0), (7, 0, 4, 0),
])
def test_only_real_other_world_check_has_item_art(location, player, flags, visual):
    assert visual_for_remote_receipt(item(location, player, flags), 1) == visual


def test_history_identity_excludes_reload_gap_unsettled_backlog_and_duplicated_ack():
    q = ReceiptVisuals()
    socket = SimpleNamespace(closed=False)
    session = ("connected",)
    history = [item(1)]
    q.packet(socket, session, history, 0, 1, 0, 1)
    q.acknowledge(0, history[0], first=True)
    assert not q.pending  # First packet is catch-up.

    history.append(item(2))
    q.packet(socket, session, history, 1, 1, 0, 1)
    q.acknowledge(1, history[1], first=True)
    assert not q.pending  # Catch-up was still being delivered during append.

    history.extend((item(3), item(4)))
    q.packet(socket, session, history, 2, 2, 2, 1)
    q.acknowledge(2, item(3), first=True)  # Same fields, but not the observed object.
    q.acknowledge(3, history[3], first=False)
    assert not q.pending

    # Rewritten index-zero history should invalidate all live witnesses.
    history.append(item(5))
    q.packet(socket, session, history, 4, 1, 4, 1)
    assert q.live
    replacement = [item(i) for i in range(1, 7)]
    q.packet(socket, session, replacement, 0, 6, 5, 1)
    q.acknowledge(5, replacement[5], first=True)
    assert not q.live and not q.pending


def test_empty_baseline_first_append_zero_and_bounded_drop_order():
    q = ReceiptVisuals()
    socket = SimpleNamespace(closed=False)
    session = ("online",)
    q.baseline(socket, session, [])
    history = [item(200 + i, flags=4 if i % 2 else 0) for i in range(23)]
    q.packet(socket, session, history, 0, len(history), 0, 1)
    assert len(q.live) == VISUAL_LIMIT
    for i, it in enumerate(history):
        q.acknowledge(i, it, first=True)
    assert list(q.pending) == [VISUAL_GEM, VISUAL_TRAP] * (VISUAL_LIMIT // 2)
    history += [item(999)]
    q.packet(socket, session, history, 23, 1, 23, 1)
    q.acknowledge(23, history[-1], first=True)
    assert len(q.pending) == VISUAL_LIMIT and not q.live


@pytest.mark.parametrize(("code", "art"), sorted(KIRBY_NATIVE_ART_BY_ITEM_CODE.items()))
def test_known_kirby_item_uses_its_distinct_code_on_live_remote_receipt(code, art):
    assert visual_for_remote_receipt(NetworkItem(code, 7, 2, 0), 1) == art + 1
    assert visual_for_remote_receipt(NetworkItem(code, 7, 2, 4), 1) == VISUAL_TRAP
    assert visual_for_remote_receipt(NetworkItem(code, -2, 0, 0), 1) == 0
    assert visual_for_remote_receipt(NetworkItem(code, 7, 1, 0), 1) == 0


def test_access_receipt_art_codes_keep_preexisting_shard_and_wire_reserved():
    assert VISUAL_ROM_MARKER == b"APVIS04\0"
    assert RewardArt.SHARD + 1 == 45
    assert RewardArt.PHONE + 1 == 46
    assert RewardArt.HUB_SWITCH + 1 == 47
    assert RewardArt.LEVER_WALL + 1 == 48
    assert visual_for_remote_receipt(NetworkItem(3860501, 7, 2, 1), 1) == 46
    for code in range(3860401, 3860416):
        assert visual_for_remote_receipt(NetworkItem(code, 7, 2, 1), 1) == 47
    for code in range(3860037, 3860041):
        assert visual_for_remote_receipt(NetworkItem(code, 7, 2, 1), 1) == 48


@pytest.mark.asyncio
async def test_native_mailbox_accept_reject_ambiguous_reset_busy_and_distinct_art():
    q = ReceiptVisuals()
    q.pending.extend((VISUAL_GEM, VISUAL_TRAP))
    q.supported = True
    read, write = AsyncMock(), AsyncMock(return_value=True)
    ready = 1

    async def pump(req, res, eligible, active, frame):
        read.return_value = [pack("<IIII", req, res, eligible, active), pack("<I", frame)]
        await q.pump(None, auth_offset=0xF00000, auth=b"rom identity", frame_addr=0x0203B01C,
                     session_current=lambda: True)

    with patch("worlds.kirbyam.receipt_visuals.bizhawk.read", read), \
         patch("worlds.kirbyam.receipt_visuals.bizhawk.guarded_write", write):
        await pump(0, 0, ready, 1, 10)
        await pump(0, 0, 0, 0, 10)
        await pump(0, 0, 1 << VISUAL_TRAP, 0, 10)  # Stale bitmask is not a valid ready value.
        assert write.await_count == 0
        await pump(0, 0, ready, 0, 10)
        first = (10 << VISUAL_ART_BITS) | VISUAL_GEM
        assert q.in_flight == first
        transport, values, guards = write.await_args.args
        assert values == [(VISUAL_MAILBOX + 4, bytes(4), "System Bus"),
                          (VISUAL_MAILBOX, pack("<I", first), "System Bus")]
        assert (0xF00000, b"rom identity", "ROM") in guards
        await pump(first, 0, ready, 0, 11)
        assert write.await_count == 1
        await pump(0, first | VISUAL_REJECTED, ready, 0, 12)
        assert write.await_count == 2 and q.in_flight == (12 << VISUAL_ART_BITS) | VISUAL_GEM
        await pump(0, 0, ready, 0, 13)  # Reset: never double-display the ambiguous gem.
        assert list(q.pending) == [VISUAL_TRAP]
        trap = (13 << VISUAL_ART_BITS) | VISUAL_TRAP
        assert q.in_flight == trap
        await pump(0, trap, ready, 1, 14)
        assert not q.pending and write.await_count == 3


@pytest.mark.asyncio
async def test_high_collectible_opcode_and_frame_wrap_keep_the_reject_bit_free():
    q = ReceiptVisuals()
    opcode = max(RewardArt) + 1
    assert opcode == VISUAL_MAX_OPCODE == 48
    q.pending.append(opcode)
    q.supported = True
    read = AsyncMock(return_value=[pack("<IIII", 0, 0, 1, 0),
                                  pack("<I", 0xFFFFFFFF)])
    write = AsyncMock(return_value=True)
    with patch("worlds.kirbyam.receipt_visuals.bizhawk.read", read), \
         patch("worlds.kirbyam.receipt_visuals.bizhawk.guarded_write", write):
        await q.pump(None, auth_offset=5, auth=b"id", frame_addr=8, session_current=lambda: True)
    assert q.in_flight == (VISUAL_FRAME_MASK << VISUAL_ART_BITS) | opcode
    assert q.in_flight & VISUAL_REJECTED == 0
    assert unpack("<I", write.await_args.args[1][-1][1])[0] == q.in_flight


@pytest.mark.asyncio
@pytest.mark.parametrize("marker", [bytes(8), b"APVIS01\0", b"APVIS02\0", b"APVIS03\0"])
async def test_marker_is_optional_and_same_socket_history_replacement_fences_async_pump(marker):
    q = ReceiptVisuals()
    q.pending.append(VISUAL_GEM)
    with patch("worlds.kirbyam.receipt_visuals.bizhawk.read", AsyncMock(return_value=[marker])), \
         patch("worlds.kirbyam.receipt_visuals.bizhawk.guarded_write", AsyncMock()) as write:
        await q.pump(None, auth_offset=5, auth=b"id", frame_addr=8, session_current=lambda: True)
        assert q.supported is False and not q.pending
        write.assert_not_awaited()
    q = ReceiptVisuals()
    socket = SimpleNamespace(closed=False)
    q.baseline(socket, ("online",), [])
    q.pending.append(VISUAL_GEM)

    async def invalidate(*_):
        q.baseline(socket, ("online",), [])
        return [VISUAL_ROM_MARKER]

    with patch("worlds.kirbyam.receipt_visuals.bizhawk.read", side_effect=invalidate), \
         patch("worlds.kirbyam.receipt_visuals.bizhawk.guarded_write", AsyncMock()) as write:
        await q.pump(None, auth_offset=5, auth=b"id", frame_addr=8, session_current=lambda: True)
        assert q.supported is None and not q.pending
        write.assert_not_awaited()


@pytest.mark.asyncio
async def test_client_ack_visuals_separate_from_sound_start_history_self_and_rewind(receipt_env):
    ctx = receipt_env
    client = make_client(ctx)
    client._notification_settings_loaded = True
    client.on_package(ctx, "Connected", {})

    def packet(index, *items):
        # CommonClient resets at index zero, otherwise appends only contiguously.
        if index == 0:
            ctx.items_received = []
        if index == len(ctx.items_received):
            ctx.items_received.extend(items)
        client.on_package(ctx, "ReceivedItems", {"index": index, "items": list(items)})

    packet(0, item(-2, 0), item(10))
    box = Mailbox(client)
    box.memory[client._transport_addr("mailbox_init_cookie")] = pack("<I", 0x4B41504D)
    box.memory[client._transport_addr("delivered_vitality_item_bits")] = pack("<I", 1 << 31)
    display = AsyncMock()
    await drain(client, ctx, box, display)
    assert not client._receipt_visuals.pending
    assert client._delivered_item_index == 2
    client._watcher_server_ready = True

    packet(2, item(20), item(21, ctx.slot), NetworkItem(3860032, 22, 2, 4),
           NetworkItem(3860201, 23, 2, 2))
    assert not client._receipt_visuals.pending
    await tick(client, ctx, box, display)
    assert not client._receipt_visuals.pending
    assert unpack("<I", box.memory[client._transport_addr("incoming_item_flag")])[0] == 1
    box.consume()
    await tick(client, ctx, box, display)
    assert list(client._receipt_visuals.pending) == [VISUAL_GEM]
    await drain(client, ctx, box, display)
    assert list(client._receipt_visuals.pending) == [VISUAL_GEM, VISUAL_TRAP, RewardArt.PAINT_02 + 1]
    assert list(client._receipt_sounds.pending) == [2, 2, 2, 3, 2]

    # Same socket Sync replay is never live; a fresh socket is not either.
    packet(0, *ctx.items_received)
    assert not client._receipt_visuals.pending
    ctx.server.socket = SimpleNamespace(closed=False)
    client.on_package(ctx, "Connected", {})
    packet(0, *ctx.items_received)
    assert not client._receipt_visuals.pending


@pytest.mark.asyncio
async def test_first_live_remote_item_after_empty_login_without_journal(receipt_env):
    ctx = receipt_env
    client = make_client(ctx)
    client._notification_settings_loaded = True
    client.on_package(ctx, "Connected", {})
    await asyncio.sleep(0)  # Complete the empty Connected packet batch.
    assert client._receipt_visuals.history_end == 0 and client._receipt_journal is None
    client._watcher_server_ready = True
    ctx.items_received = [item(20)]
    client.on_package(ctx, "ReceivedItems", {"index": 0, "items": ctx.items_received})
    assert not client._receipt_visuals.pending
    box = Mailbox(client)
    box.memory[client._transport_addr("mailbox_init_cookie")] = pack("<I", 0x4B41504D)
    box.memory[client._transport_addr("delivered_vitality_item_bits")] = pack("<I", 1 << 31)
    await drain(client, ctx, box, AsyncMock())
    assert list(client._receipt_visuals.pending) == [VISUAL_GEM]


def test_sync_after_out_of_order_packet_is_not_first_live_append_even_from_empty():
    socket = SimpleNamespace(closed=False)
    q = ReceiptVisuals()
    session = ("online",)
    history = []
    q.baseline(socket, session, history)
    q.packet(socket, session, history, 3, 2, 0, 1)  # CommonClient asks for Sync.
    assert q.history_end is None
    history = [item(7), item(8)]
    q.packet(socket, session, history, 0, 2, 0, 1)
    q.acknowledge(0, history[0], first=True)
    q.acknowledge(1, history[1], first=True)
    assert not q.pending
    history.append(item(9))
    q.packet(socket, session, history, 2, 1, 2, 1)
    q.acknowledge(2, history[2], first=True)
    assert list(q.pending) == [VISUAL_GEM]


@pytest.mark.asyncio
async def test_unassigned_wire_opcode_is_dropped_not_sent_even_if_7_bits_would_fit():
    q = ReceiptVisuals()
    q.supported = True
    q.pending.extend((VISUAL_MAX_OPCODE + 1, VISUAL_GEM))
    read = AsyncMock(return_value=[pack("<IIII", 0, 0, 1, 0), pack("<I", 19)])
    write = AsyncMock(return_value=True)
    with patch("worlds.kirbyam.receipt_visuals.bizhawk.read", read), \
         patch("worlds.kirbyam.receipt_visuals.bizhawk.guarded_write", write):
        await q.pump(None, auth_offset=5, auth=b"id", frame_addr=8, session_current=lambda: True)
        write.assert_not_awaited()
        await q.pump(None, auth_offset=5, auth=b"id", frame_addr=8, session_current=lambda: True)
    assert q.in_flight == (19 << VISUAL_ART_BITS) | VISUAL_GEM
