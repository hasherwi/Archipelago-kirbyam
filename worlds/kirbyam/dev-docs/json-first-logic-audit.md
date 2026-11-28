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

- [goal_logic.json](../data/goal_logic.json) now declares all five current goal modes, stable location keys, required predicates, and the Dark Meta Knight prerequisite event. The checker resolves shards and boss records from their existing catalogs, reads the [completion manifest](../data/full_completion.json) for completion obligations, and rejects unknown goal facts during loading. The client uses the same mode-to-location catalog, plus the separately declared legacy reporting-only hidden-boss mode. The native/acknowledgement checks that produce a runtime signal retain their existing semantics.
- [traversal_capabilities.json](../data/traversal_capabilities.json) now owns the 60 ability-provider declarations, including 49 scoped native-room/attack-medium pairs and the abilities consumed by a successful use. This migration copies the reviewed behavior exactly; it does not add a global bypass, infer anything from a missing matrix cell, or promote untested sources.
- [Lever wall logic](../data/lever_wall_logic.json) maps the four tokens used by eight directed room/subroom entrances to their existing item catalog keys. The physical lever check remains distinct from receiving the wall-unlock item. The Carrot catalog key still contains `5_12` for compatibility; its current label and wall are **5-05**. Neither the token migration nor the audit changes wall or Area Key behavior.
- [Mirror access](../data/mirror_access.json) declares the directed Starting Mirror, unlock and tutorial check, all Area Key/item bindings, the early-check fallback, excluded return types and the two forced wind-lane gates. The evaluator derives the remaining directional key edges from the compiled graph. The item catalog remains authoritative for player-facing labels and IDs.
- [Compact token vocabulary](../data/compact_room_logic.json) distinguishes Normal movement, the legacy alias-to-provider mapping, and unreviewed compatibility tokens. Those legacy tokens do not grant equipped abilities or turn uncertain native routes into proof. Existing source-backed overlays, Boolean composition, and unknown-token rejection stay intact.
- [Item pool policy](../data/item_pool_policy.json) owns the ordered filler weights, option-driven filler/trap and static non-filler exclusions, legacy trap introductions, and explicit vanilla boss-to-shard bindings. A Useful battery is still a weighted consumable, not a trap or ordinary progression item. Health gating independently checks maximum HP for healing filler and minimum HP for Health Down traps. Item-driven pool calculations for vitality counts, guaranteed Area Key and map starts, and active collection rewards remain evaluator logic.
- [Phone logic](../data/phone_logic.json) now references the canonical Phone, battery, hub connection, and area-key item keys instead of embedding display labels. These bindings do not change the native charge-free hub return or the repeatable Goal Game refill logic.
- The seven conditional ability unlocks reference ordered progression routes in [Abilities](../data/abilities.json). Author each named predicate beside its owner in [Rooms](../data/regions/rooms.json) under `permission_progression_routes`; owner placement does not add a reachability requirement. Generation and Tracker item classification use the same evaluator. New seeds do not automatically grant any copy ability. The current gate catalog comes from `safe_to_gate` in Abilities, and explicit start inventory remains available. A rule can promote an unlock required by a source-backed route; it does not grant equipment or declare a natural source by itself.
- [Traversal source scopes](../data/traversal_source_scopes.json) preserve the exact target identity and allowed source-policy combinations for narrow witnesses. Validation rejects a witness transplant to a different room, direction, or chest. It does not broaden availability.
- Inventory the **compiled** room data, not just the top-level source objects: 163 compact exits and 11 compact locations mention a pending equipment/capability token. Direct target matching accounts for 24 of those exits and two of those locations. The remaining 139 exits and nine locations have no direct match to a room-traversal JSON target. These are **review candidates**, not proven logic failures: indirect gates, separate installers, same-room exceptions, and genuine Normal routes may still cover them.
- Most candidate occurrences concern ordinary/floating blocks (134 and 20 respectively across all 174 compact sites). Prioritize the explicitly ability-sensitive predicates first: confirmed metal, Mini, pegs, fuses, ropes, timed switches, and Wheel. Identify the real evidence and the actual installed predicate for each before changing any solver result.

### Priority obstacle audit

The [door and check inventory](priority-obstacle-rules.md) traces **17 explicit compact sites** to **17 exact same-family overlays** and lists **38 catalog targets** (21 directed entrances and 17 checks). There is no unmatched explicit metal, peg, fuse, or rope token in this batch. This is not a census of native obstacles: generic block names can hide other cases, and a room visit or chest downstream of an entrance need not have its own obstacle predicate.

- **Pegs:** `install_peg_rules` adds the solver predicate at each catalog target, selecting local/carry witness graphs and requiring actual source-region access. The six shared stake entrance names in `rules.py` preserve the original compact expression; their permissive helper is not a second independent gate. For Cabbage 3-15, the east peg gates the **lower entrance**; the 3-14 west peg independently gates the Sapphire Spray Paint chest.
- **Ropes, metal, and fuses:** `install_extra_traversal_rules` adds reviewed witness graphs to the existing directed edge or the exact location. A missing optional check does not create a gate elsewhere. For Peppermint, the rope target is **7-20 → 7-21**, not a new rule on the downstream Goal Room's chest or minigame. For Candy 9-12, the linked-fuse fallback is a profile-specific graph on the **chest's block-family target**, not a second universal fuse gate. Advanced-only graphs remain opt-in.
- **Next migration:** keep the reviewed graphs authoritative; do not turn the redundant compact aliases into a second family-wide ability grant or gate. Before removing any alias, compare generated reachability and confirm its full `all`/`any` expression, optional settings, and reverse paths. The broader unmatched generic-block and floating-block sites stay unresolved until traced to native behavior or a proven bypass.

### Generic and floating block labels

The [generic block inventory](generic-block-rules.md) identifies **154 distinct surfaces**: six with exact catalog overlays (five directed exits and Mustard Map), five exits with declared Normal alternatives, and **143 without either** (134 exits, nine checks). This is a per-surface count, not a count of individual token occurrences. Exact overlays include metal walls, a fuse and a switch, so the generic token is not a trustworthy identifier for one ability class.

The [Normal-only playthrough evidence](https://github.com/hasherwi/Archipelago-kirbyam/issues/1059) resolves the physical capability question for the nine no-direct-overlay checks in the observed build:

- **Normal worked:** Rainbow Goal Games 1–3 (3960700–3960702), Cabbage Goal Game (3960705), Mustard Goal Game 2 (3960707), Olive Goal Game 2 (3960709), and Peppermint Goal Game 1 (3960710). These are exact native completions in the legacy test seed, not new AP Goal Game receipts. Ordinary star blocks, Normal attacks and existing bypasses vary by route; do not substitute one global block predicate.
- **Normal worked with an AP receipt:** Cabbage Map (3960200), separate from that room's Goal Game. Normal puff opened the upper branch after the correct approach in the Area Keys-off test.
- **Not a local block requirement:** Moonlight Goal Game 2 (3960704) was not accessible with Normal alone in the tested topology. Its upstream eastern approaches are gated at Rainbow 1-41 (metal) and Rainbow 1-42 (rope). Preserve those directed gates; the check's local floating-block token is not proof of an additional Copy Ability restriction.

The five declared Normal entrance alternatives are Boolean facts, not new physical proofs. The 134 no-direct-overlay entrances still require matching the exact side and direction to native evidence before changing solver behavior. An observed room visit does not prove every door leading into it. No predicates changed in this audit.

### Step 1 acceptance boundary

- The production compiler reads reviewed room/topology, capability providers, source requirements, mirror/key exceptions, progression promotions and goals from the data catalogs. The same evaluated rules are used during fill, final all-check validation, and Tracker reconstruction.
- The [source scopes and profiles](../data/traversal_source_scopes.json) preserve the pinned Yellow option/assignment scope, the Candy linked-fuse alternatives, Room 4-16 timer selection, and the post-clear Master stand contract. Python still applies native protocol/ROM guards and validates the exact bounds of specialized historical evidence. These checks must not become authorable arbitrary executable expressions.
- Final seed validation still uses a fresh progression sweep over actual placed items and events. An all-items state is only diagnostic. This guards against item self-locks and multiworld circular deliveries on modeled routes; it cannot certify unmodeled topology. Treat the unreviewed compact tokens as compatibility behavior, not evidence that those routes are open.
- The remaining physical entrance, room/check ownership, and source-acquisition audits belong to Steps 2–5. Do not treat Step 1 as a claim that every native route or the global three-transition limit has already been demonstrated or implemented.

### Authoring conventions

- Prefer a named game concept to a numeric ID or generic flag. For example, `goal_location` references a named location key; `all_of` makes it clear every listed condition is required. Keep identifiers stable and resolve their player-facing labels from the canonical catalogs.
- Keep a route's facts together: `allowed_abilities`, `native_room`, `attack_medium`, and `consumed_abilities` live in the same capability row, rather than in parallel dictionaries. Leave room and water off a genuinely reusable capability. Use a short `note` to explain a non-obvious limit, not to encode a second rule.
- Use explicit alternatives and units. A Phone check names its directed entrance with `from_region` and `to_region`, and follows `check_route` to the check’s declared owner. It identifies the repeatable refill source independently of the item catalog. Unknown or misspelled keys that affect logic should fail validation rather than silently falling back to open access.

## 2. Room, subroom and region data

The [compiled topology census](step-2-room-topology.md) now distinguishes physical candidates, same-room compartments, summary/sink links, and native Phone return evidence. It removes redundant exits from Room Sanity sinks and keeps area summaries terminal. Initial access and the shard gate are anchored to Central Circle without installing a Phone return route.

Audit native room identity versus AP region and logical subroom, entrance/exit ports and direction, one-way mirrors, and automatic area-summary connections. Same-native-room subroom edges are not room transitions. Retain real one-way traversal; do not create reverse routes based on naming.

## 3. Check, goal and event placement

The [compiled placement audit](step-3-check-placement.md) verifies canonical ownership and distinguishes the 395 addressable native checks, six goal definitions and 21 addressless events. Big Switch annotations now inherit the physical press rule; shared native room visits use terminal sinks across all verified compartments, including the 100% goal when RoomSanity is off. The audit preserves exact chest and Goal Game sides and flags other shared-room actions for separate traversal evidence rather than treating a room match as physical reachability.

## 4. Accessibility from playthroughs

**4A. Normal only:** reconcile every proven Normal route and retain “No, Unproven” separately from a structural impossibility. A Normal route cannot depend on called helpers or a copied ability.

**4B. Remaining checks:** record each independently supported route, the items/capabilities it actually needs, and Standard vs Advanced. Use conjunction for jointly necessary requirements and disjunction for alternatives. A successful switch or gate crossing is not by itself proof of a later chest or minigame. Phone-only covers switch timing and Heave-Ho; helper Kirby copy abilities belong to separate Advanced work. This stage establishes what can do the check; it does not prove where the required ability was acquired.

## 5. Acquisition and Phone charge

**Standard:** after ability unlock where applicable, show an independently reachable and eligible source and a directed route that carries the ability to the obstacle in **at most three room transitions**. Count physical room crossings, not areas, AP graph nodes, or the route after dropping the ability. Validate the source itself is not behind the gate that needs it. Source usability depends on the seed, options, and the segment (for example a ladder or water constraint). The current graph model has explicitly authored Advanced variants; that is not a general three-transition guarantee.

**Advanced:** waive the three-transition limit, not physical continuity. A source may be anywhere in the game provided it is actually obtainable at that point and the ability survives a viable route to the target. A global source-name match is not enough, and random rerolls at a source must not be represented as a guaranteed single draw. Master after Dark Mind is a reachable event source, not a gated unlock.

**Phone:** model ownership separately from charges. For summoning helpers, the generator requires access to one repeatable Goal Game before a Phone-dependent check; it does not have to be available at spawn. A Goal Game behind the same Phone gate cannot supply the prerequisite. The separate Phone return to Central Circle requires no charge; verify its room/state restrictions and one-way arrival during the traversal review before installing any such edges. The [Phone JSON declaration](../data/phone_logic.json) currently binds the Chalk Spray route. Existing witness restrictions remain in place. Starting mirrors and their options are unchanged.

The [native Goal Game battery-pickup hook](../kirby_ap_payload/battery_hook.s) calls the same pickup operation as field batteries. The [Goal Game acceptance record](goal-game-current-acceptance.md) also covers completion with no prizes; the placement rule relies on repeatability, not a guaranteed battery on every run. Individual batteries are Useful, not progression. They still draw from the existing weighted consumable slots, but are Useful at creation, including in starting inventory. Excluded checks cannot receive them.

## Verification boundary

The topology and rule inventory is a static audit. Phone regression tests cover reachable and unreachable refill routes, a refill route behind the Phone gate, and the non-progression battery classification. No new emulator result is claimed on this branch.

### Item catalog boundary

`data/items.json` defines every AP item with its own explicit ID, display
label, classification, and tags. The eight Mirror Shards retain IDs
3860002–3860009; their IDs no longer depend on source order or the remaining
unclaimed integers. The loader rejects malformed records and duplicate IDs
or labels rather than silently omitting or relabeling them.

This is the identity catalog, not a complete pool or native behavior
specification. Option-specific pool assembly and the weighted filler policy
still live in the generator, and runtime item effects live in the client and
ROM code. In particular, the Cell Phone Battery is Useful for AP placement
but remains selectable by the weighted filler policy; it is not a
progression requirement.

### Room-owned conditional routes

Candy 9-12's linked-fuse Normal and exact Fire alternative, Mustard Room 4-16's
timer-backed route, and Carrot Yellow's assignment-pinned Cupid route live on
their exact targets in `data/regions/rooms.json`. `conditional_routes` keeps a
profile's trigger and conditional witness alternatives together. Conditions
are validated against the target and share one evaluator. Existing native
patch guards still own the fixed Candy marker and the Room 4-16 timer token;
Tracker still reconstructs from persisted settings rather than silently
deciding an older seed should use new patch behavior. Carrot still checks the
complete source assignment signature when validating the installed rule.
