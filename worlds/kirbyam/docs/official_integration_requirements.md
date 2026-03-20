# Official Archipelago Integration Requirements

This document captures the exact requirements for Kirby & The Amazing Mirror to be
officially supported in the [Archipelago](https://github.com/ArchipelagoMW/Archipelago)
repository, sourced from the official AP docs as of March 2026.

Primary sources:
- [`docs/adding games.md`](https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/adding%20games.md)
- [`docs/contributing.md`](https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/contributing.md)
- [`docs/tests.md`](https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/tests.md)
- [`docs/world maintainer.md`](https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/world%20maintainer.md)
- [`docs/style.md`](https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/style.md)

---

## 1. Code Style & Contributing Guidelines

From [`docs/contributing.md`](https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/contributing.md)
and [`docs/style.md`](https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/style.md):

- [ ] Follow the AP style guide: PEP 8, 120 characters per line, double-quoted strings, type annotations
- [ ] Use type annotations for function signatures, class members, and local variables where appropriate
- [ ] Prefer new-style type annotations (`dict[str, str | int]` over `Dict[str, Union[str, int]]`)
- [ ] Critical changes must have test coverage; unit tests must not fail or regress
- [ ] Support Python 3.11+ (the oldest supported version in Archipelago)
- [ ] Enable GitHub Actions in your fork so unit tests run automatically after pushing

---

## 2. World Structure — Hard Requirements

From [`docs/adding games.md`](https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/adding%20games.md):

### File Structure

- [ ] World folder exists at `/worlds/{game}/` (e.g., `/worlds/kirbyam/`)
- [ ] `/worlds/{game}/__init__.py` exists
- [ ] Every subfolder under `/worlds/{game}/` that contains `*.py` files also contains
      an `__init__.py` (required for frozen build packaging)
- [ ] At least one game-info doc named `{language_code}_{game_name}.md`
      (e.g., `en_Kirby & The Amazing Mirror.md`)
- [ ] At least one setup/tutorial doc (e.g., `setup_en.md`)

### World Subclass (`World`)

- [ ] A `World` subclass exists in the game folder (typically in `__init__.py`)
- [ ] `game` attribute is set to a
      [unique game name](https://github.com/ArchipelagoMW/Archipelago/blob/main/worlds/AutoWorld.py#L260)
      not already used by any other world in Archipelago
- [ ] A `WebWorld` subclass instance is assigned to `web`, with:
  - [ ] `tutorials` list pointing to each setup/tutorial doc included in the game folder
  - [ ] `game_languages` list overriding the default if docs exist in more than one language
- [ ] `item_name_to_id: dict[str, int]` mapping — every item name to a unique AP item ID
- [ ] `location_name_to_id: dict[str, int]` mapping — every location name to a unique AP location ID
- [ ] `create_item(name: str) -> Item` implementation that creates an item on demand (called
      by your code and by other Archipelago processes)
- [ ] At least one `Region` for the player to start from (the Origin Region, default name `"Menu"`)
- [ ] A non-zero number of `Location` objects added to regions
- [ ] A non-zero number of items added to `multiworld.itempool` **equal** to the number of locations
  - *In rare cases 0-location-0-item games exist, but this is extremely atypical*
- [ ] A
      [completion condition](https://github.com/ArchipelagoMW/Archipelago/blob/main/BaseClasses.py#L77)
      set for the player: `multiworld.completion_condition[self.player] = lambda state: ...`

---

## 3. World Structure — Encouraged Features

From [`docs/adding games.md`](https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/adding%20games.md):

- [ ] `get_filler_item_name()` implementation so the default (any item from `item_name_to_id`,
      including non-repeatable ones) is not used
- [ ] `options_dataclass` defining player options, with a matching `options` type hint
- [ ] A
      [bug report page](https://github.com/ArchipelagoMW/Archipelago/blob/main/worlds/AutoWorld.py#L220)
      in `WebWorld`
- [ ] A list of
      [option groups](https://github.com/ArchipelagoMW/Archipelago/blob/main/worlds/AutoWorld.py#L226)
      for better organization on the webhost
- [ ] A dictionary of
      [options presets](https://github.com/ArchipelagoMW/Archipelago/blob/main/worlds/AutoWorld.py#L223)
      for player convenience
- [ ] A dictionary of
      [item name groups](https://github.com/ArchipelagoMW/Archipelago/blob/main/worlds/AutoWorld.py#L273)
      for player convenience and cross-game hints
- [ ] A dictionary of
      [location name groups](https://github.com/ArchipelagoMW/Archipelago/blob/main/worlds/AutoWorld.py#L276)
      for player convenience and cross-game features

---

## 4. World Structure — Prohibited Behaviors

From [`docs/adding games.md`](https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/adding%20games.md):

- [ ] Items submitted to `multiworld.itempool` must **not** be manually placed by the World (use
      `place_locked_item` or other placement methods instead; do not add pre-placed items to the pool)
- [ ] Do **not** use `eval` (security concern)
- [ ] Do **not** use `yaml.load` directly; use `Utils.parse_yaml` instead (defaults to safe loader
      and faster C parser)
- [ ] Do **not** use `=` when submitting to `multiworld.regions` or `multiworld.itempool`; use
      `append`, `extend`, or `+=` to avoid overwriting other games' data

---

## 5. Testing

From [`docs/tests.md`](https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/tests.md)
and [`docs/contributing.md`](https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/contributing.md):

- [ ] A `test/` package exists under the world folder with an `__init__.py`
- [ ] A `WorldTestBase` subclass (typically in `test/bases.py` or a non-`test_*.py` file) sets
      `game = "Kirby & The Amazing Mirror"`
- [ ] The three default `WorldTestBase` tests pass:
  - [ ] `test_all_state_can_reach_everything` — with all items, everything is reachable
  - [ ] `test_empty_state_can_reach_something` — with no items, at least something is reachable
  - [ ] `test_fill` — a valid multiworld can be completed with all generation steps called
- [ ] All generic tests in
      [`test/general/`](https://github.com/ArchipelagoMW/Archipelago/tree/main/test/general)
      pass for this world (run automatically against every world)
- [ ] Test files are named `test_*.py`, test classes are named `Test*` or `*Test`, and test
      methods are named `test_*`; test classes inherit from `unittest.TestCase` or a test base
- [ ] Individual tests take less than one second each
- [ ] Tests do not use `@pytest.mark.parametrize` (use the parametrization helpers in
      [`test.param`](https://github.com/ArchipelagoMW/Archipelago/blob/main/test/param.py) instead,
      since Archipelago tests are test-runner-agnostic)

---

## 6. Client Requirements — Hard Requirements

From [`docs/adding games.md`](https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/adding%20games.md)
(client section):

- [ ] Handle both **secure** (wss://) and **unsecure** (ws://) WebSocket connections
- [ ] Reconnect automatically if the connection is lost while playing
- [ ] Support changing the port for saved connection info (rooms may be moved to a new port)
- [ ] Send a
      [StatusUpdate packet](https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/network%20protocol.md)
      to the server when the player completes their goal

### Location Handling

- [ ] Send a network packet to the server when a location is checked in-game
- [ ] If location checks occurred while the client was disconnected (and the in-game action can
      only be taken once), re-send those checks on the next connection (e.g., by reading flags
      from game state or save file)

### Item Handling

- [ ] Receive and parse item packets from the server on demand (items can arrive from other
      players at any time)
- [ ] Reward items even when the game would not normally expect duplicates — **any** item can
      be received **any** number of times (starting inventory, item links, admin commands, cheating)
- [ ] Handle server-command items that have no player or location attributed to them
- [ ] Keep an **index** for items received in order to resync (`ItemsReceived` packets form a
      single ordered list)
- [ ] Receive items that were sent while the client was not connected to the server

---

## 7. Client — Encouraged Features

From [`docs/adding games.md`](https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/adding%20games.md):

- [ ] Define a custom **48×48 pixel** launcher icon (smaller/larger images are scaled) if the
      client appears in the Archipelago Launcher
- [ ] Add a `Component` to `LauncherComponents.components` with at least `display_name` and
      `func`; optionally add `supports_uri` + `game_name` for webhost link launching, `icon` +
      `description` for display, and `file_identifier` for launching by file

---

## 8. Pull Request Submission

From [`docs/contributing.md`](https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/contributing.md)
and the AP pull request template:

- [ ] Fork the official [ArchipelagoMW/Archipelago](https://github.com/ArchipelagoMW/Archipelago)
      repository
- [ ] Add the world under `/worlds/kirbyam/` in the fork
- [ ] Title the PR using the format:
      `"Kirby & The Amazing Mirror: implement new game"`
- [ ] Describe what was added and how it was tested in the PR body
- [ ] Attach screenshots if there are any graphical/UI changes
- [ ] Ensure all unit tests pass (GitHub Actions CI will run them)
- [ ] Do not introduce regressions in any existing world's tests

---

## 9. World Maintainer Responsibilities (post-merge)

From [`docs/world maintainer.md`](https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/world%20maintainer.md):

After the world is merged you automatically become a **world maintainer**. Ongoing responsibilities:

- [ ] Be on the Archipelago [Discord](https://archipelago.gg/discord) to receive updates on
      problems and suggestions for the world
- [ ] Review and decide on feature pull requests targeting the world
- [ ] Fix or point out issues when core Archipelago changes break the world
- [ ] Monitor GitHub for new pull requests (via Watch, `#github-updates` on Discord, or manual checks)
- [ ] Test the world on the `main` branch periodically, especially during RC (release candidate) phases
- [ ] Communicate long periods of unavailability to the core team
- [ ] Add yourself to
      [`docs/CODEOWNERS`](https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/CODEOWNERS)
      in the official repo PR
