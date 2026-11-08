# Nine legacy metal exits: research audit

Baseline: `bee5a93`. Native source revision: `7d969fbce14fdc838d2c1ea01389717fb96c3189`.

This is research, not production route acceptance. This audit itself changes no production route, world data, or starting inventory. The complete structured result is `legacy-metal-exit-audit.json`, keyed by all nine exact directed AP edges. Three supplemental native extracts were read independently and are not bundled publication dependencies. Their content-addressed retrieval URLs and retention/access limits are in the audit JSON. All ten inspected map images now have URLs, article revisions and byte hashes in `legacy-metal-public-map-references.json`. Actual map pixels were inspected.

## Findings that change implementation

1. **707 is a cramped horizontal passage.** Its F5 tiles `(69,4)` and `(70,4)` lie under solid ceiling and above solid floor. The left approach pocket is reached through shaft `(65..66,5..6)`. The door beyond the metal is `707 (72,2) -> 712 (2,29)`. There is no upper-pocket ammunition. The local Heavy Knight supplies Sword and the Waddle Doo supplies Beam in vanilla. An ordinary statue Burning carrier can start at native592, continue through801/790/706, and approach707, but the continuation and exact attack still require acceptance. A source from740 was investigated and rejected: the apparent outdoor Flamer is a tomato.

2. **742 needs a chest co-target and distinct arrivals.** Chest `0x088BDD10` at `(408,280)` contains the sparerib and is currently ungated in `ROOM_2_15`. Map and prose put it beyond the same upper metal entrance as Warp. The lower bomb-component check is complete: its outer trigger closes the upper-to-chest opening and introduces upward-only side caps. The inner trigger only reveals the741 door. Warp and chest therefore need separate post-metal state routes. The actual native return loop is `742 (25,12) -> 741 (11,8)`, followed by native Flamer sources `0x088BDA38 (136,80)` or `0x088BDA5C (200,80)`, then `741 (3,2) -> 742 (19,8)`. The initial lower entry is `741 (1,17) -> 742 (30,29)`. Current `ROOM_2_15_UPPER_LEDGE_SPAWN` has no incoming AP edge; both741 entries point at the generic room.

3. **141 needs entry-side preservation.** Its first bank is left-to-right at `x5..6/y7..8`; the second is left-to-right at `x27..28/y9..10`. The lower pre-gate Flamer is `0x088B78E8 (152,192)`, and the upper Flamer is `0x088B7810 (168,64)`. The source-looking icons at `(520,280)` and `(376,168)` are food. Native144 returns at `(43,9)`, already right of the second bank. Native545 returns at `(34,4)` in the uppermost corridor. Both currently map to generic lower `ROOM_1_41`. The apparent top bypass crosses an upward-only platform cap, so it is not accepted as a Normal drop route.

4. **708 needs directed choke and source proofs.** Its two F5 tiles at `x36..37/y23` split the left and right compartments. Vanilla local abilities are Beam/Cutter, not metal providers. The left Snooter at `(496,344)` is a nearby possible physical object, but its capture pose and throw trajectory are not demonstrated. It cannot be walked to the barrier after capture. The right Scarfy is absent from the source registry. Native706 returns at `(43,3)` on the right, although current AP maps its lower return to generic left `ROOM_2_01`.

5. **205 is a downward plug, not a horizontal wall.** F5 `x21..22/y8..9` has solid side columns and water below. The separate upper cluster `x24..26/y3..4` is not this gate. Existing aerial Hammer acceptance proves only this isolated dry attack. A source carrier and the subsequent water/Bomb path to `205 (29,17) -> 209 (11,3)` are not yet accepted. Local Burning does not automatically solve this geometry. Actual Flamers are `(304,16)` and `(656,216)`; the object at `(264,280)` is a Blipper.

## Policy and test boundaries

- Fixed or excluded sources supply only their actual native grant, subject to permission gating.
- Deterministic sources must use the finalized assignment and an independently reachable physical placement.
- A multi-output live-random enemy, especially with a possible Normal result, is not a finite guarantee. No enemy retry loop is established here.
- Existing permanent-statue retouch fairness can be reused only with explicit retry evidence and an accepted subsequent carrier.
- Throw remains a physical-object action, not an inventory-only provider. No new Throw witness is accepted here.
- No new controller sequence was run by this audit. The existing205 Hammer result is not extended to other providers or rooms.
- Starting Stone/Burning removal remains unsafe on these findings alone.

## Completed final mutation check

- Native708 is confirmed as a one-tile-high horizontal throat, with solid ceiling and floor around its two F5 tiles.
- Native742 outer bomb `(19,12)` changes row9 x22..28 to spikes, cells `(24,8)/(25,8)` to solid, and side shaft caps `(22,13)/(28,13)` to upward-only platforms. Inner bomb `(26,12)` is a separate component and only reveals the741 return door. It does not open the floor.
- Warp and chest must have separate post-metal routes. A Burning return loop cannot assume the742 room resets after leaving it.
- Native741 has another actual Flamer in its main corridor, `0x088BD8AC (200,224)`. If a capture-and-carry path can be proven before its lower door to742, it avoids the chest-closing742 bomb loop. This is the preferred next source candidate, not a completed acceptance.

## Next bounded acceptance work

- Native707: actual Burning source/carry continuation, left-pocket launch, passage through the one-tile throat, and entry into712. Keep the source and attack proof layers separate.
- Native742: verify capture of the main-corridor741 Flamer, carry into742 without activating its outer lower bomb, horizontal Burning, and the distinct Warp/chest branches. The return-corridor Flamer loop remains a separate state-sensitive alternative.
- Native141: controller proof from each lower entry to the lower Flamer, then the two directed horizontal banks. Resolve144/545 arrival compartments before using them as starts.
- Native708: exact low-throat move from each side, plus actual source carrier and Bomb order. Treat Throw as a separate unresolved capture experiment.
- Native205: production source to the dry plug, the exact vertical attack, then the water/Bomb route to209.

## Reproducibility and implementation follow-up

See `legacy-metal-reproducibility.md`, `legacy-metal-public-source-references.json`, and the portable `validate_legacy_metal_audit.py`. Published consistency validation is not independent native reproduction. The optional local-ROM reader was not executed in this audit environment. The original extraction commands were not supplied; their byte-for-byte recreation is not claimed.

The isolated `moonlight-742-implementation-design.md` proposes explicit clean/altered action-state nodes, separate chest/Warp targets, and existing graph-part reuse. Its `check_742_design_semantics.py` passed 35 kernel assertions at `32d1c44`, with hypothetical physical movement edges only. It does not authorize marking those routes reviewed.
