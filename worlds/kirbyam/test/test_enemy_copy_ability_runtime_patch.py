"""Tests for runtime ROM writes of enemy copy-ability randomization (Issue #338)."""

from __future__ import annotations

import random

from ..ability_randomization import build_enemy_copy_ability_policy
from ..enemy_ability_runtime_patch import build_enemy_copy_runtime_patch_writes
from ..options import EnemyCopyAbilityRandomization


def test_vanilla_mode_emits_no_runtime_writes() -> None:
    policy = build_enemy_copy_ability_policy(
        random.Random(123),
        EnemyCopyAbilityRandomization.option_vanilla,
        randomize_boss_spawned_ability_grants=True,
        randomize_miniboss_ability_grants=True,
    )

    writes = build_enemy_copy_runtime_patch_writes(policy)
    assert writes == {}


def test_shuffled_mode_emits_deterministic_runtime_writes() -> None:
    policy_1 = build_enemy_copy_ability_policy(
        random.Random(20260324),
        EnemyCopyAbilityRandomization.option_shuffled,
        randomize_boss_spawned_ability_grants=True,
        randomize_miniboss_ability_grants=True,
    )
    policy_2 = build_enemy_copy_ability_policy(
        random.Random(20260324),
        EnemyCopyAbilityRandomization.option_shuffled,
        randomize_boss_spawned_ability_grants=True,
        randomize_miniboss_ability_grants=True,
    )

    writes_1 = build_enemy_copy_runtime_patch_writes(policy_1)
    writes_2 = build_enemy_copy_runtime_patch_writes(policy_2)

    assert writes_1 == writes_2
    assert writes_1

    # Waddle Doo and Wheelie are known vanilla non-zero enemy-grant entries.
    assert 0x3517FE in writes_1
    assert 0x351906 in writes_1


def test_miniboss_toggle_excludes_miniboss_runtime_writes() -> None:
    policy = build_enemy_copy_ability_policy(
        random.Random(42),
        EnemyCopyAbilityRandomization.option_shuffled,
        randomize_boss_spawned_ability_grants=True,
        randomize_miniboss_ability_grants=False,
    )

    writes = build_enemy_copy_runtime_patch_writes(policy)

    # Bonkers miniboss entry from reference table.
    assert 0x351BA6 not in writes
    # Normal enemy entry still present.
    assert 0x3518BE in writes


def test_boss_spawned_toggle_excludes_object_runtime_writes() -> None:
    policy = build_enemy_copy_ability_policy(
        random.Random(84),
        EnemyCopyAbilityRandomization.option_shuffled,
        randomize_boss_spawned_ability_grants=False,
        randomize_miniboss_ability_grants=True,
    )

    writes = build_enemy_copy_runtime_patch_writes(policy)

    # Known boss-spawned object entry from reference table.
    assert 0x352686 not in writes
    # Miniboss entry still present.
    assert 0x351BA6 in writes


def test_completely_random_mode_emits_deterministic_runtime_writes() -> None:
    policy_1 = build_enemy_copy_ability_policy(
        random.Random(777),
        EnemyCopyAbilityRandomization.option_completely_random,
        randomize_boss_spawned_ability_grants=True,
        randomize_miniboss_ability_grants=True,
    )
    policy_2 = build_enemy_copy_ability_policy(
        random.Random(777),
        EnemyCopyAbilityRandomization.option_completely_random,
        randomize_boss_spawned_ability_grants=True,
        randomize_miniboss_ability_grants=True,
    )

    writes_1 = build_enemy_copy_runtime_patch_writes(policy_1)
    writes_2 = build_enemy_copy_runtime_patch_writes(policy_2)

    assert writes_1 == writes_2
    assert writes_1


def test_completely_random_differs_from_shuffled_for_known_address() -> None:
    shuffled_policy = build_enemy_copy_ability_policy(
        random.Random(20260324),
        EnemyCopyAbilityRandomization.option_shuffled,
        randomize_boss_spawned_ability_grants=True,
        randomize_miniboss_ability_grants=True,
    )
    random_policy = build_enemy_copy_ability_policy(
        random.Random(20260324),
        EnemyCopyAbilityRandomization.option_completely_random,
        randomize_boss_spawned_ability_grants=True,
        randomize_miniboss_ability_grants=True,
    )

    shuffled_writes = build_enemy_copy_runtime_patch_writes(shuffled_policy)
    random_writes = build_enemy_copy_runtime_patch_writes(random_policy)

    common_addrs = set(shuffled_writes) & set(random_writes)
    assert common_addrs
    assert any(shuffled_writes[a] != random_writes[a] for a in common_addrs)


def test_non_ability_option_off_excludes_zero_id_entries() -> None:
    """With randomize_non_ability_enemies=False, no-ability enemies must not be patched."""
    policy = build_enemy_copy_ability_policy(
        random.Random(55),
        EnemyCopyAbilityRandomization.option_shuffled,
        randomize_boss_spawned_ability_grants=True,
        randomize_miniboss_ability_grants=True,
        randomize_non_ability_enemies=False,
    )
    writes = build_enemy_copy_runtime_patch_writes(policy)

    # WADDLE_DEE (0x35164E) and BRONTO_BURT (0x351666): no-ability regular enemies.
    assert 0x35164E not in writes
    assert 0x351666 not in writes


def test_non_ability_option_on_includes_zero_id_enemy_entries() -> None:
    """With randomize_non_ability_enemies=True, no-ability enemies must receive patch writes."""
    policy = build_enemy_copy_ability_policy(
        random.Random(99),
        EnemyCopyAbilityRandomization.option_shuffled,
        randomize_boss_spawned_ability_grants=True,
        randomize_miniboss_ability_grants=True,
        randomize_non_ability_enemies=True,
    )
    writes = build_enemy_copy_runtime_patch_writes(policy)

    # WADDLE_DEE (0x35164E) and BRONTO_BURT (0x351666): no-ability regular enemies.
    assert 0x35164E in writes
    assert 0x351666 in writes
    assert writes[0x35164E] != 0  # must not stay Normal
    assert writes[0x351666] != 0


def test_non_ability_option_on_patches_both_droppy_addresses() -> None:
    """DROPPY has two ROM addresses; both must be patched when the option is on."""
    policy = build_enemy_copy_ability_policy(
        random.Random(77),
        EnemyCopyAbilityRandomization.option_shuffled,
        randomize_boss_spawned_ability_grants=True,
        randomize_miniboss_ability_grants=True,
        randomize_non_ability_enemies=True,
    )
    writes = build_enemy_copy_runtime_patch_writes(policy)

    # Both DROPPY addresses must be present and identical (same enemy type -> same shuffle slot).
    assert 0x351AFE in writes
    assert 0x3527D6 in writes
    assert writes[0x351AFE] == writes[0x3527D6]


def test_non_ability_option_on_with_miniboss_toggle_off_excludes_mini_waddle_dee() -> None:
    """WADDLE_DEE_MINI is kind:miniboss; miniboss toggle gates it even when non-ability option is on."""
    policy = build_enemy_copy_ability_policy(
        random.Random(11),
        EnemyCopyAbilityRandomization.option_shuffled,
        randomize_boss_spawned_ability_grants=True,
        randomize_miniboss_ability_grants=False,
        randomize_non_ability_enemies=True,
    )
    writes = build_enemy_copy_runtime_patch_writes(policy)

    # WADDLE_DEE_MINI (0x351B76) is kind:miniboss; excluded by randomize_miniboss_ability_grants=False.
    assert 0x351B76 not in writes
    # Regular no-ability enemy WADDLE_DEE (0x35164E) must still be patched.
    assert 0x35164E in writes


def test_non_ability_option_on_with_miniboss_toggle_on_includes_mini_waddle_dee() -> None:
    """WADDLE_DEE_MINI is patched when both the non-ability option and miniboss toggle are on."""
    policy = build_enemy_copy_ability_policy(
        random.Random(22),
        EnemyCopyAbilityRandomization.option_shuffled,
        randomize_boss_spawned_ability_grants=True,
        randomize_miniboss_ability_grants=True,
        randomize_non_ability_enemies=True,
    )
    writes = build_enemy_copy_runtime_patch_writes(policy)

    assert 0x351B76 in writes
    assert writes[0x351B76] != 0
