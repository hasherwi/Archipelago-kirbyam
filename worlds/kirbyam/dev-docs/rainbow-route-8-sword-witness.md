# Rainbow Route Room8 underwater Sword alternative

This bounded witness adds a separate Sword alternative to `bomb_110_room9`, on
its existing Room8/native110 to Room9/native554 AP exit. It does not widen the
existing dry Spark capability, add a room-wide gate, or establish landing-wave
range. The compact runtime record is [rainbow-route-8-sword-runtime.json](rainbow-route-8-sword-runtime.json).

## Entry, acquisition and carry

The independent prerequisite is exactly
`REGION_RAINBOW_ROUTE/ROOM_1_06_LOWER_MID`. Native108 door record0x0087847A at
tile(34,18) selects110 spawn(7,8), decoded arrival(104,120.99609375). The startup
fixture reproduces this arrival; the incoming108 to110 door was **not replayed**.
Generic110 access or another108 compartment cannot supply this route.

Kirby starts Normal at1085. Original spawn-table1 Sword Knight0x088B74CC,
type0x1A at(120,216), retains native copy field18. Normal inhale and Down acquire
Sword at1359. The source is finite: no substitute essence, reset, renewal or retry.
Sword stays equipped throughout all later positive samples, including native554.

The route clears the upper right chains, crosses the first pool2036–2162,
opens the left F1(2,43), descends the left shaft and enters the lower pool2634.
Native enemy combat is included, with repeated attacks against surviving enemies
at500% health. Brief dry/water changes2840/2857 precede the exact target attack.
The path leaves that pool2932, descends the opened right shaft, enters the exit
pool3085 and reaches554 at3388. Its transient water flag clears3398; this is not
an assertion that the554 landing point is underwater.

## Exact attached underwater attack

Kirby at(185.99609375,926.71484375), water true, state0x69 creates an attached
Sword weapon animation0x6F variant1. Registered effect0x03004008 is parented to
Kirby0x02020EE0 and has flags0xA2084100. Active tile bounds(0,-26,25,-3) scan
columns11–13 and rows56–57 after integer quantization. This flips the specific
F1(13,57) through solid column12, at2886 for50/100% or2889 for500% enemy health.
The separate upper F1(12,50) remains sealed.

This is not the independent animation0x9C landing wave. Native
`src/code_0806F780.c:2884–3064` creates/updates the attached Sword effect and
copies sprite bounds to its tile scan without terrain-query movement. Native
`src/kirby.c:16774–16800` selects state0x69 for the moving underwater attack;
ROM table0x0834FF14 selects weapon0x6F/1. These anchors use native
`7d969fbce14fdc838d2c1ea01389717fb96c3189`.

## Accepted production replays and controls

Five strict fresh-boot production replays pass without damage:

- Actual1HP with enemy health50%,100%,500%.
- Actual6HP with enemy health100%,500%.

All enter554 at3388 and run to3467 with Sword retained. Three matched1HP controls
omit only the30-frame B press starting2882. Their full sampled states match each
positive through2882, then remain in110 with F1(13,57) sealed. Exact hashes,
fixture byte differences, hit registration and medium transitions are retained.
The100%1HP build is `8dbf941f30f88f8d0f151e2a556d31ca19aa6ac5`; the other four
are `b98feba7d5b771919ab8f0ad642c11570e3c6427`. These are distinct artifacts,
not relabeled rebuilds.

Only native assignment, ability gating off and Area Keys off were replayed.
The real client's eight guarded configuration writes occur at1085 before movement.
The accepted script then seals its write path: no gameplay RAM writes or state
restores. Fixture changes are startup-room/position fields only. Original source,
door and target content are unchanged.

These are discrete tested enemy-health values, not an exhaustive50–500 sweep.
No new health monotonicity, arbitrary approach, generic Sword range or other
ability equivalence is claimed.

## Logic binding and source-policy boundary

The two graph alternatives live under the same target row and one installed rule:
finite SPARKY→Spark with its unchanged dry attack, **or** finite
SWORD_KNIGHT→Sword with `bomb_110_room9_underwater_sword` requiring swimming.
Both need the exact independent108 lower-mid entry. Carry edges mark the dry and
swimming portions separately and never synthesize equipment from permission.

Target applicability is the explicit disjunction of those two guaranteed-source
conditions, scoped only to this target/owner/exit. Legacy single-source conditions
remain unchanged and cannot coexist with that disjunction. A mixed or failable
finite live pool is not a guarantee, and source-policy absence preserves prior
partial behavior rather than declaring all unreviewed routes impossible.

The resolver already reads the same deterministic ROM table or eligible live
pool used by runtime. A deterministic assignment or no-failure singleton live
pool yielding the exact same ability supports the same source grant in logic;
that equivalence is not another native replay. Gating requires the corresponding
permission at acquisition. Sword is already gateable/progression; the existing
conditional Spark promotion remains tied to SPARKY→Spark, not merely to this OR.

Other exits, RoomSanity and Area Keys are unchanged. The normalized AP target
count stays36. Logic tests cover isolated alternatives, missing/behind-gate
sources, wrong permissions/entry/media, malformed conditions and actual-world
wiring. Sample restrictive fills at1HP use unmodified broad policies, full
accessibility, native seed110 and Sword-only shuffled seeds30/17, with gating and
Area Keys on/off. They assert every location filled, beatability and full
accessibility; they are not new gameplay evidence or exhaustive seed coverage.
