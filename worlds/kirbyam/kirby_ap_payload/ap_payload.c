#include <stdint.h>

#define AP_BASE                 0x0202C000u
#define AP_SHARD_BITFIELD       (*(volatile uint32_t*)(AP_BASE + 0x00u))
#define AP_IN_FLAG              (*(volatile uint32_t*)(AP_BASE + 0x04u))
#define AP_IN_ITEM_ID           (*(volatile uint32_t*)(AP_BASE + 0x08u))
#define AP_IN_PLAYER            (*(volatile uint32_t*)(AP_BASE + 0x0Cu))
#define AP_DEBUG_HEARTBEAT      (*(volatile uint32_t*)(AP_BASE + 0x10u))
#define AP_DEBUG_LAST_ITEM_ID   (*(volatile uint32_t*)(AP_BASE + 0x14u))
#define AP_DEBUG_LAST_FROM      (*(volatile uint32_t*)(AP_BASE + 0x18u))

#define KIRBY_BASE_OFFSET       3860000u  // must match worlds/kirbyam/data.py BASE_OFFSET

static void ap_apply_item(uint32_t ap_item_id) {
    // Expect shards to be BASE_OFFSET+1 .. BASE_OFFSET+8
    if (ap_item_id >= (KIRBY_BASE_OFFSET + 1u) && ap_item_id <= (KIRBY_BASE_OFFSET + 8u)) {
        uint32_t shard_index = ap_item_id - (KIRBY_BASE_OFFSET + 1u); // 0..7
        AP_SHARD_BITFIELD |= (1u << shard_index);
        return;
    }

    // Unknown item: no-op for now (playable-first)
}

void ap_poll_mailbox_c(void) {
    AP_DEBUG_HEARTBEAT++;

    // if (AP_IN_FLAG != 1u) return;

    // uint32_t item = AP_IN_ITEM_ID;
    // uint32_t from = AP_IN_PLAYER;

    // // Debug: confirm delivery
    // AP_DEBUG_LAST_ITEM_ID = item;
    // AP_DEBUG_LAST_FROM = from;

    // ap_apply_item(item);

    // // Acknowledge / consume
    // AP_IN_FLAG = 0u;

    if (AP_IN_FLAG != 1u) return;

    uint32_t item = AP_IN_ITEM_ID;
    AP_DEBUG_LAST_ITEM_ID = item;

    // FORCE: prove we can change the bitfield
    AP_SHARD_BITFIELD = 0x12345678u;  // obvious value

    AP_IN_FLAG = 0u;
}
