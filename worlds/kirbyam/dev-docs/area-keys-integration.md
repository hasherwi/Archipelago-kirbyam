# Area Keys integration with Hub protocol 2

PR #908 integrates main after #932 and #999. Newly generated seeds and ROM patches are required. This is
an integration draft; source/host checks do not establish emulator acceptance.

## Transition behavior

| Mechanism | Guard and intended behavior | Evidence and remaining acceptance |
| --- | --- | --- |
| Standard mirrors | Visual, button and explicit transition paths check the destination key before native state changes. Same-area travel and Rainbow returns retain their native rules. | Native callsite contracts and host tests; denied/allowed gameplay remains required. |
| Cannons | Four native boarding eligibility calls check destination ownership before passenger/launch mutation. Accept IWRAM and EWRAM objects. The old EWRAM-only check silently bypassed native IWRAM cannons. | Production C guard executed on both RAM banks. All four inventoried retail jumps are same-area; a natural cross-area cannon case has not been established. |
| Wind chutes | Check the eventual destination before admitting Kirby into a forced lane, preserving the original native chute/spawn arguments. Retain the automatic exit check. | Verified native entry/exit records, collision lanes and host route tests; denied-entry control recovery and allowed traversal need gameplay acceptance. |
| Warp Stars | The three boarding calls check the destination before native boarding. Validate passenger pointers without unsigned-overflow acceptance. | Production C guard executed on both RAM banks. First Rainbow→Moonlight route is native 142→195; owner-reported bypass still requires fresh no-key reproduction and post-receipt entry. |

The four wind admission tuples are `(743,180,5,3)→824`,
`(824,180,12,49)→743`, `(170,181,5,3)→619`, and
`(619,181,12,49)→170`. The arrow after each tuple is its permission target,
not the room supplied to native execution. These require Olive, Moonlight,
Radish and Carrot keys respectively. The corresponding forward graph entrance
rules compose with the existing lever requirements. Native entry/exit byte
preconditions reject drift during patch generation. Detailed evidence is in
[`area_key_transports.json`](../test/data/area_key_transports.json).

Telemetry method 3 identifies wind-chute admission. Methods 1 and 2 identify
Warp Stars and cannons. Chute admission reports the eventual permission target;
normal transition telemetry retains source/destination/method/decision/reason.

## Combined contracts and ROM layout

- Eight Area Keys remain `3860041..3860048`; fifteen Hub Connections remain
  `3860401..3860415`; Hub Teleport Trap remains `3860300`. Combined catalog
  validation checks distinct IDs. Rainbow Route East is Hub item 1, Moonlight
  is item 2; native numeric semantics are preserved.
- Area ownership/telemetry occupies `0x0203B0C0..0x0203B133`. Hub protocol 2
  ownership/scratch stays at `0x0203B134..0x0203B13B`. Physical switch/save
  behavior remains independent of item ownership.
- The fixed payload starts at file offset `0x15DC00`. Its added 1 KiB must be
  verified retail zero padding. Native code occupies `0x1958` bytes, ending at
  `0x0815F558`, leaving **308 bytes** before configuration at `0x0815F68C`.
  The five Minny/health/color/gate/statue words remain at `0x0815F68C..0x0815F69F`.
- The complete fixed payload is 6,816 bytes. Transition helpers share the
  existing appended ROM extension; extension size is 3,256 bytes. Eight-byte
  Thumb entries preserve arguments/LR when native short calls enter relocated
  helpers. Linker assertions reject overlaps and writable static storage.
- Verified distributable patch SHA-256:
  `b02331897bc467f648673f89eabf918d100ef6b796270485e5ab16c3ca8b404f`.
  Applying it to the private verified USA base reproduces the compiled payload
  and extension. A clean rebuild reproduces both binaries byte-for-byte.
  All 263 native/AP room-area assignments validate.

## Validation scope

Focused tests cover destination directionality, free Rainbow returns,
key/Hub/lever composition, progression and goals, ownership reconciliation,
transport guards, telemetry, strict route preconditions, and eight mandatory
hub-room checks when Room Sanity is disabled. Synthetic patch smoke succeeds
without relaxing native guards. Packaged generation retains the exact patch;
artifact inspection excludes ROMs, saves, databases and native build outputs.

The #999 correction preserves the native Hub enum aliases while updating the
item-order assertion. Inherited lint/type findings and environment setup
failures must be reported separately from Area Key regressions.

A fresh authored runtime seed has zero starting Area Keys and 12 initially
reachable checks, above the fallback threshold of four. This avoids falsely
calling a precollected Moonlight key a Warp Star bypass. Fresh boot/authentication
is preliminary evidence only. Completion requires mechanism-specific denied
and allowed gameplay, safe control recovery, free Rainbow returns, Hub
interactions, save/load and reconnect, plus exact published-head CI. No merge
or release readiness is asserted here.
