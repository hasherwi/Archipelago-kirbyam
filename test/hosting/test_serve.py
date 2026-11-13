"""Deterministic lifecycle tests for the local hosting test helper."""
import asyncio
import multiprocessing
import pickle
import socket
import struct
import threading
import time
from multiprocessing.connection import Connection
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any, cast
from unittest.mock import Mock

import pytest

from . import serve


def _fake_server_module(monkeypatch: pytest.MonkeyPatch, *, fail: bool = False) -> tuple[Any, ...]:
    release = asyncio.Event()
    listening = Mock()
    listening.server = None
    listening.sockets = None
    listening.is_serving.return_value = False
    closed = asyncio.Event()

    async def wait_closed() -> None:
        closed.set()

    listening.wait_closed = wait_closed
    contexts: list[Any] = []

    class Context:
        def __init__(self) -> None:
            self.server = SimpleNamespace(ws_server=listening)
            self.exit_event = asyncio.Event()
            self.commandprocessor = SimpleNamespace(_cmd_exit=self.exit_event.set)
            contexts.append(self)

    async def main(args: Any) -> None:
        context = Context()
        if fail:
            raise OSError(10048, 'occupied test port')
        await release.wait()
        listening.server = object()
        listening.sockets = [SimpleNamespace(getsockname=lambda: ('127.0.0.1', 45678))]
        listening.is_serving.return_value = True
        await context.exit_event.wait()

    module = ModuleType('MultiServer')
    setattr(module, 'Context', Context)
    setattr(module, 'main', main)
    monkeypatch.setitem(sys.modules, 'MultiServer', module)
    return release, listening, closed, contexts, Context


def test_readiness_requires_actual_bound_listener_and_restores_observer(monkeypatch: pytest.MonkeyPatch) -> None:
    async def scenario() -> None:
        release, listener, closed, contexts, context_type = _fake_server_module(monkeypatch)
        original_init = context_type.__init__
        messages: list[tuple[str, int]] = []
        ready = asyncio.Event()

        def send(message: tuple[str, int]) -> None:
            messages.append(message)
            ready.set()

        stop = asyncio.Event()
        task = asyncio.create_task(serve._run_multiserver(None, cast(Any, SimpleNamespace(send=send)), cast(Any, stop)))
        await asyncio.sleep(0.03)  # longer than the old guessed readiness sleep
        assert messages == []
        release.set()
        await asyncio.wait_for(ready.wait(), 1)
        assert messages == [('ready', 45678)]
        stop.set()
        await asyncio.wait_for(task, 1)
        assert contexts[0].exit_event.is_set() and closed.is_set()
        listener.close.assert_called_once()
        assert context_type.__init__ is original_init

    asyncio.run(scenario())


def test_bind_failure_cancels_readiness_and_stop_tasks(monkeypatch: pytest.MonkeyPatch) -> None:
    async def scenario() -> None:
        _, listener, _, contexts, context_type = _fake_server_module(monkeypatch, fail=True)
        original_init = context_type.__init__
        status = Mock()
        with pytest.raises(OSError, match='occupied test port'):
            await serve._run_multiserver(None, status, cast(Any, asyncio.Event()))
        status.send.assert_not_called()
        listener.close.assert_not_called()
        assert contexts[0].exit_event.is_set()
        assert context_type.__init__ is original_init
        assert not [task for task in asyncio.all_tasks() if task is not asyncio.current_task() and not task.done()]

    asyncio.run(scenario())


def test_child_reports_startup_error_and_restores_argv(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    original_argv = sys.argv
    captured: list[str] = []

    def parse_args() -> None:
        captured.extend(sys.argv)
        raise OSError('deterministic startup failure')

    module = ModuleType('MultiServer')
    setattr(module, 'parse_args', parse_args)
    monkeypatch.setitem(sys.modules, 'MultiServer', module)
    status = Mock()
    with pytest.raises(OSError, match='deterministic startup failure'):
        serve._launch_multiserver(tmp_path / 'game.zip', status, Mock())
    assert captured[-4:] == ['--host', '127.0.0.1', '--port', '0']
    kind, message = status.send.call_args.args[0]
    assert kind == 'error' and 'deterministic startup failure' in message
    status.close.assert_called_once()
    assert sys.argv is original_argv


@pytest.mark.parametrize('message', [('ready', 43210), ('ready', 0), ('ready', True),
                                     ('ready', 65536), ('ready', '38281'), ('error', 'bind failed')])
def test_startup_channel_validates_readiness_or_propagates_error(tmp_path: Path, message: tuple[str, Any]) -> None:
    receiver, sender = multiprocessing.Pipe(duplex=False)
    host = serve.LocalServeGame(tmp_path / 'game.zip', startup_timeout=1)
    host._status = receiver
    host._proc = cast(Any, SimpleNamespace(exitcode=None))
    try:
        sender.send(message)
        if message == ('ready', 43210):
            assert host._wait_ready() == '127.0.0.1:43210'
        else:
            with pytest.raises(RuntimeError, match='bind failed' if message[0] == 'error' else 'Invalid'):
                host._wait_ready()
    finally:
        sender.close()
        if host._reader is not None:
            host._reader.join(5)
            assert not host._reader.is_alive()
        assert receiver.closed


def test_child_exit_and_closed_channel_are_not_readiness(tmp_path: Path) -> None:
    receiver, sender = multiprocessing.Pipe(duplex=False)
    host = serve.LocalServeGame(tmp_path / 'game.zip', startup_timeout=1)
    host._status = receiver
    host._proc = cast(Any, SimpleNamespace(exitcode=7))
    try:
        with pytest.raises(RuntimeError, match='exit code 7'):
            host._wait_ready()
        sender.close()
        with pytest.raises(RuntimeError, match='closed its startup channel'):
            host._wait_ready()
    finally:
        sender.close()
        if host._reader is not None:
            host._reader.join(5)
            assert not host._reader.is_alive()
        assert receiver.closed


def test_start_failure_closes_ipc_without_joining_unstarted_child(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    receiver, sender = multiprocessing.Pipe(duplex=False)
    process = Mock(pid=None)
    process.start.side_effect = OSError('spawn failed')
    context = Mock()
    context.Pipe.return_value = (receiver, sender)
    context.Process.return_value = process
    method_requests: list[str] = []

    def get_context(method: str) -> Any:
        method_requests.append(method)
        return context

    monkeypatch.setattr(multiprocessing, 'get_context', get_context)
    forbidden = Mock(side_effect=AssertionError('global start method changed'))
    monkeypatch.setattr(multiprocessing, 'set_start_method', forbidden)
    host = serve.LocalServeGame(tmp_path / 'game.zip')
    with pytest.raises(OSError, match='spawn failed'):
        host.__enter__()
    assert method_requests == ['spawn']
    forbidden.assert_not_called()
    process.join.assert_not_called()
    process.close.assert_called_once()
    assert receiver.closed and sender.closed
    assert host._proc is None and host._status is None and host._stop is None


@pytest.mark.parametrize('needs_kill', [False, True])
def test_join_timeout_reaps_child_and_surfaces_abnormal_exit(tmp_path: Path, needs_kill: bool) -> None:
    process = Mock(pid=123, exitcode=-9 if needs_kill else -15)
    process.is_alive.side_effect = [True, needs_kill, False, False]
    host = serve.LocalServeGame(tmp_path / 'game.zip', shutdown_timeout=0.01)
    host._proc = process
    stop = Mock()
    host._stop = stop
    with pytest.raises(RuntimeError, match='Local MultiServer failed'):
        host.__exit__(None, None, None)
    stop.set.assert_called_once()
    process.terminate.assert_called_once()
    assert process.kill.call_count == int(needs_kill)
    assert process.join.call_args_list[0].args == (0.01,)
    process.close.assert_called_once()
    assert host._proc is None and host._stop is None


def test_outer_failure_is_preserved_while_cleanup_reaps_child(tmp_path: Path) -> None:
    host = serve.LocalServeGame(tmp_path / 'game.zip')
    process = Mock(pid=123, exitcode=1)
    process.is_alive.return_value = False
    host._proc = process
    host.__exit__(AssertionError, AssertionError('original test failure'), None)
    process.close.assert_called_once()
    assert host._proc is None


def test_startup_timeout_uses_cleanup(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    receiver, sender = multiprocessing.Pipe(duplex=False)
    process = Mock(pid=123, exitcode=0)
    process.is_alive.return_value = False
    context = Mock()
    context.Pipe.return_value = (receiver, sender)
    context.Process.return_value = process
    monkeypatch.setattr(multiprocessing, 'get_context', lambda method: context)
    host = serve.LocalServeGame(tmp_path / 'game.zip', startup_timeout=0)
    with pytest.raises(TimeoutError, match='listener'):
        host.__enter__()
    process.join.assert_called_once()
    process.close.assert_called_once()
    assert receiver.closed and sender.closed and host._proc is None


def test_real_missing_archive_reports_child_failure_and_reaps_it(tmp_path: Path) -> None:
    host = serve.LocalServeGame(tmp_path / 'missing.archipelago', startup_timeout=30, shutdown_timeout=2)
    with pytest.raises(RuntimeError, match='startup failed') as failure:
        host.__enter__()
    assert 'missing.archipelago' in str(failure.value)
    assert host._exitcode not in (None, 0)
    assert host._proc is None and host._status is None and host._stop is None


@pytest.mark.parametrize('stage', ['Event', 'Process'])
def test_child_setup_failure_closes_ipc(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, stage: str,
) -> None:
    receiver, sender = multiprocessing.Pipe(duplex=False)
    context = Mock()
    context.Pipe.return_value = (receiver, sender)
    getattr(context, stage).side_effect = OSError('setup failed')
    monkeypatch.setattr(multiprocessing, 'get_context', lambda method: context)
    host = serve.LocalServeGame(tmp_path / 'game.zip')
    with pytest.raises(OSError, match='setup failed'):
        host.__enter__()
    assert receiver.closed and sender.closed
    assert host._proc is None and host._status is None and host._stop is None


def test_shutdown_surfaces_reported_child_error_and_closes_channel(tmp_path: Path) -> None:
    receiver, sender = multiprocessing.Pipe(duplex=False)
    host = serve.LocalServeGame(tmp_path / 'game.zip')
    host._status = receiver
    process = Mock(pid=123, exitcode=0)
    process.is_alive.return_value = False
    host._proc = process
    sender.send(('error', 'child runtime failure'))
    sender.close()
    with pytest.raises(RuntimeError, match='child runtime failure'):
        host.__exit__(None, None, None)
    assert receiver.closed and host._proc is None
    process.close.assert_called_once()


def _send_large_error_after_stop(sender: Connection, stop: Any, ready: Any) -> None:
    ready.set()
    stop.wait()
    try:
        sender.send(('error', 'large child error: ' + 'é' * 1_000_000))
    except (BrokenPipeError, OSError):
        pass  # the bounded receiver rejects this intentionally invalid frame
    finally:
        sender.close()


def _send_partial_frame(sender: socket.socket, ready: Any, stall: bool) -> None:
    try:
        sender.sendall(struct.pack('!i', 100) + b'partial')
        ready.set()
        if stall:
            while True:
                time.sleep(1)  # deliberately uncooperative child; parent must terminate it
    finally:
        sender.close()


def _assert_host_reaped(host: serve.LocalServeGame, process: Any, receiver: Connection) -> None:
    assert process._closed  # owned Process.close receipt, not a cross-process /proc inference
    assert receiver.closed
    assert host._proc is None and host._status is None and host._stop is None and host._reader is None


def _emergency_reap(process: Any) -> None:
    if not process._closed:
        if process.is_alive():
            process.kill()
        process.join(5)
        process.close()


@pytest.mark.parametrize('outer_failure', [False, True])
def test_real_oversized_child_error_is_bounded_and_cleanup_preserves_outer(
    tmp_path: Path, outer_failure: bool,
) -> None:
    context = multiprocessing.get_context('spawn')
    receiver, sender = context.Pipe(duplex=False)
    stop, ready = context.Event(), context.Event()
    process = context.Process(target=_send_large_error_after_stop, args=(sender, stop, ready))
    process.start()
    sender.close()
    host = serve.LocalServeGame(tmp_path / 'unused', shutdown_timeout=0.1)
    host._proc, host._status, host._stop = process, receiver, stop
    try:
        assert ready.wait(10)
        if outer_failure:
            original = AssertionError('original outer test failure')
            with pytest.raises(AssertionError) as caught:
                try:
                    raise original
                finally:
                    host.__exit__(*sys.exc_info())
            assert caught.value is original
        else:
            with pytest.raises(RuntimeError, match='status channel failed'):
                host.__exit__(None, None, None)
        _assert_host_reaped(host, process, receiver)
    finally:
        _emergency_reap(process)


@pytest.mark.parametrize('outer_failure', [False, True])
def test_real_truncated_frame_already_pending_cannot_skip_cleanup(
    tmp_path: Path, outer_failure: bool,
) -> None:
    context = multiprocessing.get_context('spawn')
    incoming, outgoing = socket.socketpair()
    receiver = Connection(incoming.detach(), readable=True, writable=False)
    ready = context.Event()
    process = context.Process(target=_send_partial_frame, args=(outgoing, ready, False))
    process.start()
    outgoing.close()
    host = serve.LocalServeGame(tmp_path / 'unused', shutdown_timeout=0.1)
    host._proc, host._status, host._stop = process, receiver, context.Event()
    try:
        assert ready.wait(10)
        process.join(5)
        assert not process.is_alive() and receiver.poll()
        if outer_failure:
            original = AssertionError('preserve pending-frame outer failure')
            with pytest.raises(AssertionError) as caught:
                try:
                    raise original
                finally:
                    host.__exit__(*sys.exc_info())
            assert caught.value is original
        else:
            with pytest.raises(RuntimeError, match='status channel failed'):
                host.__exit__(None, None, None)
        _assert_host_reaped(host, process, receiver)
    finally:
        _emergency_reap(process)


def test_stalled_partial_frame_cannot_defeat_startup_timeout_or_cleanup(tmp_path: Path) -> None:
    context = multiprocessing.get_context('spawn')
    incoming, outgoing = socket.socketpair()
    receiver = Connection(incoming.detach(), readable=True, writable=False)
    ready = context.Event()
    process = context.Process(target=_send_partial_frame, args=(outgoing, ready, True))
    process.start()
    outgoing.close()
    host = serve.LocalServeGame(tmp_path / 'unused', startup_timeout=0.1, shutdown_timeout=0.1)
    host._proc, host._status, host._stop = process, receiver, context.Event()
    failures: list[BaseException] = []
    finished = threading.Event()

    def wait_ready() -> None:
        try:
            host._wait_ready()
        except BaseException as error:
            failures.append(error)
        finally:
            finished.set()

    waiter = threading.Thread(target=wait_ready, daemon=True)
    try:
        assert ready.wait(10)
        waiter.start()
        assert finished.wait(5), 'partial frame blocked the parent past its startup timeout'
        assert len(failures) == 1 and isinstance(failures[0], TimeoutError)
        host.__exit__(type(failures[0]), failures[0], None)
        _assert_host_reaped(host, process, receiver)
        assert host._exitcode not in (None, 0)
    finally:
        _emergency_reap(process)
        if waiter.ident is not None:
            waiter.join(5)
        if host._reader is not None:
            host._reader.join(5)


def test_multibyte_traceback_bounds_serialized_frame_and_retains_endpoints() -> None:
    message = 'trace start\n' + '🙂' * 1_000_000 + '\nroot cause at end'
    bounded = serve._bounded_error_message(message)
    assert bounded.startswith('trace start') and bounded.endswith('root cause at end')
    assert 'traceback truncated' in bounded
    assert len(bounded.encode('utf-8')) <= serve._MAX_ERROR_BYTES
    # Include the transport's tuple/pickle and 4-byte frame header, not just characters.
    assert len(pickle.dumps(('error', bounded))) + 4 < serve._MAX_STATUS_BYTES


def test_truncated_pickle_payload_is_error_not_clean_channel_eof(tmp_path: Path) -> None:
    receiver, sender = multiprocessing.Pipe(duplex=False)
    host = serve.LocalServeGame(tmp_path / 'unused', startup_timeout=1)
    host._status = receiver
    host._proc = cast(Any, SimpleNamespace(exitcode=None))
    sender.send_bytes(b'\x80\x04')
    sender.close()
    try:
        with pytest.raises(RuntimeError, match='status channel failed'):
            host._wait_ready()
    finally:
        host._close_status_reader()
    assert receiver.closed


def test_unreaped_child_is_reported_and_recoverable_not_claimed_closed(tmp_path: Path) -> None:
    host = serve.LocalServeGame(tmp_path / 'unused', shutdown_timeout=0.1)
    process = Mock(pid=123, exitcode=None)
    process.is_alive.return_value = True
    stop = Mock()
    host._proc, host._stop = process, stop
    with pytest.raises(RuntimeError, match='Unable to reap'):
        host.__exit__(None, None, None)
    process.terminate.assert_called_once()
    process.kill.assert_called_once()
    process.close.assert_not_called()
    assert host._proc is process and host._stop is stop and host._exitcode is None


def test_child_launch_applies_byte_bound_to_actual_large_exception(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    def parse_args() -> None:
        raise RuntimeError('source context ' + '🙂' * 1_000_000 + ' terminal cause')

    module = ModuleType('MultiServer')
    setattr(module, 'parse_args', parse_args)
    monkeypatch.setitem(sys.modules, 'MultiServer', module)
    original_argv = sys.argv
    status = Mock()
    with pytest.raises(RuntimeError):
        serve._launch_multiserver(tmp_path / 'unused', status, Mock())
    message = status.send.call_args.args[0]
    assert message[0] == 'error' and 'traceback truncated' in message[1]
    assert message[1].endswith(' terminal cause\n')
    assert len(message[1].encode('utf-8')) <= serve._MAX_ERROR_BYTES
    assert len(pickle.dumps(message)) + 4 <= serve._MAX_ERROR_BYTES + 128 < serve._MAX_STATUS_BYTES
    assert sys.argv is original_argv
    status.close.assert_called_once()
