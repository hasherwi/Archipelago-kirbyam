# Universal Tracker

KirbyAM already worked with Universal Tracker's YAML-based regeneration for some
settings. Issue #1032 concerned the underlying Rainbow Route chest rule, not a
missing tracker client. The schema-1 integration restores the generated slot's
settings and enemy policy before constructing its regions and rules. It does not
replace those rules or introduce an independent tracker logic model.

## Versions and workflow

Validation baseline: KirbyAM APWorld **0.5.1**, repository main
`5fe94b87172416ef4fefef37df1179816d1e3a60`, with the changes in this PR;
Archipelago **0.6.8** from that repository; Universal Tracker **v0.3.8**, upstream
`FarisTheAncient/Archipelago` tracker branch commit
`d923c759a6e1a5e318635422fce0d47edcff06cb`; Python **3.13**.
This is source validation of the proposed integration, not a claim that the
previously released 0.5.1 APWorld contains it.

1. Install Archipelago with its generator, Universal Tracker, and a KirbyAM
   APWorld containing this integration. Use matching Kirby world logic on the
   generator and tracker machines.
2. Generate a new seed. Its slot data must contain `tracker.version: 1`.
3. Launch **Universal Tracker** separately from the Archipelago Launcher and
   connect to the room with your slot name and password if required. A player
   YAML is not required for these new slots. Keep the game client connected as
   usual; UT receives inventory and checked locations from the server.
4. UT rebuilds the graph using resolved Kirby options, exclusion settings,
   configured boss, initial color, effective starting inventory, and the exact
   generated enemy ability policy. Weighted/random YAML values are not rerolled.
   Starting items subsequently come from the server's received-item history,
   including multiplicity; do not manually grant the same starting abilities.

The current Kirby release has a fixed entrance topology. Area Keys, Hub
Connections, RoomSanity, enemy-source assignments and goal options change access
or enabled checks; there is no supported entrance-shuffle option to validate.
The exported `rooms`, `locations`, and `unique_items` remain available to other
trackers. UT uses the AP region/rule graph, rather than those display tables or
room telemetry, to calculate reachability.

## Older slots

Older slots lack the complete effective starting inventory and unambiguous
original option payload. This implementation rejects them with an actionable
error rather than advertising exact reconstruction. To keep using an old seed,
use its matching older APWorld with the original UT YAML workflow: put a YAML
with the exact resolved options in UT's configured players folder. Randomized
enemy assignments can still diverge in that older workflow; do not treat it as
validated exact support. Regenerate with schema 1 for YAML-less support. Unknown
future schemas also fail explicitly.

## Validation and limits

`test_universal_tracker.py` distinguishes source-only graph tests from optional
upstream UT tests. Without an installed `worlds.tracker`, the latter are skipped.
With the pinned upstream source installed they execute actual `TrackerCore`
initialization, `Generate`/`Main` generation, slot JSON serialization, YAML-less
regeneration, progression-sphere comparisons, received-item history, checked
location filtering and reconnect/replay. Source cases cover all four goals,
Area Keys on/off, RoomSanity on/off, ability policies off/shuffled/live-random,
resolved random options, graph topology and incremental progression inventories.

The opt-in live acceptance below additionally validates the real server socket
and UT client protocol. Neither suite validates the graphical Launcher/client,
UI goal presentation, or emulator behavior. UT core returns the reconstructed
state and events; the tests verify Kirby's completion condition against that
state. There is no Kirby-specific goal widget or embedded UT client here.

A RoomSanity + shuffled-source seed can be rejected by Kirby's existing all-check
validation because Room 4-16 has no qualifying source. That is a world-generation
restriction, not a UT reconstruction failure; these tests do not bypass it.

Phone coverage here concerns current main's `Cell Phone Battery` item and its
starting/received counts. The separate Phone PR #1086 is not included or modified;
its future item/logic changes require their own integration test after rebasing.

PopTracker is a separate product and pack/workflow. This document neither tests
nor changes PopTracker support.

References: [UT integration contract](https://github.com/FarisTheAncient/Archipelago/blob/d923c759a6e1a5e318635422fce0d47edcff06cb/worlds/tracker/docs/apworld-integration.md),
[UT setup](https://github.com/FarisTheAncient/Archipelago/blob/d923c759a6e1a5e318635422fce0d47edcff06cb/worlds/tracker/docs/setup.md),
[AP tools guide](https://archipelago.gg/tutorial/Archipelago/other_en).


## Live loopback acceptance

`test_universal_tracker_live.py` is an opt-in acceptance test using an actual
`MultiServer.Context` loaded from a freshly generated archive, its real WebSocket
server handler, and upstream `TrackerGameContext`/`CommonClient.server_loop`.
The game peer is a WebSocket protocol driver reporting generated location checks;
it is **not** a Kirby client or emulator. No protocol handlers, socket operations,
server responses, generation or tracker logic are mocked. Temporary configuration
selects headless operation, an empty YAML folder and isolated persistence.

Run with the UT source version specified above installed in `worlds/tracker`:

```sh
AP_TEST_WORLDS=kirbyam,tracker AP_RUN_UT_LIVE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
python -m pytest -p pytest_asyncio.plugin -m '' \
  worlds/kirbyam/test/test_universal_tracker_live.py -q -s
```

Loopback socket permission is required. The listener binds only `127.0.0.1:0`,
letting the OS atomically select an unused port. It never reuses or terminates
another server. Temporary generated output is not published; server saving is
disabled. The test closes its connections/listener and awaits both UT watcher
tasks created across reconnect.

The validated seed is **1054**, with shuffled enemy sources, random configured
boss and shards, configured-boss goal, two explicit Sword abilities, two Cell
Phone Batteries and Copy Ability Room Access. Observed results:

- Real YAML-less login and original starting inventory from `ReceivedItems`.
- **11 progression spheres**, exact equality of server-generation spheres and
  UT available checks, **124/124 location checks**, and **132 received items**.
- `RoomUpdate` removes checked locations from UT's available list.
- Reconnect receives a fresh index-0 history; the complete ordered `NetworkItem`
  sequence and checked-location set match the pre-disconnect state.
- Kirby completion is initially false and finally true in UT's reconstructed
  state. The actual server accepts the game peer's `StatusUpdate` with status
  **30 (CLIENT_GOAL)**. This is protocol/core goal validation, not observation of
  the GUI's Go Mode label or a native game win.

Graphical acceptance remains untested: this environment has no isolated Xvfb
executable, and the active desktop/emulator belongs to another task. The test
never launches a GUI or touches that session.
