#ifndef KIRBYAM_COPY_ROOM_H
#define KIRBYAM_COPY_ROOM_H
#include <stdint.h>
#define AP_COPY_EXT __attribute__((noinline, long_call, section(".aphub")))
#define AP_COPY_ROOM_ITEM 3860500u
#define AP_COPY_INVALID_SLOT 0xFFFFFFFFu
/* Native WORLD words 22..26; Hub checks remain independent in 27..31. */
#define AP_COPY_TAG 0x43500000u
#define AP_COPY_OWNED 1u
#define AP_GOAL_FLAGS 0x0001FFFEu
AP_COPY_EXT void ap_copy_room_complete_goal(uint32_t bit);
struct ApCopyContext {
    uint32_t epoch, serial, slot, dirty, loaded_slot, task, owned, cookie, retry;
};
#define AP_COPY_CONTEXT ((volatile struct ApCopyContext *)0x0203B13Cu)
AP_COPY_EXT uint32_t ap_copy_room_epoch(void);
AP_COPY_EXT uint32_t ap_copy_room_owned(void);
AP_COPY_EXT void ap_copy_room_poll(void);
AP_COPY_EXT uint32_t *ap_copy_room_state(uint32_t kind, uint32_t index, uint32_t player);
AP_COPY_EXT int16_t ap_copy_room_load(uint32_t kind, uint16_t slot);
AP_COPY_EXT void ap_copy_room_clear(uint32_t kind);
AP_COPY_EXT void ap_copy_room_start(uint8_t humans, uint8_t local, const uint16_t *rooms,
                                   const int32_t *positions, const uint32_t *spawn);
#endif
