#ifndef KIRBYAM_BOSS_SHARD_ART_RUNTIME_H
#define KIRBYAM_BOSS_SHARD_ART_RUNTIME_H
#include "chest_reward_art_runtime.h"

#define AP_SHARD_NATIVE_ANIM 0x2D4u
#define AP_GEM_RENDER_ANIM 0x2D1u
#define AP_SHARD_ART_PADDED_SIZE 288u

/* Native shard animation uses nine exact 4bpp tile batches. Keep each
 * destination, copy length, and queue position. Its first (nine-tile) upload
 * primes all four gem tiles; later three-tile frames retain the fourth tile. */
static inline uint8_t ap_boss_shard_redirect_upload(
    volatile struct ApChestTileUpload *ring, uint8_t before, uint8_t after,
    uint32_t dest, uint32_t art
) {
    if (before >= 64u || after != ((before + 1u) & 63u)
        || dest < 0x06014000u || dest > 0x06018000u - AP_SHARD_ART_PADDED_SIZE) return 0u;
    volatile struct ApChestTileUpload *upload = &ring[before];
    if (upload->destination != dest) return 0u;
    switch (upload->source) {
        case 0x086249ECu: case 0x08624DACu:
            if (upload->size != 96u) return 0u;
            break;
        case 0x086247ACu: case 0x086248CCu: case 0x08624A4Cu:
        case 0x08624B6Cu: case 0x08624C8Cu: case 0x08624E0Cu: case 0x08624F2Cu:
            if (upload->size != AP_SHARD_ART_PADDED_SIZE) return 0u;
            break;
        default: return 0u;
    }
    upload->source = art;
    return 1u;
}
#endif
