# Generated source activation and lifetime (#1118)

Generated inventory candidates require an evidenced activation edge before they
can be acquired. Permission and reaching the source compartment do not activate
it. The carry solver tracks active and expired output lifetimes separately from
held equipment and finite consumption. Ending a lifetime prevents acquisition,
but does not erase equipment already swallowed. A room-instance reset clears
activation; explicit revival only permits subsequent generation. It does not
manufacture a live object. An activation cannot revive an expired output or
recycle a consumed finite instance.

The lifetime identity is the generated output record, not its parent placement.
Native `sub_080AA6F8` destroys the random-statue controller after creating two
independent statues. Ordinary spawner construction likewise does not attach the
child to the controller. Controller defeat therefore cannot universally mean
child destruction. For attached projectiles, `object.c:sub_0809F840` destroys the
child when its parent is destroyed or has zero HP, except while the child's
`unkC & 0x400` interaction flag is set. No held-object exception or unreviewed
phase transition is admitted by this change; a graph must evidence its explicit
expiry edge. Separate generated phases and outputs retain separate identities.

All 37 object-spawner prototypes now record decoded counter-bank and threshold,
delay, startup timer and capacity predicates from the pinned
`asm/object_spawner.s`, plus its 32-slot global search bound. The search falls
through after exhaustion; safe exhaustion behavior is not certified. Actual
counter state and physical acquisition paths remain unresolved. All 37 have
capacity one and no destroyed-slot reclamation;
none supplies an unlimited retry guarantee. These native predicates are data,
not automatically satisfied AP requirements.

The two room951 random-statue slots preserve all 19 native selections. A fixed
selection is evaluated using every alternative's actual runtime SourcePolicy
grant. One convenient possible branch cannot become a guarantee; an empty or
unowned branch remains a failure outcome. Explicitly witnessed retouch may be
renewable, but cannot reroll the native selection. Live runtime randomness and
native branch selection are separate; no branch retry is admitted.

`generated-statue-native-acceptance.json` records four fresh blank-battery checks.
From a configured lower-floor arrival, vanilla contact grants Beam, dropping it
and retouching the same statue grants Beam again, and singleton shuffled contact
and retouch grant Cutter. Unowned gated Cutter grants nothing. Both outputs have
no parent attachment and persist after their controller disappears. The upper
platform fixture cannot contact them. Room951 has no reviewed independent AP
entry; the lower-floor fixture does not establish one. No room-reset selection
or route into the lower floor is inferred.

`generated-frosty-native-acceptance.json` binds the original room955 Frosty's
small-cube call at `src/mr_frosty.c:762`. With singleton shuffled Cutter, the
player acquires Cutter at frame1752 while Frosty remains alive at 30 HP. The
cube is attached to that Frosty; its vanilla native grant is Normal. Vanilla and
unowned gated Cutter controls do not acquire an ability during the matched
1765-frame checks. Each starts at 6 HP and takes one hit. This is a conditional
local acquisition witness, not a safe one-hit-mode or independent world route.
Encounter-generated sources remain Advanced-only, including normally empty
projectiles that become eligible through the actual runtime configuration.

These records certify the shared mechanics and bounded observations. They do
not certify all 731 encounter candidates, all branch predicates, phase changes,
controller defeat sequences, room-reset revival or safe repeatability. Unproved
candidates remain unresolved and add no automatic world access. No new world
entrance or target graph is installed from a configured native fixture. Existing
Normal witnesses and the paused #1059 playthrough are preserved.
