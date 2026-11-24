#ifndef KIRBYAM_VISIT_REWARD_ART_RUNTIME_H
#define KIRBYAM_VISIT_REWARD_ART_RUNTIME_H
#include <stdint.h>

#define AP_VISIT_ENTRY_COUNT 288u
#define AP_VISIT_NATIVE_BIT 0x8000u
#define AP_VISIT_MAX_VISUAL_WAIT 300u

static inline uint8_t ap_visit_is_first_area(
    const volatile uint16_t *visits, const uint8_t *areas, uint16_t index
) {
    if (index >= AP_VISIT_ENTRY_COUNT || (visits[index] & AP_VISIT_NATIVE_BIT) != 0u) return 0u;
    uint8_t area = areas[index];
    if (area == 0u) return 0u;
    for (uint32_t i = 0; i < AP_VISIT_ENTRY_COUNT; ++i) {
        if (areas[i] == area && (visits[i] & AP_VISIT_NATIVE_BIT) != 0u) return 0u;
    }
    return 1u;
}

/* Wait for native transition flags, not for a guessed fade delay. */
static inline uint8_t ap_visit_scene_ready(
    uint32_t player_flags, uint32_t main_flags, uint16_t blend_mode, uint16_t blend_brightness
) {
    return (player_flags & 0xF00u) == 0u && (main_flags & 0xC00u) == 0u
        && ((blend_mode & 0x00C0u) == 0u || blend_brightness == 0u);
}
#endif
