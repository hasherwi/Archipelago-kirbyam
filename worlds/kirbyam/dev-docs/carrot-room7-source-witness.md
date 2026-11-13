# Carrot Room7: original-source Room5 witness

Fresh-boot continuous positive and matched control, reviewed 2026-11-09. The
positive takes the actual native170→719 transition, acquires Beam from an original
Waddle Doo, carries it to the recessed gate and enters native734 at frame3242.
Beam remains held, and every-frame HP checks1085–3242 have minimum6 in both runs.
No enemy substitutions, runtime writes, state restores or damage requirement.

Startup is redirected near the doorway in native170, AP
`REGION_CARROT_CASTLE/ROOM_5_05`. Its existing outgoing Room7 edge is ungated.
The actual transition reaches719 at (680,456.99609375), matching spawn tiles(43,29).
This is not a replay of reaching Room5 from game start or from every incoming
position; the rule retains independent access to that existing AP room.

Normal Kirby acquires the lower Waddle Doo at (568,456), template0x008D3BF4.
The Beam-specific carry uses ladders, crouch slides through the central Gordo
lane, and an attack on Big Waddle Dee before taking the left ladder to the gate.
At frame2971 Kirby reaches the tested left-facing pose (86,232.99609375).
The bomb at(1,14) becomes FF at frame2996 and all fifteen linked F2 cells clear.
The door enters734 at (200,216.99609375), its lower1-Up compartment. No reward is
collected, and the upper Secret Notes compartment is not part of this witness.

The matched control changes only the final90-frame gate B input at2971 to neutral.
It retains F1 and all F2 cells, stays719, and also retains Beam/6HP. This supports
the particular door action, not a global Beam range or an exhaustive ability test.

[Compact acceptance manifests](carrot-room7-source-acceptance.json) include both
runs' identities, startup-only changes, input/trace hashes, source and actual
arrival, checkpoints, gate outcome and every-frame health checks. Full controller
traces, validation script and private screenshots remain local.

## Installed scope

Only guaranteed WADDLE_DOO→Beam assignments install the gate, using the lower
native instance and Room5 entry. The rule targets the **normalized** entrance
`ROOM_5_07 → ROOM_5_13__LOGIC__ENTRY_FROM_5_07`, rather than a nonexistent raw
Room13 entrance. Beam is not gateable in the ROM and does not require an item.

The other Room7 exits, cherry chest and RoomSanity remain unchanged, as does
Room14's route into the separate Secret Notes compartment. Unsupported source
assignments retain prior behavior and remain unresolved; no optional bypass or
finite random-roll guarantee is invented.
