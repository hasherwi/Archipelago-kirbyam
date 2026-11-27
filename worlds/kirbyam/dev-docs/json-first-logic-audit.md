# JSON-first logic audit

Baseline: `03195ea8ed6179994e908ad597c510649f052f3a`. Step 1 is a source audit; this branch does not change generation, runtime behavior, or the playthrough record.

## 1. Where logic lives today

| Layer | Data and code | Audit finding |
| --- | --- | --- |
| World topology and check placement | [rooms.json](../data/regions/rooms.json), [areas.json](../data/regions/areas.json), [locations.json](../data/locations.json), [locations_goal_games.json](../data/locations_goal_games.json), [data.py](../data.py), [regions.py](../regions.py) | JSON defines rooms, exits, check/event ownership and compact requirements. Python adds synthetic Main links, option filters and event/goal wiring. Audit canonical ownership, directionality and synthetic edges in steps 2–3. |
| Compact predicates | [rules.py](../rules.py) | JSON `all`/`any`/`item` expressions work, but the generic rope, peg, fuse, block and Mini predicates currently return true via the pending-gate helper. Normal movement and lever/item rules are separate. A compact obstacle entry alone is **not** evidence that the obstacle is enforced. Audit where stricter rules overlay it before deciding any specific check is wrong. Missing compact attachments are currently logged and skipped; optional targets and unexpectedly missing targets should be distinguishable. |
| Verified routes and ability sources | [rooms.json](../data/regions/rooms.json), [ability_source_inventory.json](../data/ability_source_inventory.json), [traversal_data.py](../traversal_data.py), [traversal.py](../traversal.py), [traversal_rules.py](../traversal_rules.py) | 62 authored traversal targets in nine kinds at this baseline. JSON already supports physical source placements, reusable graphs, and explicitly Advanced variants. Python resolves seed-specific grants and evaluates the route state. Coverage is not universal, and some target conditions and runtime fixups are target-specific code. |
| Goal and item semantics | [rules.py](../rules.py), [__init__.py](../__init__.py), [full_completion.json](../data/full_completion.json) | The selected goal is a locked event. Python owns goal requirements (including 100% aggregation), starting-mirror/key protections, and some progression classification. Keep generic option/state evaluation in code; migrate game-specific conditions only when the old and new predicates agree. Acquiring an unlock is a different fact from finding and equipping the ability. |
| Generation and final acceptance | [__init__.py](../__init__.py), [check_accessibility.py](../check_accessibility.py), [traversal_rules.py](../traversal_rules.py) | Pre-generation checks data and source feasibility; ordinary AP fill respects installed predicates. After final placements, the Kirby guard starts fresh and sweeps *reachable* progression, including deliveries from other worlds, then rejects unfilled or unreachable enabled checks even on Minimal. The all-items state only diagnoses failures. This catches modeled self-locks, not routes that the installed model wrongly marks possible. |

### Direction for Step 1

Keep one evaluator and one authoritative declaration per route. JSON should own the location/edge/event target, route alternatives, Standard or Advanced classification, required items and game capabilities, source/charge costs, and evidence references. Python should validate and compile that data, perform state-dependent reachability and source resolution, and enforce fill/final checks. Do not encode executable code in JSON. Do not delete the specialized witnesses until comparisons prove the replacements equivalent.

Explicitly distinguish **unrestricted**, **mode/profile excluded**, and **unreviewed**. Do not silently translate an unknown obstacle into Normal access or declare a route physically impossible because evidence is absent. First inventory every pending-token site and its installed overlay, then migrate one evidenced target family at a time. Test positive and negative cases, including missing canonical attachment, unknown requirement, all/any precedence, self-locked unlocks, remote circular deliveries, option-disabled checks, tracker reconstruction, and classified Standard/Advanced borders. Compare fixed-seed placements, reachability, and expected rejects before changing acceptance behavior.

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

**Phone:** model ownership separately from usable charges at the obstacle. Start/reload behavior and charge pickups are runtime facts, not ordinary ability unlocks. The exact current [Phone predicate](../phone_traversal.py) has a qualified two-call witness starting with three charges; other profiles use an ownership-only fallback, not a demonstrated helper route or a general charge model. Do not credit helpers with non-Normal attacks in ordinary Phone checks.

**Goal Games can supply a charge, but completing one does not guarantee it.** The [native Goal Game battery-pickup hook](../kirby_ap_payload/battery_hook.s) calls the same pickup operation as field batteries; the [pickup logic](../kirby_ap_payload/battery_runtime_logic.h) adds one below three. The [Goal Game acceptance record](goal-game-current-acceptance.md) also covers completion with no prizes. Therefore distinguish access to the minigame, completing it, and a verified outcome that awards a battery. Count it for Standard only if the required prize pickup and onwards route are demonstrated without already needing those charges. Prefer guaranteed start, reachable fixed pickups, or a verified refill route over assuming a random AP battery: [items.json](../data/items.json) classifies Cell Phone Battery as filler.

## Verification boundary

Static source and JSON inventory review only. No generator or emulator results are claimed for this branch. The focused test attempt in the review checkout could not start because pytest is not installed there. Use the project’s test environment for the first behavior-preserving migration; include both a known accepted seed and an expected rejected seed.
