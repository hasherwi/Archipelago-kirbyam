#include <assert.h>
#include <stdint.h>
#include <string.h>
#include "shard_award_runtime.h"
#include "reward_art_config.h"
#include "boss_shard_art_runtime.h"
static uint8_t dma_head, dma_tail, selected_art;
static struct ApChestTileUpload dma_ring[64];
#define AP_REWARD_UPLOAD_TAIL dma_tail
static unsigned native_pops, optional_task_attempts;
static uint16_t native_popup_variant;

static void native_chest(void *chest, int16_t x, int16_t y, uint16_t variant) {
    (void)chest;
    (void)x;
    (void)y;
    ++native_pops;   /* The real no-art variant creates the normal reward timer. */
    native_popup_variant = variant;
    if (variant == 0u) {
        dma_ring[dma_head] = (struct ApChestTileUpload){
            AP_CHEST_NATIVE_TILES, 0x06014100u, AP_CHEST_ART_SIZE, 0u,
        };
        dma_head = (dma_head + 1u) & 63u;
    }
}

static void ap_reward_gem_frame(void) {}
static void *create_task(void (*main_fn)(void), uint16_t size, uint16_t priority,
                         uint16_t flags, void (*destroy)(void *)) {
    (void)main_fn;
    (void)size;
    (void)priority;
    (void)flags;
    (void)destroy;
    ++optional_task_attempts;
    return (void*)0x03002500u;
}

static uint8_t ap_reward_native_vram_available(void) { return 1u; }
static uint32_t ap_reward_key_for_chest(const void *chest) { (void)chest; return 1u; }
static uint8_t ap_reward_art_for_key(uint32_t key) { (void)key; return selected_art; }
static uint32_t ap_reward_tiles_for_art(uint8_t art) { (void)art; return 0x09008000u; }
static uint16_t ap_reward_local_room(void) { return 7u; }
static uint8_t ap_can_show_animated_shard(void) { return ap_reward_tile_queue_available(dma_head, dma_tail); }
static uint8_t *ap_reward_task_data(void *task) { (void)task; return 0; }
static void ap_drop_invalid_reward_task(void *task) { (void)task; }

/* OVERLAY */
/* CHEST */

int main(void) {
    _Alignas(4) uint8_t chest[0xE4] = {0};
    ((uint16_t*)chest)[0x60 / 2] = 7u;
    memset(dma_ring, 0x5A, sizeof(dma_ring));
    struct ApChestTileUpload original[64];
    memcpy(original, dma_ring, sizeof(original));

    /* Both wrap and non-wrap full queues reject every optional upload. */
    for (unsigned tail = 0; tail < 64; ++tail) {
        dma_head = (tail + 63u) & 63u;
        dma_tail = tail;
        assert(!ap_reward_tile_queue_available(dma_head, dma_tail));
        for (unsigned shard = 0; shard < 2; ++shard) {
            selected_art = shard ? AP_REWARD_MIRROR_SHARD : 0u;
            native_pops = optional_task_attempts = 0;
            ap_chest_reward_art(chest, 1, 2, shard ? 0x0Au : 0x63u);
            assert(native_pops == 1u && native_popup_variant == 0x63u);
            assert(!ap_show_room_reward_gem(7u, 0, 0, 0, selected_art));
            assert(optional_task_attempts == 0u);
            assert(dma_head == ((tail + 63u) & 63u) && dma_tail == tail);
            assert(memcmp(original, dma_ring, sizeof(original)) == 0);
        }
    }

    /* With one real slot, chest uploads into it; a following second award
     * (e.g. same transition or receipt) must not make the queue look empty. */
    dma_head = 62u;
    dma_tail = 0;
    assert(ap_reward_tile_queue_available(dma_head, dma_tail));
    selected_art = 0u;
    ap_chest_reward_art(chest, 1, 2, 0x63u);
    assert(native_popup_variant == 0u && dma_head == 63u);
    assert(dma_ring[62].source == 0x09008000u);
    assert(!ap_show_room_reward_gem(7u, 0, 0, 0, 0));
    assert(optional_task_attempts == 0u);
    assert(dma_head != dma_tail && dma_tail == 0u);
    assert(!ap_reward_tile_queue_available(64u, 0u));
    assert(!ap_reward_tile_queue_available(0u, 64u));
    return 0;
}
