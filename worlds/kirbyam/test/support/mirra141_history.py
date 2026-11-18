"""Reverse only the pinned Mirra additions in frozen historical contracts."""
from copy import deepcopy
from .kibble310_history import digest

EAST_TARGET = 'mirra_141_east_moonlight'
EAST_OWNER = 'REGION_RAINBOW_ROUTE/ROOM_1_41__LOGIC__EAST_MOONLIGHT'
TARGET = 'mirra_141_top_mustard'
OWNER = 'REGION_RAINBOW_ROUTE/ROOM_1_41__LOGIC__TOP_MUSTARD'


def before_mirra141_targets(rows):
    result = []
    for row in rows:
        if row['target']['id'] == 'normal_815_vitality':
            assert row['owner'] == 'REGION_OLIVE_OCEAN/ROOM_6_CHEST_1'
            assert digest({k: v for k, v in row['target'].items() if k != 'region'}) == 'f90ff17ad62d31b79812b6281f725386cd2c6665766a9c0b7c6319f6404335d0'
        elif row['target']['id'] == 'normal_534_room15_entry':
            assert row['owner'] == 'REGION_RAINBOW_ROUTE/ROOM_1_34'
            assert digest({k: v for k, v in row['target'].items() if k != 'region'}) == 'c278b3911a413023b1862cf1ee7ecdf3b9bdcd8880b47e7e2f99847793e91eb9'
        elif row['target']['id'] == 'normal_534_mustard_entry':
            assert row['owner'] == 'REGION_RAINBOW_ROUTE/ROOM_1_34'
            assert row['target'].get('region', row['owner']) == row['owner']
            assert digest({k: v for k, v in row['target'].items() if k != 'region'}) == 'fc15b9ec9af07ecec1d1c938926749300f56e62ffa583f99aa7259486a78458c'
        elif row['target']['id'] == 'mirra_811_olive':
            assert row['owner'] == 'REGION_OLIVE_OCEAN/ROOM_6_10'
            assert row['target'].get('region', row['owner']) == row['owner']
            assert digest({k: v for k, v in row['target'].items() if k != 'region'}) == '6b909bdbf7974e628b643dbad8cd139462bb0eab92429503feb01657fb5c31bc'
        elif row['target']['id'] == 'mirra_117_carrot':
            assert row['owner'] == 'REGION_RAINBOW_ROUTE/ROOM_1_24'
            assert row['target'].get('region', row['owner']) == row['owner']
            assert digest({k: v for k, v in row['target'].items() if k != 'region'}) == '0baa3f5839ea311b821629ee68d32b9b0570045d1e90012b2b58e9b511380f1d'
        elif row['target']['id'] == EAST_TARGET:
            assert row['owner'] == EAST_OWNER
            assert digest(row['target']) == '020e2c9b461897ee37349d474a340458b0fa47d781d955b1a7f1fd396146d48f'
        elif row['target']['id'] == TARGET:
            assert row['owner'] == OWNER
            assert digest(row['target']) == '2e7f9f36c385cddcfe449fa2f197e39a7f6a663e9c37756884a59cd305e7ebd9'
        else:
            result.append(row)
    return result


def before_mirra141_surfaces(rows):
    result = deepcopy(rows)
    for row in result:
        if (row['owner'], row['kind'], row['target']) == ('REGION_OLIVE_OCEAN/ROOM_6_CHEST_1', 'location', 'VITALITY_CHEST_OLIVE_OCEAN'):
            assert row['requirement'] is None
            row['requirement'] = 'can_break_block'
        if (row['owner'], row['kind'], row['target']) == ('REGION_RAINBOW_ROUTE/ROOM_1_34', 'exit', 'REGION_MUSTARD_MOUNTAIN/ROOM_4_15'):
            assert row['requirement'] is None
            row['requirement'] = 'can_break_block'
        if (row['owner'], row['kind'], row['target']) == ('REGION_RAINBOW_ROUTE/ROOM_1_34', 'exit', 'REGION_MUSTARD_MOUNTAIN/ROOM_4_CHEST'):
            assert row['requirement'] is None
            row['requirement'] = 'can_break_block'
        if (row['owner'], row['kind'], row['target']) == ('REGION_OLIVE_OCEAN/ROOM_6_10', 'exit', 'REGION_OLIVE_OCEAN/ROOM_6_15'):
            assert row['requirement'] == 'can_swim'
            row['requirement'] = {'all': ['can_swim', 'can_break_block', 'can_mirra']}
        if (row['owner'], row['kind'], row['target']) == ('REGION_RAINBOW_ROUTE/ROOM_1_24', 'exit', 'REGION_CARROT_CASTLE/ROOM_5_02'):
            assert row['requirement'] is None
            row['requirement'] = {'all': ['can_break_block', 'can_mirra']}
        if (row['owner'], row['kind'], row['target']) == (EAST_OWNER, 'exit', 'REGION_MOONLIGHT_MANSION/ROOM_2_16'):
            assert row['requirement'] is None
            row['requirement'] = 'can_mirra'
        if (row['owner'], row['kind'], row['target']) == (OWNER, 'exit', 'REGION_MUSTARD_MOUNTAIN/ROOM_4_07'):
            assert row['requirement'] is None
            row['requirement'] = 'can_mirra'
    return result


def catalog_before_mirra141(catalog):
    result = deepcopy(catalog)
    assert (result['witnesses'], result['variants']) == (156, 312)
    normal815 = [r for r in result['graphs'] if r['target'] == 'normal_815_vitality']
    assert digest(normal815) == '7e61b2b084c7826fa2e46dbe6e25beeca1a19f1baa5e3a0ae62aa091980ebda9'
    result['graphs'] = [r for r in result['graphs'] if r['target'] != 'normal_815_vitality']
    assert result['capability_providers'].pop('normal_815_vitality_sequence') == ['Normal']
    prefix533 = [r for r in result['graphs'] if r['target'] == 'normal_534_room15_entry']
    assert digest(prefix533) == '32463a805c69b9957be9e243137ec4d9cdd95d18a6165a1425fee8c0c132f8be'
    result['graphs'] = [r for r in result['graphs'] if r['target'] != 'normal_534_room15_entry']
    prefix534 = [r for r in result['graphs'] if r['target'] == 'normal_534_mustard_entry']
    assert digest(prefix534) == '57b08f4dc6003ee3fdeab99ca6c235822fe0c260a8ff986291bb6f62abd0269a'
    result['graphs'] = [r for r in result['graphs'] if r['target'] != 'normal_534_mustard_entry']
    for capability in ('normal_534_twister_payload', 'normal_534_dee_payload'):
        assert result['capability_providers'].pop(capability) == ['Normal']
    assert result['sources'].pop('WADDLE_DEE@0x088B596C') == [{'source_key': 'WADDLE_DEE', 'identity': '0x088B596C', 'renewable': False, 'documented_retry': False}]
    added811 = [r for r in result['graphs'] if r['target'] == 'mirra_811_olive']
    assert digest(added811) == '944ebdddbfcc9881bfd9a219e5d30f4e2d258436a0252c9c9d836bc6270e9509'
    result['graphs'] = [r for r in result['graphs'] if r['target'] != 'mirra_811_olive']
    assert result['capability_providers'].pop('mirra_811_normal_puff') == ['Normal']
    added117 = [r for r in result['graphs'] if r['target'] == 'mirra_117_carrot']
    assert digest(added117) == 'cfb56b1b78ab4a4e97379176dd68b4c3317e695a81b76584736a3de1e9328297'
    result['graphs'] = [r for r in result['graphs'] if r['target'] != 'mirra_117_carrot']
    for capability in ('mirra_117_upper_payload', 'mirra_117_lower_payload', 'mirra_117_normal_clearance'):
        assert result['capability_providers'].pop(capability) == ['Normal']
    assert result['sources'].pop('WADDLE_DOO@0x088B9904') == [{'source_key': 'WADDLE_DOO', 'identity': '0x088B9904', 'renewable': False, 'documented_retry': False}]
    assert result['sources'].pop('WADDLE_DEE@0x088B9874') == [{'source_key': 'WADDLE_DEE', 'identity': '0x088B9874', 'renewable': False, 'documented_retry': False}]
    east = [r for r in result['graphs'] if r['target'] == EAST_TARGET]
    assert digest(east) == '506e57b0add54cc3ca9049108938910ba86320ef50c50ffe5c9fc9ae9e6e7bf8'
    assert result['capability_providers'].pop('mirra_141_east_normal_puff') == ['Normal']
    result['graphs'] = [r for r in result['graphs'] if r['target'] != EAST_TARGET]
    added = [r for r in result['graphs'] if r['target'] == TARGET]
    assert digest(added) == '587a1664dc805138ba2b4134a49743e7c040e264ccb0594a98150b5e4f65e055'
    assert result['capability_providers'].pop('mirra_141_top_normal_puff') == ['Normal']
    result['graphs'] = [r for r in result['graphs'] if r['target'] != TARGET]
    result['witnesses'], result['variants'] = 149, 298
    return result
