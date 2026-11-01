#ifndef KIRBYAM_TRANSITION_ROUTE_LOGIC_H
#define KIRBYAM_TRANSITION_ROUTE_LOGIC_H

#include <stdint.h>

#define AP_TRANSITION_METHOD_WIND_CHUTE 3u

/* Resolve admission to the two retail wind chutes to the room at the end of
 * the entered lane. Native room 180 belongs to Moonlight, but its left lane
 * exits to Olive; room 181 belongs to Carrot, but its left lane exits to Radish.
 * Gating only the eventual automatic exit strands a denied player in the chute.
 *
 * These are exact native (source, chute, spawn) tuples. Both 16x53 solidity
 * grids have separated lanes: x=1..6 leads to the bottom exit at y=50..52,
 * x=9..14 leads to the top exit at y=0..1. The two entry spawns are (5,3) and
 * (12,49). Return the original room for every other transition. This function
 * selects a permission target only; callers must retain the original native
 * destination/spawn when invoking native code. */
static inline uint16_t ap_transition_route_destination(
    uint16_t source_room,
    uint16_t destination_room,
    uint8_t spawn_x,
    uint8_t spawn_y
) {
    if (destination_room == 180u) {
        if (source_room == 743u && spawn_x == 5u && spawn_y == 3u) return 824u;
        if (source_room == 824u && spawn_x == 12u && spawn_y == 49u) return 743u;
    }
    if (destination_room == 181u) {
        if (source_room == 170u && spawn_x == 5u && spawn_y == 3u) return 619u;
        if (source_room == 619u && spawn_x == 12u && spawn_y == 49u) return 170u;
    }
    return destination_room;
}

#endif
