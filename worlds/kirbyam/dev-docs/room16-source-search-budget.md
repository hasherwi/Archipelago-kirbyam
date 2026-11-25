# Room16 joint source search: CI case202

Run 44848017675 (artifact 14684002928) rejected Shuffled seed 587276755 before fill:
RoomSanity on, Standard Logic, randomized statues, 71% no-ability weight. The
initial source-policy seed was 2450128862376293350. All 8192 candidates failed the
joint source constraints. The same input fails on main `06f398912`; it is not caused
by the Completely Random timer or the Advanced Fire route.

With the former randomized Copy Ability Room statues, the same candidate stream
first succeeded at attempt 8552,
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

## Fixed Copy Ability Room statues

With the Copy Ability Room keeping its vanilla statues, the identical input
and candidate stream first qualify at attempt 3354, policy seed
9372867150608014686. A 3353-attempt run still fails closed, and the first valid
candidate passes the unchanged final all-check audit. The regression separately
replays 8192-attempt exhaustion using the former statue semantics. The
production search budget remains unchanged.
