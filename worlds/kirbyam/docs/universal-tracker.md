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

This does **not** validate a live server socket, the graphical Launcher/client,
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
