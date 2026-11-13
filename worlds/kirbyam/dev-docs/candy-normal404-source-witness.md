# Candy Paint 6: qualified ordinary Normal route

## Accepted result and unchanged logic

The reviewed human-only Normal suffix uses the original 427 door into 404,
activates the falling-switch route, and enters 403's
`ENTRY_FROM_9_01` compartment to collect **Paint 6 / 3960505**, native source
`0x088C5EA0`. Actual generated cases are **6 HP / 100%**, **1 HP / 100%** and
**1 HP / 500%** enemy health. Each has an identical cold repeat and a surviving
matched one-frame puff-omission control. There is no 6 HP / 500% run.

This is evidence and regression coverage only. The existing 404 exit already
has a null rule and normalizes to
`REGION_CANDY_CONSTELLATION/ROOM_9_CHEST_2__LOGIC__ENTRY_FROM_9_01`.
That compartment alone owns Paint 6. Native 405 instead enters
`ENTRY_FROM_9_09`, which owns Candy Vitality. The physical parent is not a
bridge between these compartments; their RoomSanity sink is terminal.
No target, copied-ability gate, health item, compiler change or room split is
added. A nominal Normal graph requiring reachable 427 would not encode arrival
history: 404 already has an ungated return to 427.

## Provenance and exact qualification

The frozen source is commit `94c4e638c9de9793e589f3253379a1f5e4009118`, tree
`ef9cec4cd62afb06f14e23cce89ac0941eab19e0`; its reviewed public equivalent is
[`1cb8b12`](https://github.com/hasherwi/Archipelago-kirbyam/tree/1cb8b12ff37bcf4e1dfa31b38aa3cfce7b22cefb).
Native source is
[`7d969fb`](https://github.com/jiangzhengwenjz/katam/tree/7d969fbce14fdc838d2c1ea01389717fb96c3189).
The companion [scalar acceptance record](candy-normal404-acceptance.json) pins
reports, reviews, manifests, generated identity and all nine input/state/result
hashes. Public records omit ROMs, saves, raw memory and controller payloads.

Seed 404 uses native mode 0, gating off and keys off. Production generation and
the normal shipped patch are retained. The actual fixed HP is encoded in the
production ROM, not injected into RAM or relabeled in telemetry. Independent
review verified all 180 native enemy HP entries and corresponding meter
coefficients at 100% and 500%, including Doo HP 4 and 20.

Only 16 startup room/position bytes differ from each production ROM: human 427
at stored (696,80), helpers 101 at (48,80). At frame 1085 the settled human is
427 at (680,72.996). The real 427-to-404 transition occurs at 1097. This near-door
fixture does **not** prove independent upstream availability, arbitrary 427
arrival, the 407 approach or Peppermint 230 ingress. Those remain separate.

Fresh blank batteries and cold starts are used. Eight startup configuration
writes at frame 1085 are **harness-fenced**, with zero BizHawk GUARD requests.
They are not GUARD-protected writes. There are no gameplay RAM writes, runtime
ROM writes or state restores. Contiguous recorded frames are 1085–2277, 1,193
per run, not an all-frame record from boot frame 0.

## Mechanism and timing

The human uses only Normal puff, body contact and flight. There is no copy,
source acquisition, combat reliance or helper participation. All helpers remain
in 101, with no helper-owned attack in the human route rooms or call input.
Helpers' unrelated native behavior is not treated as a route capability.

| Frame | Observed outcome |
| --- | --- |
| 1097 | Enter 404 with lower/upper F1, support and hidden-door tile intact. |
| 1872 | Human puff, category `0x20000042`, damage 2, clears lower F1 (27,6). |
| 1878 / 1884 | Support (27,5), then upper F1 (27,4), clear; the switch falls. |
| 1903 | Human body presses original switch `0x088C600C`; contact identifies human `0x02020EE0`, with no attack in 404 at this instant. |
| 1904 | Original gate `0x088C6030` begins opening. |
| 1926 | Tile (20,4) becomes `0xFF`, exposing original door `0x088940BC` into 403, stored spawn (7,9). |
| 1947 / 1948 | Gate opening completes, then closing begins. |
| 1982 / 1978 | 6 HP / corrected 1 HP human is wholly left of gate edge 352: X 344.703 plus native Normal right bound 6. |
| 1991 | Gate fully closed. |
| 2008 | Enter the Paint 6 compartment of 403 at (104,136.996). |
| 2189 | Chest animation 96 starts beside the exact Paint 6 object. |
| 2277 | Read-only production client poll reads counter 1/source `0x088C5EA0` and emits exactly `3960505` locally. |

The original switch at (440,64) has flags 0, release parameter 0 and room-state
**slot 0**, matching the gate at (360,80). Template prefix `0x0100` does not
mean slot 1. The release parameter plus two is not a two-frame passage window.

Across all three positives, integer contact rectangles overlap at 1902–1909,
the current-contact bit is set at 1903–1910, and slot 0 remains high at
1903–1912. Frames 1911/1912 are the release countdown (1 then 0), not continuing
contact. A stored contact pointer does not imply continued contact. Gate
opening callback runs 1904–1946 and closing callback 1948–1990, independently
of that short slot-high interval.

Active Doo retains HP 4/20. Later HP 1 together with destruction flag `0x1000`
is the non-death despawn path, not combat damage. This matters in controls at
2018 and in positives/repeats after leaving 404. The human takes no damage.

## Corrected controller and decisive controls

The successful 1 HP controller removes **Right only at input frames
1882–1889**, changing Right+Up (80) to Up (64). All other input frames match
the 6 HP controller. The 100% and 500% positives share the same human trajectory.
The historical `left` case name is not a geometric claim: the first press is
at X 446.934, near the switch center/right side.

The literal 6 HP controller at actual 1 HP is preserved as a failed run:
first death is frame 1905, and eventual recovered HP is not survival evidence.
Its changed Doo phase is observed, not attributed to an untested cause.

For each accepted setting the cold repeat matches every recorded state.
Positive and control match through 1869. The only control change is input 1869,
B (2) to no input (0). Controls remain alive in 404 with both F1s and support
intact, door hidden, both slots zero, gate closed, no 403 entry and no check.
This isolates the puff-dependent chain/route for this controller. It does not
separately intervene on body contact, prove global necessity, or establish two
independent F1-trigger recipes. Lower F1 activates the shared group.

## Host predicates, accounting and limits

Local host edge/location predicates remain ungated across modes 0/1/2 and
gating off/on, without ability or health items. These are **host-rule checks**,
not native replays of all settings, RNG, policies or DeathLink. No source is
acquired or copied by this route, so the local rule has no assignment dependency.

When Area Keys are enabled, all four cross-area Candy admissions still require
Candy Constellation - Area Key: central upper platforms to hub, Moonlight warp
to 9_04, Mustard warp to 9_06, and Peppermint warp to 9_01. Only the hub route
also needs Candy Constellation - Hub Connection. These existing host paths do
not supply native proof of upstream approach or accept 407/230 arrivals.

Physical-audit group `404:27,4` is reclassified from `unbound_timed_check_route`
to `qualified_normal427_to_paint6_route`, without rewriting the historical v4
inputs. This is one newly evidenced switch/gate outcome. Its two F1 cells were
already among 43 role-reconciled/narrowed cells: **43 remains 43, and 352
unresolved-role cells in 249 groups remain unchanged**. The 395 figure remains
the historical prior-unadjudicated baseline. There are still 304 groups,
417 initial F1/F6 cells and 35 small switches.

AP structure remains 382 regions, 384 locations, 1,083 surfaces, 57 targets,
144 witnesses and 55 top-level union rows. The six conditional-source fallbacks
and overall partial-completion status are unchanged. 427's Red Paint and Room 3
switches remain separate unresolved objectives. There is no server
acknowledgement, RoomSanity credit, reset-persistence, full upstream or whole-game
claim. Integration checks recompute frozen scalar records; they do not perform
a fresh emulator replay or broaden the accepted health matrix.
