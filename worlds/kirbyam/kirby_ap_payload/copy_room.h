#ifndef KIRBYAM_COPY_ROOM_H
#define KIRBYAM_COPY_ROOM_H
#include "shared_save.h"
#define AP_COPY_ROOM_ITEM 3860500u
AP_SHARED_EXT uint32_t ap_copy_room_owned(void);
AP_SHARED_EXT void ap_copy_room_poll(void);
AP_SHARED_EXT uint32_t *ap_copy_room_state(uint32_t kind, uint32_t index, uint32_t player);
#endif
