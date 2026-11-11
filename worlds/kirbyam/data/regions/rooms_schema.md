# rooms.json Schema

This document describes the canonical structure of `rooms.json`.

`rooms.json` is the source of truth for room-level topology and transition data in KirbyAM.
Room membership for AP locations is derived from `locations.json` parent-region metadata.

## File Shape

Top-level type:
- JSON object (`dict`)
- Keys: room region names (for example `REGION_CANDY_CONSTELLATION/ROOM_9_06`)
- Values: room definition objects

Example:

```json
{
  "REGION_CANDY_CONSTELLATION/ROOM_9_06": {
    "locations": [],
    "events": [],
    "exits": [
      "REGION_CANDY_CONSTELLATION/ROOM_9_CHEST_1",
      "REGION_CANDY_CONSTELLATION/ROOM_9_07"
    ],
    "room_sanity": {
      "included": true,
      "location_id": 3961231,
      "bit_index": 143
    },
    "transitions": [
      {
        "destination_room": "REGION_CANDY_CONSTELLATION/ROOM_9_CHEST_1",
        "source_coordinates": {
          "tile": {"x": 24, "y": 30},
          "world": {"x": 187, "y": 32}
        },
        "destination_coordinates": {
          "tile": {"x": 7, "y": 8},
          "world": {"x": 187, "y": 32}
        },
        "transport_type": "other",
        "friendly_name": "Candy Constellation 9-06 to 9-Chest 1",
        "ability_gate": "CanPoundPegs"
      }
    ]
  }
}
```

## Room Object Keys

Each room object contains:

- `locations` (optional compact form):
  - Type: `dict[str, requirement] | null`
  - Meaning: explicit location claims for split rooms. Omit it when ownership
    should be derived from `locations.json` `parent_region` metadata.
  - The reserved `room_sanity` key contains the usual room-sanity metadata.
  - Other keys are location keys and their values use the requirement grammar below.

- `events`:
  - Type: `list[str]`
  - Meaning: event names associated with this room.
  - Examples:
    - Empty room: `"events": []`
    - Lever room: `"events": ["Activate Lever - Moonlight Mansion 2-11"]`

- `exits`:
  - Type: `list[str] | dict[str, requirement]`
  - Meaning: destination room keys that are reachable from this room.
  - A list represents unconditional legacy adjacency.
  - A dictionary maps each destination to its access requirement. `null` means
    unconditional. Runtime and tracker consumers normalize both forms to a list.

- `exit_requirements` (optional compatibility form):
  - Type: `dict[str, requirement]`
  - Meaning: attaches conditions to selected destinations while retaining a
    list-shaped `exits` field.
  - Every key must also appear in `exits`.

- `room_sanity`:
  - Type: object with keys:
    - `included`: `bool`
    - `location_id`: `int | null`
    - `bit_index`: `int | null`
    - `core_landmark`: `bool` (optional; default `false`)
  - Meaning: room-sanity metadata for tracker/check integration.
  - Rooms marked `core_landmark` are stable area-hub visit checks that remain
    active when full Room Sanity is disabled. They reuse the same location ID
    and native `doorsIdx` visit bit when Room Sanity is enabled, so they are
    never duplicated.

- `transitions`:
  - Type: `list[transition_object]`
  - Meaning: directional transition details for exits from this room.
  - Rule: this contains per-path metadata such as coordinates, transport type, and optional gates.

- `logical_subregions` (optional):
  - Type: `dict[str, logical_subregion_object]`
  - Meaning: defines synthetic logic-only sections for this room while preserving a single room-sanity location on the canonical room key.
  - Use when one in-game room has disconnected internal segments that should not imply full traversal access.

- `logical_exit_overrides` (optional):
  - Type: `dict[str, str]`
  - Meaning: per-exit routing override from this room to a destination room's logical subregion.
  - Key: canonical destination room key from `exits`.
  - Value: logical subregion key declared under the destination room's `logical_subregions`.

### Logical Subregion Object Keys

Each logical subregion object contains:

- `exits`:
  - Type: `list[str]`
  - Meaning: adjacency list for the synthetic logic-only region.

- `locations`:
  - Type: `list[str]`
  - Meaning: optional location keys claimed by this logical subregion.

- `events`:
  - Type: `list[str]`
  - Meaning: optional event names claimed by this logical subregion.

## Transition Object Keys

Each transition object contains:

- `destination_room`:
  - Type: `str`
  - Must be one of the values listed in the room's `exits`.

- `source_coordinates`:
  - Type: object
  - Shape:
    - `tile`: `{ "x": int | null, "y": int | null }`
    - `world`: `{ "x": int | null, "y": int | null }`

- `destination_coordinates`:
  - Type: object
  - Shape:
    - `tile`: `{ "x": int | null, "y": int | null }`
    - `world`: `{ "x": int | null, "y": int | null }`

- `transport_type`:
  - Type: `str`
  - Typical values:
    - `other`
    - `hub mirror`
    - `regular two-way mirror`
    - `one-way mirror`
    - `mirra mirror`
    - `warp star`
    - `cannon`

- `friendly_name`:
  - Type: `str`
  - Human-readable directional label.

- `ability_gate` (optional):
  - Type: `str`
  - Present only when a path has a gate condition.
  - Example: `CanPoundPegs`.

## Default Semantics

- If a destination appears in `exits`, the transition is considered valid.
- A `null` or missing requirement is ungated.
- A string requirement is a named rule token.
- `{ "all": [...] }` requires every nested requirement.
- `{ "any": [...] }` requires at least one nested requirement.
- Ability-related tokens currently retain the existing permissive placeholder
  behavior. `mm_lever` requires the Moonlight Mansion 2-11 Lever Wall item.
- Gates are path-level (transition-level), not room-level.

## Invariants

Recommended invariants for data integrity:

- Every `transitions[].destination_room` is present in the same room's `exits`.
- Every `exit_requirements` key is present in the normalized `exits` adjacency.
- No duplicate transition entries for the same source->destination pair.
- `transitions` can be empty for rooms with no directional metadata.
- `exits` remains the authoritative adjacency list.
- `logical_exit_overrides` keys reference destinations already present in `exits`.
- `logical_exit_overrides` values reference logical subregion keys defined on the destination room.

## Notes

- `areas.json` defines high-level area graph connectivity.
- `rooms.json` defines room graph topology and directional path metadata.
- Transition gating logic should read from `rooms.json` transition entries, not a separate transitions dataset.

### Underwater and finite projectile route fields

A reviewed route may specify `water_state: "dry"` (default) or `"swimming"`.
Swimming resolves native attack dispatch without replacing carried equipment;
Mini has no swimming attack and must be dropped separately. The
`underwater_block_hit` capability requires swimming state. `metal` remains a
material capability, not proof of a particular barrier's geometry.

`frozen_enemy_hit` requires `uses_object` naming a one-use placement identity at
the route's source and a nonempty `frozen_enemy_evidence` string documenting the
freeze/kick/target sequence. It cannot have `opens`, refer to renewable sources,
or be applied through an unrelated capability. No implicit object refresh is
supported. Room-local consumption prevents swallowed or fired targets from
being reused.

A target may specify `requires_guaranteed_source` with a valid swallowable
`source_key` and a non-Normal `ability` name. For example, the conditional Goal 2
witness uses `MR_FROSTY` and `Ice`. Both feasibility and rule installation skip
this partial witness unless the finalized source policy unconditionally grants
that ability. Unsupported configurations preserve prior behavior and remain
unvalidated; this condition does not assert they are impossible or safe.

### Reinforced barriers and Heave-Ho movement

The `reinforced` target kind records reviewed environmental traversal witnesses.
It does not infer a gate from every native `0xF7` tile: that collision class also
backs crumbling platforms and cannon paths. Ordinary `metal` providers must not
be used to clear this separate class.

A `heave_ho_pull` route is one directed, dry, same-room sequence using Normal
suction to move the identified Heave-Ho into its reviewed disposal path. It needs
nonempty `heave_ho_evidence` identifying the object, accessible approach and
resulting clearance, in addition to the usual route evidence. There is no
ability item or randomized enemy source for this mechanism. Carried abilities
must be dropped before this sequence, so they are not silently preserved.

No `opens` event is exposed by this route: the graph records the one-way action
and resulting compartment, without granting persistent switch credit or an
unreviewed reverse path. Native disposal persistence is a separate fact from
room-instance lifetime. A partial pull that permits jumping over the object is
not evidence that reinforced tiles were destroyed. The existing Olive Ocean
Room 6 Mini/drop/recovery witness remains independent of full disposal.

### Ordinary-metal atomic witnesses

The `metal` target kind uses the shared target installer, source policy and
finite-state planner. Both `metal` and `metal_throw` routes require an explicit,
unique `allowed_abilities` list and a `metal_evidence` object whose keys exactly
match that list. Each value is a nonempty evidence reference for that provider's
move, approach/capture position, direction, clearance, charge, and water state
at initiation and impact. A shared acceptance-record link can avoid repeating
long explanations. Validation checks provider attribution, not native physics.

`metal` is a direct attack by a reviewed subset of Burning, Hammer, Stone,
Missile, UFO, Smash and Master. Throw is still one of the eight metal-breaking
abilities, but belongs exclusively to `metal_throw`, which additionally needs
`uses_object` and `throw_evidence`. The named one-use enemy must be in the capture
compartment, with its availability requirements met. Swallowing that same enemy
for an ability and throwing it are mutually exclusive. Statues and enemies
explicitly excluded by the source registry are not admitted as ammunition.
Registry eligibility is necessary but does not replace Throw-specific capture proof.
Holding does not grant a walk, jump, remote capture or cross-room transport edge.
No implicit reset, persistent `opens`, or ammunition renewal is added for Throw.
Other object types require a separately reviewed future representation.

These are same-native-room atomic action sequences. Any door transition is a
separate edge, as is any independently proven return route. `water_state`
records attack initiation: swimming cannot initiate Stone, Missile or Throw.
A completed dry Stone transformation sinking into water or dry Missile launch
into water needs its own exact sequence evidence; neither creates a universal
swimming attack. No global facing, charge or movement-state dimension is added.
