/* Curated palette extension. Native color fields always contain 0..13.
 * Intercept native loads, not VBlank: native ability/effect composition and
 * temporary variant 14 remain responsible for their own palette indices. */
#include <stdint.h>
#define AP_COLOR_INCLUDE_PALETTES
#include "color_runtime_logic.h"

__attribute__((used, section(".apcolorinfo")))
const char ap_color_catalog_marker[8] = "APCOL02";

#define U32(addr) (*(volatile uint32_t *)(addr))
#define U16(addr) (*(volatile uint16_t *)(addr))
#define U8(addr) (*(volatile uint8_t *)(addr))
#define MAIN_FLAGS U32(0x03002440u)
#define NATIVE_OBJ_TRANSFORM ((void (*)(const uint16_t *, uint8_t, uint16_t))0x0815828Du)

static uint32_t effective_color(void) {
    uint32_t runtime = U32(0x0203B040u) == 0x4B41504Du
        ? U32(0x0203B050u) : AP_COLOR_INVALID;
    return ap_color_resolve(U32(0x0815F694u), runtime,
                            U16(0x02038982u), U32(0x02038974u));
}

static const uint16_t *curated_palette(uint32_t context) {
    uint32_t color;
    uint32_t hud = U32(0x03000010u);
    /* Single-player gameplay only; demos/multiplayer/menu colors stay native. */
    if (U8(0x0203AD3Cu) != 0u || (U32(0x0203AD10u) & 0x12u)) return 0;
    if (U32(0x0203B0B8u) != AP_COLOR_STARTUP
            && (hud < 0x03000000u || hud > 0x03007FECu || (hud & 3u)
                || U32(hud + 8u) != 0x08033B9Du)) return 0;
    color = effective_color();
    if (color < 14u || color >= AP_COLOR_COUNT) return 0;
    return ap_color_palettes[color - 14u][context];
}

/* Replacement for the palette command dispatch entry at ROM 0xD60820.
 * Byte offsets deliberately match the USA Sprite/AnimCmd ABI. */
int32_t ap_color_sprite_palette(const uint8_t *command, uint8_t *sprite) {
    uint16_t *cursor = (uint16_t *)(sprite + 0xEu);
    uint32_t sprite_flags = *(uint32_t *)(sprite + 8u);
    uint16_t anim = *(uint16_t *)(sprite + 0xCu);
    const uint16_t *source;
    uint32_t bank, offset, count, index;
    *cursor += 3u;
    if (sprite_flags & 0x40000u) return 1;
    index = *(uint32_t *)(command + 4u);
    source = *(const uint16_t **)(U32(0x03003674u) + 12u) + 16u * index;
    bank = sprite[0x1Fu];
    if (bank == 0u && sprite[0x1Au] == 0u && (anim == 0x15u || anim == 0x1A0u)
            && *(const uint16_t *)(command + 8u) == 16u
            && *(const uint16_t *)(command + 10u) == 0u) {
        const uint16_t *replacement = curated_palette(anim == 0x1A0u ? 1u : 0u);
        if (replacement) source = replacement;
    }
    offset = bank * 16u + *(const uint16_t *)(command + 10u);
    count = *(const uint16_t *)(command + 8u);
    if (MAIN_FLAGS & 0x20000u) {
        NATIVE_OBJ_TRANSFORM(source, (uint8_t)offset, (uint16_t)count);
    } else {
        volatile uint16_t *dest = (volatile uint16_t *)0x03002C60u + offset;
        for (index = 0; index < count; ++index) dest[index] = source[index];
        MAIN_FLAGS |= 2u;
    }
    return 1;
}

/* Exact raw-copy semantics of sub_0803D21C, including both palette buffers.
 * Only the fallback Pink HUD row for player zero may be replaced. */
void ap_color_load_bg(const uint16_t *source, uint32_t raw_offset, uint32_t raw_count) {
    uint32_t i, offset = raw_offset & 0xFFu, count = raw_count & 0xFFFFu;
    volatile uint16_t *work = (volatile uint16_t *)0x030037A0u + offset;
    volatile uint16_t *backup = (volatile uint16_t *)0x02022120u + offset;
    if (source == (const uint16_t *)0x0834BB20u && offset == 0xF0u && count == 16u) {
        const uint16_t *replacement = curated_palette(2u);
        if (replacement) source = replacement;
    }
    for (i = 0; i < count; ++i) work[i] = source[i];
    for (i = 0; i < count; ++i) backup[i] = source[i];
}
