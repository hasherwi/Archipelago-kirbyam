#ifndef KIRBYAM_RECEIPT_SOUND_RUNTIME_H
#define KIRBYAM_RECEIPT_SOUND_RUNTIME_H
#include <stdint.h>

#define AP_CUE_MAILBOX_ADDRESS 0x0203B1B0u
#define AP_CUE_FRAME_MASK 0x1FFFFFFFu
#define AP_CUE_REJECTED 0x80000000u

/* Permit several frames of connector latency, but do not leave an old
 * request armed across a transition, native load, or rewind. The queue on
 * the client retries only a positively rejected request. */
static inline uint8_t ap_cue_request_valid(uint32_t request, uint32_t frame, uint32_t ready) {
    uint32_t age = (frame - (request >> 2)) & AP_CUE_FRAME_MASK;
    return (request & 3u) && !(request & AP_CUE_REJECTED)
        && age <= 8u && (ready & (1u << (request & 3u)));
}
#endif
