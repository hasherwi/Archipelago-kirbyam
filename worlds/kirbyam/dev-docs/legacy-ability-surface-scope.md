# Remaining ability fallback scope (#1119)

The normalized audit preserves each exact owner, directed exit or location and
its original Boolean requirement. It enumerates 292 requirement-bearing surfaces
with 406 action/movement tokens plus eight lever-item tokens:

| Classification | Tokens | Meaning |
| --- | ---: | --- |
| Normal movement | 218 | Fly, swim and climb do not require a Copy Ability |
| Installed traversal witness | 29 | Exact surface has an existing traversal target |
| Policy-scoped witness | 2 | Mustard map tokens whose target still has unsupported-policy fallback |
| Unresolved action context | 157 | 135 block, 18 floating-block and four Mirra tokens lack an exact installed target |

Normal movement now has an explicit dispatch independent of the pending ability
fallback. This does not certify arbitrary geometry or allow equipped abilities
to cross a carry restriction; those belong to compartment routes. The audit's
structural witness classification does not replace the target's actual policy,
permission, source-access and carry evaluation. All peg, Mini, fuse, rope, Wheel
and metal tokens have exact target coverage. Mustard Room15 remains fail-closed.

The three unsupported-policy targets remain Chocolate517, Mustard310 and
Yellow733. The separate local Kibble witness closes vanilla Mustard acquisition,
but does not certify arbitrary shuffled grants or finite live-random outcomes.
No global source inventory scan, permission check, or arbitrary room-wide source
placement can safely replace these gaps. The unresolved block/floating-block
labels also do not establish that every surface needs a Copy Ability; some may
have Normal alternatives. Blanket rejection would incorrectly claim knowledge
we do not have. These fallbacks therefore remain explicit and #1119 remains open.

[Issue #1090](https://github.com/hasherwi/Archipelago-kirbyam/issues/1090) proposes
travel distance instead of area boundaries. Harrison suggests “Maybe three rooms?”
in [his comment](https://github.com/hasherwi/Archipelago-kirbyam/issues/1090#issuecomment-6936655165),
and BlameMateo agrees three is reasonable in
[the reply](https://github.com/hasherwi/Archipelago-kirbyam/issues/1090#issuecomment-6961928433).
Neither defines whether to count the source room, destination room, transitions,
revisits or same-room doors. No global limit is imposed from this design context,
and it is not used as evidence that any source can be reached or carried.

Regenerate the audit with `audit_legacy_ability_surfaces.build_audit()` from the
Kirby test environment. Tests verify exact directed matching, reproducibility,
counts, preserved `all`/`any` expressions, and Normal movement independent of
both owned items and the pending equipment fallback. This work does not claim
full closure of #1114 or #1119.
