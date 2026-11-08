# Metal-block traversal: research and acceptance plan

Status: preparation only, 2026-11-08. Baseline: `370dbb431bd0c81949a12c0be36df12b0c8879f6`.

This document preserves the ability research for a later directional, room-by-room
metal-block audit. It does not add traversal edges, change starting abilities,
change item classification, or claim that every metal barrier has been mapped.
No new emulator acceptance run was completed for this preparation.

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

The eight candidate abilities below agree with the existing `metal` attack-class
set in [`traversal.py`](../traversal.py). They are **not eight interchangeable
solutions for every room**. This table records source research, not successful
room-level acceptance tests. Native move/attack definitions are in
[`kirby.c`][kirby] and [`code_0806F780.c`][attacks]; [WiKirby's metal-block page][wiki]
and its linked ability pages provide secondary cross-checks.

| Ability | Relevant move / condition | Geometry and water limits to preserve |
| --- | --- | --- |
| Burning | Horizontal Burning attack. | Needs a usable launch position and horizontal contact. Do not infer vertical access. Swimming input does not initiate Burning. |
| Hammer | Hammer attacks carry metal-breaking capability; Hammer is usable underwater. | Grounded, aerial, and swimming attacks have different hitboxes. Side-access evidence does not establish an isolated floor-plug solution. See the pending test below. |
| Stone | Transformed falling contact; slopes can change its path. | Needs space to transform and a reachable contact path. Do not model arbitrary sideways movement. Swimming cannot initiate Stone, and the researched transform state exits into water movement on water entry. |
| Throw | A grabbed object's held/thrown collision can break metal. Throws can be horizontal or approximately 26.6 degrees upward/downward. | Requires an actually grabbable object, reachable before the barrier, and a viable held-object or projectile trajectory. Do not treat Throw permission alone as ammunition. Swimming input does not initiate this attack. |
| Missile | Eight-direction travel and explosion. | Needs launch/turning space and verified contact or blast reach. Cannot initiate while swimming; a launched Missile can travel underwater. A dry launch into water is a separate sequence, not an underwater-start permission. |
| UFO | Fully charged horizontal beam. | Requires the appropriate charge level, a reachable firing position, and line of contact. Do not count every UFO shot or infer vertical beam fire. Swimming input does not provide this attack. |
| Smash | Its Hammer and Stone moves supply the relevant attacks. | Preserve the selected move's direction and geometry. Smash's Hammer is not available from swimming input; do not inherit Hammer's underwater behavior merely because Smash has a hammer move. |
| Master | Sword moves, including sliding and upward/downward attacks; underwater upward thrust is a candidate supported by the research. | Identify the exact usable move and overlap in each room. Swimming usability does not make every dry move or direction available underwater. |

Fighter and Wheel are not metal-breaking substitutes in *Kirby & The Amazing
Mirror*. Normal Water Gun is not a metal-breaking attack. Sword and Parasol's
underwater attacks likewise do not become metal-breaking merely because they
remain usable while swimming. Ice's frozen-enemy projectile is a separate
object-dependent interaction, not a direct `metal` capability.

### Stone water-entry correction

Do not promote the earlier hypothesis that a pre-transformed Stone simply sinks
through water into a route witness. In the researched native `sub_0805E448`,
`kirby->base.unk58 & 2` calls `KirbyEnterWater` and `KirbyStartWaterMovement`, then
returns. That source evidence contradicts assuming continued transformed descent
for this state. Any exceptional transition or collision timing would need its
own controller-only demonstration. Existing planner comments about a possible
pre-transformed sequence are not proof that such a route works.

### Hammer floor-plug question remains open

The proposed test is a metal plug directly below Kirby with **no side access**.
It must distinguish a genuine top-surface hit from a side hit reached through an
adjacent gap. Test grounded swing, aerial swing/spin, and other applicable Hammer
moves with the entry position and collision geometry recorded. Include a
positive control where Hammer has side access, and repeat underwater separately
if that geometry is relevant.

A fixture was prepared during research, but the acceptance test was not
completed. There is no confirmed yes/no result for the isolated floor plug.
Do not encode “Hammer always breaks floors” or “Hammer can never break floors”
from ability descriptions, attack flags, or the unfinished test.

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
- [ ] Complete the Hammer floor-plug control experiment before choosing a floor rule.
- [ ] Validate move-specific floor, ceiling, and side contact for each candidate.
- [ ] Validate underwater starts separately from dry-to-water transitions;
      explicitly reject the unproven Stone-sinking shortcut.
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
