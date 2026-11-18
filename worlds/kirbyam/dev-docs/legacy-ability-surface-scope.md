# Remaining ability fallback scope (#1119)

The normalized audit preserves each exact owner, directed exit or location and
its original Boolean requirement. It enumerates 287 requirement-bearing surfaces
with 398 action/movement tokens plus eight lever-item tokens:

| Classification | Tokens | Meaning |
| --- | ---: | --- |
| Normal movement | 218 | Fly, swim and climb do not require a Copy Ability |
| Installed traversal witness | 29 | Exact surface has an existing traversal target |
| Policy-scoped witness | 2 | Mustard map tokens whose target still has unsupported-policy fallback |
| Unresolved action context | 149 | 131 block and 18 floating-block tokens lack an exact installed target |

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

The top room141 Mirra now has a bounded source-free Normal puff witness and an
actual native545 transition. Its removed legacy token is not counted as an
unresolved action. See `mirra141-normal-witness.md`; the other Mirra surfaces require their own evidence.

The east room141 Mirra now has a separately scoped Normal puff witness with
eight positive local/actual-entry fixtures and two wrong-facing controls.
See `mirra141-east-normal-witness.md`; failed timing variants are retained as limits.

The room117 Carrot exit now has a finite Normal route from independently reachable
Hub 3/native192, consuming the original Waddle Doo and Waddle Dee payloads. Four complete
entry-to-exit variants pass; the wrong-facing control remains blocked. See
`mirra117-normal-witness.md`. Its block and Mirra tokens leave the unresolved count;
the distinct upper-room Carrot exit remains unresolved.

Room811 now has a separately evidenced Normal route from independent Room11/native829
access to Room15/native551. Four actual-entry variants and a live blocked control
support it. Its block/Mirra requirements are replaced while swimming is preserved;
all four former Mirra tokens now have bounded routes. This does not certify the
western Bomb Block/Gordo approach. See `mirra811-normal-witness.md`.

The Normal590→534→310 prefix is now bound separately to Rainbow Room34’s Mustard chest-room entrance. All 71 retained Sir Kibble fixture prefixes preserve Normal and initial HP before any acquisition. This removes one directed block fallback; the later Mustard map source-policy fallback remains. See `normal534-mustard-entry.md`.

The second directed prefix now binds Rainbow Room34→Mustard Room15/native533, with the same two original finite payloads and a distinct verified upper approach. Four fresh one-HP positives and two failed inhale-omission controls support that entrance only. Both directed entrance replacements together leave149 unresolved action tokens; neither changes the separate Room15→Room16 or map-chest rules.
