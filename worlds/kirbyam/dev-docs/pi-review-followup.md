# Pi independent-review fixes

PR #940 addresses all four reproduced lifecycle defects in the combined v0.4
candidate, without enabling Carrot Music Sheet 6 or changing progression logic.

- Replay the retained exact-source window when the event counter regresses.
  Retry observed checks until server acknowledgment.
- Recover saved physical checks from audited chestFields bits, including map,
  Vitality and Sound Player chests. The complete USA object-list scan proves
  84 unique flags 0..83; 79 map to active-capable reward checks. Four item-owned
  lever flags and dormant Music Sheet 6 are excluded. Filter against the
  authenticated slot's active locations. No persistent client queue is needed.
- Reconcile Vitality count and identity bits from a complete index-zero AP
  received history. Before history arrives, retain saved count. Payload replay
  raises only to the number of distinct IDs observed, never increments a saved
  count. The authoritative client also repairs saves inflated by the previous
  bug, preserving dead states and damage during replay; genuinely new upgrades
  retain their normal heal. RAM writes guard the complete health/identity snapshot.
- Suppress native Vitality popup max-HP reset and tomato creation while retaining
  initial presentation and the room-completion increment. Physical collection
  never grants the AP-assigned reward locally.

Validation: combined #934/#935/#936/#938 candidate passes 1,078 tests on ARM64.
The actual payload replay harness covers each unique ID, saved partial/full
history, same-session duplicates, fresh transport replay and dead state. Client
reconciliation covers all 40 health ranges with duplicate history and living/
dead states, full-history gating and atomic death guards. Saved-check tests
cover nine offline opens, transport reset, process exit before ACK, each big
chest family, inactive locations, excluded levers and cross-session reads.

`tools/verify_chest_recovery.py OWNER_ROM` scans all 287 lists and verifies the
complete checked-in mapping against the hash-verified USA ROM. It emits no ROM
bytes. A private native-popup host probe reports check=1, native reward=99,
tomatoes=0, max HP 3 -> 3 and one room increment. Real ARM payload/bsdiff rebuild
succeeded in a private copy; generated patches/ROMs are not committed here.
All 24 fixed collectible source wrappers also have executable dispatch coverage.

Use a fresh native save for each generated ROM/seed; do not import vanilla or
another seed's save. Native save origin cannot be authenticated because it has
no AP seed identifier. Recovery cannot promise data lost before a native save.
Actual BizHawk save/load, item presentation and ARM ABI acceptance remain unrun.
Carrot Music Sheet 6 stays dormant with 64 active minor checks; no route or
minimal-ability proof is claimed. See PROTOCOL.md for the migration policy.
