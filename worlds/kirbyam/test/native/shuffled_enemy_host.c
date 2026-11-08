/* Issue #1049: exercise the production resolver after native state overwrites.
 * This is a host policy regression, not a retail-ROM/emulator playthrough. */
#include "enemy_runtime_logic.h"
#define CHECK(c) do { if (!(c)) return __LINE__; } while (0)
#define RESOLVE(mode, caller, ptr, type, flags) \
    ap_enemy_shuffled_ability_flags(config, mode, caller, ptr, type, flags, table)
int main(void) {
    uint32_t config[9] = {AP_ENEMY_SOURCE_CONFIG_MAGIC};
    uint8_t table[256 * 24] = {0};
    uint32_t type, ability, mode, flags;
    const uint32_t ordinary = AP_ENEMY_SWALLOW_CALLSITE;
    const uint32_t pointer = 0x02001000u;
    /* Waddle Doo is table index 18. Seed chooses Sword (18), while the
     * native walking reset writes Beam (7) and parasol states write 5. */
    type = 18;
    config[1] = 1u << type;
    table[type * 24] = 18;
    CHECK(RESOLVE(1, ordinary, pointer, type, 7) == 18);
    CHECK(RESOLVE(1, ordinary, pointer, type, 5) == 18);
    /* Same seed assignment survives repeated native state resets. */
    for (ability = 0; ability < 32; ability++)
        CHECK(RESOLVE(1, ordinary, pointer, type, ability) == 18);
    /* Explicit no-ability assignments must also beat native Beam. */
    table[type * 24] = 0;
    CHECK(RESOLVE(1, ordinary, pointer, type, 7) == 0);
    /* Exhaust source bitmap boundaries, all ability IDs and flag retention. */
    for (type = 0; type < 256; type++) {
        config[1 + type / 32] |= 1u << (type % 32);
        for (ability = 0; ability < 32; ability++) {
            table[type * 24] = ability;
            for (flags = 0; flags < 256; flags++)
                CHECK(RESOLVE(1, ordinary, pointer, type, flags) == ((flags & ~31u) | ability));
        }
        for (mode = 0; mode < 4; mode++) {
            if (mode != 1) CHECK(RESOLVE(mode, ordinary, pointer, type, 7) == 7);
        }
        /* Disabled passive enemies, Minny, minibosses and boss-spawned
         * sources all use this same per-seed exclusion bit. */
        config[1 + type / 32] &= ~(1u << (type % 32));
        CHECK(RESOLVE(1, ordinary, pointer, type, 7) == 7);
    }
    config[1] = 1u << 18;
    table[18 * 24] = 18;
    CHECK(RESOLVE(1, ordinary, 0x03001000u, 18, 7) == 18);
    /* Recovery stars, statues/special objects and unverified sources must
     * never be interpreted as ordinary enemies, even if r5 looks valid. */
    CHECK(RESOLVE(1, 0x0809C69Cu, pointer, 18, 0x97) == 0x97);
    CHECK(RESOLVE(1, 0x0809C674u, pointer, 18, 7) == 7);
    CHECK(RESOLVE(1, 0, pointer, 18, 7) == 7);
    CHECK(RESOLVE(1, ordinary, 0, 18, 7) == 7);
    CHECK(RESOLVE(1, ordinary, pointer + 1, 18, 7) == 7);
    CHECK(RESOLVE(1, ordinary, 0x08000000u, 18, 7) == 7);
    CHECK(RESOLVE(1, ordinary, 0x0203FF80u, 18, 7) == 7);
    CHECK(RESOLVE(1, ordinary, pointer, 256, 7) == 7);
    CHECK(RESOLVE(1, ordinary, pointer, 0xFFFFFFFFu, 7) == 7);
    table[18 * 24] = 255;
    CHECK(RESOLVE(1, ordinary, pointer, 18, 7) == 7);
    table[18 * 24] = 18;
    config[0] = AP_ENEMY_SOURCE_CONFIG_LEGACY;
    CHECK(RESOLVE(1, ordinary, pointer, 18, 7) == 7);
    config[0] = 0xFFFFFFFFu;
    CHECK(RESOLVE(1, ordinary, pointer, 18, 7) == 7);
    return 0;
}
