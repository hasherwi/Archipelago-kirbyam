# Rainbow 138 Green Paint: finite natural Spark carry

## Installed scope

`bomb_138_green` gates only `MINOR_CHEST_SPRAY_PAINT_04` (check 3960503),
owned by `REGION_RAINBOW_ROUTE/ROOM_1_28`. Independent access is exactly
`REGION_RAINBOW_ROUTE/ROOM_1_27_UPPER_LEFT`. The graph starts Normal in that
native 532 compartment, enters 138 through the original door, acquires the
original finite Sparky `0x088B9F90` at (496,88), and carries Spark to the chest.
Base Room27, its upper-right compartment or a native room number is insufficient.

The graph installs only when the production source policy guarantees
`SPARKY -> Spark`. Unsupported assignments retain the prior partial behavior,
not a claim that the check is physically accessible under those assignments.
A multi-outcome or failure-weighted finite random source gets no eventual-draw
promise. Guaranteed same-Spark assignments in randomized modes are supported by
the existing source-policy model; they are **not randomized native acceptance**.
The native proof uses natural mode 0, ability gating off and Area Keys off.

Spark inventory is permission to acquire the source, never equipment. Gating-on
logic requires Spark permission plus independent entry and finite acquisition.
The existing Room8 Spark promotion already covers this exact guaranteed-source
condition. Room8 remains enabled when optional paint is disabled, so no new or
broader progression classification condition is necessary.

The capability is restricted to a dry attack inside native 138 and represents
selectively activating the lower F1 while retaining the upper one. It is not
ordinary F1 or global Spark collision equivalence. There is no persistent open
event, room-wide gate or additional exit requirement. Other checks, exits,
RoomSanity ownership and Area Key boundaries are unchanged.

## Observed continuous route

The retained `rainbow-green-source-runtime.json` includes actual outcomes,
controller inputs, source observations, exact client configuration writes,
result/per-frame/ROM hashes and provenance. These records are condensed from
four positive cold boots and two matched negatives, not just expected results.

- Frame 1085: Normal at (72,56.996) inside native 532 upper-left. The fixture's
  starting coordinates are (80,64).
- Frame 1302: original door tile (2,3) enters native 138 at spawn tiles (44,7),
  actual position (696,104.996). Both F1s are intact.
- Frame 1451: original Sparky has native copy field 15 and HP 4 or 20 at the
  two tested enemy-health settings. Frame 1544: swallowing assigns Spark.
- Frames 3287–3587: a **300-frame Spark hold** at the bottom of the star-block
  shaft clears the approach before rising. The shorter exploratory schedule
  lost HP at 500% enemy health and failed at 1HP; it is not accepted evidence.
- Frame 3749: settled dry pose (554.855,200.996), both triggers still intact.
- Frame 3755: lower F1 (36,13) clears. Upper F1 (37,12) remains `0xF1` for
  the entire positive route.
- Frame 3989: physical chest at (648,248) opens, setting chest flag 7 and source
  event `0x088B9FD8`. The actual client captures only `LocationChecks [3960503]`.
  Native spray ownership stays unset under the AP-owned reward hook.

All four positive runs use the same final inputs: actual initial/max HP 1 or 6,
with enemy health 100% or 500%. Every sampled gameplay frame preserves HP;
Spark remains equipped after acquisition and no helper participates. The option
supports **50–500%** enemy health. Only 100% and 500% were replayed:
**50–99% and 101–499% were not independently replayed**. These are sampled
settings, not the supported range's endpoints or an interpolation proof.

## Matched controls

Both controls use the positive 500%-enemy-health, actual-1HP fixture, preserve
HP and Spark, and share the complete prefix through frame 3749.

1. **No target attack:** replace only the 60-frame B hold starting at 3749 with
   neutral input. Both F1s stay intact. The attempted crossing ends at
   (576.058,200.996), without chest flag, event or client check.
2. **Both triggers:** move/jump closer before attacking. Both F1s change in
   the same observed frame, 3774. The upper chain makes cells (38,14) and
   (38,15) solid `0x0D`. Crossing stops at (601.996,248.996), without chest
   flag, event or client check. This is not a strict upper-first-only control.

Collection is established by physical chest interaction and the client event,
not inferred from a trigger animation.

## Provenance and write boundary

The generated AP baseline is `8f2ee007bfd7bf76066ab216b15e827466064bb1`;
the inspected native source is `7d969fbce14fdc838d2c1ea01389717fb96c3189`.
The original 16 MiB USA ROM SHA-1 is
`274b102b6d940f46861a92b4e65f89a51815c12c`. Full production generation uses
seed 138 and normal HP/enemy-health options. After applying the generated
procedure patch, only startup room words at ROM offset `0x2D8CB8` and starting
positions at `0x2D8CD0` differ from the production ROM. No object, terrain,
source, essence, attack, health or reward bytes are manually changed. A fresh
100%/1HP production/fixture rebuild was byte-identical.

Each replay cold-boots with blank battery data. The only external RAM writes
are eight 32-bit initial configuration words from the actual client's
`_sync_enemy_copy_ability_runtime_config` at frame 1085, before movement.
There are zero gameplay RAM writes and state restores. Client messages are
captured locally without server submission. ROMs, saves, generated archives,
patches, full frame logs and build/replay scripts are not included here.

The compact record preserves the original acceptance SHA-256
`f3af360c536451bfb809ce6de95e04b2aa6ae638f7f9b04dfe41b288ec84a905`,
plus original manifest, build/replay/validator and static-metadata hashes.
Its public prose corrects the original report's misleading health-endpoint
wording; the original artifacts and their hashes are unchanged.

## Logic validation and limits

`test_rainbow_green_gate.py` covers actual-world source policies, precise
upstream access, source removal/source-after-gate and inventory-only negatives,
finite random grants, optional paint, RoomSanity, Area Keys, statue options,
gating and Spark classification. Three genuine filled generations at 1HP use
full accessibility, with gating off/on and an Area-Key/statue/RoomSanity-enabled
sample. Each must fill every location, beat the game and fulfill accessibility.
These validate logic integration, not additional native routes or runtime modes.

`test_bounded_bomb_traversal.py` checks every ability, dry/native-room boundaries
and inventory without equipment. `test_rainbow_green_evidence.py` guards retained
observations and attribution; it does not run an emulator. Other abilities,
sources, entries, copy-room supply, helper routes, exits, permanent state and
strict upper-only-first ordering remain unproved.
