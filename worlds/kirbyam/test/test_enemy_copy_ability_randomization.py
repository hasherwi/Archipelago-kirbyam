"""Tests for enemy copy-ability randomization remap generation (Issue #111)."""

from __future__ import annotations

import random

import pytest

from ..ability_randomization import (
    VALID_ENEMY_COPY_ABILITIES,
    build_enemy_copy_ability_remap,
    remap_is_whitelist_preserving,
)
from ..options import EnemyCopyAbilityRandomization


def test_vanilla_mode_returns_identity_mapping() -> None:
    remap = build_enemy_copy_ability_remap(
        random.Random(12345),
        EnemyCopyAbilityRandomization.option_vanilla,
    )

    assert len(remap) == len(VALID_ENEMY_COPY_ABILITIES)
    assert all(remap[name] == name for name in VALID_ENEMY_COPY_ABILITIES)
    assert remap_is_whitelist_preserving(remap, VALID_ENEMY_COPY_ABILITIES)


def test_shuffle_whitelist_mode_is_deterministic_for_fixed_seed() -> None:
    remap_a = build_enemy_copy_ability_remap(
        random.Random(20260322),
        EnemyCopyAbilityRandomization.option_shuffle_whitelist,
    )
    remap_b = build_enemy_copy_ability_remap(
        random.Random(20260322),
        EnemyCopyAbilityRandomization.option_shuffle_whitelist,
    )

    assert remap_a == remap_b
    assert remap_is_whitelist_preserving(remap_a, VALID_ENEMY_COPY_ABILITIES)


def test_shuffle_whitelist_mode_changes_at_least_one_mapping() -> None:
    remap = build_enemy_copy_ability_remap(
        random.Random(7),
        EnemyCopyAbilityRandomization.option_shuffle_whitelist,
    )

    assert any(source != target for source, target in remap.items())


def test_invalid_mode_raises_value_error() -> None:
    with pytest.raises(ValueError, match="unsupported enemy copy-ability randomization mode"):
        build_enemy_copy_ability_remap(random.Random(1), 999)


def test_empty_whitelist_raises_value_error() -> None:
    with pytest.raises(ValueError, match="enemy copy-ability whitelist cannot be empty"):
        build_enemy_copy_ability_remap(
            random.Random(1),
            EnemyCopyAbilityRandomization.option_shuffle_whitelist,
            whitelist=[],
        )
