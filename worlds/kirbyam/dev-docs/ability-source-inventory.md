# Physical ability source inventory (#1114, incomplete)

`data/ability_source_inventory.json` records every native room slot and every
static object template from the unmodified USA ROM. It includes normally
non-ability enemies, minibosses, statues, encounter controllers and other objects
so exclusions can be audited. Empty records and unused room slots are explicit.
Native room IDs identify subrooms; AP aliases come from the existing completion
index mapping and do not establish accessible compartments.

A stable placement identity is `(native room, template address)`. The record
retains spawn-table namespace, object type, coordinates, subtype, native grant
where resolved, and the native spawn-state predicate inputs. These are decoded
facts, not copied ROM payloads. The source grant key points to the existing
`SourcePolicy`, which uses actual runtime writes/configuration in vanilla,
shuffled and live-random modes. No new random-assignment approximation is used.

All 133 ordinary source rows in existing reviewed source sets and graph parts
now join this inventory through 109 legacy identity bindings (108 distinct
placements). The reviewed graph JSON and its fingerprints are unchanged.
Production room graphs require an inventory binding; isolated solver fixtures
retain their explicit synthetic-source API. Compilation rejects unknown
references, room and
grant mismatches. It preserves the original acquisition prerequisites, graph
compartments, consumed-source identities, renewability and retry evidence.
The special post-clear Master stand retains its separate exact witness contract.
Neither possession of a permission nor an inventory row equips Kirby. Gating off
still requires physical acquisition. Moving a source behind its own barrier
cannot justify reaching it.

Encounter source types are rejected from standard room graphs, including when
introduced through reusable graph parts or source sets. Advanced graphs still
need an explicit acquisition witness. The encounter census records 126
controller/call-site candidate pairs and 22 known runtime grant types as
**unresolved candidates**; none are automatically added as usable sources.
All direct-call type expressions
are decoded as candidate sets, including subtype-dependent Dark Mind stars.
Raw native grant IDs remain visible when no runtime source key is known.
The census follows generated controller types, including Titan Head and the
second Crazy Hand phase, and retains candidate roots. Translation-unit scans
can include another phase's branch; this is not a certified controller call graph.
File hashes identify the local
decompilation inputs; the reference commit identifies the layout reference,
not a claim that every local source file is unchanged from that commit.

The native random-statue controller in room 951 creates two physical slots with
19 possible native statue selections and prevents the two native indices from
matching. Those slots are recorded separately with native coordinates. A fixed
selection lasts for that instance; retouch does not redraw the native index.
Their grants remain unresolved for traversal, rather than turning the union of
possible selections into guaranteed finite acquisition.

The 37 native object spawners also have separate child prototypes: 31 enemies
and six minibosses. These include normally non-ability enemies. Their child
position, subtype, type, configured capacity and destroyed-slot reclamation
flag come from the controller template and the [pinned native creation code](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/asm/object_spawner.s#L364-L455).
All native templates have capacity one and disable slot reclamation. This does
not prove acquisition or repeatability across room instances. These unresolved
prototypes are excluded from traversal references; their miniboss descendants
are included in the Advanced-only encounter candidate census.

## Reproduction

Run from the repository root with a lawful, unmodified USA ROM and the local
KATAM decompilation source tree:

```sh
python worlds/kirbyam/tools/extract_ability_source_inventory.py \
  --rom /private/kirby-usa.gba --decomp /private/katam \
  --output worlds/kirbyam/data/ability_source_inventory.json
python worlds/kirbyam/tools/audit_ability_source_coverage.py \
  --output worlds/kirbyam/dev-docs/ability-source-coverage.json
```

The extractor checks the ROM size/SHA-1, bounds, table namespace, record sizes,
and terminators. It does not start an emulator or read/write any playthrough
save. The #1059 playthrough remains paused.

## Remaining acceptance gaps

This draft does **not** complete #1114. The machine-readable coverage report
lists unbound placements, compact ability tokens and policy-scoped targets.
Presence alone cannot prove arbitrary room geometry or acquisition. Remaining
work includes reviewed compartment access/carry for unbound placements;
encounter branches, indirect spawn helpers and lifetime prerequisites; object
spawner activation, acquisition and lifetime; random-statue acquisition/retry
routes; and systematic replacement of
legacy permissive gates with accepted source routes or established Normal
alternatives. `_allow_pending_ability_gate` and unsupported-policy fallback
behavior are still present. The draft neither invents those witnesses nor
reports unreviewed routes as physically impossible.
