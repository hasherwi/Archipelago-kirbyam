#ifndef KIRBYAM_PHONE_RUNTIME_LOGIC_H
#define KIRBYAM_PHONE_RUNTIME_LOGIC_H
#include <stdint.h>
/* This is a permission gate, not a replacement for native call eligibility.
 * The tutorial exception is local and never grants persistent ownership. */
static inline uint32_t ap_phone_blocks_initiation(
    uint32_t enabled, uint32_t epoch, uint32_t owned, uint32_t is_local,
    uint32_t room, uint32_t caller, uint32_t kirbys) {
    return enabled == 1u && epoch && !owned && is_local
        && !(room >= 803u && room <= 805u) && caller >= kirbys;
}
#endif
