# Rainbow Route East physical-switch reachability

## Reproduction

On main `6ae78a5`, the Rainbow Route East Big Switch
(location 3960411, transport bit 11) was attached to Rainbow Route East's hub
(`ROOM_1_HUB_1`, native room 190). Reaching that endpoint marked the switch
reachable even when Moonlight Mansion's Area Key was absent and its rooms were
unreachable. The endpoint contains the Rainbow Route map chest, not this switch.

The reported physical switch is in eastern Moonlight Mansion just before the
boss. The existing room map identifies that antechamber as `ROOM_2_10`, native
room 700. The location now belongs to that room and uses its existing traversal
requirements. This is not a new key-only location rule or a requirement to own
Moonlight's Hub Connection: overland access remains valid, and disabling Area
Keys still removes the key requirement.

The historical `Activate Big Switch - Rainbow Route East` area event moves with
its physical area. Its existing area-summary semantics are otherwise unchanged.
The display name and grouping tags continue to describe the unlocked shortcut.

## Compatibility

No location IDs, bits, item IDs, Hub contract mappings, protocol versions, saves,
client polling, ROM payload or binary patch change. In particular, native door
enum names and unlocked endpoint rooms are not evidence of switch position.
The historical catalog/runtime naming divergence documented in
`hub-native-layout.md` is not reconciled by this focused graph correction.

New generation and trackers loading this world data use the corrected graph.
An already generated seed's placement is not repaired retroactively by updating
a client. Do not promise that an existing seed becomes beatable without checking
its actual placements and inventory.

## Evidence and acceptance boundary

The false-positive is reproduced in executable APWorld tests in both RoomSanity
and ability-gating modes. Tests cover positive overland and Moonlight-shortcut
routes, Area Keys enabled/disabled, and blocking the pre-boss entrance despite
owning the key. Numeric transport identity is pinned.

The precise room selection follows the gameplay report, cross-referenced with
`dev-docs/native-room-wikirby-map.json` and the existing architecture note naming
Room 2-10 as the boss antechamber. No lawful original ROM was available on the
working executor, and the connected computer did not return the read-only file
probe. This change has **not** independently verified the switch's native object
record or traversed the route in an emulator. Verify that physical room before
promoting this draft for merge; a different room in Moonlight must be corrected
in the catalog and regression together rather than hidden behind a key-only gate.
