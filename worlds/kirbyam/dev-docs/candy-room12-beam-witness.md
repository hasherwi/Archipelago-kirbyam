# Candy Constellation 9-12: ranged routes to Small Chest #1

This is a bounded same-room route for AP location **3960575**, object
`0x088C5BA4`, native room 402. It does not change the RoomSanity check or
either native exit to 9-13.

- The stock North American ROM and the reproduced keyless 1197 seed have
  identical room-402 collision data (SHA-256
  `43d464d6b6a3c82b90d2087b3b98ddde26692e84214d1defff147868b4df44ae`).
  Scanning all 287 native transition tables finds only the upper 9-10
  entrance, room 418 tile (133,3) to room 402 spawn (4,4).
- The chest is at (392,424) and the linked Bomb fuse at tile (25,25).
  The three linked east seal cells (28,25–27) are initially `0xF2`.
  There is no chain from the separately reachable Bomb fuse and the tested
  Normal puff from the east does not trigger the interior fuse. The
  uninterrupted Normal route can still visit the room and reach its exit.
- In a private controller-only mGBA replay of the keyless seed, Normal
  Kirby took the native lower gallery and inhaled/swallowed the original
  Waddle Doo (`0x088C5BC8`, type 18) from the approach at about (301,457).
  Kirby retained Beam through the central one-way floor. A left-facing
  Beam sweep at (442,376.996) hit the Bomb fuse through the roof. The fuse
  and all three seal cells changed to zero.
- Without leaving the room or resetting the seal, Kirby came around the
  east gallery, passed through the opened east seal and opened the chest.
  The native exact-event counter increased from 0 to 1 and reported
  `0x088C5BA4`; no helper or gameplay writes were used. This was a private
  emulator replay, not an AP server acknowledgment. The recorded route
  survived native damage; it does not prove a damage-free or 1-HP route.
- This Standard witness has zero ability-carry room transitions and
  supplies the Beam branch below. Beam is not an AP permission item.

## UFO alternative

A separate controller-only mGBA replay used an isolated Shuffled fixture
with the actual enemy table assigning UFO to Waddle Doo. With UFO permission
present, the same lower Waddle Doo yielded UFO by an ordinary inhale and swallow;
with permission withheld, the identical tape left Kirby Normal. The permission
is `UFO Ability` (AP item 3860114) when ability gating is enabled. It is not
equipment by itself.

With the permitted grant, the uninterrupted same-room replay fired the
maximum-charge UFO shot **right** from approximately (322.035,408.992) in
the lower west aisle. The shot triggered the exact fuse and erased the three
seal tiles. Kirby continued around the east gallery, lost UFO to a native hit
after the seal cleared, and opened object `0x088C5BA4` as Normal (event 1, 4 HP).
A separate east-side control with UFO equipped through test setup also opened
the chest, preserving UFO and 6 HP, but did not prove a source from that side.
The full local-source route was tested at 6 starting HP, not at 1 HP.
Both routes stop at this check and export no door opening or equipment.

The stock routes activate only when the raw effective Waddle Doo policy
guarantees Beam, UFO, Spark, Missile, Sword, or Smash. Otherwise new seeds
use the linked-fuse Normal route below.

## Spark, Missile, Sword, and Smash alternatives

The same private keyless checkpoint and controlled, guaranteed Waddle Doo
assignments were used to witness these full routes. For each, native swallow
withholds the copy ability when its corresponding AP permission is denied.
No room transitions, helper, or gameplay state writes occurred after setup.

- **Spark:** At (381.34,376.996) use Spark through the central roof. The
  linked fuse and all three seal cells cleared, then the east gallery return
  opened the exact chest with Spark still equipped. This was reproduced with
  both 6 HP and 1 HP without taking damage.
- **Missile:** At (387.93,377) use Down+B to detonate through the roof. After
  the fuse and seals cleared, a 6-HP replay reached the exact chest after
  two native hits. A second replay at fixed 1 HP from initial swallow stayed
  hitless: from about (548.75,345.89) after the east-gallery return, descend
  left as Missile into the opened seal, then open the same chest (native
  event at frame 2405, with Missile retained).
- **Sword:** Carry the local Waddle Doo grant to the roof using rising
  slash jumps. At (376.04,377) use Up+B; the fuse and all three linked seals
  clear. Wait 24 frames after the landing/clear sequence, then return
  through the upper/east galleries and open the chest with Sword retained
  (native event at frame 2086, no damage at both 6 and fixed 1 HP).
- **Smash:** Carry the naturally swallowed local grant to the center roof.
  At about (391.06,375.14), use Up+B; the original fuse and its three seals
  clear. Circle through the east gallery, then jump and hover left from
  the lower east floor to reach the exact chest. The 6-HP controller replay
  took one native hit after the fuse cleared, lost Smash and finished as
  Normal at 5 HP (native chest event 1, template `0x088C5BA4`, frame 1689).
  With Smash permission withheld, the same inhale/swallow leaves Kirby
  Normal. A separate fixed-1-HP replay took no damage. After Up+B cleared
  the fuse and all three seals at frame 524, immediately hover upward, use
  forward Smash (Right+B) past the upper hazard, and drop the copy ability
  with Select. The same chest opened as Normal at frame 1168, still at 1 HP.
  No helper assistance or gameplay state writes were used after setup.
- **Master:** A player confirmed that Master can activate this chest.
  Master is not obtainable from the local enemy under the copy policy, and
  this work does not prove a Standard carrier or model it as required.

When Ability Gating is on, Spark or Missile permission is progression only
if this chest is enabled and the exact local source policy guarantees that
ability (independent rules may also classify these items). Neither
permission item itself equips Kirby.

## Normal linked-fuse seeds (#1161)

The seed records this patch only when minor chests are enabled and the final
enemy policy does not guarantee one of the six stock routes. Strike the
ordinary west Bomb Block at tile (7,18) with a slide. Its stock chain runs,
and the original hidden chest fuse at (25,25) clears the three east seals
through the native chain effect. Follow the regular lower gallery to the east
of the opened seal and jump/hover left into the native chest chamber.

The link is tied to an actual hit, not room entry or an item grant. It
does not change enemy assignments, the chest identity/reward, any room visit
or exit, or the number of locations. A saved same-seed tracker policy
reuses the ROM's decision; old seeds that lack this field retain their
original rules and unlinked fuse.


### Supplemental Fire route (linked-fuse seeds)

The original east Waddle Doo (room 402, template `0x088C5D0C`, spawn
`504,296`) was naturally inhaled and swallowed with a fixed Fire assignment
in isolated mGBA. With its Fire permission, Kirby acquired Fire; with the
same inputs but no permission, Kirby stayed Normal. From this source, the
east crossover and lower turnaround were traversed while carrying Fire.

Separately, a prepared pose at approximately `470,439` proved that facing left
and using Fire breath opens the original fuse at `25,25` and all three chest
seals. The same inputs without Fire left them closed. The prepared Fire run
collected native chest `0x088C5BA4`; at fixed 1 HP only the Fire ignition was
verified. The continuous source-to-ignition replay was not reproduced. Fire
is therefore a supplemental option for fixed-Fire, linked-fuse seeds, never
the sole generation guarantee. The independently verified western Normal
fuse is still present, with no Fire unlock required for the check. Older slots
without the linked-fuse flag and mixed or fallible enemy grants do not add the
Fire witness.
