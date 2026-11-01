#ifndef KIRBYAM_TRANSITION_RUNTIME_LOGIC_H
#define KIRBYAM_TRANSITION_RUNTIME_LOGIC_H

#include <stdint.h>

static inline uint8_t ap_transition_is_human_up_attempt(
    uint8_t player_id,
    uint8_t human_player_count,
    uint16_t movement_state
) {
    return (uint8_t)(player_id < human_player_count && (movement_state & 0x40u) != 0u);
}

static inline uint8_t ap_transition_matches_special_tile(
    uint16_t tile_destination_room,
    uint8_t tile_spawn_x,
    uint8_t tile_spawn_y,
    uint16_t destination_room,
    uint8_t spawn_x,
    uint8_t spawn_y
) {
    return (uint8_t)(
        tile_destination_room == destination_room
        && tile_spawn_x == spawn_x
        && tile_spawn_y == spawn_y
    );
}

#endif
