#ifndef KIRBYAM_VITALITY_RUNTIME_LOGIC_H
#define KIRBYAM_VITALITY_RUNTIME_LOGIC_H

#include <stdint.h>

/* Shared format-2 native health policy. No direct SRAM writes. */
#define AP_VITALITY_MASK 0x1FFu
#define AP_HEALTH_CONFIG_MAGIC 0xA9020000u

static inline uint8_t ap_health_config_valid(uint32_t config) {
    uint32_t minimum = config & 0xFFu;
    uint32_t maximum = (config >> 8) & 0xFFu;
    return (config & 0xFFFF0000u) == AP_HEALTH_CONFIG_MAGIC
        && minimum >= 1u && minimum <= maximum && maximum <= 10u;
}

static inline uint32_t ap_vitality_item_bit(uint32_t item) {
    switch (item) {
    case 3860018u: return 1u;
    case 3860019u: return 2u;
    case 3860020u: return 4u;
    case 3860021u: return 8u;
    case 3860224u: return 16u;
    case 3860225u: return 32u;
    case 3860226u: return 64u;
    case 3860227u: return 128u;
    case 3860228u: return 256u;
    default: return 0u;
    }
}

static inline uint16_t ap_vitality_limit(uint32_t config) {
    /* Invalid config cannot opt into extra upgrades. */
    if (!ap_health_config_valid(config)) return 4u;
    return (uint16_t)(((config >> 8) & 0xFFu) - (config & 0xFFu));
}

static inline uint16_t ap_vitality_earned(uint32_t config, uint32_t mask) {
    uint16_t count = 0u;
    uint16_t limit = ap_vitality_limit(config);
    mask &= AP_VITALITY_MASK;
    while (mask != 0u) {
        count += (uint16_t)(mask & 1u);
        mask >>= 1;
    }
    return count > limit ? limit : count;
}

static inline uint8_t ap_vitality_capacity(uint32_t config, uint16_t saved) {
    uint16_t limit = ap_vitality_limit(config);
    uint8_t minimum = ap_health_config_valid(config) ? (uint8_t)config : 6u;
    return (uint8_t)(minimum + (saved > limit ? limit : saved));
}

static inline uint16_t ap_vitality_menu_count(uint16_t saved) {
    return saved > 4u ? 4u : saved;
}

static inline uint16_t ap_vitality_partial_count(uint32_t config,
                                                uint32_t owned,
                                                uint16_t saved) {
    uint16_t count = ap_vitality_earned(config, owned);
    uint16_t limit = ap_vitality_limit(config);
    if (saved > limit) saved = limit;
    return count > saved ? count : saved;
}

static inline int8_t ap_vitality_grant_hp(int8_t hp, uint8_t capacity,
                                        uint8_t increased) {
    /* A reconstructed receipt bit is not a fresh upgrade. Keep dead HP signed. */
    if (hp <= 0) return hp;
    if (increased || hp > (int8_t)capacity) return (int8_t)capacity;
    return hp;
}

#endif
