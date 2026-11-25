#ifndef KIRBYAM_COPY_ROOM_H
#define KIRBYAM_COPY_ROOM_H
#include <stdint.h>
#define AP_COPY_EXT __attribute__((noinline, long_call, section(".aphub")))
#define AP_COPY_ROOM_ITEM 3860500u
#define AP_COPY_INVALID_SLOT 0xFFFFFFFFu
/* Native WORLD words 22..26; Hub checks remain independent in 27..31. */
/* Layout 3 separates Copy/Phone bits 0..1 from Goal Game bits 2..17.
 * The distinct tag rejects ambiguous pre-Phone Goal Game records. */
#define AP_COPY_TAG 0x43540000u
#define AP_COPY_OWNED 1u
#define AP_GOAL_FLAGS 0x0003FFFCu
#define AP_STARTING_MIRROR_ITEM 3860416u
AP_COPY_EXT uint8_t ap_copy_room_receive_starting_mirror(void);
#define AP_STARTING_MIRROR_OWNED (1u << 19)
#define AP_ACCESS_MASK (3u | AP_STARTING_MIRROR_OWNED)
AP_COPY_EXT void ap_copy_room_complete_goal(uint32_t bit);
struct ApCopyContext {
    uint32_t epoch, serial, slot, dirty, loaded_slot, task, owned, cookie, retry;
};
/* Following the four receipt visual words at 0x0203B1E0..1EF. */
#define AP_PROGRESS_RESTORE_ADDRESS 0x0203B1F0u
_Static_assert(AP_PROGRESS_RESTORE_ADDRESS + 8u <= 0x0203B200u,
               "Progress restoration overlaps the end of the AP mailbox reservation");
#define AP_COPY_CONTEXT ((volatile struct ApCopyContext *)0x0203B13Cu)
AP_COPY_EXT uint32_t ap_copy_room_epoch(void);
AP_COPY_EXT uint32_t ap_copy_room_owned(void);
AP_COPY_EXT uint32_t ap_copy_room_access_owned(uint32_t mask);
AP_COPY_EXT void ap_copy_room_grant_access(uint32_t mask);
AP_COPY_EXT void ap_copy_room_poll(void);
AP_COPY_EXT uint32_t *ap_copy_room_state(uint32_t kind, uint32_t index, uint32_t player);
AP_COPY_EXT int16_t ap_copy_room_load(uint32_t kind, uint16_t slot);
AP_COPY_EXT void ap_copy_room_clear(uint32_t kind);
AP_COPY_EXT void ap_copy_room_start(uint8_t humans, uint8_t local, const uint16_t *rooms,
                                   const int32_t *positions, const uint32_t *spawn);
AP_COPY_EXT uint32_t ap_progress_owned(void);
AP_COPY_EXT uint8_t ap_progress_receive(uint32_t bit);
void __attribute__((long_call)) ap_project_hub_doors(uint32_t owned);
#endif
