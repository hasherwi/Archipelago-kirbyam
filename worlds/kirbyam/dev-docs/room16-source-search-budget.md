# Room16 joint source search: CI case202

Run 44848017675 (artifact 14684002928) rejected Shuffled seed 587276755 before fill:
RoomSanity on, Standard Logic, randomized statues, 71% no-ability weight. The
initial source-policy seed was 2450128862376293350. All 8192 candidates failed the
joint source constraints. The same input fails on main `06f398912`; it is not caused
by the Completely Random timer or the Advanced Fire route.

The unchanged deterministic candidate stream first succeeds at attempt 8552,
policy seed 884389559316697767. Full generation then passes the unchanged final
all-check audit and produces an archive. The regression fixture retains the
original fuzzer YAML, including its normalized health-range settings. Tests also
reproduce the old 8192-cap refusal and absence of an output archive.

Production generation now gives Shuffled policies 16384 attempts only when
RoomSanity or the 100% goal requires Room16. Other profiles and the standalone
validator's default retain 8192; explicit caller budgets remain exact. The Room16
prerequisite is checked before the more expensive Wheel/peg/catalog graphs.
This consumes no RNG, changes no source grant or ability weight, and selects the
same first jointly valid candidate that the original evaluation order would
select. Exhaustion still fails closed and describes the unsatisfied joint search;
it is not treated as proof that no possible assignment exists.

This adjusts the existing pre-fill source-policy selection. It does not restart
generation or fill, introduce a launcher, alter another player's options, force
Foley's assignment, or classify search exhaustion as a successful fuzz case. No
fuzzer classification was relaxed. The Completely Random timer and Advanced Fire
route are unchanged. A bounded search can still exhaust on other seeds; that
remains an explicit error with no emitted archive.

## CI cases 369 and 497: only repair an exhausted Shuffle

Case 369 (seed 89287592, RoomSanity, Standard, 83% no-ability) exhausts the
same 16,384 assignments. Case 497 exercises the independent 100% Game
Completion requirement at 96% with RoomSanity off. When that happens,
generation can exchange Foley's assignment with an already eligible enemy
type from an existing candidate. The original stream still wins whenever it
succeeds. The repair draws no new source policies, preserves the grant
multiset and statues, and is deliberately conditioned on the required
witness rather than an unconditioned shuffle. The emitted policy records
the donor and still needs every ordinary source proof and the final
placed-progression audit. It does not extend native timed switches.

In case 369, after the source repair, Archipelago's Minimal placement left
Stone behind its own gate at Room 9-CHEST_1; placing that single existing
permission early opens the 16 checks the final audit had identified. After
plando, an affected gated Minimal slot requests normal Archipelago early
placement only if the profile still has a check that depends on Stone.
Already placed or precollected copies and existing early requests take
precedence. The request respects ordinary item placement rules, never
precollects the item, and leaves a case with no valid placement subject to
the same final audit. Minimal remains the recorded accessibility setting.
