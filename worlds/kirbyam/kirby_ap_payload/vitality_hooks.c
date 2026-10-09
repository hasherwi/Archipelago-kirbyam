/* Staged format-2 hook targets. Not linked by the shipping Makefile yet.
 * Callers are AAPCS no-argument BL sites in the verified USA ROM. */
#include "vitality_runtime_logic.h"

#define AP_NATIVE_VITALITY (*(volatile uint16_t *)0x02038980u)

/* Link at 0x0815F690; seed patching replaces bounds before ROM distribution. */
__attribute__((used, section(".apconfig.health")))
volatile const uint32_t gApHealthConfigInitial = AP_HEALTH_CONFIG_MAGIC | 0x0A06u;

/* Replacement for NumVitalitiesCollected BL + the caller's adds r0,#6. */
__attribute__((used)) uint32_t ap_vitality_initial_capacity(void) {
    return ap_vitality_capacity(gApHealthConfigInitial, AP_NATIVE_VITALITY);
}

/* Only the native collection menu gets the four-icon view. */
__attribute__((used)) uint32_t ap_vitality_collection_menu_count(void) {
    return ap_vitality_menu_count(AP_NATIVE_VITALITY);
}
