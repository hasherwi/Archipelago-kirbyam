import asyncio
import base64
import struct
from types import SimpleNamespace

import pytest

from .. import goal_game_protocol as goals


def test_goal_protocol_requires_native_context_and_explicit_capability():
    assert goals.goal_slot_version({}) == 0
    assert goals.goal_slot_version({'goal_game_protocol_version': 2, 'copy_ability_room_protocol_version': 2}) == 2
    for value in (True, '2', 1, 3, None):
        with pytest.raises(ValueError):
            goals.goal_slot_version({'goal_game_protocol_version': value, 'copy_ability_room_protocol_version': 2})
    with pytest.raises(ValueError):
        goals.goal_slot_version({'goal_game_protocol_version': 2})


@pytest.mark.parametrize('mutation', ['none', 'epoch', 'auth', 'slot', 'socket', 'disconnect', 'slot_data', 'record_change', 'saved_auth', 'tag', 'native_slot'])
def test_checks_offline_reconnect_and_fenced_identity(monkeypatch, mutation):
    auth = bytes(range(16))
    ctx = SimpleNamespace(auth=base64.b64encode(auth).decode(), team=0, slot=1,
        server_seed_name='seed', server=SimpleNamespace(socket=SimpleNamespace(closed=False)),
        bizhawk_ctx=object(), slot_data={'goal_game_protocol_version': 2, 'copy_ability_room_protocol_version': 2},
        missing_locations=set(range(3960700, 3960716)), checked_locations=set())
    messages = []
    async def send(values):
        messages.extend(values)
    ctx.send_msgs = send
    raw = struct.pack('<9I', 4, 4, 0, 0, 0, 0x03001000, 1, 0x43504332, 0)
    record_auth = bytes(16) if mutation == 'saved_auth' else auth
    tag = 0x4151ffff if mutation == 'tag' else 0x4351ffff
    record = record_auth + struct.pack('<I', tag)
    if mutation == 'native_slot':
        raw = struct.pack('<9I', 4, 4, 3, 0, 3, 0x03001000, 1, 0x43504332, 0)
    count = 0
    async def read(*args):
        nonlocal count
        count += 1
        if count % 2:
            return [raw, record, auth]
        if mutation == 'slot': ctx.slot += 1
        if mutation == 'socket': ctx.server.socket = SimpleNamespace(closed=False)
        if mutation == 'disconnect': ctx.server.socket.closed = True
        if mutation == 'slot_data': ctx.slot_data = dict(ctx.slot_data)
        return [bytes(12) if mutation == 'epoch' else raw[:12], bytes(20) if mutation == 'record_change' else record, bytes(16) if mutation == 'auth' else auth]
    monkeypatch.setattr(goals.bizhawk, 'read', read)
    asyncio.run(goals.poll_goal_games(ctx))
    if mutation != 'none':
        assert messages == []
        return
    expected = {'cmd': 'LocationChecks', 'locations': list(range(3960700, 3960716))}
    assert messages == [expected]
    # Lost send/ACK: persistent bits are resent on a new connection, no queue needed.
    ctx.server.socket = SimpleNamespace(closed=False)
    asyncio.run(goals.poll_goal_games(ctx))
    assert messages == [expected, expected]
    ctx.checked_locations = set(expected['locations'])
    asyncio.run(goals.poll_goal_games(ctx))
    assert len(messages) == 2
    ctx.server.socket.closed = True
    ctx.checked_locations.clear()
    asyncio.run(goals.poll_goal_games(ctx))
    assert len(messages) == 2


@pytest.mark.parametrize('bit', range(16))
def test_each_completion_reports_exact_location_without_copy_room_ownership(monkeypatch, bit):
    auth = bytes(range(16))
    ctx = SimpleNamespace(auth=base64.b64encode(auth).decode(), team=0, slot=1,
        server_seed_name='seed', server=SimpleNamespace(socket=SimpleNamespace(closed=False)),
        bizhawk_ctx=object(), slot_data={'goal_game_protocol_version': 2, 'copy_ability_room_protocol_version': 2},
        missing_locations=set(range(3960700, 3960716)), checked_locations=set())
    messages = []

    async def send(values):
        messages.extend(values)

    ctx.send_msgs = send
    raw = struct.pack('<9I', 4, 4, 2, 0, 2, 0x03001000, 0, 0x43504332, 0)
    record = auth + struct.pack('<I', 0x43500000 | (1 << (bit + 1)))

    async def read(_ctx, requests):
        return [raw if requests[0][1] == 36 else raw[:12], record, auth]

    monkeypatch.setattr(goals.bizhawk, 'read', read)
    asyncio.run(goals.poll_goal_games(ctx))
    assert messages == [{'cmd': 'LocationChecks', 'locations': [3960700 + bit]}]
