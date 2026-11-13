from __future__ import annotations

import asyncio
import multiprocessing
import pickle
import queue
import threading
import sys
import time
from multiprocessing.connection import Connection
from pathlib import Path
from types import TracebackType
from typing import Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from multiprocessing.process import BaseProcess
    from multiprocessing.synchronize import Event
    from werkzeug.test import Client as FlaskClient

__all__ = [
    "ServeGame",
    "LocalServeGame",
    "WebHostServeGame",
]


# Keep ordinary status frames well below pipe buffers, and reject larger frames before reading them.
_MAX_STATUS_BYTES = 4096
_MAX_ERROR_BYTES = 2048


def _bounded_error_message(message: str) -> str:
    data = message.encode("utf-8")
    if len(data) > _MAX_ERROR_BYTES:
        marker = b"\n... traceback truncated ...\n"
        end = (_MAX_ERROR_BYTES - len(marker)) // 2
        data = data[:end] + marker + data[-end:]
    return data.decode("utf-8", errors="ignore")


def _read_status_messages(status: Connection, messages: queue.Queue[tuple[str, Any]]) -> None:
    """Only this reader can block on a partial frame; the parent always has bounded waits."""
    try:
        for index in range(2):  # one ready message, then at most one terminal error
            try:
                payload = status.recv_bytes(_MAX_STATUS_BYTES)
            except EOFError:
                messages.put(("closed", "Local MultiServer closed its startup channel before readiness"))
                return
            message = pickle.loads(payload)
            if not isinstance(message, tuple) or len(message) != 2:
                raise ValueError("Invalid local MultiServer status message")
            kind, value = message
            if kind not in ("ready", "error") or (index and kind == "ready"):
                raise ValueError("Invalid local MultiServer status sequence")
            messages.put((kind, value))
            if kind == "error":
                return
    except Exception as error:
        messages.put(("ipc_error", f"Local MultiServer status channel failed: {error}"))
    finally:
        status.close()


class ServeGame:
    address: str


async def _run_multiserver(args: Any, status: Connection, stop: Event) -> None:
    """Run the real server, observing its actual listener only inside this test child."""
    from unittest.mock import patch
    import MultiServer

    contexts: list[Any] = []
    context_created = asyncio.Event()
    listener_ready = asyncio.Event()
    original_init = MultiServer.Context.__init__

    def observe_context(context: Any, *init_args: Any, **init_kwargs: Any) -> None:
        original_init(context, *init_args, **init_kwargs)
        contexts.append(context)
        context_created.set()

    async def announce_listener() -> None:
        await context_created.wait()
        context = contexts[0]
        while True:
            server = getattr(context.server, "ws_server", context.server)
            # websockets' Serve owns a WebSocketServer before its bind completes.
            sockets = getattr(server, "sockets", None)
            if sockets and server.is_serving():
                address = next(iter(sockets)).getsockname()
                if address[0] != "127.0.0.1" or not 0 < address[1] < 65536:
                    raise RuntimeError(f"Unexpected local server listener: {address!r}")
                status.send(("ready", address[1]))
                listener_ready.set()
                return
            await asyncio.sleep(0.01)

    async def wait_stop() -> None:
        await listener_ready.wait()
        # No executor thread may remain blocked on Event.wait after a startup failure.
        while not stop.is_set():
            await asyncio.sleep(0.01)
        contexts[0].commandprocessor._cmd_exit()

    # Do not replace Context itself: its constructor uses super(Context, self).
    # This observation seam is scoped to the spawned child, not production code.
    with patch.object(MultiServer.Context, "__init__", observe_context):
        tasks = [asyncio.create_task(MultiServer.main(args)),
                 asyncio.create_task(announce_listener()), asyncio.create_task(wait_stop())]
        try:
            await asyncio.gather(*tasks)
        finally:
            if contexts:
                contexts[0].exit_event.set()
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            if contexts:
                server = getattr(contexts[0].server, "ws_server", contexts[0].server)
                if getattr(server, "server", None) is not None:
                    server.close()
                    await server.wait_closed()


def _launch_multiserver(multidata: Path, status: Connection, stop: Event) -> None:
    import traceback
    import warnings

    original_argv = sys.argv
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            from MultiServer import parse_args

            # The OS chooses and retains the port during the real server bind.
            # Never probe a free port and release it for a later, racy bind.
            sys.argv = [sys.argv[0], str(multidata), "--host", "127.0.0.1", "--port", "0"]
            asyncio.run(_run_multiserver(parse_args(), status, stop))
    except BaseException:
        try:
            status.send(("error", _bounded_error_message(traceback.format_exc())))
        except (BrokenPipeError, EOFError, OSError):
            pass  # The parent may already be unwinding a startup timeout.
        raise
    finally:
        sys.argv = original_argv
        status.close()


class LocalServeGame(ServeGame):
    def __init__(self, multidata: Path, *, startup_timeout: float = 30.0, shutdown_timeout: float = 30.0) -> None:
        self.address = ""
        self._multidata = multidata
        self._startup_timeout = startup_timeout
        self._shutdown_timeout = shutdown_timeout
        self._proc: BaseProcess | None = None
        self._stop: Event | None = None
        self._status: Connection | None = None
        self._exitcode: int | None = None
        self._reader: threading.Thread | None = None
        self._messages: queue.Queue[tuple[str, Any]] = queue.Queue()

    def _start_status_reader(self) -> None:
        if self._status is not None and self._reader is None:
            reader = threading.Thread(target=_read_status_messages, args=(self._status, self._messages),
                                      name="LocalServeGame status reader", daemon=True)
            reader.start()
            self._reader = reader

    def _wait_ready(self) -> str:
        assert self._proc is not None and self._status is not None
        self._start_status_reader()
        deadline = time.monotonic() + self._startup_timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("Timed out waiting for local MultiServer listener")
            try:
                kind, value = self._messages.get(timeout=min(0.05, remaining))
            except queue.Empty:
                if self._proc.exitcode is not None:
                    raise RuntimeError(f"Local MultiServer exited before readiness (exit code {self._proc.exitcode})")
                continue
            if kind == "error":
                raise RuntimeError(f"Local MultiServer startup failed:\n{value}")
            if kind in ("closed", "ipc_error"):
                raise RuntimeError(value)
            if kind != "ready" or type(value) is not int or not 0 < value < 65536:
                raise RuntimeError(f"Invalid local MultiServer startup response: {(kind, value)!r}")
            return f"127.0.0.1:{value}"

    def __enter__(self) -> LocalServeGame:
        if self._proc is not None:
            raise RuntimeError("LocalServeGame is already running")
        self._messages = queue.Queue()
        self._exitcode = None
        # Do not change the application's global multiprocessing start method.
        context = multiprocessing.get_context("spawn")
        self._status, child_status = context.Pipe(duplex=False)
        try:
            self._stop = context.Event()
            self._proc = context.Process(target=_launch_multiserver, args=(self._multidata, child_status, self._stop))
            self._proc.start()
            child_status.close()
            self.address = self._wait_ready()
            return self
        except BaseException:
            child_status.close()
            self.__exit__(*sys.exc_info())
            raise
        finally:
            child_status.close()

    def _child_error(self) -> str | None:
        error = None
        while True:
            try:
                kind, value = self._messages.get_nowait()
            except queue.Empty:
                return error
            if kind in ("error", "ipc_error"):
                error = str(value)

    def _close_status_reader(self) -> None:
        if self._reader is not None:
            self._reader.join(5)
            if self._reader.is_alive():
                raise RuntimeError("Unable to stop local MultiServer status reader")
            self._reader = None  # the reader owns and closes the connection
            self._status = None
        elif self._status is not None:
            self._status.close()
            self._status = None

    def _reap_process(self, process: BaseProcess, attempt: Callable[[Callable[[], None]], None]) -> None:
        if process.pid is None:
            return
        attempt(lambda: process.join(self._shutdown_timeout))
        if process.is_alive():
            attempt(process.terminate)
            attempt(lambda: process.join(5))
        if process.is_alive():
            attempt(process.kill)
            attempt(lambda: process.join(5))
        if process.is_alive():
            raise RuntimeError("Unable to reap local MultiServer child")

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None,
                 exc_tb: TracebackType | None) -> None:
        cleanup_errors: list[BaseException] = []

        def attempt(action: Callable[[], None]) -> None:
            try:
                action()
            except BaseException as error:
                cleanup_errors.append(error)

        process = self._proc
        try:
            if process is not None and process.pid is not None:
                # Drain concurrently with join: even an unexpected oversized writer cannot block cleanup.
                attempt(self._start_status_reader)
            if self._stop is not None:
                attempt(self._stop.set)
            if process is not None:
                attempt(lambda: self._reap_process(process, attempt))
        except BaseException as error:
            cleanup_errors.append(error)
        finally:
            # IPC corruption must never skip closing a reaped process handle or resetting state.
            if process is not None:
                try:
                    if process.pid is None or not process.is_alive():
                        self._exitcode = process.exitcode
                        process.close()
                        self._proc = None
                    # Retain a still-live handle for recovery rather than silently orphaning it.
                except BaseException as error:
                    cleanup_errors.append(error)
            attempt(self._close_status_reader)
            if self._proc is None:
                self._stop = None
        child_error = self._child_error()
        if child_error or self._exitcode not in (None, 0):
            cleanup_errors.append(RuntimeError(
                f"Local MultiServer failed (exit code {self._exitcode}):\n{child_error or ''}"))
        if cleanup_errors:
            if exc_type is None:
                raise cleanup_errors[0]
            if exc_val is not None:
                exc_val.add_note(f"Local MultiServer cleanup: {cleanup_errors[0]}")


class WebHostServeGame(ServeGame):
    _client: FlaskClient
    _room: str

    def __init__(self, app_client: FlaskClient, room: str) -> None:
        self.address = ""
        self._client = app_client
        self._room = room

    def __enter__(self) -> WebHostServeGame:
        from .webhost import start_room
        self.address = start_room(self._client, self._room)
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None,
                 exc_tb: TracebackType | None) -> None:
        from .webhost import stop_room
        stop_room(self._client, self._room, timeout=30)
