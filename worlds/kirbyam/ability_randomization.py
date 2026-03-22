"""Deterministic enemy copy-ability remap helpers for KirbyAM.

Issue #111 introduces option-level randomization for enemy-granted copy
abilities using a conservative whitelist. This module is intentionally pure
Python so generation/test behavior remains deterministic and easy to validate.
"""

from __future__ import annotations

import random
from typing import Iterable

from .options import EnemyCopyAbilityRandomization

# Conservative whitelist used by issue #111. Ability names align with existing
# gate/source terminology in rules.py and design notes.
VALID_ENEMY_COPY_ABILITIES: tuple[str, ...] = (
    "Burning",
    "Cutter",
    "Fire",
    "Hammer",
    "Laser",
    "Mini",
    "Missile",
    "Needle",
    "Parasol",
    "Sleep",
    "Spark",
    "Stone",
    "Sword",
    "Tornado",
    "UFO",
)


def _normalize_whitelist(values: Iterable[str]) -> list[str]:
    normalized = sorted({value.strip() for value in values if value and value.strip()})
    if not normalized:
        raise ValueError("enemy copy-ability whitelist cannot be empty")
    return normalized


def build_enemy_copy_ability_remap(
    rng: random.Random,
    mode: int,
    whitelist: Iterable[str] = VALID_ENEMY_COPY_ABILITIES,
) -> dict[str, str]:
    """Build a deterministic enemy ability remap table for slot-data.

    Returns an identity mapping for vanilla mode, and a seeded permutation for
    whitelist shuffle mode.
    """
    ordered = _normalize_whitelist(whitelist)

    if mode == EnemyCopyAbilityRandomization.option_vanilla:
        return {name: name for name in ordered}

    if mode != EnemyCopyAbilityRandomization.option_shuffle_whitelist:
        raise ValueError(f"unsupported enemy copy-ability randomization mode: {mode}")

    shuffled = list(ordered)
    rng.shuffle(shuffled)
    return {source: target for source, target in zip(ordered, shuffled)}


def remap_is_whitelist_preserving(remap: dict[str, str], whitelist: Iterable[str]) -> bool:
    """Validate remap source/target keys stay within the supplied whitelist."""
    ordered = set(_normalize_whitelist(whitelist))
    return set(remap.keys()) == ordered and set(remap.values()) == ordered
