#ifndef KIRBYAM_PHONE_H
#define KIRBYAM_PHONE_H
#include "copy_room.h"
#define AP_PHONE_ITEM 3860501u
#define AP_PHONE_OWNED 2u
#define AP_PHONE_COOKIE 0x50484E31u
#define AP_PHONE_CONFIG_ENABLED (*(const volatile uint32_t *)0x0900FFD0u)
struct ApPhoneContext { uint32_t epoch, slot, owned, cookie; };
#define AP_PHONE_CONTEXT ((volatile struct ApPhoneContext *)0x0203B170u)
#define AP_PHONE_REQUEST ((volatile uint32_t *)0x0203B180u)
AP_COPY_EXT uint32_t ap_phone_owned(void);
AP_COPY_EXT void ap_phone_poll(void);
AP_COPY_EXT uint32_t ap_phone_call_blocked(uintptr_t kirby);
#endif
