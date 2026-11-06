#include "shared_save.h"
#include "goal_game_runtime_logic.h"
#define RUN ((volatile struct ApGoalRun *)0x0203B170u)
#define KIRBY 0x02020EE0u
#define U8(p) (*(volatile uint8_t *)(p))
#define U16(p) (*(volatile uint16_t *)(p))
#define U32(p) (*(volatile uint32_t *)(p))
__attribute__((used, section(".apgoalinfo")))
const uint8_t gApGoalInfo[8] = {'A','P','G','O','A','L','1',0};

AP_SHARED_EXT void ap_goal_poll(void) {
    ap_goal_validate(RUN, ap_shared_epoch(), U16(KIRBY + 0x60u), U8(KIRBY + 0x100u) != 0u);
}

/* Preserve the exact consumed door pointer before native transition clears it.
 * Only the single local human can establish an origin; AI follows are ignored. */
AP_SHARED_EXT void ap_goal_transition(void *kirby) {
    uint32_t k = (uint32_t)kirby;
    uint16_t source = U16(k + 0x60u);
    uint32_t door = U32(k + 0x10Cu);
    uint8_t physical = (U16(k + 0x58u) & 0x4000u) && (U8(k + 0x62u) & 0x10u);
    uint32_t epoch = ap_shared_epoch();
    ((void (*)(void *))0x080562D1u)(kirby);
    if (k != KIRBY) return;
    ap_goal_enter(RUN, epoch == ap_shared_epoch() ? epoch : 0u,
                  physical ? door : 0u, source, U16(k + 0x60u));
}

AP_SHARED_EXT void ap_goal_start_callback(void *star) {
    uint32_t s = (uint32_t)star;
    ap_goal_poll();
    ap_goal_start(RUN, ap_shared_epoch(), U16(KIRBY + 0x60u), s,
                  (U8(s + 0xB5u) & 1u) && U16(s + 0x60u) == U16(KIRBY + 0x60u));
    ((void (*)(void *))0x0800DCADu)(star);
}

AP_SHARED_EXT void ap_goal_landed_callback(void *star) {
    uint32_t s = (uint32_t)star;
    uint32_t bit;
    ap_goal_poll();
    ((void (*)(void *))0x0800D2E1u)(star);
    /* Native completion has finished the landing delay and launched the return
     * sequence. Zero prizes use this same event; no score threshold exists. */
    bit = ap_goal_complete(RUN, ap_shared_epoch(), U16(KIRBY + 0x60u), s,
            (U8(s + 0xB5u) & 1u) && U16(s + 0x60u) == U16(KIRBY + 0x60u),
            U32(s + 0x78u) == 0x0800DE21u);
    if (bit < 16u) ap_shared_update(0u, 1u << bit);
}
