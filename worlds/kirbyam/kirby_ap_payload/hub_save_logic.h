#ifndef KIRBYAM_HUB_SAVE_LOGIC_H
#define KIRBYAM_HUB_SAVE_LOGIC_H
#include <stdint.h>

/* USA world-state words 27..31 are inside the native checksummed, duplicated
 * save section, but have no native consumers. Words 27..30 bind physical checks
 * to the full ROM auth token. Version 2 packs 15 switches and four lever pulls
 * in word 31. Legacy hub-only records remain readable and migrate on mutation.
 * Ownership bits and native chest flags are never used to invent a pull. */
#define AP_HUB_SAVE_TAG 0x48530000u
#define AP_HUB_SAVE_MASK 0x00007FFFu
#define AP_PHYSICAL_SAVE_TAG 0x48400000u
#define AP_PHYSICAL_SAVE_MASK 0x0007FFFFu
#define AP_LEVER_SAVE_SHIFT 15u
static inline uint32_t ap_physical_saved_checks(
    const volatile uint32_t saved[5], const volatile uint32_t auth[4]
) {
    uint32_t i, mask;
    if ((saved[4] & ~AP_PHYSICAL_SAVE_MASK) == AP_PHYSICAL_SAVE_TAG)
        mask = AP_PHYSICAL_SAVE_MASK;
    else if ((saved[4] & ~AP_HUB_SAVE_MASK) == AP_HUB_SAVE_TAG)
        mask = AP_HUB_SAVE_MASK;
    else return 0u;
    for (i = 0u; i < 4u; i++) if (saved[i] != auth[i]) return 0u;
    return saved[4] & mask;
}
static inline uint32_t ap_hub_saved_checks(
    const volatile uint32_t saved[5], const volatile uint32_t auth[4]
) {
    return ap_physical_saved_checks(saved, auth) & AP_HUB_SAVE_MASK;
}
static inline uint32_t ap_lever_saved_checks(
    const volatile uint32_t saved[5], const volatile uint32_t auth[4]
) {
    return ap_physical_saved_checks(saved, auth) >> AP_LEVER_SAVE_SHIFT;
}
static inline uint8_t ap_record_physical_check(
    volatile uint32_t saved[5], const volatile uint32_t auth[4], uint32_t bit
) {
    uint32_t i, mask;
    if (bit >= 19u) return 0u;
    mask = ap_physical_saved_checks(saved, auth);
    if (mask & (1u << bit)) return 0u;
    for (i = 0u; i < 4u; i++) saved[i] = auth[i];
    saved[4] = AP_PHYSICAL_SAVE_TAG | mask | (1u << bit);
    return 1u;
}
static inline uint8_t ap_hub_record_check(
    volatile uint32_t saved[5], const volatile uint32_t auth[4], uint32_t bit
) {
    return bit < 15u ? ap_record_physical_check(saved, auth, bit) : 0u;
}
static inline uint8_t ap_lever_record_check(
    volatile uint32_t saved[5], const volatile uint32_t auth[4], uint32_t bit
) {
    return bit < 4u ? ap_record_physical_check(saved, auth, bit + AP_LEVER_SAVE_SHIFT) : 0u;
}
/* Match WorldMapUnlockSave's native save-disable, link-owner and slot policy. */
static inline uint32_t ap_hub_save_action(uint32_t flags, uint8_t local, uint8_t owner) {
    if (flags & 0x10u) return 0u;
    return ((flags & 2u) && local != owner) ? 2u : 1u;
}
static inline uint16_t ap_hub_save_slot(uint16_t slot) { return slot <= 2u ? slot : 0u; }
#endif
