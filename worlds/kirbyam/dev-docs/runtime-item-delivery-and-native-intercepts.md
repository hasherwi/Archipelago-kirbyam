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
| Mirror shards | +2..+9 | Set KIRBY_SHARD_FLAGS and AP shard authority; normal native save flow owns persistence |
| Area maps | +10..+17 and +24 | Set native big chest map bits via ap_unlock_area_map() |
| Vitality counters | +18..+21 | Increment vitality once per item index using AP_DELIVERED_VITALITY_ITEM_BITS replay guard |
| Sound Player | +25 | Call KIRBY_COLLECT_SOUND_PLAYER_FN(0) |
| Consumables | +26..+31 | Grant food, battery, max tomato, invincibility candy, energy drink, hunk of meat |
| Traps | +32..+36 | Apply health/life/bomb/battery/lives penalties |
| Spray Paint | +200..+213 | OR native `gTreasures.sprayPaintField` bits 0..13 |
| Music Sheets | +214..+223 | OR native `gTreasures.musicPlayerAndSheetsField` bits 1..10, preserving Sound Player bit 0 |

Unknown IDs are left unhandled and do not ACK-clear, by design, to avoid silent loss.

## Native reward interception policy

AP mode records checks and handles native reward paths by item family. Ordinary small-chest consumables use the delayed popup hook from PR #931; fixed small-chest collections use their native grant callsites (#525, #535, #537).

| Native reward event | Hook | Interception behavior |
|---|---|---|
| Boss shard reward | ap_on_boss_defeat_collect_shard() | Record boss-defeat check transport flag. Preserve temporary native shard write for cutscene safety, then rely on AP shard ownership/scrub logic for authority. |
| Boss already-owned reward path | ap_on_boss_defeat_already_owned_reward() | Record boss-defeat check even when native CollectShard path is skipped. |
| Major chest map reward | ap_on_collect_big_chest() | Record AP major-chest flag. Keep map unlock AP-item-only for area maps (bits 1..9), while preserving native world-map unlock for the tutorial chest (bit 0). |
| Vitality big chest reward | ap_on_collect_vitality_chest() | Convert room reward event to AP vitality-chest transport bit. |
| Sound Player chest path | ap_on_collect_sound_player_chest() | Reward index 0 remains the AP Sound Player chest check. Nonzero Music Sheets suppress their ownership grant for exact AP sources; unknown sources retain native bitwise collection behavior. |
| Spray paint chest reward | ap_on_collect_spray_paint_chest() | Suppress ownership grant only for exact AP sources. The generic small-chest hook has already recorded the physical check event and persistence. |
| Small-chest AP location | ap_on_collect_small_chest() | Record the exact source pointer and native small-chest persistence for each of 64 active checks; the client maps only exact matches. |
| Ordinary consumable chest reward | ap_minor_chest_reward_popup_hook | After native persistence and the popup delay, set only marked AP-owned chests to the existing no-bonus item value (`0x63`); the AP mailbox grants the assigned reward. Other small chests retain their native item. |
| Fixed small-chest collection reward | Native chest collection hooks | 23 fixed chests are AP locations. Candy Spray Paint #6 is isolated to the 9-01 entry compartment; Music Sheet #6 stays native pending Carrot topology reconciliation. Ownership is awarded only on matching AP item delivery; duplicate delivery is idempotent. Native persistence and original visuals are preserved. |
| Hub unlock/world map door unlock | ap_on_world_map_unlock_call() | Record AP hub-switch flag when unlock is persisted in world props. |

## Client-side reconciliation that enforces AP ownership

worlds/kirbyam/client.py runs these every active gameplay tick:

- _reconcile_native_shard_ownership(): keeps shard bits aligned to AP-delivered ownership.
- _reconcile_native_map_ownership(): keeps native map bits aligned to AP-delivered maps and start_with_all_maps.

These reconciliation passes are the final guardrails that interrupt native drift from save/load/cutscene edge cases.

## Custom health range (Issue #778)

Generation and the client share `health.py`. Only a supported prefix of the
four existing unique Vitality Counter IDs is placed; native payload grants
remain unchanged and replay-guarded. The client reuses the same native HP/max
HP/vitality fields used by One-Hit Mode. It reconciles custom capacity only in
the gameplay branch of the watcher and guards every write against the read
snapshot. No new payload build, ROM offsets, or mailbox registers are needed.

Before release, validate starts 1/6/8/10, zero/fewer/four counters, full and
partial healing, damage/DeathLink, death/respawn, room transitions, reconnect,
soft reset/save load, and the HP meter. Verify both One-Hit presets still
override custom options. Known inherited limit: native health is observable
until the next connected-client poll; offline custom enforcement is not
implemented. Do not claim a Python pass validates those emulator paths.
