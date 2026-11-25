#include "copy_room.h"
#include "battery.h"
#define U32(a) (*(volatile uint32_t *)(a))
#define U16(a) (*(volatile uint16_t *)(a))
#define U8(a) (*(volatile uint8_t *)(a))
#define RECORD ((volatile uint32_t *)0x02028C68u)
#define AUTH ((const volatile uint32_t *)0x08F00000u)
#define CTX AP_COPY_CONTEXT
#define COOKIE 0x43504332u
#define SAVE_SLOT U16(0x0203AD48u)
#define FLAGS U32(0x0203AD10u)
#define LOCAL U8(0x0203AD3Cu)
#define HUMANS U8(0x0203AD30u)
#define KIRBY 0x02020EE0u
#define WORD18 U32(0x02028C58u)
/* WORLD word 21 shares the full seed token in words 22..25. Do not
 * alias native words 1..15, Copy Room word 18, or goal/switch records. */
#define PROGRESS U32(0x02028C64u)
#define PROGRESS_TAG 0xA8000000u
#define PROGRESS_SLOT_SHIFT 24u
#define PROGRESS_BITS 0x007FFFFFu
#define INCOMING_FLAG U32(0x0203B004u)
#define INCOMING_ITEM U32(0x0203B008u)
#define REQUEST ((volatile uint32_t *)0x0203B160u)
#define PROGRESS_RESTORE ((volatile uint32_t *)AP_PROGRESS_RESTORE_ADDRESS)
#define NATIVE_SAVE ((int16_t (*)(uint32_t,uint16_t))0x0800ACD5u)

__attribute__((used,section(".apcopyinfo")))
const char ap_copy_room_marker[8] = "APCPY04";

static AP_COPY_EXT uint8_t record_valid(void) {
    if ((RECORD[4] & ~(AP_ACCESS_MASK | AP_GOAL_FLAGS)) != AP_COPY_TAG) return 0u;
    for (uint32_t i=0u; i<4u; ++i) if (RECORD[i] != AUTH[i]) return 0u;
    return 1u;
}
static AP_COPY_EXT void deactivate(void) {
    ap_battery_deactivate();
    CTX->epoch=0u; CTX->owned=0u; CTX->slot=AP_COPY_INVALID_SLOT;
    CTX->task=0u; CTX->dirty=0u; CTX->retry=0u;
    REQUEST[0]=0u; REQUEST[2]=0u; REQUEST[3]=0u;
    PROGRESS_RESTORE[1]=0u;
}
static AP_COPY_EXT void initialize(void) {
    if (CTX->cookie == COOKIE) return;
    deactivate(); CTX->serial=0u; CTX->loaded_slot=AP_COPY_INVALID_SLOT;
    CTX->cookie=COOKIE;
}
/* Previews contain normal AI state and stale Kirby memory. Require the actual
 * native player task plus a WORLD load followed by Adventure startup. */
static AP_COPY_EXT uint8_t live_task(uint32_t task) {
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
AP_COPY_EXT uint32_t ap_copy_room_epoch(void) {
    initialize();
    if (CTX->epoch && (SAVE_SLOT>2u || SAVE_SLOT!=CTX->slot
        || CTX->loaded_slot!=CTX->slot || (FLAGS&0x76u)
        || LOCAL!=0u || HUMANS!=1u || U32(KIRBY+0xCCu)!=CTX->task
        || !live_task(CTX->task) || !record_valid())) deactivate();
    return CTX->epoch;
}
/* 0..7 are Area Keys 2..9, 8..22 are Hub Connections 1..15. */
static AP_COPY_EXT uint32_t progress_for_slot(uint16_t slot) {
    if (slot > 2u || !record_valid()
        || (PROGRESS & ~PROGRESS_BITS) != (PROGRESS_TAG | ((uint32_t)slot << PROGRESS_SLOT_SHIFT)))
        return 0u;
    return PROGRESS & PROGRESS_BITS;
}

AP_COPY_EXT uint32_t ap_progress_owned(void) {
    return ap_copy_room_epoch() ? progress_for_slot((uint16_t)CTX->slot) : 0u;
}

static AP_COPY_EXT uint8_t progress_apply(uint32_t acquired) {
    uint32_t old = PROGRESS;
    uint32_t owned = progress_for_slot((uint16_t)CTX->slot);
    if ((owned & acquired) == acquired) return 1u;
    PROGRESS = PROGRESS_TAG | (CTX->slot << PROGRESS_SLOT_SHIFT) | owned | acquired;
    /* Only ACK a successful write of this active Adventure file. A failed
     * write does not become ownership in EWRAM; the same offer may retry. */
    if (NATIVE_SAVE(1u,(uint16_t)CTX->slot) != 0) {
        PROGRESS = old;
        return 0u;
    }
    CTX->dirty=0u; /* This native serialization also flushed the shared header. */
    return 1u;
}

AP_COPY_EXT uint8_t ap_progress_receive(uint32_t bit) {
    return ap_copy_room_epoch() && bit < 23u && progress_apply(1u << bit);
}

AP_COPY_EXT uint32_t ap_copy_room_owned(void) {
    return ap_copy_room_epoch() ? (RECORD[4] & AP_COPY_OWNED) : 0u;
}
AP_COPY_EXT uint32_t ap_copy_room_access_owned(uint32_t mask) {
    return ap_copy_room_epoch() ? (RECORD[4] & mask & AP_ACCESS_MASK) : 0u;
}
AP_COPY_EXT void ap_copy_room_grant_access(uint32_t mask) {
    if (!ap_copy_room_epoch() || !mask || (mask & ~AP_ACCESS_MASK)) return;
    if ((RECORD[4] & mask) != mask) {
        RECORD[4] |= mask; CTX->dirty=1u; CTX->retry=0u;
    }
    CTX->owned=RECORD[4]&AP_COPY_OWNED;
}
static AP_COPY_EXT void abandon_progress_offer(void) {
    uint32_t item = INCOMING_ITEM;
    if (INCOMING_FLAG == 1u && ((item >= 3860041u && item <= 3860048u)
        || (item >= 3860401u && item <= 3860415u))) {
        /* Reset the offer without incrementing the native receipt counter.
         * The client's receipt journal treats this as unacknowledged. */
        INCOMING_FLAG = 0u;
    }
}

AP_COPY_EXT int16_t ap_copy_room_load(uint32_t kind, uint16_t slot) {
    int16_t result;
    initialize();
    if (kind==1u) { abandon_progress_offer(); deactivate(); CTX->loaded_slot=AP_COPY_INVALID_SLOT; }
    result=((int16_t (*)(uint32_t,uint16_t))0x0800A91Du)(kind,slot);
    if (kind==1u && result==0 && slot<=2u) {
        CTX->loaded_slot=slot;
        ap_project_hub_doors(progress_for_slot(slot));
    }
    return result;
}
AP_COPY_EXT void ap_copy_room_clear(uint32_t kind) {
    initialize();
    if (kind==1u) { abandon_progress_offer(); deactivate(); CTX->loaded_slot=AP_COPY_INVALID_SLOT; }
    ((void (*)(uint32_t))0x0800AC01u)(kind);
    if (kind==1u && SAVE_SLOT<=2u) CTX->loaded_slot=SAVE_SLOT;
}
/* Only the two Adventure starts use this wrapper. Native file selection,
 * Collection, Boss Endurance, demo and linked startup remain unchanged. */
AP_COPY_EXT void ap_copy_room_start(uint8_t humans, uint8_t local, const uint16_t *rooms,
                                   const int32_t *positions, const uint32_t *spawn) {
    uint32_t task;
    initialize(); deactivate();
    ((void (*)(uint8_t,uint8_t,const uint16_t*,const int32_t*,const uint32_t*))0x080332BDu)(
        humans,local,rooms,positions,spawn);
    task=U32(KIRBY+0xCCu);
    if (SAVE_SLOT>2u || CTX->loaded_slot!=SAVE_SLOT || (FLAGS&0x76u)
        || humans!=1u || local!=0u || LOCAL!=0u || HUMANS!=1u || !live_task(task)) return;
    if (!record_valid()) {
        RECORD[4]=0u;
        PROGRESS=0u; /* Old/foreign ownership must not bind to the new token. */
        for (uint32_t i=0u; i<4u; ++i) RECORD[i]=AUTH[i];
        RECORD[4]=AP_COPY_TAG;
        CTX->dirty=1u;
    }
    CTX->slot=SAVE_SLOT; CTX->task=task; CTX->owned=RECORD[4]&AP_COPY_OWNED;
    ++CTX->serial; if (!CTX->serial) CTX->serial=1u;
    CTX->epoch=CTX->serial;
    ap_battery_start();
}
AP_COPY_EXT void ap_copy_room_poll(void) {
    uint32_t epoch=ap_copy_room_epoch(), request=REQUEST[0];
    if (request) {
        if (epoch && request==epoch && REQUEST[1]==1u) {
            /* Receipt is permanent within this authenticated native file.
             * Empty/replayed histories and zero commands cannot revoke it. */
            if (!(RECORD[4]&AP_COPY_OWNED)) {
                RECORD[4]|=AP_COPY_OWNED; CTX->dirty=1u; CTX->retry=0u;
            }
            CTX->owned=AP_COPY_OWNED; REQUEST[3]=AP_COPY_OWNED; REQUEST[2]=epoch;
        }
        REQUEST[0]=0u;
    }
    /* Never modify preview buffers or save outside the active native file. */
    if (!epoch) return;
    WORD18=ap_copy_room_owned();
    /* Restore saved-evidence bits without touching the ordinary receipt mailbox
     * or its physical count. Re-read native ownership on the next client tick. */
    uint32_t restore_epoch=PROGRESS_RESTORE[1];
    if (restore_epoch) {
        uint32_t mask=PROGRESS_RESTORE[0];
        PROGRESS_RESTORE[1]=0u;
        if (restore_epoch==epoch && !INCOMING_FLAG && mask && !(mask & ~PROGRESS_BITS)
            && progress_apply(mask)) ap_project_hub_doors(ap_progress_owned());
    }
    if (CTX->dirty) {
        if (CTX->retry) --CTX->retry;
        else if (NATIVE_SAVE(1u,(uint16_t)CTX->slot)==0) CTX->dirty=0u;
        else CTX->retry=60u;
    }
}
/* SpecialHubMirrorInit calls before changing collision. Other native lookups
 * and Boss Endurance's separate statue room keep their original behavior. */
AP_COPY_EXT uint32_t *ap_copy_room_state(uint32_t kind, uint32_t index, uint32_t player) {
    if (kind==2u && index==18u) {
        WORD18=ap_copy_room_owned();
        return (uint32_t *)0x02028C58u;
    }
    return ((uint32_t *(*)(uint32_t,uint32_t,uint32_t))0x08002889u)(kind,index,player);
}

/* Goal flags share authentication and native-file lifecycle with ownership. */
AP_COPY_EXT void ap_copy_room_complete_goal(uint32_t bit) {
    uint32_t flag;
    if (bit >= 16u || !ap_copy_room_epoch()) return;
    flag = 1u << (bit + 2u);
    if (!(RECORD[4] & flag)) {
        RECORD[4] |= flag;
        CTX->dirty = 1u;
        CTX->retry = 0u;
    }
}
