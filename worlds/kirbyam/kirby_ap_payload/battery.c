#include "battery.h"
#define LOCAL_KIRBY 0x02020EE0u
#define LOCAL_BYTE (LOCAL_KIRBY+0xDCu)
#define BATCTX AP_BATTERY_CONTEXT
_Static_assert(sizeof(struct ApBatteryContext)==20u, "battery RAM contract");
_Static_assert(0x0203B180u+16u==0x0203B190u, "Phone request boundary");
_Static_assert(0x0203B190u+sizeof(struct ApBatteryContext)<=0x02040000u, "EWRAM boundary");
AP_COPY_EXT void ap_battery_deactivate(void) { BATCTX->active=0u; BATCTX->epoch=0u; }
/* Called only by the actual Adventure start wrapper after native creation and
 * authenticated task/epoch publication. Reconnect and ownership never call it. */
AP_COPY_EXT void ap_battery_start(void) {
    ap_battery_deactivate();
    if (AP_PHONE_CONFIG_ENABLED!=1u || !ap_copy_room_epoch()) return;
    BATCTX->cookie=AP_BATTERY_COOKIE; BATCTX->task=AP_COPY_CONTEXT->task;
    BATCTX->epoch=AP_COPY_CONTEXT->epoch; BATCTX->count=3u;
    *(volatile uint8_t *)LOCAL_BYTE=3u; BATCTX->active=1u;
}
static AP_COPY_EXT uint32_t active(uintptr_t address) {
    uint32_t epoch;
    if (address!=LOCAL_BYTE || AP_PHONE_CONFIG_ENABLED!=1u) return 0u;
    epoch=ap_copy_room_epoch();
    if (!epoch || BATCTX->cookie!=AP_BATTERY_COOKIE || BATCTX->active!=1u
        || BATCTX->epoch!=epoch || BATCTX->task!=AP_COPY_CONTEXT->task) {
        ap_battery_deactivate(); return 0u;
    }
    return 1u;
}
AP_COPY_EXT uint32_t ap_battery_native(uintptr_t address, uint32_t operation) {
    uint32_t count, result;
    uint32_t wide=active(address);
    count=wide ? BATCTX->count : *(volatile uint8_t *)address;
    if (!ap_battery_change(count, operation, &result)) return count;
    if (wide) BATCTX->count=result;
    *(volatile uint8_t *)address=(uint8_t)ap_battery_proxy(result);
    return ap_battery_proxy(result);
}
AP_COPY_EXT uint32_t ap_battery_grant(uintptr_t kirby) {
    uint32_t result;
    uintptr_t address=kirby+0xDCu;
    if (AP_PHONE_CONFIG_ENABLED!=1u) {
        ap_battery_native(address, AP_BATTERY_PICKUP); return 1u;
    }
    if (!active(address) || !ap_battery_change(BATCTX->count, AP_BATTERY_GRANT, &result)) return 0u;
    BATCTX->count=result; *(volatile uint8_t *)address=(uint8_t)ap_battery_proxy(result);
    return 1u;
}
AP_COPY_EXT uint32_t ap_battery_visible(uintptr_t address) {
    if (active(address) && !ap_phone_owned()) return 0u;
    return *(volatile uint8_t *)address;
}
