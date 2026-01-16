#include <stdint.h>

#define AP_BASE            0x0202C000u
#define AP_IN_FLAG         (*(volatile uint32_t*)(AP_BASE + 0x04u))
#define AP_IN_ITEM_ID      (*(volatile uint32_t*)(AP_BASE + 0x08u))
#define AP_IN_PLAYER       (*(volatile uint32_t*)(AP_BASE + 0x0Cu))
#define AP_DEBUG_HEARTBEAT (*(volatile uint32_t*)(AP_BASE + 0x10u))

void ap_poll_mailbox_c(void) {
    AP_DEBUG_HEARTBEAT++;

    if (AP_IN_FLAG != 1u) return;

    volatile uint32_t item = AP_IN_ITEM_ID;
    volatile uint32_t from = AP_IN_PLAYER;
    (void)item; (void)from;

    AP_IN_FLAG = 0u; // acknowledge / consume
}
