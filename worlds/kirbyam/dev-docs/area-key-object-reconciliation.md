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
  boarding guards still reject new passengers. The native 142 → 195 flight has now been checked with ownership rollback
  after boarding; broader flight/destination coverage remains outstanding.

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

### Additional native and CI acceptance

- Hub room 801: without a Hub Connection, even all Area Keys leave mirrors
  uninitialized and absent. With connections present and keys absent, keyed
  hub mirrors receive boards. Cabbage item 3860042 removes only its matching
  board (destination 592). Savestate reload preserves it; key rollback restores
  the board after the native callback has gone idle.
- A normal player-controlled 801 → 592 → 801 round trip succeeds with the
  connection and Cabbage key. Return position is (94,280).
- With the immutable Area Keys configuration disabled, room 173 keeps native
  interior variant A and room 142 spawns its native star with no key ownership.
- The user accepted the current hub appearance. The standard gold frame still
  overlays the larger themed hub frame; custom fitted artwork is not claimed.
- CI's synthetic ROM initially lacked the 11 newly required object hook sites.
  The fixture now supplies their checked native contracts, and the complete
  synthetic patch build passes locally. The retail patch and runtime binaries
  are unchanged by this CI fixture correction. Regression coverage validates
  the dummy ROM with the same fail-closed hook inventory used in production.
- Native static analysis on head 72eb719 failed before compilation: the LLVM 19
  repository for the runner's Ubuntu `resolute` returns HTTP 404. No analyzer
  findings were produced; this is an external CI setup failure, not a pass.

Actual client reconnect, native in-game save/reset, other star routes/consumption and linked multiplayer remain unverified.

### Authorized flight with key rollback

Player input boarded the native room 142 star with the Moonlight key. A control
run retained the key; a second run cleared its key bit immediately after the
first passenger boarded. Both reached room 195. With rollback, the passenger
mask stayed at 1 (no later CPU passengers were admitted), the object survived
through flight, then disappeared by frame 1200 after native passenger cleanup.
At frame 2400 it remained absent. The control run returned to one idle native
star (passenger mask 0), with no duplicate. This verifies the scoped authorized
flight case; it does not substitute for linked multiplayer or all star routes.
