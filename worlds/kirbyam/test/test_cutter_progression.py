"""Cutter permission is progression, not automatic equipment or starting inventory."""

from collections.abc import Awaitable, Callable, Iterable
from typing import cast
from .. import KirbyAmWorld
from ..client import KirbyAmClient

from argparse import Namespace
from collections import Counter
from io import BytesIO
from pathlib import Path
from typing import Any
import zipfile
import hashlib
import json

import pytest
from BaseClasses import CollectionState, ItemClassification, MultiWorld, PlandoOptions

from ..enemy_ability_data import starting_copy_abilities
from ..rom import ABILITY_GATE_MASK_INITIAL_ROM_OFFSET
from ..traversal import SourcePolicy
from ..traversal_data import graph_items, room_traversal_graph
from ..traversal_rules import graph_succeeds
from .support.integration_generation import load_multidata_from_archive
from .test_mini_traversal import make_world


CUTTER = 3860106
FIXED = {3860107}
SEEDS = (1042, 20261107, 8675309)


@pytest.mark.parametrize("mode", [0, 1, 2])
@pytest.mark.parametrize("gating", [False, True])
def test_new_starting_set_and_cutter_collection(mode: int, gating: bool) -> None:
    world = make_world(mode, gating)
    assert starting_copy_abilities(mode) == ("Beam",)
    state = CollectionState(world.multiworld)
    assert not state.has("Cutter Ability", 1)
    item = world.create_item("Cutter Ability")
    assert item.code == CUTTER and item.classification == ItemClassification.progression
    assert world.collect(state, item) and state.has(item.name, 1)
    assert world.remove(state, item) and not state.has(item.name, 1)


@pytest.mark.parametrize("gating", [False, True])
def test_cutter_source_requires_permission_and_permission_requires_source(gating: bool) -> None:
    from dataclasses import replace

    graph = room_traversal_graph("rope_143_23_14", "local")
    policy = SourcePolicy({"mode": 0})
    items = graph_items(graph)
    assert graph_succeeds(graph, policy, items, gating, retries=False) == (not gating)
    assert graph_succeeds(graph, policy, items | {"Cutter Ability"}, gating, retries=False)
    assert not graph_succeeds(replace(graph, placements=()), policy,
                              items | {"Cutter Ability"}, gating, retries=False)


def _generate(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, seed: int,
              options: list[dict[str, Any]]) -> tuple[MultiWorld, dict[str, Any], Path]:
    import Generate
    import Main
    import Utils
    import settings

    players = tmp_path / "players"
    players.mkdir()
    for player, values in enumerate(options, 1):
        lines = [f"name: Cutter Test {player}", "game: Kirby & The Amazing Mirror",
                 "Kirby & The Amazing Mirror:"]
        for name, value in values.items():
            if isinstance(value, dict):
                lines.append(f"  {name}:")
                lines.extend(f"    {item}: {count}" for item, count in value.items())
            else:
                lines.append(f"  {name}: {value}")
        (players / f"{player}.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    output = tmp_path / "output"
    output.mkdir()
    monkeypatch.setattr(settings, "no_gui", True)
    monkeypatch.setattr(settings, "skip_autosave", True)
    monkeypatch.setattr(Utils, "init_logging", lambda *args, **kwargs: None)
    args = Namespace(
        weights_file_path=settings.get_settings().generator.weights_file_path,
        sameoptions=False, player_files_path=str(players), seed=seed, multi=len(options), spoiler=1,
        outputpath=str(output), allow_quantity=False, race=False, meta_file_path="meta-doesnt-exist.yaml",
        log_level="info", yaml_output=1,
        plando=PlandoOptions.items | PlandoOptions.connections | PlandoOptions.texts | PlandoOptions.bosses,
        skip_prog_balancing=False, skip_output=False, csv_output=False, log_time=False, spoiler_only=False,
    )
    generated, actual_seed = Generate.main(args)
    assert actual_seed == seed
    multiworld = Main.main(generated, actual_seed)
    assert multiworld.can_beat_game() and multiworld.fulfills_accessibility()
    archive, = output.glob("*.zip")
    return multiworld, load_multidata_from_archive(archive), archive


def _gate_words(archive: Path) -> dict[int, int]:
    words = {}
    with zipfile.ZipFile(archive) as outer:
        for name in outer.namelist():
            if not name.endswith(".apkirbyam"):
                continue
            with zipfile.ZipFile(BytesIO(outer.read(name))) as patch:
                import json
                manifest = json.loads(patch.read("archipelago.json"))
                data = patch.read("token_data.bin")
                offset = 4
                for _ in range(int.from_bytes(data[:4], "little")):
                    token = data[offset]
                    address = int.from_bytes(data[offset + 1:offset + 5], "little")
                    size = int.from_bytes(data[offset + 5:offset + 9], "little")
                    payload = data[offset + 9:offset + 9 + size]
                    offset += 9 + size
                    if address == ABILITY_GATE_MASK_INITIAL_ROM_OFFSET:
                        assert token == 0 and size == 4
                        words[manifest["player"]] = int.from_bytes(payload, "little")
    return words


def _assert_slot_contract(multiworld: MultiWorld, decoded: dict[str, Any], gates: dict[int, int],
                          player: int, explicit: int = 0) -> None:
    world = multiworld.worlds[player]
    assert isinstance(world, KirbyAmWorld)
    gating = bool(world.options.ability_gating.value)
    inventory = Counter(decoded["precollected_items"][player])
    assert all(inventory[code] == 1 for code in FIXED)
    assert inventory[CUTTER] == explicit
    pooled = Counter(item.code for location in multiworld.get_locations()
                     if (item := location.item) is not None and item.player == player)
    assert pooled[CUTTER] == int(gating)
    assert not FIXED.intersection(pooled)
    slot = decoded["slot_data"][player]
    assert ("Cutter" in slot["ability_gateable_abilities"]) == gating
    assert slot["ability_unlock_items"]["Cutter"] == "Cutter Ability"
    assert bool(gates[player] & (1 << 6)) == gating
    assert gates[player] & (1 << 7) == 0
    assert gates[player] & ((1 << 3) | (1 << 8)) == (0x108 if gating else 0)


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("mode", [0, 1, 2])
@pytest.mark.parametrize("gating,accessibility", [(0, "full"), (1, "full"), (1, "minimal")])
def test_generated_seed_matrix(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    seed: int,
    mode: int,
    gating: bool,
    accessibility: str,
) -> None:
    variant = SEEDS.index(seed)
    options = {
        "ability_randomization_mode": mode, "ability_gating": gating, "accessibility": accessibility,
        "ability_randomization_no_ability_weight": (0, 99, 100)[variant],
        "ability_randomization_statues": variant % 2,
        "ability_randomization_passive_enemies": variant % 2,
        "ability_randomization_minibosses": variant % 2,
        "ability_randomization_boss_spawns": variant % 2,
        "room_sanity": variant % 2, "area_keys": (variant + 1) % 2,
    }
    # The earlier union accepted this exact native sample. Removing the now-optional
    # Green Spark progression flag changes fill ordering, placing the Radish key
    # behind its own area gate. Keep this strict refusal and the earlier history.
    if (seed, mode, gating, accessibility) == (8675309, 0, 1, "minimal"):
        from .. import check_accessibility
        expected = json.loads((Path(__file__).parent / "data/green138-generation-contract.json").read_text())[
            "current_native8675309"]
        original = check_accessibility.validate_all_checks
        inspected: list[bool] = []

        def inspect_dependency(multiworld: MultiWorld, players: Iterable[int]) -> None:
            state = CollectionState(multiworld)
            state.sweep_for_advancements()
            location = multiworld.get_location("Radish Ruins 8-12 - Lever", 1)
            assert location.item and location.item.name == "Radish Ruins - Area Key"
            assert not state.has("Radish Ruins - Area Key", 1)
            assert not location.can_reach(state)
            assert multiworld.completion_condition[1](state)
            checks = [loc for loc in multiworld.get_locations(1) if loc.address is not None]
            assert len(checks) == 124 and all(loc.item is not None for loc in checks)
            assert sum(not loc.can_reach(state) for loc in checks) == expected["unreachable_count"] == 12
            inventory = multiworld.get_all_state()  # Diagnostic only, never used for the progression verdict.
            assert all(loc.can_reach(inventory) for loc in checks)
            inspected.append(True)
            original(multiworld, players)

        monkeypatch.setattr(check_accessibility, "validate_all_checks", inspect_dependency)
        with pytest.raises(check_accessibility.KirbyAmCheckAccessibilityError) as caught:
            _generate(monkeypatch, tmp_path, seed, [options])
        message = str(caught.value)
        assert inspected == [True]
        assert message == expected["error"]
        assert hashlib.sha256(message.encode()).hexdigest() == expected["error_sha256"] == (
            "2ff594b5140dcd8a77c23b9f772bfd995e6d6cc07cad4a33a11e5399d06e49d5")
        assert "unfilled=[]; unavailable even with all inventory=[]" in message
        assert not tuple((tmp_path / "output").glob("*.zip"))
        return
    # Source-mode 1/2 refusals retain their existing exact sample boundaries.
    if seed == 8675309 and mode in (1, 2) and gating == 1 and accessibility == "minimal":
        from ..check_accessibility import KirbyAmCheckAccessibilityError
        with pytest.raises(KirbyAmCheckAccessibilityError) as caught:
            _generate(monkeypatch, tmp_path, seed, [options])
        message = str(caught.value)
        assert "Player 1" in message and "Radish Ruins - Big Switch" in message
        assert "unfilled=[]; unavailable even with all inventory=[]" in message
        assert not tuple((tmp_path / "output").glob("*.zip"))
        return
    multiworld, decoded, archive = _generate(monkeypatch, tmp_path, seed, [options])
    _assert_slot_contract(multiworld, decoded, _gate_words(archive), 1)


@pytest.mark.parametrize("seed", SEEDS)
def test_mixed_multiworld_and_explicit_cutter_inventory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    seed: int,
) -> None:
    options = [
        {"ability_randomization_mode": 0, "ability_gating": 1, "accessibility": "full"},
        {"ability_randomization_mode": 1, "ability_gating": 0, "accessibility": "minimal",
         "ability_randomization_statues": 1, "start_inventory": {"Cutter Ability": 2}},
        {"ability_randomization_mode": 2, "ability_gating": 1, "accessibility": "full",
         "ability_randomization_no_ability_weight": 100, "ability_randomization_statues": 1},
    ]
    if seed == 1042:
        from ..check_accessibility import KirbyAmCheckAccessibilityError
        with pytest.raises(KirbyAmCheckAccessibilityError) as caught:
            _generate(monkeypatch, tmp_path, seed, options)
        message = str(caught.value)
        assert "Player 2" in message and "Radish Ruins - Big Switch" in message
        assert "Rainbow Route 1-06 (Lower) - Small Chest" in message
        assert "unfilled=[]; unavailable even with all inventory=[]" in message
        assert not tuple((tmp_path / "output").glob("*.zip"))
        return
    multiworld, decoded, archive = _generate(monkeypatch, tmp_path, seed, options)
    gates = _gate_words(archive)
    for player in multiworld.player_ids:
        _assert_slot_contract(multiworld, decoded, gates, player, explicit=2 if player == 2 else 0)


@pytest.mark.parametrize("gating", [0, 1])
def test_explicit_cutter_start_keeps_requested_count(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    gating: bool,
) -> None:
    multiworld, decoded, archive = _generate(monkeypatch, tmp_path, 1042, [{
        "ability_gating": gating, "start_inventory": {"Cutter Ability": 3},
    }])
    _assert_slot_contract(multiworld, decoded, _gate_words(archive), 1, explicit=3)


@pytest.mark.asyncio
@pytest.mark.parametrize("legacy", [False, True])
async def test_client_cutter_gate_respects_seed_policy_and_received_history(
    mock_bizhawk_context: Any,
    legacy: bool,
) -> None:
    from unittest.mock import patch
    from NetUtils import NetworkItem
    from ..enemy_ability_data import GATEABLE_ENEMY_COPY_ABILITIES
    from .test_start_inventory_protocol import validated_client

    ctx = mock_bizhawk_context
    client = await cast(Callable[[Any], Awaitable[KirbyAmClient]], validated_client)(ctx)
    ctx.slot_data = {
        "ability_gating": True,
        "ability_gateable_abilities": [name for name in GATEABLE_ENEMY_COPY_ABILITIES
                                       if not legacy or name != "Cutter"],
        "ability_unlock_items": {"Cutter": "Cutter Ability"},
    }
    memory: dict[int, bytes] = {}

    async def read(_ctx: Any, requests: list[tuple[int, int, str]]) -> list[bytes]:
        return [memory.get(address, bytes(size)) for address, size, _domain in requests]

    async def write(_ctx: Any, requests: list[tuple[int, bytes, str]]) -> None:
        for address, value, _domain in requests:
            memory[address] = value

    with patch("worlds.kirbyam.client.bizhawk.read", side_effect=read), \
            patch("worlds.kirbyam.client.bizhawk.write", side_effect=write):
        for received in ([], [NetworkItem(CUTTER, -2, 0)]):
            ctx.items_received = received
            for _ in range(2):
                memory.clear()  # Cold runtime recovery and repeated authoritative history.
                client.on_package(ctx, "Connected", {})
                client.on_package(ctx, "ReceivedItems", {"index": 0, "items": received})
                await client._sync_enemy_copy_ability_runtime_config(ctx)
                gate = int.from_bytes(memory[cast(int, client._transport_addr("ability_gate_mask_runtime"))], "little")
                unlocked = int.from_bytes(
                    memory[cast(int, client._transport_addr("ability_unlock_mask_runtime"))], "little")
                assert bool(gate & (1 << 6)) == (not legacy)
                assert bool(unlocked & (1 << 6)) == bool(received)
                from ..data import data
                assert set(memory) <= set(data.transport_ram_addresses.values())
