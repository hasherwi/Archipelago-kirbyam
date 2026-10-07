#ifndef HUB_CONNECTION_RUNTIME_LOGIC_H
#define HUB_CONNECTION_RUNTIME_LOGIC_H

#include <stdint.h>

typedef void (*ApWorldMapUnlockCallback)(void);
typedef void (*ApHubSwitchRecordCallback)(uint32_t);

/*
 * Big Switch object initialization reads the persistent world-props unlock
 * entry. If AP granted the door but its physical switch has not been collected,
 * return true so the caller can substitute a zero-valued scratch entry and
 * keep the check object available.
 *
 * The arrays are indexed by native WorldMapDoor (1..15); switch_bits contains
 * the separate AP hub-switch flag bit index for each door.
 */
static inline uint8_t ap_should_mask_item_owned_hub_unlock(
    uint32_t unlock_kind,
    uint32_t hub_unlock_kind,
    uint8_t world_props_unlock_index,
    uint32_t item_mask,
    uint32_t hub_switch_flags,
    const uint8_t world_props_by_door[16],
    const uint8_t switch_bits_by_door[16]
) {
    uint32_t door_index;

    if (unlock_kind != hub_unlock_kind || item_mask == 0xFFFFFFFFu) {
        return 0u;
    }

    for (door_index = 1u; door_index <= 15u; door_index++) {
        uint32_t switch_bit;
        if (world_props_by_door[door_index] == 0xFFu
            || world_props_by_door[door_index] != world_props_unlock_index) {
            continue;
        }

        switch_bit = switch_bits_by_door[door_index];
        if ((item_mask & (1u << door_index)) != 0u
            && (hub_switch_flags & (1u << switch_bit)) == 0u) {
            return 1u;
        }
    }

    return 0u;
}

/*
 * A mapped WorldMapDoor callback would grant the native connection before its
 * AP item arrives. Record its physical check and run the game's transition
 * completion callback instead. Preserve the selected native callback for
 * NO_UNLOCK and unknown values so their existing behavior remains intact.
 */
static inline void ap_dispatch_world_map_unlock(
    uint8_t is_mapped_hub_door,
    uint32_t hub_switch_bit,
    ApWorldMapUnlockCallback unlock_callback,
    ApWorldMapUnlockCallback transition_complete_callback,
    ApHubSwitchRecordCallback record_callback
) {
    if (is_mapped_hub_door != 0u) {
        if (record_callback != 0) {
            record_callback(hub_switch_bit);
        }
        if (transition_complete_callback != 0) {
            transition_complete_callback();
        }
        return;
    }

    if (unlock_callback != 0) {
        unlock_callback();
    }
}

#endif
