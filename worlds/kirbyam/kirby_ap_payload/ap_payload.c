#include <stdint.h>

#include "hub_connection_runtime_logic.h"
#include "hub_save_logic.h"
#include "copy_room.h"
AP_COPY_EXT void ap_goal_poll(void);
#include "phone.h"
#include "battery.h"
#include "statue_runtime_logic.h"
#include "statue_art_runtime.h"
#include "statue_logo.h"

#define AP_STATUE_FX __attribute__((noinline, long_call, section(".apstatuefx")))
#define AP_STATUE_UPLOAD_HEAD ((volatile uint8_t*)0x030039A4u)
#define AP_STATUE_UPLOAD_TAIL (*(volatile uint8_t*)0x03006078u)
#define AP_STATUE_UPLOAD_RING ((volatile struct ApStatueTileUpload*)0x03002EC0u)

__attribute__((used, section(".apstatueconfig")))
const volatile struct ApStatueConfig gApWorldStatueConfig = {.magic = "APST01"};

AP_STATUE_FX uint8_t ap_world_statue_mode(uint16_t room) {
    return ap_statue_world_mode(room, &gApWorldStatueConfig);
}

static AP_STATUE_FX uint8_t ap_world_statue_visual(const uint8_t *sprite) {
    const uint8_t *obj = sprite - 0x10u;
    if (obj[0] != 1u || *(const volatile uint16_t*)(sprite + 0xCu) != AP_STATUE_NATIVE_ANIM
        || !ap_statue_vram_address_is_valid(*(const volatile uint32_t*)sprite)) return 0u;
    return ap_statue_world_art(*(const volatile uint16_t*)(obj + 0x60u), obj[0x82u],
        sprite[0x1Au], &gApWorldStatueConfig);
}

static inline uint32_t ap_custom_statue_tiles(uint8_t index) {
    const volatile uint32_t *header = (const volatile uint32_t*)AP_STATUE_CUSTOM_ROM_ADDRESS;
    if (header[0] != AP_STATUE_CUSTOM_MARKER_FIRST || header[1] != AP_STATUE_CUSTOM_MARKER_LAST) return 0u;
    return ap_statue_custom_address(index);
}

/* Statue scripts share one static native frame and 16x16 footprint. Reuse
 * the native object's existing allocation, DMA, animation and draw order. */
static AP_STATUE_FX uint32_t ap_world_statue_tiles(uint8_t art) {
    static const uint8_t mapping[32] __attribute__((section(".apstatuefx_data"))) = {
        [7] = 1, [3] = 2, [13] = 3, [1] = 4, [8] = 5, [20] = 6, [9] = 7, [16] = 8,
        [4] = 9, [2] = 10, [15] = 11, [25] = 12, [22] = 13, [10] = 14, [17] = 15,
        [18] = 16, [6] = 17, [19] = 18, [5] = 19,
    };
    static const uint8_t custom[32] __attribute__((section(".apstatuefx_data"))) = {
        [11] = 1u, [12] = 2u, [14] = 3u, [21] = 4u, [23] = 5u, [24] = 6u,
    };
    if (art < 32u && mapping[art]) {
        return 0x0900E388u + (mapping[art] - 1u) * AP_STATUE_ART_SIZE;
    }
    uint8_t index = art == AP_STATUE_QUESTION ? 6u
        : art < 32u && custom[art] ? (uint8_t)(custom[art] - 1u) : AP_STATUE_CUSTOM_FRAME_COUNT;
    uint32_t tiles = ap_custom_statue_tiles(index);
    return tiles ? tiles : (uint32_t)(uintptr_t)gApWorldStatueLogo;
}

static AP_STATUE_FX void ap_world_statue_redirect(const uint8_t *sprite, uint8_t before) {
    uint8_t art = ap_world_statue_visual(sprite);
    if (!art) return;
    ap_statue_replace_upload(AP_STATUE_UPLOAD_RING, before, *AP_STATUE_UPLOAD_HEAD,
        *(const volatile uint32_t*)sprite, sprite[0x1Au], ap_world_statue_tiles(art));
}

AP_STATUE_FX __attribute__((used)) void ap_init_world_statue_sprite(void *obj) {
    uint8_t before = *AP_STATUE_UPLOAD_HEAD;
    ((void (*)(void*))0x0809F3E1u)(obj); /* ObjectInitSprite */
    ap_world_statue_redirect((const uint8_t*)obj + 0x10u, before);
}

AP_STATUE_FX __attribute__((used)) void ap_init_world_statue_grant(void *obj) {
    ((void (*)(void*))0x080AA4EDu)(obj); /* Native statue setup including callback. */
    uint8_t *object = obj;
    uint8_t ability = ap_statue_world_ability(*(const volatile uint16_t*)(object + 0x60u),
        object[0x82u], object[0x83u], &gApWorldStatueConfig);
    if (ability) object[0x84u] = ability;
}

AP_STATUE_FX __attribute__((used)) void ap_reload_world_statue_sprite(void *obj) {
    uint8_t before = *AP_STATUE_UPLOAD_HEAD;
    ((void (*)(void*))0x0809A631u)(obj); /* Native object residency reload. */
    ap_world_statue_redirect((const uint8_t*)obj + 0x10u, before);
}

static AP_STATUE_FX void ap_draw_world_statue_sprite(void *sprite) {
    void (*native)(void*) = (void (*)(void*))0x0815604Du;
    uint8_t *data = sprite;
    uint8_t art = ap_world_statue_visual(data);
    if (!art) {
        native(sprite);
        return;
    }
    uint32_t destination = *(const volatile uint32_t*)data;
    uint32_t tiles = ap_world_statue_tiles(art);
    if (!ap_statue_tiles_confirmed(AP_STATUE_UPLOAD_RING, *AP_STATUE_UPLOAD_HEAD,
            AP_STATUE_UPLOAD_TAIL, destination, tiles, (const volatile uint32_t*)(uintptr_t)destination,
            (const volatile uint32_t*)(uintptr_t)tiles)) {
        native(sprite);
        return;
    }
    uint8_t palette = data[0x1Fu];
    volatile uint32_t *flags = (volatile uint32_t*)(data + 8u);
    uint32_t original_flags = 0u;
    uint8_t plain_question = art == AP_STATUE_QUESTION && tiles == ap_statue_custom_address(6u);
    /* The question mark is a symbol, not a character sprite. Suppress the
     * native statue's mirrored orientation only while drawing this frame. */
    if (plain_question) {
        original_flags = *flags;
        *flags = ap_statue_question_draw_flags(original_flags);
    }
    /* Keep the native palette handle for ObjectDestroy; do not write a palette. */
    data[0x1Fu] = 15u;
    native(sprite);
    data[0x1Fu] = palette;
    if (plain_question) *flags = ap_statue_restore_draw_hflip(*flags, original_flags);
}


#include "transition_runtime_logic.h"
#include "transition_route_logic.h"
#include "enemy_runtime_logic.h"
#include "candy_runtime_logic.h"
#include "minor_chest_runtime_logic.h"
#include "lever_runtime_logic.h"
#include "vitality_runtime_logic.h"
#include "color_runtime_logic.h"
#include "goal_game_runtime_logic.h"
#include "receipt_sound_runtime.h"
#include "receipt_visual_runtime.h"
#include "chest_reward_art_runtime.h"
#include "boss_shard_art_runtime.h"
#include "shard_award_runtime.h"
#include "chest_reward_art.h"
#include "trap_reward_art.h"
#include "reward_art.h"
#include "visit_reward_art_runtime.h"
#include "random_teleport_runtime_logic.h"

__attribute__((used, section(".apcueinfo")))
const uint8_t gApReceiptCueInfo[8] = {'A','P','C','U','E','0','1',0};

_Static_assert(AP_GOAL_RUN_ADDRESS + sizeof(struct ApGoalRun) <= AP_CUE_MAILBOX_ADDRESS,
               "Receipt cue mailbox overlaps Goal Game runtime state");
#define AP_CUE_REQUEST (*(volatile uint32_t *)(AP_CUE_MAILBOX_ADDRESS))
#define AP_CUE_RESULT (*(volatile uint32_t *)(AP_CUE_MAILBOX_ADDRESS + 4u))
#define AP_CUE_READY (*(volatile uint32_t *)(AP_CUE_MAILBOX_ADDRESS + 8u))
#define AP_CUE_ACTIVE (*(volatile uint32_t *)(AP_CUE_MAILBOX_ADDRESS + 12u))
#define AP_VISUAL_MAILBOX ((volatile struct ApReceiptVisualMailbox *)AP_VISUAL_MAILBOX_ADDRESS)
__attribute__((used, section(".apvisualinfo")))
const char gApReceiptVisualInfo[8] = "APVIS05";


// Kirby AP item ID base offset
#define KIRBY_ITEM_ID_BASE_OFFSET       3860000u  // must match worlds/kirbyam/data.py BASE_OFFSET

// AP Mailbox Registers
#define AP_BASE                 0x0203B000u
#define AP_IN_FLAG              (*(volatile uint32_t*)(AP_BASE + 0x04u))
#define AP_IN_ITEM_ID           (*(volatile uint32_t*)(AP_BASE + 0x08u))
#define AP_IN_PLAYER            (*(volatile uint32_t*)(AP_BASE + 0x0Cu))
#define AP_ITEM_RCVD_COUNTER    (*(volatile uint32_t*)(AP_BASE + 0x10u))
#define AP_DEBUG_LAST_ITEM_ID   (*(volatile uint32_t*)(AP_BASE + 0x14u))
#define AP_DEBUG_LAST_FROM      (*(volatile uint32_t*)(AP_BASE + 0x18u))

// Monotonic counter incremented every AP hook call (typically once per frame).
#define AP_FRAME_COUNTER        (*(volatile uint32_t*)(AP_BASE + 0x1Cu))
#define AP_HOOK_HEARTBEAT       (*(volatile uint32_t*)(AP_BASE + 0x34u))

// Shard State Registers
#define AP_SHARD_BITFIELD       (*(volatile uint32_t*)(AP_BASE + 0x00u))
// Issue #478: AP shard authority register.
// Bits are set by ap_apply_item() shard delivery; never by boss-defeat hook.
// ap_poll_mailbox_c() may initialize/seed this from native save state when
// mailbox init cookie is absent, then uses this authority when scrubbing
// non-AP-owned temporary boss shard bits after gameplay resumes.
#define AP_DELIVERED_SHARD_BITFIELD  (*(volatile uint32_t*)(AP_BASE + 0x38u))
// Issue #478: Frames remaining before the shard scrub is allowed to run.
// Set to SHARD_BOSS_CUTSCENE_FRAMES by the boss-defeat hook so the
// post-cutscene state machine has time to observe the temporary native write
// before gameplay-resume scrub eligibility is reached.
#define AP_SHARD_SCRUB_DELAY         (*(volatile uint32_t*)(AP_BASE + 0x3Cu))
#define SHARD_BOSS_CUTSCENE_FRAMES   600u  // ~10 s at 60 fps; covers post-boss shard cutscene
// Mailbox initialization cookie to protect against stale EWRAM on cold/soft reset.
#define AP_MAILBOX_INIT_COOKIE       (*(volatile uint32_t*)(AP_BASE + 0x40u))
#define AP_MAILBOX_INIT_COOKIE_VALUE 0x4B41504Du  // "KAPM"
// Tracks shard bits temporarily written by boss defeat hook for cutscene safety.
// Cleared after gameplay resumes and non-AP-owned bits are scrubbed.
#define AP_BOSS_TEMP_SHARD_BITFIELD  (*(volatile uint32_t*)(AP_BASE + 0x44u))
// Bitfield for AP vitality item replay-guard semantics.
// Low bits 0..3 are unique Vitality identities. Client-owned bit 31 marks
// a delivery cursor whose server history includes the starting-inventory prefix.
#define AP_DELIVERED_VITALITY_ITEM_BITS (*(volatile uint32_t*)(AP_BASE + 0x48u))
// Runtime config for enemy copy-ability randomization live reroll hook.
#define AP_ABILITY_RANDOMIZATION_MODE   (*(volatile uint32_t*)(AP_BASE + 0x64u))
#define AP_ABILITY_RANDOMIZATION_SEED_LO (*(volatile uint32_t*)(AP_BASE + 0x68u))
#define AP_ABILITY_RANDOMIZATION_SEED_HI (*(volatile uint32_t*)(AP_BASE + 0x6Cu))
#define AP_ABILITY_RANDOMIZATION_NO_ABILITY_WEIGHT (*(volatile uint32_t*)(AP_BASE + 0x70u))
#define AP_ABILITY_RANDOMIZATION_ALLOWED_MASK (*(volatile uint32_t*)(AP_BASE + 0x74u))
#define AP_ABILITY_RANDOMIZATION_RNG_STATE (*(volatile uint32_t*)(AP_BASE + 0x78u))
#define AP_ABILITY_REROLL_EVENT_COUNTER (*(volatile uint32_t*)(AP_BASE + 0x7Cu))
#define AP_ABILITY_REROLL_SOURCE_ADDR (*(volatile uint32_t*)(AP_BASE + 0x80u))
#define AP_ABILITY_REROLL_ABILITY_ID (*(volatile uint32_t*)(AP_BASE + 0x84u))
#define AP_ABILITY_REROLL_SOURCE_KIND (*(volatile uint32_t*)(AP_BASE + 0x5Cu))
#define AP_ABILITY_REROLL_CALLSITE_PC (*(volatile uint32_t*)(AP_BASE + 0x60u))
#define AP_ABILITY_REROLL_KIRBY_INDEX (*(volatile uint32_t*)(AP_BASE + 0x88u))
#define AP_MINOR_CHEST_EVENT_COUNTER (*(volatile uint32_t*)(AP_BASE + 0x8Cu))
#define AP_MINOR_CHEST_EVENT_RING_BASE (AP_BASE + 0x90u)
#define AP_ABILITY_GATE_MASK (*(volatile uint32_t*)(AP_BASE + 0xB0u))
#define AP_ABILITY_UNLOCK_MASK (*(volatile uint32_t*)(AP_BASE + 0xB4u))
/*
 * Issue #852 runtime latch. Payload code executes from ROM, so mutable state
 * must live in EWRAM rather than a C static/.bss object linked into the payload.
 */
#define AP_STARTING_KIRBY_COLOR_APPLIED (*(volatile uint32_t*)(AP_BASE + 0xB8u))
/* Physical lever activations, separated from native wall-unlock state (Issue #859). */
#define AP_LEVER_ACTIVATION_FLAGS (*(volatile uint32_t*)(AP_BASE + 0xBCu))
/* Client-canonical Area Key ownership. Bits 2..9 map to AP areas 2..9. */
#define AP_AREA_KEY_BITFIELD_RUNTIME (*(volatile uint32_t*)(AP_BASE + 0xC0u))
#define AP_TRANSITION_EVENT_COUNTER (*(volatile uint32_t*)(AP_BASE + 0xC4u))
#define AP_TRANSITION_EVENT_RING_BASE (AP_BASE + 0xC8u)
#define AP_TRANSITION_EVENT_RING_SLOTS 8u
#define AP_TRANSITION_EVENT_LAST_SIGNATURE (*(volatile uint32_t*)(AP_BASE + 0x128u))
#define AP_TRANSITION_EVENT_LAST_FRAME (*(volatile uint32_t*)(AP_BASE + 0x12Cu))
#define AP_TRANSITION_EVENT_TELEMETRY_COOKIE (*(volatile uint32_t*)(AP_BASE + 0x130u))
#define AP_TRANSITION_EVENT_TELEMETRY_COOKIE_VALUE 0x54524E31u /* "TRN1" */
/* Client-owned hub connection items, indexed by native WorldMapDoor (1..15) plus starting mirror (16). */
#define AP_HUB_CONNECTION_ITEM_MASK (*(volatile uint32_t*)(AP_BASE + 0x134u))
#define AP_STARTING_MIRROR_ITEM_MASK (1u << 16)
#define AP_HUB_CONNECTION_ITEM_MASK_UNINITIALIZED 0xFFFFFFFFu
/* Scratch world-props entry so AP-owned doors do not hide uncollected switches. */
#define AP_HUB_SWITCH_INIT_STATE (*(volatile uint32_t*)(AP_BASE + 0x138u))
#define AP_MINOR_CHEST_EVENT_RING_SLOT_COUNT 8u
#define AP_MINOR_CHEST_ITEM_SUPPRESSION_MARKER 0x41504348u  // "APCH"
#define KIRBY_MINOR_CHEST_NO_NATIVE_ITEM 0x63u

/* Exact AP-owned chest sources from data/locations.json, stored as GBA bus pointers. */
static const uint32_t AP_OWNED_MINOR_CHEST_SOURCE_PTRS[] = {
    0x088B5FA8u, 0x088B6510u, 0x088B6EB4u, 0x088B7288u,
    0x088B9280u, 0x088B9FD8u, 0x088BA7A4u, 0x088BAEE0u,
    0x088BB0BCu, 0x088BBAF8u, 0x088BC018u, 0x088BC114u,
    0x088BC4A0u, 0x088BD1B0u, 0x088BDD10u, 0x088BE5E0u,
    0x088BE724u, 0x088BEF84u, 0x088BF3C8u, 0x088BF3ECu,
    0x088BF610u, 0x088BFD78u, 0x088C026Cu, 0x088C0290u,
    0x088C02B4u, 0x088C046Cu, 0x088C04D8u, 0x088C0648u,
    0x088C06B4u, 0x088C06D8u, 0x088C0E38u, 0x088C1380u,
    0x088C1ADCu, 0x088C21ACu, 0x088C4798u, 0x088C4DFCu,
    0x088C4F24u, 0x088C54B0u, 0x088C5BA4u, 0x088C5EA0u, 0x088C78F8u,
    0x088C86B8u, 0x088C876Cu, 0x088C8AACu, 0x088C9114u,
    0x088C9478u, 0x088C96E8u, 0x088C9FFCu, 0x088CA0B8u,
    0x088CA520u, 0x088CAF08u, 0x088CBDACu, 0x088CC458u,
    0x088CCEFCu, 0x088CD2F4u, 0x088CD464u, 0x088D02C0u,
    0x088D039Cu, 0x088D03E4u, 0x088D2234u, 0x088D230Cu,
    0x088D39FCu, 0x088D3DD0u, 0x088D3E64u, 0x088D3E88u,
};
// Boss Defeat Transport Register (Issue #35: Boss-defeat locations with shard-delivery decoupling)
// Written by ROM payload when an area boss is defeated; polled by Python client for location checks.
// Bit N set <=> boss of area N was defeated (same bit ordering as shard_bitfield, bits 0-7 used).
// Hook site: BL CollectShard inside sub_0801D948 (ROM addr 0x0801D948, callsite file offset 0x001D952).
#define AP_BOSS_DEFEAT_FLAGS    (*(volatile uint32_t*)(AP_BASE + 0x24u))
#define AP_MAJOR_CHEST_FLAGS    (*(volatile uint32_t*)(AP_BASE + 0x28u))
#define AP_VITALITY_CHEST_FLAGS (*(volatile uint32_t*)(AP_BASE + 0x2Cu))
#define AP_SOUND_PLAYER_CHEST_FLAGS (*(volatile uint32_t*)(AP_BASE + 0x30u))
#define AP_HUB_SWITCH_FLAGS (*(volatile uint32_t*)(AP_BASE + 0x4Cu))
#define AP_STARTING_KIRBY_COLOR_ID (*(volatile uint32_t*)(AP_BASE + 0x50u))
// Challenge-mode runtime config. Written by Python client on connect/reconnect.
// 0xFFFFFFFF means client has not synced yet (treat as off/0).
#define AP_ONE_HIT_MODE_RUNTIME    (*(volatile uint32_t*)(AP_BASE + 0x54u))
#define AP_NO_EXTRA_LIVES_RUNTIME  (*(volatile uint32_t*)(AP_BASE + 0x58u))
#define KIRBY_SHARD_FLAGS_ADDR  0x02038970u
#define KIRBY_SHARD_FLAGS       (*(volatile uint8_t*)(KIRBY_SHARD_FLAGS_ADDR))
/* Native player-one color state identified from the KATAM decomp. */
#define KIRBY_PLAYER_COUNT 4u
#define KIRBY_STARTING_COLOR_PLAYER 0u
#define KIRBY_PLAYER_COLOR_TABLE_ADDR 0x0203AD1Cu
#define KIRBY_PLAYER_COLOR_TABLE ((volatile uint8_t*)KIRBY_PLAYER_COLOR_TABLE_ADDR)
/* gUnk_0203ADE0 is an s16 selected-color value, not an active 8-bit palette. */
#define KIRBY_SELECTED_COLOR_ADDR 0x0203ADE0u
#define KIRBY_SELECTED_COLOR (*(volatile int16_t*)KIRBY_SELECTED_COLOR_ADDR)
#define AI_KIRBY_STATE_ADDR     0x0203AD2Cu
#define AI_KIRBY_STATE          (*(volatile uint32_t*)(AI_KIRBY_STATE_ADDR))
#define DEMO_PLAYBACK_FLAGS_ADDR 0x0203AD10u
#define DEMO_PLAYBACK_FLAGS     (*(volatile uint32_t*)(DEMO_PLAYBACK_FLAGS_ADDR))
#define DEMO_PLAYBACK_ACTIVE_FLAG 0x10u
#define AI_STATE_NORMAL         300u
#define AI_STATE_DARK_MIND_CLEAR 9999u
#define AI_STATE_FULL_CLEAR     10000u
#define KIRBY_SMALL_CHEST_FLAGS_ADDR 0x02038960u
#define KIRBY_SPRAY_PAINT_FLAGS (*(volatile uint32_t*)0x02038974u)
#define KIRBY_MUSIC_PLAYER_AND_SHEETS_FLAGS (*(volatile uint32_t*)0x02038978u)
#define KIRBY_BIG_CHEST_FLAGS_ADDR 0x0203897Cu
#define KIRBY_BIG_CHEST_FLAGS   (*(volatile uint32_t*)(KIRBY_BIG_CHEST_FLAGS_ADDR))
#define KIRBY_VITALITY_COUNTER_ADDR 0x02038980u
#define KIRBY_VITALITY_COUNTER  (*(volatile uint16_t*)(KIRBY_VITALITY_COUNTER_ADDR))
// Format 2 has nine distinct AP vitality counter identities.
// Clamp native vitality state to that count so mailbox replay/reset paths
// cannot over-grant vitality above intended progression.
#define KIRBY_MAX_VITALITY_COUNTERS 9u

#define KIRBY_STRUCTS_ADDR       0x02020EE0u
#define KIRBY_NUM_KIRBYS_ADDR    0x0203AD44u
#define KIRBY_NUM_HUMAN_PLAYERS_ADDR 0x0203AD30u
#define KIRBY_CURRENT_PLAYER_ADDR 0x0203AD3Cu
#define KIRBY_CURRENT_PLAYER     (*(volatile uint8_t*)(KIRBY_CURRENT_PLAYER_ADDR))
#define KIRBY_STRUCT_STRIDE      0x1A8u
#define KIRBY_STRUCT_FLAGS2_OFFSET 0x0Cu
#define KIRBY_STRUCT_X_OFFSET    0x40u
#define KIRBY_STRUCT_Y_OFFSET    0x44u
#define KIRBY_STRUCT_PLAYER_OFFSET 0x56u
#define KIRBY_STRUCT_COLLISION_OFFSET 0x58u
#define KIRBY_STRUCT_ROOM_OFFSET 0x60u
#define KIRBY_STRUCT_TRANSITION_KIND_OFFSET 0x62u
#define KIRBY_STRUCT_MOVEMENT_STATE_OFFSET 0x118u
#define KIRBY_STRUCT_CONTACT_OBJECT_OFFSET 0x6Cu
#define KIRBY_STRUCT_TASK_OFFSET 0xCCu
#define KIRBY_STRUCT_BATTERY_OFFSET 0xDCu
#define KIRBY_STRUCT_COLOR_OFFSET 0xDFu
#define KIRBY_STRUCT_ABILITY_OFFSET 0x103u
// Reverse-engineered timed-effect fields used by BonusGiveInvincibility in the
// KatAM decomp (`bonus.c`): clear the effect-reset byte, set the invincibility
// kind byte to 100, mark the state byte active, and store a 1000-tick duration.
#define KIRBY_STRUCT_INVINCIBILITY_RESET_OFFSET 0xE1u
#define KIRBY_STRUCT_INVINCIBILITY_DURATION_OFFSET 0xE2u
#define KIRBY_STRUCT_INVINCIBILITY_KIND_OFFSET 0xE4u
#define KIRBY_STRUCT_INVINCIBILITY_STATE_OFFSET 0xE5u
#define KIRBY_STRUCT_HP_OFFSET   0x100u
#define KIRBY_STRUCT_MAX_HP_OFFSET 0x101u
#define KIRBY_INVINCIBILITY_KIND 100u
#define KIRBY_INVINCIBILITY_DURATION 1000u
#define KIRBY_EFFECT_ACTIVE_COUNTDOWN 0xFFu

// Player lives is a single byte in EWRAM
#define KIRBY_LIVES_ADDR        0x02020FE2u
#define KIRBY_LIVES             (*(volatile uint8_t*)(KIRBY_LIVES_ADDR))

/* Save records are owned by the native serializer. Do not write guessed SRAM
 * shard/checksum offsets: those overlap FILE_INFO and WORLD_PROPS headers.
 * Shard changes below affect gTreasures in EWRAM; normal game save flow persists
 * them. Reset before that save requires AP history replay, not raw SRAM edits. */

// Archipelago info structure (not used in this payload)
__attribute__((section(".apinfo")))
const unsigned char gArchipelagoInfo[16] = {0};

/*
 * Per-seed runtime defaults written by rom.py after the shared base patch is
 * applied. The linker fixes these words at the final twenty-four bytes of the
 * payload window. The initial gate mask protects startup/reset windows before
 * the client has synchronized live mailbox state; the statue mask carries the
 * exact seed-specific pool for per-touch randomization.
 */
/* Immutable seed contract: AK, version 1, enable bit. Only exact v1-off
 * disables gates; unwritten/legacy/corrupt words retain the default-on policy. */
#define AP_AREA_KEYS_CONFIG_OFF 0x414B0100u
#define AP_AREA_KEYS_CONFIG_ON 0x414B0101u
#define AP_STARTING_MIRROR_CONFIG_BIT 2u
#define AP_RAINBOW_ROUTE_KEY_CONFIG_BIT 4u
#define AP_RAINBOW_ROUTE_KEY_ITEM 3860056u
#define AP_RAINBOW_ROUTE_KEY_BIT (1u << 1)
__attribute__((used, section(".apconfig.area_keys")))
volatile const uint32_t gApAreaKeysConfig = AP_AREA_KEYS_CONFIG_ON;

static inline uint8_t ap_random_starting_mirror_enabled(void) {
    return (gApAreaKeysConfig & AP_STARTING_MIRROR_CONFIG_BIT) != 0u;
}

static inline uint8_t ap_is_starting_mirror(uint16_t source, uint16_t destination) {
    return ap_random_starting_mirror_enabled() && source == 801u && destination == 101u;
}

static inline uint8_t ap_area_keys_enabled(void) {
    return (uint8_t)((gApAreaKeysConfig & ~(AP_STARTING_MIRROR_CONFIG_BIT
        | AP_RAINBOW_ROUTE_KEY_CONFIG_BIT)) != AP_AREA_KEYS_CONFIG_OFF);
}

static __attribute__((noinline, long_call, section(".aphub"))) uint8_t ap_rainbow_route_gate_enabled(void) {
    /* Older seed configurations keep the historical unlocked return. */
    return gApAreaKeysConfig == (AP_AREA_KEYS_CONFIG_ON | AP_RAINBOW_ROUTE_KEY_CONFIG_BIT)
        || gApAreaKeysConfig == (AP_AREA_KEYS_CONFIG_ON | AP_STARTING_MIRROR_CONFIG_BIT
                                | AP_RAINBOW_ROUTE_KEY_CONFIG_BIT);
}

/* Per-seed Minny inclusion, defaulting to the safe vanilla exception. */
__attribute__((used, section(".apconfig.minny")))
volatile const uint32_t gApRandomizeMinny = 0u;

/*
 * Versioned starting-color/mode configuration (see color_runtime_logic.h).
 * Legacy concrete IDs remain static; the unwritten 0xFFFFFFFF defaults to Pink.
 */
__attribute__((used, section(".apconfig.color")))
volatile const uint32_t gApStartingKirbyColorInitial = 0xFFFFFFFFu;

__attribute__((used, section(".apconfig.gate")))
volatile const uint32_t gApAbilityGateMaskInitial = 0u;

/*
 * Per-seed statue-specific ability mask at ROM address 0x0815F69C
 * (file offset 0x0015F69C), so each generated world can carry its exact statue
 * pool without rebuilding the shared payload.  Zero disables live statue
 * rerolls.  Nonzero masks already incorporate the statue toggle, selected
 * randomization mode, custom whitelist, and Minny option.  Volatile prevents
 * the compiler from constant-folding the default zero value.
 */
__attribute__((used, section(".apconfig.statue")))
volatile const uint32_t gApAbilityRandomizationStatueAllowedMask = 0u;


// Issue #35: Set the boss-defeat flag for <boss_index> (0â€“7) in the transport register.
// This function is the intended hook target for sub_0801D948 (ROM address 0x0801D948):
//   intercept the CollectShard(var->unk218) call site, call this instead, and let AP
//   item delivery (SHARD_N) grant the actual shard progression.
static void ap_set_boss_defeat_flag(uint32_t boss_index) {
    if (boss_index < 8u) {
        AP_BOSS_DEFEAT_FLAGS |= (1u << boss_index);
    }
}

static void ap_set_major_chest_flag(uint32_t area_id) {
    if (area_id < 32u) {
        AP_MAJOR_CHEST_FLAGS |= (1u << area_id);
    }
}

static void ap_set_vitality_chest_flag(uint32_t chest_index) {
    if (chest_index < 32u) {
        AP_VITALITY_CHEST_FLAGS |= (1u << chest_index);
    }
}

static void ap_set_sound_player_chest_flag(uint32_t chest_index) {
    if (chest_index < 32u) {
        AP_SOUND_PLAYER_CHEST_FLAGS |= (1u << chest_index);
    }
}

static void ap_record_minor_chest_source_ptr(uint32_t source_ptr) {
    uint32_t event_counter = AP_MINOR_CHEST_EVENT_COUNTER;
    uint32_t slot_offset = (event_counter & (AP_MINOR_CHEST_EVENT_RING_SLOT_COUNT - 1u)) << 2;
    *(volatile uint32_t*)(AP_MINOR_CHEST_EVENT_RING_BASE + slot_offset) = source_ptr;
    AP_MINOR_CHEST_EVENT_COUNTER = event_counter + 1u;
}

static uint8_t ap_is_ap_owned_minor_chest_source(uint32_t source_ptr) {
    uint32_t i;
    uint32_t source_count = (uint32_t)(
        sizeof(AP_OWNED_MINOR_CHEST_SOURCE_PTRS) / sizeof(AP_OWNED_MINOR_CHEST_SOURCE_PTRS[0])
    );
    for (i = 0u; i < source_count; i++) {
        if (source_ptr == AP_OWNED_MINOR_CHEST_SOURCE_PTRS[i]) {
            return 1u;
        }
    }
    return 0u;
}

static void ap_collect_small_chest_native(uint32_t chest_index) {
    if (chest_index >= 128u) {
        return;
    }

    *(volatile uint8_t*)(KIRBY_SMALL_CHEST_FLAGS_ADDR + (chest_index >> 3)) |=
        (uint8_t)(1u << (chest_index & 7u));
}

static __attribute__((noinline, long_call, section(".aphub")))
uint32_t ap_lever_bit_for_obj(uint32_t chest_obj_ptr) {
    return ap_lever_bit_for_chest(
        *(volatile uint32_t*)(chest_obj_ptr + 0xB0u),
        *(volatile uint16_t*)(chest_obj_ptr + 0xE0u),
        *(volatile uint8_t*)(chest_obj_ptr + 0xE2u)
    );
}

static __attribute__((noinline, long_call, section(".aprewardfx")))
uint8_t ap_reward_native_vram_available(void) {
    return ap_reward_native_vram_can_fit((const volatile uint16_t*)0x030064B0u,
        *(const volatile uint16_t*)0x03002488u, *(const volatile uint32_t*)0x03002540u);
}

__attribute__((used, section(".aprewardconfig")))
const volatile struct ApRewardArtConfig gApRewardArtConfig = {.marker = AP_REWARD_ART_MAGIC};

static inline uint8_t ap_collectible_palette_tiles_available(void) {
    const volatile uint32_t *header = (const volatile uint32_t*)AP_COLLECTIBLE_ART_ROM_ADDRESS;
    return header[0] == AP_COLLECTIBLE_ART_MARKER_FIRST && header[1] == AP_COLLECTIBLE_ART_MARKER_LAST;
}

AP_REWARD_FX uint8_t ap_reward_art_for_key(uint32_t key) {
    return ap_reward_art_from_config(&gApRewardArtConfig, key);
}

/* Native chest animation 0x2D1 uses this shared sequence of 16x16,
 * bank-F graphics. The clean-ROM patcher validates all seven scripts. */
static AP_REWARD_FX uint32_t ap_reward_tiles_for_art(uint8_t art) {
    switch (art) {
        case AP_REWARD_TRAP: return (uint32_t)(uintptr_t)gApTrapRewardArt;
        case AP_REWARD_ONE_UP: return AP_CHEST_NATIVE_TILES + 0u * AP_CHEST_ART_SIZE;
        case AP_REWARD_FOOD: return AP_CHEST_NATIVE_TILES + 4u * AP_CHEST_ART_SIZE;
        case AP_REWARD_DRINK: return AP_CHEST_NATIVE_TILES + 2u * AP_CHEST_ART_SIZE;
        case AP_REWARD_MEAT: return AP_CHEST_NATIVE_TILES + 5u * AP_CHEST_ART_SIZE;
        case AP_REWARD_TOMATO: return AP_CHEST_NATIVE_TILES + 3u * AP_CHEST_ART_SIZE;
        case AP_REWARD_CANDY: return AP_CHEST_NATIVE_TILES + 1u * AP_CHEST_ART_SIZE;
        case AP_REWARD_BATTERY: return AP_CHEST_NATIVE_TILES + 6u * AP_CHEST_ART_SIZE;
        case AP_REWARD_VITALITY: return AP_CHEST_NATIVE_TILES + 12u * AP_CHEST_ART_SIZE;
        case AP_REWARD_SOUND_PLAYER: return AP_CHEST_NATIVE_TILES + 13u * AP_CHEST_ART_SIZE;
        default:
            if (art >= AP_REWARD_AREA_KEY_FIRST && art <= AP_REWARD_AREA_KEY_LAST) {
                const volatile uint32_t *keys = (const volatile uint32_t*)AP_AREA_KEY_ART_ROM_ADDRESS;
                uint8_t index = art - AP_REWARD_AREA_KEY_FIRST;
                if (keys[0] == AP_AREA_KEY_ART_MARKER_FIRST && keys[1] == AP_AREA_KEY_ART_MARKER_LAST
                    && (keys[2] & (1u << index))) {
                    return AP_AREA_KEY_ART_ROM_ADDRESS + 12u + index * AP_CHEST_ART_SIZE;
                }
                return (uint32_t)(uintptr_t)gApChestRewardArt;
            }
            if (art >= AP_REWARD_CUSTOM_STATUE_FIRST && art <= AP_REWARD_CUSTOM_STATUE_LAST) {
                uint32_t tiles = ap_custom_statue_tiles(art - AP_REWARD_CUSTOM_STATUE_FIRST);
                if (tiles) return tiles;
            }
            if (art >= AP_REWARD_MAP_FIRST && art <= AP_REWARD_STATUE_LAST
                && ap_collectible_palette_tiles_available()) {
                return AP_COLLECTIBLE_ART_ROM_ADDRESS + 8u
                    + (art - AP_REWARD_MAP_FIRST) * AP_CHEST_ART_SIZE;
            }
            return (uint32_t)(uintptr_t)gApChestRewardArt;
    }
}

/* Only deterministic native check identities, never the displayed stock item
 * or AP receipt, may choose the sprite. Ordinary non-AP chests stay generic. */
static __attribute__((noinline, long_call, section(".aprewardfx"))) uint32_t
ap_reward_key_for_chest(const void *chest) {
    const uint8_t *object = chest;
    uint32_t source = *(const volatile uint32_t*)(object + 0xB0u);
    uint16_t reward = *(const volatile uint16_t*)(object + 0xE0u);
    uint16_t room = *(const volatile uint16_t*)(object + 0x60u);
    if (reward >= 0xAu && reward <= 0x13u) {
        return AP_REWARD_KEY(AP_REWARD_MAP_CHEST, reward - 0xAu);
    }
    if (reward == 6u) {
        switch (room) {
            case 739u: return AP_REWARD_KEY(AP_REWARD_VITALITY_CHEST, 0u);
            case 815u: return AP_REWARD_KEY(AP_REWARD_VITALITY_CHEST, 1u);
            case 610u: return AP_REWARD_KEY(AP_REWARD_VITALITY_CHEST, 2u);
            case 403u: return AP_REWARD_KEY(AP_REWARD_VITALITY_CHEST, 3u);
            default: return 0u;
        }
    }
    if (reward == 0x28u && room == 406u) return AP_REWARD_KEY(AP_REWARD_SOUND_CHEST, 0u);
    if (reward == 0x63u) {
        uint32_t lever = ap_lever_bit_for_chest(source, reward, object[0xE2u]);
        for (uint32_t bit = 0u; bit < 4u; ++bit) {
            if (lever == (1u << bit)) return AP_REWARD_KEY(AP_REWARD_LEVER, bit);
        }
    }
    return source >= 0x08000000u && source < 0x09000000u
        ? AP_REWARD_KEY(AP_REWARD_MINOR_CHEST, source - 0x08000000u) : 0u;
}

#define AP_REWARD_UPLOAD_HEAD ((volatile uint8_t*)0x030039A4u)
#define AP_REWARD_UPLOAD_TAIL (*(volatile uint8_t*)0x03006078u)
#define AP_REWARD_UPLOAD_RING ((volatile struct ApChestTileUpload*)0x03002EC0u)
static inline uint16_t ap_reward_local_room(void);

/* TitleStruct's previously unused word at +0x0C owns a native OBJ tile allocation.
 * The title constructor clears it; the title destructor returns the slots.
 * Neither the retail logo nor any Press Start frame is replaced. */
#define AP_TITLE_NATIVE_MAIN ((void (*)(void))0x08149DC1u)
#define AP_TITLE_NATIVE_DESTROY ((void (*)(void *))0x0814A1C9u)
#define AP_TITLE_VRAM_ALLOC ((uint32_t (*)(uint32_t))0x081570B1u)
#define AP_TITLE_VRAM_FREE ((void (*)(uint32_t))0x08157191u)
#define AP_TITLE_OAM_ALLOC ((volatile uint16_t *(*)(uint8_t))0x08156D85u)
#define AP_TITLE_BADGE_BANK 15u
#define AP_TITLE_BADGE_X 200u
#define AP_TITLE_BADGE_Y 8u

static inline uint8_t *ap_title_task_data(const void *task) {
    const uint16_t *native = (const uint16_t *)task;
    return (uint8_t *)(uintptr_t)((native[9] & 0x10u)
        ? 0x02000000u + ((uint32_t)native[3] << 2) : 0x03000000u + native[3]);
}

AP_REWARD_FX __attribute__((used)) void ap_title_badge_main(void) {
    void *task = *(void *volatile *)0x030035D0u;
    uint8_t *title = ap_title_task_data(task);
    uint32_t *badge_vram = (uint32_t *)(title + 0x0Cu);
    if (*(const uint32_t *)(title + 4u) != 0u) {
        if (*badge_vram == 0u) {
            uint8_t head = *AP_REWARD_UPLOAD_HEAD;
            if (ap_reward_tile_queue_available(head, AP_REWARD_UPLOAD_TAIL)) {
                uint32_t vram = AP_TITLE_VRAM_ALLOC(sizeof(gApTitleBadgeArt) / 32u);
                if (vram >= 0x06010000u && vram <= 0x06018000u - sizeof(gApTitleBadgeArt)) {
                    /* Same stock bank-F colors as generate_chest_reward_art.py.
                     * Title glyphs use OBJ bank 0; only the title owns this bank now. */
                    static const uint16_t colors[] __attribute__((section(".apstatuefx_data"))) = {
                        0x5EA0, 0x7E80, 0x00D2, 0x01B8, 0x02FE, 0x08BF, 0x025F, 0x0000,
                        0x6E9F, 0x7D40, 0x7FA0, 0x1C96, 0x393B, 0x1262, 0x7FFF, 0x03FF,
                    };
                    volatile uint16_t *palette = (volatile uint16_t *)0x03002C60u;
                    for (unsigned i = 0; i < 16; ++i)
                        palette[AP_TITLE_BADGE_BANK * 16u + i] = colors[i];
                    *(volatile uint32_t *)0x03002440u |= 1u << 1; /* OBJ palette sync */
                    AP_REWARD_UPLOAD_RING[head].source = (uint32_t)(uintptr_t)gApTitleBadgeArt;
                    AP_REWARD_UPLOAD_RING[head].destination = vram;
                    AP_REWARD_UPLOAD_RING[head].size = sizeof(gApTitleBadgeArt);
                    *AP_REWARD_UPLOAD_HEAD = (head + 1u) & 63u;
                    *badge_vram = vram;
                }
            }
        } else {
            volatile uint16_t *oam = AP_TITLE_OAM_ALLOC(0x0Bu);
            if ((uintptr_t)oam != 0x03008000u) {
                oam[0] = AP_TITLE_BADGE_Y;
                oam[1] = (2u << 14) | AP_TITLE_BADGE_X; /* 32x32 square */
                oam[2] = (AP_TITLE_BADGE_BANK << 12) | ((*badge_vram - 0x06010000u) >> 5);
            }
        }
    }
    AP_TITLE_NATIVE_MAIN();
}

AP_REWARD_FX __attribute__((used)) void ap_title_badge_destroy(void *task) {
    uint32_t *badge_vram = (uint32_t *)(ap_title_task_data(task) + 0x0Cu);
    if (*badge_vram != 0u) {
        AP_TITLE_VRAM_FREE(*badge_vram);
        *badge_vram = 0u;
    }
    AP_TITLE_NATIVE_DESTROY(task);
}

static AP_REWARD_FX uint8_t ap_can_show_animated_shard(void) {
    const volatile uint32_t *header = (const volatile uint32_t*)AP_SHARD_AWARD_ROM;
    return header[0] == AP_SHARD_AWARD_MAGIC_FIRST && header[1] == AP_SHARD_AWARD_MAGIC_LAST
        && ap_reward_tile_queue_available(*AP_REWARD_UPLOAD_HEAD, AP_REWARD_UPLOAD_TAIL)
        && ap_reward_native_vram_can_fit_tiles((const volatile uint16_t*)0x030064B0u,
            *(const volatile uint16_t*)0x03002488u, *(const volatile uint32_t*)0x03002540u,
            AP_SHARD_AWARD_VRAM_TILES);
}

/* Prefer the native 16Ã—16 chest slot (variant 0), even for no-bonus chests.
 * Without safe VRAM, use native 0x63: it starts the same popup timer but
 * reserves no sprite tiles. The native reward reads the parent Chest::unkE0. */
__attribute__((used, noinline, long_call, section(".aphub")))
void ap_chest_reward_art(void *chest, int16_t x, int16_t y, uint16_t item) {
    typedef void (*ChestPopupFn)(void *, int16_t, int16_t, uint16_t);
    ChestPopupFn native_popup = (ChestPopupFn)0x0800B415u;
    volatile uint8_t *tile_head = (volatile uint8_t *)0x030039A4u;
    volatile struct ApChestTileUpload *tile_ring = (volatile struct ApChestTileUpload *)0x03002EC0u;
    uint8_t before;

    /* Physical lever pulls use this same native open call. Wall receipts
     * and restored pulls only change the wall or callback; neither enters it. */
    (void)item;  /* Native visual parameter, not the real parent reward. */
    if (!ap_reward_tile_queue_available(*tile_head, AP_REWARD_UPLOAD_TAIL)
        || !ap_reward_native_vram_available()) {
        native_popup(chest, x, y, 0x63u);
        return;
    }
    uint8_t art = ap_reward_art_for_key(ap_reward_key_for_chest(chest));
    if (art == AP_REWARD_MIRROR_SHARD) {
        uint16_t room = *(const volatile uint16_t*)((const uint8_t*)chest + 0x60u);
        if (ap_reward_local_room() == room && ap_can_show_animated_shard()) {
            /* The native constructor still owns this chest's real timer and
             * reward. Its no-art mode leaves the optional 32x32 overlay free
             * to render without altering that task or adding a pickup. */
            native_popup(chest, x, y, 0x63u);
            (void)ap_show_room_reward_gem(room, (int32_t)x * 256,
                ((int32_t)y - 16) * 256, 0u, art);
            return;
        }
    }
    before = *tile_head;
    native_popup(chest, x, y, 0u);
    /* Change only this popup's single queued VRAM upload. All palettes,
     * native effects, timing, saves and reward/check data remain native. */
    ap_chest_redirect_upload(tile_ring, before, *tile_head, ap_reward_tiles_for_art(art));
}

#define AP_HUB_SAVED_CHECKS ((volatile uint32_t*)0x02028C7Cu)
#define AP_HUB_ROM_AUTH ((const volatile uint32_t*)0x08F00000u)

static __attribute__((noinline, long_call, section(".aphub")))
void ap_set_lever_activation_flag(uint32_t lever_bit) {
    uint32_t bit;
    for (bit = 0u; bit < 4u; bit++) {
        if (lever_bit == (1u << bit)) {
            ap_lever_record_check(AP_HUB_SAVED_CHECKS, AP_HUB_ROM_AUTH, bit);
            break;
        }
    }
    AP_LEVER_ACTIVATION_FLAGS = ap_lever_saved_checks(AP_HUB_SAVED_CHECKS, AP_HUB_ROM_AUTH);
}

/* Keep physical-check persistence outside the fixed retail payload window. */
static __attribute__((noinline, long_call, section(".aphub")))
void ap_record_minor_chest_collection_from_obj_ptr(uint32_t chest_obj_ptr) {
    uint32_t source_ptr = *(volatile uint32_t*)(chest_obj_ptr + 0xB0u);
    uint32_t chest_index = (uint32_t)(*(volatile uint8_t*)(chest_obj_ptr + 0xE2u));

    uint32_t lever_bit = ap_lever_bit_for_obj(chest_obj_ptr);
    if (lever_bit != 0u) {
        ap_set_lever_activation_flag(lever_bit);
        /* This hook replaces CollectChest, before the original guarded native
         * world-save call. Let that existing save commit the physical pull. */
        return;
    }

    ap_record_minor_chest_source_ptr(source_ptr);
    if (ap_is_ap_owned_minor_chest_source(source_ptr)
        && *(volatile uint16_t*)(chest_obj_ptr + 0xE0u) <= 5u) {
        /* Chest::unkDC is zeroed on creation and has no other use in the game code. */
        *(volatile uint32_t*)(chest_obj_ptr + 0xDCu) = AP_MINOR_CHEST_ITEM_SUPPRESSION_MARKER;
    }
    ap_collect_small_chest_native(chest_index);
}

static __attribute__((noinline, long_call, section(".aphub")))
void ap_set_hub_switch_flag(uint32_t bit) {
    if (!ap_hub_record_check(AP_HUB_SAVED_CHECKS, AP_HUB_ROM_AUTH, bit)) return;
    AP_HUB_SWITCH_FLAGS = ap_hub_saved_checks(AP_HUB_SAVED_CHECKS, AP_HUB_ROM_AUTH);
    switch (ap_hub_save_action(*(volatile uint32_t*)0x0203AD10u,
                              *(volatile uint8_t*)0x0203AD3Cu,
                              *(volatile uint8_t*)0x0203AD24u)) {
        case 1u:
            ((int16_t (*)(uint32_t, uint16_t))0x0800ACD5u)(
                1u, ap_hub_save_slot(*(volatile uint16_t*)0x0203AD48u));
            break;
        case 2u: ((void (*)(uint32_t))0x08031CE5u)(8u); break;
        default: break;
    }
}

static __attribute__((noinline, long_call, section(".aphub")))
void ap_restore_hub_switch_checks(void) {
    /* Assignment handles native file changes without leaking old RAM bits.
     * Client acknowledgement recovery updates this same seed-bound save buffer. */
    AP_HUB_SWITCH_FLAGS = ap_hub_saved_checks(AP_HUB_SAVED_CHECKS, AP_HUB_ROM_AUTH);
    AP_LEVER_ACTIVATION_FLAGS = ap_lever_saved_checks(AP_HUB_SAVED_CHECKS, AP_HUB_ROM_AUTH);
}

typedef uint32_t *(*KirbyWorldPropsEntryFn)(uint32_t, uint8_t, uint8_t);
#define KIRBY_WORLD_PROPS_ENTRY_FN ((KirbyWorldPropsEntryFn)0x08002889u)
#define KIRBY_WORLD_PROPS_HUB_UNLOCK_KIND 2u
#define KIRBY_WORLD_MAP_TRANSITION_COMPLETE_FN ((WorldMapUnlockFn)0x08039671u)

// sub_08039ED4 dispatches using enum WorldMapDoor where 0 = NO_UNLOCK.
// AP hub-switch bits use a different stable ordering contract, so translate
// explicitly and ignore non-unlock/unknown indices.
#include "generated_hub_switch_tables.inc"

static uint8_t ap_try_map_worldmap_door_to_hub_switch_bit(
    uint16_t door_index,
    uint32_t *out_bit,
    uint8_t *out_world_props_unlock_index
) {
    if (out_bit == 0 || out_world_props_unlock_index == 0 || door_index == 0u || door_index > 15u) {
        return 0u;
    }
    *out_bit = ap_hub_bits[door_index];
    *out_world_props_unlock_index = ap_hub_props[door_index];
    return 1u;
}

static volatile uint32_t *ap_get_hub_unlock_entry(uint8_t world_props_unlock_index) {
    return (volatile uint32_t*)KIRBY_WORLD_PROPS_ENTRY_FN(
        KIRBY_WORLD_PROPS_HUB_UNLOCK_KIND,
        world_props_unlock_index,
        0u
    );
}

/* The native words are projections, not ownership. Clear unearned words
 * on load as well as restoring earned ones before mirrors initialize. */
__attribute__((noinline, long_call, section(".aphub")))
void ap_project_hub_doors(uint32_t owned) {
    uint16_t door;
    for (door = 1u; door <= 15u; ++door) {
        uint32_t physical_bit;
        uint8_t native_index;
        if (!ap_try_map_worldmap_door_to_hub_switch_bit(door, &physical_bit, &native_index)) continue;
        volatile uint32_t *entry = ap_get_hub_unlock_entry(native_index);
        if (entry != 0) *entry = (owned >> (door + 7u)) & 1u;
    }
}

/* Native visits are still recorded and saved by the original transition.
 * Pending visuals are transient and tied to the authenticated save epoch. */
#define AP_RANDOM_TELEPORT_MAILBOX_ADDRESS (AP_BASE + 0x1C0u)
#define AP_VISIT_PENDING_ADDRESS (AP_BASE + 0x1C8u)
struct ApVisitPending { uint32_t epoch, start; uint16_t room, arts; };
#define AP_BOSS_ITEM_DRAW_ADDRESS (AP_BASE + 0x1D4u)
struct ApBossItemDraw { uint32_t epoch, object; uint8_t art; };
#define AP_BOSS_ITEM_DRAW ((volatile struct ApBossItemDraw*)AP_BOSS_ITEM_DRAW_ADDRESS)
#define AP_VISIT_PENDING ((volatile struct ApVisitPending*)AP_VISIT_PENDING_ADDRESS)
_Static_assert(AP_CUE_MAILBOX_ADDRESS + 0x10u <= AP_RANDOM_TELEPORT_MAILBOX_ADDRESS,
               "Random Teleport mailbox overlaps receipt cue mailbox");
_Static_assert(AP_RANDOM_TELEPORT_MAILBOX_ADDRESS + 8u <= AP_VISIT_PENDING_ADDRESS,
               "Random Teleport mailbox overlaps visit effect");
_Static_assert(AP_VISIT_PENDING_ADDRESS + sizeof(struct ApVisitPending) <= AP_BOSS_ITEM_DRAW_ADDRESS,
               "Visit and boss trap state overlap");
_Static_assert(AP_BOSS_ITEM_DRAW_ADDRESS + sizeof(struct ApBossItemDraw) <= AP_VISUAL_MAILBOX_ADDRESS,
               "Boss item art state overlaps receipt visual mailbox");
_Static_assert(AP_VISUAL_MAILBOX_ADDRESS + sizeof(struct ApReceiptVisualMailbox) <= AP_PROGRESS_RESTORE_ADDRESS,
               "Receipt visual state overlaps offline progress restore mailbox");

#define AP_NATIVE_VISITS ((const volatile uint16_t*)0x02028CA0u)
#include "generated_visit_reward_art_rooms.inc"

__attribute__((used, section(".aproomvisitconfig")))
volatile const uint32_t gApVisitRoomArtConfig = AP_VISIT_CORE_ONLY;

AP_REWARD_FX __attribute__((used)) void ap_record_room_visit_for_reward_art(uint16_t room, void *kirby) {
    uint32_t epoch = 0u;
    uint16_t arts = 0u, index = AP_VISIT_ENTRY_COUNT; /* Invalid index unless native room table matches. */
    if (kirby == (void*)KIRBY_STRUCTS_ADDR && room < 0x9998u / 40u) {
        index = *(const volatile uint16_t*)(0x089331ACu + (uint32_t)room * 40u + 36u);
        arts = ap_visit_reward_arts(AP_NATIVE_VISITS, ap_visit_areas, ap_visit_room_kinds,
            index, gApVisitRoomArtConfig, &gApRewardArtConfig);
        if (arts) epoch = ap_copy_room_epoch();
    }
    ((void (*)(uint16_t))0x08002A81u)(room);
    if (epoch != 0u && (AP_NATIVE_VISITS[index] & AP_VISIT_NATIVE_BIT) != 0u) {
        AP_VISIT_PENDING->start = AP_FRAME_COUNTER;
        AP_VISIT_PENDING->room = room;
        AP_VISIT_PENDING->arts = arts;
        AP_VISIT_PENDING->epoch = epoch;
    }
}

/* The native palette manager can keep a room white even when hardware blend
 * shadows are zero. Inspect only its currently queued, bank-F effects. */
static inline uint8_t ap_visit_palette_ready(void) {
    const uintptr_t manager = 0x02022930u;
    for (uint32_t i = 0u; i < 8u; ++i) {
        uintptr_t effect = *(const volatile uint32_t*)(manager + 0x80u + i * 4u);
        if (effect < manager || effect >= manager + 0x80u || ((effect - manager) & 15u) != 0u) {
            continue;
        }
        uint8_t type = *(const volatile uint8_t*)effect;
        if ((*(const volatile uint16_t*)(effect + 4u) & 0x8000u)
            && (*(const volatile uint16_t*)(effect + 8u) & 2u)
            && (type == 4u || (type == 1u && *(const volatile int8_t*)(effect + 1u) > 0))) {
            return 0u;
        }
    }
    return 1u;
}

static __attribute__((noinline, long_call, section(".aprewardfx"))) void ap_visit_reward_art_poll(void) {
    uint32_t epoch = AP_VISIT_PENDING->epoch;
    if (epoch == 0u) return;
    uint16_t room = AP_VISIT_PENDING->room;
    if (epoch != ap_copy_room_epoch()
        || *(volatile uint16_t*)(KIRBY_STRUCTS_ADDR + KIRBY_STRUCT_ROOM_OFFSET) != room
        || AP_FRAME_COUNTER - AP_VISIT_PENDING->start > AP_VISIT_MAX_VISUAL_WAIT) {
        AP_VISIT_PENDING->epoch = 0u;
        return;
    }
    if (!ap_visit_scene_ready(*(volatile uint32_t*)(KIRBY_STRUCTS_ADDR + 8u),
            *(volatile uint32_t*)0x03002440u, *(volatile uint16_t*)0x030024E8u,
            *(volatile uint16_t*)0x030024ECu) || !ap_visit_palette_ready()) return;
    AP_VISIT_PENDING->epoch = 0u;
    ap_show_player_reward_gem(room, AP_VISIT_PENDING->arts);
}

/* Parentless visual for AP checks that are not Chest objects. The native
 * Chest popup eventually reads and grants its parent chest's item. This task
 * uses only native tile/draw/cleanup APIs and cannot grant a reward. */
static inline uint8_t *ap_reward_task_data(void *task) {
    const uint8_t *native = task;
    return (uint8_t*)(uintptr_t)ap_reward_task_effect_address(
        *(const volatile uint16_t*)(native + 6u), *(const volatile uint16_t*)(native + 0x12u));
}

/* A failed nonempty task has a scheduler slot but no owned data. Remove it
 * without allowing the destructor or TaskDestroy to use its invalid offset. */
static inline void ap_drop_invalid_reward_task(void *task) {
    uint8_t *native = task;
    *(volatile uint16_t*)(native + 6u) = 0u;
    *(volatile uint32_t*)(native + 0xCu) = 0u;
    ((void (*)(void*))0x08152C3Du)(task);
}

static inline uint16_t ap_reward_local_room(void) {
    uint8_t player = KIRBY_CURRENT_PLAYER;
    if (player >= KIRBY_PLAYER_COUNT) return 0xFFFFu;
    return *(volatile uint16_t*)(KIRBY_STRUCTS_ADDR
        + (uint32_t)player * KIRBY_STRUCT_STRIDE + KIRBY_STRUCT_ROOM_OFFSET);
}

static const uint16_t ap_area_boss_rooms[8] __attribute__((section(".apvisitdata"))) = {
    324u, 710u, 417u, 822u, 219u, 516u, 738u, 129u,
};

/* Do not use a global replacement of animation 0x2D4: it also renders
 * outside gameplay. Match the dynamic native drop, subtype, and boss room. */
static __attribute__((noinline, section(".aprewardfx"))) uint8_t ap_is_boss_shard(const uint8_t *object) {
    if (object[0] != 1u || object[0x82u] != 0x65u) return 0u;
    uint16_t subtype = *(const volatile uint16_t*)(object + 0xD4u);
    if (subtype >= 8u || *(const volatile uint16_t*)(object + 0x60u) != ap_area_boss_rooms[subtype]) return 0u;
    uintptr_t source = *(const volatile uint32_t*)(object + 0xB0u);
    if (source < 0x02000000u || source > 0x0203FFDCu) return 0u;
    const uint8_t *template = (const uint8_t*)source;
    return template[0] == 1u && template[1] == 0x24u && template[3] == 0x1Fu
        && template[0xCu] == 0x65u && template[0xEu] == subtype;
}

static inline uint8_t ap_displayed_boss_art(const uint8_t *object) {
    return AP_BOSS_ITEM_DRAW->object == (uint32_t)(uintptr_t)object
        && AP_BOSS_ITEM_DRAW->epoch != 0u && AP_BOSS_ITEM_DRAW->epoch == AP_COPY_CONTEXT->epoch
        ? AP_BOSS_ITEM_DRAW->art : AP_REWARD_GEM;
}

static inline void ap_replace_boss_shard_tiles(const uint8_t *object, const uint8_t *sprite, uint8_t before) {
    uint8_t art = ap_displayed_boss_art(object);
    /* A real Mirror Shard awarded at a native shard drop already has the
     * correct dynamic sprite; leave its full animation and palette alone. */
    if (art == AP_REWARD_MIRROR_SHARD) return;
    ap_boss_shard_redirect_upload((volatile struct ApChestTileUpload*)0x03002EC0u, before,
        *(volatile uint8_t*)0x030039A4u, *(const volatile uint32_t*)sprite, ap_reward_tiles_for_art(art), art >= AP_REWARD_ONE_UP);
}

AP_REWARD_FX __attribute__((used)) void ap_init_boss_shard_sprite(void *object) {
    uint8_t before = *(volatile uint8_t*)0x030039A4u;
    ((void (*)(void*))0x0809F3E1u)(object);
    if (ap_is_boss_shard(object)) {
        uint16_t boss = *(const volatile uint16_t*)((const uint8_t*)object + 0xD4u);
        uint32_t epoch = ap_copy_room_epoch();
        uint8_t art = ap_reward_art_for_key(AP_REWARD_KEY(AP_REWARD_BOSS, boss));
        AP_BOSS_ITEM_DRAW->object = 0;
        if (epoch && art != AP_REWARD_GEM
            && ap_boss_item_record_display(AP_HUB_SAVED_CHECKS, AP_HUB_ROM_AUTH, boss)) {
            /* Keep that one drop's art stable for every native upload. A
             * newly spawned shard in a repeat fight is only a generic gem. */
            AP_BOSS_ITEM_DRAW->epoch = epoch;
            AP_BOSS_ITEM_DRAW->object = (uint32_t)(uintptr_t)object;
            AP_BOSS_ITEM_DRAW->art = art;
        }
        ap_replace_boss_shard_tiles(object, (const uint8_t*)object + 0x10u, before);
    }
}

AP_REWARD_FX __attribute__((used)) int32_t ap_update_reward_or_statue_sprite(void *sprite) {
    uint8_t before = *(volatile uint8_t*)0x030039A4u;
    int32_t result = ((int32_t (*)(void*))0x08155129u)(sprite);
    const uint8_t *data = sprite;
    if (*(const volatile uint16_t*)(data + 0xCu) == AP_SHARD_NATIVE_ANIM
        && ap_is_boss_shard(data - 0x10u)) {
        ap_replace_boss_shard_tiles(data - 0x10u, data, before);
    } else {
        ap_world_statue_redirect(data, before);
    }
    return result;
}

static AP_REWARD_FX void ap_draw_boss_shard_sprite(void *sprite) {
    typedef void (*DisplayFn)(void *);
    DisplayFn native = (DisplayFn)0x0815604Du;
    uint8_t *data = sprite;
    volatile uint32_t *frame = (volatile uint32_t*)(data + 4u);
    volatile uint32_t *draw_flags = (volatile uint32_t*)(data + 8u);
    volatile uint16_t *anim = (volatile uint16_t*)(data + 0xCu);
    uint32_t original_frame = *frame;
    if (*anim != AP_SHARD_NATIVE_ANIM || original_frame > 8u || !ap_is_boss_shard(data - 0x10u)
        || ap_displayed_boss_art(data - 0x10u) == AP_REWARD_MIRROR_SHARD) {
        native(sprite);
        return;
    }
    uint32_t flags = *draw_flags;
    uint8_t palette = data[0x1Fu];
    /* Temporarily select the one centered 16Ã—16 gem rendering frame.
     * Original animation, timings and collision fields remain native. */
    *anim = AP_GEM_RENDER_ANIM;
    *frame = 0u;
    *draw_flags = flags & ~0xC00u;
    data[0x1Fu] = 15u;
    native(sprite);
    data[0x1Eu] = original_frame == 2u || original_frame == 6u ? 2u : 4u;
    data[0x1Fu] = palette;
    *draw_flags = flags;
    *frame = original_frame;
    *anim = AP_SHARD_NATIVE_ANIM;
}

/* The generic object renderer is shared: each dispatch must call native
 * display once, and the unrelated sprite class keeps native behavior. */
AP_REWARD_FX __attribute__((used)) void ap_draw_reward_or_statue_sprite(void *sprite) {
    if (*(const volatile uint16_t*)((const uint8_t*)sprite + 0xCu) == AP_STATUE_NATIVE_ANIM) {
        ap_draw_world_statue_sprite(sprite);
    } else {
        ap_draw_boss_shard_sprite(sprite);
    }
}

static __attribute__((noinline, section(".aprewardfx"))) void ap_reward_gem_frame(void) {
    void *task = *(void *volatile*)0x030035D0u;
    uint8_t *effect = ap_reward_task_data(task);
    if (effect == 0) {
        ap_drop_invalid_reward_task(task);
        return;
    }
    volatile uint16_t *age = (volatile uint16_t*)(effect + 4u);
    uint8_t animated = *(const volatile uint16_t*)(effect + 0x18u) == AP_SHARD_AWARD_STATIC_ANIM;
    uint8_t ticks = (uint8_t)*age;
    uint32_t stop = *(volatile uint32_t*)(effect + 0x48u);
    uint8_t stopped = (stop & AP_VISUAL_REJECTED)
        ? (stop & ~AP_VISUAL_REJECTED) != AP_VISUAL_MAILBOX->active
        : (AP_HUB_SWITCH_FLAGS & stop) != 0u;
    if (ticks >= (animated ? AP_SHARD_AWARD_TICKS : AP_VISUAL_DURATION)
        || *(volatile uint16_t*)(effect + 0x42u) != ap_reward_local_room() || stopped) {
        if (animated) {
            ap_shard_award_cancel_uploads(AP_REWARD_UPLOAD_RING, *AP_REWARD_UPLOAD_HEAD,
                AP_REWARD_UPLOAD_TAIL, *(const volatile uint32_t*)(effect + 0xCu));
        }
        ((void (*)(void*))0x08152C3Du)(task); /* TaskDestroy invokes ObjectBaseDestroy. */
        return;
    }
    if (animated && ap_shard_award_frame_changed(ticks)) {
        /* Queue one owned 32x32 tile batch per changed frame; an occupied
         * native DMA queue safely drops visual frames without blocking. */
        (void)ap_shard_award_queue_frame(AP_REWARD_UPLOAD_RING, AP_REWARD_UPLOAD_HEAD,
            AP_REWARD_UPLOAD_TAIL, *(const volatile uint32_t*)(effect + 0xCu), ticks);
    }
    if ((ticks & 1u) == 0u) *(volatile int32_t*)(effect + 0x38u) -= 256;
    *age = ticks + 1u;
    ((void (*)(void*))0x0806FAC9u)(effect); /* EffectObjectPostUpdate */
}

AP_REWARD_FX uint8_t ap_show_room_reward_gem(uint16_t room, int32_t x, int32_t y, uint32_t stop_hub_bit, uint8_t art) {
    typedef void (*TaskFn)(void);
    typedef void (*DtorFn)(void *);
    typedef void *(*TaskCreateFn)(TaskFn, uint16_t, uint16_t, uint16_t, DtorFn);
    typedef void (*SpriteInitFn)(void *, void *, uint32_t, uint16_t, uint8_t, uint16_t);
    volatile uint8_t *head = (volatile uint8_t*)0x030039A4u;
    volatile struct ApChestTileUpload *ring = (volatile struct ApChestTileUpload*)0x03002EC0u;
    if (room != ap_reward_local_room()
        || !ap_reward_tile_queue_available(*head, AP_REWARD_UPLOAD_TAIL)) return 0u;
    uint8_t animated = art == AP_REWARD_MIRROR_SHARD && ap_can_show_animated_shard();
    if (!animated && !ap_reward_native_vram_available()) return 0u;
    void *task = ((TaskCreateFn)0x08152B01u)(ap_reward_gem_frame, AP_REWARD_EFFECT_SIZE, 0x3500u, 0u,
                                          (DtorFn)0x0803DCCDu);
    if (task == (void*)0x03002500u) return 0u; /* gEmptyTask */
    uint8_t *effect = ap_reward_task_data(task);
    if (effect == 0) {
        ap_drop_invalid_reward_task(task);
        return 0u;
    }
    ((void (*)(void*))0x0803E3B1u)(effect); /* ClearEffectObject */
    effect[0] = 3u;
    uint32_t vram = ((uint32_t (*)(uint32_t))0x081570B1u)(animated ? AP_SHARD_AWARD_VRAM_TILES : 4u);
    if (!(animated ? ap_shard_award_vram_valid(vram) : ap_reward_vram_address_is_valid(vram))) {
        ((void (*)(void*))0x08152C3Du)(task);
        return 0u;
    }
    *(volatile int32_t*)(effect + 0x34u) = x;
    *(volatile int32_t*)(effect + 0x38u) = y;
    *(volatile uint16_t*)(effect + 0x42u) = room;
    *(volatile uint32_t*)(effect + 0x48u) = stop_hub_bit;
    uint8_t before = *head;
    ((SpriteInitFn)0x080709F9u)(effect, effect + 0xCu, vram,
        animated ? AP_SHARD_AWARD_STATIC_ANIM : AP_GEM_RENDER_ANIM, 0u, 0xBu);
    uint8_t redirected = animated ? ap_shard_award_redirect_first(ring, before, *head, vram)
        : ap_chest_redirect_upload(ring, before, *head, ap_reward_tiles_for_art(art));
    if (!redirected) {
        /* Drop the effect on the next task tick; do not show a stock item. */
        *(volatile uint16_t*)(effect + 4u) = 0xFFu;
        return 0u;
    }
    return 1u;
}

/* Goal results can put Kirby above the camera. Keep the independent gem in
 * the visible room even then; the native return motion remains untouched. */
AP_REWARD_FX void ap_show_player_reward_gem(uint16_t room, uint16_t arts) {
    if (!arts) return;
    uint8_t player = KIRBY_CURRENT_PLAYER;
    if (player >= KIRBY_PLAYER_COUNT || room != ap_reward_local_room()) return;
    uintptr_t kirby = KIRBY_STRUCTS_ADDR + (uint32_t)player * KIRBY_STRUCT_STRIDE;
    uintptr_t viewport = 0x02023530u + (uint32_t)player * 0x668u + 0xCu;
    int32_t camera_x = *(volatile int32_t*)viewport;
    int32_t camera_y = *(volatile int32_t*)(viewport + 4u);
    int32_t x = *(volatile int32_t*)(kirby + 0x40u);
    int32_t y = *(volatile int32_t*)(kirby + 0x44u) - 24 * 256;
    /* A visit can collect two checks. Prioritize distinct native artwork
     * over the gem if memory fits only one, keeping them 20 pixels apart. */
    uint8_t preferred = (uint8_t)((arts & 0xFFu) - 1u);
    uint8_t other = (uint8_t)(arts >> 8);
    int32_t separation = !other ? 0 : (preferred == AP_REWARD_MIRROR_SHARD
        || other == AP_REWARD_MIRROR_SHARD + 1u ? 14 : 10) * 256;
    if (x < camera_x + 16 * 256 + separation) x = camera_x + 16 * 256 + separation;
    if (x > camera_x + 224 * 256 - separation) x = camera_x + 224 * 256 - separation;
    if (y < camera_y + 48 * 256) y = camera_y + 48 * 256;
    if (y > camera_y + 132 * 256) y = camera_y + 132 * 256;
    ap_show_room_reward_gem(room, x + separation, y, 0u, preferred);
    if (other) ap_show_room_reward_gem(room, x - separation, y, 0u, other - 1u);
}

__attribute__((used, noinline, long_call, section(".aprewardfx")))
void ap_big_switch_reward_art(void *object) {
    const uint8_t *sw = object;
    uint16_t state = *(const volatile uint16_t*)(sw + 0xB6u);
    uint16_t room = *(const volatile uint16_t*)(sw + 0x60u);
    uint32_t show_bit = 0u;
    uint8_t art = AP_REWARD_GEM;
    /* Only the world-map branch of SwitchMain reaches this wrapper. Native
     * SwitchUpdatePressState sets 2 for a newly accepted press; the function
     * below sets its own 0x2000 sequence latch, including if the map is busy. */
    if ((state & 0x2002u) == 2u
        && *(const volatile uint16_t*)(sw + 0xB8u) != 0u
        && room == ap_reward_local_room()) {
        const uint8_t *source = *(const uint8_t*const volatile*)(sw + 0xB0u);
        uint16_t door = *(const volatile uint16_t*)(source + 0x14u);
        if (source[12] == 0x86u && door >= 1u && door <= 15u && source[4] == ap_hub_props[door]) {
            uint32_t bit = 1u << ap_hub_bits[door];
            if ((ap_hub_saved_checks(AP_HUB_SAVED_CHECKS, AP_HUB_ROM_AUTH) & bit) == 0u) {
                show_bit = bit;
                art = ap_reward_art_for_key(AP_REWARD_KEY(AP_REWARD_SWITCH, ap_hub_bits[door]));
            }
        }
    }
    /* Keep the original press latch/interlude/check/save flow untouched,
     * even on dropped art or native switches outside the AP table. */
    ((void (*)(void*))0x08119B3Du)(object);
    if (show_bit) {
        ap_show_room_reward_gem(room, *(const volatile int32_t*)(sw + 0x40u),
            *(const volatile int32_t*)(sw + 0x44u) - 30 * 256, show_bit, art);
    }
}

/*
 * Hook target for the Big Switch object's native state lookup in
 * sub_0811938C. The door-to-hub initializer at sub_0802AD00 remains untouched
 * and continues to consume the real persisted world-props state.
 * An AP-owned door is not evidence that its physical switch was collected, so
 * present a zero-valued scratch entry until the AP switch check itself is hit.
 */
__attribute__((used)) uint32_t *ap_on_hub_switch_init_state_lookup(
    uint32_t unlock_kind,
    uint32_t world_props_unlock_index,
    uint32_t unlock_flags
) {
    if (unlock_kind == KIRBY_WORLD_PROPS_HUB_UNLOCK_KIND && world_props_unlock_index <= 0xFFu) {
        uint32_t door;
        ap_restore_hub_switch_checks();
        for (door = 1u; door <= 15u; door++) {
            if (ap_hub_props[door] == world_props_unlock_index) {
                /* Physical checks remain independent even before client history,
                 * and a saved hit stays hidden without owning its connection. */
                AP_HUB_SWITCH_INIT_STATE = (AP_HUB_SWITCH_FLAGS >> ap_hub_bits[door]) & 1u;
                return (uint32_t*)&AP_HUB_SWITCH_INIT_STATE;
            }
        }
    }

    return KIRBY_WORLD_PROPS_ENTRY_FN(
        unlock_kind,
        (uint8_t)world_props_unlock_index,
        (uint8_t)unlock_flags
    );
}

static void ap_set_vitality_chest_flag_for_room(uint16_t room_id) {
    switch (room_id) {
        case 739u: // Carrot Castle 5-23 Big Chest
            ap_set_vitality_chest_flag(0u);
            break;
        case 815u: // Olive Ocean 6-21 Big Chest
            ap_set_vitality_chest_flag(1u);
            break;
        case 610u: // Radish Ruins 8-4 Big Chest
            ap_set_vitality_chest_flag(2u);
            break;
        case 403u: // Candy Constellation 9-8 Big Chest
            ap_set_vitality_chest_flag(3u);
            break;
        default:
            break;
    }
}

static void ap_unlock_area_map(uint32_t area_id) {
    if (area_id < 32u) {
        KIRBY_BIG_CHEST_FLAGS |= (1u << area_id);
    }
}

typedef uint32_t (*KirbySpecialDoorVisitedFn)(uint16_t, uint16_t, uint8_t, uint8_t);
#define KIRBY_SPECIAL_DOOR_VISITED_FN ((KirbySpecialDoorVisitedFn)0x08002BA9u)
#define KIRBY_ROOM_AREA_INFO_TABLE_ADDR 0x08D6CD0Cu
#define KIRBY_ROOM_AREA_INFO_AREA_OFFSET 0x46u
#define KIRBY_ROOM_AREA_INFO_COUNT 1000u
#define KIRBY_NATIVE_AREA_UNKNOWN 0xFFu
#define ROOM_PROPS_BASE_ADDR 0x089331ACu
#define ROOM_PROPS_STRIDE 0x28u
#define ROOM_PROPS_DOORS_IDX_OFFSET 0x24u
#define ROOM_PROPS_ROOM_ID_LIMIT 0x400u
#define KIRBY_CURRENT_ROOM_ADDR 0x02023B28u
#define KIRBY_CURRENT_ROOM      (*(volatile uint16_t*)(KIRBY_CURRENT_ROOM_ADDR))
#define KIRBY_COLLISION_ATTRIBUTES_ADDR 0x082D88B8u
#define KIRBY_COLLISION_ATTRIBUTES ((volatile const uint32_t*)KIRBY_COLLISION_ATTRIBUTES_ADDR)
#define KIRBY_LEVEL_INFO_BASE_ADDR 0x02023530u
#define KIRBY_LEVEL_INFO_STRIDE 0x668u
#define KIRBY_LEVEL_MIN_X_OFFSET 0x48u
#define KIRBY_LEVEL_MIN_Y_OFFSET 0x4Cu
#define KIRBY_LEVEL_MAX_X_OFFSET 0x50u
#define KIRBY_LEVEL_MAX_Y_OFFSET 0x54u
#define KIRBY_PLAYER_COUNT_LIMIT 4u
#define KIRBY_EWRAM_START 0x02000000u
#define KIRBY_EWRAM_END 0x02040000u
#define KIRBY_IWRAM_START 0x03000000u
#define KIRBY_IWRAM_END 0x03008000u
#define KIRBY_OBJECT_DESTINATION_ROOM_OFFSET 0x63u
#define KIRBY_WARP_STAR_KIRBY_PTR_OFFSET 0x6Cu
#define KIRBY_WARP_STAR_DESTINATION_ROOM_OFFSET 0xBEu
#define KIRBY_MIRROR_SHARD_OBJECT_PTR_OFFSET 0xB0u
#define KIRBY_MIRROR_SHARD_DESTINATION_ROOM_OFFSET 0x1Eu

typedef uint8_t (*KirbyGetCollisionTileFn)(uint8_t, uint16_t, uint16_t);
#define KIRBY_GET_COLLISION_TILE_FN ((KirbyGetCollisionTileFn)0x080023E5u)
typedef void *(*KirbySpecialTileFn)(uint8_t, uint8_t, uint8_t);
#define KIRBY_SPECIAL_TILE_FN ((KirbySpecialTileFn)0x080025ADu)
typedef uint8_t (*KirbyButtonTransitionFn)(void *);
#define KIRBY_BUTTON_TRANSITION_FN ((KirbyButtonTransitionFn)0x0805BC79u)
typedef uint8_t (*KirbyExplicitTransitionFn)(void *, uint16_t, uint8_t, uint8_t);
#define KIRBY_EXPLICIT_TRANSITION_FN ((KirbyExplicitTransitionFn)0x080551FDu)
typedef uint32_t (*KirbyWarpStarTransitionFn)(void *, uint32_t);
#define KIRBY_WARP_STAR_TRANSITION_FN ((KirbyWarpStarTransitionFn)0x0800C085u)
typedef void (*KirbyMirrorShardUpdateFn)(void *);
#define KIRBY_MIRROR_SHARD_UPDATE_FN ((KirbyMirrorShardUpdateFn)0x0801BE4Du)
typedef uint8_t (*KirbyCannonBoardFn)(void *);
#define KIRBY_CANNON_BOARD_FN ((KirbyCannonBoardFn)0x080510EDu)

static __attribute__((noinline, long_call, section(".aphub"))) uint8_t ap_native_area_for_room(uint16_t room_id) {
    uint32_t info_addr;

    if ((uint32_t)room_id >= KIRBY_ROOM_AREA_INFO_COUNT) {
        return KIRBY_NATIVE_AREA_UNKNOWN;
    }

    info_addr = *(volatile const uint32_t*)(
        KIRBY_ROOM_AREA_INFO_TABLE_ADDR + ((uint32_t)room_id << 2)
    );
    if (info_addr < 0x08000000u || info_addr >= 0x0A000000u) {
        return KIRBY_NATIVE_AREA_UNKNOWN;
    }
    return *(volatile const uint8_t*)(info_addr + KIRBY_ROOM_AREA_INFO_AREA_OFFSET);
}

/* Native room pairs for the return mirrors documented in
 * dev-docs/native-room-wikirby-map.md. Boss and Goal Game exit stars,
 * Tutorial, the Copy Ability Room and in-area mirrors are not gated here. */
static __attribute__((noinline, long_call, section(".aphub"))) uint8_t ap_is_rainbow_return_mirror(
    uint16_t source, uint16_t destination
) {
    switch (((uint32_t)source << 16) | destination) {
        case (120u << 16) | 117u: /* Carrot 5-02 */
        case (122u << 16) | 171u: /* Carrot 5-01 */
        case (144u << 16) | 141u: /* Moonlight 2-16 */
        case (145u << 16) | 143u: /* Moonlight 2-17 */
        case (191u << 16) | 801u: /* Cabbage Hub East */
        case (193u << 16) | 192u: /* Carrot Hub */
        case (290u << 16) | 801u: /* Peppermint Hub East */
        case (310u << 16) | 534u: /* Mustard Chest */
        case (390u << 16) | 590u: /* Mustard Hub */
        case (490u << 16) | 801u: /* Candy Hub */
        case (509u << 16) | 127u: /* Cabbage 3-10 */
        case (512u << 16) | 507u: /* Cabbage 3-04 */
        case (533u << 16) | 534u: /* Mustard 4-15 */
        case (539u << 16) | 538u: /* Mustard 4-01 */
        case (544u << 16) | 543u: /* Mustard 4-06 */
        case (545u << 16) | 141u: /* Mustard 4-07 */
        case (591u << 16) | 194u: /* Cabbage Hub Center */
        case (592u << 16) | 801u: /* Cabbage Hub West */
        case (790u << 16) | 801u: /* Moonlight Hub */
            return 1u;
        default:
            return 0u;
    }
}

static __attribute__((noinline, long_call, section(".aphub"))) uint8_t ap_is_keyed_inter_area_edge(uint16_t source_room, uint16_t destination_room) {
    if (ap_area_keys_enabled() == 0u) return 0u;
    uint8_t source_area = ap_native_area_for_room(source_room);
    uint8_t destination_area = ap_native_area_for_room(destination_room);

    if (destination_area == 0u) {
        return ap_rainbow_route_gate_enabled() && ap_is_rainbow_return_mirror(source_room, destination_room);
    }
    return (uint8_t)(
        source_area != KIRBY_NATIVE_AREA_UNKNOWN
        && source_area != destination_area
        && destination_area >= 1u && destination_area <= 8u
    );
}

/* Native areas 0..8 map to AP areas 1..9. Tutorial and Dimension Mirror remain unkeyed. */
__attribute__((used, noinline, long_call, section(".aphub"))) uint32_t ap_transition_allowed(uint16_t source_room, uint16_t destination_room) {
    uint8_t destination_area;

    if (source_room == 801u && destination_room == 970u) return ap_copy_room_owned();
    if (ap_is_starting_mirror(source_room, destination_room))
        return ap_copy_room_access_owned(AP_STARTING_MIRROR_OWNED) != 0u;


    if (ap_is_keyed_inter_area_edge(source_room, destination_room) == 0u) {
        return 1u;
    }

    destination_area = ap_native_area_for_room(destination_room);
    if (destination_area == 0u) {
        /* Rainbow is guaranteed by the ROM before mailbox initialization.
         * After initialization its separate bit is not part of the earned ledger. */
        if (AP_MAILBOX_INIT_COOKIE != AP_MAILBOX_INIT_COOKIE_VALUE) return 1u;
        return (AP_AREA_KEY_BITFIELD_RUNTIME & AP_RAINBOW_ROUTE_KEY_BIT) != 0u;
    }
    return (ap_progress_owned() >> (destination_area - 1u)) & 1u;
}

/* The ring is ROM-to-client telemetry. Each slot has sequence, packed room IDs,
 * and method/decision/reason so a reconnect can replay only unseen attempts. */
static __attribute__((noinline, long_call, section(".aphub"))) void ap_initialize_transition_event_telemetry(void) {
    uint32_t i;

    if (AP_TRANSITION_EVENT_TELEMETRY_COOKIE == AP_TRANSITION_EVENT_TELEMETRY_COOKIE_VALUE) return;
    AP_TRANSITION_EVENT_COUNTER = 0u;
    AP_TRANSITION_EVENT_LAST_SIGNATURE = 0xFFFFFFFFu;
    AP_TRANSITION_EVENT_LAST_FRAME = 0u;
    for (i = 0u; i < AP_TRANSITION_EVENT_RING_SLOTS; i++) {
        uint32_t slot = AP_TRANSITION_EVENT_RING_BASE + (i * 12u);
        *(volatile uint32_t*)slot = 0u;
        *(volatile uint32_t*)(slot + 4u) = 0u;
        *(volatile uint32_t*)(slot + 8u) = 0u;
    }
    AP_TRANSITION_EVENT_TELEMETRY_COOKIE = AP_TRANSITION_EVENT_TELEMETRY_COOKIE_VALUE;
}

static __attribute__((noinline, long_call, section(".aphub"))) void ap_log_transition_attempt(uint16_t source_room, uint16_t destination_room,
                                      uint8_t method, uint8_t allowed, uint8_t reason) {
    uint32_t signature = ((uint32_t)source_room << 16) | destination_room;
    uint32_t metadata = ((uint32_t)method & 0xFu)
        | (((uint32_t)allowed & 1u) << 4)
        | (((uint32_t)reason & 0xFu) << 5);
    uint32_t frame = AP_FRAME_COUNTER;
    uint32_t counter;
    uint32_t slot;

    ap_initialize_transition_event_telemetry();

    /* Native collision probes can repeat while the player remains at a gate.
     * Suppress identical polling repeats for 30 frames; a retry after moving
     * away or receiving a key is emitted when its signature/decision changes. */
    if (AP_TRANSITION_EVENT_LAST_SIGNATURE == (signature ^ (metadata * 0x9E3779B9u))
        && (frame - AP_TRANSITION_EVENT_LAST_FRAME) < 30u) {
        return;
    }
    AP_TRANSITION_EVENT_LAST_SIGNATURE = signature ^ (metadata * 0x9E3779B9u);
    AP_TRANSITION_EVENT_LAST_FRAME = frame;
    counter = AP_TRANSITION_EVENT_COUNTER + 1u;
    slot = AP_TRANSITION_EVENT_RING_BASE
        + ((counter % AP_TRANSITION_EVENT_RING_SLOTS) * 12u);
    *(volatile uint32_t*)(slot + 4u) = signature;
    *(volatile uint32_t*)(slot + 8u) = metadata;
    *(volatile uint32_t*)slot = counter;
    AP_TRANSITION_EVENT_COUNTER = counter;
}

static __attribute__((noinline, long_call, section(".aphub"))) uint8_t ap_transition_reason(uint16_t source_room, uint16_t destination_room, uint8_t allowed) {
    if (ap_area_keys_enabled() == 0u) return 6u; /* Area Keys disabled for this seed */
    uint8_t source_area = ap_native_area_for_room(source_room);
    uint8_t destination_area = ap_native_area_for_room(destination_room);

    if (source_area == KIRBY_NATIVE_AREA_UNKNOWN || destination_area == KIRBY_NATIVE_AREA_UNKNOWN) return 5u;
    if (source_area == destination_area) return 0u;
    if (destination_area == 0u && (!ap_rainbow_route_gate_enabled()
        || !ap_is_rainbow_return_mirror(source_room, destination_room)))
        return 1u; /* unkeyed Rainbow Route return */
    if (destination_area > 8u) return 4u; /* other unkeyed area */
    return allowed ? 3u : 2u; /* destination key present / missing */
}

static __attribute__((noinline, long_call, section(".aphub"))) uint8_t ap_current_special_tile_destination(void *kirby, uint16_t *out_destination_room,
                                                   uint8_t *out_spawn_x, uint8_t *out_spawn_y) {
    uint32_t kirby_addr = (uint32_t)kirby;
    uint8_t player_id = *(volatile uint8_t*)(kirby_addr + KIRBY_STRUCT_PLAYER_OFFSET);
    int32_t x;
    int32_t y;
    uint32_t level_info_addr;
    uint16_t tile_x;
    uint16_t tile_y;
    uint8_t collision_tile;
    uint8_t *special_tile;

    if (out_destination_room == 0 || player_id >= KIRBY_PLAYER_COUNT_LIMIT) {
        return 0u;
    }

    x = *(volatile int32_t*)(kirby_addr + KIRBY_STRUCT_X_OFFSET);
    y = *(volatile int32_t*)(kirby_addr + KIRBY_STRUCT_Y_OFFSET);
    level_info_addr = KIRBY_LEVEL_INFO_BASE_ADDR + ((uint32_t)player_id * KIRBY_LEVEL_INFO_STRIDE);
    if (x <= *(volatile int32_t*)(level_info_addr + KIRBY_LEVEL_MIN_X_OFFSET)
        || x >= *(volatile int32_t*)(level_info_addr + KIRBY_LEVEL_MAX_X_OFFSET)
        || y <= *(volatile int32_t*)(level_info_addr + KIRBY_LEVEL_MIN_Y_OFFSET)
        || y >= *(volatile int32_t*)(level_info_addr + KIRBY_LEVEL_MAX_Y_OFFSET)) {
        return 0u;
    }

    tile_x = (uint16_t)(x >> 12);
    tile_y = (uint16_t)(y >> 12);
    collision_tile = KIRBY_GET_COLLISION_TILE_FN(player_id, tile_x, tile_y);
    if ((KIRBY_COLLISION_ATTRIBUTES[collision_tile] & 0x4000u) == 0u) {
        return 0u;
    }

    special_tile = (uint8_t*)KIRBY_SPECIAL_TILE_FN(player_id, (uint8_t)tile_x, (uint8_t)tile_y);
    if (special_tile == 0) {
        return 0u;
    }
    *out_destination_room = *(volatile uint16_t*)(special_tile + 0x08u);
    if (out_spawn_x != 0) *out_spawn_x = *(volatile uint8_t*)(special_tile + 0x0Au);
    if (out_spawn_y != 0) *out_spawn_y = *(volatile uint8_t*)(special_tile + 0x0Bu);
    return 1u;
}

static __attribute__((noinline, long_call, section(".aphub"))) uint8_t ap_current_special_tile_is_locked(void *kirby) {
    uint32_t kirby_addr = (uint32_t)kirby;
    uint16_t destination_room;

    if (ap_current_special_tile_destination(kirby, &destination_room, 0, 0) == 0u) {
        return 0u;
    }
    return (uint8_t)(ap_transition_allowed(
        *(volatile uint16_t*)(kirby_addr + KIRBY_STRUCT_ROOM_OFFSET),
        destination_room
    ) == 0u);
}

static __attribute__((noinline, long_call, section(".aphub"))) uint8_t ap_button_transition_destination(void *kirby, uint16_t *out_destination_room) {
    uint32_t kirby_addr = (uint32_t)kirby;
    uint16_t destination_room;
    uint8_t spawn_x, spawn_y;
    uint32_t contact_object_addr;
    int8_t object_destination_room;

    if (ap_current_special_tile_destination(kirby, &destination_room, &spawn_x, &spawn_y) != 0u) {
        *out_destination_room = ap_transition_route_destination(
            *(volatile uint16_t*)(kirby_addr + KIRBY_STRUCT_ROOM_OFFSET),
            destination_room, spawn_x, spawn_y);
        return 1u;
    }

    /*
     * sub_0805BC78 also accepts object-backed doors when unk62 bit 0x10 is
     * set and unk58 is not using the special-tile form. Native code takes the
     * destination from the contacted ObjectBase's signed byte at +0x63.
     */
    if ((*(volatile uint8_t*)(kirby_addr + KIRBY_STRUCT_TRANSITION_KIND_OFFSET) & 0x10u) == 0u
        || (*(volatile uint32_t*)(kirby_addr + KIRBY_STRUCT_COLLISION_OFFSET) & 0x4000u) != 0u) {
        return 0u;
    }

    contact_object_addr = *(volatile uint32_t*)(kirby_addr + KIRBY_STRUCT_CONTACT_OBJECT_OFFSET);
    if (!((contact_object_addr >= KIRBY_EWRAM_START
            && contact_object_addr + KIRBY_OBJECT_DESTINATION_ROOM_OFFSET < KIRBY_EWRAM_END)
        || (contact_object_addr >= KIRBY_IWRAM_START
            && contact_object_addr + KIRBY_OBJECT_DESTINATION_ROOM_OFFSET < KIRBY_IWRAM_END))) {
        return 0u;
    }

    object_destination_room = *(volatile int8_t*)(
        contact_object_addr + KIRBY_OBJECT_DESTINATION_ROOM_OFFSET
    );
    *out_destination_room = (uint16_t)(int16_t)object_destination_room;
    return 1u;
}

/*
 * This replaces the native comparison at 0x0803FE10. Returning zero branches
 * around the transition setup; an allowed transition returns the exact unk58
 * value the overwritten retail instructions would have stored.
 */
__attribute__((used, noinline, long_call, section(".aphub"))) uint32_t ap_prepare_automatic_transition(void *kirby, uint32_t collision_flags) {
    uint32_t kirby_addr = (uint32_t)kirby;
    uint16_t source_room = *(volatile uint16_t*)(kirby_addr + KIRBY_STRUCT_ROOM_OFFSET);
    uint16_t destination_room;

    if (collision_flags == 0x104000u
        && ap_current_special_tile_destination(kirby, &destination_room, 0, 0) != 0u) {
        uint8_t allowed = (uint8_t)ap_transition_allowed(source_room, destination_room);
        ap_log_transition_attempt(source_room, destination_room, 0u, allowed,
                                  ap_transition_reason(source_room, destination_room, allowed));
        if (!allowed) return 0u;
    }
    if (collision_flags != 0x104000u || ap_current_special_tile_is_locked(kirby) != 0u) {
        return 0u;
    }
    return *(volatile uint32_t*)(kirby_addr + KIRBY_STRUCT_COLLISION_OFFSET) | 0x4000u;
}

/*
 * sub_0805BC78 only attempts a transition for a human player holding Up
 * (movementState & 0x40). Ignore idle/non-human helper calls for telemetry,
 * while preserving native behavior and checking real attempts before flags
 * mutate.
 */
__attribute__((used, noinline, long_call, section(".aphub"))) uint8_t ap_on_button_special_transition(void *kirby) {
    uint32_t kirby_addr = (uint32_t)kirby;
    uint16_t destination_room;
    uint16_t source_room = *(volatile uint16_t*)(kirby_addr + KIRBY_STRUCT_ROOM_OFFSET);
    uint8_t player_id = *(volatile uint8_t*)(kirby_addr + KIRBY_STRUCT_PLAYER_OFFSET);
    uint8_t human_player_count = *(volatile uint8_t*)KIRBY_NUM_HUMAN_PLAYERS_ADDR;
    uint16_t movement_state = *(volatile uint16_t*)(kirby_addr + KIRBY_STRUCT_MOVEMENT_STATE_OFFSET);

    if (ap_transition_is_human_up_attempt(player_id, human_player_count, movement_state) == 0u) {
        return KIRBY_BUTTON_TRANSITION_FN(kirby);
    }

    uint8_t has_destination = ap_button_transition_destination(kirby, &destination_room);
    uint8_t allowed = has_destination
        ? (uint8_t)ap_transition_allowed(source_room, destination_room)
        : 1u;

    if (has_destination != 0u) {
        ap_log_transition_attempt(source_room, destination_room,
            (source_room == 743u && destination_room == 824u)
            || (source_room == 824u && destination_room == 743u)
            || (source_room == 170u && destination_room == 619u)
            || (source_room == 619u && destination_room == 170u)
                ? AP_TRANSITION_METHOD_WIND_CHUTE : 5u, allowed,
                                  ap_transition_reason(source_room, destination_room, allowed));
    }
    if (allowed == 0u) {
        *(volatile uint32_t*)(kirby_addr + KIRBY_STRUCT_FLAGS2_OFFSET) |= 0x1000u;
        return 0u;
    }
    return KIRBY_BUTTON_TRANSITION_FN(kirby);
}

__attribute__((used)) uint8_t ap_on_explicit_room_transition(
    void *kirby,
    uint16_t destination_room,
    uint8_t spawn_x,
    uint8_t spawn_y
) {
    uint32_t kirby_addr = (uint32_t)kirby;
    uint16_t source_room = *(volatile uint16_t*)(kirby_addr + KIRBY_STRUCT_ROOM_OFFSET);
    uint16_t tile_destination_room;
    uint8_t tile_spawn_x;
    uint8_t tile_spawn_y;
    uint16_t permission_room = ap_transition_route_destination(
        source_room, destination_room, spawn_x, spawn_y);
    uint8_t allowed = (uint8_t)ap_transition_allowed(source_room, permission_room);

    /* This helper is shared by player transitions and AI/follower state machines.
     * Attribute telemetry only for a human holding Up at the matching source
     * special tile when its native destination and spawn agree exactly. */
    if (ap_transition_is_human_up_attempt(
            *(volatile uint8_t*)(kirby_addr + KIRBY_STRUCT_PLAYER_OFFSET),
            *(volatile uint8_t*)KIRBY_NUM_HUMAN_PLAYERS_ADDR,
            *(volatile uint16_t*)(kirby_addr + KIRBY_STRUCT_MOVEMENT_STATE_OFFSET)) != 0u
        && ap_current_special_tile_destination(
            kirby, &tile_destination_room, &tile_spawn_x, &tile_spawn_y) != 0u
        && ap_transition_matches_special_tile(
            tile_destination_room, tile_spawn_x, tile_spawn_y,
            destination_room, spawn_x, spawn_y) != 0u) {
        ap_log_transition_attempt(source_room, permission_room,
            permission_room != destination_room ? AP_TRANSITION_METHOD_WIND_CHUTE : 0u, allowed,
            ap_transition_reason(source_room, permission_room, allowed));
    }
    if (allowed == 0u) {
        return 0u;
    }
    return KIRBY_EXPLICIT_TRANSITION_FN(kirby, destination_room, spawn_x, spawn_y);
}

/* sub_080510EC is the last eligibility check before sub_08121B70 marks a
 * Kirby as boarded in the cannon passenger bitfield. */
__attribute__((used)) uint8_t ap_on_cannon_board_transition(void *kirby) {
    uint32_t kirby_addr = (uint32_t)kirby;
    uint32_t cannon_addr = *(volatile uint32_t*)(kirby_addr + 0x6Cu);
    uint16_t source_room;
    uint16_t destination_room;
    uint8_t allowed;

    if (!((cannon_addr >= KIRBY_EWRAM_START && cannon_addr <= KIRBY_EWRAM_END - 0xBCu)
        || (cannon_addr >= KIRBY_IWRAM_START && cannon_addr <= KIRBY_IWRAM_END - 0xBCu))) {
        return KIRBY_CANNON_BOARD_FN(kirby);
    }
    source_room = *(volatile uint16_t*)(kirby_addr + KIRBY_STRUCT_ROOM_OFFSET);
    destination_room = *(volatile uint16_t*)(cannon_addr + 0xBAu);
    allowed = (uint8_t)ap_transition_allowed(source_room, destination_room);
    ap_log_transition_attempt(source_room, destination_room, 2u, allowed,
                              ap_transition_reason(source_room, destination_room, allowed));
    if (allowed == 0u) return 0u;
    return KIRBY_CANNON_BOARD_FN(kirby);
}

/* Unknown 83 refreshes pending room/spawn state for every matching Kirby on
 * each callback. Keep its destination-key safety check, but do not report the
 * room-wide state refresh as a player-initiated transition attempt. */
__attribute__((used)) void ap_on_unknown83_transport_update(void *object2) {
    uint32_t object2_addr = (uint32_t)object2;
    uint32_t object_addr = *(volatile uint32_t*)(object2_addr + 0xB0u);
    uint16_t source_room = *(volatile uint16_t*)(object2_addr + KIRBY_STRUCT_ROOM_OFFSET);
    uint16_t destination_room = *(volatile uint16_t*)(object_addr + 0x1Eu);
    uint8_t kirby_count = *(volatile uint8_t*)KIRBY_NUM_KIRBYS_ADDR;
    uint8_t i;

    if (kirby_count > KIRBY_PLAYER_COUNT_LIMIT) kirby_count = KIRBY_PLAYER_COUNT_LIMIT;
    for (i = 0u; i < kirby_count; i++) {
        uint32_t kirby_addr = KIRBY_STRUCTS_ADDR + ((uint32_t)i * KIRBY_STRUCT_STRIDE);
        if (*(volatile uint16_t*)(kirby_addr + KIRBY_STRUCT_ROOM_OFFSET) == source_room) {
            uint8_t allowed = (uint8_t)ap_transition_allowed(source_room, destination_room);
            if (allowed != 0u) {
                *(volatile uint16_t*)(kirby_addr + 0x106u) = destination_room;
                *(volatile int16_t*)(kirby_addr + 0x108u) = *(volatile int16_t*)(object_addr + 0x1Au);
                *(volatile int16_t*)(kirby_addr + 0x10Au) = *(volatile int16_t*)(object_addr + 0x1Cu);
            }
        }
    }
}

/* Mirror Shards use a callback that writes each living Kirby's pending room,
 * then changes the shard callback to its departure animation. Deny before
 * either mutation so a missing-key attempt remains retryable. */
__attribute__((used)) void ap_on_mirror_shard_update(void *shard) {
    uint32_t shard_addr = (uint32_t)shard;
    uint32_t object_addr = *(volatile uint32_t*)(shard_addr + KIRBY_MIRROR_SHARD_OBJECT_PTR_OFFSET);
    uint16_t source_room;
    uint16_t destination_room;
    uint8_t allowed;

    if (object_addr < KIRBY_EWRAM_START
        || object_addr + KIRBY_MIRROR_SHARD_DESTINATION_ROOM_OFFSET + sizeof(uint16_t) > KIRBY_EWRAM_END) {
        KIRBY_MIRROR_SHARD_UPDATE_FN(shard);
        return;
    }
    source_room = *(volatile uint16_t*)(shard_addr + KIRBY_STRUCT_ROOM_OFFSET);
    destination_room = *(volatile uint16_t*)(object_addr + KIRBY_MIRROR_SHARD_DESTINATION_ROOM_OFFSET);
    allowed = (uint8_t)ap_transition_allowed(source_room, destination_room);
    ap_log_transition_attempt(source_room, destination_room, 4u, allowed,
                              ap_transition_reason(source_room, destination_room, allowed));
    if (allowed == 0u) return;
    KIRBY_MIRROR_SHARD_UPDATE_FN(shard);
}

/*
 * Warp stars bypass the normal room-transition functions: sub_0800C084 writes
 * Kirby's destination room and spawn point directly. Guard that shared helper
 * before it performs those writes, then preserve its retail behavior otherwise.
 */
__attribute__((used, noinline, long_call, section(".aphub"))) uint32_t ap_on_warp_star_transition(void *warp_star, uint32_t human_only) {
    uint32_t warp_star_addr = (uint32_t)warp_star;
    uint32_t kirby_addr;
    uint16_t source_room;
    uint16_t destination_room;
    uint32_t object_flags;

    object_flags = *(volatile uint32_t*)(warp_star_addr + 0x08u);
    if ((object_flags & 0x40000u) == 0u) {
        return KIRBY_WARP_STAR_TRANSITION_FN(warp_star, human_only);
    }

    kirby_addr = *(volatile uint32_t*)(warp_star_addr + KIRBY_WARP_STAR_KIRBY_PTR_OFFSET);
    if (!((kirby_addr >= KIRBY_EWRAM_START
            && kirby_addr <= KIRBY_EWRAM_END - KIRBY_STRUCT_ROOM_OFFSET - sizeof(uint16_t))
        || (kirby_addr >= KIRBY_IWRAM_START
            && kirby_addr <= KIRBY_IWRAM_END - KIRBY_STRUCT_ROOM_OFFSET - sizeof(uint16_t)))) {
        return KIRBY_WARP_STAR_TRANSITION_FN(warp_star, human_only);
    }

    source_room = *(volatile uint16_t*)(kirby_addr + KIRBY_STRUCT_ROOM_OFFSET);
    destination_room = *(volatile uint16_t*)(warp_star_addr + KIRBY_WARP_STAR_DESTINATION_ROOM_OFFSET);
    {
        uint8_t allowed = (uint8_t)ap_transition_allowed(source_room, destination_room);
        ap_log_transition_attempt(source_room, destination_room, 1u, allowed,
                                  ap_transition_reason(source_room, destination_room, allowed));
        if (allowed == 0u) {
            return 0u;
        }
    }
    return KIRBY_WARP_STAR_TRANSITION_FN(warp_star, human_only);
}

__attribute__((used)) uint32_t ap_on_query_special_door_state(
    uint16_t room_id,
    uint16_t destination_room,
    uint8_t spawn_x,
    uint8_t spawn_y
) {
    uint16_t permission_room = ap_transition_route_destination(room_id, destination_room, spawn_x, spawn_y);
    if (ap_is_starting_mirror(room_id, permission_room) || ap_is_keyed_inter_area_edge(room_id, permission_room) != 0u) {
        return ap_transition_allowed(room_id, permission_room);
    }

    return KIRBY_SPECIAL_DOOR_VISITED_FN(room_id, destination_room, spawn_x, spawn_y);
}

#include "area_key_objects.inc"

typedef void (*KirbySmallSwitchEffectFn)(void);

/* The AP levers are Chest reward 0x63, not native small switches.  Keep this
 * legacy dispatch wrapper transparent; ordinary small switches remain native. */
__attribute__((used)) void ap_on_small_switch_effect(KirbySmallSwitchEffectFn native_effect) {
    native_effect();
}

typedef void (*KirbyChestFn)(void*);
#define KIRBY_CHEST_INIT_FN ((KirbyChestFn)0x0800BD4Du)
#define KIRBY_CHEST_WAIT_FN ((KirbyChestFn)0x0800AEB1u)
#define KIRBY_CHEST_OPEN_FN ((KirbyChestFn)0x0800BD9Du)
typedef void (*KirbyRoomCounterFn)(uint32_t, uint32_t);
#define KIRBY_ROOM_COUNTER_FN ((KirbyRoomCounterFn)0x080029F5u)
/* gCurLevelInfo[player].unk65E; currentRoom is at +0x5F8, stride 0x668. */
#define KIRBY_LEVEL_INFO_BASE 0x02023530u
#define KIRBY_LEVEL_INFO_STRIDE 0x668u
#define KIRBY_LEVEL_INFO_ROOM_SLOT_OFFSET 0x65Eu

static uint8_t ap_lever_wall_owned(uint32_t chest_obj_ptr) {
    uint8_t chest_id = *(volatile uint8_t*)(chest_obj_ptr + 0xE2u);
    return (uint8_t)((*(volatile uint8_t*)(KIRBY_SMALL_CHEST_FLAGS_ADDR
        + (chest_id >> 3)) >> (chest_id & 7u)) & 1u);
}

/* Object::unk7C runs before the native chest callback, including after the
 * physical lever has been pulled.  Receipt therefore opens a live wall without
 * consuming the lever, and later room loads reapply exactly one contribution. */
static void ap_update_lever_wall(void *chest) {
    uint32_t chest_obj_ptr = (uint32_t)chest;
    volatile uint32_t *applied = (volatile uint32_t*)(chest_obj_ptr + 0xDCu);
    uint8_t player = *(volatile uint8_t*)(chest_obj_ptr + 0x56u);
    uint8_t room_slot;
    /* Server-acknowledged pulls can be restored after this object was loaded.
     * Only retire the waiting state: never replace an active native pull/popup.
     * This changes physical appearance, not wall ownership or its counter. */
    if ((AP_LEVER_ACTIVATION_FLAGS & ap_lever_bit_for_obj(chest_obj_ptr)) != 0u
        && *(KirbyChestFn volatile *)(chest_obj_ptr + 0x78u) == KIRBY_CHEST_WAIT_FN) {
        *(volatile uint8_t*)(chest_obj_ptr + 0x83u) = 3u;
        *(KirbyChestFn volatile *)(chest_obj_ptr + 0x78u) = KIRBY_CHEST_OPEN_FN;
    }
    if (player >= KIRBY_PLAYER_COUNT
        || ap_lever_should_open_wall(ap_lever_wall_owned(chest_obj_ptr), *applied) == 0u) {
        return;
    }
    room_slot = *(volatile uint8_t*)(KIRBY_LEVEL_INFO_BASE
        + (uint32_t)player * KIRBY_LEVEL_INFO_STRIDE + KIRBY_LEVEL_INFO_ROOM_SLOT_OFFSET);
    if (room_slot < KIRBY_PLAYER_COUNT) {
        KIRBY_ROOM_COUNTER_FN(room_slot, 1u);
        *applied = 1u;
    }
}

__attribute__((used)) void ap_on_initialize_chest(void *chest) {
    uint32_t chest_obj_ptr = (uint32_t)chest;
    uint32_t lever_bit = ap_lever_bit_for_obj(chest_obj_ptr);
    uint8_t activated;
    /* Native initialization opens the wall once if its AP-owned chest bit is
     * already set.  It also supplies unchanged behavior for every other chest. */
    KIRBY_CHEST_INIT_FN(chest);
    if (lever_bit == 0u) {
        return;
    }
    activated = (AP_LEVER_ACTIVATION_FLAGS & lever_bit) != 0u;
    *(volatile uint32_t*)(chest_obj_ptr + 0xDCu) = ap_lever_wall_owned(chest_obj_ptr);
    *(volatile uint8_t*)(chest_obj_ptr + 0x83u) = activated ? 3u : 2u;
    *(KirbyChestFn volatile *)(chest_obj_ptr + 0x78u) =
        activated ? KIRBY_CHEST_OPEN_FN : KIRBY_CHEST_WAIT_FN;
    *(KirbyChestFn volatile *)(chest_obj_ptr + 0x7Cu) = ap_update_lever_wall;
}

/* Only BLs in ChestItemPopup's reward callback are redirected here.  r8 is the
 * live popup throughout that verified native function; do not use a current-room
 * guess, which could suppress unrelated chests or another player's room. */
__attribute__((used)) void ap_on_chest_popup_room_counter(uint32_t room_slot, uint32_t amount) {
    register uint32_t popup_obj_ptr asm("r8");
    uint32_t chest_obj_ptr = *(volatile uint32_t*)(popup_obj_ptr + 0x4Cu);
    uint32_t source_ptr = *(volatile uint32_t*)(chest_obj_ptr + 0xB0u);
    uint16_t reward = *(volatile uint16_t*)(chest_obj_ptr + 0xE0u);
    /* The ordinary-reward hook substitutes 0x63 to skip native consumable
     * creation. Unlike actual native levers/collections, ordinary bonuses do
     * not increment this room counter (their template uses unk2=0, unk3=31).
     * Preserve that boundary without suppressing fixed collection rewards. */
    uint8_t suppressed_ordinary = reward == KIRBY_MINOR_CHEST_NO_NATIVE_ITEM
        && ap_is_ap_owned_minor_chest_source(source_ptr);
    if (ap_lever_bit_for_obj(chest_obj_ptr) == 0u && !suppressed_ordinary) {
        KIRBY_ROOM_COUNTER_FN(room_slot, amount);
    }
}

// Hook target for the original boss shard grant call. The game passes the boss's
// shard index in r0 (same value passed to CollectShard(var->unk218) in sub_0801D948).
// Records the AP boss-defeat transport flag for client polling AND replicates the
// native CollectShard behavior (writing KIRBY_SHARD_FLAGS) so
// that the post-cutscene state machine can continue the screen transition correctly.
// AP SHARD_N delivery (ap_apply_item) performs the same KIRBY_SHARD_FLAGS write,
// making native and AP grants idempotent when both occur on the same shard index.
// Fixes Issue #380: native shard state left stale caused a permanent white screen
// after the shard-to-hub-mirror cutscene.
__attribute__((used)) void ap_on_boss_defeat_collect_shard(uint32_t boss_index) {
    ap_set_boss_defeat_flag(boss_index);
    // Replicate CollectShard(boss_index): update native EWRAM shard bitfield and
    // retain it for the post-cutscene transition; native save flow owns persistence.
    if (boss_index < 8u) {
        uint8_t mask = (uint8_t)(1u << boss_index);
        uint8_t new_shard_flags = (uint8_t)(KIRBY_SHARD_FLAGS | mask);
        KIRBY_SHARD_FLAGS = new_shard_flags;
        AP_SHARD_BITFIELD |= (uint32_t)mask;

        // Issue #478: Hold off the per-frame shard scrub so the post-cutscene
        // state machine can read the temporary native write without white-screening.
        AP_SHARD_SCRUB_DELAY = SHARD_BOSS_CUTSCENE_FRAMES;
        AP_BOSS_TEMP_SHARD_BITFIELD |= (uint32_t)mask;
    }
}

static AP_REWARD_FX void ap_note_boss_tomato_for_reward_art(uint32_t boss) {
    if (boss < 8u && ap_copy_room_epoch()
        && ap_reward_art_for_key(AP_REWARD_KEY(AP_REWARD_BOSS, boss)) != AP_REWARD_GEM) {
        (void)ap_boss_item_record_display(AP_HUB_SAVED_CHECKS, AP_HUB_ROM_AUTH, boss);
    }
}

typedef void (*KirbyBossAlreadyOwnedRewardFn)(void *obj2, int16_t x, int16_t y, uint32_t boss_index);
#define KIRBY_BOSS_ALREADY_OWNED_REWARD_FN ((KirbyBossAlreadyOwnedRewardFn)0x08088A39u)

// Hook target for native HasShard==true boss reward path (Issue #754).
// In this branch, the game does not run CollectShard(), so the existing
// CollectShard hook source alone can miss boss-defeat transport signaling.
// Record boss defeat and preserve native behavior by chaining into the
// original reward function.
__attribute__((used)) void ap_on_boss_defeat_already_owned_reward(void *obj2, int16_t x, int16_t y, uint32_t boss_index) {
    ap_set_boss_defeat_flag(boss_index);
    ap_note_boss_tomato_for_reward_art(boss_index);
    KIRBY_BOSS_ALREADY_OWNED_REWARD_FN(obj2, x, y, boss_index);
}

// Hook target for native big chest reward collection. The game passes the area ID
// in r0; record the major chest AP check and intentionally do not unlock the
// native map here. Native maps are granted only when the corresponding AP map
// item is delivered through ap_apply_item().
__attribute__((used)) void ap_on_collect_big_chest(uint32_t area_id) {
    ap_set_major_chest_flag(area_id);

    // Preserve native world-map unlock from the tutorial chest (area_id=0).
    // Area maps (1..9) remain AP-item gated.
    if (area_id == 0u) {
        ap_unlock_area_map(0u);
    }
}

// Hook target for native vitality big chest reward collection. This callsite does
// not pass a stable argument in r0, so read the live chest object from r5 and
// map its roomId to a dedicated vitality-chest transport bit.
__attribute__((used)) void ap_on_collect_vitality_chest(void) {
    register uint32_t chest_obj_ptr asm("r5");
    uint16_t room_id = *(volatile uint16_t*)(chest_obj_ptr + 0x60u);
    ap_set_vitality_chest_flag_for_room(room_id);
    /* CollectVitality interception alone leaves the delayed native popup free
     * to reset max HP and spawn a healing tomato. Defer both to AP delivery,
     * while retaining the popup and its native room-completion increment. */
    *(volatile uint32_t*)(chest_obj_ptr + 0xDCu) = AP_MINOR_CHEST_ITEM_SUPPRESSION_MARKER;
}

// Hook target for native small chest reward collection. The live chest object remains in r5,
// allowing the payload to record the exact ROM source pointer for later client disambiguation
// while preserving the native small-chest persistence write.
__attribute__((used)) void ap_on_collect_small_chest(void) {
    register uint32_t chest_obj_ptr asm("r5");
    ap_record_minor_chest_collection_from_obj_ptr(chest_obj_ptr);
}

/* Called after the native chest popup delay, after open sound/persistence are complete. */
__attribute__((used)) void ap_on_minor_chest_reward_popup(void) {
    register uint32_t popup_obj_ptr asm("r8");
    uint32_t chest_obj_ptr = *(volatile uint32_t*)(popup_obj_ptr + 0x4Cu);
    uint32_t marker = *(volatile uint32_t*)(chest_obj_ptr + 0xDCu);

    if (marker == AP_MINOR_CHEST_ITEM_SUPPRESSION_MARKER) {
        /* The native popup treats 0x63 as a chest with no bonus item. */
        *(volatile uint16_t*)(chest_obj_ptr + 0xE0u) = KIRBY_MINOR_CHEST_NO_NATIVE_ITEM;
        *(volatile uint32_t*)(chest_obj_ptr + 0xDCu) = 0u;
    }
}


typedef void (*KirbyCollectSoundPlayerFn)(uint32_t reward_index);
#define KIRBY_COLLECT_SOUND_PLAYER_FN ((KirbyCollectSoundPlayerFn)0x08019E69u)

typedef void (*KirbyRequestAbilityTransitionFn)(void*, uint32_t);
#define KIRBY_REQUEST_ABILITY_TRANSITION_FN ((KirbyRequestAbilityTransitionFn)0x080547C5u)

typedef void (*KirbyStartAbilityTransitionFn)(void*);
#define KIRBY_START_ABILITY_TRANSITION_FN ((KirbyStartAbilityTransitionFn)0x08054C0Du)

typedef void (*KirbyRefreshPaletteFn)(uint8_t player);
/* Thumb entry for native sub_0803E558(u8), which rebuilds and uploads Kirby's OBJ palette. */
#define KIRBY_REFRESH_PALETTE_FN ((KirbyRefreshPaletteFn)0x0803E559u)

typedef void (*KirbyStartGameFn)(
    uint8_t mode,
    uint8_t arg1,
    const uint16_t *rooms,
    const int32_t *positions,
    const uint32_t *flags
);
/* Thumb entry for native sub_080332BC, which creates the Kirby players. */
#define KIRBY_START_GAME_FN ap_copy_room_start

typedef void (*KirbyGiveInvincibilityFn)(void *kirby, uint16_t duration);
#define KIRBY_GIVE_INVINCIBILITY_FN ((KirbyGiveInvincibilityFn)0x0808324Du)

#define ABILITY_RANDOMIZATION_MODE_SHUFFLED 1u
#define ABILITY_RANDOMIZATION_MODE_COMPLETELY_RANDOM 2u
#define KIRBY_ABILITY_MASK 0x1Fu
#define KIRBY_ABILITY_CHANGE_IS_ABILITY_STAR 0x20u
#define ABILITY_REROLL_SOURCE_KIND_NONE 0u
#define ABILITY_REROLL_SOURCE_KIND_OBJECT2_TYPE 1u
#define ABILITY_REROLL_SOURCE_KIND_NULL_SOURCE_PTR 2u
#define ABILITY_REROLL_SOURCE_KIND_NON_EWRAM_SOURCE_PTR 3u
#define ABILITY_REROLL_SOURCE_KIND_ABILITY_STATUE 4u
#define ENEMY_ABILITY_TABLE_BASE_ADDR 0x35164Eu
#define ENEMY_ABILITY_TABLE_STRIDE 0x18u
#define OBJECT2_TYPE_OFFSET 0x82u

/*
 * Verified against katam/include/kirby.h from the game decompilation.
 * Ability statues bypass sub_080547C4 entirely: they write the requested
 * ability directly to Kirby::transitioningAbility and then call sub_08054C0C.
 */
#define KIRBY_TRANSITIONING_ABILITY_OFFSET 0xDDu

static __attribute__((noinline, long_call, section(".aphub"))) uint32_t ap_mix_u32(uint32_t x) {
    x ^= x >> 16;
    x *= 0x7FEB352Du;
    x ^= x >> 15;
    x *= 0x846CA68Bu;
    x ^= x >> 16;
    return x;
}

static __attribute__((noinline, long_call, section(".aphub"))) uint32_t ap_next_rng_u32(void) {
    uint32_t state = AP_ABILITY_RANDOMIZATION_RNG_STATE;
    if (state == 0u) {
        uint32_t seed_lo = AP_ABILITY_RANDOMIZATION_SEED_LO;
        uint32_t seed_hi = AP_ABILITY_RANDOMIZATION_SEED_HI;
        state = ap_mix_u32(seed_lo ^ (seed_hi * 0x9E3779B9u) ^ 0xA5C39E21u);
        if (state == 0u) {
            state = 0x6D2B79F5u;
        }
    }

    // xorshift32
    state ^= state << 13;
    state ^= state >> 17;
    state ^= state << 5;
    if (state == 0u) {
        state = 0x6D2B79F5u;
    }
    AP_ABILITY_RANDOMIZATION_RNG_STATE = state;
    return state;
}

static __attribute__((noinline, long_call, section(".aphub"))) uint8_t ap_select_random_allowed_ability(uint32_t allowed_mask, uint32_t random_u32) {
    uint8_t ids[32];
    uint32_t count = 0u;
    uint32_t i;
    for (i = 1u; i <= KIRBY_ABILITY_MASK; i++) {
        if ((allowed_mask & (1u << i)) != 0u) {
            ids[count++] = (uint8_t)i;
        }
    }

    if (count == 0u) {
        return 0u;
    }
    return ids[random_u32 % count];
}

static uint8_t ap_is_locked_gated_ability(uint8_t ability_id) {
    uint32_t bit = 1u << (uint32_t)ability_id;
    return ((AP_ABILITY_GATE_MASK & bit) != 0u && (AP_ABILITY_UNLOCK_MASK & bit) == 0u) ? 1u : 0u;
}

static uint8_t ap_select_random_allowed_ability_excluding(
    uint32_t allowed_mask,
    uint32_t excluded_mask,
    uint32_t random_u32
) {
    return ap_select_random_allowed_ability(allowed_mask & ~excluded_mask, random_u32);
}

/* Version zero means an older seed did not write a source inclusion bitmap. */
__attribute__((used, section(".apsourceconfig")))
volatile const uint32_t gApEnemySourceConfig[9] = { AP_ENEMY_SOURCE_CONFIG_LEGACY };

static __attribute__((noinline, long_call, section(".aphub"))) uint8_t ap_enemy_seed_source_allows(
    uint32_t caller_pc, uint32_t source_ptr, uint32_t source_type
) {
    return ap_enemy_source_policy_allows(gApEnemySourceConfig, caller_pc, source_ptr, source_type);
}

static __attribute__((noinline, long_call, section(".aphub"))) uint32_t ap_enemy_restore_shuffled_ability(
    uint32_t mode, uint32_t caller_pc, uint32_t source_ptr,
    uint32_t source_type, uint32_t ability_flags
) {
    return ap_enemy_shuffled_ability_flags(
        gApEnemySourceConfig, mode, caller_pc, source_ptr, source_type, ability_flags,
        (const volatile uint8_t *)(0x08000000u + ENEMY_ABILITY_TABLE_BASE_ADDR)
    );
}

// Hook target for all callsites that request Kirby ability transition.
// In completely-random mode, this rerolls a fresh ability for each request,
// except verified raw Mini recovery stars. Direct statue touches bypass this
// function and are handled by ap_on_start_copy_ability_transition below.
/* Assembly entry snapshots incoming r5/LR before any C prologue or RNG call. */
__attribute__((used, section(".text.ap_request_impl"))) void ap_on_request_copy_ability_transition_c(
    void *kirby, uint32_t ability_flags, uint32_t source_obj_ptr, uint32_t caller_lr
) {
    uint32_t mode = AP_ABILITY_RANDOMIZATION_MODE;
    uint32_t rewritten_flags = ability_flags;
    uint8_t selected_ability = (uint8_t)(ability_flags & KIRBY_ABILITY_MASK);
    uint8_t is_ability_star =
        ((ability_flags & KIRBY_ABILITY_CHANGE_IS_ABILITY_STAR) != 0u) ? 1u : 0u;

    uint32_t caller_pc = (caller_lr & ~1u) - 4u;
    uint8_t source_type = 0xFFu;
    if (ap_enemy_has_verified_source(caller_pc, source_obj_ptr) != 0u) {
        source_type = *(volatile uint8_t*)(source_obj_ptr + OBJECT2_TYPE_OFFSET);
    }

    /* Restore only eligible, verified ordinary enemy grants. Stars, statues,
     * legacy seeds and excluded sources retain their existing semantics.
     * The authoritative ability gate below still applies to the restored ID.
     */
    if (mode == ABILITY_RANDOMIZATION_MODE_SHUFFLED) {
        rewritten_flags = ap_enemy_restore_shuffled_ability(
            mode, caller_pc, source_obj_ptr, source_type, ability_flags
        );
    }

    if (ap_is_mini_star_recovery(caller_pc, source_obj_ptr, ability_flags) == 0u
        && ap_enemy_should_reroll(mode, gApRandomizeMinny, source_type) != 0u
        && ap_enemy_seed_source_allows(caller_pc, source_obj_ptr, source_type) != 0u) {
        uint32_t no_ability_weight = AP_ABILITY_RANDOMIZATION_NO_ABILITY_WEIGHT;
        uint32_t allowed_mask = AP_ABILITY_RANDOMIZATION_ALLOWED_MASK;
        uint32_t random_roll = ap_next_rng_u32();
        uint32_t source_addr = 0u;
        uint32_t source_kind = ABILITY_REROLL_SOURCE_KIND_NONE;
        uint32_t kirby_index = (uint32_t)KIRBY_CURRENT_PLAYER;

        if (is_ability_star != 0u) {
            no_ability_weight = 0u;
        }

        if (no_ability_weight >= 100u) {
            selected_ability = 0u;
        } else if (no_ability_weight > 0u && (random_roll % 100u) < no_ability_weight) {
            selected_ability = 0u;
        } else {
            selected_ability = ap_select_random_allowed_ability(allowed_mask, ap_next_rng_u32());
        }

        if (selected_ability != 0u && ap_is_locked_gated_ability(selected_ability) != 0u) {
            uint32_t locked_mask = AP_ABILITY_GATE_MASK & ~AP_ABILITY_UNLOCK_MASK;
            uint32_t excluded_mask = locked_mask | (1u << (uint32_t)selected_ability);
            selected_ability = ap_select_random_allowed_ability_excluding(
                allowed_mask,
                excluded_mask,
                ap_next_rng_u32()
            );
        }

        rewritten_flags = (ability_flags & ~KIRBY_ABILITY_MASK) | (uint32_t)(selected_ability & KIRBY_ABILITY_MASK);

        if (is_ability_star != 0u) {
            source_kind = ABILITY_REROLL_SOURCE_KIND_ABILITY_STATUE;
            source_addr = (uint32_t)(ability_flags & KIRBY_ABILITY_MASK);
        } else {
            if (source_obj_ptr == 0u) {
                source_kind = ABILITY_REROLL_SOURCE_KIND_NULL_SOURCE_PTR;
            } else if (ap_enemy_source_pointer_is_readable(source_obj_ptr) != 0u) {
                uint8_t source_type = *(volatile uint8_t*)(source_obj_ptr + OBJECT2_TYPE_OFFSET);
                source_kind = ABILITY_REROLL_SOURCE_KIND_OBJECT2_TYPE;
                source_addr = ENEMY_ABILITY_TABLE_BASE_ADDR + ((uint32_t)source_type * ENEMY_ABILITY_TABLE_STRIDE);
            } else {
                source_kind = ABILITY_REROLL_SOURCE_KIND_NON_EWRAM_SOURCE_PTR;
            }
        }

        AP_ABILITY_REROLL_SOURCE_ADDR = source_addr;
        AP_ABILITY_REROLL_ABILITY_ID = (uint32_t)(selected_ability & KIRBY_ABILITY_MASK);
        AP_ABILITY_REROLL_SOURCE_KIND = source_kind;
        AP_ABILITY_REROLL_CALLSITE_PC = caller_pc;
        AP_ABILITY_REROLL_KIRBY_INDEX = kirby_index;
        AP_ABILITY_REROLL_EVENT_COUNTER++;
    }

    selected_ability = (uint8_t)(rewritten_flags & KIRBY_ABILITY_MASK);
    if (selected_ability != 0u && ap_is_locked_gated_ability(selected_ability) != 0u) {
        rewritten_flags = (rewritten_flags & ~KIRBY_ABILITY_MASK);
        selected_ability = 0u;
    }

    // In shuffled mode, ability-star/statue grants do not emit reroll telemetry in the
    // randomization branch above, so emit a compact event here for file-only client logs.
    if (is_ability_star != 0u && mode == ABILITY_RANDOMIZATION_MODE_SHUFFLED) {
        AP_ABILITY_REROLL_SOURCE_ADDR = (uint32_t)(ability_flags & KIRBY_ABILITY_MASK);
        AP_ABILITY_REROLL_ABILITY_ID = (uint32_t)(selected_ability & KIRBY_ABILITY_MASK);
        AP_ABILITY_REROLL_SOURCE_KIND = ABILITY_REROLL_SOURCE_KIND_ABILITY_STATUE;
        AP_ABILITY_REROLL_CALLSITE_PC = 0u;
        AP_ABILITY_REROLL_KIRBY_INDEX = (uint32_t)KIRBY_CURRENT_PLAYER;
        AP_ABILITY_REROLL_EVENT_COUNTER++;
    }

    KIRBY_REQUEST_ABILITY_TRANSITION_FN(kirby, rewritten_flags);
}

/*
 * Hook target for every direct call to sub_08054C0C, the routine that starts
 * Kirby's ability-change animation after Kirby::transitioningAbility has
 * already been populated.
 *
 * Why this second hook is required:
 *   - Enemy and dropped ability-star requests normally flow through
 *     sub_080547C4 and are handled by ap_on_request_copy_ability_transition.
 *   - Ability statues and the Master Sword stand do not call sub_080547C4.
 *     They assign Object2::kirbyAbility directly to Kirby::transitioningAbility
 *     (offset 0xDD) and then call sub_08054C0C.
 *
 * Sanitizing the authoritative pending field here closes that bypass while
 * retaining the game's original animation/state-machine behavior. Only the
 * low five ability-ID bits are cleared; upper transition flags are preserved.
 */
__attribute__((used)) void ap_on_start_copy_ability_transition(void *kirby) {
    volatile uint8_t *transitioning_ability;
    uint32_t caller_lr_snapshot = 0u;
    uint32_t caller_pc;
    uint32_t mode;
    uint8_t pending_flags;
    uint8_t pending_ability;
    uint8_t original_ability;
    uint8_t is_direct_statue;
    uint32_t statue_allowed_mask;

    /*
     * Snapshot lr before any helper call can clobber it.  Because patch_rom.py
     * replaces the caller's BL instruction, this resolves to the original
     * retail callsite rather than a location inside the payload.
     */
    __asm__ volatile("mov %0, lr" : "=r"(caller_lr_snapshot));
    caller_pc = caller_lr_snapshot & ~1u;
    if (caller_pc >= 4u) {
        caller_pc -= 4u;
    }

    if (kirby == (void*)0) {
        return;
    }

    transitioning_ability =
        (volatile uint8_t *)((uintptr_t)kirby + KIRBY_TRANSITIONING_ABILITY_OFFSET);
    pending_flags = *transitioning_ability;
    pending_ability = (uint8_t)(pending_flags & KIRBY_ABILITY_MASK);
    original_ability = pending_ability;
    is_direct_statue = ap_statue_is_direct_touch_callsite(caller_pc);
    mode = is_direct_statue
        && ap_world_statue_mode(*(const volatile uint16_t*)((uintptr_t)kirby + KIRBY_STRUCT_ROOM_OFFSET))
        ? AP_ABILITY_RANDOMIZATION_MODE : 0u;
    statue_allowed_mask = gApAbilityRandomizationStatueAllowedMask;

    /*
     * Issue #875: regular statues write their table-selected ability directly
     * to transitioningAbility and therefore never enter the request hook that
     * performs per-event completely-random rerolls.  Reroll only the verified
     * sub_080AA588 call path, only when statue randomization is enabled for the
     * generated seed, and select directly from the per-seed statue mask after
     * removing currently locked abilities.  That mask is derived from the same
     * normalized pool as the static table writes, so custom whitelist and Minny
     * settings stay aligned. The Copy Ability Room uses the retail table
     * and never rerolls. Statues intentionally ignore the no-ability,
     * passive-enemy, miniboss, and boss-spawn options.
     */
    if (ap_statue_should_reroll(caller_pc, mode, statue_allowed_mask) != 0u) {
        uint32_t candidate_mask = ap_statue_unlocked_candidate_mask(
            statue_allowed_mask,
            AP_ABILITY_GATE_MASK,
            AP_ABILITY_UNLOCK_MASK
        );
        pending_ability = ap_statue_select_ability(
            candidate_mask,
            ap_next_rng_u32()
        );
        pending_flags = ap_statue_replace_ability_bits(
            pending_flags,
            pending_ability
        );
        *transitioning_ability = pending_flags;
    }

    /*
     * Issue #874: this remains the final authority for direct pending-field
     * writers.  It also safely handles shuffled/off modes and a config race
     * where an ability becomes locked after the random selection above.
     */
    {
        /*
         * Encapsulated equivalent of the original source-level contract:
         *   ap_is_locked_gated_ability(pending_ability)
         *   pending_flags & (uint8_t)~KIRBY_ABILITY_MASK
         * The helper is shared with an executable native C contract test.
         */
        uint8_t gated_flags = ap_statue_apply_final_gate(
            pending_flags,
            AP_ABILITY_GATE_MASK,
            AP_ABILITY_UNLOCK_MASK
        );
        if (gated_flags != pending_flags) {
            pending_flags = gated_flags;
            pending_ability = 0u;
            *transitioning_ability = pending_flags;
        }
    }

    /*
     * Direct statues bypass the request hook's telemetry too.  Emit one event
     * per touch in both shuffled and completely-random modes after gating has
     * determined the final ability.  source_addr retains the table-selected
     * input ability so existing client-side statue labels continue to work.
     */
    if (is_direct_statue != 0u
        && statue_allowed_mask != 0u
        && (mode == ABILITY_RANDOMIZATION_MODE_SHUFFLED
            || mode == ABILITY_RANDOMIZATION_MODE_COMPLETELY_RANDOM)) {
        AP_ABILITY_REROLL_SOURCE_ADDR = (uint32_t)original_ability;
        AP_ABILITY_REROLL_ABILITY_ID = (uint32_t)pending_ability;
        AP_ABILITY_REROLL_SOURCE_KIND = ABILITY_REROLL_SOURCE_KIND_ABILITY_STATUE;
        AP_ABILITY_REROLL_CALLSITE_PC = caller_pc;
        AP_ABILITY_REROLL_KIRBY_INDEX = (uint32_t)KIRBY_CURRENT_PLAYER;
        AP_ABILITY_REROLL_EVENT_COUNTER++;
    }

    KIRBY_START_ABILITY_TRANSITION_FN(kirby);
}

/* Native sub_0805C618 is installed as Kirby::stateFn by both ordinary and
 * roulette transitions. Gate immediately before its authoritative ability write,
 * after native roulette or collision state has finished choosing the result. */
__attribute__((used)) void ap_on_commit_copy_ability_transition(void *kirby) {
    volatile uint8_t *pending;
    typedef void (*KirbyCommitAbilityFn)(void*);
    if (kirby == (void*)0) {
        return;
    }
    pending = (volatile uint8_t*)((uintptr_t)kirby + KIRBY_TRANSITIONING_ABILITY_OFFSET);
    *pending = ap_statue_apply_final_gate(*pending, AP_ABILITY_GATE_MASK, AP_ABILITY_UNLOCK_MASK);
    ((KirbyCommitAbilityFn)0x0805C619u)(kirby);
}

/* Native CollectSprayPaint only ORs its ownership bit (katam/src/treasures.c).
 * The physical chest event/persistence was already recorded by the generic hook.
 * Keep unrecognized sources native rather than silently consuming their rewards.
 */
__attribute__((used)) void ap_on_collect_spray_paint_chest(uint32_t reward_index) {
    register uint32_t chest_obj_ptr asm("r5");
    uint32_t source_ptr = *(volatile uint32_t*)(chest_obj_ptr + 0xB0u);
    ap_apply_native_collection_reward(
        &KIRBY_SPRAY_PAINT_FLAGS, reward_index, 14u,
        ap_is_ap_owned_minor_chest_source(source_ptr)
    );
}

/* Reward index 0 remains the existing Sound Player location. Sheet indices
 * 1..10 are AP-owned only when the physical source is in the exact source table.
 */
__attribute__((used)) void ap_on_collect_sound_player_chest(uint32_t reward_index) {
    register uint32_t chest_obj_ptr asm("r5");
    uint32_t source_ptr = *(volatile uint32_t*)(chest_obj_ptr + 0xB0u);
    if (reward_index == 0u) {
        ap_set_sound_player_chest_flag(0u);
        return;
    }

    ap_apply_native_collection_reward(
        &KIRBY_MUSIC_PLAYER_AND_SHEETS_FLAGS, reward_index, 11u,
        ap_is_ap_owned_minor_chest_source(source_ptr)
    );
}

typedef void (*WorldMapUnlockFn)(void);

/* Dispatcher indices 0..9 are non-Hub; 10..24 are the 15 unlock
 * callbacks. Its task index is NOT WorldMapDoor. Identify
 * the selected callback in r0, without reading an undeclared caller register.
 * patch_rom validates this exact USA table before installing the hook. */
static __attribute__((noinline, long_call, section(".aphub")))
void ap_dispatch_hub_unlock_callback(WorldMapUnlockFn unlock_fn) {
    const volatile uint32_t *callbacks = (const volatile uint32_t*)0x0834BDBCu;
    uint32_t door;
    for (door = 1u; door <= 15u; door++) {
        if ((uintptr_t)unlock_fn == callbacks[door - 1u]) {
            ap_set_hub_switch_flag(ap_hub_bits[door]);
            KIRBY_WORLD_MAP_TRANSITION_COMPLETE_FN();
            return;
        }
    }
    if (unlock_fn != 0) unlock_fn();
}

__attribute__((used)) void ap_on_world_map_unlock_call(WorldMapUnlockFn unlock_fn) {
    ap_dispatch_hub_unlock_callback(unlock_fn);
}

/* Format-2 per-seed bounds apply before connecting after native reload. */
__attribute__((used, section(".apconfig.health")))
volatile const uint32_t gApHealthConfigInitial = 0xA9020A06u;

__attribute__((used)) uint32_t ap_initial_health_capacity(void) {
    return ap_vitality_capacity(gApHealthConfigInitial, KIRBY_VITALITY_COUNTER);
}

/* The native collection menu has exactly four icon slots. Clamp the u16
 * before its caller truncates to u8; never modify saved ownership here. */
__attribute__((used)) uint32_t ap_vitality_collection_menu_count(void) {
    return ap_vitality_menu_count(KIRBY_VITALITY_COUNTER);
}

static void ap_sync_active_kirby_health_from_vitality(void) {
    uint8_t player = KIRBY_CURRENT_PLAYER;
    uint32_t kirby_addr = KIRBY_STRUCTS_ADDR + ((uint32_t)player * KIRBY_STRUCT_STRIDE);
    int8_t vitality_total = (int8_t)ap_initial_health_capacity();

    if (*(volatile int8_t*)(kirby_addr + KIRBY_STRUCT_HP_OFFSET) > 0) {
        *(volatile int8_t*)(kirby_addr + KIRBY_STRUCT_HP_OFFSET) = vitality_total;
    }
    *(volatile int8_t*)(kirby_addr + KIRBY_STRUCT_MAX_HP_OFFSET) = vitality_total;
}

/* Only a confirmed owned-paint menu action writes this saved marker. */
#define AP_SAVED_PAINT_CHOICE (*(volatile uint16_t*)0x02038982u)
#define KIRBY_SAVE_ID (*(volatile uint16_t*)0x0203AD48u)
#define KIRBY_PRESSED_KEYS (*(volatile uint16_t*)0x030039FCu)
#define KIRBY_MAIN_FLAGS (*(volatile uint32_t*)0x03002440u)
#define KIRBY_BLD_CONTROL (*(volatile uint16_t*)0x030024E8u)
#define KIRBY_BLD_Y (*(volatile uint16_t*)0x030024ECu)
#define KIRBY_HUD_TASK (*(volatile uint32_t*)0x03000010u)
#define KIRBY_MENU_SELECT_FN ((uint32_t (*)(uint8_t*))0x081447E1u)
#define KIRBY_SAVE_WORLD_FN ((int16_t (*)(uint32_t, uint16_t))0x0800ACD5u)
#define KIRBY_TRANSFORM_BG_PALETTE_FN ((void (*)(const uint16_t*, uint8_t, uint16_t))0x08158335u)
#define KIRBY_LOAD_BG_PALETTE_FN ((void (*)(const uint16_t*, uint8_t, uint16_t))0x0803D21Du)

static uint32_t ap_get_effective_starting_kirby_color(void) {
    uint32_t runtime = AP_MAILBOX_INIT_COOKIE == AP_MAILBOX_INIT_COOKIE_VALUE
        ? AP_STARTING_KIRBY_COLOR_ID : AP_COLOR_INVALID;
    return ap_color_resolve(gApStartingKirbyColorInitial, runtime,
                            AP_SAVED_PAINT_CHOICE, KIRBY_SPRAY_PAINT_FLAGS);
}

/* Runs only at the treasure menu's A-button handler, after native save loading.
 * This also records choosing an owned paint that happens to match an AP default:
 * native code otherwise treats that genuine confirmation as a no-op. */
__attribute__((used)) uint32_t ap_on_treasure_paint_selection(uint8_t *menu) {
    uint32_t index = menu[0x2A];
    if ((KIRBY_PRESSED_KEYS & 1u) && index < 40u && menu[2u + index]
        && KIRBY_SAVE_ID < 3u) {
        uint32_t tag = ((const uint16_t*)0x08386A50u)[index * 2u];
        uint32_t paint = tag - 0x101u;
        if (tag == 0x100u || (ap_native_color_valid(paint)
            && (KIRBY_SPRAY_PAINT_FLAGS & (1u << paint)))) {
            uint16_t saved = tag == 0x100u ? 0u : ap_color_choice_encode(paint);
            if (AP_SAVED_PAINT_CHOICE != saved) {
                AP_SAVED_PAINT_CHOICE = saved;
                /* Use the native serializer for both checksum-protected copies.
                 * Never write raw SRAM or save from the per-frame palette path. */
                KIRBY_SAVE_WORLD_FN(1u, KIRBY_SAVE_ID);
            }
            AP_STARTING_KIRBY_COLOR_APPLIED = 0u;
        }
    }
    return KIRBY_MENU_SELECT_FN(menu);
}

static uint8_t ap_is_player_kirby_ready(uint8_t player) {
    uint32_t kirby_addr;
    uint32_t task_ptr;
    uint8_t ability;

    if (player >= KIRBY_PLAYER_COUNT) {
        return 0u;
    }

    kirby_addr = KIRBY_STRUCTS_ADDR + ((uint32_t)player * KIRBY_STRUCT_STRIDE);
    task_ptr = *(volatile uint32_t*)(kirby_addr + KIRBY_STRUCT_TASK_OFFSET);
    ability = *(volatile uint8_t*)(kirby_addr + KIRBY_STRUCT_ABILITY_OFFSET);

    /* sub_0803E558 indexes ability palette metadata and assumes a live Kirby.
     * Native Task objects are allocated in IWRAM. Waiting for both conditions
     * avoids calling the palette loader from menus or before CreateKirby. */
    if (task_ptr < 0x03000000u || task_ptr >= 0x03008000u) {
        return 0u;
    }
    if (ability > KIRBY_ABILITY_MASK) {
        return 0u;
    }
    return 1u;
}

/*
 * Hook for the two single-player calls to sub_080332BC in code_08123950.c.
 * The seed color is installed before CreateKirby copies the player-color table,
 * so the first visible gameplay frame uses the configured palette.
 */
__attribute__((used)) void ap_on_start_single_player_game(
    uint8_t mode,
    uint8_t arg1,
    const uint16_t *rooms,
    const int32_t *positions,
    const uint32_t *flags
) {
    uint32_t desired_color = ap_native_color(ap_get_effective_starting_kirby_color());
    KIRBY_SELECTED_COLOR = (int16_t)desired_color;
    KIRBY_PLAYER_COLOR_TABLE[KIRBY_STARTING_COLOR_PLAYER] = (uint8_t)desired_color;
    AP_STARTING_KIRBY_COLOR_APPLIED = AP_COLOR_STARTUP;

    AP_VISIT_PENDING->epoch = 0u;
    AP_VISUAL_MAILBOX->request = AP_VISUAL_MAILBOX->result = 0u;
    AP_VISUAL_MAILBOX->ready = AP_VISUAL_MAILBOX->active = 0u;
    KIRBY_START_GAME_FN(mode, arg1, rooms, positions, flags);
    AP_STARTING_KIRBY_COLOR_APPLIED = 0u;
}

static void ap_apply_starting_kirby_color_config(void) {
    uint32_t desired_color;
    uint32_t kirby_addr;
    uint32_t hud = KIRBY_HUD_TASK;
    if (AP_STARTING_KIRBY_COLOR_APPLIED != 0u) return;
    /* A live gameplay HUD owns BG bank 15. Menu tasks can reuse its memory.
     * RGB transformation flags can remain enabled throughout normal gameplay;
     * use the native loaders instead of treating those flags as an active fade. */
    if (hud < 0x03000000u || hud >= 0x03007FECu || (hud & 3u)
        || *(volatile uint32_t*)(hud + 8u) != 0x08033B9Du
        || ((KIRBY_BLD_CONTROL & 0x80u) && KIRBY_BLD_Y != 0u)
        || KIRBY_CURRENT_PLAYER != KIRBY_STARTING_COLOR_PLAYER
        || (DEMO_PLAYBACK_FLAGS & 0x12u)
        || !ap_is_player_kirby_ready(KIRBY_STARTING_COLOR_PLAYER)) return;
    desired_color = ap_native_color(ap_get_effective_starting_kirby_color());
    kirby_addr = KIRBY_STRUCTS_ADDR;
    KIRBY_SELECTED_COLOR = (int16_t)desired_color;
    KIRBY_PLAYER_COLOR_TABLE[KIRBY_STARTING_COLOR_PLAYER] = (uint8_t)desired_color;
    *(volatile uint8_t*)(kirby_addr + KIRBY_STRUCT_COLOR_OFFSET) = (uint8_t)desired_color;
    KIRBY_REFRESH_PALETTE_FN(KIRBY_STARTING_COLOR_PLAYER);
    KIRBY_LOAD_BG_PALETTE_FN((const uint16_t*)(0x0834BB20u + desired_color * 32u), 0xF0u, 16u);
    if (KIRBY_MAIN_FLAGS & 0x10000u) {
        /* The raw loader also preserves the resolved HUD row in its backup. */
        KIRBY_TRANSFORM_BG_PALETTE_FN((const uint16_t*)0x02022300u, 0xF0u, 16u);
    }
    KIRBY_MAIN_FLAGS |= 1u; /* Native VBlank uploader consumes the BG sync flag. */
    AP_STARTING_KIRBY_COLOR_APPLIED = 1u;
}

static uint32_t ap_get_active_kirby_addr(void) {
    return KIRBY_STRUCTS_ADDR + ((uint32_t)KIRBY_CURRENT_PLAYER * KIRBY_STRUCT_STRIDE);
}

/* Clear states are saved progression, not permanent ending-screen markers.
 * CreateKirby installs this callback and player-index payload; TaskDestroy
 * replaces the callback before freeing the task. Require live identity before
 * admitting post-clear gameplay, rather than trusting stale room/HP fields. */
static __attribute__((noinline, long_call, section(".aphub"))) uint8_t ap_runtime_ai_allows_gameplay(void) {
    uint32_t ai = AI_KIRBY_STATE;
    uint32_t kirby, task, payload;
    uint16_t flags, offset;
    if (ai == AI_STATE_NORMAL) return 1u;
    if ((ai != AI_STATE_DARK_MIND_CLEAR && ai != AI_STATE_FULL_CLEAR)
        || (DEMO_PLAYBACK_FLAGS & 0x70u) != 0u /* Replay credits retain a live Kirby task. */
        || KIRBY_CURRENT_PLAYER >= KIRBY_PLAYER_COUNT) return 0u;
    kirby = ap_get_active_kirby_addr();
    task = *(volatile uint32_t*)(kirby + KIRBY_STRUCT_TASK_OFFSET);
    if (task < 0x03000000u || task > 0x03007FECu || (task & 3u)
        || *(volatile uint32_t*)(task + 8u) != 0x0803EE19u
        || *(volatile uint16_t*)(task + 0x10u) != 0x3000u
        || *(volatile uint16_t*)(task + 2u) == 0u
        || *(volatile uint16_t*)(task + 4u) == 0u) return 0u;
    flags = *(volatile uint16_t*)(task + 0x12u);
    offset = *(volatile uint16_t*)(task + 6u);
    if ((flags & 1u) || !offset) return 0u;
    if (flags & 0x10u) payload = 0x02000000u + ((uint32_t)offset << 2);
    else {
        if (offset > 0x7FFFu) return 0u;
        payload = 0x03000000u + offset;
    }
    return *(volatile uint8_t*)payload == KIRBY_CURRENT_PLAYER
        && KIRBY_CURRENT_ROOM != 0u
        && *(volatile uint16_t*)(kirby + KIRBY_STRUCT_ROOM_OFFSET) == KIRBY_CURRENT_ROOM;
}

static void ap_grant_heal_amount(uint8_t amount) {
    uint32_t kirby_addr = ap_get_active_kirby_addr();
    int8_t hp = *(volatile int8_t*)(kirby_addr + KIRBY_STRUCT_HP_OFFSET);
    int8_t max_hp = *(volatile int8_t*)(kirby_addr + KIRBY_STRUCT_MAX_HP_OFFSET);

    // Preserve dead/invalid negative HP states; mailbox healing items should not revive Kirby.
    if (hp <= 0) {
        return;
    }

    if (hp > max_hp) {
        *(volatile int8_t*)(kirby_addr + KIRBY_STRUCT_HP_OFFSET) = max_hp;
        return;
    }

    if (hp < max_hp) {
        uint16_t healed_hp = (uint16_t)((uint8_t)hp + (uint16_t)amount);
        if (healed_hp > (uint16_t)((uint8_t)max_hp)) {
            healed_hp = (uint16_t)((uint8_t)max_hp);
        }
        *(volatile int8_t*)(kirby_addr + KIRBY_STRUCT_HP_OFFSET) = (int8_t)healed_hp;
    }
}

static void ap_grant_small_food(void) {
    ap_grant_heal_amount(1u);
}

static void ap_grant_energy_drink(void) {
    ap_grant_heal_amount(2u);
}

static void ap_grant_hunk_of_meat(void) {
    ap_grant_heal_amount(3u);
}

static uint32_t ap_grant_battery(void) {
    return ap_battery_grant(ap_get_active_kirby_addr());
}

static void ap_grant_max_tomato(void) {
    uint32_t kirby_addr = ap_get_active_kirby_addr();
    int8_t hp = *(volatile int8_t*)(kirby_addr + KIRBY_STRUCT_HP_OFFSET);
    int8_t max_hp = *(volatile int8_t*)(kirby_addr + KIRBY_STRUCT_MAX_HP_OFFSET);

    // Preserve dead/invalid negative HP states; mailbox healing items should not revive Kirby.
    if (hp <= 0) {
        return;
    }

    *(volatile int8_t*)(kirby_addr + KIRBY_STRUCT_HP_OFFSET) = max_hp;
}

/* Preserve the offer until native Candy can actually create its effect task.
 * In forbidden rooms native silently rejects it; an existing task is not refreshed.
 * This is also the final guard against room/death changes after client preflight. */
static __attribute__((noinline, long_call, section(".aphub"))) uint8_t ap_invincibility_candy_ready(void) {
    uint32_t kirby_addr;
    uint32_t task;
    if (KIRBY_CURRENT_PLAYER >= KIRBY_PLAYER_COUNT || !ap_runtime_ai_allows_gameplay()
        || (DEMO_PLAYBACK_FLAGS & 0x16u) != 0u) return 0u;
    kirby_addr = ap_get_active_kirby_addr();
    task = *(volatile uint32_t*)(kirby_addr + KIRBY_STRUCT_TASK_OFFSET);
    return task >= 0x03000000u && task < 0x03008000u && (task & 3u) == 0u
        && *(volatile int8_t*)(kirby_addr + KIRBY_STRUCT_HP_OFFSET) > 0
        && (*(volatile uint32_t*)(kirby_addr + 0xCu) & 0x40u) == 0u
        && ap_candy_room_supported(*(volatile uint16_t*)(kirby_addr + KIRBY_STRUCT_ROOM_OFFSET),
                                   (const volatile uint16_t*)0x0835105Cu);
}

static void ap_grant_invincibility_candy(void) {
    uint32_t kirby_addr = ap_get_active_kirby_addr();

    *(volatile uint8_t*)(kirby_addr + KIRBY_STRUCT_INVINCIBILITY_RESET_OFFSET) = 0u;
    *(volatile uint8_t*)(kirby_addr + KIRBY_STRUCT_INVINCIBILITY_KIND_OFFSET) = KIRBY_INVINCIBILITY_KIND;
    *(volatile uint8_t*)(kirby_addr + KIRBY_STRUCT_INVINCIBILITY_STATE_OFFSET) = KIRBY_EFFECT_ACTIVE_COUNTDOWN;
    *(volatile uint16_t*)(kirby_addr + KIRBY_STRUCT_INVINCIBILITY_DURATION_OFFSET) = KIRBY_INVINCIBILITY_DURATION;
    KIRBY_GIVE_INVINCIBILITY_FN((void*)kirby_addr, KIRBY_INVINCIBILITY_DURATION);
}

static void ap_grant_vitality_counter(void) {
    uint16_t previous = KIRBY_VITALITY_COUNTER;
    uint16_t confirmed_count = ap_vitality_partial_count(
        gApHealthConfigInitial, AP_DELIVERED_VITALITY_ITEM_BITS, previous);
    KIRBY_VITALITY_COUNTER = confirmed_count;
    /* Partial replay retains saved ownership and never heals a reconstructed
     * receipt. Complete authenticated history can correct an inflated save. */
    if (confirmed_count > previous) {
        ap_sync_active_kirby_health_from_vitality();
    }
}

static void ap_grant_lives(uint8_t amount) {
    uint8_t lives = KIRBY_LIVES;

    if (lives >= 255u) {
        return;
    }

    if ((uint16_t)lives + amount > 255u) {
        KIRBY_LIVES = 255u;
        return;
    }

    KIRBY_LIVES = (uint8_t)(lives + amount);
}

// --- Trap effect helpers ---

static uint8_t ap_one_hit_mode_runtime_enabled(void) {
    uint32_t mode = AP_ONE_HIT_MODE_RUNTIME;
    if (mode == 0xFFFFFFFFu) {
        return 0u;
    }
    return mode != 0u;
}

static uint8_t ap_no_extra_lives_runtime_enabled(void) {
    uint32_t enabled = AP_NO_EXTRA_LIVES_RUNTIME;
    if (enabled == 0xFFFFFFFFu) {
        return 0u;
    }
    return enabled != 0u;
}

static void ap_trap_health_down(void) {
    if (ap_one_hit_mode_runtime_enabled() != 0u) {
        return;
    }

    uint32_t kirby_addr = ap_get_active_kirby_addr();
    int8_t hp = *(volatile int8_t*)(kirby_addr + KIRBY_STRUCT_HP_OFFSET);
    if (hp <= 1) {
        return;
    }
    int8_t new_hp = (int8_t)((uint8_t)hp - 2u);
    if (new_hp < 1) {
        new_hp = 1;
    }
    *(volatile int8_t*)(kirby_addr + KIRBY_STRUCT_HP_OFFSET) = new_hp;
}

static void ap_trap_life_down(void) {
    if (ap_no_extra_lives_runtime_enabled() != 0u) {
        return;
    }

    uint8_t lives = KIRBY_LIVES;
    if (lives == 0u) {
        return;
    }
    KIRBY_LIVES = (uint8_t)(lives - 1u);
}

static void ap_trap_lives_wipeout(void) {
    KIRBY_LIVES = 0u;
}

static void ap_trap_bomb(void) {
    uint32_t kirby_addr = ap_get_active_kirby_addr();
    *(volatile int8_t*)(kirby_addr + KIRBY_STRUCT_HP_OFFSET) = 0;
}

static void ap_trap_battery_drain(void) {
    uint32_t kirby_addr = ap_get_active_kirby_addr();
    ap_battery_native(kirby_addr + KIRBY_STRUCT_BATTERY_OFFSET, AP_BATTERY_DRAIN);
}

/* The native input decoder reads gHeldKeys and derives Kirby's press edges.
 * Keep native room/boss/ability eligibility and cancellation authoritative. */
#define HUB_HELD_KEYS (*(volatile uint16_t *)0x03002E90u)
#define HUB_STATE_FN (*(volatile uint32_t *)(KIRBY_STRUCTS_ADDR + 0x78u))
#define HUB_CALL_STATE 0x0805701Du
#define HUB_CHARGE_STATE 0x080573D1u
#define HUB_TAKEOFF_STATE 0x080575D9u
#define HUB_EXT __attribute__((noinline, long_call, section(".aphub")))

static HUB_EXT uint8_t ap_hub_pending_ready(void) {
    uint32_t hud;
    uint16_t animation = *(volatile uint16_t *)(KIRBY_STRUCTS_ADDR + 0xD4u);
    if (AP_MAILBOX_INIT_COOKIE != AP_MAILBOX_INIT_COOKIE_VALUE
        || AP_IN_FLAG != 1u
        || AP_IN_ITEM_ID != KIRBY_ITEM_ID_BASE_OFFSET + 300u) return 0u;
    if (!ap_runtime_ai_allows_gameplay()
        || (DEMO_PLAYBACK_FLAGS & 0x16u) != 0u
        || (*(volatile uint32_t *)0x03002440u & 0x800u) != 0u
        || KIRBY_CURRENT_PLAYER != 0u
        || *(volatile uint8_t *)0x0203AD30u != 1u) return 0u;
    hud = KIRBY_HUD_TASK;
    if (hud < 0x03000000u || hud >= 0x03007FECu || (hud & 3u)
        || *(volatile uint32_t *)(hud + 8u) != 0x08033B9Du) return 0u;
    if ((*(volatile uint8_t *)0x03000514u & 0x11u) != 0u
        || *(volatile uint32_t *)(KIRBY_STRUCTS_ADDR + KIRBY_STRUCT_TASK_OFFSET) == 0u
        || *(volatile int8_t *)(KIRBY_STRUCTS_ADDR + KIRBY_STRUCT_HP_OFFSET) <= 0
        || animation == 39u || animation > 122u
        || *(volatile uint32_t *)(KIRBY_STRUCTS_ADDR + 0x110u) != 0u) return 0u;
    return 1u;
}

static HUB_EXT uint8_t ap_hub_idle_ready(void) {
    return (*(volatile uint32_t *)(KIRBY_STRUCTS_ADDR + 8u) & 0x3800B00u) == 0u
        && (*(volatile uint32_t *)(KIRBY_STRUCTS_ADDR + 0xCu) & 0x1000u) != 0u;
}

/* US retail m4a player/song tables. Progression uses the first native
 * effects player; useful/filler and trap use the second. Never start an AP
 * cue over a native effect already using its player. */
#define AP_CUE_MPLAY_TABLE ((const uint32_t *)0x08B59EA0u)
#define AP_CUE_SONG_TABLE ((const uint32_t *)0x08B59ED0u)
#define AP_CUE_SONG_START ((void (*)(uint16_t))0x0815011Du)

static HUB_EXT uint8_t ap_cue_mplay_busy(uint32_t player) {
    const volatile uint32_t *info = (const volatile uint32_t *)AP_CUE_MPLAY_TABLE[player * 3u];
    const volatile uint8_t *track = (const volatile uint8_t *)AP_CUE_MPLAY_TABLE[player * 3u + 1u];
    uint32_t status = info[1];
    /* MPlayStart clears the status before its first mixer tick; track
     * flags still show that a native sound is armed in that interval. */
    return !(status & 0x80000000u) && ((status & 0xFFFFu) || (*track & 0x40u));
}

static HUB_EXT uint8_t ap_receipt_cue_gameplay_ready(void) {
    uint32_t kirby = KIRBY_STRUCTS_ADDR, hud = KIRBY_HUD_TASK;
    uint16_t animation = *(volatile uint16_t *)(kirby + 0xD4u);
    return AP_MAILBOX_INIT_COOKIE == AP_MAILBOX_INIT_COOKIE_VALUE
        && ap_runtime_ai_allows_gameplay()
        && !(DEMO_PLAYBACK_FLAGS & 0x76u)
        && !(KIRBY_MAIN_FLAGS & 0x4C00u)
        && *(volatile uint32_t *)0x0203AD4Cu == 0u /* gInGameInterludeTask */
        && KIRBY_CURRENT_PLAYER == 0u && *(volatile uint8_t *)0x0203AD30u == 1u
        && hud >= 0x03000000u && hud < 0x03007FECu && !(hud & 3u)
        && *(volatile uint32_t *)(hud + 8u) == 0x08033B9Du
        && !(*(volatile uint8_t *)0x03000514u & 0x11u)
        && *(volatile uint32_t *)(kirby + KIRBY_STRUCT_TASK_OFFSET) != 0u
        && *(volatile int8_t *)(kirby + KIRBY_STRUCT_HP_OFFSET) > 0
        && KIRBY_CURRENT_ROOM != 0u
        && *(volatile uint16_t *)(kirby + KIRBY_STRUCT_ROOM_OFFSET) == KIRBY_CURRENT_ROOM
        && animation != 39u && animation <= 122u
        && !(*(volatile uint8_t *)(kirby + 0x62u) & 0x10u) /* native pending doorway */
        && *(volatile uint32_t *)(kirby + 0x110u) == 0u;
}

/* APN1: receipt 3860301 is implemented by this payload. The client checks the
 * marker before reserving the trap so an older ROM cannot strand a receipt. */
__attribute__((used, section(".apnarcolepsyinfo")))
const uint8_t gApNarcolepsyInfo[4] = {'A', 'P', 'N', '1'};

#define AP_NARCOLEPSY_ITEM (KIRBY_ITEM_ID_BASE_OFFSET + 301u)
#define KIRBY_ABILITY_SLEEP 11u
#define KIRBY_ABILITY_UFO 14u
#define KIRBY_ABILITY_MINI 23u
#define KIRBY_ABILITY_MASTER 26u
#define KIRBY_NATIVE_GROUNDED_IDLE 0x0803FF65u
#define KIRBY_NATIVE_GROUNDED_WALK 0x080411E9u
#define KIRBY_NATIVE_GROUNDED_RUN  0x08041B09u
#define KIRBY_NATIVE_UFO_HOVER 0x0806A85Du

static HUB_EXT uint8_t ap_trap_narcolepsy(void) {
    uint32_t kirby = KIRBY_STRUCTS_ADDR; /* Only the local, human-controlled Kirby. */
    uint8_t ability, stage;
    uint32_t state, collision;
    if (!ap_receipt_cue_gameplay_ready()) return 0u;

    ability = *(volatile uint8_t *)(kirby + KIRBY_STRUCT_ABILITY_OFFSET);
    if (ability == KIRBY_ABILITY_SLEEP) return 1u; /* Don't reset a native nap. */

    state = *(volatile uint32_t *)(kirby + 0x78u);
    collision = *(volatile uint32_t *)(kirby + KIRBY_STRUCT_COLLISION_OFFSET);
    stage = *(volatile uint8_t *)(kirby + KIRBY_STRUCT_TRANSITION_KIND_OFFSET);
    if ((collision & 2u) /* Not underwater. */
            || (*(volatile uint32_t *)(kirby + 8u) & 0x03800B80u)
            || *(volatile uint8_t *)(kirby + KIRBY_TRANSITIONING_ABILITY_OFFSET)) return 0u;

    if (ability == KIRBY_ABILITY_UFO) {
        /* UFO never enters the grounded callbacks. Its stock hover controller
         * decelerates to zero when released. Refuse active flight, hazardous
         * tiles and attack states rather than waiting for UFO to be discarded. */
        if (state != KIRBY_NATIVE_UFO_HOVER
                || *(volatile int16_t *)(kirby + 0x50u) != 0 /* xspeed */
                || *(volatile int16_t *)(kirby + 0x52u) != 0 /* yspeed */
                || (*(volatile uint16_t *)(kirby + KIRBY_STRUCT_MOVEMENT_STATE_OFFSET) & 0xF3u)
                || (collision & 0x2400u)) return 0u;
    } else if (!(stage & 4u) /* Ground contact. */
            || (state != KIRBY_NATIVE_GROUNDED_IDLE && state != KIRBY_NATIVE_GROUNDED_WALK
                && state != KIRBY_NATIVE_GROUNDED_RUN)) return 0u;

    /* The retail tile predicate distinguishes Mini passages from normal space.
     * Do not expand the body while it is still inside a small passage. */
    if (ability == KIRBY_ABILITY_MINI && (collision & 0x400u)) return 0u;
    /* Do not take away the Sword during the Dimension Mirror boss sequence. */
    if (ability == KIRBY_ABILITY_MASTER && KIRBY_CURRENT_ROOM >= 909u
            && KIRBY_CURRENT_ROOM <= 919u) return 0u;

    /* Enter the retail transition directly, like a statue, without going
     * through the copy-source RNG/unlock hooks. A new temporary Sleep effect
     * replaces the old ability; no star creation or ownership change occurs. */
    *(volatile uint8_t *)(kirby + KIRBY_TRANSITIONING_ABILITY_OFFSET) = KIRBY_ABILITY_SLEEP;
    KIRBY_START_ABILITY_TRANSITION_FN((void *)kirby);
    if (*(volatile uint32_t *)(kirby + 0x78u)
            != (uint32_t)(uintptr_t)ap_on_commit_copy_ability_transition) {
        *(volatile uint8_t *)(kirby + KIRBY_TRANSITIONING_ABILITY_OFFSET) = 0u;
        return 0u; /* No confirmed native transition; leave the mailbox pending. */
    }
    /* Bypass the final ownership gate for this one actor/state only. Nothing
     * is unlocked: native commit replaces this callback, and interruption or
     * death discards it together with any ordinary ability transition. */
    *(volatile uint32_t *)(kirby + 0x78u) = 0x0805C619u;
    /* Native Master loss releases the global uniqueness latch. */
    if (ability == KIRBY_ABILITY_MASTER) *(volatile uint8_t *)0x0203AD34u = 0u;
    return 1u;
}

__attribute__((used, section(".aprandomteleportinfo")))
const uint8_t gApRandomTeleportInfo[4] = {'A', 'P', 'R', '2'};

#define AP_RANDOM_TELEPORT_ITEM (KIRBY_ITEM_ID_BASE_OFFSET + 302u)
#define AP_RANDOM_TELEPORT_NONCE (*(volatile uint32_t *)AP_RANDOM_TELEPORT_MAILBOX_ADDRESS)
#define AP_RANDOM_TELEPORT_EPOCH (*(volatile uint32_t *)(AP_RANDOM_TELEPORT_MAILBOX_ADDRESS + 4u))

struct ApTeleportLanding {
    uint16_t room;
    uint8_t x, y, connection;
};

/* Exact reciprocal Rainbow Route native mirrors. Each remote route is a
 * Central Circle edge and has a return under the same owned connection.
 * Never use physical visit bits, ability reachability guesses or all-items logic. */
__attribute__((section(".aphubteleportdata")))
static const struct ApTeleportLanding AP_TELEPORT_LANDINGS[] = {
    {190u, 9u, 3u, 1u},  /* East */
    {194u, 9u, 3u, 3u},  /* South */
    {192u, 13u, 3u, 5u}, /* West */
    {AP_RANDOM_TELEPORT_CENTRAL_ROOM, 24u, 12u, 0u}, /* Central Circle, stock return from East */
};

static HUB_EXT uint8_t ap_trap_random_teleport(void) {
    uint32_t kirby = KIRBY_STRUCTS_ADDR, owned = AP_HUB_CONNECTION_ITEM_MASK;
    uint32_t request = AP_RANDOM_TELEPORT_NONCE;
    uint32_t nonce = request & 0x1FFFFFFFu;
    uint16_t source;
    uint8_t ability, area, count = 0u, eligible[3];
    const struct ApTeleportLanding *target;
    uint32_t epoch = ap_copy_room_epoch();
    if (!epoch || AP_RANDOM_TELEPORT_EPOCH != epoch) {
        /* Adventure file load/restart invalidates this offer. Do not turn a
         * file boundary into an ACK: the client retains its durable evidence. */
        AP_RANDOM_TELEPORT_NONCE = AP_RANDOM_TELEPORT_EPOCH = 0u;
        AP_IN_FLAG = 0u;
        return 0u;
    }
    if (owned == AP_HUB_CONNECTION_ITEM_MASK_UNINITIALIZED || !nonce
            || !ap_receipt_cue_gameplay_ready()) return 0u;
    source = KIRBY_CURRENT_ROOM;
    ability = *(volatile uint8_t *)(kirby + KIRBY_STRUCT_ABILITY_OFFSET);
    /* Match ordinary native retreat availability outside Central Circle.
     * Do not interrupt ability-specific bodies/scripts or strand their egress. */
    area = ap_native_area_for_room(source);
    if (area >= 9u
            || !ap_random_teleport_source_supported(source, area,
                  *(volatile const uint16_t *)(0x089331ACu + 40u * source + 0x12u))
            || ability == KIRBY_ABILITY_SLEEP || ability == KIRBY_ABILITY_MINI
            || ability == KIRBY_ABILITY_MASTER || ability == KIRBY_ABILITY_UFO) return 1u;
    if (*(volatile uint32_t *)(kirby + 0x78u) != KIRBY_NATIVE_GROUNDED_IDLE
            || !(*(volatile uint8_t *)(kirby + KIRBY_STRUCT_TRANSITION_KIND_OFFSET) & 4u)
            || (*(volatile uint32_t *)(kirby + KIRBY_STRUCT_COLLISION_OFFSET) & 0x6402u)
            || (*(volatile uint32_t *)(kirby + 8u) & 0x03800B80u)
            || *(volatile uint8_t *)(kirby + KIRBY_TRANSITIONING_ABILITY_OFFSET)
            || HUB_HELD_KEYS != 0u) return 0u;

    /* Prefer destinations that differ from the ordinary Hub Teleport Trap. */
    for (uint8_t i = 0u; i < 3u; ++i) {
        const struct ApTeleportLanding *landing = &AP_TELEPORT_LANDINGS[i];
        if (landing->room != source && (request & (1u << (29u + i)))
                && (owned & (1u << landing->connection))
                && ap_transition_allowed(source, landing->room)) {
            const volatile uint32_t *native = ap_get_hub_unlock_entry(ap_hub_props[landing->connection]);
            if (native != 0 && *native == 1u) eligible[count++] = i;
        }
    }
    if (count) {
        /* A stable per-receipt pseudorandom ordinal among eligible rooms. */
        target = &AP_TELEPORT_LANDINGS[eligible[(nonce - 1u) % count]];
    } else {
        if (source == AP_RANDOM_TELEPORT_CENTRAL_ROOM) return 1u; /* No distinct safe destination. */
        target = &AP_TELEPORT_LANDINGS[3];
    }
    return ap_on_explicit_room_transition((void *)kirby, target->room, target->x, target->y);
}

static HUB_EXT void ap_receipt_cue_poll(void) {
    uint32_t ready = 0u, request, active;
    if (AP_MAILBOX_INIT_COOKIE != AP_MAILBOX_INIT_COOKIE_VALUE) return;
    request = AP_CUE_REQUEST;
    active = AP_CUE_ACTIVE;
    if (active && (active > 2u || !ap_cue_mplay_busy(active))) AP_CUE_ACTIVE = active = 0u;
    if (ap_receipt_cue_gameplay_ready() && !active) {
        if (!ap_cue_mplay_busy(1u)) ready |= (1u << 1);
        if (!ap_cue_mplay_busy(2u)) ready |= (1u << 2) | (1u << 3);
    }
    if (request) {
        uint32_t cue = request & 3u;
        uint32_t player = cue == 1u ? 1u : 2u;
        uint16_t song = cue == 1u ? 0x227u : cue == 2u ? 0x20Du : 0x251u;
        AP_CUE_RESULT = request | AP_CUE_REJECTED;
        if (ap_cue_request_valid(request, AP_FRAME_COUNTER, ready)) {
            const volatile uint32_t *info = (const volatile uint32_t *)AP_CUE_MPLAY_TABLE[player * 3u];
            AP_CUE_SONG_START(song);
            if (info[0] == AP_CUE_SONG_TABLE[(uint32_t)song << 1] && ap_cue_mplay_busy(player)) {
                AP_CUE_ACTIVE = player;
                AP_CUE_RESULT = request;
                ready = 0u;
            }
        }
        /* Publish the result first. No queued/chained native requests. */
        AP_CUE_REQUEST = 0u;
    }
    AP_CUE_READY = ready;
}

static AP_REWARD_FX uint8_t ap_show_incoming_reward(uint8_t art, uint32_t active) {
    uintptr_t viewport = 0x0202353Cu;
    int32_t cx = *(const volatile int32_t*)viewport;
    int32_t cy = *(const volatile int32_t*)(viewport + 4u);
    int32_t x = *(const volatile int32_t*)(KIRBY_STRUCTS_ADDR + 0x40u);
    int32_t y = *(const volatile int32_t*)(KIRBY_STRUCTS_ADDR + 0x44u) - 42 * 256;
    /* Keep a live receipt above and to the side of the normal check art;
     * a remote arrival should not hide the event that was played locally. */
    x += (x < cx + 120 * 256 ? 24 : -24) * 256;
    if (x < cx + 16 * 256) x = cx + 16 * 256;
    if (x > cx + 224 * 256) x = cx + 224 * 256;
    int32_t minimum_y = cy + (art == AP_REWARD_MIRROR_SHARD ? 40 : 30) * 256;
    if (y < minimum_y) y = minimum_y;
    if (y > cy + 132 * 256) y = cy + 132 * 256;
    return ap_show_room_reward_gem(ap_reward_local_room(), x, y, active | AP_VISUAL_REJECTED, art);
}

static AP_REWARD_FX void ap_receipt_visual_poll(void) {
    volatile struct ApReceiptVisualMailbox *msg = AP_VISUAL_MAILBOX;
    uint32_t frame = AP_FRAME_COUNTER, request = msg->request, active = msg->active;
    uint8_t game = ap_receipt_cue_gameplay_ready()
        && ap_copy_room_epoch() && ap_visit_palette_ready();
    uint32_t duration = (active & AP_VISUAL_CODE_MASK) == AP_REWARD_MIRROR_SHARD + 1u
        ? AP_SHARD_AWARD_TICKS : AP_VISUAL_DURATION;
    if (active && (!game || ap_visual_age(active, frame) >= duration)) {
        msg->active = active = 0u;
    }
    uint32_t ready = game && !active ? AP_VISUAL_READY : 0u;
    if (request) {
        msg->result = request | AP_VISUAL_REJECTED;
        uint32_t code = request & AP_VISUAL_CODE_MASK;
        uint32_t token = ((frame & AP_VISUAL_FRAME_MASK) << AP_VISUAL_FRAME_SHIFT) | code;
        if (ap_visual_can_start(request, frame, ready)
            && ap_show_incoming_reward((uint8_t)(code - 1u), token)) {
            msg->active = token;
            msg->result = request;
            ready = 0u;
        }
        msg->request = 0u;
    }
    msg->ready = ready;
}

HUB_EXT void ap_hub_tasks(void) {
    uint16_t held = HUB_HELD_KEYS;
    uint32_t before = HUB_STATE_FN;
    uint8_t ready = ap_hub_pending_ready();
    uint8_t calling = before == HUB_CALL_STATE || before == HUB_CHARGE_STATE;
    uint8_t inject = 0u;
    if (ready && (held & 0xCu) == 0u
        && *(volatile uint16_t *)(KIRBY_STRUCTS_ADDR + 0x60u) != 0x321u) {
        if (calling) {
            /* Only sustain native L-call states, never other phone actions. */
            inject = (*(volatile uint32_t *)(KIRBY_STRUCTS_ADDR + 0xCu) & 0x40000u) != 0u;
        } else if (ap_hub_idle_ready()
            && (*(volatile uint16_t *)(KIRBY_STRUCTS_ADDR + 0x118u) & 0x200u) == 0u) {
            /* Rejected native presses get a release frame, then a new edge.
             * Physical input is never cleared, including a user's held L. */
            inject = 1u;
        }
    }
    if (inject) HUB_HELD_KEYS = held | 0x200u;
    ((void (*)(void))0x08152CF5u)();
    HUB_HELD_KEYS = held;
    /* Native TasksExec has already updated menu, transition and mixer state. */
    ap_receipt_cue_poll();
    ap_receipt_visual_poll();
    if (!ap_hub_pending_ready()) return;
    /* Accept only this frame's native charge -> takeoff transition. A receipt
     * arriving during an earlier takeoff must wait for safe arrival instead. */
    if (!(ready && before == HUB_CHARGE_STATE && HUB_STATE_FN == HUB_TAKEOFF_STATE)
        && !(*(volatile uint16_t *)(KIRBY_STRUCTS_ADDR + 0x60u) == 0x321u
             && ap_hub_idle_ready())) return;
    AP_DEBUG_LAST_ITEM_ID = AP_IN_ITEM_ID;
    AP_DEBUG_LAST_FROM = AP_IN_PLAYER;
    AP_ITEM_RCVD_COUNTER++;
    AP_IN_FLAG = 0u;
}

// Returns 1 if item was successfully processed, 0 if unrecognized
static uint8_t ap_apply_item(uint32_t ap_item_id) {
    /* Only authenticated complete history may grant this access item. */
    if (ap_item_id == AP_PHONE_ITEM) return (uint8_t)ap_phone_owned();
    if (ap_item_id == AP_COPY_ROOM_ITEM) return (uint8_t)ap_copy_room_owned();
    if (ap_item_id == AP_NARCOLEPSY_ITEM) return ap_trap_narcolepsy();
    if (ap_item_id == AP_RANDOM_TELEPORT_ITEM) return ap_trap_random_teleport();
    // 1_UP = BASE+1
    if (ap_item_id == (KIRBY_ITEM_ID_BASE_OFFSET + 1u)) {
        ap_grant_lives(1u);
        return 1u;
    }

    // SHARD_1..SHARD_8 = BASE+2 .. BASE+9
    if (ap_item_id >= (KIRBY_ITEM_ID_BASE_OFFSET + 2u) && ap_item_id <= (KIRBY_ITEM_ID_BASE_OFFSET + 9u)) {

        uint32_t shard_index = ap_item_id - (KIRBY_ITEM_ID_BASE_OFFSET + 2u); // 0..7
        uint8_t mask = (uint8_t)(1u << shard_index);

        // Issue #478: Record AP-delivered authority so the per-frame scrub knows
        // which shard bits are legitimately AP-owned.
        AP_DELIVERED_SHARD_BITFIELD |= (uint32_t)mask;

        // Update EWRAM (volatile, temporary)
        uint8_t new_shard_flags = (uint8_t)(KIRBY_SHARD_FLAGS | mask);
        KIRBY_SHARD_FLAGS = new_shard_flags;

        // Optional: keep hack mirror for AP client polling/debugging
        AP_SHARD_BITFIELD |= (uint32_t)mask;

        // Native save flow persists gTreasures; no direct SRAM writes here.

        return 1u;
    }

    if (ap_item_id == (KIRBY_ITEM_ID_BASE_OFFSET + 24u)) {
        ap_unlock_area_map(1u);
        return 1u;
    }

    if (ap_item_id >= (KIRBY_ITEM_ID_BASE_OFFSET + 10u) && ap_item_id <= (KIRBY_ITEM_ID_BASE_OFFSET + 17u)) {
        static const uint8_t map_area_ids[8] = {4u, 2u, 9u, 6u, 7u, 3u, 5u, 8u};
        uint32_t map_index = ap_item_id - (KIRBY_ITEM_ID_BASE_OFFSET + 10u);
        ap_unlock_area_map(map_area_ids[map_index]);
        return 1u;
    }

    /* Explicit noncontiguous identities; physical chest flags are unrelated. */
    uint32_t vitality_mask = ap_vitality_item_bit(ap_item_id);
    if (vitality_mask != 0u) {
        if ((AP_DELIVERED_VITALITY_ITEM_BITS & vitality_mask) == 0u) {
            AP_DELIVERED_VITALITY_ITEM_BITS |= vitality_mask;
            ap_grant_vitality_counter();
        }
        return 1u;
    }

    // SOUND_PLAYER = BASE+25
    if (ap_item_id == (KIRBY_ITEM_ID_BASE_OFFSET + 25u)) {
        KIRBY_COLLECT_SOUND_PLAYER_FN(0u);
        return 1u;
    }

    // Dynamic ability unlock items map by runtime ability id:
    // BASE + 100 + <ability_id>, where ability_id is 1..31.
    if (ap_item_id >= (KIRBY_ITEM_ID_BASE_OFFSET + 101u) && ap_item_id <= (KIRBY_ITEM_ID_BASE_OFFSET + 131u)) {
        uint32_t ability_id = ap_item_id - (KIRBY_ITEM_ID_BASE_OFFSET + 100u);
        AP_ABILITY_UNLOCK_MASK |= (1u << ability_id);
        return 1u;
    }

    // SMALL_FOOD, BATTERY, MAX_TOMATO, INVINCIBILITY_CANDY = BASE+26 .. BASE+29
    if (ap_item_id == (KIRBY_ITEM_ID_BASE_OFFSET + 26u)) {
        ap_grant_small_food();
        return 1u;
    }

    if (ap_item_id == (KIRBY_ITEM_ID_BASE_OFFSET + 27u)) {
        return ap_grant_battery();
    }

    if (ap_item_id == (KIRBY_ITEM_ID_BASE_OFFSET + 28u)) {
        ap_grant_max_tomato();
        return 1u;
    }

    if (ap_item_id == (KIRBY_ITEM_ID_BASE_OFFSET + 29u)) {
        if (!ap_invincibility_candy_ready()) return 0u;
        ap_grant_invincibility_candy();
        return 1u;
    }

    // ENERGY_DRINK, HUNK_OF_MEAT = BASE+30 .. BASE+31
    if (ap_item_id == (KIRBY_ITEM_ID_BASE_OFFSET + 30u)) {
        ap_grant_energy_drink();
        return 1u;
    }

    if (ap_item_id == (KIRBY_ITEM_ID_BASE_OFFSET + 31u)) {
        ap_grant_hunk_of_meat();
        return 1u;
    }

    // TRAP_HEALTH_DOWN = BASE+32
    if (ap_item_id == (KIRBY_ITEM_ID_BASE_OFFSET + 32u)) {
        ap_trap_health_down();
        return 1u;
    }

    // TRAP_LIFE_DOWN = BASE+33
    if (ap_item_id == (KIRBY_ITEM_ID_BASE_OFFSET + 33u)) {
        ap_trap_life_down();
        return 1u;
    }

    // TRAP_BOMB = BASE+34
    if (ap_item_id == (KIRBY_ITEM_ID_BASE_OFFSET + 34u)) {
        ap_trap_bomb();
        return 1u;
    }

    // TRAP_BATTERY_DRAIN = BASE+35
    if (ap_item_id == (KIRBY_ITEM_ID_BASE_OFFSET + 35u)) {
        ap_trap_battery_drain();
        return 1u;
    }

    // TRAP_LIFE_WIPEOUT = BASE+36
    if (ap_item_id == (KIRBY_ITEM_ID_BASE_OFFSET + 36u)) {
        ap_trap_lives_wipeout();
        return 1u;
    }

    // LEVER_WALL_* = BASE+37 .. BASE+40 (Issue #859).
    // Native chest bits are AP wall ownership. Physical activations use the AP
    // latch; the lever object's auxiliary callback observes this bit and opens
    // the live wall once. Chest initialization handles later room visits.
    if (ap_item_id >= (KIRBY_ITEM_ID_BASE_OFFSET + 37u)
        && ap_item_id <= (KIRBY_ITEM_ID_BASE_OFFSET + 40u)) {
        static const uint8_t lever_wall_chest_ids[4] = {18u, 65u, 77u, 74u};
        uint32_t lever_index = ap_item_id - (KIRBY_ITEM_ID_BASE_OFFSET + 37u);
        ap_collect_small_chest_native((uint32_t)lever_wall_chest_ids[lever_index]);
        return 1u;
    }

    if (ap_item_id == AP_RAINBOW_ROUTE_KEY_ITEM) {
        if (ap_area_keys_enabled()) AP_AREA_KEY_BITFIELD_RUNTIME |= AP_RAINBOW_ROUTE_KEY_BIT;
        return 1u;
    }

    // AREA_KEY_2..AREA_KEY_9 = BASE+41 .. BASE+48 (Issue #42).
    if (ap_item_id >= (KIRBY_ITEM_ID_BASE_OFFSET + 41u)
        && ap_item_id <= (KIRBY_ITEM_ID_BASE_OFFSET + 48u)) {
        return ap_progress_receive(ap_item_id - (KIRBY_ITEM_ID_BASE_OFFSET + 41u));
    }

    if (ap_item_id == AP_STARTING_MIRROR_ITEM) {
        if (!ap_random_starting_mirror_enabled()) return 1u;
        uint32_t mask = AP_HUB_CONNECTION_ITEM_MASK;
        return mask != AP_HUB_CONNECTION_ITEM_MASK_UNINITIALIZED
            && (mask & AP_STARTING_MIRROR_ITEM_MASK) && ap_copy_room_receive_starting_mirror();
    }

    // HUB_CONNECTION_* = BASE+401 .. BASE+415; enum values 1..15 match WorldMapDoor.
    if (ap_item_id >= (KIRBY_ITEM_ID_BASE_OFFSET + 401u)
        && ap_item_id <= (KIRBY_ITEM_ID_BASE_OFFSET + 415u)) {
        uint32_t door_index = ap_item_id - (KIRBY_ITEM_ID_BASE_OFFSET + 400u);
        uint32_t mask = AP_HUB_CONNECTION_ITEM_MASK;
        if (mask == AP_HUB_CONNECTION_ITEM_MASK_UNINITIALIZED
            || !(mask & (1u << door_index))
            || !ap_progress_receive(door_index + 7u)) return 0u;
        ap_project_hub_doors(ap_progress_owned());
        return 1u;
    }

    // Fixed Spray Paint (+200..+213) and Music Sheet (+214..+223) items.
    // Bitwise ownership grants are idempotent when received history is replayed.
    if (ap_apply_collection_item(ap_item_id - KIRBY_ITEM_ID_BASE_OFFSET,
                                &KIRBY_SPRAY_PAINT_FLAGS,
                                &KIRBY_MUSIC_PLAYER_AND_SHEETS_FLAGS)) {
        return 1u;
    }

    // Unhandled item - return 0 to signal that the flag should NOT be cleared
    return 0u;
}


AP_COPY_EXT void ap_poll_mailbox_c(void) {
    ap_copy_room_poll();
    ap_goal_poll();
    ap_phone_poll();

    // Hook liveness diagnostic counter; increments on every AP hook entry.
    AP_HOOK_HEARTBEAT++;

    // Always tick a monotonic frame counter so the Python client can perform
    // deterministic, frame-based testing without relying on wall-clock time.
    AP_FRAME_COUNTER++;

    // Initialize mailbox-owned shard scrub state once per fresh EWRAM session.
    // This avoids acting on stale/garbage transport values after soft reset.
    if (AP_MAILBOX_INIT_COOKIE != AP_MAILBOX_INIT_COOKIE_VALUE) {
        uint8_t native_shards_boot = KIRBY_SHARD_FLAGS;
        AP_DELIVERED_SHARD_BITFIELD = (uint32_t)native_shards_boot;
        AP_SHARD_SCRUB_DELAY = 0u;
        AP_BOSS_DEFEAT_FLAGS = 0u;
        AP_BOSS_TEMP_SHARD_BITFIELD = 0u;
        AP_CUE_REQUEST = AP_CUE_RESULT = AP_CUE_READY = AP_CUE_ACTIVE = 0u;
        AP_VISUAL_MAILBOX->request = AP_VISUAL_MAILBOX->result = 0u;
        AP_VISUAL_MAILBOX->ready = AP_VISUAL_MAILBOX->active = 0u;
        AP_VISIT_PENDING->epoch = 0u;
        AP_BOSS_ITEM_DRAW->epoch = 0u;
        AP_BOSS_ITEM_DRAW->object = 0;
        AP_RANDOM_TELEPORT_NONCE = AP_RANDOM_TELEPORT_EPOCH = 0u;
        AP_DELIVERED_VITALITY_ITEM_BITS = 0u;
        AP_HUB_CONNECTION_ITEM_MASK = AP_HUB_CONNECTION_ITEM_MASK_UNINITIALIZED;
        AP_HUB_SWITCH_INIT_STATE = 0u;
        AP_HUB_SWITCH_FLAGS = 0u;
        AP_STARTING_KIRBY_COLOR_ID = 0xFFFFFFFFu;
        AP_ONE_HIT_MODE_RUNTIME = 0xFFFFFFFFu;
        AP_NO_EXTRA_LIVES_RUNTIME = 0xFFFFFFFFu;
        AP_STARTING_KIRBY_COLOR_APPLIED = 0u;
        AP_LEVER_ACTIVATION_FLAGS = 0u;
        AP_AREA_KEY_BITFIELD_RUNTIME = ap_rainbow_route_gate_enabled() ? AP_RAINBOW_ROUTE_KEY_BIT : 0u;
        AP_ABILITY_RANDOMIZATION_MODE = 0u;
        AP_ABILITY_RANDOMIZATION_SEED_LO = 0u;
        AP_ABILITY_RANDOMIZATION_SEED_HI = 0u;
        AP_ABILITY_RANDOMIZATION_NO_ABILITY_WEIGHT = 0u;
        AP_ABILITY_RANDOMIZATION_ALLOWED_MASK = 0u;
        AP_ABILITY_RANDOMIZATION_RNG_STATE = 0u;
        AP_ABILITY_REROLL_EVENT_COUNTER = 0u;
        AP_ABILITY_REROLL_SOURCE_ADDR = 0u;
        AP_ABILITY_REROLL_SOURCE_KIND = 0u;
        AP_ABILITY_REROLL_CALLSITE_PC = 0u;
        AP_ABILITY_REROLL_KIRBY_INDEX = 0u;
        AP_ABILITY_REROLL_ABILITY_ID = 0u;
        /*
         * Deny gated abilities from the first gameplay frame, even before the
         * Python client connects. The client later rewrites this mailbox field
         * with the same canonical mask and synchronizes received unlock bits.
         */
        AP_ABILITY_GATE_MASK = gApAbilityGateMaskInitial;
        AP_ABILITY_UNLOCK_MASK = 0u;
        AP_MINOR_CHEST_EVENT_COUNTER = 0u;
        {
            uint32_t i;
            for (i = 0u; i < AP_MINOR_CHEST_EVENT_RING_SLOT_COUNT; i++) {
                *(volatile uint32_t*)(AP_MINOR_CHEST_EVENT_RING_BASE + (i << 2)) = 0u;
            }
        }
        AP_MAILBOX_INIT_COOKIE = AP_MAILBOX_INIT_COOKIE_VALUE;
    }

    ap_visit_reward_art_poll();

    // Native startup/receipt projects durable door ownership. Item history alone
    // is not authority for a native file, and cannot invent physical checks.
    ap_restore_hub_switch_checks();

    uint8_t ap_delivered = (uint8_t)(AP_DELIVERED_SHARD_BITFIELD & 0xFFu);
    uint8_t native_shards = KIRBY_SHARD_FLAGS;
    uint8_t pending_boss_temp = (uint8_t)(AP_BOSS_TEMP_SHARD_BITFIELD & 0xFFu);

    // Cold-boot/soft-reset guard: before any local boss-defeat hook activity,
    // align AP-delivered authority to the current native shard save state.
    // This prevents scrub from acting on stale/uninitialized transport values.
    if (pending_boss_temp == 0u && AP_SHARD_SCRUB_DELAY == 0u) {
        if (ap_delivered != native_shards) {
            AP_DELIVERED_SHARD_BITFIELD = (uint32_t)native_shards;
        }
    } else {
        // Issue #505: keep temporary native shard visibility during post-boss
        // cutscene, but scrub to AP-owned authority as soon as gameplay resumes.
        uint32_t ai_state = AI_KIRBY_STATE;
        uint8_t gameplay_active = 0u;
        if ((ai_state >= AI_STATE_NORMAL
            && ai_state != AI_STATE_DARK_MIND_CLEAR
            && ai_state != AI_STATE_FULL_CLEAR) || ap_runtime_ai_allows_gameplay()) {
            gameplay_active = 1u;
        }
        if (gameplay_active) {
            uint32_t demo_flags = DEMO_PLAYBACK_FLAGS;
            if ((demo_flags & DEMO_PLAYBACK_ACTIVE_FLAG) != 0u) {
                gameplay_active = 0u;
            }
        }

        if (!gameplay_active) {
            if (AP_SHARD_SCRUB_DELAY > 0u) {
                AP_SHARD_SCRUB_DELAY--;
            }
        } else {
            uint8_t scrub_mask = (uint8_t)(pending_boss_temp & (uint8_t)(~ap_delivered));
            uint8_t clamped = (uint8_t)(native_shards & (uint8_t)(~scrub_mask));
            if (clamped != native_shards) {
                KIRBY_SHARD_FLAGS = clamped;
            }
            AP_BOSS_TEMP_SHARD_BITFIELD = 0u;
            AP_SHARD_SCRUB_DELAY = 0u;
        }
    }

    ap_apply_starting_kirby_color_config();

    // Check if there's an item to process
    uint32_t flag = AP_IN_FLAG;
    if (flag != 1u) return;

    // Receive an item from a player - read IMMEDIATELY after confirming flag
    uint32_t item = AP_IN_ITEM_ID;
    uint32_t from = AP_IN_PLAYER;

    // Debug: confirm delivery
    AP_DEBUG_LAST_ITEM_ID = item;
    AP_DEBUG_LAST_FROM = from;

    // Apply the received item
    // Returns 1 if item was recognized and processed, 0 if unrecognized.
    uint8_t item_was_processed = ap_apply_item(item);

    // Acknowledge / consume: clear flag to signal completion.
    // We ONLY clear the flag after successfully processing a valid item.
    // If the item was unrecognized (item_was_processed==0), the flag is NOT cleared,
    // allowing the client to detect a protocol mismatch and retry/stall appropriately.
    if (item_was_processed) {
        if (item == AP_RANDOM_TELEPORT_ITEM) {
            AP_RANDOM_TELEPORT_NONCE = AP_RANDOM_TELEPORT_EPOCH = 0u;
        }
        AP_ITEM_RCVD_COUNTER++;
        AP_IN_FLAG = 0u;
    }
}

/* Native sub_0803518C redraws only the current capacity and its endcap.
 * A client-side custom-capacity reduction can therefore leave old HP tiles.
 * Restore the unused cells to the native HUD initializer's blank tile 0x184.
 * Six cells cover the supported 1..10 HP range (five pairs plus endcap).
 * Keep demo-mode suppression and all native HP/endcap rendering unchanged.
 */
void ap_draw_health_hud(uint8_t *kirby) {
    typedef void (*draw_fn)(uint8_t *);
    ((draw_fn)0x0803518Du)(kirby);
    int8_t capacity = *(volatile int8_t *)(kirby + 0x101u);
    if ((*(volatile uint32_t *)0x0203AD10u & 0x10u) != 0u
            || capacity < 1 || capacity > 10) {
        return;
    }
    for (uint32_t cell = (uint32_t)capacity / 2u + 1u; cell < 6u; ++cell) {
        *(volatile uint16_t *)(0x0600E49Au + cell * 2u) = 0x0184u;
        *(volatile uint16_t *)(0x0600E4DAu + cell * 2u) = 0x0184u;
    }
}
