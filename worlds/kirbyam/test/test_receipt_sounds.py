"""Receipt cues use a separate native mailbox, never the AP offer itself."""
from os import name as os_name
from pathlib import Path
from runpy import run_path
from shutil import which
from struct import pack, unpack
from subprocess import run
from unittest.mock import AsyncMock, patch

import pytest

from NetUtils import NetworkItem
from ..receipt_sounds import CUE_MAILBOX, CUE_REJECTED, ReceiptSounds, cue_for_receipt
from .test_receipt_journal import Mailbox, drain, make_client, receipt_env, tick  # noqa: F401
from .test_runtime_regression_hooks import patch_rom


@pytest.mark.parametrize("flags,cue", [(0, 2), (2, 2), (1, 1), (3, 1), (4, 3), (7, 3)])
def test_mateos_classes_prioritize_trap_then_progression(flags, cue):
    assert cue_for_receipt(NetworkItem(3860001, 3960000, 1, flags)) == cue
    assert cue_for_receipt(NetworkItem(3860001, -2, 0, flags)) == 0


@pytest.mark.asyncio
async def test_ack_sounds_not_writes_or_replay_even_for_same_item(receipt_env):
    ctx = receipt_env
    # A starting item is silent. A useful remote receipt and a self-sent copy
    # with the same item ID remain distinct. The trap has mixed flags.
    ctx.items_received = [
        NetworkItem(3860025, -2, 0, 1),
        NetworkItem(3860025, 3960000, 2, 2),
        NetworkItem(3860025, 3960001, ctx.slot, 2),
        NetworkItem(3860032, 3960002, 2, 5),
    ]
    client = make_client(ctx)
    display = AsyncMock()
    box = Mailbox(client)
    box.memory[client._transport_addr("mailbox_init_cookie")] = (0x4B41504D).to_bytes(4, "little")
    box.memory[client._transport_addr("delivered_vitality_item_bits")] = (1 << 31).to_bytes(4, "little")
    await tick(client, ctx, box, display)
    assert not client._receipt_sounds.pending
    box.consume()
    await tick(client, ctx, box, display)
    assert not client._receipt_sounds.pending
    # Reset clears the offer without advancing the native count: not an ACK.
    box.memory[client._transport_addr("incoming_item_flag")] = bytes(4)
    await tick(client, ctx, box, display)
    assert not client._receipt_sounds.pending
    await drain(client, ctx, box, display)
    assert list(client._receipt_sounds.pending) == [2, 2, 3]
    client._receipt_journal.close()

    restarted = make_client(ctx)
    restored = Mailbox(restarted)
    restored.memory[restarted._transport_addr("mailbox_init_cookie")] = (0x4B41504D).to_bytes(4, "little")
    restored.memory[restarted._transport_addr("delivered_vitality_item_bits")] = (1 << 31).to_bytes(4, "little")
    await drain(restarted, ctx, restored, display)
    assert not restarted._receipt_sounds.pending
    # Outgoing ItemSend JSON is not a local receipt.
    restarted._maybe_queue_self_send_fallback_item(ctx, {
        "type": "ItemSend", "receiving": ctx.slot + 1,
        "item": NetworkItem(3860025, 3960004, ctx.slot, 1),
    })
    assert len(ctx.items_received) == 4
    assert not restarted._receipt_sounds.pending
    restarted._reset_reconnect_transient_state()
    ctx.items_received.append(NetworkItem(3860025, 3960003, 2, 1))
    await drain(restarted, ctx, restored, display)
    assert list(restarted._receipt_sounds.pending) == [1]

    # A genuinely different seed/ROM clears queued cues before any transport.
    ctx.server_seed_name = "other seed"
    restarted._vitality_history_session = restarted._authenticated_session_key(ctx)
    assert restarted._prepare_receipts(ctx)
    assert not restarted._receipt_sounds.pending


@pytest.mark.asyncio
async def test_native_mailbox_hold_spacing_retry_and_scope_guard():
    sounds = ReceiptSounds()
    sounds.pending.extend((1, 2, 3))
    sounds.supported = True
    read, write = AsyncMock(), AsyncMock(return_value=True)

    async def pump(request, result, ready, frame):
        read.return_value = [pack("<III", request, result, ready), pack("<I", frame)]
        await sounds.pump(None, auth_offset=0xF00000, auth=b"test identity", frame_addr=0x0203B01C)

    with patch("worlds.kirbyam.receipt_sounds.bizhawk.read", read), \
         patch("worlds.kirbyam.receipt_sounds.bizhawk.guarded_write", write):
        await pump(0, 0, 0, 10)  # Menu/transition/mixer busy.
        assert write.await_count == 0
        await pump(0, 0, 14, 11)
        first = sounds.in_flight
        assert first == (11 << 2) | 1
        assert write.call_args.args[2][0] == (0xF00000, b"test identity", "ROM")
        assert unpack("<I", write.call_args.args[1][-1][1]) == (first,)
        await pump(first, 0, 0, 12)
        assert write.await_count == 1
        await pump(0, first | CUE_REJECTED, 0, 12)  # State changed before native start.
        assert list(sounds.pending) == [1, 2, 3]
        await pump(0, 0, 14, 20)
        second = sounds.in_flight
        await pump(0, second, 0, 21)  # Native start, but mixer still playing.
        assert list(sounds.pending) == [2, 3]
        assert write.await_count == 2
        await pump(0, 0, 14, 90)
        assert sounds.in_flight & 3 == 2
        await pump(0, 0, 0, 0)  # Reset/load erased in-flight evidence: do not duplicate.
        assert list(sounds.pending) == [3]


@pytest.mark.asyncio
async def test_old_rom_does_not_receive_audio_writes():
    sounds = ReceiptSounds()
    sounds.pending.append(1)
    with patch("worlds.kirbyam.receipt_sounds.bizhawk.read", AsyncMock(return_value=[bytes(8)])), \
         patch("worlds.kirbyam.receipt_sounds.bizhawk.guarded_write", AsyncMock()) as write:
        await sounds.pump(None, auth_offset=0xF00000, auth=b"test identity", frame_addr=0x0203B01C)
    assert sounds.supported is False and not sounds.pending
    write.assert_not_awaited()


def test_native_deadline_and_ready_mask(tmp_path):
    cc = which("cc")
    if cc is None:
        pytest.skip("native C test requires a host compiler")
    include = Path(__file__).parents[1] / "kirby_ap_payload"
    source = tmp_path / "receipt-cue.c"
    output = tmp_path / ("receipt-cue.exe" if os_name == "nt" else "receipt-cue")
    source.write_text(
        '#include <assert.h>\n#include "receipt_sound_runtime.h"\n'
        'int main(void) {\n'
        '  assert(ap_cue_request_valid((40u<<2)|1u, 42u, 2u));\n'
        '  assert(!ap_cue_request_valid((40u<<2)|1u, 42u, 4u));\n'
        '  assert(!ap_cue_request_valid((40u<<2)|3u, 49u, 8u));\n'
        '  assert(!ap_cue_request_valid((40u<<2)|3u, 39u, 8u));\n'
        '  assert(ap_cue_request_valid((AP_CUE_FRAME_MASK<<2)|2u, 3u, 4u));\n'
        '  assert(!ap_cue_request_valid(AP_CUE_REJECTED|1u, 0u, 2u));\n'
        '}\n', encoding="utf-8")
    run([cc, "-std=c99", "-Wall", "-Wextra", "-Werror", "-I", str(include),
         str(source), "-o", str(output)], check=True)
    run([str(output)], check=True)


def test_symbol_and_player_validation_is_fail_closed_on_the_synthetic_smoke_rom():
    dummy = run_path(str(Path(__file__).parents[1] / "tools" / "create_dummy_rom.py"))
    rom = dummy["build_dummy_rom"]()
    patch_rom.validate_receipt_sound_native_contract(rom)
    for offset, error in (
        (0x15011C, "m4aSongNumStart"),
        (0xB59ED0 + 0x227 * 8 + 4, "receipt song player"),
        (0xB59ED0 + 0x20D * 8 + 4, "receipt song player"),
        (0xB59ED0 + 0x251 * 8 + 4, "receipt song player"),
    ):
        rom[offset] ^= 1
        with pytest.raises(SystemExit, match=error):
            patch_rom.validate_receipt_sound_native_contract(rom)
        rom[offset] ^= 1
