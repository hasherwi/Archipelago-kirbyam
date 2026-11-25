#ifndef KIRBYAM_STATUE_ART_RUNTIME_H
#define KIRBYAM_STATUE_ART_RUNTIME_H

#include <stdint.h>

#define AP_STATUE_ART_SIZE 128u

/* Native sprite DMA attaches a 12-byte record to its 64-slot queue. */
struct ApStatueTileUpload {
    uint32_t source;
    uint32_t destination;
    uint16_t size;
    uint16_t padding;
};

static inline uint8_t ap_statue_vram_address_is_valid(uint32_t address) {
    return address >= 0x06014000u && address <= 0x06018000u - AP_STATUE_ART_SIZE;
}

#define AP_STATUE_COPY_ROOM 970u
#define AP_STATUE_LOGO 0xFFu
#define AP_STATUE_NATIVE_ANIM 0x384u
#define AP_STATUE_NATIVE_TILES 0x087E63ECu
#define AP_STATUE_SLOT_COUNT 19u

struct ApStatueConfig {
    char magic[8];
    uint8_t mode;
    uint8_t assignments[AP_STATUE_SLOT_COUNT];
};

static inline uint8_t ap_statue_world_mode(uint16_t room, const volatile struct ApStatueConfig *config) {
    uint8_t mode = config->mode;
    return room != AP_STATUE_COPY_ROOM && (mode == 1u || mode == 2u) ? mode : 0u;
}

static inline uint8_t ap_statue_slot(uint8_t type, uint8_t subtype) {
    switch (type) {
        case 0x92u: if (subtype < 8u) return subtype; break;
        case 0x93u: if (subtype < 7u) return 8u + subtype; break;
        case 0x94u: if (!subtype) return 15u; break;
        case 0x95u: if (subtype < 3u) return 16u + subtype; break;
        default: break;
    }
    return AP_STATUE_SLOT_COUNT;
}

static inline uint8_t ap_statue_world_ability(uint16_t room, uint8_t type, uint8_t subtype,
                                              const volatile struct ApStatueConfig *config) {
    uint8_t slot = ap_statue_slot(type, subtype);
    if (!ap_statue_world_mode(room, config) || slot >= AP_STATUE_SLOT_COUNT) return 0u;
    uint8_t ability = config->assignments[slot];
    return ability < 32u ? ability : 0u;
}

static inline uint8_t ap_statue_world_art(uint16_t room, uint8_t type, uint8_t variant,
                                         const volatile struct ApStatueConfig *config) {
    uint8_t mode = ap_statue_world_mode(room, config);
    if (!mode) return 0u;
    /* The retail Parasol variant follows 0x95 in the art atlas, although
     * it precedes it in the native assignment table. */
    uint8_t base = type == 0x92u ? 11u : type == 0x93u ? 19u : type == 0x94u ? 29u : 26u;
    uint8_t ability = ap_statue_world_ability(room, type, variant - base, config);
    return ability && mode == 2u ? AP_STATUE_LOGO : ability;
}

static inline uint8_t ap_statue_replace_upload(volatile struct ApStatueTileUpload *ring, uint8_t before,
                                                uint8_t after, uint32_t destination, uint8_t variant,
                                                uint32_t replacement) {
    if (before >= 64u || after != ((before + 1u) & 63u) || variant < 11u || variant > 29u
        || !ap_statue_vram_address_is_valid(destination)) return 0u;
    volatile struct ApStatueTileUpload *upload = &ring[before];
    if (upload->source != AP_STATUE_NATIVE_TILES + (variant - 11u) * AP_STATUE_ART_SIZE
        || upload->destination != destination || upload->size != AP_STATUE_ART_SIZE) return 0u;
    upload->source = replacement;
    return 1u;
}

/* Decide for the tiles that will actually be visible, not just the configured
 * art. The newest overlapping queued DMA wins; otherwise verify resident
 * tiles. This needs no side state keyed to a room or recycled object slot. */
static inline uint8_t ap_statue_tiles_confirmed(const volatile struct ApStatueTileUpload *ring,
                                                uint8_t head, uint8_t tail, uint32_t destination,
                                                uint32_t replacement, const volatile uint32_t *resident,
                                                const volatile uint32_t *expected) {
    if (head >= 64u || tail >= 64u || (destination | replacement) & 3u
        || !ap_statue_vram_address_is_valid(destination)) return 0u;
    while (head != tail) {
        head = (head - 1u) & 63u;
        const volatile struct ApStatueTileUpload *upload = &ring[head];
        uint32_t start = upload->destination;
        uint32_t size = upload->size;
        if (size && start < destination + AP_STATUE_ART_SIZE
            && (start >= destination || destination - start < size)) {
            return start == destination && size == AP_STATUE_ART_SIZE && upload->source == replacement;
        }
    }
    for (uint32_t i = 0u; i < AP_STATUE_ART_SIZE / sizeof(uint32_t); ++i) {
        if (resident[i] != expected[i]) return 0u;
    }
    return 1u;
}

#endif
