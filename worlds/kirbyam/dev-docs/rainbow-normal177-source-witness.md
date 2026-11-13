# Rainbow Goal 3: ordinary Normal large-star route

Independent artifact/source review and production ROM reconstruction passed for
four ungated witnesses: enemy health 100%/500% crossed with actual HP 1/6.
`rainbow-normal177-acceptance.json` retains reviewed scalars and private artifact
hashes, not ROMs, saves, raw traces or private paths. This documentation/test
integration does not change production behavior or introduce a traversal target.

## Exact ownership and boundary

Native 177 owns `REGION_RAINBOW_ROUTE/ROOM_1_GOAL_3` and its minor chest
`MINOR_CHEST_RAINBOW_ROUTE_1_GOAL_3` / 3960568, physical template 0x088BB0BC.
Its existing null location requirement remains unchanged. The native switch is
object index 9 at (120,288), counter 60, activating slot 2. The central-circle exit
still requires `can_break_block`; no exit or RoomSanity result is credited.

Each cold boot reproduces native 178's unique right incoming boundary at
(1432,136.99609375), then actually enters 177 at (712,56.99609375). Fixture changes
are exactly 15 startup room/position bytes; eight fenced client configuration
writes occur at frame 1085. No gameplay injection, runtime ROM writes, state
restoration or helpers in 178/177 occur. Reaching upstream 138 or reaching this
boundary from a new game is not established.

## Native mechanism and controls

Normal completes the ingress and Box Boxer fight, then genuinely captures two
original Flamers in one pass. The multi-mouth flag survives until the final
large-star shot. At 500%, the 1 HP recipe captures Flamers 1+2, while 6 HP captures
1+3; both 100% recipes capture 1+3. These are distinct input recipes, not proof
that one controller stream works at every health. Offscreen unloading and
reactivation do not establish continuous object identity.

The damage 25 Normal star survives contact with the closed dynamic door object,
activates the switch, and permits physical passage and chest collection. Native
`code_0806F780.c::sub_080728B0` exempts damage 25 from object-contact destruction
but still checks terrain collision. This is **object-door bypass, not terrain
piercing**, and not a general Normal ranged capability or copied equipment.

All four positives remain Normal without damage. Each control removes only the
one-frame final B input from the matched positive prefix, ending 81 frames after
the omitted shot, before the positive's later chest/final frame. Controls retain
the multi-mouth payload at x 182 with slot 2 and chest counter zero, and no local
client check. Positives reach the physical chest and local production-client
LocationChecks 3960568. This is not a server submission. Controls establish the
role of the final shot in these runs, not universal failure of alternatives.

## Integration and limits

The AP runs used source 6948ac7295d3b3e8e1eaf08506338592d707254e and native
source 7d969fbce14fdc838d2c1ea01389717fb96c3189. Independent review checked relevant
client, ROM, rules, payload and runtime code against integration base d04d4d0;
this does not relabel the old runs as current-commit replays.

The original matrix accepts only sampled health endpoints and tested ungated
policies. Source reasoning about native consumption and copy policy is distinct
from the separately reviewed gated runtime supplement below. No all-RNG/options,
health continuum, central-circle return or RoomSanity proof follows. These limits
do not justify inventing health restrictions or an equipped Copy Ability gate on the existing
null chest rule. Earlier failed upper drop-through and ordinary damage 10-star
attempts are contextual controls, not proof of an exclusive Fighter requirement.

## Separate gated representative

The original four ungated records are unchanged. Independent review also passed
one gated, no-items-received witness at actual 1 HP and 500% enemy health, from
the same native 178 boundary. All 32,924 samples remain Normal and HP 1, with
unlock mask zero. Original Flamers 1+2 produce pending mouth 0x40; the damage 25
star contacts the gate at frame 33389, the switch at 33399 and sets slot 2 at
33400. Physical chest collection at 33869 precedes local client check 3960568.
Its matched control omits only B at 33386 and stops at 33467 with mouth 0x40,
x 182, no switch/chest event and no client check. Setup and no-injection limits
are unchanged. This representative does not prove every random policy, a gated
6 HP/100% matrix, upstream access or a universal fixed input recipe.
