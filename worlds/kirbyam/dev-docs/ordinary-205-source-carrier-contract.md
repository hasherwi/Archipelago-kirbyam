# Native205: reviewed Hammer and directed return evidence

These original evidence records were first committed without production rules.
The later [directed check implementation](ordinary-205-209-directed-checks.md)
uses them alongside the separate209/210 entrance and Snow/map proofs. These
traces alone do not certify the former coarse regions or justify removing
starting Burning and Stone.

## Actual source and the disclosed fixture

Native210 Bonkers is object `0x088BF730`, type0x39, at(440,232). Its ability-table
field is `0x351BA6`, native Hammer17, matching the registered `BONKERS` source.
Actual Normal entry through205 door(10,18) reaches210(264,40.996), then the
central ladder and right shaft reach the arena at(393.141,232.996), without damage.
The approach is repeated independently in both enemy-health fixtures.

At pinned native source revision
[`7d969fb`](https://github.com/jiangzhengwenjz/katam/tree/7d969fbce14fdc838d2c1ea01389717fb96c3189),
`InitObject` loads the copy field from `0x08351648 + type * 24 + 6`. The shared
defeat path enters `sub_0809D060`, and the true guard `(unk2 || unk3 != 31)` permits
the matching room slot to be updated. Bonkers has unk2=0, unk3=10, unk4=2.
Scroll lock `0x088BF5C8` at(384,192) uses the same slot2, with flags0x6. The shared
defeated-body and copy path is `sub_0809C48C -> sub_080547C4`.

This uses the world's existing ordinary miniboss-combat assumption. It is not a
combined controller replay of defeating and inhaling the actual Bonkers. The
suffix fixture explicitly replaces Bonkers with a Hammer statue/essence at the
unchanged position and moves only that scroll lock's x coordinate384 to2000,
simulating its post-defeat release. The fixture source is not a production
statue, a renewable source, or evidence of boss respawn. No terrain, attack, or
runtime memory changes occur in either accepted controller chain.

The finite Bonkers source branch can use only policies that actually guarantee Hammer
from the finite Bonkers placement. Item permission alone cannot equip Hammer;
a mixed finite live pool, no-ability result, or source behind the target cannot
be promoted to a guarantee. That finite branch stays closed under other grants; the later directed target
also has a separate renewable statue-backed Stone alternative.

## Directed carrier and exact check

The accepted suffix carries Hammer through actual210 door(15,2), record
`0x888C78`, to205 live(152,296.996). It climbs the left shaft, reaches the upper
platform, and launches above the **floor** plug at(350.121,120.996).

Two low aerial swings, each `A1, release8, B1, wait60`, destroy the two rows of
F5 at x21..22/y8..9. Both artifacts read all four cells as245 before and0 after.
A six-frame high jump was ineffective; no alternative timing, provider, or
underwater floor attack is accepted from this result. The separate six-tile
upper obstacle at x24..26/y3..4 is not the floor gate.

The continuation swims around the lower solid shelf without needing the Bomb,
then takes actual205 door(29,17), record `0x887434`, into209's top arrival.
The exact check is `MINOR_CHEST_PEPPERMINT_PALACE_7_CHEST_OBJECT_01`, native
object `0x088BF3C8` at(56,56), location3960587, chest flag23. Both traces include
an actual Up interaction at(53.617,56.996) and masked flag readback128. Earlier
proximity-only observations were not collection and are superseded by this
explicit readback. Neither the map chest nor the lower minor24 is accepted here.

The source approach and post-defeat suffix remain two separate controller
chains. Their independent cold-boot roots are not falsely joined as an actual
Bonkers acquisition replay. Every post-boot segment is linked to its prior
controller-earned checkpoint and audited at every frame:

- [Default enemy health](ordinary-205-hammer-source-acceptance.json):19 audited
  segments,4,290 frames, minimum6HP and zero HP decreases.
- [500% enemy health](ordinary-205-hammer-all500-acceptance.json):18 audited
  segments,4,184 frames, minimum6HP and zero HP decreases.

Normal is retained throughout the approach. The suffix acquires Hammer17 from
the disclosed fixture and retains it through actual209 collection. At500%, the
final water continuation uses a prompt door entry after the left-facing Hammer
attack. It does not wait for a durable enemy to die or assume a one-hit kill.

## Enemy scaling and low-health scope

The500% fixture applies the production `scale_enemy_health_tables` once before
cold boot, to both approach and suffix ROM fixtures. Its source is revision
`a062278eea84ce3c2a6a7bbc601262cda0f3fab2`, module Git blob
`bbae3fc5368eddecc7183590ce7f4defaf7effa4`, SHA256
`cff04ec15000178c220ea4a3774cebc4412ceb386275faefe85d46e1d72c8098`.
Independent native readbacks compare original and scaled suffix bytes: Blipper
at0x35167C:2 to10, Glunk at0x351694:2 to10, Waddle Doo at0x3517FC:4 to20, and
Flamer at0x351814:4 to20. The tests also match the current scaler to that pinned
Git blob. This is all supported enemy tables, not a single-enemy HP substitution.

The supported health settings include starting1HP. The existing
[health-scope analysis](ordinary-742-health-scope.md) establishes that AP health
configuration changes health, not movement or collision physics. The bounded
additional Hammer source review is:

- Dry and water dispatch tables `gUnk_0834C2AC` and `gUnk_0834C318` select
  `sub_080618C0` at ability index17. `Macro_0803FF64_2` selects by water state.
- `sub_080618C0` selects aerial animation104/105 and `sub_0806268C` by airborne
  and water flags. Grounded/water swings use `sub_080622A0` and `sub_08062548`.
  These functions have no HP or maximum-HP predicate.
- `KirbyStartWaterMovement`, `KirbySwim`, `KirbyEnterWater`, `KirbyLeaveWater`
  and the shared movement helpers use fixed movement/input/collision state,
  with no positive-HP-dependent speed or attack selection in these paths.
- The explicit native `hp == 1` attack variant is Fighter's charged projectile,
  not Hammer or Normal. The other such branch is the low-health sound.

This source argument plus continuous zero-loss traces supports the same bounded
movement at positive Kirby HP. It is **not** a direct AP1HP replay, a full AP
patch/server session, a full Bonkers combat replay, or an exhaustive replay of
every intermediate enemy-health percentage and controller timing.

## Topology limits of these original traces

Native205 maps to `ROOM_7_07`,209 to `ROOM_7_CHEST`, and210 to `ROOM_7_05`.
Their former coarse regions merged distinct native arrivals. In particular:

- 209's top door returns to205(29,18), already inside the post-metal water
  pocket. It must not be treated as an outer arrival that crossed the floor.
- 208 enters209 at(3,39). The two210 doors enter209 at(2,9) and(2,20), unlike
  the reviewed205 top arrival at(11,3). Their paths to the top chest/return
  were unqualified by these original records.
- 209 returns to210 at(30,24) and(30,44). Splitting209 alone can still leak
  between those heights through the coarse210 region.

The [separate Normal return trace](ordinary-205-normal-return-egress.json) starts
at a disclosed209 top-arrival fixture, activates the actual209-to205 return door,
and uses water-gun Bomb trigger(23,12) to open a different shaft. Cells23..25/y12
and25/y10..11 become water0x48;25/y9 becomes upward-passable0x0F. Kirby ascends
and flies left to the outer-middle gap at(347.230,21.004), with both F5 banks
still intact. Default and500% each contain six post-boot segments audited every
frame:1,403 and1,663 frames respectively, Normal6HP throughout with no decreases.
The500% variant safely handles durable Blipper with repeated water-gun timing;
the original default continuation was not assumed sufficient.

This establishes a directed pocket-to-outer-middle egress, not independent access
to209, every205 exit, other209 pockets, or a reverse entrance into the water
pocket. The later implementation adds only the separately accepted continuation to the
actual203 exit, not a generic return edge or free Normal floor bypass. Its
additional directed source/access and arrival records are documented in the
linked implementation contract, with stable check identities, one physical
room-check sink per room, and no sink-mediated crossings. Starting-inventory
removal remains blocked.
