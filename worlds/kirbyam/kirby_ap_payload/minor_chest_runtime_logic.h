#ifndef KIRBYAM_MINOR_CHEST_RUNTIME_LOGIC_H
#define KIRBYAM_MINOR_CHEST_RUNTIME_LOGIC_H

#include <stdint.h>

/* These are AP offsets, not native reward IDs or runtime palette indices.
 * +41..+55 are reserved by deferred work; +101..+131 are ability items.
 */
#define AP_SPRAY_PAINT_ITEM_FIRST 200u
#define AP_SPRAY_PAINT_ITEM_COUNT 14u
#define AP_MUSIC_SHEET_ITEM_FIRST 214u
#define AP_MUSIC_SHEET_ITEM_COUNT 10u

/* Equivalent to the native CollectSprayPaint/CollectMusicPlayerOrSheet OR,
 * except AP-owned physical sources defer the grant until mailbox delivery.
 * Bound the shift before touching memory, including malformed reward indices.
 */
static inline void ap_apply_native_collection_reward(
    volatile uint32_t *field, uint32_t index, uint32_t count, uint8_t ap_owned
) {
    if (!ap_owned && index < count && index < 32u) {
        *field |= 1u << index;
    }
}

/* Apply the real payload policy to native fields or host-test stand-ins.
 * The music-player unlock is bit 0; sheets own only bits 1..10.
 * Existing ownership (and unrelated/reserved bits) is always preserved.
 */
static inline uint8_t ap_apply_collection_item(
    uint32_t relative_item_id,
    volatile uint32_t *spray_field,
    volatile uint32_t *music_field
) {
    uint32_t index = relative_item_id - AP_SPRAY_PAINT_ITEM_FIRST;
    if (index < AP_SPRAY_PAINT_ITEM_COUNT) {
        *spray_field |= 1u << index;
        return 1u;
    }
    index = relative_item_id - AP_MUSIC_SHEET_ITEM_FIRST;
    if (index < AP_MUSIC_SHEET_ITEM_COUNT) {
        *music_field |= 1u << (index + 1u);
        return 1u;
    }
    return 0u;
}

#endif
