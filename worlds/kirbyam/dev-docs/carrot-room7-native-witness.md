# Carrot Castle Room 7: recessed door to Room 13

## Verified result

**Beam opens the recessed mid-left Bomb Block and reaches native room734. Spark fails the tested standing and jumping attacks at the closest right face.** Original collision geometry also excludes direct Spark contact with this sealed target under ordinary movement: every origin close enough for its terrain-scanning bounds is inside solid/linked-block cells or outside the room.

This is a concrete reason not to add Spark automatically to every Beam gate. The conclusion concerns direct Spark activation of this closed gate, not glitches, teammate actions, alternate entrances, or other abilities.

## Correct gate and destination

- Source: native719, Carrot Castle Room7, 720×528 pixels.
- Target: **F1** Bomb Block at tile(1,14), x16–31/y224–239. The sealed 4×4 cluster spans tile columns1–4, rows11–14: one F1 and fifteen F2 cells.
- Revealed native door: object template 0x8d39d8, type0x6f, position **(24,232)**.
- Beam changes F1 to **FF**, not zero: FF is the revealed doorway. All fifteen linked F2 cells become zero.
- Walking left and pressing Up enters **native734 at (200,216.9961)**, through the lower compartment's door near (216,216).
- This is Room13's lower **1-Up compartment**. The experiment does not collect Room7's cherry chest or Room13's upper Secret Notes chest. No reward collection is claimed.

## Fresh-boot witnesses and controls

All accepted runs begin from a fresh FF battery save, use continuous controller input, and perform zero runtime memory writes or state restores.

| Run | Target result | Final room |
|---|---|---|
| Beam positive | F1→FF; all fifteen F2→00 | **734**, arrival frame1613 |
| Beam control, tested B inputs omitted | F1 and all F2 unchanged | 719 |
| Spark standing and jump+B | F1 and all F2 unchanged | 719 |
| Spark control, tested B inputs omitted | F1 and all F2 unchanged | 719 |

### Beam range boundary observed here

Facing left at **(86.0000,232.9961)**, hold B. The target first changes on attack frame25, global frame1367. Its nearest pixel edge x31 is **55 pixels** left of Kirby's origin; its center x24 is 62 pixels away. This is consistent with Beam's separate 55-pixel terrain-scanning leading edge, rather than its 59-pixel damage-hitbox envelope.

A preceding attack beginning at x87.7500, with the entire traced motion staying at or above x87.296875, leaves the target intact. Its closest observed distance to that tile edge is about56.297 pixels. This brackets the practical result at these measured positions; it is not an exhaustive subpixel search or a universal target-independent range claim.

### Spark evidence and geometry

The closest legal right-face origin is **(86.0000,232.9961)**. A 90-frame Spark hold fails. Releasing, jumping for 3 frames, and holding Spark for another90 frames also fails. Door-entry inputs still leave Kirby in719.

Using Spark's terrain-scanning bounds x±26, y−22..+30, overlapping the target tile requires an origin within approximately x−10..57/y194..261. The relevant in-room tile cells, columns0–3 and rows12–16, are all original solid0D, F1, or linkedF2 cells. Negative x lies outside the room boundary. Small coordinate-rounding differences do not change those occupied cells. Thus no ordinary pre-opening Kirby position can directly bring Spark's scan to this target; this is stronger than the two failed controller attempts alone.

The necessary-origin argument concerns the terrain scanner, not Spark's smaller damage hitbox. It assumes the ordinary collision/block rules and the cluster is still closed. Source-derived bounds should be kept alongside this room-specific geometry; this report does not claim global impossibility of reaching Room13 by every conceivable route.

## Fixture limitations and integrity

Private authorized USA source ROM SHA1: **274b102b6d940f46861a92b4e65f89a51815c12c**. The original file is unchanged.

Only these setup fields differ in the private fixture:

- Startup-room entries and startup coordinates, putting the controlled Kirby in native719 at (104,224).
- One native Chip template at 0x8d3924, originally (48,136), replaced by an ability essence at (96,216). Beam: type0x92/subtype0. Spark: type0x93/subtype2.

No attack code, terrain, HP, doors, rewards, or other objects are changed. Ability acquisition is controller-driven and settled for90 frames. Exact allowlisted byte diffs and ROM hashes are retained in every sanitized run manifest.

This proves native physical gate behavior, not a natural or randomized source path to Beam/Spark and not AP item-delivery acceptance. Ice, Smash, frozen-enemy projectiles, and other alternatives are untested in this room.

## Evidence manifest

[Runtime and geometry manifest](carrot-room7-runtime.json) retains the four controller runs, fixture differences, checkpoints, attack traces, outcomes, and scalar geometry. No full ROM, battery save, emulator state, or raw extracted map is published.
