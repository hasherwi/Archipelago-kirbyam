# Native 742: separate clean chest and return-loop Warp witnesses

Status: implementation design only, not a reviewed production graph. Reviewed against `5a01bb9` and exercised against kernel `32d1c44`. Files are isolated from the production checkout. Starting Stone and Burning remain unchanged.

## Decision

Use the existing finite graph with explicit **physical compartment plus action-history nodes**. Do not add a new global Bomb flag, a generic closing-gate capability, or negative `opened` predicates. Keep chest and Warp as separate AP targets. Reuse physical prefixes and metal actions through the existing `graph_parts` schema, which already merges nodes, routes and sources.

A successful clean witness is an alternative plan from independent access, not proof that a previously altered room resets. AP may union the existence of a clean chest plan and a return-loop Warp plan. Neither plan may splice the other's equipment, mutations or finite enemy consumption into itself.

## Evidence that the representation must preserve

- F5 bank: x20..21, y6..7. Attack direction is left to right into the upper tower. No provider is accepted by this design document.
- Actual clean entry: native 741 lower door record ROM offset `0x884BE2` (full GBA address `0x08884BE2`), trigger (1,17), enters 742 at tile (30,29). Source is 741 main Flamer `0x088BD8AC`, (200,224), table grant Burning.
- Actual upper return: 742 revealed door record offset `0x88554E`, trigger (25,12), enters 741 at (11,8). Upper Flamers are `0x088BDA38`, (136,80), and `0x088BDA5C`, (200,80). The 741 upper door offset `0x884A48`, trigger (3,2), enters 742 at (19,8).
- Warp: 742 door offset `0x885348`, trigger (27,2), enters native 705 at (4,39).
- Chest: native object `0x088BDD10`, (408,280), Sparerib, chest flag 17. AP location is `MINOR_CHEST_MOONLIGHT_MANSION_2_15_OBJECT_01`.
- Outer Bomb (19,12) changes both the lower route and the upper-to-chest route. In particular (24,8)/(25,8) become solid; row y9, x22..28 becomes spikes; side caps (22,13)/(28,13) become upward-only 0x0F. The center floor x23..27/y13..14 remains solid.
- Inner Bomb (26,12) is a different connected component. It changes (25,12) to door 0xFF and (25,11) to air. It does not clear the center floor. An outer-Bomb action cannot automatically receive inner-door credit.
- `FillLevelInfo` may retain a shared room instance if another Kirby occupies it. A door transition is not proof of a clean collision map or renewed enemy.

Door records above use ROM offsets unless explicitly labeled as full GBA addresses. Object identities use full GBA addresses; do not subtract or add the ROM base twice.

Native research update, 2026-11-08: the source prefix from actual 712 door arrival through 741 main Flamer acquisition to a first-ever 742 lower entry has been controller-tested successfully. It includes two 741 Bomb actions and preserves Burning into 742. The 742 climb, metal attack, chest and Warp were still being tested when this design was written. The native acceptance artifact, not this summary, must be the production evidence reference.

## Minimal graph partition

Use names with a room and phase, not one generic `742_post_metal` node.

Clean witness:

1. `741_clean_arrival`: actual 712→741 bottom arrival, equipped Normal.
2. `741_main_flamer`: reachable main-corridor capture position after the accepted 741 mechanisms.
3. `742_clean_lower`: actual lower-door entry while retaining the acquired ability; outer Bomb not used.
4. `742_clean_launch`: accepted launch position immediately before F5, still without using the outer Bomb.
5. `742_clean_tower`: after the exact accepted F5 action.
6. `742_clean_chest`: exact chest collection, through the still-open upper shaft.
7. `742_warp`: exact Warp door trigger.

Return-loop witness, only after its own physical sequence is accepted:

1. `742_lower_before_outer`.
2. `742_outer_changed`: after outer Bomb, with chest shaft closed.
3. `742_inner_door_revealed`: after the separate inner Bomb.
4. `741_upper_return_flamer`: actual upper-room arrival and capture position.
5. `742_return_launch_unknown`: upper 742 arrival. Outer mutation is known earlier in the plan; current room lifetime is unknown. Use only routes valid without reset.
6. `742_return_tower_unknown`: its own accepted F5 action.
7. `742_warp`: same final target is safe to share if it has no outgoing edges into either phase.

There is **no edge** from a return/outer-changed node to `742_clean_tower` or `742_clean_chest`. Do not add one merely because a transition clears `Position.opened`, because an enemy is encountered again, or because AP has reached the generic 742 room. A future accepted return-to-chest bypass can add its own directed edge and evidence without changing the kernel.

Outer and inner Bomb edges can be atomic ordinary routes with exact evidence and accepted equipment constraints. Do not label them `opens` and then treat all modifications as helpful. The initial implementation need not include the return-loop branch at all if only the clean route is accepted. Keep the full mutation separation in regression fixtures.

## AP arrival and room-check wiring

Current defects:

- Both `ROOM_2_14` and `ROOM_2_14_UPPER` target generic `ROOM_2_15` despite different native arrivals.
- `ROOM_2_15_UPPER_LEDGE_SPAWN` has no incoming edge.
- The chest is a null requirement in canonical `ROOM_2_15`.

Recommended compact fix uses existing room-loader features:

1. Keep canonical `REGION_MOONLIGHT_MANSION/ROOM_2_15` as the lower-entry compartment.
2. Add `logical_subregions.UPPER_RETURN` to that room, with no chest and only reviewed outgoing routes. Its generated name is `REGION_MOONLIGHT_MANSION/ROOM_2_15__LOGIC__UPPER_RETURN`.
3. Add `logical_exit_overrides` on `ROOM_2_14_UPPER`, mapping its existing `ROOM_2_15` destination to `UPPER_RETURN`. Leave the lower 741 exit mapped to canonical 742.
4. Retire the disconnected explicit `ROOM_2_15_UPPER_LEDGE_SPAWN` definition after updating its references. Do not leave a second accidental route to Warp. If external compatibility requires retaining it, keep it as a deliberately inert alias until a separately tested migration is possible; do not wire it back into canonical lower 742.
5. The existing loader creates one `ROOM_2_15__ROOM_CHECK` sink for room sanity, reachable from canonical and logical compartments. It has no outgoing edges, so merely visiting 742 does not leak lower-entry exits or the chest to the upper return.
6. Preserve chest location ID, flag and item identity. Attach its source-backed traversal target to its actual owning region. Do not copy the location into both arrivals.
7. Keep the lower 742→741 upper return route separate from the metal target. Its ordinary requirements do not establish Bomb timing or inner-component reachability; audit or constrain it with its own accepted mechanism witness as needed.

This uses no changes to `traversal.py`, `traversal_data.py`, or `data.py`. If the existing region loader cannot express a verified physical path, first consider another existing logical subregion rather than expanding the search state globally.

## Target and graph-part data

Suggested IDs (names may follow current production conventions):

- `metal_742_clean_source_prefix`: reusable part with the accepted 741 arrival, source identity, lower door and clean 742 launch approach.
- `metal_742_clean_burning_action`: reusable part with only the accepted local F5 action and clean post-metal node.
- `metal_742_clean_outcomes`: reusable clean tower→chest and tower→Warp routes, each independently evidenced.
- `metal_742_return_source_prefix` and `metal_742_return_burning_action`: separate optional parts if/when the return-loop experiment is accepted.

Only a complete accepted witness should receive `status: reviewed`. Do not place this design fixture into the production catalog. Parts cannot contain starts, access conditions or target bindings and cannot nest; final graph definitions provide these fields.

Bindings:

- `metal_742_sparerib`: kind metal; native room 742; `location` set to the exact existing chest key; required target only `742_clean_chest`. Its clean graph combines the three clean parts.
- `metal_742_lower_to_warp`: kind metal; native room 742; `exit` set to `REGION_MOONLIGHT_MANSION/ROOM_2_WARP`; required target only `742_warp`. It can reuse all clean parts, but it must not require chest collection.
- `metal_742_upper_return_to_warp`: owned by the logical upper-return AP region; same Warp exit; independent return witness only when accepted. It must never bind the chest.

A row must name exactly one exit or location. A graph with both chest and Warp in `required_targets` means **both** are required; it is not an OR and should not replace two target rows.

For the clean cross-room witness, prefer `access.region = REGION_MOONLIGHT_MANSION/ROOM_2_13` (native 712), start Normal at its verified 741 arrival, and include the 712 door/arrival in the evidence. This prevents a dirty 742→741 upper return from serving as the clean prefix. If a different access region is used, explicitly prove that its compartment is independently reachable through that same clean entry. Do not use the target chest, Warp, or a recursively gated 742 compartment as its own access predicate. Any area-connection/key requirements needed before 712 access belong to the existing AP route, not invented equipment.

Finite source placements use the real object identities. Do not make the two phases' sources interchangeable or mark Flamers renewable. Do not source equipment from an AP permission. Use `room_transition: true` on 741/742 crossings; omit reset/preserve flags until separately evidenced. The phase is encoded by the destination node and survives either flag behavior.

## Source-policy scope

The first Burning-only stage should use the existing target condition `requires_guaranteed_source = {source_key: FLAMER, ability: Burning}` and narrow each metal route to `allowed_abilities: [Burning]` with a per-provider acceptance reference.

- Vanilla or excluded Flamer: applicable when its actual native grant is Burning. Under future gating, the permission must still be owned at capture.
- Deterministic shuffle: applicable only when the finalized Flamer assignment is exactly Burning. A Hammer assignment is not licensed by a Burning attack witness.
- Live random: applicable for the globally guaranteed singleton Burning pool with zero no-ability weight. A mixed pool or positive no-ability weight is not a finite guarantee. The conditional predicate intentionally uses the full policy pool; it must not become applicable merely because the player's current permissions temporarily narrow that pool.
- No enemy retry loop or multi-enemy sampling guarantee is accepted. No generic ability carrier, Throw ammunition or source behind the metal may replace this prefix.

**Partial-condition warning:** `target_applies` skips a row when the condition is false and leaves its older AP rule untouched. This is a staging mechanism, not comprehensive safety. A conditionally gated chest can still be incorrectly open under unsupported policies. Before removing starting Stone/Burning, close that gap with complete accepted alternatives or explicit fail-closed unsupported-case handling, and test every supported policy. A generation pass only checks the graph it was given; it cannot detect an omitted physical gate.

## Exact implementation/test checklist

Production edits after native acceptance:

- `data/regions/rooms.json`: arrival split, chest/Warp target rows, source and graph parts, only exact accepted providers. Leave all unrelated rooms to their owners.
- `dev-docs/ordinary-metal-coverage.json`: cluster `742:20,6` must show chest and both directed AP Warp routes, with status per path rather than one blanket accepted flag.
- `dev-docs/ordinary-metal-role-review.json`: keep exit and chest co-target identity; distinguish clean and mutated layouts.
- `docs/native-room-wikirby-map.json`: update AP compartment correspondence without changing native/wiki identity.
- Native acceptance artifact: source acquisition, movement/carry, mutation chronology, local metal action, exact chest flag/door result and failure limits. No full ROM or map art.
- Tests under `worlds/kirbyam/test/`: add state-isolation fixture and real compiled-data/region tests. Update snapshots/counts only after inspecting the actual delta.

Required tests:

1. Exact 741 lower and upper incoming exits land in different logical compartments.
2. Both arrivals reach the same single room-sanity check; the sink cannot grant lower entry, chest, upper entry or Warp.
3. Clean accepted prefix can reach chest and Warp independently. Test each target with the other's final edge removed.
4. Starting only from upper return or outer-changed state cannot reach clean chest, even with every permission and every metal provider in inventory.
5. Inner-door credit is not granted by outer Bomb alone. Reaching the inner Bomb must be a separate accepted edge.
6. Unknown, preserved and reset transition flags cannot invent an edge from mutated/unknown phase to clean phase.
7. Permission without the physical source fails. Source behind the gate fails. Consumed Flamer cannot be reacquired without reset proof. No source is both swallowed and spent as projectile ammunition.
8. Policy matrix: vanilla, fixed Burning, fixed non-Burning, live singleton Burning/no failure, mixed pool, positive failure weight, 100% failure. Apply the target condition and evaluate source acquisition separately.
9. Only the exact accepted metal provider passes. Add alternatives only with their own room-specific evidence.
10. The clean and return results may be unioned as independent plans, but no individual graph path reverts phase or double-spends a finite source.
11. Native target test confirms chest flag 17 and the exact Warp room/door separately. Merely reaching the tower or visually touching a chest is not full collection evidence.
12. Full-accessibility generation plus no-starting-Stone/Burning experimental fixtures must remain a final audit step, not evidence that missing physical gates are absent. Do not alter starting inventory in this increment.

## Executed synthetic regression

`check_742_design_semantics.py` runs against the actual traversal kernel with hypothetical movement edges. At `32d1c44` it passed **35 assertions**, with 45 clean-start states and 10 upper-return-start states. It exercises phase isolation, finite identity, future Burning permission, source-before-gate, policy conditions, exact provider restriction, and AP union of independent plans.

This test does **not** accept the hypothetical edges. It does not run the emulator, validate capture coordinates, execute Bomb actions, test attacks, collect the chest or enter Warp. It temporarily changes the imported gateable-ability set inside its own process solely to test eventual Burning permission behavior, then restores it. There are no production writes.
