# Source-backed traversal (draft)

## Contract

An ability item permits acquisition; it does not equip Kirby. `traversal.py`
models a directed entrance/compartment-to-exit/check graph, one equipped ability,
physical source identities, source consumption, and transient opened pegs.
Capability providers are separate from room records. The policy resolver uses
`build_enemy_copy_runtime_patch_writes`, the same assignments and eligibility
bitmap as the ROM. Excluded categories keep their native grants.

A source behind its own obstacle cannot solve it. Copying another ability replaces
current equipment. Mini disappears on a transition, including a same-room cannon.
A transition and a room-instance reset are distinct: only an explicit reset
renews consumed sources, and a reset also loses opened pegs. Multiple rows for
one physical source share its stable identity. No permanent AP peg event is used.

Live random grants expose outcome sets, not the deterministic fallback hash.
A single-use random source proves a capability only when every possible output
solves it and no Normal result is possible. Sequential capabilities cannot select
different favorable outputs from the same consumed source. Explicit renewable
placements can instead use possible-acquisition semantics: repeated attempts are
assumed eventually to produce a positive-support eligible output. This is a
fairness assumption, not a first-inhale or bounded-attempt guarantee. A full-period
PRNG alone does not prove it because grants consume differing numbers of draws.

The reviewed hub190 regular statue is renewable in place: native
`ability_objects.c:sub_080AA588` grants an ability without consuming the statue.
Kirby can drop an unwanted result and touch it again. Ordinary enemies and ability
stars do not inherit this renewable classification. Enemy weight100 removes
random enemy outputs; statue output pools ignore that enemy weight. All gateable
outputs still require their unlock items.

## Mini

The exhaustive native collision0x59 census contains only rooms134,312,321,736.
All four routes are installed in production in every randomization mode:

- Olive6/134: lower Ocean Spray route, with local Minny and the drop/inhale/recover
  sequence before the final throat. Upper Goal1 remains independent.
- Mustard18/312: Warp branch. Ordinary Room19 remains independent.
- Mustard5/321: lower Room6 route. Upper Room9 and its bomb-block chest remain
  independent.
- Carrot10/736: down-cannon compartment to Chest1. Upper Room11 is independent.

Canonical Minny placements precede their throats; unrelated room-wide enemies
are not credited. In particular, a source across a cannon transition cannot carry
Mini back through that transition. The four compact records include source object
addresses and the native evidence contract.

Minny always grants Mini. Only the Minny carve-out option was removed; general
randomization, statue, miniboss, boss-spawn and non-ability-enemy options remain.
Mini can still appear from other randomized enemies. Statue pools preserve the
former default exclusion of Mini. Mini remains gated and is no longer precollected.
Stone and Wheel starting permissions remain unchanged in this checkpoint.

Raw Mini ability stars recover Mini under the same unlock gate in every mode.
Other stars preserve existing behavior, including the existing native0x80 versus
legacy0x20 detector mismatch. Do not assume ordinary stars suppress no-ability
weight. See `mini-star-recovery.md` for actual-C tests and patch verification.
Old Minny policy keys are ignored for newly generated patch plans. This does not
repair an old ROM whose static Minny grant was already changed: regenerate and
repatch from the supported original ROM.

## Peg coverage

`peg_traversal_audit.json` records all14 pegs in13 native rooms. An audit record is
not automatically an executable route. Production source-aware gates currently:

- 401 peg28,30: right shaft to406 Sound Player; local Rockys or explicit Stone
  carry190→801→490→407→401. The407 bomb is approached from above with Stone.
- 411 peg4,3: revealed405 doorway; Stone190→801→490→411. Other exits stay free.
- 221 peg41,12: Pink chest tunnel; local Giant Rockys or Stone
  190→801→290→291→215→212→216→217→221. The carry avoids rock bodies,
  ordinary blocks, and the star platform rather than assuming them absent.

Carrier witnesses require an independently reachable source hub, actual Hub
Connection items, and destination Area Key when that option is enabled. Static
assignment validation accepts reviewed local or carrier witnesses rather than
rewriting individual randomized outputs. Static policies, including shuffled weight100/statue configurations, get at most
1024 assignment attempts without forcing individual outputs. If that budget
finds no reviewed all-items source witness,
that finite-witness peg rule is explicitly deferred with a warning. Unknown
alternatives are not declared impossible; this remains incomplete draft coverage.
The current repository has no entrance
shuffle option; RoomSanity adds checks, not shuffled transitions.

204→227 Happy Notes has a one-way target compartment: regular227 entry cannot
reach it through the nondroppable0x0F platform. The upper compartment can exit to
main. Its exact peg-side entrance is separated, but its source rule is still
pending. Do not describe that topology correction as completed source enforcement.

Remaining audit-only routes:149 chest (alternate underwaterF7 approach unresolved),
204 alternate exit,510 chest (different lower metal route),513 upper-to-lower
peg then bomb (reverse bomb bypass),527 first peg/Sapphire and second peg/lower
exit,605 revealed610 door,816 map (remote bomb alternative unresolved).
509 and218 gate food rather than AP exits;741 gates a loose1-Up, not its room exit.
527 Sapphire requires bomb38,8 then peg18,13; an earlier bomb24,14-only bypass was
invalidated by directed0x0F analysis. Its timed gate is a separate constraint.

## Destructive chains and remaining acceptance

A closing chain is not automatically a Wheel gate. Candy424 Music Scores was
collected with Normal in an isolated native replay. Moonlight708's secret22,28
exit was reached with Normal from the743 return entrance30,29. These successes
must not be gated on Wheel. Other708 entrances need separate analysis.

Rainbow108 upper chest has an actual Wheel success witness from110 arrival34,19.
Wheel exclusivity is not established. A potential Wheel140 carrier through an
independent108 bomb is being checked. No production Wheel race restriction or
Wheel-start removal is claimed by this checkpoint.

Before treating this draft as gameplay accepted:

- Finish source/compartment rules for the remaining mapped peg targets.
- Complete Rainbow108 source carry and relevant substitute/race proofs, then
  wire the exact chest route and reassess Wheel starting permission.
- Replay the full Olive Mini sequence with the rebuilt randomized/gated ROM.
- Verify room-reset retry routes before marking any enemy renewable; AI occupancy
  can preserve a room and prevent respawn.
- Run the complete world suite and archive generation matrix on the final commit.

Research was pinned to native source commit
`7d969fbce14fdc838d2c1ea01389717fb96c3189`. Published records contain compact
facts and addresses, not full ROMs, save states, or native collision dumps.
