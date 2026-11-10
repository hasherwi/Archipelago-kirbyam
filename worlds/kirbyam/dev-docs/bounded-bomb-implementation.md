# Bounded bomb traversal implementation

Status: partial implementation, 2026-11-10. The conditional Rainbow110→554
upper-source rule, conditional Cabbage517 Chocolate chest rule, conditional
Carrot719→734 lower-compartment rule and selective Rainbow138 Green Paint
chest rule are installed. Other source-policy/target subsets remain open.

## Implemented kernel behavior

The traversal kernel now has five Bomb Block target-specific capabilities on four targets, with
no global wall-piercing class or numerical range assumption:

| Capability | Native target | Admitted witnessed moves |
| --- | --- | --- |
| `bomb_110_room9` | Room110 wall-separated chain opening the Room9 route | Spark, from the closer dry pose above the waterline |
| `bomb_110_room9_underwater_sword` | Same exact Room110 lower F1(13,57), same Room9 route | Attached underwater Sword spin, separate from landing wave |
| `bomb_138_green` | Room138 Green Paint selective lower trigger, upper trigger intact | Spark, finite natural source/carry from Room27 upper-left |
| `bomb_517_chocolate` | Room517 Chocolate Spray Paint barrier | Beam, closer upper-step Spark, ordinary Ice breath, rising Smash Up+B |
| `bomb_719_room13` | Room719 recessed door to Room13's 1-Up compartment | Beam |

Both route endpoints must belong to the named native room and use the reviewed
medium: dry except for the separate underwater Sword effect. These are action
steps inside a room, not the subsequent cross-room door
transition. Each provider set records known successful routes, not an exhaustive
claim that every other ability is impossible. Direct Spark at the sealed719 gate
is separately excluded by the retained native geometry evidence.

The kernel still begins with Normal unless a preceding physical path has acquired
an ability. Inventory never supplies equipment. Source-policy grants, finite
source consumption, permissions and independently declared access remain intact.
Beam is not gateable in the current ROM. Spark, Ice, Smash and Sword are gateable.
Spark becomes progression when gating is enabled and the installed Rainbow
source-policy condition applies. Ice would require classification review before
installing an Ice-dependent new target; Smash and Sword are already progression. Runtime
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

- Rainbow110: installed for guaranteed SPARKY→Spark **or** SWORD_KNIGHT→Sword,
  with independent Room6 lower-mid access, finite acquisition and intact carry.
  The unchanged dry Spark graph and separate swimming Sword graph are OR
  alternatives under one target/exit rule. The [Sword witness](rainbow-route-8-sword-witness.md)
  originally reproduces decoded108 upper arrival rather than replaying the door.
  A [separate actual-entry supplement](rainbow-route-8-sword-entry-witness.md)
  closes that door gap at100% enemy health and actual1HP only. The original
  native assignment/gating-off packet covers actual1HP at enemy50/100/500% and actual6HP
  at100/500%, with three matched no-attack controls. Other health values and
  same-ability randomized/gating-on source policies were not natively replayed.
  Unsupported source policies retain prior behavior and remain unresolved.
- Rainbow138: installed only for guaranteed SPARKY→Spark, with exact Room27
  upper-left access, original finite Sparky and selective lower-trigger carry.
  See [the Green Paint witness](rainbow-green-source-witness.md). Native replays
  cover natural mode, gating off, actual HP1/6 and enemy100%/500%; supported
  50–99% and 101–499% settings remain unreplayed. Only the optional paint
  check is gated, with existing Room8 Spark classification unchanged.
- Cabbage517: installed only for a guaranteed singleton WADDLE_DOO→Beam or
  WADDLE_DOO→Smash, with independent Cabbage Hub2 access. The new Smash
  alternative proves complete production acquisition/carry and the physical chest check,
  using [the Smash witness](cabbage-smash-source-witness.md). Beam and Smash
  are separate OR graphs inside the same target row. Spark/Ice target-hit
  witnesses still do not establish their source carry routes.
- Carrot719: installed only for guaranteed WADDLE_DOO→Beam, using the lower
  native Doo(568,456) and independent Room5 access. The other Doo(616,232) is
  recorded in the complete source inventory, not substituted into this route.

Do not set a capability-only permission on these AP targets. Rainbow binds its
outgoing110→554 edge and the separate Green Paint check only; Cabbage binds
`MINOR_CHEST_SPRAY_PAINT_12` only. Carrot binds the normalized entrance to
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

`test_cabbage_smash_gate.py` adds the separate Smash carry contract, finite-source
and inventory-only negatives, target-scoped applicability validation, and actual
world policy, gating, optional minor-chest, statue, RoomSanity and Area-Key checks.
Restricted policy/option fixtures use minimal accessibility to isolate rule wiring,
not to claim those fixtures are valid full-accessibility seeds. Beam remains
non-gateable and Carrot's source condition remains Beam-only.
`test_cabbage_smash_evidence.py` checks the retained production policy, exact
source/chest/client-check identities, four HP/enemy-health configurations, two
matched negatives, eight initial configuration writes, and no gameplay writes or
state restores. It guards evidence metadata rather than running an emulator.

A separate local restrictive-fill check used `test.general.setup_multiworld`,
`Fill.distribute_items_restrictive`, `post_fill`, `can_beat_game`, and
`fulfills_accessibility`, with full accessibility and minimum/maximum health both1.
All five cases filled every location and passed beatability/full accessibility:
native mode seed1052 with gating on and off (all three targets applicable), shuffled
seed59 (Spark target applicable), shuffled seed70 (both Beam targets applicable),
and completely-random seed1052 (none of these finite-source targets applicable).
These are sampled fill checks, not exhaustive seed coverage. Fully-random success
does not validate the unresolved target routes under that source policy.

The Smash extension adds four real `Generate.main` / `Main.main` seed173 runs,
with full accessibility, HP1, gating on/off and Area Keys on/off. All retain the
normal 25-ability policy and WADDLE_DOO→Smash assignment, fill every location,
and pass explicit beatability and full-accessibility assertions. These are sampled
generation/fill checks, not new native gameplay evidence or all-seed coverage.


`test_rainbow_sword_gate.py` adds the exact-target two-source OR schema,
mutual-exclusion/malformed negatives, independent Spark/Sword permission and
finite-source tests, dry/swimming rejection and actual-world option wiring.
`test_rainbow_sword_evidence.py` checks the five retained production records and
three matched1HP controls without replaying ROMs. Native seed110 and Sword-only
shuffled seeds30/17 sample restrictive fills at1HP assert beatability and full
accessibility. The target count remains36; no second target or AND rule is added.
