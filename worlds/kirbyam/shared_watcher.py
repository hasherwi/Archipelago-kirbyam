"""Keep one async watcher tick bound to its authenticated native adventure epoch."""
import base64
import struct
from contextlib import contextmanager
from contextvars import ContextVar

import worlds._bizhawk as bizhawk
from .shared_save_protocol import SHARED_CONTEXT_ADDRESS


class SharedContextChanged(bizhawk.RequestFailedError):
    pass


_active = ContextVar('kirby_shared_watcher', default=None)


def _identity(ctx):
    server = getattr(ctx, 'server', None)
    return (ctx.auth, ctx.team, ctx.slot, getattr(ctx, 'server_seed_name', None),
            server, getattr(server, 'socket', None), ctx.bizhawk_ctx)


@contextmanager
def shared_watcher(ctx, snapshot):
    guard = None
    if snapshot is not None:
        guard = (ctx, _identity(ctx), [
            (SHARED_CONTEXT_ADDRESS, struct.pack('<3I', snapshot.epoch, snapshot.epoch, snapshot.slot), 'System Bus'),
            (0xF00000, base64.b64decode(ctx.auth, validate=True), 'ROM'),
        ])
    token = _active.set(guard)
    try:
        yield
    finally:
        _active.reset(token)


def _guard(connector):
    guard = _active.get()
    if guard is not None and (connector is not guard[1][-1] or _identity(guard[0]) != guard[1]):
        raise SharedContextChanged('shared_save_context_changed')
    return guard


async def _verify(connector, guard):
    # The bridge may have executed the request before a reset but delivered its
    # response afterward. Reject that old response before caller state advances.
    result = await bizhawk.guarded_read(connector, [], guard[2])
    _guard(connector)
    if result is None:
        raise SharedContextChanged('shared_save_context_changed')


async def read(connector, reads):
    guard = _guard(connector)
    if guard is None:
        return await bizhawk.read(connector, reads)
    result = await bizhawk.guarded_read(connector, reads, guard[2])
    _guard(connector)
    if result is None:
        raise SharedContextChanged('shared_save_context_changed')
    await _verify(connector, guard)
    return result


async def write(connector, writes):
    guard = _guard(connector)
    if guard is None:
        return await bizhawk.write(connector, writes)
    accepted = await bizhawk.guarded_write(connector, writes, guard[2])
    _guard(connector)
    if not accepted:
        raise SharedContextChanged('shared_save_context_changed')
    await _verify(connector, guard)


async def guarded_write(connector, writes, guards):
    guard = _guard(connector)
    if guard is None:
        return await bizhawk.guarded_write(connector, writes, guards)
    accepted = await bizhawk.guarded_write(connector, writes, [*guard[2], *guards])
    _guard(connector)
    # Preserve ordinary native guard failures, but abort a stale tick.
    await _verify(connector, guard)
    return accepted


async def send_msgs(ctx, messages):
    if _active.get() is not None:
        await read(ctx.bizhawk_ctx, [])
    await ctx.send_msgs(messages)
