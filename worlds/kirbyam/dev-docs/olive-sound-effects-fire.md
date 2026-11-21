# Olive Sound Effects: Advanced Fire alternative

Issue #1127 adds one dry native825 capability, `switch_825_fire_breath`, as an
Advanced-only OR on `frozen_825_sound_effects`. Existing Ice, UFO and generated-Ice
witnesses are unchanged. This is not generic Fire range or a RoomSanity gate.

## Physical acquisition and carry

Cold runs start at the reviewed native814 right-door approach and traverse the
complete Normal831 maze into825 at (280,296.996). The independent graph access is
`ROOM_6_14`, qualified by its actual831 bottom-left arrival, as in the existing
[UFO composition](olive-sound-effects-ufo.md).

Original Hot Head at (184,296), template `0x088CD3A8`, is reachable before Frosty.
Kirby inhales and swallows it, acquiring Fire at frame3860. The physical binding
is `room:825/template:0x088CD3A8`; permission is not equipment. Only a guaranteed
singleton HOT_HEAD ->Fire grant admits this finite source, including equivalent
Shuffled policies. Mixed live pools or nonzero no-ability weight do not become a
finite guarantee, and the graph does not retry the enemy.

Kirby clears the lower star blocks with Fire, flies to Frosty, defeats the
original Frosty with Fire and exits the arena carrying it. The recorded route
later takes one Waddle hit, drops Fire, inhales its actual copy star and reacquires
Fire before the final setup. This is an observed recovery, not permission-based
re-equipping. Damage taken in this execution is not a traversal requirement or
proof that a cleaner execution is impossible. These runs use six starting HP and
100% enemy health; they do not claim a tested continuum of health settings.

## Exact switch setup

Stand on the **lower step at approximately (570,121)** immediately left of the
enclosure. Start Fire breath, then continue holding B and Right. Right extends
Fire's active attack; simply facing right with B alone is not the demonstrated
input. Watch the switch/gate, release the attack upon activation, jump onto the
next step, cross the opening and collect the chest with Up. The source, switch,
gate and chest templates are respectively `0x088CD3A8`, `0x088CD360`,
`0x088CD33C`, `0x088CD2F4`.

Three cold positive runs vary the pre-attack delay by0/37/211frames. They activate
the switch at11532/11660/11821 and collect chest66 at11745/11873/12034. A matched
no-target-attack control does not activate or collect. A separate identical
positive replay through the current production client emits exactly
`LocationChecks: [3960523]`; this is local client output, not server submission.
A further cold run uses a full-pool Shuffled policy with guaranteed Hot Head Fire,
eight real startup client configuration writes, identical controller inputs and
the same successful client check. Its exact policy is recorded in the manifest.

The active player0 attack task `0x080737D9` has damage5 and mask`0xA0000103`.
Native `sub_080734F8/sub_080737D8` reroll its acceleration; `sub_0805D268` adjusts
speed from directional controller input. This affects the hit packet, not just
visual flame particles. The reported15–20seconds and these measured waits are
observations, **not a guaranteed upper bound**. The maintained Fire action can
continue without spending another source; no favorable copy-ability roll is
assumed. The logic represents a reactive timed crossing, not a permanent switch
event or fixed-duration guarantee.

The lower floor at (554,137), upper step at (586,105), and different breath
inputs did not activate the switch in exploratory trials. They are not admitted
by this exact capability. These negative trials do not prove all other poses
impossible. Helpers remain outside814/831/825 throughout the qualified runs;
no Phone input, live gameplay write or state restore occurs.

See [controller acceptance](olive-sound-effects-fire-acceptance.json). ROMs,
saves, screenshots and full traces remain private; the public manifest contains
inputs, event identity and safe reproducibility hashes only.
