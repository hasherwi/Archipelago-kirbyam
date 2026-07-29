"""Per-seed ROM config tests for direct statue runtime rerolls."""

from __future__ import annotations

import random
from types import SimpleNamespace
from typing import Any, cast

from worlds.Files import APTokenTypes

from ..ability_randomization import build_enemy_copy_ability_policy
from ..options import AbilityRandomizationMode
from ..rom import ABILITY_RANDOMIZATION_STATUES_CONFIG_ROM_OFFSET, write_tokens


class _DummyPatch:
    def __init__(self) -> None:
        self.token_writes: list[tuple[int, int, bytes]] = []
        self.files: dict[str, bytes] = {}

    def write_token(self, token_type: int, address: int, payload: bytes) -> None:
        self.token_writes.append((token_type, address, payload))

    def get_token_binary(self) -> bytes:
        return b"dummy-token-binary"

    def write_file(self, name: str, data: bytes) -> None:
        self.files[name] = data


def _make_world(mode: int, *, randomize_statues: bool) -> SimpleNamespace:
    return SimpleNamespace(
        auth=b"0123456789ABCDEF",
        options=SimpleNamespace(
            ability_randomization_mode=SimpleNamespace(value=mode),
            ability_randomization_statues=SimpleNamespace(value=randomize_statues),
        ),
    )


def _statue_config_payload(patch: _DummyPatch) -> bytes:
    matches = [
        payload
        for token_type, address, payload in patch.token_writes
        if token_type == APTokenTypes.WRITE
        and address == ABILITY_RANDOMIZATION_STATUES_CONFIG_ROM_OFFSET
    ]
    assert len(matches) == 1
    return matches[0]


def test_write_tokens_disables_direct_statue_runtime_rerolls_explicitly() -> None:
    world = _make_world(AbilityRandomizationMode.option_off, randomize_statues=False)
    patch = _DummyPatch()

    write_tokens(cast(Any, world), cast(Any, patch))

    assert _statue_config_payload(patch) == (0).to_bytes(4, "little")


def test_write_tokens_enables_direct_statue_runtime_rerolls_explicitly() -> None:
    world = _make_world(
        AbilityRandomizationMode.option_completely_random,
        randomize_statues=True,
    )
    world._enemy_copy_ability_policy = build_enemy_copy_ability_policy(
        random.Random(20260729),
        AbilityRandomizationMode.option_completely_random,
        include_boss_spawns=True,
        include_minibosses=True,
    )
    patch = _DummyPatch()

    write_tokens(cast(Any, world), cast(Any, patch))

    assert _statue_config_payload(patch) == (1).to_bytes(4, "little")
