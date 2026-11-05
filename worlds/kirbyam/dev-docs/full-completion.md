# 100% Game Completion (#204)

`goal: full_completion` (value 5) uses the existing addressless locked goal event.
Dark Mind remains the default; values 0 through 4 retain their current meanings.
The client sends `CLIENT_GOAL` only after both the native snapshot and all 99
physical AP acknowledgements satisfy the contract. No numeric goal check or
extra item-awarding location is introduced.

## Completion contract

- Visit every native completion room: 272 entries, doorsIdx 8 through 279.
- Open all 80 physical reward chests and pull all four levers.
- Physically press all 15 Big Switches.
- Own all eight shards, four Lever Wall items and 15 Hub Connection items, and
  wait until their corresponding native state is present.
- Observe native final-clear state 9999 or 10000 in that complete save.

Vitality ownership is independent. The four physical Vitality chests remain
required for every health range, including 6/6 (zero upgrades), 3/5 (two), 6/10
(four) and 1/10 (nine). Precollected, extra, duplicated or delayed Vitality items
neither open checks nor add completion obligations. HP and the native Vitality
count are never used by the predicate. Paints, music sheets, maps and Sound
Player ownership are likewise not additional requirements; their physical
chests still are. Goal Games, sub-games, ordinary filler and traps are excluded.

`data/full_completion.json` pins the native room and object inventories to the
USA ROM SHA1 and decomp source. Room Sanity has 262 of these rooms plus Central
Circle (doorsIdx 0), which native completion excludes. The ten remaining rooms
are the final Dimension Mirror sequence; generation uses the existing final
sequence model for them, without inventing new graph edges. Room Sanity off
still requires the same exploration. Split-room visit sinks preserve any-entry
visit semantics; specific chest checks retain their compartment access rules.
Music Sheet #6 is already active at flag81, in the upper 5-13 compartment entered
from 5-14; older documents describing it as dormant are stale.

The retail formula is `39*chests//84 + 37*rooms//272 + switches + shards + clear`,
with maxima 39/37/15/8/1. The new predicate checks the exact constituent flags.
It does not trust cached percentage, let reserved bits compensate for missing
ones, or use AI10000 alone. Native lever and switch state can be item-owned;
that is why separate physical acknowledgements and saved physical masks are
required. The final-clear/credits boundary still needs emulator confirmation.

## State and compatibility

`full_completion_version: 1` identifies the goal contract. All new seeds emit
`physical_check_save_version: 1` and require ROM marker `APFULL01` at 0x1000010.
Use the updated client and regenerate the ROM patch. Missing/unknown goal
metadata, old patches, incomplete reads and unauthenticated sessions fail closed.
Older seeds without the save-version field retain their legacy client path.
Do not downgrade a new physical-check save to an older payload.

The full-goal evaluator requires current-socket authenticated item history,
ROM auth, marker, mailbox cookie, a valid native save index and a seed-bound
physical-check record. It reads native fields as one connector batch, then
compares every byte again with guarded reads before reporting. Server, socket,
connector, slot metadata and history changes invalidate an in-flight attempt.
A positive-HP live player task and clear demo/credits flags are required, with
that task evidence included in the final guard. Completion is recognized after
returning to playable game state; a loaded completed save needs no boss refight.
It does not reuse the generic AI latch across a reload or another slot.

Native saves own room/chest/final-clear state. The extended, full-auth-bound
physical-check record preserves offline Hub and lever actions through ordinary
native saves. The client can project server-acknowledged lever checks back into
that RAM save buffer with guards, leaving SRAM/checksums to the native saver.
Server checks are authoritative for the AP seed/player, not per native save
index. Importing a vanilla or another seed's save is unsupported: native chest
and exploration fields do not themselves carry a seed identity. No claim is
made that arbitrary external saves can be authenticated or migrated.

See [native persistence](full-completion-native-persistence.md). Power loss
before a native save completes is not a durable-save guarantee.

## Validation and remaining acceptance

Automated tests exercise each missing native obligation and each missing
physical acknowledgement, generation reachability independent of Room Sanity,
health bounds, precollects and delayed required ownership, malformed input,
marker/auth guards, reconnect, save changes, duplicate reporting and history
replay. Native host tests cover the shipping persistence code, including legacy
migration, all Hub/lever masks and all three simulated save slots. The shipped
bsdiff must match the rebuilt ARM payload against the verified private USA ROM.

These checks do not establish real gameplay acceptance. Before promoting this
goal as verified, record BizHawk captures for:

- Final-clear-only, one missing chest/room/switch/shard, and true full completion.
- Credits completion and loading an already-complete save without a boss refight.
- All three native files; room transitions; same-seed save/load and reconnect.
- Health 6/6, 3/5, 6/10 and 1/10, with chest-open/upgrade-missing and the reverse.
- Offline lever pulls followed by native save, cold load and later AP reconnect;
  item-before-pull and pull-before-item; delayed shard/lever/Hub delivery.
- Demo/title, reset and save-state rewind while a completion read is pending.

The draft remains pending these acceptance captures; host tests alone do not
justify changing native policy status to verified or closing #204.
