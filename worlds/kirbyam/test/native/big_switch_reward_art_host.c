#include <assert.h>
#include <stdint.h>

#include "generated_hub_switch_tables.inc"
#include "reward_art_config.h"
#include "receipt_visual_runtime.h"
#include "shard_award_runtime.h"

#define AP_HUB_SAVED_CHECKS ((void *)0)
#define AP_HUB_ROM_AUTH ((void *)0)
static _Alignas(8) uint8_t object[0xC0];
static _Alignas(2) uint8_t fixture_source[0x24];
static uint16_t local_room = 790u;
static uint32_t saves;
static unsigned pops, calls, draws, destroys;
static _Alignas(4) uint8_t fixture_effect[0x4C];
static uint8_t task_identity;
static void *fixture_task = &task_identity;
static uint32_t AP_HUB_SWITCH_FLAGS;
static struct ApReceiptVisualMailbox fake_visuals;
static struct ApChestTileUpload tile_uploads[64];
static uint8_t head, tail;
#define AP_REWARD_UPLOAD_RING tile_uploads
#define AP_REWARD_UPLOAD_HEAD (&head)
#define AP_REWARD_UPLOAD_TAIL tail
#define AP_VISUAL_MAILBOX (&fake_visuals)

static uint8_t *ap_reward_task_data(void *task) {
    assert(task == fixture_task);
    return fixture_effect;
}

static void destroy_task(void *task) {
    assert(task == fixture_task);
    ++destroys;
}

static void draw_effect(void *effect) {
    assert(effect == fixture_effect);
    ++draws;
}

static void ap_drop_invalid_reward_task(void *task) {
    assert(task == fixture_task);
    assert(0 && "valid fixture tasks should use standard cleanup");
}

static uint32_t ap_hub_saved_checks(const void *saved, const void *auth) {
    (void)saved;
    (void)auth;
    return saves;
}

static uint16_t ap_reward_local_room(void) {
    return local_room;
}

static uint8_t ap_reward_art_for_key(uint32_t key) {
    return key == AP_REWARD_KEY(AP_REWARD_SWITCH, 11u) ? AP_REWARD_TRAP : AP_REWARD_GEM;
}

static void ap_show_room_reward_gem(uint16_t room, int32_t x, int32_t y, uint32_t bit, uint8_t art) {
    assert(room == local_room && x == 136 * 256 && y == 98 * 256);
    assert((*(uint16_t*)(object + 0xB6u) & 0x2000u) != 0u);
    assert(bit == (1u << ap_hub_bits[*(uint16_t*)(fixture_source + 0x14u)]));
    assert(art == (bit == (1u << 11u) ? AP_REWARD_TRAP : AP_REWARD_GEM));
    ++pops;
}

static void native_dispatch(void *sw) {
    assert(sw == object);
    ++calls;
    uint16_t *state = (uint16_t*)(object + 0xB6u);
    if (*state & 2u) *state |= 0x2000u; /* Accepted press's real native latch. */
}

/* WRAPPER */
/* FRAME */

static void physical_state(uint16_t state, uint16_t big, uint16_t room, uint16_t door,
                           uint8_t world_prop, uint8_t object_type) {
    *(int32_t*)(object + 0x40u) = 136 * 256;
    *(int32_t*)(object + 0x44u) = 128 * 256;
    *(uint16_t*)(object + 0xB6u) = state;
    *(uint16_t*)(object + 0xB8u) = big;
    *(uint16_t*)(object + 0x60u) = room;
    *(uint16_t*)(fixture_source + 0x14u) = door;
    fixture_source[4] = world_prop;
    fixture_source[12] = object_type;
}

static void expect_increment(unsigned expect) {
    unsigned p = pops, c = calls;
    ap_big_switch_reward_art(object);
    assert(pops == p + expect);
    assert(calls == c + 1u); /* Native behavior is always forwarded exactly once. */
}

int main(void) {
    for (uint16_t door = 1u; door <= 15u; ++door) {
        uint8_t props = ap_hub_props[door];
        physical_state(0u, 1u, 790u, door, props, 0x86u);
        expect_increment(0u); /* Spawn or item receipt, no accepted physical press. */
        physical_state(0x0303u, 1u, 790u, door, props, 0x86u);
        expect_increment(1u);
        expect_increment(0u); /* Held or waiting for the map cutscene. */
        saves = 1u << ap_hub_bits[door];
        physical_state(2u, 1u, 790u, door, props, 0x86u);
        expect_increment(0u); /* Recovered or previously acknowledged row. */
        saves = 0u;
    }
    physical_state(2u, 0u, 790u, 2u, ap_hub_props[2], 0x86u);
    expect_increment(0u); /* Ordinary small switch. */
    physical_state(2u, 1u, 711u, 2u, ap_hub_props[2], 0x86u);
    expect_increment(0u); /* Offscreen/other Kirby's room. */
    physical_state(2u, 1u, 790u, 2u, ap_hub_props[2], 0x8Au);
    expect_increment(0u); /* Other native source using matching door/index. */
    physical_state(2u, 1u, 790u, 2u, 0u, 0x86u);
    expect_increment(0u); /* Unknown AP template. */
    physical_state(2u, 1u, 790u, 0u, 0u, 0x86u);
    expect_increment(0u); /* No map unlock. */
    physical_state(2u, 1u, 790u, 16u, 0u, 0x86u);
    expect_increment(0u); /* Non-AP map transition. */
    uint16_t *age = (uint16_t*)(fixture_effect + 4u);
    int32_t *y = (int32_t*)(fixture_effect + 0x38u);
    uint16_t *effect_room = (uint16_t*)(fixture_effect + 0x42u);
    uint32_t *bit = (uint32_t*)(fixture_effect + 0x48u);
    *effect_room = local_room;
    *bit = 2u;
    AP_HUB_SWITCH_FLAGS = 1u; /* Different checks do not despawn this gem. */
    ap_reward_gem_frame();
    ap_reward_gem_frame();
    assert(*age == 2u && *y == -256 && draws == 2u && destroys == 0u);
    AP_HUB_SWITCH_FLAGS = 3u;
    ap_reward_gem_frame(); /* Native tasks resumed after the save/transition. */
    assert(draws == 2u && destroys == 1u);
    AP_HUB_SWITCH_FLAGS = 0u;
    *effect_room = 711u;
    ap_reward_gem_frame(); /* Nothing follows the camera to another room. */
    assert(draws == 2u && destroys == 2u);
    *effect_room = local_room;
    *age = 32u;
    ap_reward_gem_frame(); /* No persisted check needed for normal expiry. */
    assert(draws == 2u && destroys == 3u);
    return 0;
}
