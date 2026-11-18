"""Native nuts stay physical outputs without gaining an unconfigured random grant."""
import random
import struct

import pytest

from ..ability_randomization import build_enemy_copy_ability_policy
from ..enemy_ability_runtime_patch import build_enemy_copy_runtime_patch_writes, build_enemy_source_runtime_config


@pytest.mark.parametrize('mode', [0, 1, 2])
@pytest.mark.parametrize('seed', [0, 17, 427])
def test_maximally_enabled_policy_does_not_randomize_unconfigured_nuts(mode, seed):
    policy = build_enemy_copy_ability_policy(random.Random(seed), mode, True, True, True,
                                             include_passive_enemies=True)
    writes = build_enemy_copy_runtime_patch_writes(policy, include_statues=True)
    words = struct.unpack('<9I', build_enemy_source_runtime_config(policy))
    for native_type in (168, 169):
        assert 0x35164E + 24 * native_type not in writes
        assert not words[1 + (native_type >> 5)] & (1 << (native_type & 31))
