#ifndef KIRBYAM_CANDY_RUNTIME_LOGIC_H
#define KIRBYAM_CANDY_RUNTIME_LOGIC_H
#include <stdint.h>

/* Retail sub_0808324C and its active task use this same room exclusion list. */
static inline uint8_t ap_candy_room_supported(uint16_t room, const volatile uint16_t *boss_rooms) {
    uint32_t i;
    if (room > 899u || room == 801u) return 0u;
    for (i = 1u; i <= 8u; ++i) {
        if (room == boss_rooms[i]) return 0u;
    }
    return 1u;
}
#endif
