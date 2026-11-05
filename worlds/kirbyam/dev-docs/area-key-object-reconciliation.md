# Area Key object reconciliation (#1010)

This is an implementation draft, not gameplay acceptance or a release claim.
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
  Its three decoration calls now select the existing `0x294/0xA` board while
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

No emulator gameplay acceptance has been recorded for this draft. ROM-level
and ARM fixture checks cannot replace that gate.

## Integration and deferred attribution

This branch rebuilds `base_patch.bsdiff4` from its own source. PRs #1015 and
#1016 also modify the payload/base patch: integrate source first and rebuild
one combined patch. Never resolve a binary patch conflict by choosing a side.
No palette catalog or completion protocol change is included here.

After this implementation is merged, add once to its delivered changelog entry:
“Thanks to SpawnSean for sharing early mirror-door research.” It is intentionally
not added to the changelog or described as shipped in this draft.
