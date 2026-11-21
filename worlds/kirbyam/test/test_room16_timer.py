"""The live-random Normal route requires the exact published ROM patch contract."""
from copy import deepcopy

import pytest
from BaseClasses import CollectionState
from .. import room16_timer as timer
from ..rom import KirbyAmPatchExtension, write_tokens
from ..traversal import SourcePolicy
from ..traversal_data import has_graph_access
from ..traversal_rules import static_room16_witness
from .test_traversal import policy
from .test_mini_traversal import make_world
from .test_rom_tokens import _DummyPatch, _make_world
from .test_universal_tracker import reconstruct


def test_no_ability_grant_is_changed_and_historical_slots_remain_closed():
    raw = policy(2, pool=['Beam', 'Bomb'], weight=55).policy
    patched = timer.configure_policy(raw)
    assert patched == {**raw, timer.POLICY_KEY: timer.TIMER_FRAMES}
    for source in ('FOLEY', 'HOT_HEAD', 'WADDLE_DEE'):
        assert SourcePolicy(raw).grant(source, lambda _: True) == SourcePolicy(patched).grant(source, lambda _: True)
    assert not static_room16_witness(SourcePolicy(raw))
    assert static_room16_witness(SourcePolicy(patched))
    for mode in (0, 1):
        original = policy(mode).policy
        assert timer.configure_policy(original) is original
        assert timer.timer_bytes(original) == bytes(2)
    assert not timer.graph().placements
    assert not any(r.opens for r in timer.graph().routes)


@pytest.mark.parametrize('mode,value', [(0, 600), (1, 600), (2, True), (2, 599), (2, '600')])
def test_invalid_patch_contract_never_grants_route(mode, value):
    raw = {**policy(mode).policy, timer.POLICY_KEY: value}
    assert not timer.enabled(SourcePolicy(raw))
    with pytest.raises(ValueError, match='contract'):
        timer.timer_bytes(raw)


@pytest.mark.parametrize('mode', [0, 1, 2])
def test_exact_rom_timer_token_and_base_guard(mode):
    world = _make_world(mode)
    world._enemy_copy_ability_policy = timer.configure_policy(world._enemy_copy_ability_policy)
    patch = _DummyPatch()
    write_tokens(world, patch)
    values = [payload for _, address, payload in patch.token_writes if address == timer.ROM_OFFSET]
    assert values == [(600 if mode == 2 else 0).to_bytes(2, 'little')]
    rom = bytearray(timer.ROM_OFFSET + 2)
    assert KirbyAmPatchExtension.validate_room16_timer_base(None, bytes(rom)) == bytes(rom)
    rom[-1] = 1
    with pytest.raises(ValueError, match='native switch timer'):
        KirbyAmPatchExtension.validate_room16_timer_base(None, bytes(rom))


@pytest.mark.parametrize('rooms', [0, 1])
def test_tracker_restores_patch_without_inventing_it_for_old_slots(rooms):
    world = make_world(2, True, room_sanity=rooms, goal='full_completion')
    world.create_items()
    slot = world.fill_slot_data()
    rebuilt = reconstruct(slot)
    assert rebuilt.worlds[1]._enemy_copy_ability_policy == world._enemy_copy_ability_policy
    assert rebuilt.get_all_state().can_reach_region('REGION_MUSTARD_MOUNTAIN/ROOM_4_16', 1)
    state = CollectionState(rebuilt)
    assert not has_graph_access(rebuilt.worlds[1], state, timer.graph())
    old = deepcopy(slot)
    del old['enemy_copy_ability_policy'][timer.POLICY_KEY]
    historical = reconstruct(old)
    assert timer.POLICY_KEY not in historical.worlds[1]._enemy_copy_ability_policy
    assert not historical.get_all_state().can_reach_region('REGION_MUSTARD_MOUNTAIN/ROOM_4_16', 1)
