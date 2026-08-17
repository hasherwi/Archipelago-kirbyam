# Runtime Item Delivery And Native Reward Intercepts

This document defines how AP items are injected and how native reward paths are intercepted when a location becomes AP-owned.

## AP item injection path

1. worlds/kirbyam/client.py _deliver_items() writes mailbox fields:
   - incoming_item_id
   - incoming_item_player
   - incoming_item_flag = 1
2. kirby_ap_payload/ap_payload.c ap_poll_mailbox_c() consumes mailbox entries.
3. ap_apply_item(ap_item_id) applies the item effect.
4. Payload clears incoming_item_flag to ACK.
5. Client observes ACK and advances delivered_item_index.

## Item type handling in ap_apply_item()

| AP item family | IDs (base offset relative) | Runtime effect |
|---|---|---|
| 1-UP | +1 | ap_grant_lives(1) |
| Mirror shards | +2..+9 | Set KIRBY_SHARD_FLAGS, AP shard authority bitfield, and persist shard state to SRAM |
| Area maps | +10..+17 and +24 | Set native big chest map bits via ap_unlock_area_map() |
| Vitality counters | +18..+21 | Increment vitality once per item index using AP_DELIVERED_VITALITY_ITEM_BITS replay guard |
| Sound Player | +25 | Call KIRBY_COLLECT_SOUND_PLAYER_FN(0) |
| Consumables | +26..+31 | Grant food, battery, max tomato, invincibility candy, energy drink, hunk of meat |
| Traps | +32..+36 | Apply health/life/bomb/battery/lives penalties |

Unknown IDs are left unhandled and do not ACK-clear, by design, to avoid silent loss.

## Native reward interception policy

AP mode records checks and suppresses or normalizes native rewards so progression is AP-authoritative.

| Native reward event | Hook | Interception behavior |
|---|---|---|
| Boss shard reward | ap_on_boss_defeat_collect_shard() | Record boss-defeat check transport flag. Preserve temporary native shard write for cutscene safety, then rely on AP shard ownership/scrub logic for authority. |
| Boss already-owned reward path | ap_on_boss_defeat_already_owned_reward() | Record boss-defeat check even when native CollectShard path is skipped. |
| Major chest map reward | ap_on_collect_big_chest() | Record AP major-chest flag. Keep map unlock AP-item-only for area maps (bits 1..9), while preserving native world-map unlock for the tutorial chest (bit 0). |
| Vitality big chest reward | ap_on_collect_vitality_chest() | Convert room reward event to AP vitality-chest transport bit. |
| Sound Player chest path | ap_on_collect_sound_player_chest() | Reward index 0 becomes AP Sound Player chest check; other rewards route through AP-owned minor chest collection recording. |
| Spray paint chest reward | ap_on_collect_spray_paint_chest() | Suppress native reward grant; only record AP-owned minor chest collection transport/native persistence bits. |
| Small chest reward | ap_on_collect_small_chest() | Record exact source pointer and native small-chest persistence so client can map to correct AP minor location. |
| Hub unlock/world map door unlock | ap_on_world_map_unlock_call() | Record AP hub-switch flag when unlock is persisted in world props. |

## Client-side reconciliation that enforces AP ownership

worlds/kirbyam/client.py runs these every active gameplay tick:

- _reconcile_native_shard_ownership(): keeps shard bits aligned to AP-delivered ownership.
- _reconcile_native_map_ownership(): keeps native map bits aligned to AP-delivered maps and start_with_all_maps.

These reconciliation passes are the final guardrails that interrupt native drift from save/load/cutscene edge cases.
