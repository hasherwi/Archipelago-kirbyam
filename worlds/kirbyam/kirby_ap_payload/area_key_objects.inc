/* USA object lifecycle integration. No AP object registry or saved pointers:
 * native spawn slots remain authoritative for presence and consumption. */
#define AREA_OBJECT_EXT __attribute__((used, noinline, long_call, section(".aphub")))
#define OBJ_U8(p, o) (*(volatile uint8_t*)((uint32_t)(p) + (o)))
#define OBJ_U16(p, o) (*(volatile uint16_t*)((uint32_t)(p) + (o)))
#define OBJ_U32(p, o) (*(volatile uint32_t*)((uint32_t)(p) + (o)))
#define OBJ_S32(p, o) (*(volatile int32_t*)((uint32_t)(p) + (o)))
typedef void (*AreaObjectVoidFn)(void);
typedef uint32_t (*AreaObjectSlotFn)(uint32_t, uint32_t, uint32_t);
#define AREA_NATIVE_SLOT ((AreaObjectSlotFn)0x080027E9u)

/* Invoked only after the native spawn-slot predicate returned zero. */
AREA_OBJECT_EXT uint32_t ap_area_key_spawn_blocked(uint32_t template, uint32_t level) {
    if (OBJ_U8(template, 0) != 1u || OBJ_U8(template, 0xCu) != 0x84u) return 0u;
    return !ap_transition_allowed(OBJ_U16(level, 0x5F8u), OBJ_U16(template, 0x1Eu));
}

static __attribute__((noinline, section(".aphub"))) uint32_t ap_area_current_object(void) {
    uint32_t task = *(volatile uint32_t*)0x030035D0u;
    uint32_t offset = OBJ_U16(task, 6u);
    return (OBJ_U16(task, 0x12u) & 0x10u) ? 0x02000000u + (offset << 2) : 0x03000000u + offset;
}

AREA_OBJECT_EXT void ap_area_warp_star_main(void) {
    uint32_t obj = ap_area_current_object();
    /* Never free a transport that already owns passengers. Existing boarding
     * guards reject new passengers; retire it once native flight cleanup ends. */
    if (!(OBJ_U32(obj, 8u) & 0x1000u) && OBJ_U8(obj, 0xB5u) == 0u
        && !ap_transition_allowed(OBJ_U16(obj, 0x60u), OBJ_U16(obj, 0xBEu))) {
        /* Destroy through the native destructor: releases VRAM, room-object
         * registration and the spawn slot. Do not flag an ordinary death. */
        OBJ_U32(obj, 8u) |= 0x1000u;
        ((void (*)(void*))0x08152C3Du)((void*)*(volatile uint32_t*)0x030035D0u);
        return;
    }
    ((AreaObjectVoidFn)0x08099B81u)();
}

/* Native movement spawners scan only newly exposed screen strips. Recheck
 * eligible keyed stars in the current viewport even if the player is still.
 * This deliberately does not rescan enemies or modify any native slot bits. */
AREA_OBJECT_EXT void ap_area_spawn_main(void) {
    uint8_t player, count = *(volatile uint8_t*)KIRBY_NUM_HUMAN_PLAYERS_ADDR;
    ((AreaObjectVoidFn)0x0800A6E9u)();
    if (!ap_area_keys_enabled() || count > 4u) return;
    for (player = 0; player < count; ++player) {
        uint32_t level = KIRBY_LEVEL_INFO_BASE_ADDR + player * KIRBY_LEVEL_INFO_STRIDE;
        uint16_t room = OBJ_U16(level, 0x5F8u);
        uint32_t template, remaining = 512u;
        int32_t left, top;
        if (room == 0xFFFFu) continue;
        template = OBJ_U32(OBJ_U32(level, 0x1E4u), 0u);
        left = ((OBJ_S32(level, 0xCu) + OBJ_S32(level, 0x1Cu)) >> 12) - 3;
        top = ((OBJ_S32(level, 0x10u) + OBJ_S32(level, 0x20u)) >> 12) - 3;
        while (OBJ_U8(template, 1u) && remaining--) {
            uint8_t size = OBJ_U8(template, 1u);
            if (size < 0x24u) break;
            if (OBJ_U8(template, 0u) == 1u && OBJ_U8(template, 0xCu) == 0x84u
                && ap_is_keyed_inter_area_edge(room, OBJ_U16(template, 0x1Eu))
                && !ap_area_key_spawn_blocked(template, level)
                && !AREA_NATIVE_SLOT(OBJ_U8(template, 2u), OBJ_U8(template, 3u), OBJ_U8(level, 0x65Eu))) {
                int32_t x = (int16_t)OBJ_U16(template, 6u) >> 4;
                int32_t y = (int16_t)OBJ_U16(template, 8u) >> 4;
                if ((OBJ_U8(template, 5u) & 1u) || (left <= x && x < left + 0x16 && top <= y && y < top + 0x11))
                    ((void* (*)(uint8_t, void*))0x0800A869u)(player, (void*)template);
            }
            template += size;
        }
    }
}

AREA_OBJECT_EXT void ap_area_mirror_main(void) {
    uint32_t obj = ap_area_current_object();
    uint8_t player = OBJ_U8(obj, 0x56u);
    uint16_t x = OBJ_U16(obj, 0xBCu), y = OBJ_U16(obj, 0xBEu);
    /* Only touch an existing, natively enabled transition decoration. Inactive
     * collision tiles and consumed/session-controlled mirrors remain native. */
    if (player < 4u && !(OBJ_U32(obj, 8u) & 0x1000u)
        && (KIRBY_COLLISION_ATTRIBUTES[KIRBY_GET_COLLISION_TILE_FN(player, x, y)] & 0x4000u)) {
        uint32_t tile = (uint32_t)KIRBY_SPECIAL_TILE_FN(player, x, y);
        uint16_t source = OBJ_U16(obj, 0x60u);
        uint16_t dest = ap_transition_route_destination(source, OBJ_U16(tile, 8u), OBJ_U8(tile, 0xAu), OBJ_U8(tile, 0xBu));
        uint32_t effect = OBJ_U32(obj, 0xB4u);
        if (effect && ap_is_keyed_inter_area_edge(source, dest)) {
            uint8_t open = ap_transition_allowed(source, dest);
            uint8_t variant = open ? ((OBJ_U16(OBJ_U32(obj, 0xB0u), 0x22u) & 0x100u) ? 9u : 2u) : 0xAu;
            if (OBJ_U16(effect, 0x18u) != 0x294u || OBJ_U8(effect, 0x26u) != variant) {
                OBJ_U16(effect, 0x18u) = 0x294u;
                OBJ_U8(effect, 0x26u) = variant;
                OBJ_U8(effect, 0x27u) = 0xFFu;
            }
            OBJ_U16(obj, 0xC0u) = (OBJ_U16(obj, 0xC0u) & ~2u) | (open ? 2u : 0u);
        }
    }
    ((AreaObjectVoidFn)0x08099B81u)();
}

AREA_OBJECT_EXT void ap_area_door_decoration(void *door) {
    uint32_t obj = (uint32_t)door;
    uint8_t player = OBJ_U8(obj, 0x56u);
    uint32_t tile = (uint32_t)KIRBY_SPECIAL_TILE_FN(player,
        OBJ_S32(obj, 0x40u) >> 12, (OBJ_S32(obj, 0x44u) - 0xFFF) >> 12);
    uint16_t source = OBJ_U16(obj, 0x60u);
    uint16_t dest = ap_transition_route_destination(source, OBJ_U16(tile, 8u), OBJ_U8(tile, 0xAu), OBJ_U8(tile, 0xBu));
    if (ap_transition_allowed(source, dest)) {
        ((void (*)(void*))0x0802B2F5u)(door);
    } else {
        uint32_t effect = OBJ_U32(obj, 0xB4u);
        if (!effect) {
            effect = (uint32_t)((void* (*)(void*, uint32_t, uint32_t, uint32_t, uint32_t))0x0808B62Du)(door, 0, 0x294, 0xA, 0);
            OBJ_U32(obj, 0xB4u) = effect;
        }
        if (OBJ_U16(effect, 0x18u) != 0x294u || OBJ_U8(effect, 0x26u) != 0xAu) {
            OBJ_U16(effect, 0x18u) = 0x294u;
            OBJ_U8(effect, 0x26u) = 0xAu;
            OBJ_U8(effect, 0x27u) = 0xFFu;
        }
        OBJ_U16(effect, 6u) &= ~1u;
        OBJ_U32(effect, 0x34u) = OBJ_U32(obj, 0x40u);
        OBJ_U32(effect, 0x38u) = OBJ_U32(obj, 0x44u) - 0xA00u;
        OBJ_U16(effect, 0x20u) = 0x780u;
    }
}

/* Hub background mirrors and door-to-hub frames have a different native
 * decoration layout from MirrorDoor. Only reconcile after their own native
 * initializer has enabled them; never clear Hub/switch collision tiles here. */
AREA_OBJECT_EXT void ap_area_hub_mirror_main(void) {
    uint32_t obj = ap_area_current_object();
    uint32_t slot = 0u;
    uint16_t source = OBJ_U16(obj, 0x60u), dest = 0xFFFFu;
    int32_t board_y = 0;
    if (!(OBJ_U32(obj, 8u) & 0x1000u)) {
        if (OBJ_U8(obj, 0x82u) == 0x8Cu) {
            dest = OBJ_U16(obj, 0xB8u); /* FFFF until the Hub initializer passes. */
            slot = obj + 0xB4u;
            board_y = OBJ_S32(obj, 0x44u) + 0x1000;
        } else if (!(OBJ_U32(obj, 8u) & 0x400u) && OBJ_U32(obj, 0xB4u)) {
            uint8_t player = OBJ_U8(obj, 0x56u);
            uint16_t x = OBJ_S32(obj, 0x40u) >> 12;
            uint16_t y = (OBJ_S32(obj, 0x44u) - 0xFFF) >> 12;
            if (player < 4u && (KIRBY_COLLISION_ATTRIBUTES[KIRBY_GET_COLLISION_TILE_FN(player, x, y)] & 0x4000u)) {
                uint32_t tile = (uint32_t)KIRBY_SPECIAL_TILE_FN(player, x, y);
                dest = ap_transition_route_destination(source, OBJ_U16(tile, 8u), OBJ_U8(tile, 0xAu), OBJ_U8(tile, 0xBu));
                slot = obj + 0xB8u;
                board_y = OBJ_S32(obj, 0x44u) - 0x800;
            }
        }
        if (slot && ap_is_keyed_inter_area_edge(source, dest)) {
            uint32_t effect = OBJ_U32(slot, 0u);
            if (!ap_transition_allowed(source, dest)) {
                if (!effect) {
                    effect = (uint32_t)((void* (*)(void*, uint32_t, uint32_t, uint32_t, uint32_t))0x0808B62Du)((void*)obj, 0, 0x294, 0xA, 0);
                    OBJ_U32(slot, 0u) = effect;
                }
                if (OBJ_U16(effect, 0x18u) != 0x294u || OBJ_U8(effect, 0x26u) != 0xAu) {
                    OBJ_U16(effect, 0x18u) = 0x294u;
                    OBJ_U8(effect, 0x26u) = 0xAu;
                    OBJ_U8(effect, 0x27u) = 0xFFu;
                }
                OBJ_U16(effect, 6u) &= ~1u;
                OBJ_U32(effect, 0x34u) = OBJ_U32(obj, 0x40u);
                OBJ_S32(effect, 0x38u) = board_y;
                OBJ_U16(effect, 0x20u) = 0x780u;
            } else if (effect && OBJ_U16(effect, 0x18u) == 0x294u && OBJ_U8(effect, 0x26u) == 0xAu) {
                OBJ_U16(effect, 6u) |= 0x1000u;
                OBJ_U32(slot, 0u) = 0u;
            }
        }
    }
    ((AreaObjectVoidFn)0x08099B81u)();
}
