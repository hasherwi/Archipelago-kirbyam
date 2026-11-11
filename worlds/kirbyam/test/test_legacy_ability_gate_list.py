"""Legacy slot gates stay fixed when the current generation catalog grows."""

from __future__ import annotations

from importlib import import_module
from typing import Any, Callable
from unittest.mock import AsyncMock, patch

import pytest
from NetUtils import NetworkItem
from worlds._bizhawk.context import BizHawkClientCommandProcessor

from .. import client as client_module, enemy_ability_data, rom
from ..client import KirbyAmClient, _build_kirbyam_command_processor
from ..data import data
from ..enemy_ability_data import (
    ABILITY_NAME_TO_ID, LEGACY_SLOT_GATEABLE_ABILITIES, STARTING_COPY_ABILITIES,
    resolve_slot_gateable_abilities,
)

from .test_mini_traversal import make_world

# Literal protocol expectations, deliberately not derived from today's catalog.
LEGACY_NAMES = (
    "Bomb", "Cook", "Crash", "Cutter", "Cupid", "Fighter", "Fire", "Hammer", "Ice", "Laser", "Magic",
    "Mini", "Missile", "Parasol", "Smash", "Sleep", "Spark", "Sword", "Throw", "Tornado", "UFO", "Wheel",
)
LEGACY_MASK = 0x03FFFE76
EXPANDED_NAMES = (*LEGACY_NAMES, "Stone", "Burning")
EXPANDED_MASK = 0x03FFFF7E
STONE_BURNING_MASK = 0x108
MISSING = object()
GATE_CASES = [
    pytest.param(MISSING, LEGACY_NAMES, LEGACY_MASK, id="missing"),
    pytest.param([], LEGACY_NAMES, LEGACY_MASK, id="empty-list"),
    pytest.param(None, LEGACY_NAMES, LEGACY_MASK, id="none"),
    pytest.param("Stone", LEGACY_NAMES, LEGACY_MASK, id="string"),
    pytest.param(("Stone",), LEGACY_NAMES, LEGACY_MASK, id="tuple"),
    pytest.param({"Stone": True}, LEGACY_NAMES, LEGACY_MASK, id="dict"),
    pytest.param(1, LEGACY_NAMES, LEGACY_MASK, id="integer"),
    pytest.param(list(LEGACY_NAMES), LEGACY_NAMES, LEGACY_MASK, id="explicit-old"),
    pytest.param(list(EXPANDED_NAMES), EXPANDED_NAMES, EXPANDED_MASK, id="explicit-new"),
    pytest.param(["Stone"], ("Stone",), 0x100, id="stone-only"),
    pytest.param(["Burning"], ("Burning",), 0x8, id="burning-only"),
    pytest.param(["Beam"], ("Beam",), 0x80, id="beam-only"),
    pytest.param([None], (), 0, id="nonempty-none"),
    pytest.param([None, 1, {}, []], (), 0, id="nonempty-invalid"),
    pytest.param(["unknown"], ("unknown",), 0, id="unknown-name"),
    pytest.param([None, "Stone", 1, "Burning", "Stone", "unknown"],
                 ("Stone", "Burning", "Stone", "unknown"), STONE_BURNING_MASK, id="mixed-duplicates"),
]
RUNTIME_FIELDS = (
    "ability_randomization_mode_runtime", "ability_randomization_seed_lo_runtime",
    "ability_randomization_seed_hi_runtime", "ability_randomization_no_ability_weight_runtime",
    "ability_randomization_allowed_mask_runtime", "ability_gate_mask_runtime", "ability_unlock_mask_runtime",
    "ability_randomization_rng_state_runtime",
)


@pytest.fixture
def expanded_catalog(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(enemy_ability_data, "GATEABLE_ENEMY_COPY_ABILITIES", EXPANDED_NAMES)
    # Also catch the old imported alias if a consumer accidentally reintroduces it.
    monkeypatch.setattr(client_module, "GATEABLE_ENEMY_COPY_ABILITIES", EXPANDED_NAMES, raising=False)


def _slot_data(structured: bool, gating: bool, raw: object) -> dict[str, object]:
    slot: dict[str, object] = {"ability_gating": gating}
    if structured:
        slot["enemy_copy_ability_policy"] = {
            "mode": 2, "seed": 0x100000002, "ability_randomization_no_ability_weight": 17,
            "allowed_abilities": ["Stone", "Burning"],
        }
    if raw is not MISSING:
        slot["ability_gateable_abilities"] = raw
    return slot


def _abilities(ctx: Any) -> list[str]:
    processor = _build_kirbyam_command_processor(BizHawkClientCommandProcessor)(ctx)
    with patch.object(processor, "output") as output:
        assert processor("/abilities") is True
    lines = [call.args[0] for call in output.call_args_list]
    assert lines[0] == f"Unlocked Abilities for {KirbyAmClient.game}"
    return lines[1:]


def _expected_abilities(names: tuple[str, ...], gating: bool, received: bool) -> list[str]:
    available = set(ABILITY_NAME_TO_ID) - {"Wait"}
    if gating:
        available.difference_update(names)
    if received:
        available.update(("Stone", "Burning"))
    return sorted(available)


def test_frozen_gate_list_and_historical_receipt_names() -> None:
    assert LEGACY_SLOT_GATEABLE_ABILITIES == LEGACY_NAMES
    assert len(LEGACY_SLOT_GATEABLE_ABILITIES) == 22
    assert sum(1 << ABILITY_NAME_TO_ID[name] for name in LEGACY_SLOT_GATEABLE_ABILITIES) == LEGACY_MASK
    assert sum(1 << ABILITY_NAME_TO_ID[name] for name in EXPANDED_NAMES) == EXPANDED_MASK
    assert EXPANDED_MASK ^ LEGACY_MASK == STONE_BURNING_MASK
    assert STARTING_COPY_ABILITIES == ("Beam", "Burning", "Cutter", "Mini", "Stone", "Wheel")


@pytest.mark.parametrize("raw,names,mask", GATE_CASES)
def test_slot_list_selection_precedes_filtering(
    expanded_catalog: None, raw: object, names: tuple[str, ...], mask: int,
) -> None:
    assert resolve_slot_gateable_abilities(raw) == names
    # The helper preserves unknown strings and duplicate ordering; consumers ignore unknown IDs.
    resolved_mask = 0
    for name in resolve_slot_gateable_abilities(raw):
        ability_id = ABILITY_NAME_TO_ID.get(name)
        if ability_id is not None and 0 < ability_id <= 31:
            resolved_mask |= 1 << ability_id
    assert resolved_mask == mask


@pytest.mark.asyncio
@pytest.mark.parametrize("raw,names,mask", GATE_CASES)
@pytest.mark.parametrize("structured", [False, True])
@pytest.mark.parametrize("gating", [False, True])
@pytest.mark.parametrize("received", [False, True])
async def test_both_consumers_keep_seed_gates_after_catalog_expansion(
    mock_bizhawk_context: Any, expanded_catalog: None, raw: object, names: tuple[str, ...],
    mask: int, structured: bool, gating: bool, received: bool,
) -> None:
    ctx = mock_bizhawk_context
    ctx.game = KirbyAmClient.game
    ctx.slot_data = _slot_data(structured, gating, raw)
    # Historical useful flags are valid ownership, not equipment changes.
    ctx.items_received = [NetworkItem(code, -2, 0, 2) for code in (3860108, 3860103)] if received else []
    client = KirbyAmClient()
    client.initialize_client()
    with patch("worlds.kirbyam.client.bizhawk.write", new_callable=AsyncMock) as write:
        await client._sync_enemy_copy_ability_runtime_config(ctx)
        write.assert_awaited_once()
        assert write.await_args is not None
        requests = write.await_args.args[1]
        written = {address: int.from_bytes(value, "little") for address, value, domain in requests}
        expected_values = (
            (2, 2, 1, 17, STONE_BURNING_MASK) if structured else (0, 0, 0, 0, 0)
        ) + (mask if gating else 0, STONE_BURNING_MASK if received else 0, 0)
        assert written == dict(zip((data.transport_ram_addresses[name] for name in RUNTIME_FIELDS), expected_values))
        assert all(len(value) == 4 and domain == "System Bus" for _, value, domain in requests)
        assert _abilities(ctx) == _expected_abilities(names, gating, received)
        # /abilities is read-only; all synchronization writes above are mailbox fields, never native equipment.
        write.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("structured", [False, True])
@pytest.mark.parametrize("gating", [False, True])
@pytest.mark.parametrize("explicit", [False, True])
async def test_seed_gates_and_receipts_survive_reconnect_reset_and_new_client(
    mock_bizhawk_context: Any, expanded_catalog: None, structured: bool, gating: bool, explicit: bool,
) -> None:
    ctx = mock_bizhawk_context
    ctx.game = KirbyAmClient.game
    names = EXPANDED_NAMES if explicit else LEGACY_NAMES
    mask = (EXPANDED_MASK if explicit else LEGACY_MASK) if gating else 0
    ctx.slot_data = _slot_data(structured, gating, list(names) if explicit else MISSING)
    ctx.items_received = []
    client = KirbyAmClient()
    client.initialize_client()
    memory: dict[int, bytes] = {}
    addresses = {data.transport_ram_addresses[name] for name in RUNTIME_FIELDS}
    gate_addr = data.transport_ram_addresses["ability_gate_mask_runtime"]
    unlock_addr = data.transport_ram_addresses["ability_unlock_mask_runtime"]

    async def read(_ctx: Any, requests: list[tuple[int, int, str]]) -> list[bytes]:
        return [memory.get(address, bytes(size)) for address, size, _ in requests]

    async def write(_ctx: Any, requests: list[tuple[int, bytes, str]]) -> None:
        assert {address for address, _, _ in requests} == addresses
        assert all(len(value) == 4 and domain == "System Bus" for _, value, domain in requests)
        memory.update({address: value for address, value, _ in requests})

    with patch("worlds.kirbyam.client.bizhawk.read", side_effect=read), \
         patch("worlds.kirbyam.client.bizhawk.write", side_effect=write):
        await client._sync_enemy_copy_ability_runtime_config(ctx)
        assert int.from_bytes(memory[gate_addr], "little") == mask
        assert int.from_bytes(memory[unlock_addr], "little") == 0
        assert _abilities(ctx) == _expected_abilities(names, gating, False)
        ctx.items_received = [NetworkItem(code, -2, 0, 2) for code in (3860108, 3860103)]
        for event in ("receipts", "reconnect", "cold-reset", "mailbox-drift", "new-client"):
            if event == "reconnect":
                client._reset_reconnect_transient_state()
            elif event == "cold-reset":
                memory.clear()
            elif event == "mailbox-drift":
                memory[gate_addr] = (mask ^ STONE_BURNING_MASK).to_bytes(4, "little")
                memory[unlock_addr] = bytes(4)
            elif event == "new-client":
                client = KirbyAmClient()
                client.initialize_client()
                memory.clear()
            await client._sync_enemy_copy_ability_runtime_config(ctx)
            assert int.from_bytes(memory[gate_addr], "little") == mask, event
            assert int.from_bytes(memory[unlock_addr], "little") == STONE_BURNING_MASK, event
            assert _abilities(ctx) == _expected_abilities(names, gating, True), event
        # A replacement history is authoritative too; cached ownership must not equip/unlock anything.
        ctx.items_received = []
        await client._sync_enemy_copy_ability_runtime_config(ctx)
        assert int.from_bytes(memory[gate_addr], "little") == mask
        assert int.from_bytes(memory[unlock_addr], "little") == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("slot", [None, {}, {"goal": 0}])
async def test_no_config_keeps_legacy_runtime_return(
    mock_bizhawk_context: Any, expanded_catalog: None, slot: object,
) -> None:
    client = KirbyAmClient()
    client.initialize_client()
    mock_bizhawk_context.slot_data = slot
    with patch("worlds.kirbyam.client.bizhawk.read", new_callable=AsyncMock) as read, \
         patch("worlds.kirbyam.client.bizhawk.write", new_callable=AsyncMock) as write:
        await client._sync_enemy_copy_ability_runtime_config(mock_bizhawk_context)
    read.assert_not_awaited()
    write.assert_not_awaited()
    assert client._last_ability_runtime_config_signature is None


@pytest.mark.parametrize("history", [
    (3860107, 3860103, 3860106, 3860123, 3860108, 3860104),  # Historical six.
    (3860107, 3860103, 3860108),  # Current automatic starts.
    (3860107,),  # Future Beam-only starts do not need a new receipt protocol.
    (3860108, 3860103),  # Explicit Stone/Burning starts.
])
def test_historical_start_receipt_exception_remains_precollect_only(history: tuple[int, ...]) -> None:
    for code in history:
        assert KirbyAmClient._is_guaranteed_starting_ability_receipt(NetworkItem(code, -2, 0, 2))
        assert not KirbyAmClient._is_guaranteed_starting_ability_receipt(NetworkItem(code, 3960566, 1, 2))
        assert not KirbyAmClient._is_guaranteed_starting_ability_receipt(NetworkItem(code, -2, 1, 2))


@pytest.mark.parametrize("mode", [0, 1, 2])
@pytest.mark.parametrize("gating", [False, True])
def test_new_seed_serialization_and_bootstrap_keep_current_catalog(
    monkeypatch: pytest.MonkeyPatch, expanded_catalog: None, mode: int, gating: bool,
) -> None:
    create_world: Callable[..., Any] = make_world
    world = create_world(mode, gating)
    monkeypatch.setattr(import_module("worlds.kirbyam"), "GATEABLE_ENEMY_COPY_ABILITIES", EXPANDED_NAMES)
    monkeypatch.setattr(rom, "GATEABLE_ENEMY_COPY_ABILITIES", EXPANDED_NAMES)
    # Only serialization/bootstrap are under test; no future pool/classification behavior is inferred.
    slot = world.fill_slot_data()
    assert slot["ability_gateable_abilities"] == (list(EXPANDED_NAMES) if gating else [])
    assert len(slot["ability_unlock_items"]) == 25
    assert rom._initial_ability_gate_mask(world) == (EXPANDED_MASK if gating else 0)
    assert resolve_slot_gateable_abilities(None) == LEGACY_NAMES
