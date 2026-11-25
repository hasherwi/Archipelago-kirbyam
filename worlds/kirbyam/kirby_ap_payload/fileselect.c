#include <stdint.h>

/* Native ROM 0x0813AD9C draws the three-file selector (and only its own
 * transition frames). Banks 3 and 7 are its unselected row labels/numbers
 * and completion medallions. File 1 keeps the native selected banks. */
#define NATIVE_FILE_SELECT_DRAW ((void (*)(void *))0x0813AD9Du)
#define NATIVE_OBJ_PALETTE ((volatile uint16_t *)0x03002C60u)
#define NATIVE_MAIN_FLAGS (*(volatile uint32_t *)0x03002440u)
#define OBJ_PALETTE_SYNC (1u << 1)

static void ap_file_select_mute_bank(unsigned bank)
{
    unsigned changed = 0;
    for (unsigned i = 1; i < 16; ++i) {
        volatile uint16_t *color = &NATIVE_OBJ_PALETTE[bank * 16 + i];
        uint16_t old = *color;
        unsigned red = old & 31u;
        unsigned green = (old >> 5) & 31u;
        unsigned blue = (old >> 10) & 31u;
        /* Keep neutral colors fixed across frames. Color entries converge in
         * one step, avoiding cumulative dimming and unnecessary DMA. */
        if (red == green && green == blue)
            continue;
        unsigned gray = (red + green * 2 + blue) >> 2;
        gray = (gray + 8) >> 1;
        *color = (uint16_t)(gray | (gray << 5) | (gray << 10));
        changed = 1;
    }
    if (changed)
        NATIVE_MAIN_FLAGS |= OBJ_PALETTE_SYNC;
}

void ap_draw_single_file_selector(void *menu)
{
    ap_file_select_mute_bank(3);
    ap_file_select_mute_bank(7);
    NATIVE_FILE_SELECT_DRAW(menu);
}
