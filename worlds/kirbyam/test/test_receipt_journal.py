"""Cold restarts, save restoration and uncertain delivery use receipt evidence."""
import sqlite3
from unittest.mock import AsyncMock, patch

import pytest
from NetUtils import NetworkItem
from ..client import KirbyAmClient, _build_kirbyam_command_processor
from ..receipts import ReceiptJournal, TRANSIENT_ITEM_IDS, receipt_key, scope_key
from .test_reset_counter_gaps import Mailbox


@pytest.fixture
def receipt_env(tmp_path, monkeypatch, mock_bizhawk_context):
    monkeypatch.setattr('worlds.kirbyam.client.Utils.user_path', lambda *args: str(tmp_path / 'receipts.sqlite3'))
    ctx = mock_bizhawk_context
    ctx.server_seed_name = 'receipt-test-seed'
    ctx.auth = 'test-rom-auth'
    ctx.items_received = []
    return ctx


def make_client(ctx, auth=b'1234567890abcdef'):
    client = KirbyAmClient()
    client.initialize_client()
    client._health_rom_auth = auth
    client._vitality_history_session = client._authenticated_session_key(ctx)
    ctx.client_handler = client
    return client


async def tick(client, ctx, box, display):
    with patch('worlds.kirbyam.client.bizhawk.read', side_effect=box.read), \
         patch('worlds.kirbyam.client.bizhawk.write', side_effect=box.write), \
         patch('worlds.kirbyam.client.bizhawk.display_message', display):
        await client._deliver_items(ctx)


async def drain(client, ctx, box, display):
    for _ in range(len(ctx.items_received) * 3 + 3):
        await tick(client, ctx, box, display)
        if box.memory[client._transport_addr('incoming_item_flag')] == (1).to_bytes(4, 'little'):
            box.consume()


@pytest.mark.asyncio
@pytest.mark.parametrize('item', sorted(TRANSIENT_ITEM_IDS) + [3860025, 3860018, 3860037, 3860003])
async def test_cold_restart_skips_transients_restores_ownership_silently(receipt_env, item):
    ctx = receipt_env
    ctx.items_received = [NetworkItem(item, 3960566, 1)]
    client = make_client(ctx)
    box = Mailbox(client)
    display = AsyncMock()
    await drain(client, ctx, box, display)
    assert box.applied == [item]
    assert display.await_count == 1
    client._receipt_journal.close()
    client = make_client(ctx)
    box = Mailbox(client)  # Native save restored; transport RAM is zero.
    display.reset_mock()
    await drain(client, ctx, box, display)
    assert box.applied == ([] if item in TRANSIENT_ITEM_IDS else [item])
    assert display.await_count == 0
    # A legitimate newly received copy still applies and notifies.
    ctx.items_received.append(NetworkItem(item, 3960567, 1))
    await drain(client, ctx, box, display)
    assert box.applied[-1:] == [item]
    assert display.await_count == 1


@pytest.mark.asyncio
@pytest.mark.parametrize('dimension', ['seed', 'slot', 'team', 'rom'])
async def test_receipts_never_cross_identity(receipt_env, dimension):
    ctx = receipt_env
    ctx.items_received = [NetworkItem(3860027, 3960566, 1)]
    client = make_client(ctx)
    await drain(client, ctx, Mailbox(client), AsyncMock())
    auth = b'1234567890abcdef'
    if dimension == 'seed':
        ctx.server_seed_name = 'different-seed'
    elif dimension == 'slot':
        ctx.slot = 2
    elif dimension == 'team':
        ctx.team = 1
    else:
        auth = b'fedcba0987654321'
    client = make_client(ctx, auth)
    box = Mailbox(client)
    display = AsyncMock()
    await drain(client, ctx, box, display)
    assert box.applied == [3860027]
    assert display.await_count == 1


@pytest.mark.asyncio
@pytest.mark.parametrize('consumed', [False, True])
@pytest.mark.parametrize('decision', ['received', 'retry'])
async def test_crash_window_pauses_even_when_counter_looks_acknowledged(receipt_env, consumed, decision):
    ctx = receipt_env
    ctx.items_received = [NetworkItem(3860026, 3960566, 1)]
    client = make_client(ctx)
    box = Mailbox(client)
    display = AsyncMock()
    await tick(client, ctx, box, display)
    assert box.offers == [3860026]
    if consumed:
        box.consume()  # Crash before client can record ACK.
    client = make_client(ctx)
    box.client = client
    box.offers = []
    for _ in range(3):
        await tick(client, ctx, box, display)
    assert not box.offers
    assert client._receipt_blocked

    class Commands:
        def __init__(self):
            self.ctx = ctx
            self.output = lambda message: None

    command = _build_kirbyam_command_processor(Commands)()
    assert command._cmd_receipt(decision)
    # A live mailbox must not be overridden by a recovery command.
    if not consumed:
        await tick(client, ctx, box, display)
        assert client._receipt_blocked
    box = Mailbox(client)  # Explicit native-save restart, not a guessed ACK.
    await drain(client, ctx, box, display)
    assert box.applied == ([3860026] if decision == 'retry' else [])


@pytest.mark.asyncio
async def test_same_client_reset_and_network_reconnect_preserve_receipts(receipt_env):
    ctx = receipt_env
    ctx.items_received = [NetworkItem(3860027, 1, 1), NetworkItem(3860025, 2, 1)]
    client = make_client(ctx)
    box = Mailbox(client)
    display = AsyncMock()
    await drain(client, ctx, box, display)
    client._reset_reconnect_transient_state()
    await drain(client, ctx, box, display)
    assert box.applied == [3860027, 3860025]
    box = Mailbox(client)
    await drain(client, ctx, box, display)
    assert box.applied == [3860025]
    assert display.await_count == 2


@pytest.mark.asyncio
async def test_failed_journal_write_blocks_mailbox(receipt_env):
    ctx = receipt_env
    ctx.items_received = [NetworkItem(3860026, 1, 1)]
    client = make_client(ctx)
    box = Mailbox(client)
    with patch.object(ReceiptJournal, 'reserve', side_effect=sqlite3.OperationalError('disk full')):
        await tick(client, ctx, box, AsyncMock())
    assert not box.offers


@pytest.mark.asyncio
async def test_journal_requires_index_zero_authority(receipt_env):
    ctx = receipt_env
    ctx.items_received = [NetworkItem(3860026, 1, 1)]
    client = make_client(ctx)
    client._vitality_history_session = None
    box = Mailbox(client)
    await tick(client, ctx, box, AsyncMock())
    assert not box.offers
    client.on_package(ctx, 'ReceivedItems', {'index': 0})
    await drain(client, ctx, box, AsyncMock())
    assert box.applied == [3860026]


def test_identity_survives_start_inventory_prefix_and_distinguishes_duplicates():
    item = NetworkItem(3860027, 42, 1)
    prefix = NetworkItem(3860018, -2, 0)
    assert receipt_key([item], 0) == receipt_key([prefix, item], 1)
    assert receipt_key([prefix, prefix], 0) != receipt_key([prefix, prefix], 1)
    assert scope_key('seed', bytes(16), 0, 1) != scope_key('seed', bytes(16), 1, 1)


def test_atomic_reservation_between_clients(tmp_path):
    path = str(tmp_path / 'receipts.sqlite3')
    first, second = ReceiptJournal(path, 'scope'), ReceiptJournal(path, 'scope')
    assert first.reserve('receipt')
    assert not second.reserve('receipt')
    assert second.pending() == ['receipt']
    first.acknowledge('receipt')
    assert second.acknowledged('receipt')
    assert first.claim_notice('receipt')
    assert not second.claim_notice('receipt')
    first.close()
    second.close()


@pytest.mark.asyncio
async def test_revalidation_keeps_durable_evidence_and_distinct_duplicate_receipts(receipt_env):
    ctx = receipt_env
    item = NetworkItem(3860027, 42, 1)
    ctx.items_received = [item, item]
    client = make_client(ctx)
    box = Mailbox(client)
    display = AsyncMock()
    await drain(client, ctx, box, display)
    assert box.applied == [3860027, 3860027]
    client.initialize_client()  # Same object, as used by ROM revalidation.
    client._health_rom_auth = b'1234567890abcdef'
    client.on_package(ctx, 'ReceivedItems', {'index': 0})
    box = Mailbox(client)
    await drain(client, ctx, box, display)
    assert not box.applied
    assert display.await_count == 2


@pytest.mark.asyncio
async def test_corrupt_journal_never_silently_falls_back_to_replay(receipt_env, tmp_path):
    (tmp_path / 'receipts.sqlite3').write_bytes(b'not a sqlite database')
    ctx = receipt_env
    ctx.items_received = [NetworkItem(3860027, 42, 1)]
    client = make_client(ctx)
    box = Mailbox(client)
    await tick(client, ctx, box, AsyncMock())
    assert not box.offers
    assert 'journal unavailable' in client._receipt_error


@pytest.mark.asyncio
async def test_ack_storage_failure_retains_pending_until_commit_succeeds(receipt_env):
    ctx = receipt_env
    ctx.items_received = [NetworkItem(3860027, 42, 1)]
    client = make_client(ctx)
    box = Mailbox(client)
    display = AsyncMock()
    await tick(client, ctx, box, display)
    box.consume()
    with patch.object(ReceiptJournal, 'acknowledge', side_effect=sqlite3.OperationalError('disk full')):
        await tick(client, ctx, box, display)
    assert client._delivery_pending
    assert client._delivered_item_index == 0
    assert display.await_count == 0
    await drain(client, ctx, box, display)
    assert box.applied == [3860027]
    assert display.await_count == 1


@pytest.mark.asyncio
async def test_scope_change_on_same_handler_does_not_reuse_index_sets(receipt_env):
    ctx = receipt_env
    ctx.items_received = [NetworkItem(3860027, 42, 1)]
    client = make_client(ctx)
    display = AsyncMock()
    await drain(client, ctx, Mailbox(client), display)
    ctx.slot = 2
    client.on_package(ctx, 'ReceivedItems', {'index': 0})
    box = Mailbox(client)
    await drain(client, ctx, box, display)
    assert box.applied == [3860027]
    assert display.await_count == 2


def test_permanent_sound_player_never_inherits_filler_replay_policy():
    assert 3860025 not in TRANSIENT_ITEM_IDS
    assert not KirbyAmClient._is_non_redeliverable_item(3860025)


@pytest.mark.asyncio
async def test_changed_history_cannot_ack_a_different_receipt(receipt_env):
    ctx = receipt_env
    ctx.items_received = [NetworkItem(3860027, 42, 1)]
    client = make_client(ctx)
    box = Mailbox(client)
    await tick(client, ctx, box, AsyncMock())
    box.consume()
    ctx.items_received = [NetworkItem(3860026, 43, 1)]
    await tick(client, ctx, box, AsyncMock())
    assert client._delivered_item_index == 0
    assert 'history changed' in client._receipt_error
    assert not client._receipt_journal.acknowledged(receipt_key(ctx.items_received, 0))


@pytest.mark.asyncio
async def test_disabled_notifications_do_not_reappear_on_later_restore(receipt_env):
    ctx = receipt_env
    ctx.items_received = [NetworkItem(3860025, 42, 1)]
    client = make_client(ctx)
    client._receive_notifications_enabled = False
    display = AsyncMock()
    await drain(client, ctx, Mailbox(client), display)
    assert display.await_count == 0
    client = make_client(ctx)
    await drain(client, ctx, Mailbox(client), display)
    assert display.await_count == 0


def test_all_existing_consumable_and_trap_tags_have_explicit_delivery_policy():
    from ..data import data
    transient = {item.item_id for item in data.items.values()
                 if {'Consumable', 'Life', 'Trap'} & set(item.tags)}
    assert transient <= TRANSIENT_ITEM_IDS
    assert {3860035, 3860036} <= TRANSIENT_ITEM_IDS


@pytest.mark.asyncio
async def test_session_change_during_bridge_read_prevents_delivery(receipt_env):
    ctx = receipt_env
    ctx.items_received = [NetworkItem(3860027, 42, 1)]
    client = make_client(ctx)
    box = Mailbox(client)
    original_read = box.read
    async def changed_session(*args):
        values = await original_read(*args)
        ctx.slot = 2
        return values
    box.read = changed_session
    await tick(client, ctx, box, AsyncMock())
    assert not box.offers


@pytest.mark.asyncio
async def test_reused_history_index_does_not_suppress_a_different_receipt(receipt_env):
    ctx = receipt_env
    ctx.items_received = [NetworkItem(3860027, 42, 1)]
    client = make_client(ctx)
    display = AsyncMock()
    await drain(client, ctx, Mailbox(client), display)
    ctx.items_received = [NetworkItem(3860027, 43, 1)]
    client.on_package(ctx, 'ReceivedItems', {'index': 0})
    box = Mailbox(client)
    await drain(client, ctx, box, display)
    assert box.applied == [3860027]
    assert display.await_count == 2
