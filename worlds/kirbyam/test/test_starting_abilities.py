"""Issue #957: fixed starting permissions are real AP inventory, never equipment."""
from collections import Counter
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from NetUtils import NetworkItem

from .. import KirbyAmWorld
from ..data import data
from ..enemy_ability_data import ABILITY_NAME_TO_ID, GATEABLE_ENEMY_COPY_ABILITIES, STARTING_COPY_ABILITIES
from ..rom import _initial_ability_gate_mask
from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive
from .test_start_inventory_protocol import validated_client, server_history
from .test_client import _run_abilities_command

STARTING_IDS = {3860103, 3860104, 3860106, 3860107, 3860108, 3860123}
STARTING_MASK = sum(1 << (item - 3860100) for item in STARTING_IDS)


@pytest.mark.parametrize("gating", [0, 1])
@pytest.mark.parametrize("explicit", [0, 1, 3])
def test_generated_start_inventory_and_balanced_pool(tmp_path, gating, explicit):
    player = tmp_path / "player.yaml"
    player.write_text(
        "name: Starting Abilities\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n"
        f"  ability_gating: {gating}\n  start_inventory:\n"
        f"    Beam Ability: {explicit}\n    Sword Ability: 1\n    Small Food: 2\n",
        encoding="utf-8",
    )
    archive = generate_archive_from_fixture(player, tmp_path / "output", seed=957)
    decoded = load_multidata_from_archive(archive)
    inventory = Counter(decoded["precollected_items"][1])
    assert {code: inventory[code] for code in STARTING_IDS} == {
        code: max(1, explicit) if code == 3860107 else 1 for code in STARTING_IDS
    }
    assert inventory[3860118] == 1  # Explicit Sword retained.
    assert inventory[3860026] == 2  # Unrelated multiplicity retained.
    locations = decoded["locations"][1]
    assert len(locations) == 116  # Existing default active physical-check count.
    pool = Counter(item[0] for item in locations.values())
    assert STARTING_IDS.isdisjoint(pool)
    gateable_ids = {3860100 + ABILITY_NAME_TO_ID[name] for name in GATEABLE_ENEMY_COPY_ABILITIES}
    assert gateable_ids.intersection(pool) == (gateable_ids if gating else set())
    slot = decoded["slot_data"][1]
    assert all(slot["ability_unlock_items"][name] == f"{name} Ability" for name in STARTING_COPY_ABILITIES)
    assert set(slot["ability_gateable_abilities"]) == (set(GATEABLE_ENEMY_COPY_ABILITIES) if gating else set())


@pytest.mark.parametrize("gating", [0, 1])
def test_bootstrap_preserves_initial_access_without_any_received_items(gating):
    world = SimpleNamespace(options=SimpleNamespace(ability_gating=SimpleNamespace(value=gating)))
    gate = _initial_ability_gate_mask(world)
    assert not gate & STARTING_MASK
    assert bool(gate) == bool(gating)
    assert {KirbyAmWorld.item_name_to_id[f"{name} Ability"] for name in STARTING_COPY_ABILITIES} == STARTING_IDS


@pytest.mark.asyncio
@pytest.mark.parametrize("gating", [False, True])
@pytest.mark.parametrize("normal_history", [False, True])
async def test_stock_history_and_unlock_restoration(mock_bizhawk_context, gating, normal_history):
    ctx = mock_bizhawk_context
    client = await validated_client(ctx)
    starting = [NetworkItem(code, -2, 0) for code in sorted(STARTING_IDS)]
    normal = [NetworkItem(3860026, 3960566, 1)] if normal_history else []
    server, _ = await server_history(ctx, starting, normal)
    packet = server.send_msgs.call_args.args[1][0]
    assert packet["index"] == 0 and packet["items"] == starting + normal
    ctx.items_received = packet["items"]
    ctx.slot_data = {"ability_gating": gating, "ability_unlock_items": {
        name: f"{name} Ability" for name in STARTING_COPY_ABILITIES
    }}
    memory = {}

    async def read(_ctx, requests):
        return [memory.get(address, bytes(size)) for address, size, _domain in requests]

    async def write(_ctx, requests):
        for address, value, _domain in requests:
            memory[address] = value

    with patch('worlds.kirbyam.client.bizhawk.read', side_effect=read), \
         patch('worlds.kirbyam.client.bizhawk.write', side_effect=write):
        for reset in range(3):
            # Initial delivery, ROM/save-state loss, then a new client process.
            memory.clear()
            if reset == 2:
                client = await validated_client(ctx)
            client.on_package(ctx, 'Connected', {})
            client.on_package(ctx, 'ReceivedItems', packet)
            await client._sync_enemy_copy_ability_runtime_config(ctx)
            for _ in range(2):
                client.on_package(ctx, 'ReceivedItems', packet)
                await client._sync_enemy_copy_ability_runtime_config(ctx)
            unlock = int.from_bytes(memory[client._transport_addr('ability_unlock_mask_runtime')], 'little')
            gate = int.from_bytes(memory[client._transport_addr('ability_gate_mask_runtime')], 'little')
            assert unlock == STARTING_MASK
            assert gate & STARTING_MASK == 0
            assert bool(gate) == gating
            # Runtime config never writes a held ability or any native Kirby field.
            assert set(memory) <= set(data.transport_ram_addresses.values())
    lines = _run_abilities_command(ctx)
    assert all(name in lines for name in STARTING_COPY_ABILITIES)


def test_starting_ownership_is_visible_to_collection_state_without_new_gates():
    from BaseClasses import CollectionState, ItemClassification, MultiWorld
    multiworld = MultiWorld(1)
    multiworld.game[1] = KirbyAmWorld.game
    world = KirbyAmWorld(multiworld, 1)
    multiworld.worlds[1] = world
    state = CollectionState(multiworld)
    for name in STARTING_COPY_ABILITIES:
        item = world.create_item(f"{name} Ability")
        assert item.classification == ItemClassification.useful
        assert not state.has(item.name, 1)
        assert world.collect(state, item)
        assert state.has(item.name, 1)
        assert world.remove(state, item)
        assert not state.has(item.name, 1)
