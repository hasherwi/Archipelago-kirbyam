#ifndef KIRBYAM_ENEMY_RUNTIME_LOGIC_H
#define KIRBYAM_ENEMY_RUNTIME_LOGIC_H

#include <stdint.h>

/* US ROM sub_0809C48C: ordinary object swallow BL at 0x0809C6AA.
 * r5 is Object2*, type at +0x82; Minny is OBJ_MINNY (0x27).
 * The separate ability-star (0x0809C69C), special-object (0x0809C674)
 * and effect-object callers do not qualify for this exception.
 */
#define AP_ENEMY_SWALLOW_CALLSITE 0x0809C6AAu
#define AP_ENEMY_MINNY_TYPE 0x27u

/* TaskCreate may fall back from EWRAM to IWRAM for an enemy allocation.
 * Share this check to fit the fixed payload window.
 */
static __attribute__((noinline)) uint8_t ap_enemy_source_pointer_is_readable(uint32_t source_ptr) {
    return ((source_ptr & 3u) == 0u
        && ((source_ptr - 0x02000000u < 0x40000u - 0x82u)
            || (source_ptr - 0x03000000u < 0x8000u - 0x82u))) ? 1u : 0u;
}

static inline uint8_t ap_enemy_has_verified_source(uint32_t caller_pc, uint32_t source_ptr) {
    return (caller_pc == AP_ENEMY_SWALLOW_CALLSITE
        && ap_enemy_source_pointer_is_readable(source_ptr) != 0u) ? 1u : 0u;
}

static inline uint8_t ap_enemy_should_reroll(
    uint32_t mode, uint32_t randomize_minny, uint8_t verified_source_type
) {
    if (mode != 2u) return 0u;
    /* Unknown callers/pointers retain the existing reroll behavior.
     * Pass 0xFF for unverified sources. Never infer Minny from an ability ID:
     * enemies and stars can also grant Mini.
     */
    return (randomize_minny == 0u
        && verified_source_type == AP_ENEMY_MINNY_TYPE) ? 0u : 1u;
}

/* Native star swallow loads Object2::kirbyAbility from r5+0x84 and ORs
 * 0x80 at 0x0809C69C. Preserve only raw Mini from verified A3/A4 stars.
 * Do not infer recovery from Mini on an ordinary randomized enemy. The
 * caller still applies the request gate and authoritative commit gate.
 */
static inline uint8_t ap_is_mini_star_recovery(
    uint32_t caller_pc, uint32_t source_ptr, uint32_t ability_flags
) {
    uint8_t type;
    if (caller_pc != 0x0809C69Cu || (ability_flags & 0x9Fu) != 0x97u
        || ap_enemy_source_pointer_is_readable(source_ptr) == 0u) return 0u;
    type = *(volatile uint8_t *)(uintptr_t)(source_ptr + 0x82u);
    return (type == 0xA3u || type == 0xA4u) ? 1u : 0u;
}

#define AP_ENEMY_SOURCE_CONFIG_MAGIC 0x41534501u
#define AP_ENEMY_SOURCE_CONFIG_LEGACY 0x41534500u

/* Only verified ordinary-swallow Object2 sources consult the per-seed bitmap.
 * Stars and unrelated callers retain their established reroll behavior. */
static inline uint8_t ap_enemy_source_policy_allows(
    const volatile uint32_t *config, uint32_t caller_pc, uint32_t source_ptr,
    uint32_t source_type
) {
    if (ap_enemy_has_verified_source(caller_pc, source_ptr) == 0u) return 1u;
    if (config[0] != AP_ENEMY_SOURCE_CONFIG_MAGIC) return 1u;
    if (source_type >= 256u) return 0u;
    return (uint8_t)((config[1u + (source_type >> 5)] >> (source_type & 31u)) & 1u);
}

#endif
