#ifndef KIRBYAM_GOAL_GAME_RUNTIME_LOGIC_H
#define KIRBYAM_GOAL_GAME_RUNTIME_LOGIC_H
#include <stdint.h>

struct ApGoalDoor {
    uint32_t pointer;
    uint16_t source, destination;
    uint8_t bit;
};
#include "generated_goal_game_doors.inc"

/* Lookup only the inventoried doorway record, physical origin and actual
 * arrival together. Neither a shared scene nor a room-visit index is an origin. */
static inline uint32_t ap_goal_origin(uint32_t door, uint16_t source, uint16_t destination) {
    uint32_t i;
    for (i = 0; i < sizeof(ap_goal_doors) / sizeof(ap_goal_doors[0]); ++i) {
        const struct ApGoalDoor *candidate = &ap_goal_doors[i];
        if (candidate->pointer == door && candidate->source == source
            && candidate->destination == destination) return candidate->bit;
    }
    return 16u;
}

/* Transient only. Context epochs and storage are owned by the shared save
 * lifecycle; the feature never authenticates or initializes that record itself. */
struct ApGoalRun {
    uint32_t epoch, star;
    uint16_t room;
    uint8_t bit, phase;
};
static inline void ap_goal_cancel(volatile struct ApGoalRun *run) {
    run->phase = 0u;
    run->star = 0u;
}
static inline void ap_goal_enter(volatile struct ApGoalRun *run, uint32_t epoch,
                                 uint32_t door, uint16_t source, uint16_t arrival) {
    uint32_t bit = ap_goal_origin(door, source, arrival);
    ap_goal_cancel(run);
    if (epoch == 0u || bit >= 16u) return;
    run->epoch = epoch;
    run->room = arrival;
    run->bit = (uint8_t)bit;
    run->phase = 1u;
}
static inline void ap_goal_validate(volatile struct ApGoalRun *run, uint32_t epoch,
                                    uint16_t room, uint8_t alive) {
    if (!epoch || run->epoch != epoch || room != run->room || !alive) ap_goal_cancel(run);
}
static inline void ap_goal_start(volatile struct ApGoalRun *run, uint32_t epoch,
                                 uint16_t room, uint32_t star, uint8_t participant) {
    ap_goal_validate(run, epoch, room, 1u);
    if (run->phase != 1u || !star || !participant) {
        ap_goal_cancel(run);
        return;
    }
    run->star = star;
    run->phase = 2u;
}
static inline uint32_t ap_goal_complete(volatile struct ApGoalRun *run, uint32_t epoch,
                                       uint16_t room, uint32_t star, uint8_t participant,
                                       uint8_t completed) {
    ap_goal_validate(run, epoch, room, 1u);
    if (run->phase != 2u || run->star != star || !participant) return 16u;
    if (completed) {
        uint32_t bit = run->bit;
        ap_goal_cancel(run);
        return bit;
    }
    return 16u;
}
#endif
