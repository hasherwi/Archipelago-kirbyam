#include <stdint.h>

/*
 * Issue #875: direct ability-statue touches bypass sub_080547C4, so the
 * generation-time statue table mapping was reused on every touch even in
 * completely-random mode.  This module replaces the Issue #874
 * transition-start hook with a superset that handles both gating and live
 * per-touch randomization.
 */

#define AP_BASE 0x0203B000u
#define AP_ABILITY_RANDOMIZATION_MODE (*(volatile uint32_t *)(AP_BASE + 0x64u))
#define AP_ABILITY_RANDOMIZATION_SEED_LO (*(volatile uint32_t *)(AP_BASE + 0x68u))
#define AP_ABILITY_RANDOMIZATION_SEED_HI (*(volatile uint32_t *)(AP_BASE + 0x6Cu))
#define AP_ABILITY_RANDOMIZATION_ALLOWED_MASK (*(volatile uint32_t *)(AP_BASE + 0x74u))
#define AP_ABILITY_RANDOMIZATION_RNG_STATE (*(volatile uint32_t *)(AP_BASE + 0x78u))
#define AP_ABILITY_REROLL_EVENT_COUNTER (*(volatile uint32_t *)(AP_BASE + 0x7Cu))
#define AP_ABILITY_REROLL_SOURCE_ADDR (*(volatile uint32_t *)(AP_BASE + 0x80u))
#define AP_ABILITY_REROLL_ABILITY_ID (*(volatile uint32_t *)(AP_BASE + 0x84u))
#define AP_ABILITY_REROLL_SOURCE_KIND (*(volatile uint32_t *)(AP_BASE + 0x5Cu))
#define AP_ABILITY_REROLL_CALLSITE_PC (*(volatile uint32_t *)(AP_BASE + 0x60u))
#define AP_ABILITY_REROLL_KIRBY_INDEX (*(volatile uint32_t *)(AP_BASE + 0x88u))
#define AP_ABILITY_GATE_MASK (*(volatile uint32_t *)(AP_BASE + 0xB0u))
#define AP_ABILITY_UNLOCK_MASK (*(volatile uint32_t *)(AP_BASE + 0xB4u))

#define KIRBY_CURRENT_PLAYER (*(volatile uint8_t *)0x0203AD3Cu)
#define KIRBY_TRANSITIONING_ABILITY_OFFSET 0xDDu
#define KIRBY_ABILITY_MASK 0x1Fu

#define ABILITY_RANDOMIZATION_MODE_SHUFFLED 1u
#define ABILITY_RANDOMIZATION_MODE_COMPLETELY_RANDOM 2u
#define ABILITY_REROLL_SOURCE_KIND_ABILITY_STATUE 4u

/* sub_080AA588 is the regular ability-statue touch callback.  The next
 * function, sub_080AA618, is the Master Sword stand and is intentionally not
 * part of the configurable statue-randomization table. */
#define ABILITY_STATUE_TOUCH_FN_START_ADDR 0x080AA588u
#define ABILITY_STATUE_TOUCH_FN_END_ADDR 0x080AA618u

typedef void (*KirbyStartAbilityTransitionFn)(void *kirby);
#define KIRBY_START_ABILITY_TRANSITION_FN ((KirbyStartAbilityTransitionFn)0x08054C0Du)

/*
 * Per-seed ROM config.  rom.py writes 0 or 1 at file offset 0x15F69C after
 * applying the shared base patch.  volatile prevents the compiler from
 * constant-folding the default value before the token write is applied.
 */
__attribute__((used, section(".apconfig")))
volatile const uint32_t gApAbilityRandomizationStatuesEnabled = 0u;

static uint32_t ap_statue_mix_u32(uint32_t value) {
    value ^= value >> 16;
    value *= 0x7FEB352Du;
    value ^= value >> 15;
    value *= 0x846CA68Bu;
    value ^= value >> 16;
    return value;
}

static uint32_t ap_statue_next_rng_u32(void) {
    uint32_t state = AP_ABILITY_RANDOMIZATION_RNG_STATE;

    if (state == 0u) {
        state = ap_statue_mix_u32(
            AP_ABILITY_RANDOMIZATION_SEED_LO
            ^ (AP_ABILITY_RANDOMIZATION_SEED_HI * 0x9E3779B9u)
            ^ 0xA5C39E21u
        );
        if (state == 0u) {
            state = 0x6D2B79F5u;
        }
    }

    state ^= state << 13;
    state ^= state >> 17;
    state ^= state << 5;
    if (state == 0u) {
        state = 0x6D2B79F5u;
    }

    AP_ABILITY_RANDOMIZATION_RNG_STATE = state;
    return state;
}

static uint8_t ap_statue_select_random_ability(uint32_t allowed_mask, uint32_t random_value) {
    uint32_t count = 0u;
    uint32_t ability_id;
    uint32_t selected_index;

    for (ability_id = 1u; ability_id <= KIRBY_ABILITY_MASK; ability_id++) {
        if ((allowed_mask & (1u << ability_id)) != 0u) {
            count++;
        }
    }
    if (count == 0u) {
        return 0u;
    }

    selected_index = random_value % count;
    for (ability_id = 1u; ability_id <= KIRBY_ABILITY_MASK; ability_id++) {
        if ((allowed_mask & (1u << ability_id)) == 0u) {
            continue;
        }
        if (selected_index == 0u) {
            return (uint8_t)ability_id;
        }
        selected_index--;
    }

    return 0u;
}

static uint8_t ap_statue_is_locked(uint8_t ability_id) {
    uint32_t bit = 1u << (uint32_t)ability_id;
    return ((AP_ABILITY_GATE_MASK & bit) != 0u
            && (AP_ABILITY_UNLOCK_MASK & bit) == 0u) ? 1u : 0u;
}

static uint8_t ap_is_direct_ability_statue_callsite(uint32_t caller_pc) {
    return (caller_pc >= ABILITY_STATUE_TOUCH_FN_START_ADDR
            && caller_pc < ABILITY_STATUE_TOUCH_FN_END_ADDR) ? 1u : 0u;
}

/*
 * Public replacement hook resolved by patch_rom.py.
 *
 * - All transition sources still receive the Issue #874 final gating check.
 * - Direct regular-statue touches reroll once per touch in completely-random
 *   mode when ability_randomization_statues is enabled.
 * - Locked abilities are removed from the candidate mask before selection, so
 *   gating never turns a valid random statue touch into Normal unless no
 *   unlocked candidate remains.
 * - Statues intentionally ignore no-ability weight.
 * - Consecutive independent rolls may legitimately select the same ability.
 */
__attribute__((used))
void ap_on_start_copy_ability_transition(void *kirby) {
    uint32_t caller_lr_snapshot;
    uint32_t caller_pc;
    volatile uint8_t *transitioning_ability;
    uint8_t pending_flags;
    uint8_t native_ability;
    uint8_t selected_ability;
    uint32_t mode;
    uint8_t direct_statue;

    __asm__ volatile("mov %0, lr" : "=r"(caller_lr_snapshot));
    caller_pc = caller_lr_snapshot & ~1u;
    if (caller_pc >= 4u) {
        caller_pc -= 4u;
    }

    if (kirby == (void *)0) {
        return;
    }

    transitioning_ability =
        (volatile uint8_t *)((uintptr_t)kirby + KIRBY_TRANSITIONING_ABILITY_OFFSET);
    pending_flags = *transitioning_ability;
    native_ability = (uint8_t)(pending_flags & KIRBY_ABILITY_MASK);
    selected_ability = native_ability;
    mode = AP_ABILITY_RANDOMIZATION_MODE;
    direct_statue = ap_is_direct_ability_statue_callsite(caller_pc);

    if (direct_statue != 0u
        && gApAbilityRandomizationStatuesEnabled != 0u
        && mode == ABILITY_RANDOMIZATION_MODE_COMPLETELY_RANDOM) {
        uint32_t locked_mask = AP_ABILITY_GATE_MASK & ~AP_ABILITY_UNLOCK_MASK;
        uint32_t unlocked_allowed_mask =
            AP_ABILITY_RANDOMIZATION_ALLOWED_MASK & ~locked_mask;

        selected_ability = ap_statue_select_random_ability(
            unlocked_allowed_mask,
            ap_statue_next_rng_u32()
        );
        pending_flags = (uint8_t)(
            (pending_flags & (uint8_t)~KIRBY_ABILITY_MASK)
            | (selected_ability & KIRBY_ABILITY_MASK)
        );
    }

    /* Final authority for Issue #874, including shuffled/off modes and every
     * other path that writes Kirby::transitioningAbility directly. */
    selected_ability = (uint8_t)(pending_flags & KIRBY_ABILITY_MASK);
    if (selected_ability != 0u && ap_statue_is_locked(selected_ability) != 0u) {
        pending_flags = (uint8_t)(pending_flags & (uint8_t)~KIRBY_ABILITY_MASK);
        selected_ability = 0u;
    }
    *transitioning_ability = pending_flags;

    if (direct_statue != 0u
        && gApAbilityRandomizationStatuesEnabled != 0u
        && (mode == ABILITY_RANDOMIZATION_MODE_SHUFFLED
            || mode == ABILITY_RANDOMIZATION_MODE_COMPLETELY_RANDOM)) {
        AP_ABILITY_REROLL_SOURCE_ADDR = (uint32_t)native_ability;
        AP_ABILITY_REROLL_ABILITY_ID = (uint32_t)selected_ability;
        AP_ABILITY_REROLL_SOURCE_KIND = ABILITY_REROLL_SOURCE_KIND_ABILITY_STATUE;
        AP_ABILITY_REROLL_CALLSITE_PC = caller_pc;
        AP_ABILITY_REROLL_KIRBY_INDEX = (uint32_t)KIRBY_CURRENT_PLAYER;
        AP_ABILITY_REROLL_EVENT_COUNTER++;
    }

    KIRBY_START_ABILITY_TRANSITION_FN(kirby);
}
