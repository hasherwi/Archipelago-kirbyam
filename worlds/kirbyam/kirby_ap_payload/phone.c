#include "phone.h"
#include "phone_runtime_logic.h"
#define U32(a) (*(volatile uint32_t *)(a))
#define U16(a) (*(volatile uint16_t *)(a))
#define U8(a) (*(volatile uint8_t *)(a))
/* Production activation remains zero pending route/CPU acceptance. */
__attribute__((used,section(".apphoneinfo")))
const struct { char marker[8]; uint32_t enabled; } gApPhoneConfig = {"APPHN01", 0u};
AP_COPY_EXT uint32_t ap_phone_owned(void) {
    return ap_copy_room_access_owned(AP_PHONE_OWNED) ? 1u : 0u;
}
AP_COPY_EXT void ap_phone_poll(void) {
    volatile struct ApPhoneContext *ctx = AP_PHONE_CONTEXT;
    volatile uint32_t *request = AP_PHONE_REQUEST;
    uint32_t epoch = AP_PHONE_CONFIG_ENABLED == 1u ? ap_copy_room_epoch() : 0u;
    ctx->epoch = 0u; /* Publish epoch last after the snapshot fields. */
    ctx->slot = epoch ? AP_COPY_CONTEXT->slot : AP_COPY_INVALID_SLOT;
    ctx->owned = epoch ? ap_phone_owned() : 0u;
    ctx->cookie = AP_PHONE_COOKIE;
    if (!epoch) {
        request[0] = 0u; request[2] = 0u; request[3] = 0u;
        return;
    }
    if (request[0]) {
        if (request[0] == epoch && request[1] == 1u) {
            ap_copy_room_grant_access(AP_PHONE_OWNED);
            ctx->owned = ap_phone_owned();
            request[3] = ctx->owned; request[2] = epoch;
        }
        request[0] = 0u;
    }
    ctx->epoch = epoch;
}
AP_COPY_EXT uint32_t ap_phone_call_blocked(uintptr_t kirby) {
    return ap_phone_blocks_initiation(AP_PHONE_CONFIG_ENABLED,
        ap_copy_room_epoch(), ap_phone_owned(), kirby == 0x02020EE0u,
        U16(kirby + 0x60u), U8(0x02021580u), U8(0x0203AD44u));
}
