#include "shared_save.h"
#define U32(a) (*(volatile uint32_t *)(a))
#define U16(a) (*(volatile uint16_t *)(a))
#define U8(a) (*(volatile uint8_t *)(a))
#define RECORD ((volatile uint32_t *)0x02028C68u)
#define AUTH ((const volatile uint32_t *)0x08F00000u)
#define CTX AP_SHARED_CONTEXT
#define COOKIE 0x41505331u
#define SAVE_SLOT U16(0x0203AD48u)
#define FLAGS U32(0x0203AD10u)
#define LOCAL U8(0x0203AD3Cu)
#define HUMANS U8(0x0203AD30u)
#define KIRBY 0x02020EE0u
#define NATIVE_SAVE ((int16_t (*)(uint32_t,uint16_t))0x0800ACD5u)

__attribute__((used,section(".apsharedinfo")))
const char ap_shared_save_marker[8] = "APSHR02";

static AP_SHARED_EXT void deactivate(void) {
    CTX->epoch = 0u;
    CTX->bits = 0u;
    CTX->slot = AP_SHARED_INVALID_SLOT;
    CTX->task = 0u;
    CTX->dirty = 0u;
    CTX->retry = 0u;
}
static AP_SHARED_EXT void initialize(void) {
    if (CTX->cookie == COOKIE) return;
    deactivate();
    CTX->serial = 0u;
    CTX->loaded_slot = AP_SHARED_INVALID_SLOT;
    CTX->cookie = COOKIE;
}
/* Require the actual native player task, even when saved AI state says 300.
 * File previews can contain normal AI state and stale Kirby memory. */
static AP_SHARED_EXT uint8_t live_task(uint32_t task) {
    uint32_t payload;
    uint16_t offset, flags;
    if (!task || task < 0x03000000u || task > 0x03007FECu || (task & 3u)
        || U32(task+8u) != 0x0803EE19u || U16(task+0x10u) != 0x3000u
        || !U16(task+2u) || !U16(task+4u)) return 0u;
    flags=U16(task+0x12u); offset=U16(task+6u);
    if ((flags & 1u) || !offset) return 0u;
    if (flags & 0x10u) payload=0x02000000u+((uint32_t)offset<<2);
    else {
        if (offset > 0x7FFFu) return 0u;
        payload=0x03000000u+offset;
    }
    return U8(payload)==0u;
}
static AP_SHARED_EXT uint8_t context_matches(void) {
    return CTX->epoch && SAVE_SLOT == 0u && SAVE_SLOT == CTX->slot
        && CTX->loaded_slot == CTX->slot && !(FLAGS & 0x76u)
        && LOCAL == 0u && HUMANS == 1u
        && U32(KIRBY+0xCCu) == CTX->task && live_task(CTX->task)
        && ap_shared_record_valid(RECORD, AUTH);
}
AP_SHARED_EXT uint32_t ap_shared_epoch(void) {
    initialize();
    if (CTX->epoch && !context_matches()) deactivate();
    return CTX->epoch;
}
AP_SHARED_EXT uint8_t ap_shared_update(uint32_t clear, uint32_t set) {
    if (!ap_shared_epoch()) return 0u;
    if (ap_shared_record_update(RECORD, AUTH, clear, set)) {
        CTX->bits=ap_shared_record_bits(RECORD, AUTH);
        CTX->dirty=1u;
        CTX->retry=0u;
    }
    return 1u;
}
AP_SHARED_EXT void ap_shared_poll(void) {
    if (!ap_shared_epoch()) return;
    CTX->bits=ap_shared_record_bits(RECORD, AUTH);
    if (!CTX->dirty) return;
    if (CTX->retry) { --CTX->retry; return; }
    /* Native routine writes both checksummed copies. Retry only this slot,
     * never fall back to file 0. No direct SRAM/checksum manipulation. */
    if (NATIVE_SAVE(1u,(uint16_t)CTX->slot)==0) CTX->dirty=0u;
    else CTX->retry=60u;
}
AP_SHARED_EXT int16_t ap_shared_load(uint32_t kind, uint16_t slot) {
    int16_t result;
    initialize();
    if (kind==1u) { deactivate(); CTX->loaded_slot=AP_SHARED_INVALID_SLOT; }
    result=((int16_t (*)(uint32_t,uint16_t))0x0800A91Du)(kind,slot);
    if (kind==1u && result==0 && slot==0u) CTX->loaded_slot=slot;
    return result;
}
AP_SHARED_EXT void ap_shared_clear(uint32_t kind) {
    initialize();
    if (kind==1u) { deactivate(); CTX->loaded_slot=AP_SHARED_INVALID_SLOT; }
    ((void (*)(uint32_t))0x0800AC01u)(kind);
    if (kind==1u && SAVE_SLOT==0u) CTX->loaded_slot=SAVE_SLOT;
}
/* Patch only the two adventure startup calls; Boss Endurance, demo and linked
 * startup keep their original calls. The native load happened before this. */
AP_SHARED_EXT void ap_shared_start(uint8_t humans, uint8_t local, const uint16_t *rooms,
                                   const int32_t *positions, const uint32_t *spawn) {
    uint32_t task;
    initialize();
    deactivate();
    ((void (*)(uint8_t,uint8_t,const uint16_t*,const int32_t*,const uint32_t*))0x080332BDu)(
        humans,local,rooms,positions,spawn);
    task=U32(KIRBY+0xCCu);
    if (SAVE_SLOT!=0u || CTX->loaded_slot!=SAVE_SLOT || (FLAGS&0x76u)
        || humans!=1u || local!=0u || LOCAL!=0u || HUMANS!=1u || !live_task(task)) return;
    CTX->dirty=ap_shared_record_init(RECORD,AUTH);
    if (CTX->dirty) {
        volatile uint32_t *extra=(volatile uint32_t *)0x0203B200u;
        for (uint32_t i=0; i<1024u; ++i) extra[i]=0u;
    }
    CTX->slot=SAVE_SLOT;
    CTX->task=task;
    CTX->bits=ap_shared_record_bits(RECORD,AUTH);
    CTX->serial=ap_shared_next_epoch(CTX->serial);
    CTX->epoch=CTX->serial;
}

/* The title task is already destroyed at this call site. Never enter the
 * selector or its three-file preview loader. Continue uses the original
 * adventure startup call, including the color and shared-context wrappers. */
AP_SHARED_EXT void ap_single_save_enter(void) {
    initialize();
    deactivate();
    ((void (*)(void))0x08150251u)(); /* native m4aMPlayAllStop */
    U16(0x030024E8u)=0u; U16(0x030024EAu)=0u; U16(0x030024ECu)=0u;
    SAVE_SLOT=0u;
    U8(0x0203ADE0u)=0xFFu;
    if (ap_shared_load(1u,0u)!=0) ap_shared_clear(1u);
    ((void (*)(void))0x08123FD5u)();
}

/* Native descriptors drive clearing, checksums, reads, writes and duplicate
 * offsets. Preserve all original fields, then append 4096 bytes of AP data. */
__attribute__((used,section(".apsavedesc")))
const uint32_t ap_single_save_descriptors[18] = {
    0x02028BF0u,32u, 0x02028C10u,128u, 0x02028CA0u,574u,
    0x02038960u,36u, 0x020229D0u,4u, 0x020229D8u,4u,
    0x0203AD2Cu,2u, 0x0203B200u,4096u, 0xFFFFFFFFu,0xFFFFFFFFu
};
