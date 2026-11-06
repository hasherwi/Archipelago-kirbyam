import asyncio
import base64
import struct
from types import SimpleNamespace

import pytest

from .. import goal_game_protocol as goals, shared_save_protocol as shared


def test_goal_protocol_requires_shared_and_explicit_capability():
    assert goals.goal_slot_version({}) == 0
    assert goals.goal_slot_version({'goal_game_protocol_version': 1, 'shared_save_protocol_version': 1}) == 1
    for value in (True, '1', 2, None):
        with pytest.raises(ValueError):
            goals.goal_slot_version({'goal_game_protocol_version': value, 'shared_save_protocol_version': 1})
    with pytest.raises(ValueError):
        goals.goal_slot_version({'goal_game_protocol_version': 1})


@pytest.mark.parametrize('mutation', ['none', 'epoch', 'auth', 'slot', 'socket', 'disconnect', 'slot_data'])
def test_checks_offline_reconnect_and_fenced_identity(monkeypatch, mutation):
    auth = bytes(range(16))
    ctx = SimpleNamespace(auth=base64.b64encode(auth).decode(), team=0, slot=1,
        server_seed_name='seed', server=SimpleNamespace(socket=SimpleNamespace(closed=False)),
        bizhawk_ctx=object(), slot_data={'goal_game_protocol_version': 1, 'shared_save_protocol_version': 1},
        missing_locations=set(range(3960700, 3960716)), checked_locations=set())
    messages = []
    async def send(values):
        messages.extend(values)
    ctx.send_msgs = send
    raw = struct.pack('<9I', 4, 4, 0, 0, 0, 0x03001000, 0x3ffff, 0x41505331, 0)
    count = 0
    async def read(*args):
        nonlocal count
        count += 1
        if count % 2:
            return [raw, auth]
        if mutation == 'slot': ctx.slot += 1
        if mutation == 'socket': ctx.server.socket = SimpleNamespace(closed=False)
        if mutation == 'disconnect': ctx.server.socket.closed = True
        if mutation == 'slot_data': ctx.slot_data = dict(ctx.slot_data)
        return [bytes(12) if mutation == 'epoch' else raw[:12], bytes(16) if mutation == 'auth' else auth]
    monkeypatch.setattr(shared, 'read', read)
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
