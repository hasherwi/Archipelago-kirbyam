"""Server item-history snapshots include an explicit empty inventory."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

import MultiServer


class _Client:
    def __init__(self, *, auth: bool = False, items_handling: int = 1) -> None:
        self.auth = auth
        self.team = None if not auth else 0
        self.slot = None if not auth else 0
        self.version = MultiServer.no_version
        self.tags: set[str] = set()
        self.no_locations = False
        self.no_text = False
        self.no_items = False
        self.remote_items = False
        self.remote_start_inventory = False
        self.send_index = 9
        self.items_handling = items_handling

    @property
    def items_handling(self) -> int:
        if self.no_items:
            return 0
        return 1 + (self.remote_items << 1) + (self.remote_start_inventory << 2)

    @items_handling.setter
    def items_handling(self, value: int) -> None:
        self.no_items = not (value & 0b001)
        self.remote_items = bool(value & 0b010)
        self.remote_start_inventory = bool(value & 0b100)


@pytest.mark.asyncio
async def test_connect_sends_index_zero_for_a_new_empty_slot() -> None:
    client = _Client()
    ctx = SimpleNamespace(
        password=None,
        connect_names={"Kirby": (0, 0)},
        games={0: "KirbyAM"},
        minimum_client_versions={0: MultiServer.min_client_version},
        compatibility=0,
        clients={0: {0: []}},
        client_ids={},
        slot_info={},
        slot_data={0: {"test": True}},
        start_inventory={},
        received_items={},
        send_msgs=AsyncMock(),
        get_players_package=Mock(return_value=[]),
        logger=Mock(),
    )
    args = {
        "cmd": "Connect",
        "password": None,
        "name": "Kirby",
        "game": "KirbyAM",
        "version": MultiServer.version_tuple,
        "tags": set(),
        "items_handling": 1,
        "uuid": "empty-slot-client",
    }

    with (
        patch.object(MultiServer, "get_missing_checks", return_value=[]),
        patch.object(MultiServer, "get_checked_checks", return_value=[]),
        patch.object(MultiServer, "get_slot_points", return_value=0),
        patch.object(MultiServer, "on_client_joined", new_callable=AsyncMock),
    ):
        await MultiServer.process_client_cmd(ctx, client, args)

    sent = ctx.send_msgs.await_args.args[1]
    assert sent[-1] == {"cmd": "ReceivedItems", "index": 0, "items": []}
    assert client.send_index == 0

    # Feed the actual server response to KirbyAM's package handler, so a fresh
    # empty history is distinguished from the empty list before replay starts.
    from worlds.kirbyam.client import KirbyAmClient

    game_client = KirbyAmClient()
    game_client.initialize_client()
    game_client._notification_settings_loaded = True
    socket = SimpleNamespace(closed=False)
    game_ctx = SimpleNamespace(
        server=SimpleNamespace(socket=socket),
        items_received=[],
    )
    game_client.on_package(game_ctx, sent[-1]["cmd"], sent[-1])
    assert game_client._hub_connection_item_history_ready(game_ctx) is True


@pytest.mark.asyncio
async def test_sync_sends_index_zero_for_an_empty_inventory() -> None:
    client = _Client(auth=True)
    client.send_index = 9
    ctx = SimpleNamespace(start_inventory={}, received_items={}, send_msgs=AsyncMock())

    await MultiServer.process_client_cmd(ctx, client, {"cmd": "Sync"})

    ctx.send_msgs.assert_awaited_once_with(
        client,
        [{"cmd": "ReceivedItems", "index": 0, "items": []}],
    )
    assert client.send_index == 0


@pytest.mark.asyncio
async def test_sync_does_not_send_items_to_no_items_clients() -> None:
    client = _Client(auth=True, items_handling=0)
    ctx = SimpleNamespace(start_inventory={}, received_items={}, send_msgs=AsyncMock())

    await MultiServer.process_client_cmd(ctx, client, {"cmd": "Sync"})

    ctx.send_msgs.assert_not_awaited()


@pytest.mark.asyncio
async def test_connect_update_sends_index_zero_when_reenabling_empty_inventory() -> None:
    client = _Client(auth=True, items_handling=0)
    ctx = SimpleNamespace(start_inventory={}, received_items={}, send_msgs=AsyncMock())

    await MultiServer.process_client_cmd(
        ctx,
        client,
        {"cmd": "ConnectUpdate", "items_handling": 1},
    )

    ctx.send_msgs.assert_awaited_once_with(
        client,
        [{"cmd": "ReceivedItems", "index": 0, "items": []}],
    )
    assert client.send_index == 0
