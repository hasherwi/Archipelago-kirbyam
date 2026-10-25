"""Execute the real mailbox and hub dispatch against mapped host RAM."""
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any

import pytest

from ..data import data
from ..receipts import TRANSIENT_ITEM_IDS
from .test_runtime_regression_hooks import patch_rom
from .test_receipt_journal import receipt_env  # noqa: F401

PAYLOAD = Path(__file__).resolve().parents[1] / "kirby_ap_payload"


def test_hub_trap_catalog_and_receipt_policy() -> None:
    assert data.item_key_to_id["TRAP_HUB_TELEPORT"] == 3860300
    assert data.items[3860300].label == "Hub Teleport Trap"
    assert 3860300 in TRANSIENT_ITEM_IDS
    assert "Hub Teleport Trap" in data.available_trap_item_labels


def test_hub_hook_rejects_wrong_rom_without_mutation() -> None:
    rom = bytearray(0x1000000)
    before = bytes(rom)
    with pytest.raises(SystemExit, match="hub trap scheduler call"):
        patch_rom.build_hub_teleport_writes(rom, 0x0815E100)
    assert rom == before
    rom[0x151CF4:0x151CF8] = patch_rom.thumb_bl_bytes(0x08151CF4, 0x08152CF4)
    before = bytes(rom)
    with pytest.raises(SystemExit, match="native transition contract"):
        patch_rom.build_hub_teleport_writes(rom, 0x0815E100)
    assert rom == before


def test_actual_mailbox_and_hub_dispatch(tmp_path: Path) -> None:
    compiler = shutil.which("cc")
    if not sys.platform.startswith("linux") or not compiler:
        pytest.skip("requires Linux low-address memory mapping and C compiler")
    assert compiler is not None
    source = (PAYLOAD / "ap_payload.c").read_text()
    # Only platform calls/register bindings are substituted. All mailbox,
    # item effects, readiness guards and acknowledgement code run unchanged.
    source = re.sub(r'register uint32_t (\w+) asm\("r\d+"\);', r'uint32_t \1 = 0;', source)
    source = source.replace('((KirbyWorldPropsEntryFn)0x08002889u)', 'native_world_props')
    source = source.replace('((RoomSpawnFn)0x08002D41u)', 'native_spawn')
    source = source.replace('((RequestRoomFn)0x080551FDu)', 'native_request')
    source = source.replace('((void (*)(void))0x08152CF5u)', 'native_tasks')
    harness = (Path(__file__).parent / 'native/hub_teleport_host.c').read_text()
    source = harness.replace('/* PAYLOAD */', source)
    path = tmp_path / 'hub.c'
    path.write_text(source)
    exe = tmp_path / 'hub'
    built = subprocess.run([compiler, '-std=gnu99', '-O2', '-w', '-I', str(PAYLOAD),
                            str(path), '-o', str(exe)], capture_output=True, text=True)
    assert built.returncode == 0, built.stderr
    result = subprocess.run([str(exe)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


@pytest.mark.asyncio
async def test_deferred_hub_receipt_survives_timeout_in_order(receipt_env: Any) -> None:  # noqa: F811
    from unittest.mock import AsyncMock
    from NetUtils import NetworkItem
    from .test_receipt_journal import make_client, tick, drain
    from .test_reset_counter_gaps import Mailbox
    ctx = receipt_env
    ctx.items_received = [NetworkItem(3860300, 3960566, 1), NetworkItem(3860032, 3960567, 1)]
    client = make_client(ctx)  # type: ignore[no-untyped-call]  # Existing shared test helpers.
    box = Mailbox(client)  # type: ignore[no-untyped-call]  # Existing shared test helpers.
    display = AsyncMock()
    await tick(client, ctx, box, display)  # type: ignore[no-untyped-call]  # Existing shared test helpers.
    assert box.offers == [3860300]
    client._delivery_pending_frame = -100000
    client._delivery_pending_time = -100000.0
    for _ in range(5):
        await tick(client, ctx, box, display)  # type: ignore[no-untyped-call]  # Existing shared test helpers.
    assert box.offers == [3860300]
    assert client._delivery_pending
    assert client._delivered_item_index == 0
    assert box.memory[client._transport_addr('incoming_item_flag')] == (1).to_bytes(4, 'little')
    box.consume()  # type: ignore[no-untyped-call]  # Existing shared test helpers.
    await drain(client, ctx, box, display)  # type: ignore[no-untyped-call]  # Existing shared test helpers.
    assert box.applied == [3860300, 3860032]
    assert client._delivered_item_index == 2


def test_verified_hub_fixture_accepts_only_unmodified_contract() -> None:
    from .native.hub_transition_fixture import CONTRACT_BYTES, populate_hub_transition_fixture
    rom = bytearray(0x1000000)
    populate_hub_transition_fixture(rom)
    before = bytes(rom)
    target = 0x0815E100
    writes = patch_rom.build_hub_teleport_writes(rom, target)
    assert writes == {0x151CF4: patch_rom.thumb_bl_bytes(0x08151CF4, target)}
    assert rom == before
    for offset, original in CONTRACT_BYTES.items():
        for index in range(len(original)):
            rom[offset + index] ^= 1
            mutated = bytes(rom)
            with pytest.raises(SystemExit, match='native transition contract'):
                patch_rom.build_hub_teleport_writes(rom, target)
            assert rom == mutated
            rom[offset + index] ^= 1
    assert rom == before
