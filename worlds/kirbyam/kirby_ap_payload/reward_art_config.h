#ifndef KIRBYAM_REWARD_ART_CONFIG_H
#define KIRBYAM_REWARD_ART_CONFIG_H
#include <stdint.h>

#define AP_REWARD_ART_MAGIC 0x33565241u /* ARV3 */
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
#define AP_REWARD_MAP_FIRST 9u
#define AP_REWARD_MAP_LAST 17u
#define AP_REWARD_VITALITY 18u
#define AP_REWARD_SOUND_PLAYER 19u
#define AP_REWARD_PAINT_FIRST 20u
#define AP_REWARD_PAINT_LAST 33u
#define AP_REWARD_SHEET_FIRST 34u
#define AP_REWARD_SHEET_LAST 43u
#define AP_REWARD_MIRROR_SHARD 44u
#define AP_REWARD_PHONE 45u
#define AP_REWARD_HUB_SWITCH 46u
#define AP_REWARD_LEVER_WALL 47u
#define AP_REWARD_STATUE_FIRST 48u
#define AP_REWARD_STATUE_LAST 66u
#define AP_REWARD_ART_COUNT 67u
#define AP_COLLECTIBLE_ART_ROM_ADDRESS 0x0900D000u
#define AP_COLLECTIBLE_ART_MARKER_FIRST 0x52415041u
#define AP_COLLECTIBLE_ART_MARKER_LAST 0x00353054u
#define AP_REWARD_MASK_GEM (1u << AP_REWARD_GEM)
#define AP_REWARD_MASK_TRAP (1u << AP_REWARD_TRAP)
#define AP_REWARD_KEY_MASK 0x0FFFFFFFu
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
    uint8_t variants[AP_REWARD_ART_CAPACITY];
    uint8_t reserved[2];
};

_Static_assert(sizeof(struct ApRewardArtConfig) == 0xA00u, "Reward art config ABI changed");

/* Seed ROMs store only exceptions to generic art (traps and supported local item classes).
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
        uint32_t index = config->keys[mid];
        if (index == key) {
            uint8_t art = config->variants[mid];
            return art < AP_REWARD_ART_COUNT ? art : AP_REWARD_GEM;
        }
        if (index < key) first = mid + 1u;
        else past = mid;
    }
    return AP_REWARD_GEM;
}
/* Two simultaneous checks can each name any variant. Zero means absent;
 * otherwise encode art+1. Identical icons coalesce before presentation. */
static inline uint16_t ap_reward_pair_add(uint16_t pair, uint8_t art) {
    uint16_t value = (uint16_t)art + 1u;
    uint16_t first = pair & 0xFFu;
    if (art >= AP_REWARD_ART_COUNT) return pair;
    if (!first) return value;
    if (first == value || pair >> 8) return pair;
    /* Give a trap, then any item over generic, the first chance to draw. */
    if (art == AP_REWARD_TRAP || first == AP_REWARD_GEM + 1u) {
        return (first << 8) | value;
    }
    return (value << 8) | first;
}

#endif
