#ifndef KIRBYAM_CHEST_REWARD_ART_RUNTIME_H
#define KIRBYAM_CHEST_REWARD_ART_RUNTIME_H
#include <stdint.h>

/* Native sub_08155370 appends a 12-byte tile DMA record to the 64-entry ring.
 * Visual variant zero requests one four-tile transfer at construction. */
struct ApChestTileUpload {
    uint32_t source;
    uint32_t destination;
    uint16_t size;
    uint16_t padding;
};

#define AP_CHEST_NATIVE_TILES 0x0861F46Cu
#define AP_CHEST_ART_SIZE 128u
#define AP_REWARD_EFFECT_SIZE 0x4Cu

/* The native 64-entry ring uses equal head/tail to mean empty, so the last
 * slot is reserved. Animation commands append unconditionally; check here
 * before starting any optional animation or injecting an additional upload. */
static inline uint8_t ap_reward_tile_queue_available(uint8_t head, uint8_t tail) {
    return head < 64u && tail < 64u && ((head + 1u) & 63u) != tail;
}

static inline uint8_t ap_reward_vram_address_is_valid(uint32_t address) {
    return address >= 0x06014000u && address <= 0x06018000u - AP_CHEST_ART_SIZE;
}

/* Mirror the USA VramMalloc first fit without mutating its heap. Occupied
 * runs are tagged only at the start; interior zero entries are not free. */
static inline uint8_t ap_reward_native_vram_can_fit_tiles(
    const volatile uint16_t *segments, uint16_t tile_slots, uint32_t base, uint16_t tiles
) {
    uint32_t count = tile_slots >> 1, needed = tiles >> 1;
    if (!needed || tiles & 1u || count > 0x200u || base < 0x06010000u || base >= 0x06018000u) return 0u;
    for (uint32_t i = 0u; i + needed <= count;) {
        uint16_t occupied = segments[i];
        if (occupied == 0u) {
            uint32_t run = 1u;
            while (run < needed && !segments[i + run]) ++run;
            if (run == needed) {
                uint32_t address = base + i * 64u;
                return address >= 0x06014000u && address <= 0x06018000u - (uint32_t)tiles * 32u;
            }
            i += run;
        } else {
            i += occupied;
        }
    }
    return 0u;
}

static inline uint8_t ap_reward_native_vram_can_fit(
    const volatile uint16_t *segments, uint16_t tile_slots, uint32_t base
) {
    return ap_reward_native_vram_can_fit_tiles(segments, tile_slots, base, 4u);
}

/* TaskCreate may return a linked task when both heaps fail. Reject invalid
 * offsets before initializing an effect or attaching its destructor. */
static inline uint32_t ap_reward_task_effect_address(uint16_t offset, uint16_t flags) {
    if (flags & 0x10u) {
        uint32_t address = 0x02000000u + ((uint32_t)offset << 2);
        return address >= 0x02000008u && address <= 0x02020080u - AP_REWARD_EFFECT_SIZE ? address : 0u;
    }
    uint32_t address = 0x03000000u + offset;
    return address >= 0x03003A24u && address <= 0x03006024u - AP_REWARD_EFFECT_SIZE
        && !(address & 3u) ? address : 0u;
}


static inline uint8_t ap_chest_redirect_upload(
    volatile struct ApChestTileUpload *ring, uint8_t before, uint8_t after, uint32_t source
) {
    if (before >= 64u || after != ((before + 1u) & 63u)) return 0u;
    volatile struct ApChestTileUpload *upload = &ring[before];
    if (upload->source != AP_CHEST_NATIVE_TILES || upload->size != AP_CHEST_ART_SIZE
        || upload->destination < 0x06014000u || upload->destination > 0x06018000u - AP_CHEST_ART_SIZE)
        return 0u;
    upload->source = source;
    return 1u;
}

#endif
