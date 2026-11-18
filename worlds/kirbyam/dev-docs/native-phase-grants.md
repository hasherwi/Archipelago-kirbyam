# Native phase-dependent grants

The ROM table is a default, not every native state write. WiKirby's
[Golem description](https://wikirby.com/wiki/Golem) identifies Stone, rolling Wheel
and uppercut Fighter as a research lead. The pinned native `golem.c` verifies the
actual assignments and selection branches. This adds conditional grant contracts
to 19 static Golems and three King Golem output candidates; no acquisition route is
created by these facts.

For low-seven-bit subtype zero, native type 31 retains Stone, type 32 selects
Stone/Wheel, and type 33 selects Stone/Fighter. A nonzero low-seven-bit subtype can
select all three actions; unknown generated subtypes retain all three candidates.
`sub_080C5500` selects actions, `sub_080C5AB4`/`sub_080C5B50` dispatch them, and the
named state functions write `kirbyAbility`. The inventory records the source hash,
subtype, allowed outputs and state writers. It does not infer safe timing,
Super Inhale access, source repeatability, or a defeat/carry suffix from the wiki.

Physical compilation supplies `Placement.native_grants` to the existing source
resolver. In vanilla, these are alternative outcomes of an unselected native
phase. Owning only Stone cannot turn Stone/Wheel into guaranteed Stone: the
unowned Wheel outcome remains a possible failure. Native phases are not live RNG
retries. A witness may narrow `native_grants` only to listed native outcomes and
must supply `native_grant_evidence`; unrelated sources cannot invent phase grants.
This evidence still needs physical acquisition and carry review.

Eligible shuffled assignments override native state writes through the existing
production swallow hook and actual patched table. Eligible live randomization
uses its actual allowed pool, ownership filter and no-ability weight. The new
native alternatives therefore do not replace randomized grants. Cache identity
includes the native outcome set so two physical phases of the same enemy family
cannot borrow each other's grant.

No current production witness acquires a Golem. Existing King Golem native
fixtures demonstrate bounded Stone/Ice outcomes at their recorded intake phases,
not every phase or a safe 500% route. This change prevents future physical joins
from silently treating the default Stone table entry as unconditional equipment.


## Attached Parasol parents

The same native-state audit covers 26 static parent placements. Waddle Dee type 0
subtype 3 has Parasol/Normal alternatives; subtype 4 retains Parasol. Waddle Doo
type 18 subtype 1 has Parasol/Beam alternatives. The extractor pins
`waddle_dee.c`, `waddle_doo.c` and `parasol.c`: the constructors install the attached
states, and `sub_080C2D44` restores the parent's native grant when its attachment
ends, explicitly excluding Waddle Dee subtype 4 from the Normal reset.

These are parent grants, not duplicate credit for the detached Parasol object.
No current reviewed graph binds these 26 placements. Unknown generated subtypes
are outside this specific contract; no generic Waddle family behavior, safe
attachment timing, source access or reacquisition is inferred. Existing runtime
assignments still override native writes. The ordinary room117 payloads are
unaffected and remain finite objects used for spitting, not copy grants.
