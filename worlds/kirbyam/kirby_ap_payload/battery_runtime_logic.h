#ifndef KIRBYAM_BATTERY_RUNTIME_LOGIC_H
#define KIRBYAM_BATTERY_RUNTIME_LOGIC_H
#include <stdint.h>
enum ApBatteryOperation { AP_BATTERY_SET3, AP_BATTERY_SET1, AP_BATTERY_SPEND,
    AP_BATTERY_PICKUP, AP_BATTERY_DRAIN, AP_BATTERY_GRANT };
static inline uint32_t ap_battery_proxy(uint32_t count) {
    return count > 255u ? 255u : count;
}
/* Zero means defer, never successful saturation or wrapping. Native pickup
 * keeps its original three-charge threshold; AP delivery does not. */
static inline uint32_t ap_battery_change(uint32_t count, uint32_t operation,
                                       uint32_t *result) {
    switch (operation) {
    case AP_BATTERY_SET3: *result=3u; break;
    case AP_BATTERY_SET1: *result=count ? count : 1u; break;
    case AP_BATTERY_SPEND: *result=count ? count-1u : 0u; break;
    case AP_BATTERY_PICKUP: *result=count<3u ? count+1u : count; break;
    case AP_BATTERY_DRAIN: *result=0u; break;
    case AP_BATTERY_GRANT:
        if (count==UINT32_MAX) return 0u;
        *result=count+1u; break;
    default: return 0u;
    }
    return 1u;
}
#endif
