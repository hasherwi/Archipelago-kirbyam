# Targeted Bomb-chain route audit

Reviewed 2026-11-08 against PR #1051's `49ec2e2` baseline. This follow-up changes
only evidence and regression tests. **No incorrect AP access was established in
the two focused room graphs, so no new traversal state or ability gate is added.**
It does not complete the visual classification or controller acceptance of every
Bomb-controlled route.

## Mechanism, appearance, and traversal are separate

At native revision `7d969fbce14fdc838d2c1ea01389717fb96c3189`,
[`sub_0800E27C`][chain] propagates through four-neighbor tiles whose collision
attributes include `0x40`. The matching collision IDs are F1 (`0x101260`),
F2 (`0x240`), and F3 (`0x41`). F7 (`0x401200`) does not participate. The initial
F1/F2/F3 inventory contains 132 rooms, including non-gameplay/test rooms; this is
an inventory count, not 132 reviewed reinforced-metal puzzles.

[`sub_08001408`][mutation] applies each tile's recorded replacement. Propagation
is not equivalent to clearing every connected coordinate to air. A chain may
change terrain, produce a hazard, or close a passage. Consequently, neither
"F2 is reinforced metal" nor "Bomb activation permanently opens the room" is a
safe global rule.

The [Block article][block], revision 592841, calls reinforced metal a block
removed by a falling Heave-Ho or a Bomb Block. Its illustrative screenshot is
[Olive Ocean Room 6][reinforced-image]. That appearance does not classify every
native F2 or F7 tile. In particular, the [Rainbow Route Room 6 composite][108-map]
shows Bomb-controlled earthen terrain, rather than treating every Bomb barrier
as a bank of visually reinforced metal. We do not relabel the F2 inventory from
this visual observation.

Normal's [air puff][puff] can activate an F1 trigger when its hitbox reaches it.
That capability is not proof of an approach from every entry or of a successful
route after the mutation. It also must not be confused with requiring the Bomb
copy ability.

## Rainbow Route Room 6, native 108

Sources: [room article, revision 574489][108-page], its full composite map, the
native room mapping, and the existing
[combined patched-ROM Wheel acceptance](../docs/traversal-logic.md#combined-patched-rom-wheel-acceptance).
The native inventory records four F1 triggers at `(29,16)`, `(41,17)`, `(44,17)`,
and `(36,18)`, plus 57 F2 and 38 F3 tiles. Counts alone do not assign all of them
to one trigger or one visual category. A targeted four-neighbor component audit
finds `(44,17)` (mutation offset `0x878468`) and `(41,17)` (`0x878432`) share
42 F2 and four F3 tiles. The F2 coordinates are:

- `x41..44,y9..10`; `x40..45,y11..12`; `x41..44,y13..16`;
  `x42..43,y17`; `x41..44,y18`.
- Fourteen replace with `0x0D`: `(41,9)`, `(44,9)`, `(41,10)`, `(44,10)`,
  `(40,11)`, `(41,11)`, `(44,11)`, `(45,11)`, `(40,12)`, `(45,12)`, and
  `x41..44,y18`. The other 28 replace with zero.
- Four F3 tiles at `x42..43,y7..8` and both F1 triggers replace with zero.

All these are kind-1 mutations. The component aligns with the earthen bank
between the two lower triggers and the surface, confirming that this F2 example
is not a bank of the reinforced tiles illustrated in the Block article.

The existing controller witness activates `(44,17)` before the detour and
`(36,18)` for the Wheel race. Both reconstruct as F1 after the documented fresh
room return. Therefore no permanent bomb-open event should be inferred across
that reload. The AP graph already preserves:

- Upper arrival is separate from the inaccessible lower approach.
- The lower-right and lower-middle compartments have their reviewed connection.
- Lower-middle can reach the upper exit without an ordinary-metal ability gate.
- The optional lower chest remains bound to `wheel_108_chest`, not to a generic
  Bomb or metal capability.

The existing source-aware Wheel witness remains untouched. Normal trigger
eligibility does not replace its Wheel source, permission, detour, or race.

## Moonlight Mansion Room 11, native 743

Sources: [room article, revision 574549][743-page], its
[full composite map][743-map], native room mapping, and existing `rooms.json`
compartments. Native F1 coordinates are `(14,7)` and `(6,20)`; the room contains
26 F2 and 92 F3 tiles.

The left upper entry descends to the lower machine and Bomb trigger `(6,20)`.
The article describes that activation as both opening the way forward and
starting floor/ceiling sparks. The top-right arrival is a dead end, not an
alternate approach to the machine. The native component audit confirms the lower trigger and upper trigger
are separate, with all reviewed mutations kind 1:

- Upper: F1 `(14,7)`, mutation offset `0x885D50`, and F2 `(14,6)` both replace
  with zero. No F3 belongs to this component.
- Lower: F1 `(6,20)`, offset `0x88646A`, replaces with zero. Nineteen F2 belong
  to this component: `x6..12,y13` and `x15..22,y16` replace with `0x0D`, while
  the visible four-tile bank `x13..14,y19..20` replaces with zero.
- All 92 F3 belong to the lower component: 85 replace with zero; seven replace
  with `0x5E` at `(6,14)`, `(10,14)`, `(8,17)`, `(19,17)`, `(11,18)`, `(15,20)`,
  and `(19,20)`. This is a concrete reason not to model the chain as deletion
  alone. The remaining six F2 tiles in the room are not assigned to either of
  these two Bomb components.

Native transitions independently identify the two arrivals from 708:
`0x883E9C`, trigger `(22,28)`, spawns at `(6,3)`; `0x883EF2`, trigger `(28,28)`,
spawns at `(12,3)`. In 743, outgoing record `0x885CA8` at `(6,2)` returns to
708 `(23,29)`, and `0x885CB6` at `(10,2)` returns to 708 `(30,29)`. The lever-door
record `0x885D1E` at `(6,7)` leads to native 180 `(5,3)`; its reverse arrivals
spawn at `(8,8)`. These are stored tile coordinates, not live Kirby positions.

The component/transition audit uses the original USA ROM SHA-1
`274b102b6d940f46861a92b4e65f89a51815c12c` and the native revision above. Static
connectivity and map inspection do not establish exact controller trajectories,
damage-free passage, or one-hit-health acceptance.

The AP graph already distinguishes `ROOM_2_11`, `ROOM_2_11_DEAD_END`, and
`ROOM_2_11_AFTER_LEVER`. The right entrance goes only to the dead-end compartment;
its only exit returns to the right entrance. The main compartment owns the lever
check. Progression beyond the lever wall still requires the AP item
`Moonlight Mansion 2-11 - Lever Wall`, not merely the physical lever event or a
Bomb activation. Generic movement and `can_break_block` tokens currently add no
copy-ability-item requirement. Adding an extra bomb state machine would duplicate
that existing access behavior without correcting a demonstrated error.

## Regression coverage and remaining work

[`test_bomb_chain_routes.py`](../test/test_bomb_chain_routes.py) adds seven AP
regressions for the two entry splits, ordinary passage permission independence,
separate Wheel target, and preserved lever-wall item gate. They test serialized
AP topology and requirement evaluation, not native movement.

Five room articles were read in this targeted pass: native 108, 143, 228, 308,
and 743. Full composite pixels were inspected for 108, 228, and 743, plus the
Block article's reinforced example. Existing 143 rope, 228 ordered-bomb/rope,
and 308 single-bomb carry witnesses remain unchanged. Native counts and trigger
coordinates were checked separately; the complete 132-room chain inventory has
not been visually classified or accepted as traversable.

Next useful acceptance, if a new 743 route rule becomes necessary, is an actual
left-entry Normal controller run through the lower machine trigger to the lever,
with read-only pre/post collision observations and a separate right-entry
negative. The component audit above supplies the coordinates to observe. Merely finding
another Bomb or F2 tile is not a reason to add a new rule.

These ordinary trigger passages introduce no Stone or Burning source assumption.
This does **not** establish that either ability can safely be removed from the
starting inventory: all other checks, carried-source routes, randomization modes,
and relevant generation/gameplay acceptance remain separate obligations.

[chain]: https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/code_0800E0E4.c
[mutation]: https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/code_080023A4.c#L586-L662
[puff]: https://github.com/jiangzhengwenjz/katam/blob/1197474f80e5de282fbedcd0025ebfa61f61a764/src/code_0806F780.c#L2093-L2180
[block]: https://wikirby.com/w/index.php?title=Block&oldid=592841
[reinforced-image]: https://cdn.wikirby.com/8/87/KaTAM_Olive_Ocean_Room_6.png
[108-page]: https://wikirby.com/w/index.php?title=Rainbow_Route_-_Room_6&oldid=574489
[108-map]: https://cdn.wikirby.com/a/a0/KaTAM_1-6_Map.png
[743-page]: https://wikirby.com/w/index.php?title=Moonlight_Mansion_-_Room_11&oldid=574549
[743-map]: https://cdn.wikirby.com/2/2d/KaTAM_2-11_Map.png
