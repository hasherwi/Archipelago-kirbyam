#ifndef KIRBYAM_VISIT_REWARD_ART_RUNTIME_H
#define KIRBYAM_VISIT_REWARD_ART_RUNTIME_H
#include <stdint.h>
#include "reward_art_config.h"

#define AP_VISIT_ENTRY_COUNT 288u
#define AP_VISIT_NATIVE_BIT 0x8000u
#define AP_VISIT_MAX_VISUAL_WAIT 300u
#define AP_VISIT_CORE_ONLY 0x30525041u /* APR0 */
#define AP_VISIT_ALL_ROOMS 0x31525041u /* APR1 */

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

/* One transition can collect RoomSanity and first-area AP checks.
 * Coalesce identical art only, retaining both visuals if their outcomes differ. */
static inline uint16_t ap_visit_reward_arts(
    const volatile uint16_t *visits, const uint8_t *areas, const uint8_t *room_kinds,
    uint16_t index, uint32_t config, const volatile struct ApRewardArtConfig *art
) {
    if (index >= AP_VISIT_ENTRY_COUNT || (visits[index] & AP_VISIT_NATIVE_BIT) != 0u) return 0u;
    uint16_t arts = 0u;
    uint8_t room_kind = room_kinds[index];
    if (room_kind == 2u || (room_kind == 1u && config == AP_VISIT_ALL_ROOMS)) {
        arts |= 1u << ap_reward_art_from_config(art, AP_REWARD_KEY(AP_REWARD_ROOM, index));
    }
    if (ap_visit_is_first_area(visits, areas, index)) {
        arts |= 1u << ap_reward_art_from_config(art, AP_REWARD_KEY(AP_REWARD_AREA, areas[index]));
    }
    return arts;
}

/* Wait for native transition flags, not for a guessed fade delay. */
static inline uint8_t ap_visit_scene_ready(
    uint32_t player_flags, uint32_t main_flags, uint16_t blend_mode, uint16_t blend_brightness
) {
    return (player_flags & 0xF00u) == 0u && (main_flags & 0xC00u) == 0u
        && ((blend_mode & 0x00C0u) == 0u || blend_brightness == 0u);
}
#endif
