# Ranged completion status

PR #1052 remains **partial**. The bounded routes have real source-aware logic,
but four targets skip their extra rule outside reviewed guaranteed source
assignments. Relevant physical outcomes also remain unadjudicated. Neither a
large test count nor a machine inventory certifies every move against every
surface, current-generator acceptance, or native gameplay completion.

## Reproduce the current status

From the repository root, with the normal test dependencies installed:

```sh
AP_TEST_WORLDS=kirbyam python -c 'import unittest, test, runpy; runpy.run_module("worlds.kirbyam.tools.build_ranged_completion_status", run_name="__main__")' --check
AP_TEST_WORLDS=kirbyam python -m unittest discover -s worlds/kirbyam/tools/tests -p test_ranged_completion_status.py -v
AP_TEST_WORLDS=kirbyam python -m pytest worlds/kirbyam/tools/tests/test_ranged_completion_status.py -q
```

The first command prints a short report. Add `--output ranged-status.json` to
write machine-readable details instead. The test bootstrap prevents dependency
updates and settings autosave. No ROM, emulator, private path, network call or
generated export is required. `--check` checks declaration consistency, **not
completion**: a successful check still reports partial coverage.

The two test commands run the same runner-agnostic `unittest.TestCase` tests,
using `test.param.classvar_matrix`: 120 public-profile installer probes,
270 synthetic installer probes and nine contract checks (399 tests total).
These are case counts, not 399 distinct physical targets or native replays.

The report derives exact owners, target source conditions, witness names and
policy applicability from production-normalized data and the production policy
resolver. It fingerprints the data, normalizer, policy builder/runtime patch,
traversal compiler/installer, fixed-source constants, legacy rules, inventory
and declaration inputs.
The companion tests exercise the actual installer with its real compiled graphs
on isolated enabled targets. With gating enabled, no items and no independent
access, an applied rule constrains an initially true base rule. A skipped rule
preserves it. An initially false base rule must never become true. These probes
do not generate seeds or establish a physical softlock.

Public profiles use the full 25-ability pool: native mode, one deterministic
shuffled policy built with seed 427, live mode at Normal weights 0/99/100, and a
live example with passive enemies excluded. They sample supported option shapes,
not every seed, option combination or accepted generation. Internal singleton,
mixed Beam/Spark and failure-bearing Beam diagnostics are explicitly separate.
There is **no public custom-whitelist option**.

## Known source-policy gaps

| Target | Exact bounded surface | Fallback scope |
| --- | --- | --- |
| `bomb_517_chocolate` | Cabbage Chocolate Paint | Outside its ten reviewed Doo assignments |
| `bomb_733_yellow` | Carrot Yellow Paint | Outside guaranteed Sparky→UFO |
| `switch_533_room16` | Mustard Room15→16 | Outside Foley→Bomb/UFO/Crash/Magic |
| `switch_310_mustard_map` | Mustard map only | Outside Twister→UFO/Crash/Cupid/Cutter |

Native Twister→Tornado and Sparky→Spark already leave the 310 and 733 rules
unapplied. The three full live-pool weight profiles and the passive-excluded
live profile skip all four. The older base rule remaining permissive is a
coverage gap, not evidence that every such
room is physically impossible. Do not replace this gap with blanket fail-closed
restrictions or assume helper abilities provide a solution.

Two raw `can_hit_far_switch` strings remain, at 310 and 533. They acquire real
constraints under the supported source assignments above. Main resolved 209
through directed compartment/Normal/Snow-loop logic; it is not a third missing
far-switch implementation. Preserve exact entry and historical native limits.

110 is one unconditional target with three OR witnesses. Its Normal route
consumes the original Knight as ordinary mouth payload and uses a separate
underwater spray; it is source-policy-independent, not physically source-free.
Finite Spark/Sword branches keep their own raw source conditions. Exact108
LOWER_MID access remains mandatory; native503 is not an alternate entry.
See `rainbow-normal110-source-witness.md` for the accepted native evidence and
its native/policy/health qualifications.

138 is one unconditional Green Paint target with two OR witnesses: the exact
human Normal lower-slide suffix and the preserved finite Sparky branch. Only
the Spark graph retains its guaranteed-source predicate. Both require independent
room 532 UPPER_LEFT access and a fresh room 138 door entry; base room 532, UPPER_RIGHT or owner-only
access is insufficient. No Copy item or local Area Key is needed for Normal.
The accepted natural 50% / 1 HP, shuffled 500% / 1 HP and live 100% / actual 6 HP profiles each
have a cold repeat. Intermediate health/source-policy equivalence is source-backed,
not execution at every setting. Helpers settle in room 101 after initialization, with
actual AI state 0, not ordinary 300. See `green138-normal-witness.md` for boundaries
and the corrected generated Cutter assignment. Green no longer promotes Spark;
Chocolate's independent progression reason remains.

719 is an always-installed target with five OR witnesses: finite Doo Beam,
Fighter, Sword and Fire, plus the exact post-clear Central Master stand carrier.
Finite applicability is graph-local. The late branch still requires the modeled
return event, independent Central access, both carrier hubs and the enabled
Carrot Area Key. The [accepted native source/carrier](carrot-room7-master-source-witness.md)
now includes five key-on HP1 profiles at enemy 50/100/300/450/500, each with a
positive and cold repeat (ten successful traces total), a final-action omission
at 100 and source-derived finite-health qualification across 50–500. Mode1 qualifies acquisition only. Imported genuine historical
clear and already-open Hub doors do not establish current earned victory or
missing-Hub enforcement. The addressless event requires all 8 unique shards,
actual Dimension access, the DMK sequence and reachable Central independently
of the selected goal. Prior exact-source validation passed 46 real-generation
regressions plus eight goal audits (six archives, two correct minimal refusals);
these 54 checks are not a final-head aggregate or universal-seed proof.
No helper ability, other exit or reward is supplied by this branch.

825 is **one unconditional target with four OR witnesses**, not a conditional
target. Its finite Frosty Ice/UFO graphs retain source predicates;
its independent permanent Ice graphs do not depend on Frosty assignment.
Chocolate retains ten OR alternatives. The optional 538 Beam edge remains
always installed and fail-closed, without becoming a mandatory route.

404 now has reviewed ordinary human Normal evidence for the qualified
427→404→403 Paint 6 suffix at 6 HP/100%, 1 HP/100% and 1 HP/500%, each with
repeat and surviving puff-omission control. Its existing local predicates stay
null; no graph or source-policy fallback changes. Upstream availability,
407/230 ingress and broader native settings remain separate. See
`candy-normal404-source-witness.md`. One shared physical outcome is evidenced,
not two independent trigger recipes. The two cells were already among v4's
43 narrowed-role cells, leaving 352 unresolved-role cells in 249 groups.

## Completion boundary and maintaining the contract

`ranged-completion-scope.json` declares the reviewed bounded set, current
conditional targets and sampled public fallbacks. A change to applicability
must update the implementation, declaration and tests together after review.
The tests compare explicit declared outcomes to actual installation; they do
not require legacy permissiveness forever or silently accept arbitrary results.
A missing/new conditional target or changed public fallback fails `--check`.
Repairing a gap is progress, not a reason to preserve a failing legacy outcome.
The schema deliberately cannot promote an inventory into a completion claim.

Before making a broader completion claim:

- Assign relevant physical outcomes to exact AP checks, directed exits or goal
  routes. Distinguish irrelevant loot and valid ordinary alternatives from
  unresolved dependencies. 417 static F1/F6 cells are not 417 missing gates; the
  historical completion audit left 395 individually unadjudicated before
  role reconciliation. That historical baseline is not a new current metric.
  The 35 small switches likewise do not all require a copied ability.
- Cover supported source-policy classes with reviewed source, acquisition,
  carried-equipment, target-action and continuation contracts. Preserve ordinary
  solutions instead of adding mandatory copied-ability gates from one witness.
- Retain each native record's entry, health, permission, timing and continuity
  qualifications. Historical fixtures are not current-generator seed proof.
- Never rely on helper Copy Abilities, Bomb activation, combat, acquisition or
  carry. Only small-switch and Heave-Ho assistance may be considered, with its
  own positioning/timing evidence. No Phone capability or unmerged #1086 logic
  is supplied by this contract.

The normalized inventory has 382 regions, 384 locations and 1,083 AP surfaces.
Its 57 targets/146 witnesses include `mini_321_right_lower` and `fuse_323`, which
normalization adds to the 55 top-level union catalog rows. Those counts describe
structure, not 57 universally complete routes or all move×surface pairings.

## Bounded ordinary Peppermint 218 evidence

[Normal 218 witness](peppermint-normal218-source-witness.md) and its
[scalar acceptance](peppermint-normal218-acceptance.json) qualify only the original
221 left door bay → 218 → actual 200 suffix: natural500/HP1 acquisition, exact
repeat and live omission, plus shuffled50/HP1 positive12 and exact repeat13. Puff contact is 2114,
13 mutations finish 2168 with seven ceiling hazards, the lower peg stays 246,
and actual 200 arrives 2188. The omission has an exact common input window
through 2188 followed by a separately labeled 8+1+40 suffix and qualified Up2197.
Live/default-health attempt14 failed at1119 and receives no route credit;
proposed fresh15/repeat16 are unrun.
Existing null 22→23/23→24 rules, Paint01 peg, RoomSanity and 200→BOSS stay
unchanged. Right-side 217/225 ingress to the 221 left bay is not proved. No
new target, source-policy binding or generic Normal ability gate is added.
Current counts remain 57 targets/146 witnesses/four target-wide fallbacks.
