#ifndef KIRBYAM_RECEIPT_VISUAL_RUNTIME_H
#define KIRBYAM_RECEIPT_VISUAL_RUNTIME_H
#include <stdint.h>

#define AP_VISUAL_MAILBOX_ADDRESS 0x0203B1E0u
#define AP_VISUAL_FRAME_MASK 0x07FFFFFFu
#define AP_VISUAL_CODE_MASK 15u
#define AP_VISUAL_FRAME_SHIFT 4u
#define AP_VISUAL_REJECTED 0x80000000u
#define AP_VISUAL_GEM 1u
#define AP_VISUAL_TRAP 2u
#define AP_VISUAL_MAX_CODE 9u
#define AP_VISUAL_READY_MASK ((1u << (AP_VISUAL_MAX_CODE + 1u)) - 2u)
#define AP_VISUAL_DURATION 32u

struct ApReceiptVisualMailbox { uint32_t request, result, ready, active; };

static inline uint32_t ap_visual_age(uint32_t packet, uint32_t now) {
    return (now - (packet >> AP_VISUAL_FRAME_SHIFT)) & AP_VISUAL_FRAME_MASK;
}

static inline uint8_t ap_visual_can_start(uint32_t request, uint32_t frame, uint32_t ready) {
    uint32_t kind = request & AP_VISUAL_CODE_MASK;
    return !(request & AP_VISUAL_REJECTED) && ap_visual_age(request, frame) <= 8u
        && (ready & (1u << kind) & AP_VISUAL_READY_MASK) != 0u;
}

#endif
