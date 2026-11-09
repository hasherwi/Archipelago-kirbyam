# Bounded bomb traversal implementation

Status: partial implementation, 2026-11-09. The conditional Rainbow110→554
upper-source rule, conditional Cabbage517 Chocolate chest rule, and conditional
Carrot719→734 lower-compartment rule are installed. Other source-policy/target
subsets remain open.

## Implemented kernel behavior

The traversal kernel now has three target-specific capabilities, with no global
wall-piercing class or numerical range assumption:

| Capability | Native target | Admitted witnessed moves |
| --- | --- | --- |
| `bomb_110_room9` | Room110 wall-separated chain opening the Room9 route | Spark, from the closer dry pose above the waterline |
| `bomb_517_chocolate` | Room517 Chocolate Spray Paint barrier | Beam, closer upper-step Spark, ordinary Ice breath, rising Smash Up+B |
| `bomb_719_room13` | Room719 recessed door to Room13's 1-Up compartment | Beam |

Both route endpoints must belong to the named native room and the attack must be
dry. These are action steps inside a room, not the subsequent cross-room door
transition. Each provider set records known successful routes, not an exhaustive
claim that every other ability is impossible. Direct Spark at the sealed719 gate
is separately excluded by the retained native geometry evidence.

The kernel still begins with Normal unless a preceding physical path has acquired
an ability. Inventory never supplies equipment. Source-policy grants, finite
source consumption, permissions and independently declared access remain intact.
Beam is not gateable in the current ROM. Spark, Ice and Smash are gateable.
Spark becomes progression when gating is enabled and the installed Rainbow
source-policy condition applies. Ice would require classification review before
installing an Ice-dependent new target; Smash is already progression. Runtime
permission eligibility remains unchanged.

## Installed binding and remaining evidence

The original attack replays substitute an essence and redirect startup positions.
The new [Rainbow source witness](rainbow-route-8-source-witness.md) additionally
proves natural acquisition/carry from the decoded upper arrival. The new
[Cabbage source witness](cabbage-room6-source-witness.md) proves actual Hub2
entry, native Beam acquisition and complete chest collection. The new
[Carrot source witness](carrot-room7-source-witness.md) proves actual Room5 entry,
native Beam acquisition/carry and the lower Room13 doorway. Missing evidence
is not replaced by room-wide enemy assumptions:

- Rainbow110: installed only for guaranteed SPARKY→Spark, with independent
  Room6 lower-mid access, finite acquisition and intact carry. Unsupported source
  policies retain prior behavior and remain unresolved.
- Cabbage517: installed only for guaranteed WADDLE_DOO→Beam, with independent
  Cabbage Hub2 access. The complete carry is restricted to Beam; Spark/Ice/Smash
  target-hit witnesses do not establish their source carry routes.
- Carrot719: installed only for guaranteed WADDLE_DOO→Beam, using the lower
  native Doo(568,456) and independent Room5 access. The other Doo(616,232) is
  recorded in the complete source inventory, not substituted into this route.

Do not set a capability-only permission on these AP targets. Rainbow binds its
outgoing110→554 edge only, and Cabbage binds `MINOR_CHEST_SPRAY_PAINT_12`
only. Carrot binds the normalized entrance to
`ROOM_5_13__LOGIC__ENTRY_FROM_5_07` only. Preserve unrelated exits, RoomSanity,
and Room13's Secret Notes compartment. Enable progression classification for
any gateable formerly-useful item used by an installed target, respecting source
policy and disabled optional location categories.

The 35 small switches remain an evidence inventory: ordinary timing alternatives
and unresolved attack/door sequences cannot become blanket ability gates.
Rainbow138's selective lower trigger is not equivalent to an arbitrary bomb hit.
Olive825's existing guaranteed-Frosty rule is unchanged; no unpublished #1051
source expansion or artifact is imported.

## Validation

`test_bounded_bomb_traversal.py` checks every native ability against each provider
set, foreign-room and swimming rejection, source-after-gate circularity, inventory
without equipment, and all three source modes with gating/statue-option variants.
Synthetic test placements are kernel fixtures, not asserted natural sources.

`test_conditional_bomb_gates.py` checks the actual generated entrances, independent
entry prerequisites, source-policy applicability, disabled location categories,
area-key/statue/gating variants, and Spark collection/classification. The native
replays establish acquisition/carry outcomes; these AP tests establish rule wiring,
not additional physical routes.

A separate local restrictive-fill check used `test.general.setup_multiworld`,
`Fill.distribute_items_restrictive`, `post_fill`, `can_beat_game`, and
`fulfills_accessibility`, with full accessibility and minimum/maximum health both1.
All five cases filled every location and passed beatability/full accessibility:
native mode seed1052 with gating on and off (all three targets applicable), shuffled
seed59 (Spark target applicable), shuffled seed70 (both Beam targets applicable),
and completely-random seed1052 (none of these finite-source targets applicable).
These are sampled fill checks, not exhaustive seed coverage. Fully-random success
does not validate the unresolved target routes under that source policy.
