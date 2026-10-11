# Nine-counter health integration (#947)

The implementation is integrated with merged PR931 (main tree
`afc8819260ece9989ff4c79f40ca7b88a69da2ad`). It supports all 55 ordered
minimum/maximum pairs within 1..10. Defaults remain 6/10. One-Hit overrides
remain 1/1 and 1/5. The four existing items and physical chest checks retain
their identities; IDs 3860224 through 3860228 add five unique upgrades.

## Contract and implementation

`health.py` validates generation; `vitality.py` defines explicit identity bits
and protocol policy. The catalog and real pool builder select exactly the first
maximum-minus-minimum identities. Precollects use the stock server's complete
`items_handling=0b111` history, not physical chest flags.

The shipping payload includes `vitality_runtime_logic.h`. Initial capacity uses
ROM config at 0x0815F690 (magic A902, resolved bounds); the native getter call at
0x3EB0E is redirected and its six-HP addition replaced by a NOP. The collection
menu call at 0x14380A clamps the raw u16 count to four before u8 truncation,
avoiding the fifth icon's adjacent selection-field overwrite. HUD cleanup from
PR931 remains active. No native save layout or direct SRAM writer is added.

New ROMs carry title KIRBYAM APV2 and a recalculated GBA header checksum. Slot
protocol 2, exact bounds and authentication are checked before watcher writes.
Validated legacy sessions also recheck title/authentication; their ownership
mask remains four bits. All reserved high bits survive reconciliation.

Native partial replay retains the bounded saved count. Complete authenticated
history supplies exact ownership. A genuinely increased count heals living
Kirby once; repeated polls/receipts preserve damage, and signed nonpositive HP
is never revived. Physical transport counters and history indices remain
separate, preserving PR931's reset/reconnect fix.

## Validation and limits

Tests cover all 55 ranges, exact pool multiplicities and exclusions, all 512
ownership masks, stock server precollects for all nine identities, changed ROM
identity/configuration, guarded writes, duplicate/reordered replay, death and
native menu bounds. Separate native instruction execution verifies initializer
ABI/register preservation and every u16 menu count. The distributable bsdiff
must match the independently rebuilt payload, not merely its source.

The finite pool matrix exhausts 55 health ranges, two shard modes, map/life/gate
modifiers and all integer trap percentages. The archive matrix remains a set
of mixed scenarios, not a global option Cartesian proof. Known room-sanity
issue #945 remains a strict expected failure; no topology changes are included.

No new nine-counter gameplay, native save/load roundtrip or BizHawk acceptance
is claimed by these offline tests. Native receipt ACK is not immediate save
flush; use a guarded native save point or authenticated replay. Arbitrary
process-loss ambiguity for transient consumables remains outside this change.
