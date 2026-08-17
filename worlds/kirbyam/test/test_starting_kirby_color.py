from __future__ import annotations

from random import Random
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock, patch

import pytest

from .. import KirbyAmWorld
from ..client import KirbyAmClient
from ..colors import (
    STARTING_KIRBY_COLOR_RANDOM_PER_ROOM_OPTION,
    choose_different_kirby_color,
    load_kirby_colors,
)
from ..data import data
from ..options import StartingKirbyColor


def test_starting_kirby_color_framework_random_resolves_to_concrete_color() -> None:
    # Match ConfiguredAreaBoss: use Archipelago Choice's built-in literal `random`
    # rather than a world-specific random_color sentinel.
    with patch("Options.random.choice", return_value=7):
        resolved_option = StartingKirbyColor.from_text("random")

    assert resolved_option.value == 7
    assert resolved_option.current_key == "sapphire"

    world = KirbyAmWorld.__new__(KirbyAmWorld)
    world.options = cast(Any, SimpleNamespace(starting_kirby_color=resolved_option))
    assert KirbyAmWorld._get_resolved_starting_kirby_color(world) == (7, "Sapphire")


def test_starting_kirby_color_has_only_room_transition_custom_random_choice() -> None:
    supported_ids = {color.color_id for color in load_kirby_colors()}

    assert set(StartingKirbyColor.name_lookup) == {
        *supported_ids,
        STARTING_KIRBY_COLOR_RANDOM_PER_ROOM_OPTION,
    }
    assert "random_color" not in StartingKirbyColor.options
    assert StartingKirbyColor.options["random_color_per_room"] == STARTING_KIRBY_COLOR_RANDOM_PER_ROOM_OPTION


def test_world_helper_resolves_room_transition_random_mode_to_initial_color() -> None:
    world = KirbyAmWorld.__new__(KirbyAmWorld)
    world.random = Random(0)
    world.options = cast(Any, SimpleNamespace(
        starting_kirby_color=SimpleNamespace(
            current_key="random_color_per_room",
            value=STARTING_KIRBY_COLOR_RANDOM_PER_ROOM_OPTION,
        ),
    ))

    resolved_color_id, resolved_color_name = KirbyAmWorld._get_resolved_starting_kirby_color(world)
    supported = {color.color_id: color.display_name for color in load_kirby_colors()}

    assert resolved_color_id in supported
    assert resolved_color_name == supported[resolved_color_id]
    assert KirbyAmWorld._starting_kirby_color_randomize_on_room_transition_enabled(world) is True


def test_choose_different_kirby_color_never_repeats_current_color() -> None:
    rng = Random(0)
    for color in load_kirby_colors():
        next_color = choose_different_kirby_color(color.color_id, rng)
        assert next_color.color_id != color.color_id


def test_world_helper_caches_resolved_starting_kirby_color_metadata() -> None:
    world = KirbyAmWorld.__new__(KirbyAmWorld)
    world.options = cast(Any, SimpleNamespace(
        starting_kirby_color=SimpleNamespace(current_key="sapphire", value=7),
    ))

    first = KirbyAmWorld._get_resolved_starting_kirby_color(world)
    # StartingKirbyColor is generated dynamically, so mypy cannot reliably
    # expose Choice.value through the annotated options type here.
    cast(Any, world.options.starting_kirby_color).value = 3
    second = KirbyAmWorld._get_resolved_starting_kirby_color(world)

    assert first == (7, "Sapphire")
    assert second == first


@pytest.mark.asyncio
async def test_client_syncs_starting_kirby_color_runtime_config_once(mock_bizhawk_context: Any) -> None:
    client = KirbyAmClient()
    client.initialize_client()
    mock_bizhawk_context.slot_data = {
        "debug": {"logging": False},
        "starting_kirby_color": 7,
        "starting_kirby_color_name": "Sapphire",
    }

    with (
        patch.dict(
            data.transport_ram_addresses,
            {"starting_kirby_color_id": 0x0203B050},
            clear=False,
        ),
        patch(
            "worlds.kirbyam.client.bizhawk.read",
            new_callable=AsyncMock,
            # First call: mailbox holds sentinel (unsynced).
            side_effect=[
                [(0xFFFFFFFF).to_bytes(4, "little")],
            ],
        ) as mock_read,
        patch(
            "worlds.kirbyam.client.bizhawk.write",
            new_callable=AsyncMock,
        ) as mock_write,
    ):
        client._load_debug_settings(mock_bizhawk_context)
        await client._sync_starting_kirby_color_runtime_config(mock_bizhawk_context)
        await client._sync_starting_kirby_color_runtime_config(mock_bizhawk_context)

    assert mock_read.await_count == 1
    assert mock_write.await_count == 1
    write_payload = mock_write.await_args_list[0].args[1]
    assert write_payload == [(0x0203B050, (7).to_bytes(4, "little"), "System Bus")]


@pytest.mark.asyncio
async def test_client_starting_color_sync_short_circuits_after_initial_sync(mock_bizhawk_context: Any) -> None:
    client = KirbyAmClient()
    client.initialize_client()
    mock_bizhawk_context.slot_data = {
        "debug": {"logging": False},
        "starting_kirby_color": 7,
        "starting_kirby_color_name": "Sapphire",
    }

    with (
        patch.dict(
            data.transport_ram_addresses,
            {"starting_kirby_color_id": 0x0203B050},
            clear=False,
        ),
        patch(
            "worlds.kirbyam.client.bizhawk.read",
            new_callable=AsyncMock,
            side_effect=[[(0xFFFFFFFF).to_bytes(4, "little")]],
        ) as mock_read,
        patch(
            "worlds.kirbyam.client.bizhawk.write",
            new_callable=AsyncMock,
        ) as mock_write,
    ):
        client._load_debug_settings(mock_bizhawk_context)
        await client._sync_starting_kirby_color_runtime_config(mock_bizhawk_context)
        await client._sync_starting_kirby_color_runtime_config(mock_bizhawk_context)

    assert mock_read.await_count == 1
    assert mock_write.await_count == 1


@pytest.mark.asyncio
async def test_client_room_random_sync_preserves_valid_live_color(mock_bizhawk_context: Any) -> None:
    client = KirbyAmClient()
    client.initialize_client()
    mock_bizhawk_context.slot_data = {
        "debug": {"logging": False},
        "starting_kirby_color": 7,
        "starting_kirby_color_name": "Sapphire",
        "starting_kirby_color_randomize_on_room_transition": True,
    }

    with (
        patch.dict(
            data.transport_ram_addresses,
            {"starting_kirby_color_id": 0x0203B050},
            clear=False,
        ),
        patch(
            "worlds.kirbyam.client.bizhawk.read",
            new_callable=AsyncMock,
            side_effect=[[(12).to_bytes(4, "little")]],
        ) as mock_read,
        patch(
            "worlds.kirbyam.client.bizhawk.write",
            new_callable=AsyncMock,
        ) as mock_write,
    ):
        await client._sync_starting_kirby_color_runtime_config(mock_bizhawk_context)

    assert mock_read.await_count == 1
    assert mock_write.await_count == 0
    assert client._starting_kirby_color_synced_id == 12


@pytest.mark.asyncio
async def test_room_transition_random_color_changes_color_and_clears_apply_latch(
    mock_bizhawk_context: Any,
) -> None:
    client = KirbyAmClient()
    client.initialize_client()
    client._room_transition_color_rng = Random(0)
    client._starting_kirby_color_synced_id = 7
    mock_bizhawk_context.slot_data = {
        "starting_kirby_color": 7,
        "starting_kirby_color_name": "Sapphire",
        "starting_kirby_color_randomize_on_room_transition": True,
    }

    with (
        patch.dict(
            data.transport_ram_addresses,
            {
                "starting_kirby_color_id": 0x0203B050,
                "starting_kirby_color_applied": 0x0203B0B8,
            },
            clear=False,
        ),
        patch(
            "worlds.kirbyam.client.bizhawk.write",
            new_callable=AsyncMock,
        ) as mock_write,
    ):
        await client._maybe_randomize_kirby_color_on_room_transition(mock_bizhawk_context, 100)
        await client._maybe_randomize_kirby_color_on_room_transition(mock_bizhawk_context, 100)
        await client._maybe_randomize_kirby_color_on_room_transition(mock_bizhawk_context, 101)

    assert mock_write.await_count == 1
    writes = mock_write.await_args_list[0].args[1]
    next_color_id = int.from_bytes(writes[0][1], "little")
    assert 0 <= next_color_id <= 13
    assert next_color_id != 7
    assert writes[0][0] == 0x0203B050
    assert writes[1] == (0x0203B0B8, (0).to_bytes(4, "little"), "System Bus")
    assert client._starting_kirby_color_synced_id == next_color_id
    assert client._room_transition_color_last_native_room_id == 101


def test_load_kirby_colors_rejects_invalid_key_format() -> None:
    from .. import colors as colors_module

    load_kirby_colors.cache_clear()
    with patch.object(
        colors_module,
        "load_json_data",
        return_value={"colors": [{"key": "bad-key", "id": 1, "name": "Bad"}, {"key": "pink", "id": 0, "name": "Pink"}]},
    ):
        with pytest.raises(ValueError, match="invalid key format"):
            load_kirby_colors()
    load_kirby_colors.cache_clear()


def test_load_kirby_colors_rejects_non_string_key() -> None:
    from .. import colors as colors_module

    load_kirby_colors.cache_clear()
    with patch.object(
        colors_module,
        "load_json_data",
        return_value={"colors": [{"key": None, "id": 0, "name": "Pink"}]},
    ):
        with pytest.raises(ValueError, match="non-string key"):
            load_kirby_colors()
    load_kirby_colors.cache_clear()


def test_load_kirby_colors_rejects_non_string_name() -> None:
    from .. import colors as colors_module

    load_kirby_colors.cache_clear()
    with patch.object(
        colors_module,
        "load_json_data",
        return_value={"colors": [{"key": "pink", "id": 0, "name": None}]},
    ):
        with pytest.raises(ValueError, match="non-string display name"):
            load_kirby_colors()
    load_kirby_colors.cache_clear()


def test_load_kirby_colors_rejects_out_of_range_id() -> None:
    from .. import colors as colors_module

    load_kirby_colors.cache_clear()
    with patch.object(
        colors_module,
        "load_json_data",
        return_value={
            "colors": [{"key": "pink", "id": 0, "name": "Pink"}, {"key": "ultra", "id": 14, "name": "Ultra"}]
        },
    ):
        with pytest.raises(ValueError, match="out of supported range"):
            load_kirby_colors()
    load_kirby_colors.cache_clear()


def test_reset_reconnect_transient_state_clears_starting_color_log_signature() -> None:
    client = KirbyAmClient()
    client.initialize_client()
    client._starting_kirby_color_logged_signature = (7, "Sapphire")
    client._room_transition_color_last_native_room_id = 101

    client._reset_reconnect_transient_state()

    assert client._starting_kirby_color_logged_signature is None
    assert client._room_transition_color_last_native_room_id is None


def test_client_starting_color_config_log_hidden_when_debug_disabled(mock_bizhawk_context: Any) -> None:
    client = KirbyAmClient()
    client.initialize_client()
    client._debug_logging_enabled = False
    mock_bizhawk_context.slot_data = {
        "starting_kirby_color": 0,
        "starting_kirby_color_name": "Pink",
    }

    with patch("CommonClient.logger.info") as mock_info:
        client._log_starting_kirby_color_config_once(mock_bizhawk_context)
        client._log_starting_kirby_color_config_once(mock_bizhawk_context)

    assert mock_info.call_count == 0


def test_client_starting_color_config_log_emits_once_when_debug_enabled(mock_bizhawk_context: Any) -> None:
    client = KirbyAmClient()
    client.initialize_client()
    client._debug_logging_enabled = True
    mock_bizhawk_context.slot_data = {
        "starting_kirby_color": 0,
        "starting_kirby_color_name": "Pink",
    }

    with patch("CommonClient.logger.info") as mock_info:
        client._log_starting_kirby_color_config_once(mock_bizhawk_context)
        client._log_starting_kirby_color_config_once(mock_bizhawk_context)

    assert mock_info.call_count == 1
    assert mock_info.call_args.args[0] == "KirbyAM: configured starting Kirby color is %s (%s)"


def test_client_starting_color_config_log_emits_after_debug_toggle_on(mock_bizhawk_context: Any) -> None:
    client = KirbyAmClient()
    client.initialize_client()
    client._debug_logging_enabled = False
    mock_bizhawk_context.slot_data = {
        "starting_kirby_color": 0,
        "starting_kirby_color_name": "Pink",
    }

    with patch("CommonClient.logger.info") as mock_info:
        client._log_starting_kirby_color_config_once(mock_bizhawk_context)

        client._debug_logging_enabled = True
        client._log_starting_kirby_color_config_once(mock_bizhawk_context)

    assert mock_info.call_count == 1
    assert client._starting_kirby_color_logged_signature == (0, "Pink")


@pytest.mark.asyncio
async def test_client_starting_color_sync_log_hidden_when_debug_disabled(mock_bizhawk_context: Any) -> None:
    client = KirbyAmClient()
    client.initialize_client()
    client._debug_logging_enabled = False
    mock_bizhawk_context.slot_data = {
        "starting_kirby_color": 7,
        "starting_kirby_color_name": "Sapphire",
    }

    with (
        patch.dict(
            data.transport_ram_addresses,
            {"starting_kirby_color_id": 0x0203B050},
            clear=False,
        ),
        patch(
            "worlds.kirbyam.client.bizhawk.read",
            new_callable=AsyncMock,
            side_effect=[[(0xFFFFFFFF).to_bytes(4, "little")]],
        ),
        patch(
            "worlds.kirbyam.client.bizhawk.write",
            new_callable=AsyncMock,
        ),
        patch("CommonClient.logger.info") as mock_info,
    ):
        await client._sync_starting_kirby_color_runtime_config(mock_bizhawk_context)

    assert mock_info.call_count == 0


@pytest.mark.asyncio
async def test_client_game_watcher_logs_starting_color_once_after_initial_ready_transition(
    mock_bizhawk_context: Any,
) -> None:
    client = KirbyAmClient()
    client.initialize_client()
    client._ram_state_loaded = True
    mock_bizhawk_context.slot_data = {
        "starting_kirby_color": 0,
        "starting_kirby_color_name": "Pink",
    }
    mock_bizhawk_context.server = SimpleNamespace(socket=SimpleNamespace(closed=False))
    mock_bizhawk_context.items_received = []
    mock_bizhawk_context.bizhawk_ctx = object()

    with (
        patch.object(client, "_sync_death_link_setting", new=AsyncMock()),
        patch.object(client, "_sync_enemy_copy_ability_runtime_config", new=AsyncMock()),
        patch.object(
            client,
            "_load_debug_settings",
            side_effect=lambda _ctx: setattr(client, "_debug_logging_enabled", True),
        ),
        patch.object(client, "_sync_starting_kirby_color_runtime_config", new=AsyncMock()),
        patch.object(client, "_runtime_gameplay_state", new=AsyncMock(return_value=(False, "menu", None))),
        patch.object(client, "_log_boss_shard_debug_window", new=AsyncMock()),
        patch.object(client, "_display_client_message", new=AsyncMock()),
        patch.object(client, "_deliver_items", new=AsyncMock()),
        patch.object(client, "_maybe_report_goal", new=AsyncMock()),
        patch("CommonClient.logger.info") as mock_info,
    ):
        await client.game_watcher(mock_bizhawk_context)
        await client.game_watcher(mock_bizhawk_context)

    matching = [
        call for call in mock_info.call_args_list
        if call.args and call.args[0] == "KirbyAM: configured starting Kirby color is %s (%s)"
    ]
    assert len(matching) == 1


def test_payload_applies_starting_color_before_create_and_refreshes_live_palette() -> None:
    from pathlib import Path

    payload_dir = Path(__file__).resolve().parents[1] / "kirby_ap_payload"
    payload = (payload_dir / "ap_payload.c").read_text(encoding="utf-8")
    linker = (payload_dir / "linker.ld").read_text(encoding="utf-8")

    # Generation-time path: both single-player starts are redirected to a
    # wrapper that writes the native selected-color state before CreateKirby.
    assert "void ap_on_start_single_player_game(" in payload
    assert "gApStartingKirbyColorInitial" in payload
    assert "KIRBY_SELECTED_COLOR = (int16_t)desired_color" in payload
    assert "KIRBY_PLAYER_COLOR_TABLE[KIRBY_STARTING_COLOR_PLAYER]" in payload
    assert "KIRBY_START_GAME_FN(mode, arg1, rooms, positions, flags)" in payload

    # Runtime recovery path: writing Kirby::color alone is insufficient; the
    # native palette loader must be called after a live Kirby is available.
    assert "KIRBY_STRUCT_COLOR_OFFSET 0xDFu" in payload
    assert "KIRBY_REFRESH_PALETTE_FN(KIRBY_STARTING_COLOR_PLAYER)" in payload
    assert "ap_is_player_kirby_ready" in payload

    # Mutable latch state belongs in EWRAM, not payload .bss/ROM.
    assert "AP_STARTING_KIRBY_COLOR_APPLIED" in payload
    assert "static uint8_t ap_starting_kirby_color_applied" not in payload

    # Preserve the already-shipped gate/statue offsets while adding color first.
    assert "AP_CONFIG_ADDR = 0x0815F694" in linker
    assert linker.index(".apconfig.color") < linker.index(".apconfig.gate")
    assert linker.index(".apconfig.gate") < linker.index(".apconfig.statue")
    assert "SIZEOF(.apconfig) == 12" in linker
