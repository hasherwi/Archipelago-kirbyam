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
