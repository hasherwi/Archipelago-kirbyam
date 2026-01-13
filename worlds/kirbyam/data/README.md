# Kirby & The Amazing Mirror – Canonical Data

These YAML files are the canonical, version-controlled datasets for this world.

- `items.yaml`: item definitions
- `locations.yaml`: location/check definitions
- `goals.yaml`: goals/events definitions

Notes:

- These files should remain stable and reviewable (small diffs, sorted by `key`).
- Addresses are stored per localization (`na`, `eu`, `jp`, `vc`) and may be `null` until verified.
- Prefer adding fields rather than changing meanings of existing fields.

Conventions:

- Keep entries sorted alphabetically by `key`.

## Canonical Identifiers

Each entry includes:

- `key`: **canonical identifier**
- `name`: display name

### `key` (canonical)

- Stable, machine-facing identifier.
- Must be unique within its file.
- Must not be renamed after release.
- Must not be reused for different concepts.
- Keys should be lowercase snake_case (e.g., `defeat_dark_mind`).

`key` is the source of truth for deterministic numeric ID assignment.

### `name` (display)

- Human-facing string shown in Archipelago UI/spoilers.
- Must be unique within its file (Archipelago uses `name -> id` mappings).
- May be adjusted for clarity/typos, but changing names can break external expectations (trackers, documentation).
