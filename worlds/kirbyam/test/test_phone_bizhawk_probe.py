"""Harness contract checks only, never native BizHawk acceptance."""
import asyncio
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Awaitable

import pytest

SPEC = importlib.util.spec_from_file_location(
    "phone_probe", Path(__file__).resolve().parents[3] / "tools/phone_bizhawk_readonly_probe.py")
assert SPEC is not None and SPEC.loader is not None
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


class ReadOnlyTransport:
    def __init__(self, raw: bytes = b"\0" * 12, identity: str = "a" * 40) -> None:
        self.raw = raw
        self.identity = identity
        self.reads: list[list[tuple[int, int, str]]] = []

    async def get_script_version(self, ctx: object) -> int:
        return 1

    async def ping(self, ctx: object) -> None:
        pass

    async def get_system(self, ctx: object) -> str:
        return "GBA"

    async def get_hash(self, ctx: object) -> str:
        return self.identity

    async def get_memory_size(self, ctx: object, domain: str) -> int:
        assert domain == "System Bus"
        return 0x10000000

    async def read(self, ctx: object, requests: list[tuple[int, int, str]]) -> list[bytes]:
        self.reads.append(requests)
        return [self.raw]


@pytest.mark.parametrize("raw,expected", [
    (bytes(12), "legacy"), (probe.MARKER + bytes(4), "disabled"),
    (probe.MARKER + b"\1\0\0\0", "enabled"),
])
def test_exact_probe(raw: bytes, expected: str) -> None:
    transport = ReadOnlyTransport(raw)
    result = asyncio.run(probe.collect(transport, None, "a" * 40, expected, 3))
    assert transport.reads == [[(0x0900FFC8, 12, "System Bus")]] * 3
    assert result["configuration"] == expected
    assert "raw" not in result


@pytest.mark.parametrize("raw", [bytes(11), bytes(13), b"APPHN02\0" + bytes(4), probe.MARKER + b"\2\0\0\0"])
def test_invalid_config(raw: bytes) -> None:
    with pytest.raises(ValueError):
        probe.classify(raw)


def test_wrong_rom_refuses_before_read() -> None:
    transport = ReadOnlyTransport(identity="b" * 40)
    with pytest.raises(ValueError, match="does not match"):
        asyncio.run(probe.collect(transport, None, "a" * 40, "legacy", 3))
    assert not transport.reads


def test_unexpected_marker_refused() -> None:
    with pytest.raises(ValueError, match="expected case"):
        asyncio.run(probe.collect(ReadOnlyTransport(probe.MARKER + bytes(4)), None, "a" * 40, "legacy", 3))


def test_changed_rom_refused() -> None:
    class ChangedIdentity(ReadOnlyTransport):
        async def get_hash(self, ctx: object) -> str:
            return "b" * 40 if self.reads else "a" * 40
    with pytest.raises(ValueError, match="changed during"):
        asyncio.run(probe.collect(ChangedIdentity(), None, "a" * 40, "legacy", 3))


def test_unstable_legacy_data_refused() -> None:
    class ChangedBytes(ReadOnlyTransport):
        async def read(self, ctx: object, requests: list[tuple[int, int, str]]) -> list[bytes]:
            self.reads.append(requests)
            return [bytes([len(self.reads)]) * 12]
    with pytest.raises(ValueError, match="changed between"):
        asyncio.run(probe.collect(ChangedBytes(), None, "a" * 40, "legacy", 3))


@pytest.mark.parametrize("method,value,message", [
    ("get_script_version", 2, "script version"),
    ("get_system", "NES", "not running GBA"),
    ("get_memory_size", probe.ADDRESS + 11, "too small"),
    ("read", [], "response count"),
    ("read", [bytes(12), bytes(12)], "response count"),
])
def test_invalid_endpoint_response(
    monkeypatch: pytest.MonkeyPatch, method: str, value: object, message: str,
) -> None:
    transport = ReadOnlyTransport()

    async def response(*args: object) -> object:
        return value

    monkeypatch.setattr(transport, method, response)
    with pytest.raises(ValueError, match=message):
        asyncio.run(probe.collect(transport, None, "a" * 40, "legacy", 3))
    assert not transport.reads


@pytest.mark.parametrize("prefix", ["", "SHA1:", "sha1:", "Sha1:"])
def test_sha1_normalization(prefix: str) -> None:
    assert probe.normalize_sha1(prefix + "ABCDEF0123" * 4) == "abcdef0123" * 4


@pytest.mark.parametrize("value", ["a" * 39, "a" * 41, "g" * 40, "MD5:" + "a" * 40,
                                   "SHA1:sha1:" + "a" * 40, " " + "a" * 40])
def test_sha1_invalid(value: str) -> None:
    with pytest.raises(ValueError, match="SHA-1"):
        probe.normalize_sha1(value)


@pytest.fixture
def run_setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    rom = tmp_path / "synthetic-test-only.bin"
    rom.write_bytes(b"synthetic fixture, not a ROM")
    args = SimpleNamespace(rom=rom, output=tmp_path / "result.json", port=43057,
                           expected="legacy", samples=3, bizhawk_version="test-only", core="stub")
    contexts: list[SimpleNamespace] = []
    disconnected: list[SimpleNamespace] = []
    connections: list[tuple[str, int]] = []

    def context() -> SimpleNamespace:
        ctx = SimpleNamespace(streams=None)
        contexts.append(ctx)
        return ctx

    transport = SimpleNamespace(BizHawkContext=context, disconnect=disconnected.append,
                                ConnectionStatus=SimpleNamespace(TENTATIVE="tentative"))

    async def connect(host: str, port: int) -> tuple[object, object]:
        connections.append((host, port))
        return object(), object()

    async def collect(*args: object) -> dict[str, object]:
        return {"configuration": "legacy"}

    monkeypatch.setattr(probe, "load_transport", lambda: transport)
    monkeypatch.setattr(probe.asyncio, "open_connection", connect)
    monkeypatch.setattr(probe, "collect", collect)
    return SimpleNamespace(args=args, contexts=contexts, disconnected=disconnected, connections=connections)


def test_run_writes_sanitized_output_and_disconnects(run_setup: SimpleNamespace) -> None:
    import json
    setup = run_setup
    asyncio.run(probe.run(setup.args))
    result = json.loads(setup.args.output.read_text())
    assert result["configuration"] == "legacy"
    assert setup.connections == [("127.0.0.1", 43057)]
    assert setup.disconnected == setup.contexts
    assert str(setup.args.rom) not in setup.args.output.read_text()
    assert "synthetic fixture" not in setup.args.output.read_text()


def test_existing_output_refused_before_connection(run_setup: SimpleNamespace) -> None:
    setup = run_setup
    setup.args.output.write_text("preserve me")
    with pytest.raises(FileExistsError):
        asyncio.run(probe.run(setup.args))
    assert setup.args.output.read_text() == "preserve me"
    assert not setup.connections


def test_output_creation_race_does_not_overwrite(
    run_setup: SimpleNamespace, monkeypatch: pytest.MonkeyPatch,
) -> None:
    setup = run_setup

    async def collect(*args: object) -> dict[str, object]:
        setup.args.output.write_text("created concurrently")
        return {}

    monkeypatch.setattr(probe, "collect", collect)
    with pytest.raises(FileExistsError):
        asyncio.run(probe.run(setup.args))
    assert setup.args.output.read_text() == "created concurrently"
    assert setup.disconnected == setup.contexts


@pytest.mark.parametrize("stage,expected_budgets", [("connect", [5]), ("collect", [5, 30])])
def test_timeout_is_bounded_disconnects_and_writes_no_evidence(
    run_setup: SimpleNamespace, monkeypatch: pytest.MonkeyPatch, stage: str, expected_budgets: list[int],
) -> None:
    setup = run_setup
    budgets: list[float] = []
    original_wait_for = asyncio.wait_for

    async def bounded_wait(awaitable: Awaitable[Any], timeout: float) -> Any:
        budgets.append(timeout)
        return await original_wait_for(awaitable, min(timeout, 0.01))

    async def never_finishes(*args: object) -> None:
        await asyncio.Event().wait()

    monkeypatch.setattr(probe.asyncio, "wait_for", bounded_wait)
    if stage == "connect":
        monkeypatch.setattr(probe.asyncio, "open_connection", never_finishes)
    else:
        monkeypatch.setattr(probe, "collect", never_finishes)
    with pytest.raises(asyncio.TimeoutError):
        asyncio.run(probe.run(setup.args))
    assert budgets == expected_budgets
    assert setup.disconnected == setup.contexts
    assert not setup.args.output.exists()
