# Area Key object reconciliation (#1010)

This is an implementation draft with scoped native emulator evidence, not a release claim.
The existing transition guards and authoritative Area Key mailbox are retained.
New ROM patches must be generated to use these hooks.

## Native paths verified

Research used the USA ROM (SHA-1
`274b102b6d940f46861a92b4e65f89a51815c12c`) and KatAM's
`mirror_door.c`, `special_doors.c`, `special_hub_mirror.c`, `warp_star.c`,
`object.c`, `task.c`, and `code_080023A4.c`. Addresses were checked against
retail disassembly, not copied from the old issue proposal.

- `MirrorDoor` caches an open bit at `+0xC0`; its native refresh only checks
  closed-to-open. Its task callback now reconciles the decoration in both
  directions, without changing native collision or session state.
- `AreaDoor` normally creates either the visited arrow or an area decoration.
  Its three decoration calls now select the existing `0x294/6` boarded frame while
  locked, including templates without the native area-decoration flag. Native
  decoration handling resumes on unlock.
- `DoorToHub` and `SpecialHubMirror` use different effect slots. Their task
  wrappers wait for native initialization, then reconcile a board in those
  slots. The SpecialHubMirror native callback can become permanently idle;
  the task wrapper continues checking even in that state.
- Warp Stars are object type `0x84`, spawn-table 1. Three native viewport
  scanners now AND the existing spawn-slot result with the shared destination
  predicate before constructor dispatch. Register adapters preserve the native
  r6/r7 (full scan) and r5/r7 (strip scan) template/LevelInfo contracts.
- An idle, loaded, locked star is marked retiring and passed to native
  `TaskDestroy`, which invokes `ObjectDestroy` and releases its native spawn
  slot, object registration and graphics. It is not merely made invisible.
- The native spawn scheduler additionally checks eligible keyed stars in its
  current viewport. It consults native occupancy/consumption bits and invokes
  native `CreateObject`; no independent pointer registry or save fields exist.
  Enemies and unrelated stars are not included in this extra scan.
- An already authorized flight retains its passenger-owning star until native
  cleanup. Freeing that object mid-flight would strand its passengers. Existing
  boarding guards still reject new passengers. Mid-flight ownership rollback
  remains an explicit gameplay acceptance case, not a proven behavior.

All paths use `ap_transition_allowed` / `ap_is_keyed_inter_area_edge`; the
immutable disabled setting preserves native execution. Native Hub/switch and
collision prerequisites are not overwritten. Dimension Mirror shard gating
is unchanged.

## Verification and remaining acceptance

`test_area_key_object_patch.py` rejects drift in every added patch site and
verifies the complete write set. Existing transition tests still run.
`tools/verify_area_key_objects.py` executes compiled ARM with retail room-area
metadata, synthetic RAM and intercepted native callees. It covers repeated
lock/unlock/relock, disabled keys, spawn adapter ABI, native destruction calls,
Hub initialization, and duplicate/occupied-slot prevention. It is deliberately
not described as native gameplay proof.

Before marking this PR ready, validate all of the following in mGBA or BizHawk
on the exact rebuilt seed:

- Visible boarded/open artwork and alignment for all four mirror object
  families and every applicable destination, including already-visited mirrors.
- Key receipt in the loaded room, entry/re-entry, save/load, reset and reconnect.
- Star suppression, removal and restoration without duplicate registrations;
  native consumption and already-authorized flights; linked-player viewports.
- Independent Hub Connection, shard, lever and native collision requirements;
  same-area/ungated routes and Area Keys disabled.

## Native emulator evidence (rendering correction)

mGBA 0.10.5 exposed an incorrect asset selection: `0x294/0xA` is an
animated mirror interior, not wooden boards. The native `MirrorDoor` disabled
frame is `0x294/6` (`gUnk_08357BEC[1]`). All AP board paths now select that
frame. AreaDoor and DoorToHub anchor the complete frame at the door foot;
AreaDoor restores the interior/indicator anchor before its native updater
reuses the effect after unlocking.

A fresh start-room fixture for native room 173 proves an unobscured boarded
mirror at (472,560), then the same open mirror after the payload acknowledges
Cabbage Cavern item 3860042. Moonlight Mansion item 3860041 alone leaves it
boarded. Clearing only the Cabbage key bit restores boards; redelivery restores
the open mirror; emulator savestate reload preserves the open state. Walking
through the unlocked mirror enters native destination room 508. The active
native collision prerequisite is retained throughout. The same-area / unkeyed
543 destination of room 544 retains native artwork.

The companion Kirbys retain their original start rooms; only player 0's start
room/coordinates are changed for the mirror fixture. Native code, room geometry
and object templates are untouched. Screenshots are emulator framebuffer
captures, scaled 3x nearest-neighbor. Mailbox injection exercises ROM delivery,
not a live server reconnect; rollback is an explicit controlled RAM mutation.

The rebuilt star fixture again proves zero / one / zero / one live native
Warp Star objects across lock, delivery, rollback and redelivery; 240 further
frames retain one object, and a private emulator savestate reload preserves it.
No shared emulator session or pre-existing save was modified.

See `area-key-native-evidence.json` for patch hashes and RAM observations.
Other mirror families/destinations, native in-game save/reset/reconnect,
consumption, flights, multiplayer and full prerequisite composition remain
outstanding. Scoped screenshots and ARM fixtures do not close those gates.

## Integration and deferred attribution

This branch rebuilds `base_patch.bsdiff4` from its own source. PRs #1015 and
#1016 also modify the payload/base patch: integrate source first and rebuild
one combined patch. Never resolve a binary patch conflict by choosing a side.
No palette catalog or completion protocol change is included here.

After this implementation is merged, add once to its delivered changelog entry:
“Thanks to SpawnSean for sharing early mirror-door research.” It is intentionally
not added to the changelog or described as shipped in this draft.
