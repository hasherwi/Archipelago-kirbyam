# Bounded bomb traversal implementation

Status: partial implementation, 2026-11-10. The conditional Rainbow110→554
upper-source rule, conditional Cabbage517 Chocolate chest rule, conditional
Carrot719→734 lower-compartment rule, selective Rainbow138 Green Paint
chest rule and entry-bound Carrot733 Yellow Paint UFO rule are installed. Other source-policy/target subsets remain open.

## Implemented kernel behavior

The traversal kernel has Bomb Block target-specific capabilities on five targets, with
no global wall-piercing class or numerical range assumption:

| Capability | Native target | Admitted witnessed moves |
| --- | --- | --- |
| `bomb_110_room9` | Room110 wall-separated chain opening the Room9 route | Spark, from the closer dry pose above the waterline |
| `bomb_110_room9_underwater_sword` | Same exact Room110 lower F1(13,57), same Room9 route | Attached underwater Sword spin, separate from landing wave |
| `bomb_138_green` | Room138 Green Paint selective lower trigger, upper trigger intact | Spark, finite natural source/carry from Room27 upper-left |
| `bomb_517_chocolate` | Room517 Chocolate Spray Paint barrier | Beam, closer upper-step Spark, ordinary Ice breath, rising Smash Up+B |
| `bomb_517_fire_breath` | Same exact Room517 F1 (14,7) and Chocolate chest | Neutral traveling Fire breath packet from the reviewed dry pose |
| `bomb_517_missile_blast` | Same exact Room517 F1 (14,7) and Chocolate chest | Down-right local Missile detonation with a ±24 tile scanner |
| `bomb_517_parasol_swing` | Same exact Room 517 F1 (14,7) and Chocolate chest | Dry active forward swing with actual bounds (16,-11,48,11), not held umbrella |
| `bomb_719_room13` | Room719 recessed door to Room13's 1-Up compartment | Beam |
| `bomb_719_fighter_first_combo` | Same lower-entry gate, ordinary first combo | Fighter |
| `bomb_719_sword_repeated_slash` | Same lower-entry gate, three-tap animation111 | Sword |
| `bomb_733_yellow_ufo_top_charge` | Room733 Yellow Paint lower trigger, upper intact | UFO top charge after two finite Sparky acquisitions |

Both route endpoints must belong to the named native room and use the reviewed
medium: dry except for the separate underwater Sword effect. These are action
steps inside a room, not the subsequent cross-room door
transition. Each provider set records known successful routes, not an exhaustive
claim that every other ability is impossible. Direct Spark at the sealed719 gate
is separately excluded by the retained native geometry evidence.

The kernel still begins with Normal unless a preceding physical path has acquired
an ability. Inventory never supplies equipment. Source-policy grants, finite
source consumption, permissions and independently declared access remain intact.
Beam is not gateable in the current ROM. Fire, Missile, Spark, Ice, Smash, Sword and UFO are gateable.
Spark becomes progression when gating is enabled and the installed Rainbow
source-policy condition applies. Ice would require classification review before
installing an Ice-dependent new target; Fire, Smash, Sword and UFO are already progression. Runtime
permission eligibility remains unchanged. Missile is conditionally promoted only
for the enabled guaranteed-Doo Chocolate chest rule when gating is on.

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
- Cabbage517: installed only for a guaranteed singleton WADDLE_DOO→Beam,
  WADDLE_DOO→Smash, WADDLE_DOO→Fire or WADDLE_DOO→Missile, with independent
  Cabbage Hub2 access.
  Separate [Smash](cabbage-smash-source-witness.md) and
  [Fire](cabbage-fire-source-witness.md) and
  [Missile](cabbage-missile-source-witness.md) witnesses prove complete production
  acquisition/carry and the physical chest check. Beam, Smash, Fire and Missile
  are separate OR graphs inside one target row. Fire and Missile guard the
  raw source policy before permission filtering, rejecting mixed random pools.
  Spark/Ice target-hit witnesses still do not establish their source carry routes.
- Carrot719: installed only for guaranteed WADDLE_DOO→Beam/Fighter/Sword, using
  the lower native Doo(568,456) and independent Room5 access. Separate Beam,
  [Fighter](carrot-room7-fighter-witness.md) and
  [Sword](carrot-room7-sword-witness.md) OR graphs preserve their own carry and
  target attacks. Sword guards the raw singleton source before permission
  filtering; its three-tap111 combo is not a general range or landing wave.
  The other Doo(616,232) is recorded in the complete source inventory, not
  substituted into this route.

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
accessibility. This alternative adds no second target or AND rule. The catalog now has37 targets, including Yellow Paint.

## Carrot Yellow Paint

The fifth bounded Bomb Block target is `bomb_733_yellow`, only
`MINOR_CHEST_SPRAY_PAINT_02` /3960501 at native733. It requires independent720
access and guaranteed SPARKY→UFO. The unchanged719→720 labels remain permissive
existing assumptions. A separate ordinary170-door→719→720 segment is now
verified in `carrot-yellow-ufo-upstream-witness.md`, without claiming all170
arrivals or a continuous170-to-Yellow replay. The reviewed Normal
720→734 upper→720 left→730 ingress avoids a circular734 prerequisite.

Actual equipment guards require upper finite Sparky acquisition, UFO maze carry,
intentional drop/Normal ladder and distinct lower Sparky reacquisition before the
733 top-charge shot and physical chest collection. Neither source alone suffices.
Only lowerF1(21,6) is opened; upper(18,2) remains intact. This is a target-specific
dry attack, not global UFO range.16 new sealed cases and12 separately qualified
earlier cases cover only actualHP1/6 × enemy100/500%; controls and source/entry
limits are retained in `carrot-yellow-ufo-source-witness.md` and its runtime JSON.

## Cabbage Fire validation

`test_cabbage_fire.py` covers finite source consumption, permission without
equipment, raw mixed-pool rejection, exact target scope and actual-world option
wiring. Four full seed 18 generations preserve the normal 25-ability policy and
Doo→Fire assignment, fill every check and assert beatability/full accessibility
at 1 HP, with gating/Area Keys on and off and sampled 100%/500% enemy health.
Eight native runs and matched controls are separately qualified in the Fire
witness and compact acceptance metadata. These host tests do not replay a ROM.

## Cabbage Missile validation

`test_cabbage_missile.py` adds the distinct dry detonation, retained equipment,
finite-source and raw mixed-pool guards, conditional progression and disabled
minor-chest behavior. Actual-world fixtures preserve unrelated exits, RoomSanity
and Area-Key rules. Four full seed 5 generations retain the normal 25-ability
Doo→Missile policy and assert fill, beatability and full accessibility at 1 HP.
Native four-endpoint positives, bounded no-attack controls and the separate
neutral-direction negative are qualified in the Missile witness. Failed later
closed-wall continuations are not counted as accepted no-damage controls.

## Conditional starting permissions

The scoped [starting-inventory lifecycle correction](traversal-start-inventory-lifecycle.md)
reconciles early precollected Ice, Twister-only Crash and Missile permissions
once their actual target locations exist. It preserves each existing source,
gating and enabled-location condition, requested multiplicity and unrelated
item classifications. This is host generation behavior, not new native route
acceptance.
