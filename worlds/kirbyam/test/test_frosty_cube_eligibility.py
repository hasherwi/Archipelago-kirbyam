"""Retail Frosty projectiles grant Normal, independently of Frosty's Ice grant."""
import random
import struct

import pytest

from ..ability_randomization import build_enemy_copy_ability_policy
from ..enemy_ability_runtime_patch import (
    build_enemy_copy_runtime_patch_writes,
    build_enemy_source_runtime_config,
)


@pytest.mark.parametrize("mode", [1, 2], ids=["shuffled", "completely_random"])
@pytest.mark.parametrize("passive", [False, True])
@pytest.mark.parametrize("boss_spawns", [False, True])
def test_frosty_cubes_respect_native_no_ability_exclusion(mode, passive, boss_spawns):
    policy = build_enemy_copy_ability_policy(
        random.Random(908), mode, boss_spawns, True,
        include_passive_enemies=passive, whitelist=["Hammer"], no_ability_weight=0,
    )
    writes = build_enemy_copy_runtime_patch_writes(policy)
    _, *words = struct.unpack("<9I", build_enemy_source_runtime_config(policy))
    # USA object table types A6/A7 both contain zero. InitObject copies this
    # byte; CreateMrFrostyIceCube never overrides it. The defeated miniboss's
    # separate type26 entry grants Ice and must remain independently eligible.
    for address, native_type in [(0x3525DE, 0xA6), (0x3525F6, 0xA7)]:
        included = boss_spawns and passive
        assert (address in writes) is included
        assert bool(words[native_type // 32] & (1 << (native_type % 32))) is included
        retail_byte = 0
        patched_byte = writes.get(address, retail_byte)
        assert patched_byte == (17 if included else retail_byte)
    assert writes[0x351B8E] == 17
    assert words[0x26 // 32] & (1 << (0x26 % 32))
