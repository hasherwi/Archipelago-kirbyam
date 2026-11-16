"""Room Sanity is a check-set extension, not new physical Phone evidence."""
import asyncio
from types import SimpleNamespace as NS

import pytest


@pytest.mark.parametrize('keys', [0, 1])
def test_room_sanity_preserves_exact_production_tokens(keys):
    from test.general import setup_multiworld
    from .. import KirbyAmWorld
    from ..phone_generation import PHONE_CONFIG_FILE
    from ..rom import KirbyAmProcedurePatch, write_tokens
    patches = []
    counts = []
    for room_sanity in (0, 1):
        mw = setup_multiworld(KirbyAmWorld, seed=1086, options={
            'phone_progression':1, 'ability_gating':0, 'area_keys':keys,
            'room_sanity':room_sanity})
        w = mw.worlds[1]
        # Location-count changes may advance generation RNG. The comparison
        # deliberately holds seed identity constant, not historical save bytes.
        w.auth = bytes(range(16))
        patch = KirbyAmProcedurePatch()
        write_tokens(w, patch)
        patches.append(patch)
        counts.append(len(mw.get_locations(1)))
        assert w.fill_slot_data()['room_sanity'] == bool(room_sanity)
    assert counts[1] > counts[0]
    for name in ('token_data.bin', PHONE_CONFIG_FILE, 'enemy_health_multiplier.bin'):
        assert patches[0].get_file(name) == patches[1].get_file(name)


@pytest.mark.parametrize('room_sanity', [False, True])
def test_full_room_sanity_generation_accessibility_and_phone_placement(tmp_path, monkeypatch, room_sanity):
    import Main
    from ..phone_protocol import PHONE_ITEM_ID
    from ..phone_traversal import SOURCE_REGION, MAIN
    from .support.integration_generation import generate_archive_from_fixture
    generated = []
    original = Main.main
    def capture(*args, **kwargs):
        mw = original(*args, **kwargs)
        generated.append(mw)
        return mw
    monkeypatch.setattr(Main, 'main', capture)
    player = tmp_path / 'phone.yaml'
    player.write_text('name: Phone Room Sanity\ngame: Kirby & The Amazing Mirror\n'
        'Kirby & The Amazing Mirror:\n  phone_progression: true\n'
        '  ability_gating: false\n  ability_randomization_mode: 0\n'
        f'  room_sanity: {str(room_sanity).lower()}\n  accessibility: full\n')
    generate_archive_from_fixture(player, tmp_path / 'out', seed=1086)
    mw, = generated
    assert not mw.get_unfilled_locations()
    assert mw.can_beat_game() and mw.fulfills_accessibility()
    phones = [loc for loc in mw.get_filled_locations() if loc.item and loc.item.code == PHONE_ITEM_ID]
    assert len(phones) == 1
    state = mw.get_all_state()
    while state.has('Phone a Friend', 1):
        state.remove(phones[0].item)
    assert phones[0].can_reach(state)
    assert state.can_reach_region(SOURCE_REGION, 1)
    assert state.can_reach_region(MAIN, 1)
    chalk = next(loc for loc in mw.get_locations(1) if loc.address == 3960513)
    assert not chalk.can_reach(state)
    state.collect(phones[0].item)
    assert chalk.can_reach(state)


def test_actual_visit_poll_expands_checks_without_writing_native_state():
    from ..client import KirbyAmClient
    raw = bytearray(512)
    raw[2:4] = (0x8000).to_bytes(2, 'little')
    raw[4:6] = (0x8000).to_bytes(2, 'little')
    async def run(enabled):
        sent = []
        async def read(_ctx):
            return memoryview(raw)
        async def send(messages):
            sent.extend(messages)
        # Invoke the actual method with a closed read/report-only dependency
        # surface. There is deliberately no native write method or connection.
        client = NS(_coerce_bool=KirbyAmClient._coerce_bool,
            _room_sanity_location_ids_by_bit={1:[101],2:[102]},
            _room_sanity_bits_sorted=[1,2], _core_landmark_location_ids={101},
            _core_landmark_location_ids_by_bit={1:[101]},
            _get_room_visit_flags_view=read, _active_location_id_set=lambda ctx: {101,102},
            _last_room_sanity_poll_log=None)
        ctx = NS(slot_data={'room_sanity':enabled,'core_landmark_location_ids':[101]},
                 checked_locations=set(), send_msgs=send)
        await KirbyAmClient._poll_room_sanity_locations(client,ctx)
        return sent
    before = bytes(raw)
    assert asyncio.run(run(False)) == [{'cmd':'LocationChecks','locations':[101]}]
    assert asyncio.run(run(True)) == [{'cmd':'LocationChecks','locations':[101,102]}]
    assert bytes(raw) == before
