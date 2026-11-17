#ifndef KIRBYAM_BATTERY_H
#define KIRBYAM_BATTERY_H
#include "phone.h"
#include "battery_runtime_logic.h"
struct ApBatteryContext { uint32_t cookie, task, epoch, count, active; };
#define AP_BATTERY_CONTEXT ((volatile struct ApBatteryContext *)0x0203B190u)
#define AP_BATTERY_COOKIE 0x42415431u
AP_COPY_EXT void ap_battery_start(void);
AP_COPY_EXT void ap_battery_deactivate(void);
AP_COPY_EXT uint32_t ap_battery_native(uintptr_t byte_address, uint32_t operation);
AP_COPY_EXT uint32_t ap_battery_grant(uintptr_t kirby);
AP_COPY_EXT uint32_t ap_battery_visible(uintptr_t byte_address);
#endif
