# Runtime Location Checks

This document defines how each KirbyAM location type is read at runtime.

## Polling loop entry point

All location polling runs in worlds/kirbyam/client.py from KirbyAmClient.game_watcher(), in this order:

1. Boss defeat
2. Major chest
3. Saved physical chest recovery, then minor chest events
4. Vitality chest
5. Sound Player chest
6. Hub switch
7. Area visit
8. Room sanity

Each poll computes mapped AP location IDs and sends LocationChecks for IDs not yet acknowledged by the server.

## Location type matrix

| Location type | Runtime signal source | Writer side | Client reader |
|---|---|---|---|
| BOSS_DEFEAT | AP_BOSS_DEFEAT_FLAGS transport bitfield | payload hook ap_on_boss_defeat_collect_shard() and ap_on_boss_defeat_already_owned_reward() in kirby_ap_payload/ap_payload.c | _poll_boss_defeat_locations() |
| MAJOR_CHEST | AP_MAJOR_CHEST_FLAGS transport bitfield | payload hook ap_on_collect_big_chest() | _poll_major_chest_locations() |
| MINOR_CHEST | Exact source-pointer event ring | payload hook ap_on_collect_small_chest() records the source pointer and native persistence bit; native reward callsites remain intact | _poll_minor_chest_locations() delegates to _poll_minor_chest_event_locations() |
| VITALITY_CHEST | AP_VITALITY_CHEST_FLAGS transport bitfield | payload hook ap_on_collect_vitality_chest() | _poll_vitality_chest_locations() |
| SOUND_PLAYER_CHEST | AP_SOUND_PLAYER_CHEST_FLAGS transport bitfield | payload hook ap_on_collect_sound_player_chest() | _poll_sound_player_chest_locations() |
| HUB_SWITCH | AP_HUB_SWITCH_FLAGS transport bitfield | payload hook ap_on_world_map_unlock_call() and world-props sync helpers | _poll_hub_switch_locations() |
| AREA_VISIT | Native gVisitedDoors bit-15 interpreted via doorsIdx -> area mapping | native game room-visit state | _poll_area_visit_locations() |
| ROOM_SANITY | Native gVisitedDoors bit-15 interpreted directly by doorsIdx | native game room-visit state | _poll_room_sanity_locations() |
| GOAL | Native AI state signal + AP checked location state | native gameplay state + client-side goal option | _maybe_report_goal() |

## Minor chest disambiguation details

All 65 physical USA small chests are active: 41 ordinary rewards, 14 Spray
Paints, and 10 Music Sheets. Historical AP IDs remain stable. Every exact event
must match a verified `source_rom_offset`; nearby pointers are not aliases.
Music Sheet 6 is source `0x008D3E64`, native flag 81, reward 46, AP ID 3960519,
in the upper Carrot 5-13 compartment entered from 5-14. The lower 1UP belongs
to the separate entrance from 5-07.

The eight-entry event ring provides prompt reporting. On counter rollback the
client replays its retained window. Observed checks remain pending until server
acknowledgment. Independently, `_poll_saved_chest_locations` reads the 16-byte
native `chestFields` at `0x02038960` each gameplay poll. A complete scan of 287
USA object lists establishes 84 unique flags (0..83): 65 small chests, 15 reward
big chests, and four levers. `chest_recovery.json` maps the 80 reward chests;
lever flags are excluded because they have item-owned semantics. Tutorial
polling recovers only the tutorial World Map. Recovery filters active server
locations and acknowledgments, and discards reads across session changes.

Native chest flags are physical collection state, unlike reward ownership.
A same-seed native save can recover an event overwritten while disconnected;
unsaved collection lost by resetting before a native save cannot be recovered
from the older save. Importing vanilla or other-seed saves is unsupported: the
native save has no AP seed identity. This is not an exactly-once item-delivery
or native-save-flush guarantee.

This location-only foundation preserves native ordinary, paint, and music
rewards. It adds no collection item IDs, pool entries, or suppression hooks.
The later reward PRs must be reconciled onto this expanded location baseline.

The physical inventory is reproducible with `tools/verify_chest_recovery.py`
and an owner-provided unmodified USA ROM (SHA-1
`274b102b6d940f46861a92b4e65f89a51815c12c`). Native collection/save semantics
are cross-checked against [the pinned decompilation](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/chest.c)
and its `src/treasures.c`. No ROM bytes are included in the repository.

### v0.4.0 starting access

All 65 checks are reachable in the current AP graph with no received AP items
after native event sweeping. The native copy abilities Beam, Burning, Cutter,
Mini, Stone, and Wheel remain ungated even with `ability_gating: true`; they
are not six precollected AP items. The set intersects every current capability
group, and capability rules remain permissive. No hub/area keys or new route
requirements are introduced here. Physical traversal still requires playing
the native game; this graph test is not a gameplay or timed-gate validation.

The default enemy randomization mode is off. Optional shuffled/random modes
can alter where abilities occur; in particular `ability_randomization_no_ability_weight:
100` removes every participating enemy's grant, including Minny when its toggle
is on. Statues remain a separate source. Therefore the ungated set alone does
not establish a universal physical starting-access guarantee for every custom
randomization setting. This existing option behavior is not changed here.

## Active-location filtering

When slot_data includes a reduced location set, the client filters mapped checks to active IDs via _active_location_id_set(). This prevents reporting checks that are not part of the current generated slot.
