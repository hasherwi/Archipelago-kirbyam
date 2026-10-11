#ifndef KIRBYAM_LEVER_RUNTIME_LOGIC_H
#define KIRBYAM_LEVER_RUNTIME_LOGIC_H

#include <stdint.h>

/* Verified USA Chest objects in the four repository lever savestates.
 * See dev-docs/lever-runtime-regressions.md for provenance and lifecycle. */
static inline uint32_t ap_lever_bit_for_chest(
    uint32_t source_ptr, uint16_t reward, uint8_t chest_id
) {
    if (reward != 0x63u) {
        return 0u;
    }
    switch (source_ptr) {
        case 0x088BE07Cu: return chest_id == 18u ? 1u : 0u;
        case 0x088CD240u: return chest_id == 65u ? 2u : 0u;
        case 0x088D2E68u: return chest_id == 77u ? 4u : 0u;
        case 0x088D1454u: return chest_id == 74u ? 8u : 0u;
        default: return 0u;
    }
}

/* Each live lever object contributes at most once to its room's wall counter.
 * Physical activation and AP wall ownership are deliberately independent. */
static inline uint8_t ap_lever_should_open_wall(uint8_t owned, uint32_t applied) {
    return (owned != 0u && applied == 0u) ? 1u : 0u;
}

#endif
