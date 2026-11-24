#include <assert.h>
#include <stdint.h>
#include <string.h>
#include "chest_reward_art_runtime.h"
#include "reward_art_config.h"
#include "lever_runtime_logic.h"

#define ART 0x09001000u
#define TRAP 0x09001200u
static _Alignas(4) uint8_t native_chest[0xE4];
static struct ApRewardArtConfig config = {AP_REWARD_ART_MAGIC, 0, {0}};
static uint8_t ap_reward_art_for_key(uint32_t key) {
    return ap_reward_art_from_config(&config, key);
}
static uint32_t ap_reward_tiles_for_art(uint8_t art) {
    return art == AP_REWARD_TRAP ? TRAP : ART;
}
static volatile uint8_t head;
static volatile struct ApChestTileUpload ring[64];
static uint8_t commands;
static uint8_t enough_vram = 1u;
static unsigned native_popups;

static uint8_t ap_reward_native_vram_available(void) {
    return enough_vram;
}
static uint16_t parent_reward, visual_reward, transferred_size;
static uint32_t source;

static void native_popup_host(void *chest, int16_t x, int16_t y, uint16_t visual) {
    assert(chest == native_chest);
    assert(x == -8 && y == 46);
    visual_reward = visual;
    ++native_popups;
    if (visual != 0x63u && commands) {
        ring[head].source = source;
        ring[head].destination = 0x06015400u;
        ring[head].size = transferred_size;
        head = (head + commands) & 63;
    }
}

/* WRAPPER */

int main(void) {
    /* Opening real chests, including all ordinary items and no-bonus cases,
     * always queues the same image without changing the original item. */
    const uint16_t cases[] = {0, 1, 2, 3, 4, 5, 6, 0xA, 0x13, 0x14, 0x21, 0x28, 0x29, 0x32, 0x63};
    commands = 1;
    source = AP_CHEST_NATIVE_TILES;
    transferred_size = AP_CHEST_ART_SIZE;
    for (unsigned i = 0; i < sizeof(cases) / sizeof(*cases); i++) {
        head = 63;
        memset((void *)ring, 0, sizeof(ring));
        ring[62].source = AP_CHEST_NATIVE_TILES;
        parent_reward = cases[i];
        ap_chest_reward_art(native_chest, -8, 46, parent_reward);
        assert(visual_reward == 0 && parent_reward == cases[i] && head == 0);
        assert(ring[63].source == ART && ring[62].source == AP_CHEST_NATIVE_TILES);
        assert(ring[63].destination == 0x06015400u && ring[63].size == AP_CHEST_ART_SIZE);
    }
    /* Under VRAM pressure the native timer still starts exactly once for
     * every original parent reward, but native 0x63 queues no sprite tiles. */
    enough_vram = 0u;
    for (unsigned i = 0; i < sizeof(cases) / sizeof(*cases); i++) {
        head = 63;
        unsigned started = native_popups;
        parent_reward = cases[i];
        ap_chest_reward_art(native_chest, -8, 46, parent_reward);
        assert(visual_reward == 0x63 && parent_reward == cases[i]);
        assert(native_popups == started + 1 && head == 63);
    }
    enough_vram = 1u;
    /* Real lever pulls enter the constructor with 0x63 as well. The same
     * visual bytes apply without changing the actual lever reward value. */
    parent_reward = 0x63;
    head = 9;
    ap_chest_reward_art(native_chest, -8, 46, parent_reward);
    assert(visual_reward == 0 && parent_reward == 0x63 && ring[9].source == ART);
    const uint32_t trap_keys[] = {
        AP_REWARD_KEY(AP_REWARD_LEVER, 0u), AP_REWARD_KEY(AP_REWARD_MAP_CHEST, 0u), AP_REWARD_KEY(AP_REWARD_VITALITY_CHEST, 0u),
        AP_REWARD_KEY(AP_REWARD_VITALITY_CHEST, 1u), AP_REWARD_KEY(AP_REWARD_VITALITY_CHEST, 2u),
        AP_REWARD_KEY(AP_REWARD_VITALITY_CHEST, 3u), AP_REWARD_KEY(AP_REWARD_SOUND_CHEST, 0u),
        AP_REWARD_KEY(AP_REWARD_MINOR_CHEST, 0x008B6EB4u),
    };
    const struct {uint16_t reward, room; uint32_t source; uint8_t id;} trapped[] = {
        {0xAu, 30u, 0u, 1u}, {6u, 739u, 0u, 1u}, {6u, 815u, 0u, 1u},
        {6u, 610u, 0u, 1u}, {6u, 403u, 0u, 1u}, {0x28u, 406u, 0u, 1u},
        {0x29u, 30u, 0x088B6EB4u, 1u}, {0x63u, 743u, 0x088BE07Cu, 18u},
    };
    for (unsigned i = 0; i < sizeof(trap_keys) / sizeof(trap_keys[0]); ++i) {
        config.keys[i] = trap_keys[i] | (AP_REWARD_TRAP << AP_REWARD_ART_SHIFT);
    }
    config.count = sizeof(trap_keys) / sizeof(trap_keys[0]);
    for (unsigned i = 0; i < config.count; ++i) {
        *(uint32_t*)(native_chest + 0xB0u) = trapped[i].source;
        *(uint16_t*)(native_chest + 0xE0u) = trapped[i].reward;
        *(uint16_t*)(native_chest + 0x60u) = trapped[i].room;
        native_chest[0xE2u] = trapped[i].id;
        head = 9u;
        ap_chest_reward_art(native_chest, -8, 46, trapped[i].reward);
        assert(ring[9].source == TRAP);
    }
    config.count = AP_REWARD_ART_CAPACITY + 1;
    head = 9u;
    ap_chest_reward_art(native_chest, -8, 46, 0x63u);
    assert(ring[9].source == ART);
    config.count = 0u;
    ring[9].source = AP_CHEST_NATIVE_TILES;
    /* Fail closed on unexpected queue shape, source and size. */
    for (uint8_t n = 0; n <= 2; n += 2) {
        head = 9;
        commands = n;
        ap_chest_reward_art(native_chest, -8, 46, 0xA);
        assert(ring[9].source == AP_CHEST_NATIVE_TILES);
    }
    commands = 1;
    source = 0x08000000u;
    head = 9;
    ap_chest_reward_art(native_chest, -8, 46, 0xA);
    assert(ring[9].source == source);
    source = AP_CHEST_NATIVE_TILES;
    transferred_size = 64;
    head = 9;
    ap_chest_reward_art(native_chest, -8, 46, 0xA);
    assert(ring[9].source == source && ring[9].size == 64);
    return 0;
}
