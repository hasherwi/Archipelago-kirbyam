#include "copy_room.h"
#define WORD18 (*(volatile uint32_t *)0x02028C58u)
#define REQUEST ((volatile uint32_t *)0x0203B160u)
#define KIRBY 0x02020EE0u
__attribute__((used,section(".apcopyinfo")))
const char ap_copy_room_marker[8] = "APCPY01";

AP_SHARED_EXT uint32_t ap_copy_room_owned(void) {
    if (!ap_shared_epoch()) return 0u;
    return (AP_SHARED_CONTEXT->bits & (AP_SHARED_ACCESS_VALID | AP_SHARED_ACCESS_OWNED))
        == (AP_SHARED_ACCESS_VALID | AP_SHARED_ACCESS_OWNED);
}
AP_SHARED_EXT void ap_copy_room_poll(void) {
    uint32_t epoch=ap_shared_epoch(), request=REQUEST[0], owned, was_open;
    if (request) {
        if (epoch && request==epoch && REQUEST[1]<=1u) {
            owned=REQUEST[1];
            if (ap_shared_update(AP_SHARED_ACCESS_OWNED,
                    AP_SHARED_ACCESS_VALID | (owned ? AP_SHARED_ACCESS_OWNED : 0u))) {
                REQUEST[3]=owned;
                REQUEST[2]=epoch;
            }
        }
        REQUEST[0]=0u;
    }
    /* Never touch the WORLD buffer during menu summaries or teardown. */
    if (!epoch) return;
    was_open=WORD18;
    WORD18=ap_copy_room_owned();
    /* Native mirror collision is a one-time mutation. If authoritative history
     * revokes live access, reload Central Circle via its ordinary transition,
     * rebuilding the closed mirror rather than leaving misleading open tiles.
     * The transition guard rejects entry immediately, including during reload. */
    if (was_open && !WORD18 && *(volatile uint16_t *)(KIRBY+0x60u)==801u) {
        ((uint8_t (*)(void*,uint16_t,uint8_t,uint8_t))0x080551FDu)(
            (void*)KIRBY,801u,5u,4u);
    }
}
/* Called by SpecialHubMirrorInit before its first collision mutation. Only the
 * WORLD-18 mirror is replaced; every other native lookup remains unchanged. */
AP_SHARED_EXT uint32_t *ap_copy_room_state(uint32_t kind, uint32_t index, uint32_t player) {
    if (kind==2u && index==18u) {
        WORD18=ap_copy_room_owned();
        return (uint32_t *)0x02028C58u;
    }
    return ((uint32_t *(*)(uint32_t,uint32_t,uint32_t))0x08002889u)(kind,index,player);
}
