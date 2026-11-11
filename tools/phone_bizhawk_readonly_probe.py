"""Bounded read-only Phone configuration probe through the stock BizHawk transport.

Run only against a dedicated native BizHawk instance with its stock Lua connector.
A successful socket exchange alone cannot establish emulator provenance.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ADDRESS = 0x0900FFC8
MARKER = b"APPHN01\0"


def load_transport() -> ModuleType:
    spec = importlib.util.spec_from_file_location("phone_probe_transport", ROOT / "worlds/_bizhawk/__init__.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load production BizHawk transport")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def classify(raw: bytes) -> str:
    if len(raw) != 12:
        raise ValueError("configuration read did not return exactly 12 bytes")
    if raw == MARKER + bytes(4):
        return "disabled"
    if raw == MARKER + b"\1\0\0\0":
        return "enabled"
    if raw.startswith(b"APPHN"):
        raise ValueError("unsupported or malformed Phone configuration")
    return "legacy"


def normalize_sha1(value: str) -> str:
    value = value.lower().removeprefix("sha1:")
    if len(value) != 40 or any(c not in "0123456789abcdef" for c in value):
        raise ValueError("connector did not provide a SHA-1 ROM identity")
    return value


async def collect(transport: Any, ctx: Any, rom_sha1: str, expected: str, samples: int) -> dict[str, object]:
    """Only VERSION, PING, SYSTEM, HASH, MEMORY_SIZE and READ requests are sent."""
    version = await transport.get_script_version(ctx)
    if version != 1:
        raise ValueError("unsupported connector script version")
    await transport.ping(ctx)
    if await transport.get_system(ctx) != "GBA":
        raise ValueError("connector is not running GBA")
    if normalize_sha1(await transport.get_hash(ctx)) != rom_sha1:
        raise ValueError("loaded ROM does not match the supplied local file")
    size = await transport.get_memory_size(ctx, "System Bus")
    if size < ADDRESS + 12:
        raise ValueError("System Bus domain is too small")
    hashes = []
    for _ in range(samples):
        values = await transport.read(ctx, [(ADDRESS, 12, "System Bus")])
        if len(values) != 1:
            raise ValueError("unexpected read response count")
        raw = bytes(values[0])
        if classify(raw) != expected:
            raise ValueError("Phone configuration does not match expected case")
        hashes.append(hashlib.sha256(raw).hexdigest())
    if len(set(hashes)) != 1:
        raise ValueError("configuration changed between reads")
    if normalize_sha1(await transport.get_hash(ctx)) != rom_sha1:
        raise ValueError("ROM identity changed during probe")
    return {"connector_version": version, "system": "GBA", "system_bus_size": size,
            "bus_address": hex(ADDRESS), "returned_size": 12, "samples": samples,
            "configuration": expected, "bytes_sha256": hashes[0]}


async def run(args: argparse.Namespace) -> None:
    if args.output.exists():
        raise FileExistsError("output already exists; choose a fresh evidence path")
    rom = args.rom.read_bytes()
    sha1 = hashlib.sha1(rom).hexdigest()
    transport = load_transport()
    ctx = transport.BizHawkContext()
    try:
        # Explicit port: do not rotate through or commandeer other emulator sessions.
        ctx.streams = await asyncio.wait_for(asyncio.open_connection("127.0.0.1", args.port), 5)
        ctx.connection_status = transport.ConnectionStatus.TENTATIVE
        result = await asyncio.wait_for(collect(transport, ctx, sha1, args.expected, args.samples), 30)
    finally:
        transport.disconnect(ctx)
    result.update({"schema_version": 1,
                   "scope": "Read-only Lua transport configuration probe; not gameplay or watcher pairing acceptance",
                   "rom_sha1": sha1, "rom_sha256": hashlib.sha256(rom).hexdigest(), "rom_size": len(rom),
                   "operator_reported_bizhawk_version": args.bizhawk_version,
                   "operator_reported_core": args.core,
                   "transport_sha256": hashlib.sha256((ROOT / "worlds/_bizhawk/__init__.py").read_bytes()).hexdigest(),
                   "stock_lua_sha256": hashlib.sha256(
                       (ROOT / "data/lua/connector_bizhawk_generic.lua").read_bytes()).hexdigest()})
    # Exclusive output, with neither local paths nor ROM bytes in the evidence.
    with args.output.open("x", encoding="utf-8") as output:
        json.dump(result, output, indent=2)
        output.write("\n")
    print("Read-only probe passed. Emulator provenance must be independently verified.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--port", type=int, required=True, choices=range(43055, 43060))
    parser.add_argument("--expected", choices=("legacy", "disabled", "enabled"), required=True)
    parser.add_argument("--samples", type=int, default=3, choices=range(1, 6))
    parser.add_argument("--bizhawk-version", required=True)
    parser.add_argument("--core", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; choose a fresh evidence path")
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
