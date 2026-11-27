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

All 134 ordinary source rows in existing reviewed source sets and graph parts
now join this inventory through 110 legacy identity bindings (109 distinct
placements). The pre-existing reviewed graphs and their fingerprints are
unchanged; #1117 adds a separately verified local Sir Kibble alternative.
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
A reviewed contact witness evaluates every possible native selection through
SourcePolicy; the union is not a guaranteed chosen ability. Independent AP access
to these slots remains unresolved.

The 37 native object spawners also have separate child prototypes: 31 enemies
and six minibosses. These include normally non-ability enemies. Their child
position, subtype, type, configured capacity and destroyed-slot reclamation
flag come from the controller template and the [pinned native creation code](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/asm/object_spawner.s#L364-L455).
All native templates have capacity one and disable slot reclamation. This does
not prove acquisition or repeatability across room instances. These unresolved
prototypes join the same physical registry as static placements. Their miniboss
descendants are included in the Advanced-only encounter candidate census.

The common registry also indexes 731 root/controller/call/output combinations,
with explicit per-room references. These preserve candidate branch sets and
unresolved access rather than manufacturing a guaranteed output. A generated
reference requires generation, lifetime and acquisition evidence. Its lifetime
identity is pinned to the output record, separately from its parent placement.
Separately evidenced finite encounter occurrences may append a named instance;
fixed statue slots and non-reclaiming spawners cannot use this to multiply supply. Encounter-generated ordinary enemies
are Advanced-only too; their ordinary source type cannot bypass this restriction.

The existing traversal state tracks active and expired source lifetimes alongside
one equipped ability and consumed objects. Generated outputs require an evidenced
activation edge before acquisition. Evidenced routes can lose equipment or
end an encounter lifetime. Loss requires actual reacquisition from a still-live
source. A room reset clears only ordinary finite uses in its destination native room
whose spawn-state bank permits room-local respawn. Remote sources and the ten
Cookin/Jack placements with persistent banks retain consumption. Generated
consumption and expired lifetimes require explicit revival on an actual reset
transition, followed by separately evidenced generation. Capacity-one
spawners without destroyed-slot reclamation cannot be declared renewable; a
renewal claim cannot override that decoded native limit. These fields
extend the existing solver and preserve previous routes when absent.

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

## Step 5 acquisition backlog (#1170)

Build a room-by-room review queue from the existing inventory and traversal
references, without a ROM, emulator, or new playthrough results:

```sh
python worlds/kirbyam/tools/audit_ability_source_coverage.py \
  --output /tmp/kirby-ability-source-coverage.json \
  --acquisition-backlog /tmp/kirby-ability-acquisition-backlog.json
```

The backlog separates static placements, generated statue slots, spawner
children and encounter outputs, including potential randomized sources whose
stock grant is Normal. Existing inventory references, including alternatives
and legacy bindings, are excluded; that does not certify all uses of a
referenced source. Known outside-Adventure candidates are counted but not
queued. AP region names are candidate aliases only, not source access in
every subroom. Empty aliases mean no known mapping in the inventory.

Review each candidate's exact acquisition compartment, activation, lifetime,
and directed route separately. This report does not add routes, prove
three-room carry, certify a dynamic spawn, or affect generation. It is a
physical-source backlog, not a count of remaining playthrough checks.

## Remaining acceptance gaps

This draft does **not** complete #1114. The machine-readable coverage report
lists unbound placements, compact ability tokens and policy-scoped targets.
Presence alone cannot prove arbitrary room geometry or acquisition. Remaining
work includes reviewed compartment access/carry for unbound placements;
encounter branches, indirect spawn helpers and lifetime prerequisites; object
spawner acquisition and lifetime; safe AP access and reset routes for random
statues; and systematic replacement of
legacy permissive gates with accepted source routes or established Normal
alternatives. `_allow_pending_ability_gate` and unsupported-policy fallback
behavior are still present. The draft neither invents those witnesses nor
reports unreviewed routes as physically impossible.


## Follow-up evidence

The separately verified [Mustard local Cutter route #1117](https://github.com/hasherwi/Archipelago-kirbyam/issues/1117)
is now included; its [native witness](mustard-map-kibble-source-witness.md) and
acceptance manifest document bounded claims; earlier failed timings remain in
the private evidence packets.
[Generated activation/lifetimes #1118](https://github.com/hasherwi/Archipelago-kirbyam/issues/1118)
and [remaining legacy fallbacks #1119](https://github.com/hasherwi/Archipelago-kirbyam/issues/1119)
are being addressed separately in sequence. The shared generated-source
[activation, selection and lifetime contract](generated-source-lifetimes.md) now
includes bounded native statue and Frosty observations. Unresolved AP access and
other generated branches remain explicit; catalog coverage alone does not
complete them. The exact requested changelog wording must not be used as evidence
that every legacy gate is fixed.

Native phase-dependent grants are now explicit for all22 Golem records; the ROM
table default is not assumed to describe every attack state. See
`native-phase-grants.md`. Phase alternatives preserve uncertainty in vanilla,
while eligible shuffled/live behavior retains the production runtime semantics.

### AP room and subroom coverage

`ap_region_inventory` explicitly enumerates all 354 declared AP room/compartment
records, including 33 generated `__LOGIC__` subregions. There are 263 direct
native door-list joins, 33 joins through an explicitly declared logical parent,
and 58 unresolved mappings. An empty `native_rooms` list means **unknown mapping**,
not an empty physical room. Native empty object lists remain separately recorded
in `rooms`.

A parent/native-room join does not assign its enemies to every compartment.
Compartment placement membership remains unresolved until the existing reviewed
source bindings and acquisition graphs establish it. In particular, similarly
named legacy regions such as `ROOM_1_24_UPPER` do not inherit the base region's
sources or the Hub3 entry merely because their names share a prefix. These
coverage rows add no access rule, carry route, grant or renewable source.
