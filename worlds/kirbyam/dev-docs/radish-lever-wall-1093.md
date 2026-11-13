# Radish lever wall compartment correction (#1093)

## Confirmed defect

The old graph let a Carrot Castle 5-06 arrival access Radish 8-12's
lever and onward exit without receiving the Radish wall item. Its reverse-only
`rr_lever` gate did not represent the actual barrier. All four Lever Wall items
were and remain progression; spoiler minimization is not the cause of this
incorrect reachability edge.

## Native evidence

The reproducible read-only `tools/verify_radish_lever_wall.py` requires the
unmodified USA SHA1 `274b102b6d940f46861a92b4e65f89a51815c12c`. It emits only
interpreted coordinates/metadata (fixture `test/data/radish-lever-wall-native.json`),
not ROM assets.

- Native Carrot chute 181 enters Radish room 619 at spawn (4,4), on the left.
- Room 619 has ordinary solid walls surrounding a vertical F2 barrier at x=5,
  y=1..3. F2 collision attributes are `0x240`: solid (`0x200`) plus the
  break-chain flag (`0x40`). Its two closed components contain 12 and 54 cells.
- The return door to 181 is at (2,3), left of the barrier. The Radish exit to
  608 is at (12,7), on the right; the lever object is at (12,3), also right.
- The triggerable-wall object at ROM offset `0x8D1478` (type `0x91`) is
  at pixel (88,56), tile (5,3). The native spawn table maps this type to
  `CreateLeverWall`. `LeverWallAction` waits for its room counter, clears
  the tile, then `sub_0800E0E4` removes connected tiles with flag `0x40`.
- Clearing those barrier tiles joins the components. This is static geometry
  evidence, **not** a newly performed gameplay traversal or full-seed run.

Native source pinned at
[katam 7d969f](https://github.com/jiangzhengwenjz/katam/tree/7d969fbce14fdc838d2c1ea01389717fb96c3189):
`src/lever_wall.c`, `src/code_0800E0E4.c`, `data/object.s`.

## Model

Keep the canonical 8-12 region as the Radish/right side. Redirect Carrot
5-06 arrivals to `CARROT_SIDE`; it retains its ungated same-side return to
5-06, but crossing to the canonical region requires `rr_lever`. The reverse
crossing has the same requirement. Lever check and activation event remain on
the right. The existing physical-room check sink credits either arrival without
connecting the sides. Area Key requirements continue to be applied separately.

## Tester seed status

Supplied screenshots show the Carrot wall in the minimized required playthrough
and the Radish wall at Room 1-41 outside it. They do not supply a seed identifier,
full options, or all placements. This confirms an incorrectly credited route,
not that the seed cannot be completed. An independently reachable Room 1-41 or
alternate valid Radish ingress may rescue it. Exact seed completion remains
unverified until its original generation data can be checked. No screenshot,
private conversation content, or full ROM is included in this change.

## Validation at the proposed change

- USA-ROM static verifier passed: closed component sizes 12/54; opened-grid
  connectivity restored.
- 167 focused tests passed across `test_radish_lever_compartment`, `test_rules`,
  `test_lever_items`, `test_area_keys`, `test_area_keys_option`,
  `test_snapshot_outputs`, and `test_room_sanity_reachability` (including its
  original reported generation-seed regression).
- Updated the expected compiled-region count by two (Carrot-side compartment
  and singleton physical-room sink) and regenerated the slot-data snapshot.
- See the later bounded native gameplay comparison below; tester-seed completion remains unverified.

## Bounded native gameplay comparison (2026-11-13)

See `radish-lever-native-20261113.json`. Two ordinary generated seeds used the
same gameplay options and starting inventory except the Radish wall item,
with separate blank saves and legitimate local-server/shipping-client delivery.
No post-patch ROM edits, forced coordinates, injected checks, or fabricated
received items were used. Seeds differ, so this is not a bit-identical seed
comparison; the replayed room/position approach checkpoints match exactly.

- Seed 109314, Radish wall absent: Carrot chute arrival in native 619 at
  (56,56.996). Holding right for 120 frames stops at x73.996 before the x80
  wall. A further 120-frame up/right attempt also remains at x73.996.
- Seed 109315, Radish wall received as an ordinary configured starting item:
  the same arrival and 120-frame right input crosses to x217.996.
- Screenshots visibly confirm the closed barrier and its absence respectively.
  The two states retain the ability gained during ordinary gameplay; this is
  directional movement testing, not attack/bypass testing.
- All stage processes and both local servers exited successfully; dependency
  pins remained unchanged and the exclusive native lock was released.

CI additionally caught the new compartment missing from the explicit native-room
map and two stale expected counts. Added the alias to native room 619, regenerated
the mapping table, and corrected counts (384 compiled regions, 353 native mapped
definitions). All 457 tools-policy tests pass after these metadata corrections.
