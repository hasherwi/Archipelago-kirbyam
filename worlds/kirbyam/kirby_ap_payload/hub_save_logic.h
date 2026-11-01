#ifndef KIRBYAM_HUB_SAVE_LOGIC_H
#define KIRBYAM_HUB_SAVE_LOGIC_H
#include <stdint.h>

/* USA world-state words 27..31 are inside the native checksummed, duplicated
 * save section, but have no native consumers. Words 27..30 bind the check mask
 * to the complete per-seed ROM auth token; word 31 carries a version tag.
 * No SRAM offsets, section sizes, slot numbering, or checksum rules change. */
#define AP_HUB_SAVE_TAG 0x48530000u
#define AP_HUB_SAVE_MASK 0x00007FFFu
static inline uint32_t ap_hub_saved_checks(
    const volatile uint32_t saved[5], const volatile uint32_t auth[4]
) {
    uint32_t i;
    if ((saved[4] & ~AP_HUB_SAVE_MASK) != AP_HUB_SAVE_TAG) return 0u;
    for (i = 0u; i < 4u; i++) if (saved[i] != auth[i]) return 0u;
    return saved[4] & AP_HUB_SAVE_MASK;
}
static inline uint8_t ap_hub_record_check(
    volatile uint32_t saved[5], const volatile uint32_t auth[4], uint32_t bit
) {
    uint32_t i, mask;
    if (bit >= 15u) return 0u;
    mask = ap_hub_saved_checks(saved, auth);
    if (mask & (1u << bit)) return 0u;
    for (i = 0u; i < 4u; i++) saved[i] = auth[i];
    saved[4] = AP_HUB_SAVE_TAG | mask | (1u << bit);
    return 1u;
}
/* Match WorldMapUnlockSave's native save-disable, link-owner and slot policy. */
static inline uint32_t ap_hub_save_action(uint32_t flags, uint8_t local, uint8_t owner) {
    if (flags & 0x10u) return 0u;
    return ((flags & 2u) && local != owner) ? 2u : 1u;
}
static inline uint16_t ap_hub_save_slot(uint16_t slot) { return slot <= 2u ? slot : 0u; }
#endif
