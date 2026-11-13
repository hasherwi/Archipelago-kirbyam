# Rainbow110 Normal payload and underwater spray

**Native evidence and the separate helper supplement are independently accepted
within the bounded scope below. Implementation review remains separate.**
The frozen native packet contains18 cold runs:12 positives including an
identical100% cold repeat, and six matched lower-target omissions. All retain
their initial1HP or6HP. This is source-assignment-independent, not physically
source-free. No helper participates. The compact scalar record is
[rainbow-normal110-acceptance.json](rainbow-normal110-acceptance.json).

## Independent entry and two different payload uses

The independent prerequisite is exactly `REGION_RAINBOW_ROUTE/ROOM_1_06_LOWER_MID`.
Normal starts108 at(504,277), settles at(551.546875,296.99609375), and actually
uses door0x0087847A at tile(34,18) to enter110 at1218, (104,120.99609375).
Generic108/110 access and native503's separate lower-left arrival do not qualify.

Original Sword Knight0x088B74CC, type26 at(120,215.99609375), is captured1443
as a single ordinary mouth payload. No Down overlaps that mouth interval.
B1579 produces ordinary spit animation38 at1580, clearing pending ability and
opening upper F1(14,21), with connected11,26. Equipped ability remains Normal.
The graph's atomic capture/carry/spit requires and consumes this exact finite
object. Swallowing it cannot also supply ammunition; no respawn is assumed.

The source copy hook runs at capture. Pending Knight grants are18 native,
8 shuffled ungated,6 live ungated and0 in gated cases. Pending is not equipment.
Native object.c1195–1250 passes the captured copy ID; kirby.c12100–12156 sets
full-mouth independent of legal low ID. code_0806F780.c1928–2020 selects generic
star size by the multiple-capture bit, not the low copy ID; every accepted
capture is single. kirby.c12346–12367 clears pending during spit without equipping
it. Exceptional ID28 is outside the supported randomization pool. These anchors
use native commit7d969fbce14fdc838d2c1ea01389717fb96c3189.

Original Waddle Dee0x088B7484 takes2damage from Normal's falling body. It dies
at50–124% health; at125–500% the same controller captures it1796 and spits LEFT
1814, never swallowing/copying. Left disposal avoids opening13,32 prematurely.
A later slide opens that chain. This enemy is an optional obstacle, not required
target ammunition: the lower-health route already works after its death. The
atomic continuation records both branches without inventing a live Waddle copy
source where the enemy is dead. Pending Waddle values include0 native,5 shuffled
and18 live; all are cleared. Live telemetry records two capture-policy decisions,
not two equipment grants.

Normal floats over the first pool, slides2,43 from the left, then slides2,55 and
its chain. A jump across the lower pool draws Blipper left. Batty and Blipper
remain alive; no health tanking, copied combat ability or invulnerability is used.

## Exact lower spray and completed continuation

Right+B2785–2794 is the lower-target action. At2788 Kirby is underwater at
(174.09375,926.73046875), Normal, animation66. The parent-linked spray has
category0x30000043, animation0x2E/0, tile bounds(-8,-12,12,10), and center
(197.2734375,926.73046875). Its scanner covers columns11–13/rows57–58 across
solid column12 and changes exact F1(13,57). Damage bounds(-8,-12,10,11) are
separate. Unrelated upper F1(12,50) remains sealed throughout110.

The spray's source constructor/update is code_0806F780.c4214–4358, with horizontal
x+16 initialization, an eight-update packet cycle, no terrain query and the
ordinary tile scanner. kirby.c14063–14085 selects horizontal66/up67/down68.
This is neither the ordinary mouth star, a dry puff nor the underwater Sword spin.

The connected chain opens the right shaft and14,63. Normal crosses above the
permanent column, descends the right shaft and enters the exit pool. Up3481
starts the real door animation3482 and enters554 at3493. Final3572 is alive and
Normal. The water flag clears3503; this is not an underwater554 landing claim.

## Runtime identity, health and controls

Production/client commit714a06f8794076e3261062344dfad8f3810d6898 has tree
49a999340b61aa144c3e77118c8ee3ec7c9a41c7. Only startup room/position fixture bytes
change; original enemies, source tables, targets, terrain, doors and HP are
preserved. Cold blank battery loading precedes frames. Eight actual client copy
configuration writes occur at1085 before movement; key-enabled cases also sync
the generated starting mask0x4 once. Gated variants own no copied permissions.
The raw Transport logger mislabeled the key-address write0x0203B0C0 as copy sync;
the derived scalar record corrects its caller to `_sync_area_key_runtime_config`
and retains all raw hashes. The other eight origins remain copy/config sync.
Startup fixture helpers are in room 101 and global AI is 0. This is not a normal
global AI300 replay. The separately reviewed read-only supplement matches all
2,488 frozen 500% / 1 HP human samples, effects and results. All three helpers
remain in 101 while the human traverses 108 → 110 → 554. Helper 1 acquires
Fighter remotely; helpers are not absent, disabled or all Normal. No helper
participation or ability is credited. Live task identity and TASK_INACTIVE
clear establish scheduler eligibility, not execution on every frame.

Frames 1218–1226 retain three kind-1 room-108 registry entries with null parents.
Only the kind-2 attack counts are always zero at post-frame observation. Counts
are cleared after collision processing, so an empty registry cannot establish
attack absence. The retained pointer scan is not a complete live-attack census.
Continuous helper room separation, the target spray's human parent 0x02020EE0,
native room-scoped mechanics and the matched omission control support the
nonparticipation conclusion. The supplement adds only reads and preserves the
original 96 artifacts, seven dependencies and historical first100 packet.

There are no later gameplay writes or state restores. Both doors are within
Rainbow, so key-on coverage does not imply bypassing an inter-area key.

Discrete positive coverage is1HP at50/100/124/125/500% and6HP at100/500%, plus
shuffled/live500%1HP with gating on/off and Area Keys on. Source-policy equivalence
for other legal assignments is a source argument, not a replay of every grant.

The Waddle's scaled native2HP, rounded half-up, is1–2 at50–124 and3–10 at125–500.
The fixed2damage therefore partitions death versus survival at125. The surviving
125%/500% objects share position/flags before capture; generic inhale forces HP0.
Knight inhale also forces HP0, independent of its scaled2–20HP. Unattacked
Batty/Blipper do not introduce numeric-HP combat dependencies. This supports the
bounded kill-or-capture strategy, not a451-percentage sweep or global monotonicity.

Six matched controls cover native50/100/125/500%1HP and shuffled/live gated500%1HP.
Only target input2785 changes Right+B18 to Right16. Each full sampled prefix
matches through2785; all controls preserve1HP, keep13,57 sealed and never enter554.
The100% cold repeat matches every sample. The old first100 packet stays frozen.
The earlier500% incidental Waddle swallow, right-facing secondary-spit failure,
and initial gated runs with incorrect setup assertions are excluded.

## Installed bounded route

One exact target ORs Normal with the prior Spark and Sword graphs. Their new
graph-local raw singleton predicates preserve finite source access, acquisition,
permissions and carried equipment without permission-filtered live guarantees.
The Normal graph has no source-policy predicate or copy permission. Existing
`uses_object` consumption models its one atomic Knight capture/carry/spit; no
new persistent mouth state or schema is introduced. Both new effects require
actual Normal equipment, exact native110 and their own dry/swimming medium.
No `opens`, source retry, implicit reset or generic ammunition is supported.

Other exits, RoomSanity, Green Paint3960503, native503 and real Area Keys stay
separate. Spark progression follows enabled Green Paint or the independent
Chocolate Spark reason. Historical Spark/Sword packets retain their original
health, entry and policy limits. This candidate does not make PR1052 complete.

## Independent review bindings

The compact scalar record binds the original packet, accepted main review,
helper supplement and supplement review by SHA-256. The combined review
manifest is `28cd3b98846404162e63d38c3759425395479443d0948ee3c0b5de43e475d3c0`.
Derived provenance and registry wording are corrected without altering any
frozen input. This acceptance does not establish arbitrary arrivals, every
seed/RNG state, global AI-state equivalence or completion of PR1052.
