# Mustard Room15: bounded Bomb placement and timed gate

This is one complete solo alternative for native533's small switch, not a general ranged-attack or Phone provider list. It adds only the native533→325 exit rule when the actual Foley source is guaranteed to grant Bomb. A separate [UFO top-charge graph](mustard-room15-ufo-source-witness.md) now covers guaranteed UFO from the same source. Other assignments now remain out of logic unless covered by a complete reviewed alternative (see issue #1099 below). Bomb is already a progression item and remains subject to the ROM's ability-permission gate.

## Actual source and entry

The accepted cold-boot fixture changes startup coordinates to Rainbow Hub4/native590 and moves AI starts to101. It does not replace enemies, abilities, terrain, doors or payloads. From Normal, the replay enters534 through its actual lower-left Hub4 door. It inhales the native Twister, spits that payload away, then inhales the native Waddle Dee and spits it into the lower Bomb Block barrier. It climbs around the right side, deflates while moving left to dodge Bronto Burt, and uses Normal air puffs to open the upper Bomb Block barrier and clear the star at the533 doorway. These are actual payload/action sequences, not Copy Ability inventory grants.

The actual534→533 arrival is(616,264.996). The replay flies around the lower obstacles and returns through the upper-right viewport before approaching Foley at(224,64), template0x088C2714. The earlier falling Foley is not treated as an inexhaustible randomized source. One final physical acquisition grants Bomb. The graph starts at independently reachable REGION_RAINBOW_ROUTE/ROOM_1_HUB_4; generic534 or533 reachability cannot supply this approach.

## Attack and completed crossing

At frame4457 the player presses B for one frame, then Down+B for30frames. This places Bomb beside the barrier rather than merely crouching or throwing it away. After retreat, the explosion activates small-switch template0x088C26F0 at(312,144). The player crosses the timed gate0x088C26CC and enters the actual325 door at frame4890. The graph's terminal pose represents this completed sequence. It does not give persistent switch credit or gate other exits, checks or RoomSanity.

Matched controls remove only B from those two placement segments. They acquire the same Bomb and follow all other inputs but remain in533. Both positive and control runs were repeated with production enemy-health scaling at100% and500%. Every gameplay frame1085–4958 has HP6, no decreases, no runtime writes and no state restoration. This supports a no-damage movement sequence; it is not a direct1HP or patched-AP-ROM replay. Health scaling is applied before boot, not by editing live health.

The compact acceptance manifest is [mustard-room15-bomb-acceptance.json](mustard-room15-bomb-acceptance.json). It retains input/reproducer/ROM/bridge hashes, full positive input sequence, selected checkpoints and matched control results. Original USA SHA1 is274b102b6d940f46861a92b4e65f89a51815c12c. Native source revision is7d969fbce14fdc838d2c1ea01389717fb96c3189.

## Limits and alternative composition

The source condition is guaranteed FOLEY→Bomb, including equivalent shuffled assignments, not a prediction of finite random rolls. No other attack's carry, placement, range or timer is inferred. Foley's own environmental explosion is a separate unproven alternative. The upper534 fixture-only experiments are superseded by this Hub4 approach.

Future reviewed ranged, environmental or Phone alternatives for this same exit belong in the same target row, switch_533_room16, as alternative complete graphs. Separate add_rule calls would combine with AND and must not be used to require both Bomb and Phone. Ordinary solo alternatives remain part of the outstanding investigation; this bounded subset is not completion of PR1052's broad scope.

## All-policy access rule (issue #1099)

The timed Room15 → Room16 edge now always enforces reviewed source-backed access.
Policies outside the guaranteed-source subset explicitly close the edge; supported
policies use the existing reviewed traversal graphs.
Unsupported Foley assignments, mixed live-random results, and failable finite
sources no longer bypass that rule. Ability ownership alone does not equip Kirby,
and Phone is not assumed to supply an unreviewed alternative. Missing source-policy
data also keeps this edge closed. Supported Bomb/UFO/Ice and Advanced-only Crash/Magic
witnesses retain their existing entry, equipment, permission and crossing checks.

This is an optional progression route, not an unconditional generation constraint:
the existing Room15 → Room17 → Room18 route bypasses Room16. Room16 itself contains
only its optional RoomSanity check; the bypass does **not** grant access to it.
With RoomSanity enabled, issue #1124 adds the Room16 visit to the early source
feasibility filter in both Full and Minimal accessibility. Shuffled mode searches
the same bounded deterministic policy stream; a candidate must pass this witness
and the existing source checks together. The accepted mapping is shared by logic
and ROM patching. Off retains vanilla Foley Bomb. Completely Random cannot
guarantee an eligible finite Foley grant, so this combination reports an early
error. Shuffled with 100% no-ability weight also reports an early error. With
RoomSanity off, the source filter still does not resample to qualify this optional
exit. Final validation continues to check every enabled check, including actual
entry and progression. This is not proof that unreviewed routes are impossible.

The applicability check uses the unfiltered source policy. It must not infer a
guaranteed finite grant from the currently owned subset of ability permissions:
collecting another permission could widen the live-random pool and invalidate
that inference, violating monotone access rules.


### Fuzzer rejection evidence

The final all-check validator still rejects unsafe outputs. For an exact,
single-player Room16 source/Advanced-option exclusion, it also logs the actual
raw source policy and seed. The optional fuzzer classifier reconstructs that
policy independently and checks the current target contract, rolled options,
terminal exception, and reproducer. Qualified sources, missing proof, other
infeasible checks, and full-accessibility placement failures remain unclassified.
Raw failure counts and the minimum 50% playable-generation floor are unchanged.
See `issue1099-fuzz-replay.json` for the bounded 119-case replay audit and the
separate fresh local fuzz result; neither establishes native gameplay coverage.

The normal-logic [Ice alternative](mustard-room15-ice-source-witness.md) also
requires guaranteed Foley→Ice, natural acquisition and one witnessed camera
respawn for a distinct finite frozen projectile. It does not qualify arbitrary
carried Ice, mixed/failable grants or unlimited source retries.
