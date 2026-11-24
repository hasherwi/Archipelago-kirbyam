"""Random Teleport candidate authority excludes later receipts and physical visits."""

from unittest.mock import AsyncMock

import pytest
from BaseClasses import CollectionState
from NetUtils import NetworkItem
from test.general import setup_multiworld
from .. import KirbyAmWorld
from ..random_teleport import (
    RANDOM_TELEPORT_ITEM_ID, RANDOM_TELEPORT_NONCE_ADDR, RANDOM_TELEPORT_ROM_MARKER_OFFSET,
    teleport_nonce,
)
from ..receipts import receipt_key
from .test_receipt_journal import make_client, receipt_env, tick  # noqa: F401
from .test_reset_counter_gaps import Mailbox


@pytest.mark.parametrize("area_keys", [0, 1])
def test_candidate_routes_have_unconditional_central_root_and_owned_hub_edges(area_keys):
    mw = setup_multiworld(KirbyAmWorld, options={"area_keys": area_keys}, seed=696)
    world = mw.worlds[1]
    root = "REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE"
    hubs = {
        "REGION_RAINBOW_ROUTE/ROOM_1_HUB_1": "Rainbow Route East - Hub Connection",
        "REGION_RAINBOW_ROUTE/ROOM_1_HUB_2": "Rainbow Route South - Hub Connection",
        "REGION_RAINBOW_ROUTE/ROOM_1_HUB_3": "Rainbow Route West - Hub Connection",
    }
    for hub, item_name in hubs.items():
        state = CollectionState(mw)
        assert mw.get_region(root, 1).can_reach(state)
        state.collect(world.create_item(item_name), True)
        assert mw.get_region(hub, 1).can_reach(state)


@pytest.mark.asyncio
async def test_only_earlier_hub_receipts_admit_candidates(receipt_env):
    ctx = receipt_env
    # East is in the ACKed prefix. West exists in complete history, but
    # has not reached the native mailbox before Random Teleport.
    ctx.items_received = [
        NetworkItem(3860401, 3960566, 1, 1),
        NetworkItem(RANDOM_TELEPORT_ITEM_ID, 3960567, 1, 4),
        NetworkItem(3860405, 3960568, 1, 1),
    ]
    client = make_client(ctx)
    box = Mailbox(client, count=1, cursor=1)
    client._delivered_item_index = 1
    await tick(client, ctx, box, AsyncMock())
    request = int.from_bytes(box.memory[RANDOM_TELEPORT_NONCE_ADDR], "little")
    assert request >> 29 == 1
    assert request & 0x1FFFFFFF == teleport_nonce(client._receipt_scope, receipt_key(ctx.items_received, 1))
    assert box.offers == [RANDOM_TELEPORT_ITEM_ID]


@pytest.mark.asyncio
async def test_missing_marker_and_rejected_guard_never_reserve_or_offer(receipt_env):
    ctx = receipt_env
    ctx.items_received = [NetworkItem(RANDOM_TELEPORT_ITEM_ID, 3960566, 1, 4)]
    client = make_client(ctx)
    box = Mailbox(client)
    marker = box.memory.pop(RANDOM_TELEPORT_ROM_MARKER_OFFSET)
    await tick(client, ctx, box, AsyncMock())
    assert not box.offers and not client._receipt_journal.pending()
    assert "does not support Random Teleport" in client._receipt_error
    box.memory[RANDOM_TELEPORT_ROM_MARKER_OFFSET] = marker
    box.guarded_write = AsyncMock(return_value=False)
    await tick(client, ctx, box, AsyncMock())
    assert box.guarded_write.await_count == 1
    assert not box.offers and not client._receipt_journal.pending()


def test_native_source_admits_central_even_without_redundant_retreat_flag(tmp_path):
    """Exercise the same C predicate used by the production payload."""
    from pathlib import Path
    import shutil
    import subprocess

    cc = shutil.which("cc")
    if cc is None:
        pytest.skip("requires a C compiler")
    payload = Path(__file__).resolve().parents[1] / "kirby_ap_payload"
    source = tmp_path / "source.c"
    source.write_text("""
#include "random_teleport_runtime_logic.h"
int main(void) {
    return !ap_random_teleport_source_supported(801, 0, 0x19)
        || !ap_random_teleport_source_supported(190, 0, 0x79)
        || ap_random_teleport_source_supported(970, 0, 0x19)
        || ap_random_teleport_source_supported(801, 255, 0x19)
        || ap_random_teleport_source_supported(909, 10, 0x79);
}
""")
    executable = tmp_path / "source"
    subprocess.run([cc, "-std=c99", "-Wall", "-Werror", "-I", str(payload), str(source),
                    "-o", str(executable)], check=True)
    subprocess.run([str(executable)], check=True)
