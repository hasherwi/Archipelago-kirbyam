#ifndef KIRBYAM_SHARED_SAVE_LOGIC_H
#define KIRBYAM_SHARED_SAVE_LOGIC_H
#include <stdint.h>

/* WORLD 22..26, independent of the Hub record at 27..31. */
#define AP_SHARED_TAG 0x41500000u
#define AP_SHARED_GOALS 0x0000FFFFu
#define AP_SHARED_ACCESS_OWNED 0x00010000u
#define AP_SHARED_ACCESS_VALID 0x00020000u
#define AP_SHARED_BITS 0x0003FFFFu
#define AP_SHARED_INVALID_SLOT 0xFFFFFFFFu

static inline uint8_t ap_shared_record_valid(const volatile uint32_t *record,
                                            const volatile uint32_t *auth) {
    uint32_t i;
    if ((record[4] & ~AP_SHARED_BITS) != AP_SHARED_TAG) return 0u;
    for (i=0u; i<4u; ++i) if (record[i] != auth[i]) return 0u;
    return 1u;
}
static inline uint32_t ap_shared_record_bits(const volatile uint32_t *record,
                                            const volatile uint32_t *auth) {
    return ap_shared_record_valid(record, auth) ? record[4] & AP_SHARED_BITS : 0u;
}
/* Publish the tag last. No observer can accept an identity halfway through
 * replacement, and neither feature can inherit the other's stale bits. */
static inline uint8_t ap_shared_record_init(volatile uint32_t *record,
                                           const volatile uint32_t *auth) {
    uint32_t i;
    if (ap_shared_record_valid(record, auth)) return 0u;
    record[4] = 0u;
    for (i=0u; i<4u; ++i) record[i] = auth[i];
    record[4] = AP_SHARED_TAG;
    return 1u;
}
static inline uint8_t ap_shared_record_update(volatile uint32_t *record,
                                             const volatile uint32_t *auth,
                                             uint32_t clear, uint32_t set) {
    uint32_t previous, next;
    if (!ap_shared_record_valid(record, auth) || ((clear | set) & ~AP_SHARED_BITS)) return 0u;
    previous = record[4];
    next = (previous & ~clear) | set;
    if (next == previous) return 0u;
    record[4] = next;
    return 1u;
}
static inline uint32_t ap_shared_next_epoch(uint32_t serial) {
    ++serial;
    return serial ? serial : 1u;
}
#endif
