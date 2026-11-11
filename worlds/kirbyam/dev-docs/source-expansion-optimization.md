# Per-evaluation source expansion deduplication

## Scope and equivalence

The optimization's only production change is a local `expanded_sources` set in
`reachable_positions`. Its key is `(node, opened, consumed)`. It is discarded
when the evaluation ends. Graph compilation, source grants, AP source-access
checks, inventory gathering, equipment drops, recovery and route transfers are
unchanged. There is no persistent result cache or cross-target state sharing.

For fixed policy, permissions and retry mode, the source loop never reads the
incoming equipment. Its output Positions and retry qualifications depend only
on that key: source eligibility and finite identities use `node` and `consumed`,
and every successor retains `opened`. The first reachable Position for a key
therefore emits exactly the same source successors and qualifications as any
later Position with that key. Repeating these identical transitions cannot
change the finite fixed point or the union of retry assumptions. All Positions
still receive their own drop, recovery and route expansion.

In particular, a mixed finite grant remains an uncertain equipment set, not a
chosen outcome. Documented retries still require the same renewable placement,
evidence and live grant. Neither consumed identities nor opened barriers are
projected away. A new physical phase still gets its own source expansion.

## Verification

`test/traversal_reference.py` freezes the complete pre-change evaluator from
`181c6e9faeb97040723d0786d4b6f1fc31156441`. Its function AST was checked against
that commit. Removing only the new set, key and source-loop guard reconstructs
the original production module AST; route/drop handling has not changed.

`test/test_traversal_source_expansion.py` performs 7,171 exact full-result
comparisons at this checkpoint, in 707 pytest cases:

- Exhaustive local combinations of finite/renewable enemy/statue sources,
  permissions, acquisition requirements, starting equipment and opened/consumed
  phases, repeated with changed permissions and reversed starts.
- 32 deterministic generated graphs across eight policies and both gating/retry
  modes. These include finite ammunition, frozen projectiles, Crash consumption,
  Mini transitions/recovery, opened pegs, and preserved/reset room instances.
- All 80 reviewed graph/witness pairs across eight policies and all area-key,
  gating and retry combinations. The catalog test also includes future targets.
- Full 25-ability live 707, with finite failure and qualified-retry success kept
  distinct, plus an explicit opened/consumed-identity regression.

Every comparison checks all Positions, including their equipment sets and both
phase sets, and all retry-assumption strings. Negative mutation checks verified
that omitting `opened`, omitting `consumed`, or keeping only `node` fails the
explicit phase regression.

The broader focused traversal/metal/peg/mini/wheel/hub/audit run passed 1,446
tests. An unscoped run with all-world imports passed 996 tests, including the
new equivalence suite, core traversal/data, metal, hub and audit tests. Flake8,
strict mypy on all four changed/new Python modules and `git diff --check` passed.

## Paired measurements

Reproduce from the repository with its test Python environment:

```sh
python worlds/kirbyam/tools/benchmark_source_expansion.py
```

The separate `source-expansion-benchmark.json` preserves every sample. Python
3.12.14; seven samples of 50 evaluations, alternating old/new order after warmup.
Both evaluators receive identical graph, policy and owned-item inputs, and their
complete results are checked equal. Imports and graph compilation are excluded.
Queue counts are recorded separately from timing. Full-pool live runs use the
existing documented-retry semantics, not a finite RNG guarantee.

| Case | Positions, unchanged | Dequeues, reference / optimized | Median ms, reference / optimized |
| --- | ---: | ---: | ---: |
| 707_native | 290 | 1265 / 815 | 1.6797 / 1.0474 |
| 707_live_finite | 36 | 143 / 113 | 0.3303 / 0.2890 |
| 707_live_retries | 452 | 19235 / 1955 | 19.1425 / 2.5179 |
| 216_native | 306 | 1296 / 846 | 1.6213 / 1.0983 |
| 216_live_finite | 38 | 146 / 116 | 0.3241 / 0.2912 |
| 216_live_retries | 477 | 19284 / 2004 | 18.6723 / 2.4517 |
| 742_native | 9 | 10 / 10 | 0.0243 / 0.0240 |
| 557_native | 9 | 10 / 10 | 0.0237 / 0.0243 |
| peg605_native | 17 | 31 / 27 | 0.0453 / 0.0422 |
| mini134_native | 7 | 7 / 7 | 0.0215 / 0.0222 |

The benefit comes from suppressing duplicate source successors, rather than
changing reachable states. Small local graphs see less than one microsecond of
added bookkeeping in this run; timings are machine-specific, not CI thresholds.
These are planner measurements, not new native movement, source-carrier or
one-hit-health acceptance evidence. The integrated benchmark and catalog tests
include both new room 216 graphs. The combined Kirby test suite passed 7,618
tests with one missing-Lua skip; hosting was excluded for the local socket
restriction and remains covered by CI.
