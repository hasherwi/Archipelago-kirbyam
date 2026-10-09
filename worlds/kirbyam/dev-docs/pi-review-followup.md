# Pi independent-review fixes

Two reproduced defects are addressed in this source change:

- When the exact chest event counter regresses, consume the retained valid
  sequence window. Keep pending checks until server acknowledgment. A reset
  observed after a new chest opens no longer discards that first event.
- Mark intercepted Vitality chest rewards for the existing delayed popup hook.
  Preserve initial presentation, then substitute the native no-item branch
  before reward dispatch. This prevents the popup from resetting maximum HP
  to native vitality count + 6 and creating a healing tomato. The native room
  completion increment remains intact because Vitality sources are not minor
  chest sources in the suppression table.

Validation on ARM64 Pi: combined v0.4 tree, including #934/#935 overlays and
#938, passes 986 tests. Focused client/Vitality tests: 27 passed. A private
host probe executes the actual payload wrappers and pinned native chest.c
sub_0800B97C body using IO stand-ins: check=1, native reward=99, tomatoes=0,
max HP 3 -> 3, room increments=1. This is not ARM ABI or gameplay validation.
The test collection wrappers added here also exercise all 24 fixed collectible
manifest sources with native/deferred dispatch and invalid-index preservation.

Still open: more than eight unobserved chest events can be overwritten; saved
native flag recovery has not been implemented. A reviewer also identified
possible Vitality replay duplication when fresh EWRAM clears delivery bits but
native saved count remains. These fixes do not resolve that boot/save issue.
Real BizHawk gameplay acceptance and Carrot Music Sheet 6 traversal remain
unrun; Music Sheet 6 stays dormant with 64 active minor checks.
