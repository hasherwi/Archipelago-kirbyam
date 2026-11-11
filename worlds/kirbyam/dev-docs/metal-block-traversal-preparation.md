# Metal-block traversal: research and acceptance plan

Historical preparation, 2026-11-08. See the subsequent
[ordinary-metal implementation checkpoint](ordinary-metal-traversal-implementation.md)
for the bounded native557 rule and remaining coverage limits. Preparation baseline: `370dbb431bd0c81949a12c0be36df12b0c8879f6`.

This document preserves ordinary-metal ability research for a later directional,
room-by-room audit. At this preparation baseline ordinary-metal traversal edges
remain deferred. The separate
reinforced/Heave-Ho follow-up adds only the reviewed native 102 mechanism witness;
starting abilities and item classification are unchanged.
The later isolated Hammer floor test is recorded below; room-by-room traversal
acceptance remains separate from the presence inventory.

The subsequent [room inventory](metal-block-room-inventory.md) records the complete
native collision scan and WiKirby cross-check. The room-presence audit is separate
from the pending directional traversal acceptance work described here.

## What a metal-breaking capability means

The native collision routine checks the attack's actual tile-overlap rectangle.
For collision class `0x200000`, it additionally requires attack flag
`attack->unk68 & 0x1000`. This is not a universal rule that an ability only breaks
blocks on a particular side of Kirby. Move hitboxes, animation frames, launch
position, trajectory, and the room's geometry determine whether the attack can
actually touch the block. See [native object collision][collision], around the
`switch (attributes & 0xF00000)` in the attack/tile loop.

Keep ordinary metal blocks distinct from ordinary breakable blocks, heavy stone
blocks, and reinforced metal barriers. The latter need their environmental
mechanism rather than an ordinary metal-breaking ability check. Identify the
collision/object class before assigning any requirement; visual appearance or
an ability's behavior in another Kirby game is not sufficient.

## Ability and condition inventory

The eight candidate abilities below agree with `METAL_BREAKING_ABILITIES` in
[`traversal.py`](../traversal.py). The subsequent ordinary-metal implementation
separates Throw into a physical-object action; it is not a direct unarmed hit. They are **not eight interchangeable
solutions for every room**. This table records source research, not successful
room-level acceptance tests. Native move/attack definitions are in
[`kirby.c`][kirby] and [`code_0806F780.c`][attacks]; [WiKirby's metal-block page][wiki]
and its linked ability pages provide secondary cross-checks.

| Ability | Relevant move / condition | Geometry and water limits to preserve |
| --- | --- | --- |
| Burning | Horizontal Burning attack. | Needs a usable launch position and horizontal contact. Do not infer vertical access. Swimming input does not initiate Burning. |
| Hammer | Hammer attacks carry metal-breaking capability; Hammer is usable underwater. | Grounded, aerial, and swimming attacks have different hitboxes. The isolated floor test supports the tested aerial sequence, not arbitrary clearance. See acceptance below. |
| Stone | Transformed falling contact; slopes can change its path. | Needs space to transform and a reachable contact path. Do not model arbitrary sideways movement. Swimming cannot initiate Stone, but a completed transformation can enter water and sink; activation timing must be preserved. |
| Throw | A grabbed object's held/thrown collision can break metal. Throws can be horizontal or approximately 26.6 degrees upward/downward. | Requires a grabbable object at a reachable capture position and a viable trajectory from there. Kirby cannot walk or initiate a jump while holding; do not carry ammunition to an arbitrary firing position. Do not treat Throw permission alone as ammunition. Swimming input does not initiate this attack. |
| Missile | Eight-direction travel and explosion. | Needs launch/turning space and verified contact or blast reach. Cannot initiate while swimming; a launched Missile can travel underwater. A dry launch into water is a separate sequence, not an underwater-start permission. |
| UFO | Fully charged horizontal beam. | Requires the appropriate charge level, a reachable firing position, and line of contact. Do not count every UFO shot or infer vertical beam fire. Swimming input does not provide this attack. |
| Smash | Its Hammer and Stone moves supply the relevant attacks. | Preserve the selected move's direction and geometry. Smash's Hammer is not available from swimming input; do not inherit Hammer's underwater behavior merely because Smash has a hammer move. |
| Master | Sword moves, including sliding and upward/downward attacks; underwater upward thrust is a candidate supported by the research. | Identify the exact usable move and overlap in each room. Swimming usability does not make every dry move or direction available underwater. |

Fighter and Wheel are not metal-breaking substitutes in *Kirby & The Amazing
Mirror*. Normal Water Gun is not a metal-breaking attack. Sword and Parasol's
underwater attacks likewise do not become metal-breaking merely because they
remain usable while swimming. Ice's frozen-enemy projectile is a separate
object-dependent interaction, not a direct `metal` capability.

### Throw: capture position is part of the witness

Native `sub_08063A88` uses directions for facing and aim, not walking; B or the
holding counter releases the projectile. It has no new jump handler. Gravity,
deceleration, and an already-started jump still apply, so this is not a claim
that Kirby's coordinates can never change while holding. It rules out assuming
that Kirby can grab ammunition below and then walk/jump it up to a firing ledge.

**Moonlight Mansion Room 4 (native 707)** illustrates the issue. Its two F5 tiles
at columns 69–70, row 4 protect the upper-right Room 13 door, matching
[WiKirby's description](https://wikirby.com/wiki/Moonlight_Mansion_-_Room_4).
The left approach chamber has no local enemy/object ammunition or Star Blocks;
its access shaft is at columns 65–66, rows 5–6. The nearest enemy spawn is a
Heavy Knight at (952, 288), far below the blocks at x=1104–1135, y=64–79.
Throw cannot be credited by grabbing that lower enemy and carrying it up the
shaft. This source/geometry finding supports the reported local-route limitation,
but is not a controller-tested proof against every enemy-luring, preexisting
jump, externally supplied projectile, or multiplayer sequence. Ordinary-metal
implementation is deferred; no new Throw gate is enabled here.

WiKirby's [Throw page](https://wikirby.com/wiki/Throw) supports directional aiming
and metal-breaking projectiles, but does not establish a reachable capture point.
Only the isolated Hammer floor sequence below has controller acceptance in this
preparation; **not every metal-breaking move or attack direction is validated**.

### Stone: startup is different from completed transformation

The initial version of this note incorrectly generalized from transformation
startup `sub_0805E448`, which aborts into ordinary water movement on water entry.
The completed Stone states behave differently: `sub_0805EA50` transitions to
`sub_0805EF18` in water, and landed Stone `sub_0805ED40` transitions to
`sub_0805F210`. Thus Stone can enter water already transformed and sink; it cannot
start the transformation using ordinary swimming input. WiKirby's
[Olive Ocean gallery](https://wikirby.com/wiki/Olive_Ocean) also documents sinking
Stone. A room witness must still establish a dry activation location, completed
transformation before water entry, trajectory, and contact with the barrier.

### Hammer floor-plug acceptance: positive for the tested aerial sequence

The controller-only native test in **room 205 (Peppermint Palace Room 7)** now
confirms that aerial Hammer can break a floor directly below Kirby without side
entry. The existing plug occupies columns 21–22, rows 8–9, with solid adjacent
columns. A grounded B control left all four metal tiles intact at the tested
position. Jump, wait eight frames, then swing removed both top-row tiles; a
second jump-and-swing removed both bottom-row tiles and Kirby descended through.
X remained 352.75 pixels throughout, and HP remained six.

The clean fixture changes only startup room/positions and a local Hammer essence
placement. Native terrain, collision, and attack code are unchanged; there were
no runtime memory writes. See the reproducible
[acceptance record](metal-hammer-floor-acceptance.json) for input timing, fixture
hash/patch details, and observations. This establishes a usable move for this
geometry, not an ability-source witness under AP randomization, universal floor
clearance, underwater behavior, or every Hammer move. Do not encode either
“Hammer cannot break below” or “Hammer always breaks floors.”

## Current implementation boundaries

- [`traversal.py`](../traversal.py) tracks equipped ability, source eligibility,
  room-instance state, and consumable physical objects. Item possession is
  permission to acquire an ability, not proof that Kirby is already carrying it.
- `attack_provider` dispatches swimming input to Parasol, Hammer, Sword, or
  Master. Other equipment normally uses Normal Water Gun; Mini has no direct
  swimming attack. Within the current metal class, only Hammer and Master are
  swimming-start providers. This is a dispatch result, not a room witness.
- [`test_block_traversal.py`](../test/test_block_traversal.py) already checks that
  dry metal providers do not automatically work from swimming, and that Ice
  does not become a direct metal attack. It also protects physical projectile
  identity and source availability.
- The existing Normal exits in Olive Ocean Room 12 and Room 21 must not acquire
  speculative metal requirements. Their regression tests and
  [`block-hit-acceptance.json`](block-hit-acceptance.json) remain the baseline.
- This preparation deliberately leaves the broad capability set unchanged.
  In particular, it does not claim that its current abstraction fully models
  Throw ammunition, UFO charge, Missile launch transitions, or Hammer floor reach.

## Evidence required before activating a room rule

For each directed route, record all of the following:

1. Native room ID, named room, entry door/compartment, target exit or check,
   barrier coordinates, and actual collision/object class.
2. Whether Normal Kirby can bypass it, including alternate entries, bomb chains,
   environmental triggers, currents, and return routes. Distinguish required
   traversal from optional consumables or convenience.
3. Exact move, approach side, attack direction, hitbox overlap, clearance, timing,
   and water state at attack initiation and at impact.
4. A physically reachable ability source before the barrier under the active
   enemy/statue randomization policy. A source behind the barrier cannot justify
   opening it; owning the unlock is not enough.
5. Any grabbable/freezable ammunition, its identity, availability, and consumption.
   The same enemy cannot be swallowed for an ability and also thrown/frozen as
   ammunition. Prove renewal/reset explicitly if needed.
6. Post-action ability, consumed objects, destroyed blocks, return access, and
   whether state persists across room transitions.
7. A reproducible controller-only acceptance record: ROM/patch identity, fixture
   changes, entry setup, input sequence, observations, positive/negative controls,
   and retained evidence references. Distinguish isolated fixtures from combined
   patched-ROM/multiworld acceptance; never publish full ROMs or raw ROM assets.

## Next implementation and test checklist

- [ ] Inventory ordinary metal barriers by room and directed entry, without
      equating every visible barrier with required progression.
- [x] Complete the isolated Hammer floor-plug control experiment; preserve its clearance/setup limits.
- [ ] Validate move-specific floor, ceiling, and side contact for each candidate.
- [ ] Validate underwater starts separately from dry-to-water transitions;
      verify completed Stone transformation before water entry and the descent geometry.
- [ ] Model Throw's physical ammunition and UFO charge/trajectory when an audited
      route needs them, rather than widening the generic capability predicate.
- [ ] Add positive and negative tests for each accepted room witness: wrong entry,
      wrong direction, inaccessible source, no ammunition, consumed ammunition,
      insufficient clearance, and wrong water state.
- [ ] Check source randomization, alternate routes, return access, and destructive
      puzzle state before enabling the new directed edges.
- [ ] Run focused traversal tests, the Kirby suite, and applicable repository
      checks against the implementation commit. Record controller acceptance
      separately; Python reachability tests do not prove native hitbox behavior.

## Sources and verification level

- [Native collision code][collision]: directly re-read for this preparation;
  confirms the collision-class attack-flag filter and tile-overlap loop.
- [Native Kirby state/move code][kirby]: Stone water-entry state directly re-read;
  other move findings summarized from the preceding source research.
- [Native attack/effect code][attacks]: attack/projectile implementation reference.
- [WiKirby: Metal block][wiki]: secondary game-specific ability and block-type
  reference. Consult the linked ability pages for move descriptions; descriptions
  do not substitute for room-level geometry evidence.
- Repository code/tests above: inspected at the stated baseline. No production
  logic, item pool, runtime patch, or ROM artifact is changed by this document.

[collision]: https://github.com/jiangzhengwenjz/katam/blob/master/src/object_collision.c
[kirby]: https://github.com/jiangzhengwenjz/katam/blob/master/src/kirby.c
[attacks]: https://github.com/jiangzhengwenjz/katam/blob/master/src/code_0806F780.c
[wiki]: https://wikirby.com/wiki/Metal_block
