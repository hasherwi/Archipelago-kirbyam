# JSON-first logic audit

Baseline: `03195ea8ed6179994e908ad597c510649f052f3a`. The source audit below describes baseline behavior. The first follow-on batches cover Phone charge logic and generation-side goal requirements. Neither changes native gameplay or the playthrough record.

## 1. Where logic lives today

| Layer | Data and code | Audit finding |
| --- | --- | --- |
| World topology and check placement | [rooms.json](../data/regions/rooms.json), [areas.json](../data/regions/areas.json), [locations.json](../data/locations.json), [locations_goal_games.json](../data/locations_goal_games.json), [data.py](../data.py), [regions.py](../regions.py) | JSON defines rooms, exits, check/event ownership and compact requirements. Python adds synthetic Main links, option filters and event/goal wiring. Audit canonical ownership, directionality and synthetic edges in steps 2–3. |
| Compact predicates | [rules.py](../rules.py) | JSON `all`/`any`/`item` expressions work, but the generic rope, peg, fuse, block and Mini predicates currently return true via the pending-gate helper. Normal movement and lever/item rules are separate. A compact obstacle entry alone is **not** evidence that the obstacle is enforced. Audit where stricter rules overlay it before deciding any specific check is wrong. Missing compact attachments are currently logged and skipped; optional targets and unexpectedly missing targets should be distinguishable. |
| Verified routes and ability sources | [rooms.json](../data/regions/rooms.json), [ability_source_inventory.json](../data/ability_source_inventory.json), [traversal_data.py](../traversal_data.py), [traversal.py](../traversal.py), [traversal_rules.py](../traversal_rules.py) | 62 top-level authored traversal targets in nine kinds; 66 after logical subregion expansion. JSON already supports physical source placements, reusable graphs, and explicitly Advanced variants. Python resolves seed-specific grants and evaluates the route state. Coverage is not universal, and some target conditions and runtime fixups are target-specific code. |
| Goal and item semantics | [rules.py](../rules.py), [__init__.py](../__init__.py), [full_completion.json](../data/full_completion.json) | The selected goal is a locked event. Python owns goal requirements (including 100% aggregation), starting-mirror/key protections, and some progression classification. Keep generic option/state evaluation in code; migrate game-specific conditions only when the old and new predicates agree. Acquiring an unlock is a different fact from finding and equipping the ability. |
| Generation and final acceptance | [__init__.py](../__init__.py), [check_accessibility.py](../check_accessibility.py), [traversal_rules.py](../traversal_rules.py) | Pre-generation checks data and source feasibility; ordinary AP fill respects installed predicates. After final placements, the Kirby guard starts fresh and sweeps *reachable* progression, including deliveries from other worlds, then rejects unfilled or unreachable enabled checks even on Minimal. The all-items state only diagnoses failures. This catches modeled self-locks, not routes that the installed model wrongly marks possible. |

### Direction for Step 1

Keep one evaluator and one authoritative declaration per route. JSON should own the location/edge/event target, route alternatives, Standard or Advanced classification, required items and game capabilities, source/charge costs, and evidence references. Python should validate and compile that data, perform state-dependent reachability and source resolution, and enforce fill/final checks. Do not encode executable code in JSON. Do not delete the specialized witnesses until comparisons prove the replacements equivalent.

Explicitly distinguish **unrestricted**, **mode/profile excluded**, and **unreviewed**. Do not silently translate an unknown obstacle into Normal access or declare a route physically impossible because evidence is absent. First inventory every pending-token site and its installed overlay, then migrate one evidenced target family at a time. Test positive and negative cases, including missing canonical attachment, unknown requirement, all/any precedence, self-locked unlocks, remote circular deliveries, option-disabled checks, tracker reconstruction, and classified Standard/Advanced borders. Compare fixed-seed placements, reachability, and expected rejects before changing acceptance behavior.

### Step 1 follow-on: goals and compact obstacle inventory

- [goal_logic.json](../data/goal_logic.json) now declares all five current goal modes, stable location keys, required predicates, and the Dark Meta Knight prerequisite event. The checker resolves shards and boss records from their existing catalogs, reads the [completion manifest](../data/full_completion.json) for completion obligations, and rejects unknown goal facts during loading. The legacy hidden-boss mode remains outside the active goal set. Client-side goal protocol and its current native/runtime checks are not part of this migration.
- [traversal_capabilities.json](../data/traversal_capabilities.json) now owns the 60 ability-provider declarations, including 49 scoped native-room/attack-medium pairs and the abilities consumed by a successful use. This migration copies the reviewed behavior exactly; it does not add a global bypass, infer anything from a missing matrix cell, or promote untested sources.
- [Lever wall logic](../data/lever_wall_logic.json) maps the four tokens used by eight directed room/subroom entrances to their existing item catalog keys. The physical lever check remains distinct from receiving the wall-unlock item. The Carrot catalog key still contains `5_12` for compatibility; its current label and wall are **5-05**. Neither the token migration nor the audit changes wall or Area Key behavior.
- Inventory the **compiled** room data, not just the top-level source objects: 163 compact exits and 11 compact locations mention a pending equipment/capability token. Direct target matching accounts for 24 of those exits and two of those locations. The remaining 139 exits and nine locations have no direct match to a room-traversal JSON target. These are **review candidates**, not proven logic failures: indirect gates, separate installers, same-room exceptions, and genuine Normal routes may still cover them.
- Most candidate occurrences concern ordinary/floating blocks (134 and 20 respectively across all 174 compact sites). Prioritize the explicitly ability-sensitive predicates first: confirmed metal, Mini, pegs, fuses, ropes, timed switches, and Wheel. Identify the real evidence and the actual installed predicate for each before changing any solver result.

### Priority obstacle audit

The [door and check inventory](priority-obstacle-rules.md) traces **17 explicit compact sites** to **17 exact same-family overlays** and lists **38 catalog targets** (21 directed entrances and 17 checks). There is no unmatched explicit metal, peg, fuse, or rope token in this batch. This is not a census of native obstacles: generic block names can hide other cases, and a room visit or chest downstream of an entrance need not have its own obstacle predicate.

- **Pegs:** `install_peg_rules` adds the solver predicate at each catalog target, selecting local/carry witness graphs and requiring actual source-region access. The six shared stake entrance names in `rules.py` preserve the original compact expression; their permissive helper is not a second independent gate. For Cabbage 3-15, the east peg gates the **lower entrance**; the 3-14 west peg independently gates the Sapphire Spray Paint chest.
- **Ropes, metal, and fuses:** `install_extra_traversal_rules` adds reviewed witness graphs to the existing directed edge or the exact location. A missing optional check does not create a gate elsewhere. For Peppermint, the rope target is **7-20 → 7-21**, not a new rule on the downstream Goal Room's chest or minigame. For Candy 9-12, the linked-fuse fallback is a profile-specific graph on the **chest's block-family target**, not a second universal fuse gate. Advanced-only graphs remain opt-in.
- **Next migration:** keep the reviewed graphs authoritative; do not turn the redundant compact aliases into a second family-wide ability grant or gate. Before removing any alias, compare generated reachability and confirm its full `all`/`any` expression, optional settings, and reverse paths. The broader unmatched generic-block and floating-block sites stay unresolved until traced to native behavior or a proven bypass.

### Authoring conventions

- Prefer a named game concept to a numeric ID or generic flag. For example, `goal_location` references a named location key; `all_of` makes it clear every listed condition is required. Keep identifiers stable and resolve their player-facing labels from the canonical catalogs.
- Keep a route's facts together: `allowed_abilities`, `native_room`, `attack_medium`, and `consumed_abilities` live in the same capability row, rather than in parallel dictionaries. Leave room and water off a genuinely reusable capability. Use a short `note` to explain a non-obvious limit, not to encode a second rule.
- Use explicit alternatives and units. A Phone check names its directed entrance with `from_region` and `to_region`; it identifies the repeatable refill source separately from the reward classification of a battery item. Unknown or misspelled keys that affect logic should fail validation rather than silently falling back to open access.

## 2. Room, subroom and region data

Audit native room identity versus AP region and logical subroom, entrance/exit ports and direction, one-way mirrors, and automatic area-summary connections. Same-native-room subroom edges are not room transitions. Retain real one-way traversal; do not create reverse routes based on naming.

## 3. Check, goal and event placement

Verify one canonical owner and exact physical action/side of each obstacle for every check, goal and event. Separate AP delivery from a native action or a logical AP event. Confirm optional locations only disappear when declared out of scope, and verify the final goal/event sequence independently of check counts.

## 4. Accessibility from playthroughs

**4A. Normal only:** reconcile every proven Normal route and retain “No, Unproven” separately from a structural impossibility. A Normal route cannot depend on called helpers or a copied ability.

**4B. Remaining checks:** record each independently supported route, the items/capabilities it actually needs, and Standard vs Advanced. Use conjunction for jointly necessary requirements and disjunction for alternatives. A successful switch or gate crossing is not by itself proof of a later chest or minigame. Phone-only covers switch timing and Heave-Ho; helper Kirby copy abilities belong to separate Advanced work. This stage establishes what can do the check; it does not prove where the required ability was acquired.

## 5. Acquisition and Phone charge

**Standard:** after ability unlock where applicable, show an independently reachable and eligible source and a directed route that carries the ability to the obstacle in **at most three room transitions**. Count physical room crossings, not areas, AP graph nodes, or the route after dropping the ability. Validate the source itself is not behind the gate that needs it. Source usability depends on the seed, options, and the segment (for example a ladder or water constraint). The current graph model has explicitly authored Advanced variants; that is not a general three-transition guarantee.

**Advanced:** waive the three-transition limit, not physical continuity. A source may be anywhere in the game provided it is actually obtainable at that point and the ability survives a viable route to the target. A global source-name match is not enough, and random rerolls at a source must not be represented as a guaranteed single draw. Master after Dark Mind is a reachable event source, not a gated unlock.

**Phone:** model ownership separately from charges. The generator requires access to one repeatable Goal Game before a Phone-dependent check; it does not have to be available at spawn. A Goal Game behind the same Phone gate cannot supply the prerequisite. The [Phone JSON declaration](../data/phone_logic.json) currently binds the Chalk Spray route. Existing witness restrictions remain in place. Starting mirrors and their options are unchanged.

The [native Goal Game battery-pickup hook](../kirby_ap_payload/battery_hook.s) calls the same pickup operation as field batteries. The [Goal Game acceptance record](goal-game-current-acceptance.md) also covers completion with no prizes; the placement rule relies on repeatability, not a guaranteed battery on every run. Individual batteries are Useful, not progression. They use their existing weighted slots during fill, then receive the Useful reward classification without reshuffling placements.

## Verification boundary

The topology and rule inventory is a static audit. Phone regression tests cover reachable and unreachable refill routes, a refill route behind the Phone gate, and the non-progression battery classification. No new emulator result is claimed on this branch.
