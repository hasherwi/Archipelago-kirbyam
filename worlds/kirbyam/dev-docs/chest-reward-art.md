# Shared location reward art

Every treasure chest uses the supplied six-gem reward art on opening. The
closed chest, rising popup motion, sounds, duration, original reward logic, and
check IDs are unchanged. A physical lever pull shows the same art because it
uses the same native popup path. Receiving Lever Wall, restoring a lever, or
re-entering its room does not show the art. The same gem also appears on the
first physical press of an Archipelago Big Switch and the first completion
of each Goal Game check (even with no native prize), on first area visits,
and on the first defeat of each area boss. Other reward surfaces are unchanged.

| Original | Same frame with this patch |
| --- | --- |
| ![Native map reward](chest_reward_art_before.png) | ![Six-gem popup](chest_reward_art_in_game.png) |

Both panels are native mGBA frames from a cold Tutorial World Map Chest replay
(room 805, frame 18405), with identical input and no gameplay-RAM edits. Exactly
206 rendered pixels differ, all inside the 16×16 sprite at (104, 57).
The compared runs recorded the same chest flags and reached Central Circle.

## Physical lever replay

| Chest-only control | Same frame with lever art |
| --- | --- |
| ![Lever without a reward sprite](lever_reward_art_before.png) | ![Six-gem popup after a physical lever pull](lever_reward_art_in_game.png) |

These are native mGBA frames from Moonlight Mansion Room 2-11 (internal room
743), 12 frames after the physical lever pull at frame 40902. Both input-only
runs started from blank SRAM and matched all 115 replay checkpoints through
frame 41104, with no gameplay RAM edits or save-state loads. All changed pixels
in the comparison are inside the 16×16 sprite at (115, 41). Only the candidate
queued the gem on the pull. Both runs recorded the same physical activation
flags, and neither granted Lever Wall ownership.

## Physical Big Switch replay

| Chest/lever-only control | Same frame with Big Switch art |
| --- | --- |
| ![Pressed Big Switch without the gem](big_switch_reward_art_before.png) | ![Six-gem popup after a physical Big Switch press](big_switch_reward_art_in_game.png) |

These are native mGBA frames in Moonlight Mansion Room 2-6 (internal room 790),
four frames after the physical press. Both runs started from the same tracked
pre-press state and used the same controller input, with no runtime memory edits.
All 196 changed pixels in this frame are inside the 16×16 gem at (120, 80).
The two runs matched all recorded gameplay fields over 712 frames, including
the native pause and map sequence, the AP check and save at frame 75, player
positions, and the later exit and re-entry. The corresponding hub connection
stayed closed without receiving its item. The new build queued the gem exactly
once, on the press at frame 41, and did not requeue it after re-entry.

## Goal Game replay

| Zero-prize control | Same frame with Goal Game art |
| --- | --- |
| ![Goal Game completion without the gem](goal_game_reward_art_before.png) | ![Six-gem popup after a zero-prize Goal Game](goal_game_reward_art_in_game.png) |

This is the first physical Goal Game source (room 557 to cabinet 980), 33
frames after the authenticated completion. Both zero- and one-prize input
routes used an isolated blank-save native startup-room fixture, with no runtime
memory edits. Candidate and control matched all 1,180 sampled gameplay states
per route. Both recorded the expected native-file-0 check at frame 2185 and
returned to Central Circle at frame 2639. Read-only native callback counting
confirmed unchanged prize counts (0 and 1) and landing counts (62 each). The
candidate queued the gem exactly once on the new check in each route.

## First area visit replay

| First visit control | Same frame with first-visit art |
| --- | --- |
| ![Central Circle without the gem](first_area_reward_art_before.png) | ![Six-gem popup on the first Rainbow Route visit](first_area_reward_art_in_game.png) |

Both native mGBA runs start from blank SRAM and the same controller replay,
without a loaded save state or runtime writes. The first Rainbow Route visit
is recorded upon entering Central Circle (room 801) at frame 21307. The effect
waits for the room to become visible and queues at frame 21439, with 32 visible
frames. All 200 changed pixels in the illustrated frame fall inside the gem.
Both runs match the native visit events and progress to Room 1-01; entering
that second room does not display another first-area gem. Transient VBlank
phase differences during the scripted transition settle before the gem draws.

## Area boss replay

| King Golem reward branch | Control | Same frame with boss art |
| --- | --- | --- |
| Shard not owned | ![Unowned-shard branch without the gem](area_boss_reward_art_unowned_before.png) | ![Gem above the boss, native shard effect intact](area_boss_reward_art_unowned_in_game.png) |
| Shard already owned | ![Owned-shard branch without the gem](area_boss_reward_art_owned_before.png) | ![Gem above the boss, native tomato intact](area_boss_reward_art_owned_in_game.png) |

Both mGBA replays use the native pre-boss fixture and controller inputs for
the actual King Golem fight (room 710). The owned-shard variant receives its
shard through the normal isolated AP inbox before the fight. Each candidate
queues one gem on the physical defeat. The control comparisons matched all
3,596 owned-branch and 4,996 unowned-branch sampled gameplay states. The
unowned replay continues through the native shard pickup and returns to
Central Circle without a second gem. The 26-frame image pair changes pixels
only inside the 16×16 gem rectangle at (196, 19), not the native reward.

## ROM contract

The sole call from the chest-open handler to ChestItemPopup at ROM offset
`0xB3FE` passes a visual-only argument. The new wrapper selects the same
native single-frame visual slot every time, including for an empty chest.
The parent chest's original reward still governs the real item, AP suppression,
reward timing, room counter and saving. The wrapper replaces only the matching
128-byte tile upload at the native queue boundary. It does not change the
shared animation, tile or palette tables and does not allocate a custom slot.

`chest_reward_art.png` retains the exact 16×16 RGBA pixel grid of the supplied
100× enlarged art. The encoded preview (`chest_reward_art_gba.png`) uses the
native pickup palette in OBJ bank F. Stock GBA colors approximate the reference
colors without overwriting palette entries used elsewhere. Regenerate the
preview and tile header with `kirby_ap_payload/generate_chest_reward_art.py`
and Pillow, then rebuild the USA ROM patch.

The Big Switch hook is its native world-map branch at ROM offset `0x1199F6`.
Only the 15 AP Big Switch identities qualify. Check for the fresh press edge,
the native press latch, and the persisted AP check without writing those fields.
Keep the original dispatch intact. A short-lived, parentless effect uses the
same four tiles and palette as the two chest-task families, without invoking
the chest reward callback. It stops drawing when that check persists, the
player leaves the room, or the effect expires.

Goal Games reuse the parentless art without touching native prize collection.
The shipping landing handler records the physical check only after the native
completion step, and now reports whether the authenticated save record changed.
Only that fresh-check result shows the gem. Its position stays inside the
current cabinet view even when Kirby has moved above the camera for the native
return sequence. A completed cabinet remains playable without another AP gem.

The native visit writer stays authoritative. The hook reads the same
catalog-derived area identity and native high visit bit used by the client,
and does not write an extra check or grant. Any newly set area visit queues
only a transient visual tied to the active native save and destination. The
effect waits until the local room, native player state, and native palette
state allow it to draw. File changes, room changes, and timeouts clear pending
visuals. Areas already established by any mapped room do not replay.

The eight area-boss finish callsites share one hook immediately after the
native reward branch. It forwards the native finish call and adds only a
seed-authenticated cosmetic seen bit. It never writes boss transport, shard
ownership, or other check state. Existing native saves carry the visual
history; there is no forced save when showing the gem. A power loss or
reset before any native save can replay the visual. Older Hub/lever records
are read as before and have no historical boss-visual bits. Use the matching
updated client and do not downgrade a save with these new visual bits.
