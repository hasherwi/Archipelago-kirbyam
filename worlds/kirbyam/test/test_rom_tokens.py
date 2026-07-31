"""Tests for KirbyAM ROM token generation behavior."""

from __future__ import annotations

import random
from types import SimpleNamespace
from typing import Any, cast

import pytest
import worlds.kirbyam.rom as rom_module

from worlds.Files import APTokenTypes

from ..ability_randomization import build_enemy_copy_ability_policy
from ..options import AbilityRandomizationMode
from ..enemy_ability_data import ABILITY_NAME_TO_ID
from ..enemy_ability_runtime_patch import build_statue_runtime_allowed_mask
from ..rom import (
    STARTING_KIRBY_COLOR_INITIAL_ROM_OFFSET,
    ABILITY_GATE_MASK_INITIAL_ROM_OFFSET,
    ABILITY_RANDOMIZATION_STATUE_ALLOWED_MASK_ROM_OFFSET,
    write_tokens,
)


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


def _make_world(
    mode: int,
    *,
    randomize_statues: bool = False,
    ability_gating: bool = True,
    starting_color_id: int = 0,
) -> SimpleNamespace:
    world = SimpleNamespace(
        auth=b"0123456789ABCDEF",
        options=SimpleNamespace(
            ability_randomization_mode=SimpleNamespace(value=mode),
            ability_randomization_statues=SimpleNamespace(value=randomize_statues),
            ability_gating=SimpleNamespace(value=ability_gating),
        ),
    )
    world._get_resolved_starting_kirby_color = lambda: (
        starting_color_id,
        "Test Color",
    )
    return world


def test_write_tokens_bakes_resolved_starting_color() -> None:
    world = _make_world(
        AbilityRandomizationMode.option_off,
        starting_color_id=7,
    )
    patch = _DummyPatch()

    write_tokens(cast(Any, world), cast(Any, patch))

    assert (
        APTokenTypes.WRITE,
        STARTING_KIRBY_COLOR_INITIAL_ROM_OFFSET,
        (7).to_bytes(4, "little"),
    ) in patch.token_writes


def test_write_tokens_rejects_invalid_resolved_starting_color() -> None:
    world = _make_world(
        AbilityRandomizationMode.option_off,
        starting_color_id=14,
    )
    patch = _DummyPatch()

    with pytest.raises(ValueError, match="within 0..13"):
        write_tokens(cast(Any, world), cast(Any, patch))


def test_write_tokens_rejects_missing_policy_for_non_vanilla_mode() -> None:
    world = _make_world(AbilityRandomizationMode.option_shuffled)
    patch = _DummyPatch()

    with pytest.raises(ValueError, match="enemy_copy_ability_policy must be initialized"):
        write_tokens(cast(Any, world), cast(Any, patch))


def test_write_tokens_emits_runtime_enemy_writes_for_non_vanilla_mode() -> None:
    world = _make_world(AbilityRandomizationMode.option_shuffled)
    world._enemy_copy_ability_policy = build_enemy_copy_ability_policy(
        random.Random(20260324),
        AbilityRandomizationMode.option_shuffled,
        include_boss_spawns=True,
        include_minibosses=True,
    )

    patch = _DummyPatch()
    write_tokens(cast(Any, world), cast(Any, patch))

    # Auth token write + many single-byte ability remap writes.
    single_byte_writes = [
        w for w in patch.token_writes
        if w[0] == APTokenTypes.WRITE and len(w[2]) == 1
    ]
    assert single_byte_writes
    assert "token_data.bin" in patch.files


def test_write_tokens_allows_non_vanilla_mode_with_no_runtime_writes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    world = _make_world(AbilityRandomizationMode.option_shuffled)
    world._enemy_copy_ability_policy = build_enemy_copy_ability_policy(
        random.Random(20260324),
        AbilityRandomizationMode.option_shuffled,
        include_boss_spawns=True,
        include_minibosses=True,
    )
    monkeypatch.setattr(
        rom_module,
        "build_enemy_copy_runtime_patch_writes",
        lambda policy, include_statues=False: {},
    )

    patch = _DummyPatch()
    write_tokens(cast(Any, world), cast(Any, patch))

    single_byte_writes = [
        w for w in patch.token_writes
        if w[0] == APTokenTypes.WRITE and len(w[2]) == 1
    ]
    assert not single_byte_writes
    assert "token_data.bin" in patch.files


@pytest.mark.parametrize(
    ("mode", "randomize_statues"),
    [
        (AbilityRandomizationMode.option_off, False),
        (AbilityRandomizationMode.option_off, True),
        (AbilityRandomizationMode.option_shuffled, False),
        (AbilityRandomizationMode.option_completely_random, False),
    ],
)
def test_write_tokens_emits_explicit_disabled_statue_mask(
    mode: int,
    randomize_statues: bool,
) -> None:
    world = _make_world(mode, randomize_statues=randomize_statues)
    if mode != AbilityRandomizationMode.option_off:
        world._enemy_copy_ability_policy = build_enemy_copy_ability_policy(
            random.Random(20260729),
            mode,
            include_boss_spawns=True,
            include_minibosses=True,
        )
    patch = _DummyPatch()

    write_tokens(cast(Any, world), cast(Any, patch))

    config_writes = [
        write
        for write in patch.token_writes
        if write[1] == ABILITY_RANDOMIZATION_STATUE_ALLOWED_MASK_ROM_OFFSET
    ]
    assert config_writes == [
        (
            APTokenTypes.WRITE,
            ABILITY_RANDOMIZATION_STATUE_ALLOWED_MASK_ROM_OFFSET,
            (0).to_bytes(4, "little"),
        )
    ]


def test_write_tokens_emits_exact_statue_runtime_pool_mask() -> None:
    world = _make_world(
        AbilityRandomizationMode.option_completely_random,
        randomize_statues=True,
    )
    world._enemy_copy_ability_policy = build_enemy_copy_ability_policy(
        random.Random(20260729),
        AbilityRandomizationMode.option_completely_random,
        include_boss_spawns=False,
        include_minibosses=False,
        include_minny=False,
        include_passive_enemies=True,
        no_ability_weight=100,
        whitelist=("Beam", "Mini", "Sword"),
    )
    patch = _DummyPatch()

    write_tokens(cast(Any, world), cast(Any, patch))

    expected_mask = (
        (1 << ABILITY_NAME_TO_ID["Beam"])
        | (1 << ABILITY_NAME_TO_ID["Sword"])
    )
    assert build_statue_runtime_allowed_mask(
        world._enemy_copy_ability_policy,
        include_statues=True,
    ) == expected_mask
    assert (
        APTokenTypes.WRITE,
        ABILITY_RANDOMIZATION_STATUE_ALLOWED_MASK_ROM_OFFSET,
        expected_mask.to_bytes(4, "little"),
    ) in patch.token_writes


def test_write_tokens_statue_mask_is_written_once() -> None:
    world = _make_world(
        AbilityRandomizationMode.option_shuffled,
        randomize_statues=True,
    )
    world._enemy_copy_ability_policy = build_enemy_copy_ability_policy(
        random.Random(8),
        AbilityRandomizationMode.option_shuffled,
        include_boss_spawns=True,
        include_minibosses=True,
    )
    patch = _DummyPatch()

    write_tokens(cast(Any, world), cast(Any, patch))

    assert sum(
        address == ABILITY_RANDOMIZATION_STATUE_ALLOWED_MASK_ROM_OFFSET
        for _, address, _ in patch.token_writes
    ) == 1


@pytest.mark.parametrize("ability_gating", [False, True])
def test_write_tokens_emits_seed_initial_gate_mask(ability_gating: bool) -> None:
    world = _make_world(
        AbilityRandomizationMode.option_off,
        ability_gating=ability_gating,
    )
    patch = _DummyPatch()

    write_tokens(cast(Any, world), cast(Any, patch))

    expected_mask = 0
    if ability_gating:
        from ..enemy_ability_data import GATEABLE_ENEMY_COPY_ABILITIES

        expected_mask = sum(
            1 << ABILITY_NAME_TO_ID[name]
            for name in GATEABLE_ENEMY_COPY_ABILITIES
        )
    assert (
        APTokenTypes.WRITE,
        ABILITY_GATE_MASK_INITIAL_ROM_OFFSET,
        expected_mask.to_bytes(4, "little"),
    ) in patch.token_writes


def test_write_tokens_runtime_config_words_are_each_written_once() -> None:
    world = _make_world(
        AbilityRandomizationMode.option_completely_random,
        randomize_statues=True,
        ability_gating=True,
    )
    world._enemy_copy_ability_policy = build_enemy_copy_ability_policy(
        random.Random(99),
        AbilityRandomizationMode.option_completely_random,
        include_boss_spawns=True,
        include_minibosses=True,
    )
    patch = _DummyPatch()

    write_tokens(cast(Any, world), cast(Any, patch))

    for config_address in (
        ABILITY_GATE_MASK_INITIAL_ROM_OFFSET,
        ABILITY_RANDOMIZATION_STATUE_ALLOWED_MASK_ROM_OFFSET,
    ):
        assert sum(
            address == config_address
            for _, address, _ in patch.token_writes
        ) == 1
