#ifndef KIRBYAM_REWARD_ART_CONFIG_H
#define KIRBYAM_REWARD_ART_CONFIG_H
#include <stdint.h>

#define AP_REWARD_ART_MAGIC 0x31565241u /* ARV1 */
#define AP_REWARD_ART_CAPACITY 510u
#define AP_REWARD_GEM 0u
#define AP_REWARD_TRAP 1u
#define AP_REWARD_MASK_GEM (1u << AP_REWARD_GEM)
#define AP_REWARD_MASK_TRAP (1u << AP_REWARD_TRAP)
#define AP_REWARD_BOSS 2u
#define AP_REWARD_MAP_CHEST 9u
#define AP_REWARD_VITALITY_CHEST 10u
#define AP_REWARD_SOUND_CHEST 11u
#define AP_REWARD_ROOM 12u
#define AP_REWARD_SWITCH 13u
#define AP_REWARD_MINOR_CHEST 14u
#define AP_REWARD_AREA 15u
#define AP_REWARD_LEVER 16u
#define AP_REWARD_GOAL 17u
#define AP_REWARD_KEY(kind, id) (((uint32_t)(kind) << 24) | (uint32_t)(id))

struct ApRewardArtConfig {
    uint32_t marker, count, keys[AP_REWARD_ART_CAPACITY];
};

_Static_assert(sizeof(struct ApRewardArtConfig) == 0x800u, "Reward art config ABI changed");

/* Seed ROMs store only exceptions to generic art (known trap placements).
 * No network round trip, scouting request, or receipt can trigger artwork. */
static inline uint8_t ap_reward_art_from_config(
    const volatile struct ApRewardArtConfig *config, uint32_t key
) {
    uint32_t first = 0u, past = config->count;
    if (config->marker != AP_REWARD_ART_MAGIC || past > AP_REWARD_ART_CAPACITY || !key) {
        return AP_REWARD_GEM;
    }
    while (first < past) {
        uint32_t mid = first + (past - first) / 2u;
        uint32_t entry = config->keys[mid];
        if (entry == key) return AP_REWARD_TRAP;
        if (entry < key) first = mid + 1u;
        else past = mid;
    }
    return AP_REWARD_GEM;
}
#endif
