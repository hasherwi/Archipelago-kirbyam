#ifndef KIRBYAM_STATUE_RUNTIME_LOGIC_H
#define KIRBYAM_STATUE_RUNTIME_LOGIC_H

#include <stdint.h>

/*
 * Pure helpers for the ability-statue runtime hook.
 *
 * Keeping policy decisions here makes the ROM behavior executable in a native
 * unit-test harness without emulating GBA memory.  The payload supplies the
 * mailbox values, RNG state, and verified caller PC; these helpers decide
 * whether a touch participates, which abilities remain eligible, and how the
 * low-five-bit ability ID is replaced without disturbing transition flags.
 */
#define AP_STATUE_RANDOMIZATION_MODE_COMPLETELY_RANDOM 2u
#define AP_STATUE_ABILITY_ID_MASK 0x1Fu

/*
 * sub_080AA588 is the regular ability-statue callback.  sub_080AA618 begins
 * the Master Sword stand callback, which is intentionally not randomized.
 * The payload records the original BL callsite as (lr & ~1) - 4.
 */
#define AP_STATUE_TOUCH_CALLSITE_START 0x080AA588u
#define AP_STATUE_TOUCH_CALLSITE_END   0x080AA618u

static inline uint8_t ap_statue_is_direct_touch_callsite(uint32_t caller_pc) {
    return (caller_pc >= AP_STATUE_TOUCH_CALLSITE_START
        && caller_pc < AP_STATUE_TOUCH_CALLSITE_END) ? 1u : 0u;
}

static inline uint8_t ap_statue_should_reroll(
    uint32_t caller_pc,
    uint32_t randomization_mode,
    uint32_t statue_allowed_mask
) {
    return (ap_statue_is_direct_touch_callsite(caller_pc) != 0u
        && randomization_mode == AP_STATUE_RANDOMIZATION_MODE_COMPLETELY_RANDOM
        && statue_allowed_mask != 0u) ? 1u : 0u;
}

/*
 * Ability gating is represented by two mailbox masks.  A bit is unavailable
 * only when it is both gateable and not yet unlocked.  Gating disabled is
 * naturally represented by gate_mask == 0, so no separate branch is needed.
 */
static inline uint8_t ap_statue_is_locked_ability(
    uint8_t ability_id,
    uint32_t gate_mask,
    uint32_t unlock_mask
) {
    uint32_t ability_bit;
    if (ability_id == 0u || ability_id > AP_STATUE_ABILITY_ID_MASK) {
        return 0u;
    }
    ability_bit = 1u << ability_id;
    return ((gate_mask & ability_bit) != 0u
        && (unlock_mask & ability_bit) == 0u) ? 1u : 0u;
}

static inline uint32_t ap_statue_unlocked_candidate_mask(
    uint32_t statue_allowed_mask,
    uint32_t gate_mask,
    uint32_t unlock_mask
) {
    uint32_t locked_mask = gate_mask & ~unlock_mask;
    return statue_allowed_mask & ~locked_mask;
}

/*
 * Select uniformly from set ability bits 1..31.  Bit 0 is Normal/no ability
 * and is deliberately not part of the randomized statue pool.  A zero pool
 * resolves to Normal, which is the safe result when every eligible ability is
 * still locked.
 */
static inline uint8_t ap_statue_select_ability(
    uint32_t candidate_mask,
    uint32_t random_u32
) {
    uint32_t count = 0u;
    uint32_t i;
    uint32_t selected_index;

    candidate_mask &= 0xFFFFFFFEu;
    for (i = 1u; i <= AP_STATUE_ABILITY_ID_MASK; i++) {
        if ((candidate_mask & (1u << i)) != 0u) {
            count++;
        }
    }
    if (count == 0u) {
        return 0u;
    }

    selected_index = random_u32 % count;
    for (i = 1u; i <= AP_STATUE_ABILITY_ID_MASK; i++) {
        if ((candidate_mask & (1u << i)) == 0u) {
            continue;
        }
        if (selected_index == 0u) {
            return (uint8_t)i;
        }
        selected_index--;
    }

    /* Unreachable for a stable mask; retain a safe fallback for corruption. */
    return 0u;
}

static inline uint8_t ap_statue_apply_final_gate(
    uint8_t transition_flags,
    uint32_t gate_mask,
    uint32_t unlock_mask
) {
    uint8_t ability_id = (uint8_t)(transition_flags & AP_STATUE_ABILITY_ID_MASK);
    if (ap_statue_is_locked_ability(ability_id, gate_mask, unlock_mask) != 0u) {
        return (uint8_t)(transition_flags & (uint8_t)~AP_STATUE_ABILITY_ID_MASK);
    }
    return transition_flags;
}

static inline uint8_t ap_statue_replace_ability_bits(
    uint8_t transition_flags,
    uint8_t ability_id
) {
    return (uint8_t)(
        (transition_flags & (uint8_t)~AP_STATUE_ABILITY_ID_MASK)
        | (ability_id & AP_STATUE_ABILITY_ID_MASK)
    );
}

#endif
