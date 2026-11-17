# Mustard Room15: Ice, respawned Foley, and timed crossing

The proposed Ice alternative is physically possible. It is not merely permission
ownership or an assumed repeatable source. The bounded witness starts at the
independently accessible Rainbow Hub 4/native 590 approach, enters 534 and then 533,
acquires Ice from the original guaranteed Foley source, resets the camera to
respawn that Foley template, freezes the new enemy, kicks it through the wall,
and crosses the timed gate into native 325. This bounded route is included in normal logic, with the same source and
physical traversal requirements at both logic levels. No generic Ice far-switch capability or other
room/target is qualified by this evidence.

## Source, camera reset, and projectile

Normal production generation seed 43, full 25-ability shuffled pool, no-ability
weight 0, produces policy seed 4777282310011543242 and guaranteed Foley→Ice/2.
The native source table offset is 0x35197E and source bitmap index 34. The original
Foley template 0x088C2714 is at (224,64) in 533. Inputs follow the existing independent
590→534→533 ingress and clear 534's actual barriers using Normal payloads/air puffs.
At frame 4377 Kirby naturally acquires Ice; at 4404 he carries it at
(245.51953125,72.99609375). No equipment is injected.

Fifty Left frames, fifty neutral frames, and ninety Down frames settle Kirby at
(183.94921875,152.99609375) and move the camera to
(63.94921875,120.99609375). A one-frame Right input faces the enemy; the following
130-frame B hold is Ice breath. The consumed original Foley is absent before
this reset; a new live instance of its original template appears at 4599, with
copy field 2. This is an observed respawn after consumption, not an inference
that finite randomized sources can always be retried.

At 100% enemy health, breath freezes the enemy at4661 at (224,134.57421875).
At 500%, the same sequence deals three 4-damage contacts:10→6,6→2,then freezing
at 4705 at (228.5,143.59765625). Thus the input must keep breathing long enough;
the initial 100-frame experimental breath was insufficient at 500%.

The fixed tail is Right 40, Left 25 grounded, Up+Left+A 100, Left 30, Up 100,
Right 24, B 10, neutral 80, Up 20, neutral 40. Grounded retreat before the jump
avoids catching the underside of the nearby obstruction. Frozen-object position
and timing differ by health tier, but the same tail succeeds at both endpoints.

## Observed switch contact and complete crossing

The small switch template 0x088C26F0 is at(312,145.99609375); the timed gate is
0x088C26CC at(152,128). In the 100% replay, switch contact at 4810 points exactly
to the frozen object 0x030043AC. Gate opening starts 4812 and closing starts 4856;
Kirby is fully left of the gate at 4865. At 500%, contact 4776 points exactly to
frozen object 0x03004428; opening starts 4778, closing 4822, and Kirby is fully
left at 4855, before the gate finishes closing. Both enter actual native 325 at
5146 and settle at5194. The graph must represent this completed traversal,
not a persistent switch-open event.

Source agrees with the observed mechanism: frozen-enemy creation, follow/idle,
and kick behavior are in
[`code_0806F780.c`](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/code_0806F780.c#L5764-L5915).
A kick launches at 4 px/tick and removes idle expiry; terrain pass-through does
not imply arbitrary object pass-through. This exact target contact and completed
crossing, rather than the general source property alone, qualify the route.

## Acceptance and limits

The [sanitized manifest](mustard-room15-ice-acceptance.json) contains eight cold
production-fixture replays: player HP 1/6 × enemy health 100%/500%, each with a
positive and matched no-freeze control. Every gameplay frame 1085–5194 retains
its initial HP. Removing only B from the 130-frame freeze segment leaves all
four controls in 533 without a frozen projectile, switch contact, or gate opening.
Additional raw-ROM exploration at 50%,100%,250%,500% completed 325 using the same
inputs without damage, covering one-, two-, and three-hit freeze behavior. These
are sampled health settings, not exhaustive native testing of every percentage.

The fixtures use the normal generation/patch pipeline and differ from their
production ROM only in startup room/position records: player 0 starts at Hub 4,
others at 101. Every replay cold-boots with a blank battery; the real client makes
eight guarded configuration writes at 1085 and no later writes. There are no
runtime ROM writes, gameplay RAM writes, state restores, nonblank-save imports,
source substitutions after boot, or RNG manipulation. The committed manifest
retains exact ROM/patch/script/trace hashes; ROMs, saves, screenshots, and raw
traces remain private.

Historical native fixtures disable ability gating and area keys and enable Advanced Logic.
That recorded option remains unchanged in the manifest; normal-logic eligibility
is a subsequent host-logic change, covered by host tests at both logic levels.
Permission checks, source-policy monotonicity, progression classification,
RoomSanity, and access-rule negatives need separate host tests; this is not a
native gate-on or full-new-game replay. Production fixture builds were made
from head 96bfc803b with the in-progress Ice integration; their exact byte hashes
are authoritative, not a claim that every later source edit received native QA.

Scope remains guaranteed Foley→Ice, actual acquisition, one witnessed subsequent
respawn, and this complete ingress/attack/crossing. Mixed/failable sources,
arbitrary starting/carried Ice providers, generic room reachability, Phone,
and unrelated Sword/Smash alternatives are not qualified by these tests.
