#ifndef KIRBYAM_SHARD_AWARD_RUNTIME_H
#define KIRBYAM_SHARD_AWARD_RUNTIME_H
#include "chest_reward_art_runtime.h"

#define AP_SHARD_AWARD_ROM 0x09007000u
#define AP_SHARD_AWARD_MAGIC_FIRST 0x48535041u
#define AP_SHARD_AWARD_MAGIC_LAST 0x00313044u
#define AP_SHARD_AWARD_FIRST (AP_SHARD_AWARD_ROM + 8u)
#define AP_SHARD_AWARD_TICKS 40u
#define AP_SHARD_AWARD_ART_SIZE 512u
#define AP_SHARD_AWARD_VRAM_TILES 16u
#define AP_SHARD_AWARD_STATIC_ANIM 0x2D2u
#define AP_SHARD_AWARD_NATIVE_TILES 0x0861FB6Cu

static inline uint8_t ap_shard_award_vram_valid(uint32_t destination) {
    return destination >= 0x06014000u && destination <= 0x06018000u - AP_SHARD_AWARD_ART_SIZE;
}

static inline uint8_t ap_shard_award_source_valid(uint32_t source) {
    return source >= AP_SHARD_AWARD_FIRST
        && source < AP_SHARD_AWARD_FIRST + AP_SHARD_AWARD_TICKS * AP_SHARD_AWARD_ART_SIZE
        && ((source - AP_SHARD_AWARD_FIRST) & (AP_SHARD_AWARD_ART_SIZE - 1u)) == 0u;
}

static inline uint8_t ap_shard_award_redirect_first(
    volatile struct ApChestTileUpload *ring, uint8_t before, uint8_t after, uint32_t destination
) {
    if (before >= 64u || after != ((before + 1u) & 63u) || !ap_shard_award_vram_valid(destination)) return 0u;
    volatile struct ApChestTileUpload *upload = &ring[before];
    if (upload->source != AP_SHARD_AWARD_NATIVE_TILES || upload->size != AP_SHARD_AWARD_ART_SIZE
        || upload->destination != destination) return 0u;
    upload->source = AP_SHARD_AWARD_FIRST;
    return 1u;
}

/* Changes in the stock-derived, clipped composite; held ticks need no
 * duplicate DMA. Stock source fingerprints pin this exact frame sequence. */
static inline uint8_t ap_shard_award_frame_changed(uint8_t tick) {
    if (tick < 32u) return (0x108F3FFCu >> tick) & 1u;
    return tick < AP_SHARD_AWARD_TICKS && ((0x42u >> (tick - 32u)) & 1u);
}

/* A failed optional animation upload drops a frame, never a native queue item. */
static inline uint8_t ap_shard_award_queue_frame(
    volatile struct ApChestTileUpload *ring, volatile uint8_t *head, uint8_t tail,
    uint32_t destination, uint8_t tick
) {
    uint8_t index = *head;
    if (!ap_reward_tile_queue_available(index, tail)
        || !ap_shard_award_vram_valid(destination) || tick >= AP_SHARD_AWARD_TICKS) return 0u;
    volatile struct ApChestTileUpload *upload = &ring[index];
    upload->source = AP_SHARD_AWARD_FIRST + (uint32_t)tick * AP_SHARD_AWARD_ART_SIZE;
    upload->destination = destination;
    upload->size = AP_SHARD_AWARD_ART_SIZE;
    *head = (index + 1u) & 63u;
    return 1u;
}

static inline void ap_shard_award_cancel_uploads(
    volatile struct ApChestTileUpload *ring, uint8_t head, uint8_t tail, uint32_t destination
) {
    if (head >= 64u || tail >= 64u || !ap_shard_award_vram_valid(destination)) return;
    /* If VBlank has not drained our art, do not let it write a now-freed OBJ
     * allocation. No native transfer, cursor, or unrelated destination changes. */
    while (tail != head) {
        volatile struct ApChestTileUpload *upload = &ring[tail];
        if (upload->destination == destination && ap_shard_award_source_valid(upload->source)) {
            upload->size = 0u;
        }
        tail = (tail + 1u) & 63u;
    }
}

#endif
