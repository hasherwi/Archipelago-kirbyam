# Fresh finite release generation audit

`tools/audit_release_generation.py` is a reproducible **112-attempt first checkpoint**,
not an exhaustive option product or proof of all seeds/native routes. Run it using
the repository's test Python environment, with a new durable output directory:

```
python worlds/kirbyam/tools/audit_release_generation.py --output /local/audit --plan-only
python worlds/kirbyam/tools/audit_release_generation.py --output /local/audit --limit 8
```

Repeat the second command to continue. `--case ID` selects a planned case without
changing its options or seed. Each attempt runs in an isolated subprocess and
retains its inputs, log, result and generated archive. Started/completed JSONL
records are flushed and fsynced individually. An interrupted attempt is preserved;
review it before explicitly using `--retry-incomplete`, which creates a different
attempt directory. Candidate or options digest changes prohibit resume into the
same directory. There is no automatic seed replacement. Unexpected errors and
timeouts are failures to investigate, not successful rejection evidence.

## Coverage

Two fixed seeds,105100 and20261109, each exercise:

*36 core combinations: three ability modes × gating on/off × full/minimal
 accessibility × Normal weights0/99/100.
*16 binary orthogonal rows for statue/passive/miniboss/boss-spawn inclusion,
 room sanity, area keys and all-maps starts. Every pair of those seven factors
 has each binary combination four times. Other values rotate across all four
 goals, all eight configured bosses, boss counts1/8, health minima1/6 and
 maxima1/10, enemy health50/100/500%, and vanilla/randomized shards.
*Two three-player mixed-mode/gating worlds, with explicit Ice×3 on player2.
*Two two-player Stone/Burning item-link worlds, at full/minimal accessibility.

The manifest lists explicit per-dimension values, fixed cases, options digest,
Git HEAD/tree and hashes of current tracked Kirby files plus generation core.
Other unlisted option defaults remain defaults. This is pairwise balance for the
listed binary factors, **not** a pairwise claim across every nonbinary dimension.
Results should determine targeted extensions or a larger public-option product.

## Outcomes and acceptance

The existing generation helper calls real Generate/Main, fill, production source
selection and the all-check guard. Solver budgets and guards are never replaced.
Instrumentation measures attempts/timing without changing decisions. Known
source-search budget exhaustion is distinct from the post-fill all-check refusal;
unknown option/value errors remain unexpected errors for manual review. A refused
case must have no output archive. Accepted archives are decoded and checked for:

* Exact explicit/automatic ability starts, preserving multiplicity.
* New24 gate mask0x03ffff7e when gated,0 otherwise, and matching slot catalog.
* One permission per enabled ability, accounting for linked group ownership,
 with no duplicate private copy of linked items; Beam absent from the pool.
* No unfilled checks, no all-inventory unreachable checks, and independently no
 checks unreachable from the **actual placed progression sweep** across players.

The sweep never bulk-collects the item pool or promotes useful items. Archives are
hashed. These are generated token-patch/archive and logical-closure checks, not
an applied commercial-ROM playthrough, server session or native controller proof.
Historical test counts do not establish a pass for this new candidate.

## Defined2304 product and bounded parallelism

`--plan product2304` selects exactly3 ability modes ×2 gating values ×2
accessibility values ×3 Normal weights(0/99/100) ×64 combinations of six binary
flags(statues, passive enemies, minibosses, boss spawns, room sanity, area keys),
at fixed seed105100. IDs are `product-0000-105100` through
`product-2303-105100`. All other options retain defaults. Goals, health, maps and
shards remain separately sampled by the default112 plan;2304 does not mean all
public options or all seeds.

`--jobs 1` is the default. Values2–4 bound concurrent fresh worker processes;
start conservatively and inspect timings/peak RSS before increasing. Only the
coordinating thread writes the JSONL. A coordinator lease excludes concurrent
runs against the same output directory; each attempt has a child-inherited lease
so a surviving worker cannot be duplicated by a resumed coordinator. Completed
orphans are verified before reconciliation. Worker results are atomically
replaced after fsync and include peak RSS where supported. POSIX file leases
require the Linux/macOS test environment; do not remove lease files to bypass a
live process. Parallelism changes scheduling, not source-selection budgets or
case seeds. Use a separate directory for each plan/candidate hash.


Parallel startup requires an existing `options.yaml` or `host.yaml` in the writable
source checkout. If neither exists, the preflight stops without creating or changing
configuration. Initialize sequentially with `--jobs 1 --limit 1`, then resume the
same candidate/output with multiple workers. `--plan-only` does not start workers
and needs no settings file. Existing settings are never rewritten by this preflight.
The legacy `options.yaml` filename remains supported, matching the settings loader.
