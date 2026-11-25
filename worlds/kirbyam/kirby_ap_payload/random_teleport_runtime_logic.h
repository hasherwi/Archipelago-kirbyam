#ifndef KIRBYAM_RANDOM_TELEPORT_RUNTIME_LOGIC_H
#define KIRBYAM_RANDOM_TELEPORT_RUNTIME_LOGIC_H

#include <stdint.h>

#define AP_RANDOM_TELEPORT_CENTRAL_ROOM 801u

/* Central has no L-to-return flag because it is already the hub. It can
 * still use the ordinary explicit transition, with all live guards intact. */
static inline uint8_t ap_random_teleport_source_supported(
    uint16_t room, uint8_t area, uint16_t priority
) {
    return area < 9u && (room == AP_RANDOM_TELEPORT_CENTRAL_ROOM || (priority & 0x40u));
}

#endif
