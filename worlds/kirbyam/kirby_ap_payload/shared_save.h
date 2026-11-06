#ifndef KIRBYAM_SHARED_SAVE_H
#define KIRBYAM_SHARED_SAVE_H
#include "shared_save_logic.h"
#define AP_SHARED_EXT __attribute__((noinline, long_call, section(".aphub")))
/* Foundation reserves mailbox 0x13C..0x15F. Copy Room uses 0x160..0x16F;
 * Goal Games use 0x170..0x18F. Feature ranges are not touched here. */
struct ApSharedContext {
    uint32_t epoch;       /* +13C: zero while inactive; publish last */
    uint32_t serial;      /* +140: monotonic activation counter, not saved */
    uint32_t slot;        /* +144: active native file 0 (File 1) */
    uint32_t dirty;       /* +148: native save still needs successful retry */
    uint32_t loaded_slot;/* +14C: last native WORLD load/clear identity */
    uint32_t task;        /* +150: active local Kirby task identity */
    uint32_t bits;        /* +154: authenticated public feature snapshot */
    uint32_t cookie;      /* +158: private lifecycle initialization */
    uint32_t retry;       /* +15C: bounded retry countdown */
};
#define AP_SHARED_CONTEXT ((volatile struct ApSharedContext *)0x0203B13Cu)
AP_SHARED_EXT void ap_shared_start(uint8_t humans, uint8_t local, const uint16_t *rooms,
                                   const int32_t *positions, const uint32_t *spawn);
AP_SHARED_EXT void ap_shared_poll(void);
AP_SHARED_EXT uint32_t ap_shared_epoch(void);
/* Only the native Collection paint-confirmation hook uses this loaded-file check.
 * It does not activate an Adventure context. */
AP_SHARED_EXT uint8_t ap_shared_can_save_paint(void);
/* Mutations only succeed inside the current authenticated gameplay context. */
AP_SHARED_EXT uint8_t ap_shared_update(uint32_t clear, uint32_t set);
#endif
