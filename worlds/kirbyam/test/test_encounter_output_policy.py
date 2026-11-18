"""The complete encounter census must agree with production runtime eligibility.

Unconfigured native effects (notably Wait/mixing) are not direct grants. This
checks patch eligibility, not whether those objects can be interacted with.
"""
import random
import struct

import pytest

from ..ability_randomization import build_enemy_copy_ability_policy
from ..ability_source_inventory import source_inventory, resolve_inventory_source
from ..enemy_ability_runtime_patch import build_enemy_copy_runtime_patch_writes, build_enemy_source_runtime_config


UNCONFIGURED = tuple(row for row in source_inventory().values()
                     if row['source_type'] == 'encounter_spawn' and row['source_key'] is None)


@pytest.mark.parametrize('mode', [0, 1, 2])
@pytest.mark.parametrize('seed', [0, 17, 427])
def test_complete_unconfigured_encounter_census_stays_out_of_runtime_assignment(mode, seed):
    policy = build_enemy_copy_ability_policy(random.Random(seed), mode, True, True, True,
                                             include_passive_enemies=True)
    writes = build_enemy_copy_runtime_patch_writes(policy, include_statues=True)
    words = struct.unpack('<9I', build_enemy_source_runtime_config(policy))
    assert len(UNCONFIGURED) == 300
    assert len({row['type_id'] for row in UNCONFIGURED}) == 32
    for row in UNCONFIGURED:
        native_type = row['type_id']
        assert 0x35164E + 24 * native_type not in writes, row['id']
        assert not words[1 + (native_type >> 5)] & (1 << (native_type & 31)), row['id']


@pytest.mark.parametrize('row', UNCONFIGURED, ids=lambda row: row['id'])
def test_unconfigured_output_cannot_be_presented_as_a_direct_ability(row):
    with pytest.raises(ValueError, match='Unresolved physical ability grant'):
        resolve_inventory_source({'inventory_id': row['id'], 'source_key': 'WADDLE_DOO',
                                  'generation_evidence': 'fixture', 'lifetime_evidence': 'fixture'},
                                 row['native_room'], advanced=True)
