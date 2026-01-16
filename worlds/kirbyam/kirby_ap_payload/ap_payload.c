#include <stdint.h>

// Kirby AP item ID base offset
#define KIRBY_BASE_OFFSET       3860000u  // must match worlds/kirbyam/data.py BASE_OFFSET

// AP Mailbox Registers
#define AP_BASE                 0x0202C000u
#define AP_IN_FLAG              (*(volatile uint32_t*)(AP_BASE + 0x04u))
#define AP_IN_ITEM_ID           (*(volatile uint32_t*)(AP_BASE + 0x08u))
#define AP_IN_PLAYER            (*(volatile uint32_t*)(AP_BASE + 0x0Cu))
#define AP_DEBUG_HEARTBEAT      (*(volatile uint32_t*)(AP_BASE + 0x10u))
#define AP_DEBUG_LAST_ITEM_ID   (*(volatile uint32_t*)(AP_BASE + 0x14u))
#define AP_DEBUG_LAST_FROM      (*(volatile uint32_t*)(AP_BASE + 0x18u))

// Shard State Registers
#define AP_SHARD_BITFIELD       (*(volatile uint32_t*)(AP_BASE + 0x00u))
#define KIRBY_SHARD_FLAGS_ADDR  0x02038970u
#define KIRBY_SHARD_FLAGS       (*(volatile uint8_t*)(KIRBY_SHARD_FLAGS_ADDR))

// Player lives is a single byte in EWRAM
#define KIRBY_LIVES_ADDR        0x02020FE2u
#define KIRBY_LIVES             (*(volatile uint8_t*)(KIRBY_LIVES_ADDR))

static void ap_apply_item(uint32_t ap_item_id) {
    // 1_UP = BASE+1
    if (ap_item_id == (KIRBY_BASE_OFFSET + 1u)) {

        uint8_t lives = KIRBY_LIVES;

        if (lives < 255u) {
            KIRBY_LIVES = (uint8_t)(lives + 1u);
        }

        return;
    }

    // SHARD_1..SHARD_8 = BASE+2 .. BASE+9
    if (ap_item_id >= (KIRBY_BASE_OFFSET + 2u) && ap_item_id <= (KIRBY_BASE_OFFSET + 9u)) {

        uint32_t shard_index = ap_item_id - (KIRBY_BASE_OFFSET + 2u); // 0..7
        uint8_t mask = (uint8_t)(1u << shard_index);

        // Optional: keep hack mirror for AP client polling/debugging
        AP_SHARD_BITFIELD |= (uint32_t)mask;

        // Actual game state
        KIRBY_SHARD_FLAGS |= mask;

        return;
    }

    // Unhandled item
}


void ap_poll_mailbox_c(void) {

    // Check if there's an item to process
    if (AP_IN_FLAG != 1u) return;

    // Debug heartbeat
    AP_DEBUG_HEARTBEAT++;

    // Receive an item from a player
    uint32_t item = AP_IN_ITEM_ID;
    uint32_t from = AP_IN_PLAYER;

    // Debug: confirm delivery
    AP_DEBUG_LAST_ITEM_ID = item;
    AP_DEBUG_LAST_FROM = from;

    // Apply the received item
    ap_apply_item(item);

    // Acknowledge / consume
    AP_IN_FLAG = 0u;
}
