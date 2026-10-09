"""Health ownership is reconstructed only from full authenticated AP history."""
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
import pytest
from ..client import KirbyAmClient

RANGES = [(low, high) for low in range(1, 11) for high in range(low, min(10, low+4)+1)]


@pytest.mark.asyncio
@pytest.mark.parametrize('minimum,maximum', RANGES)
@pytest.mark.parametrize('hp', [0, 2])
async def test_history_repairs_inflated_save_without_replay_heal(mock_bizhawk_context, minimum, maximum, hp):
    client=KirbyAmClient(); client.initialize_client()
    ctx=mock_bizhawk_context
    ctx.slot_data.update(minimum_health=minimum, maximum_health=maximum)
    ctx.items_received=[SimpleNamespace(item=3860018), SimpleNamespace(item=3860018)]
    client.on_package(ctx, 'ReceivedItems', {'index':0})
    addresses=[client._transport_addr('delivered_vitality_item_bits'),client._native_addr('kirby_vitality_counter_native'),
               client._native_addr('kirby_hp_native'),client._native_addr('kirby_max_hp_native')]
    memory=dict(zip(addresses,[bytes(4),(4).to_bytes(2,'little'),bytes([hp]),bytes([10])]))
    async def read(_ctx, reads): return [memory[a] for a,_,_ in reads]
    async def write(_ctx, writes, guards):
        assert all(memory[a]==v for a,v,_ in guards)
        for a,v,_ in writes:memory[a]=v
        return True
    with patch('worlds.kirbyam.client.bizhawk.read', side_effect=read), patch('worlds.kirbyam.client.bizhawk.guarded_write', side_effect=write) as writes:
        await client._reconcile_vitality_ownership(ctx)
        after=dict(memory)
        await client._reconcile_vitality_ownership(ctx)
    assert writes.await_count==1
    assert memory==after
    count=min(1,maximum-minimum)
    assert int.from_bytes(memory[addresses[1]],'little')==count
    assert memory[addresses[0]]==b'\x01\x00\x00\x00'
    assert memory[addresses[3]]==bytes([minimum+count])
    assert memory[addresses[2]]==bytes([min(hp, minimum+count)])


@pytest.mark.asyncio
async def test_history_waits_for_complete_packet_and_reauth(mock_bizhawk_context):
    client=KirbyAmClient();client.initialize_client()
    ctx=mock_bizhawk_context
    with patch('worlds.kirbyam.client.bizhawk.read',new_callable=AsyncMock) as read:
        await client._reconcile_vitality_ownership(ctx)
        client.on_package(ctx,'ReceivedItems',{'index':2})
        await client._reconcile_vitality_ownership(ctx)
        client.on_package(ctx,'ReceivedItems',{'index':0})
        client.on_package(ctx,'Connected',{})
        await client._reconcile_vitality_ownership(ctx)
        read.assert_not_awaited()


def test_actual_payload_replay_preserves_saved_counts_and_dead_state(tmp_path):
    import re, shutil, subprocess, sys
    from pathlib import Path
    compiler=shutil.which('cc')
    if not compiler or not sys.platform.startswith('linux'):
        pytest.skip('requires Linux low-address memory and a C compiler')
    world=Path(__file__).resolve().parents[1]
    payload=(world/'kirby_ap_payload/ap_payload.c').read_text()
    functions=[]
    for name in ['ap_sync_active_kirby_health_from_vitality','ap_grant_vitality_counter','ap_apply_item']:
        match=re.search(r'[^\n]*\b'+name+r'\([^)]*\)\s*\{',payload);assert match
        end,depth=match.end(),1
        while depth:
            depth+=(payload[end]=='{')-(payload[end]=='}');end+=1
        functions.append(payload[match.start():end])
    source='''
#define _GNU_SOURCE
#include <stdint.h>
#include <sys/mman.h>
#include "minor_chest_runtime_logic.h"
#define KIRBY_ITEM_ID_BASE_OFFSET 3860000u
#define KIRBY_MAX_VITALITY_COUNTERS 4u
#define KIRBY_CURRENT_PLAYER 0u
#define KIRBY_STRUCTS_ADDR 0x02020EE0u
#define KIRBY_STRUCT_STRIDE 0x1A8u
#define KIRBY_STRUCT_HP_OFFSET 0x100u
#define KIRBY_STRUCT_MAX_HP_OFFSET 0x101u
#define HP (*(int8_t*)0x02020FE0u)
#define MAX_HP (*(int8_t*)0x02020FE1u)
#define CHECK(x) do {if(!(x)) return __LINE__;} while(0)
static uint32_t AP_DELIVERED_VITALITY_ITEM_BITS,AP_DELIVERED_SHARD_BITFIELD,AP_SHARD_BITFIELD,AP_ABILITY_UNLOCK_MASK,KIRBY_SPRAY_PAINT_FLAGS,KIRBY_MUSIC_PLAYER_AND_SHEETS_FLAGS;
static uint16_t KIRBY_VITALITY_COUNTER;
static uint8_t KIRBY_SHARD_FLAGS;
'''
    for name in ['ap_grant_lives','persist_shard_to_sram','ap_unlock_area_map','KIRBY_COLLECT_SOUND_PLAYER_FN','ap_collect_small_chest_native']:
        source+=f'static void {name}(uint32_t x) {{(void)x;}}\n'
    for name in ['ap_grant_small_food','ap_grant_battery','ap_grant_max_tomato','ap_grant_invincibility_candy','ap_grant_energy_drink','ap_grant_hunk_of_meat','ap_trap_health_down','ap_trap_life_down','ap_trap_bomb','ap_trap_battery_drain','ap_trap_lives_wipeout']:
        source+=f'static void {name}(void) {{}}\n'
    source+='\n'.join(functions)+'''
int main(void) {
    CHECK(mmap((void*)0x02020000,0x2000,PROT_READ|PROT_WRITE,
        MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED,-1,0)==(void*)0x02020000);
    for(unsigned saved=0;saved<=4;saved++) for(unsigned first=0;first<4;first++) {
        KIRBY_VITALITY_COUNTER=saved;AP_DELIVERED_VITALITY_ITEM_BITS=0;
        HP=2;MAX_HP=6+saved;
        for(unsigned i=0;i<4;i++) {
            unsigned id=3860018u+((first+i)%4);
            CHECK(ap_apply_item(id));
            unsigned expected=saved>i+1?saved:i+1;
            CHECK(KIRBY_VITALITY_COUNTER==expected);
            int before=HP;CHECK(ap_apply_item(id));
            CHECK(KIRBY_VITALITY_COUNTER==expected && HP==before);
        }
        CHECK(KIRBY_VITALITY_COUNTER==4);
        AP_DELIVERED_VITALITY_ITEM_BITS=0;HP=2;
        CHECK(ap_apply_item(3860018u));
        CHECK(KIRBY_VITALITY_COUNTER==4 && HP==2);
    }
    KIRBY_VITALITY_COUNTER=0;AP_DELIVERED_VITALITY_ITEM_BITS=0;HP=0;MAX_HP=6;
    CHECK(ap_apply_item(3860018u));
    CHECK(KIRBY_VITALITY_COUNTER==1 && HP==0 && MAX_HP==7);
    return 0;
}
'''
    path,exe=tmp_path/'replay.c',tmp_path/'replay'
    path.write_text(source)
    result=subprocess.run([compiler,'-Wno-int-to-pointer-cast','-I'+str(world/'kirby_ap_payload'),str(path),'-o',str(exe)],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    result=subprocess.run([str(exe)],capture_output=True,text=True)
    assert result.returncode==0,f'payload replay failed at C line {result.returncode}'


@pytest.mark.asyncio
@pytest.mark.parametrize('guard_succeeds', [False, True])
async def test_new_vitality_heals_once_with_atomic_death_guard(mock_bizhawk_context, guard_succeeds):
    client=KirbyAmClient();client.initialize_client()
    ctx=mock_bizhawk_context
    ctx.items_received=[SimpleNamespace(item=3860018),SimpleNamespace(item=3860019)]
    client.on_package(ctx,'ReceivedItems',{'index':0})
    before=[(1).to_bytes(4,'little'),(1).to_bytes(2,'little'),bytes([2]),bytes([7])]
    with patch('worlds.kirbyam.client.bizhawk.read',new_callable=AsyncMock,return_value=before), \
         patch('worlds.kirbyam.client.bizhawk.guarded_write',new_callable=AsyncMock,return_value=guard_succeeds) as write:
        await client._reconcile_vitality_ownership(ctx)
    writes={a:v for a,v,_ in write.call_args.args[1]}
    assert writes[client._native_addr('kirby_hp_native')]==bytes([8])
    guards={a:v for a,v,_ in write.call_args.args[2]}
    assert guards[client._native_addr('kirby_hp_native')]==bytes([2])
    assert guards[client._transport_addr('delivered_vitality_item_bits')]==(1).to_bytes(4,'little')
    # A rejected guard is left for a new snapshot, never an unguarded retry.
    assert write.await_count==1
