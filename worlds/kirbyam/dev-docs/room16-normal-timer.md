# Mustard Room 4-16: explicit Completely Random timer patch

Issue #1126 is resolved by a room edit, not a claim that a finite Foley roll will
provide the required equipment. Newly generated Completely Random policies record
`room16_switch_timer_frames: 600`. Their ROM token changes only the little-endian
halfword at ROM offset `0x008C2708`: native533 switch template `0x088C26F0` + `0x18`,
from zero to600. This is the native release-delay field. `sub_081197D4` loads it
plus2 on activation and decrements it after release; the room state and gate still
close normally. No permanent-open flag, source remapping, global timer change or
full-completion bypass is introduced. Off/Shuffled retain zero and their existing
source-aware routes. Old tracker slots without the explicit marker retain the
old fail-closed rule.

The ordinary Normal approach is the previously reviewed Hub4/native590 ->534
->533 route. At the actual533 arrival (616,264.996), Kirby flies around the lower
obstacles, reaches the switch and stands on it without swallowing Foley. After
release, fly left over the upper block, descend, rise through the open gate's
lower opening, clear the left star block with an air puff and enter325. The
continuous positive enters325 at frame4698, retaining Normal and HP6. There is
no Phone input, state restore, runtime gameplay write or helper participation.

A matched cold control replays identical controller inputs with the native zero
timer: it remains533. Both use the production Completely Random client startup
configuration (full pool, weight55), so the positive does not depend on a
particular copy outcome. The earlier unmodified standing-switch test activated
then released the switch but did not finish the crossing. These attempts do not
prove every untested carried-object or Phone route impossible. No independently
guaranteed random enemy acquisition was established; the explicit room patch
avoids using such an assumption.

The graph is installed as a profile-specific OR alongside the existing room
catalog witnesses, using the same traversal engine and independent Hub4 access.
The profile marker travels in the existing source-policy slot data, allowing
tracker reconstruction to reproduce the exact ROM contract. Static source
preflight accepts this Normal graph, while final full-completion/accessibility
validation still checks all required visits and locations.

See [controller acceptance](room16-normal-timer-acceptance.json). Fixture ROMs,
saves and full traces remain private. The manifest records their hashes and
controller inputs; startup room/position fixtures precede all controller frames.
