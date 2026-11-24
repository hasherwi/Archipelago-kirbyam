#ifndef KIRBYAM_REWARD_ART_CONFIG_H
#define KIRBYAM_REWARD_ART_CONFIG_H
#include <stdint.h>

#define AP_REWARD_ART_MAGIC 0x32565241u /* ARV2 */
#define AP_REWARD_ART_CAPACITY 510u
#define AP_REWARD_GEM 0u
#define AP_REWARD_TRAP 1u
#define AP_REWARD_ONE_UP 2u
#define AP_REWARD_FOOD 3u
#define AP_REWARD_DRINK 4u
#define AP_REWARD_MEAT 5u
#define AP_REWARD_TOMATO 6u
#define AP_REWARD_CANDY 7u
#define AP_REWARD_BATTERY 8u
#define AP_REWARD_ART_COUNT 9u
#define AP_REWARD_MASK_GEM (1u << AP_REWARD_GEM)
#define AP_REWARD_MASK_TRAP (1u << AP_REWARD_TRAP)
#define AP_REWARD_KEY_MASK 0x0FFFFFFFu
#define AP_REWARD_ART_SHIFT 28u
#define AP_REWARD_BOSS 2u
#define AP_REWARD_MAP_CHEST 9u
#define AP_REWARD_VITALITY_CHEST 10u
#define AP_REWARD_SOUND_CHEST 11u
#define AP_REWARD_ROOM 12u
#define AP_REWARD_SWITCH 13u
#define AP_REWARD_MINOR_CHEST 14u
#define AP_REWARD_AREA 15u
#define AP_REWARD_LEVER 3u
#define AP_REWARD_GOAL 4u
#define AP_REWARD_KEY(kind, id) (((uint32_t)(kind) << 24) | (uint32_t)(id))

struct ApRewardArtConfig {
    uint32_t marker, count, keys[AP_REWARD_ART_CAPACITY];
};

_Static_assert(sizeof(struct ApRewardArtConfig) == 0x800u, "Reward art config ABI changed");

/* Seed ROMs store only exceptions to generic art (traps and local consumables).
 * No network round trip, scouting request, or receipt can trigger this lookup. */
static inline uint8_t ap_reward_art_from_config(
    const volatile struct ApRewardArtConfig *config, uint32_t key
) {
    uint32_t first = 0u, past = config->count;
    if (config->marker != AP_REWARD_ART_MAGIC || past > AP_REWARD_ART_CAPACITY || !key || key > AP_REWARD_KEY_MASK) {
        return AP_REWARD_GEM;
    }
    while (first < past) {
        uint32_t mid = first + (past - first) / 2u;
        uint32_t entry = config->keys[mid];
        uint32_t index = entry & AP_REWARD_KEY_MASK;
        if (index == key) {
            uint32_t art = entry >> AP_REWARD_ART_SHIFT;
            return art < AP_REWARD_ART_COUNT ? (uint8_t)art : AP_REWARD_GEM;
        }
        if (index < key) first = mid + 1u;
        else past = mid;
    }
    return AP_REWARD_GEM;
}
/* A non-generic result keeps its own slot if only one effect can be made. */
static inline uint8_t ap_reward_preferred_art(uint16_t arts) {
    for (uint8_t art = AP_REWARD_TRAP; art < AP_REWARD_ART_COUNT; ++art) {
        if (arts & (1u << art)) return art;
    }
    return AP_REWARD_GEM;
}

#endif
