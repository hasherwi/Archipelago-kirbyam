#ifndef KIRBYAM_COLOR_RUNTIME_LOGIC_H
#define KIRBYAM_COLOR_RUNTIME_LOGIC_H
#include <stdint.h>
#include "color_tables.h"

/* Versioned ROM configuration; legacy concrete color words remain static. */
#define AP_COLOR_CONFIG_MAGIC 0xC0100000u
#define AP_COLOR_PER_ROOM 0x100u
#define AP_COLOR_STARTUP 0x43535441u /* bounded synchronous scene construction */
#define AP_COLOR_INVALID 0xFFFFFFFFu
#define AP_PAINT_CHOICE_MAGIC 0xC600u

static inline uint8_t ap_native_color_valid(uint32_t color) { return color < 14u; }
static inline uint8_t ap_color_valid(uint32_t color) { return color < AP_COLOR_COUNT; }
static inline uint32_t ap_native_color(uint32_t color) {
    return ap_native_color_valid(color) ? color : 0u;
}
static inline uint8_t ap_color_config_valid(uint32_t config) {
    return (config & 0xFFFFFE00u) == AP_COLOR_CONFIG_MAGIC
        && ap_color_valid(config & 0xFFu);
}
static inline uint32_t ap_color_initial(uint32_t config) {
    return ap_color_config_valid(config) ? config & 0xFFu
        : (ap_color_valid(config) ? config : 0u);
}
static inline uint8_t ap_color_per_room(uint32_t config) {
    return ap_color_config_valid(config) && (config & AP_COLOR_PER_ROOM) != 0u;
}
/* Two native Treasures tail-padding bytes, included in native checksums/copies.
 * A complemented nibble and magic distinguish an explicit choice from zero/old saves. */
static inline uint16_t ap_color_choice_encode(uint32_t color) {
    return (uint16_t)(AP_PAINT_CHOICE_MAGIC | (color << 4) | (color ^ 15u));
}
static inline uint32_t ap_color_choice_decode(uint16_t saved, uint32_t paints) {
    uint32_t color = (saved >> 4) & 15u;
    return ap_native_color_valid(color) && saved == ap_color_choice_encode(color)
        && (paints & (1u << color)) ? color : AP_COLOR_INVALID;
}
static inline uint32_t ap_color_resolve(uint32_t config, uint32_t runtime,
                                      uint16_t saved, uint32_t paints) {
    uint32_t manual = ap_color_choice_decode(saved, paints);
    if (!ap_color_per_room(config) && ap_native_color_valid(manual)) return manual;
    return ap_color_valid(runtime) ? runtime : ap_color_initial(config);
}
#endif
