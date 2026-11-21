# Opt-in placement retries

Use **KirbyAM Generator (placement retries)** in Archipelago Launcher, or from a
source checkout run:

```
python -m worlds.kirbyam.generation_retry --seed 105103 --player_files_path Players --outputpath output
```

This entry point supports one KirbyAM player, non-race generation and normal
archive output (or `--skip_output`). YAML and weighted options are rolled once.
There are at most **eight total attempts**, including the unchanged original
first seed. Later seeds use the first eight bytes of SHA-256 of
`kirbyam-placement-retry-v1:<input_seed>:<zero_based_attempt>`, interpreted as an
unsigned big-endian integer. The same rolled settings and input seed therefore
produce the same attempt sequence. Each attempt builds a fresh MultiWorld from a
deep copy of the original arguments at `Main.main`, never refilling shared state.

Only the final Kirby all-check audit can authorize a retry: every enabled check
must be filled and reachable with all inventory, and the remaining failure must
be progression locked behind actual placements. Invalid options, missing items,
structurally unavailable routes, source-selection failures, generic FillError,
ROM/output errors and other exceptions stop immediately. The audit still runs
with minimal accessibility; it never accepts an unsafe fill. This does not change
copy-ability pools, runtime odds, permissions or acquisition rules. Completely
Random can roll any eligible unlocked ability, but a possible finite roll is not
a guaranteed acquisition.

Each attempt writes into a temporary directory within the destination. Rejected
attempts are deleted, and only the successful archive is atomically published
without overwriting an existing file. The archive includes
`kirbyam-generation-attempts.json` with input/successful seeds, attempt count,
cap and failed audit reasons. Exhaustion reports the input seed, cap and last
failure; no archive is published. Logs retain every attempt's reason.

## Scope

Ordinary Archipelago generation and web generation are unchanged. APWorld hooks
cannot safely restart an entire shared generation, so this opt-in launcher does
not intercept those entry points. Multiworld, race mode, CSV and spoiler-only
output are explicitly rejected by this launcher before generation. Use ordinary
Archipelago generation for those modes; its existing fail-closed audit remains.
This is not an in-place refill hook and does not alter another player's settings.

The Mustard timer patch and source-aware Advanced Fire route apply identically
in both entry points. Tests cover the unchanged first attempt, controlled
failure/success, actual minimal-fill failure/success and repeated placements,
exhaustion, structured retry classification, no partial output, output collisions
and unsupported shared/race modes.
