#include <stdint.h>

/* Only new seeds without a guaranteed 9-12 copy source enable this link.
 * The marker is outside the base payload and separate from other seed flags. */
const volatile uint32_t gApCandy912Fuse __attribute__((section(".apcandy912config"))) = 0x43393100u;

typedef void (*BombChainFn)(void *, int16_t, int16_t);
typedef uint8_t (*CollisionFn)(uint8_t, uint16_t, uint16_t);
typedef void *(*TileRecordFn)(uint8_t, uint8_t, uint8_t);
typedef void (*BreakTileFn)(uint8_t, void *, void *, void *);

#define BOMB_CHAIN ((BombChainFn)0x0800E0E5u)
#define COLLISION_TILE ((CollisionFn)0x080023E5u)
#define TILE_RECORD ((TileRecordFn)0x080025ADu)
#define BREAK_TILE ((BreakTileFn)0x08001409u)

enum {
    CANDY_ROOM = 402,
    CHAIN_TRIGGER = 0xF1,
    WEST_X = 7, WEST_Y = 18,
    CHEST_X = 25, CHEST_Y = 25,
};

__attribute__((used)) void ap_candy912_bomb_chain(void *attack, int16_t x, int16_t y) {
    const uint8_t *object = attack;
    uint8_t player;

    /* This exact retail call already broke the attacked tile. Never skip its
     * explosion, even when a second chain is linked to it. */
    BOMB_CHAIN(attack, x, y);
    if (gApCandy912Fuse != 0x43393101u || x != WEST_X || y != WEST_Y
        || *(const uint16_t *)(object + 0x60u) != CANDY_ROOM) {
        return;
    }

    player = object[0x56u];  /* Attack's resident level index, not its owner. */
    if (player < 4u && COLLISION_TILE(player, CHEST_X, CHEST_Y) == CHAIN_TRIGGER) {
        /* Trigger only the original 9-12 fuse, even if this room is shared by
         * Kirbys. The live tile guards repeat hits/re-entry within this load. */
        BREAK_TILE(player, TILE_RECORD(player, CHEST_X, CHEST_Y), 0, 0);
        BOMB_CHAIN(attack, CHEST_X, CHEST_Y);
    }
}
