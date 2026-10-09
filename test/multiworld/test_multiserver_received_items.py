"""Integration coverage for the standard server's item-history Connect batch."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

import CommonClient
import MultiServer


class _Client:
    def __init__(self) -> None:
        self.auth = False
        self.team = None
        self.slot = None
        self.version = MultiServer.no_version
        self.tags: set[str] = set()
        self.no_locations = False
        self.no_text = False
        self.no_items = False
        self.remote_items = False
        self.remote_start_inventory = False
        self.send_index = 0
        self.items_handling = 1

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


async def _standard_connect_batch(received_items=()):
    server_client = _Client()
    server_ctx = SimpleNamespace(
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
        received_items={(0, 0, False): list(received_items)},
        send_msgs=AsyncMock(),
        get_players_package=Mock(return_value=[]),
        logger=Mock(),
    )
    connect = {
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
        await MultiServer.process_client_cmd(server_ctx, server_client, connect)

    return server_ctx.send_msgs.await_args.args[1]


def _game_client_context(game_client, socket, items_received):
    game_ctx = SimpleNamespace(
        server=SimpleNamespace(socket=socket),
        bizhawk_ctx=SimpleNamespace(_send_message=AsyncMock()),
        items_received=items_received,
        auth="Kirby",
        team=0,
        slot=0,
        slot_info={},
        hint_points=0,
        consume_players_package=Mock(),
        stored_data_notification_keys=set(),
        game="Kirby & The Amazing Mirror",
        locations_checked=set(),
        locations_scouted=set(),
        send_msgs=AsyncMock(),
        finished_game=False,
        missing_locations=set(),
        checked_locations=set(),
        server_locations=set(),
        server_address="ws://localhost:38281",
        watcher_event=asyncio.Event(),
    )

    def on_package(cmd, args):
        if cmd == "Connected":
            game_ctx.slot_data = args.get("slot_data")
        game_client.on_package(game_ctx, cmd, args)

    game_ctx.on_package = on_package
    return game_ctx


@pytest.mark.asyncio
async def test_standard_empty_connect_batch_marks_reconnect_inventory_empty() -> None:
    """An empty standard-server Connect has Connected and no ReceivedItems packet."""
    connect_batch = await _standard_connect_batch()
    assert [packet["cmd"] for packet in connect_batch] == ["Connected"]

    # Model reconnecting with stale items still held by CommonClient. The new
    # socket must stay unknown until the Connected batch has fully drained.
    from worlds.kirbyam.client import KirbyAmClient

    game_client = KirbyAmClient()
    game_client.initialize_client()
    game_client._notification_settings_loaded = True
    old_socket = SimpleNamespace(closed=False)
    new_socket = SimpleNamespace(closed=False)
    game_ctx = _game_client_context(
        game_client,
        old_socket,
        [SimpleNamespace(item=3860041, player=1)],
    )
    game_client.on_package(game_ctx, "ReceivedItems", {"index": 0})
    game_ctx.server.socket = new_socket

    with patch("worlds.kirbyam.client.bizhawk.write", new_callable=AsyncMock) as write:
        await game_client._sync_hub_connection_item_ownership(game_ctx)
        assert write.await_args.args[1][0][1] == (0xFFFFFFFF).to_bytes(4, "little")

        with patch("CommonClient.Utils.persistent_store"):
            for packet in connect_batch:
                await CommonClient.process_server_cmd(game_ctx, packet)
        assert game_client._hub_connection_item_history_ready(game_ctx) is False

        # The scheduled fallback runs after CommonClient has processed all
        # packets in this websocket batch. No ReceivedItems means known empty.
        await asyncio.sleep(0)
        assert game_client._hub_connection_item_history_ready(game_ctx) is True
        assert game_ctx.items_received == []

        await game_client._sync_hub_connection_item_ownership(game_ctx)
        assert write.await_args.args[1][0][1] == (0).to_bytes(4, "little")


@pytest.mark.asyncio
async def test_received_items_in_connect_batch_cancels_empty_fallback() -> None:
    """The standard non-empty Connect batch replays items before the fallback."""
    item = MultiServer.NetworkItem(3860042, -1, 1)
    connect_batch = await _standard_connect_batch([item])
    assert [packet["cmd"] for packet in connect_batch] == ["Connected", "ReceivedItems"]
    item_packet = connect_batch[1]
    assert item_packet["index"] == 0

    from worlds.kirbyam.client import KirbyAmClient

    game_client = KirbyAmClient()
    game_client.initialize_client()
    game_client._notification_settings_loaded = True
    socket = SimpleNamespace(closed=False)
    game_ctx = _game_client_context(game_client, socket, [SimpleNamespace(item=3860041, player=1)])

    with patch("CommonClient.Utils.persistent_store"):
        for packet in connect_batch:
            await CommonClient.process_server_cmd(game_ctx, packet)
    await asyncio.sleep(0)

    assert game_client._hub_connection_item_history_ready(game_ctx) is True
    assert game_ctx.items_received[0].item == 3860042
