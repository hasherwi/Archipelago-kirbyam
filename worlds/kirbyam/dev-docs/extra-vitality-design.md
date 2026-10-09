# Design: up to nine Vitality upgrades (#946)

Status: implementation in progress for v0.4.0; blocked on #931 reaching main.
The policy and native hook components below are implemented and tested in
isolation. Generation, the shipping payload and client still use the four-counter
contract. Expanded ranges are **not available yet**.

## Implementation checkpoint

- `vitality.py`: explicit nine-ID mapping, all 55 range plans, One-Hit precedence,
  pool arithmetic, ROM/slot compatibility checks, authenticated-history mask
  helpers, partial-replay counts and health reconciliation. Reconciliation takes
  the previous native count so genuine new ownership heals once on either arrival
  path, while replay and dead HP remain unchanged.
- `vitality_runtime_logic.h`: matching executable C policy, bounded menu count,
  partial receipt recovery, capacity and signed dead-HP handling.
- `vitality_hooks.c` / `vitality_patch.py`: staged no-argument native hook targets
  and all-or-nothing validation of the USA initializer getter call at `0x3EB0E`,
  its `+6` instruction at `0x3EB12`, and menu getter call at `0x14380A`.
  Neither source is enabled by the shipping Makefile/patcher.
- Local validation: 532 new/existing health tests passed, including 2,640 real
  pool-builder runs with an isolated nine-ID catalog (55 ranges, both shard modes,
  all three One-Hit choices and eight map/life/gating combinations). The new tests enumerate
  55 ranges × 512 ownership masks, compare Python/C policy, exercise fresh versus
  replayed ownership and death, and reject unknown patch callsites. Independent
  review also exercised 563,200 authority transitions and all 65,536 u16 menu
  counts, with a negative control reproducing the original menu overwrite.
- Isolated ARM link on main fits the existing 5,792-byte window with health config
  at `0x0815F690`; callsites validated against the private USA ROM in memory.
  This is not the final combined #931 payload, a distributable patch rebuild,
  native save/load validation, or emulator acceptance.

Still required after the prerequisites reach main: register extra catalog items;
wire the plan into real pool generation; integrate both clients' guarded authority
and protocol checks; install hooks/config/title/header checksum changes; rebuild
and verify the distributable patch and package; run actual server precollect,
delivery/reconnect and both-emulator acceptance. Do not enable ranges 5..9 using
these standalone components alone or interpret this checkpoint as merge-ready.

## Baseline and dependency

This document branches directly from main `104a1fd83e51a7890be7b881b9a13f7464689c61`.
[PR #931](https://github.com/hasherwi/Archipelago-kirbyam/pull/931), reviewed at
`384e52b31136de209726e2fda76009eba210a868`, is still unmerged when this design is
written. Implementation depends on its full-history authority, dead-HP protection,
native Vitality-popup suppression, reset-counter coordination, save-integrity fixes,
and shared BizHawk/mGBA client path. Land those prerequisites in main first, then
update the implementation branch from main. Do not stack this PR on #931 or copy
its unrelated collection, lever, or emulator changes into the design PR.

Issue: [#946](https://github.com/hasherwi/Archipelago-kirbyam/issues/946).
Related: custom health #778; historical delivery regressions #571, #943, #944.
No area keys, hub progression, room-sanity repair, or new physical checks are proposed.

## Recommended representation

Use **nine unique +1 HP items**, not repeated copies of a progressive item.
Keep all four existing IDs, names, and bit meanings. Add five useful, Unique,
Vitality-tagged items without area/chest names, because they have no native chest
identity. These IDs are proposed reservations, not yet implemented:

| Index | Item key | AP ID | Ownership bit |
| --- | --- | --- | --- |
| 1..4 | `VITALITY_COUNTER_1` .. `_4` | 3860018..3860021 (unchanged) | 0..3 |
| 5..9 | `VITALITY_COUNTER_5` .. `_9` | 3860224..3860228 | 4..8 |

New labels: `Vitality Counter #5` through `Vitality Counter #9`. The proposed range
follows #931's collection items ending at 3860223, is unused in its catalog, and
does not overlap the known ability or deferred hub/area-key ranges. Recheck the
live catalog before implementation; never renumber existing items.

Define an explicit ordered Python ID tuple and matching generated/tested C mapping.
Do not subtract the first ID across the gap or rely on arbitrary tag sorting.
Expand the existing ownership mask at `AP_BASE + 0x48` from `0xF` to `0x1FF`.
Keep bit 31 as #931's prefixed-history marker; bits 9..30 remain reserved. Do not
move the mailbox or change the meaning of the physical applied-item counter.
Nine bits fit the existing u32; no extra persistent receipt journal is required
for these idempotent items. Repeated packets for one ID cannot buy extra capacity.

## Option and pool algorithm

With One-Hit Mode off, accept integer `1 <= minimum <= maximum <= 10` (55 pairs).
Set `N = maximum - minimum`, now 0..9. Emit the first N IDs in the ordered tuple,
exactly once each. All ordinary generation remains under existing AP placement
rules: the vanilla/random shard choice affects shards only, not Vitality placement.
Keep the four physical vitality-chest locations independent of item count.

Examples:

| Minimum/maximum | Upgrades | Capacity progression |
| --- | --- | --- |
| 1/10 | 9 | 1, 2, ... 10 |
| 6/10 (default) | 4, original IDs only | 6, 7, 8, 9, 10 |
| 3/5 | 2 | 3, 4, 5 |
| 4/4 | 0 | 4 |

Insert the selected upgrades into the normal non-filler pool, then calculate
remaining filler slots and the existing trap percentage/rounding. Five extra
upgrades replace five disposable slots compared with a four-upgrade pool with
otherwise identical options. Never enlarge the pool beyond unfilled locations.
Retain no-extra-lives, health-food and Health Down Trap exclusions, start-with-all-maps,
ability-gating, and shard-mode behavior. Reject a pool that genuinely cannot fit.

Preserve One-Hit precedence: exclude counters resolves to 1/1 and zero upgrades;
include counters resolves to 1/5 and the original four. Do not silently reinterpret
include-counters as nine. Resolve presets before serializing the effective range.

Starting inventory follows normal AP semantics, not a new subtraction rule. Every
recognized starting identity participates in authority; duplicate copies of one
identity contribute once. Test the actual generated precollect and remaining-pool
behavior. Clamp earned count to N even if plando/start inventory supplies otherwise
inactive identities. Document that such extras never exceed the configured cap.

## Authority and delivery

Let `owned_mask` be the OR of the nine recognized IDs in complete authenticated
history, including precollects; `earned = min(popcount(owned_mask), N)` and
`capacity = minimum + earned`. Keep ownership independent of physical chest flags.
Only an actual index-zero history supplies full authority. Stock-server silence
for empty history remains a wait, not permission to erase a loaded save.

The client reconciles the low nine mask bits, saved native count, max HP and living
HP together using guarded writes, preserving bit 31. Preserve damage on replay and
never revive HP <= 0. Genuine new ownership may retain the current one-time heal
policy. Reject a raced snapshot and reread, rather than writing stale health.

The native item decoder maps all nine IDs explicitly. A first receipt sets its
bit; duplicates acknowledge normally without another health effect. During partial
history replay, only raise the retained count toward the capped popcount; never
add popcount to the saved count or shrink it before full authority is known.
Keep #931's pending-ACK-before-rewind and history-index versus physical-count
separation unchanged. This does not solve arbitrary process-loss ambiguity for
transient consumables; Vitality uses identity authority instead.

## Native save and ROM changes: required, not optional

Store the capped earned count (0..9) in the existing native u16
`gTreasures.vitalityField`. Its width is sufficient and the native serializer already
includes it. Do not expand the SRAM layout, invent a checksum offset, or invoke a
save routine from an unverified frame hook. Normal native save flow persists the
count; a grant not yet flushed requires same-seed AP history replay after reset.
Identity bits remain volatile and are reconstructed from authenticated history.
A saved numeric count alone is not proof of which IDs were received.

**Do not ship by raising the native count limit alone.** The pinned decompilation
has two important consumers:

- `kirby.c:6167` initializes HP/max HP with `NumVitalitiesCollected() + 6`.
  Count 9 would yield 15, violating the requested cap. Replace verified health
  initialization/reconstruction sites with an AP capacity helper reading the
  effective minimum/maximum and clamped saved count. Reuse that helper in native
  Vitality sync. Preserve tutorial behavior and normal respawn healing; item
  application/reconciliation must still preserve dead HP.
- `collection_room.c:806-814` loops to the raw count, searches a table containing
  only entries `0x800..0x803`, then writes `arr[i]` even if no entry was found.
  Count 5+ can overrun that table-backed array. Patch this consumer to a bounded
  getter returning `min(saved_count, 4)` and retain its four native icons. Extra
  upgrades are represented by actual HP and AP item names, not invented menu slots.
  Do not globally clamp the count getter and accidentally discard health ownership.

The two chest-popup `+6` consumers in `chest.c:333/338` remain suppressed for AP
Vitality chests by #931. Audit all getter calls, direct reads and native count
increments against the retail USA build, including assembler consumers and HP UI
bounds. Patch every reachable health reconstruction that can escape the configured
cap. The source scan identifies these consumers; exact retail hook offsets,
displaced instructions and register contracts still require implementation-time
verification. Those hooks and menu bounds are release blockers, not optional polish.

Propose one per-seed ROM word at file offset `0x0015F690`, immediately before the
three current config words. Encode `0xA9020000 | (maximum << 8) | minimum` after
One-Hit resolution. This supplies format 2 and effective bounds even before client
synchronization. Move the config section start back four bytes while preserving
color/gate/statue offsets `0x15F694/698/69C`. Add linker and patcher assertions for
16 config bytes and no overlap; rebuild to prove the code still fits the existing
0x16A0 window. Current measured ELF sections total 4,684 bytes including the old
12-byte config, so this is plausible, not proof the added hooks will fit.
Do not silently move auth metadata or expand into adjacent ROM data if it does not.

## Compatibility and both clients

Publish `health_protocol_version: 2` in slot data and require it to agree with the
validated ROM config before any health/history writes. New clients support legacy
ROMs with the original four-ID path and legacy bounds; never apply nine-bit writes
to a legacy payload. Unsupported/mismatched pairs stop with a regenerate/update
message. World/package version and patch metadata must reflect the new contract.

A slot-data version alone cannot stop an old client that ignores it: #931's client
can overwrite the new mask/count with its four-ID view. Recommend a new 12-byte
patched-ROM title, `KIRBYAM APV2`, for format-2 ROMs. Existing clients strictly
validate the retail title and therefore reject this format before auth/delivery.
Update the shared validator to accept both recognized titles with their corresponding
protocol checks, and recompute the GBA header complement checksum. Keep base-ROM
hash validation unchanged: only the generated patched image receives the new title.
Test emulator detection, patch association and native-save filename behavior.
Do not reuse the 16-byte auth token as a capability marker.

Both BizHawk and the world-local mGBA launcher use the shared Kirby client, mapping
and guarded-write authority. No transport-specific health policy or shared emulator
framework refactor is needed. Exercise both adapters; retain current mGBA notice
limitations. If either backend cannot enforce the compatibility gate, do not ship
expanded ranges on that backend.

New seeds use their own native saves. Existing seeds remain playable with the new
client's legacy path; this is not a promise to import another seed or convert old
savestates. Preserve #931's restart requirement for ambiguous legacy cursor formats.
A same-seed format upgrade, if offered later, must validate history and native save
compatibility explicitly; do not guess ownership or silently migrate a legacy ROM
in place. Offline saved-count reconstruction uses the ROM range and cannot prove
unsaved or unreceived ownership without the server.

## Implementation order and acceptance

1. After #931 lands in main, add the canonical identity mapping and all 55 range
   validations; preserve IDs, default counts, One-Hit overrides and exact pool size.
2. Implement and verify ROM config, title/version gate, native capacity consumers,
   bounded collection-menu getter, and nine-ID application as one compatible unit.
   Do not enable generation of spans 5..9 until this unit and client gates exist.
3. Extend history reconciliation and native replay together, rebuild the distributable
   patch, and update protocol/help/slot snapshots. Do not publish a stale base patch.
4. Execute host and emulator acceptance before calling this implemented.

Required tests:

- All 55 custom pairs and three One-Hit choices, invalid/reversed inputs, exact IDs
  and first-N selection; counts 0..9, defaults, filler/trap rounding and pool options.
- All 512 identity subsets across 55 ranges; duplicates, every ID order boundary,
  marker/reserved bits, capped extra precollects, stock-server starting histories,
  empty-history wait, guards rejected during damage/death, repeated stable polls.
- Actual native functions and patched instruction contracts: all nine IDs, count
  bounds, HP <= 0, life/food/DeathLink interactions, partial replay, cold transport
  resets, pending ACK polls and noncontiguous acknowledged history indices.
- Native collection-menu harness with canaries for saved counts 0..9 and corrupt
  inputs; no out-of-bounds access. Startup/respawn HP and UI must remain within 1..10.
- New/legacy ROM × new/old-client compatibility rejection, mismatched slot data,
  unchanged original four IDs, migration/reconnect and both emulator adapters.
- ARM size/ABI checks, real-USA in-memory patch verification, fresh APWorld packaging,
  and manual nine-upgrade delivery, collection-menu entry, native save/load across
  all three files, reset before/after save, reconnect and death/respawn on both clients.

Feasibility review: the nine-bit mask, five unused proposed IDs and existing u16
save field avoid a new save format or progressive-receipt journal. The unsafe menu
loop and native six-HP reconstruction prevent a Python-only implementation. Exact
retail hooks, header compatibility and final code size remain explicit gates.
This design does not claim those new paths have already been implemented or tested.

## Pinned evidence

- [Reviewed health validator](https://github.com/hasherwi/Archipelago-kirbyam/blob/384e52b31136de209726e2fda76009eba210a868/worlds/kirbyam/health.py).
- [Pool and option integration](https://github.com/hasherwi/Archipelago-kirbyam/blob/384e52b31136de209726e2fda76009eba210a868/worlds/kirbyam/__init__.py).
- [Client authority, four-ID filter, and strict ROM header validation](https://github.com/hasherwi/Archipelago-kirbyam/blob/384e52b31136de209726e2fda76009eba210a868/worlds/kirbyam/client.py).
- [Native payload](https://github.com/hasherwi/Archipelago-kirbyam/blob/384e52b31136de209726e2fda76009eba210a868/worlds/kirbyam/kirby_ap_payload/ap_payload.c) and [linker layout](https://github.com/hasherwi/Archipelago-kirbyam/blob/384e52b31136de209726e2fda76009eba210a868/worlds/kirbyam/kirby_ap_payload/linker.ld).
- Pinned native source: [treasures.c](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/treasures.c#L107-L113), [kirby.c](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/kirby.c#L6167), [collection_room.c](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/collection_room.c#L806-L814), [save.c](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/save.c#L23).
