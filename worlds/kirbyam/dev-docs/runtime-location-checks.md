# Runtime Location Checks

This document defines how each KirbyAM location type is read at runtime.

## Polling loop entry point

All location polling runs in worlds/kirbyam/client.py from KirbyAmClient.game_watcher(), in this order:

1. Boss defeat
2. Major chest
3. Minor chest
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

Minor chest reporting uses one exact path: the event ring's source pointer must
match the `source_rom_offset` of one active physical location. Native small chest
and collectible bitfields are not used to infer location checks because the same
bits can represent multiple physical chests. Nearby source-pointer offsets are
not treated as aliases.

Only the fourteen verified rows in this rollout have source offsets. Older
spray-paint/music-note metadata rows remain dormant because they identify reward
collections, not unique physical chests.

## Active-location filtering

When slot_data includes a reduced location set, the client filters mapped checks to active IDs via _active_location_id_set(). This prevents reporting checks that are not part of the current generated slot.
