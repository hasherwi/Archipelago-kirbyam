# KirbyAM APWorld Changelog

## Unreleased

- Integrate `ai_kirby_state_native` (0x0203AD2C, u32) for native goal detection.
  - Dark Mind goal triggers on AI state 9999; 100% goal triggers on state 10000.
  - Replaces temporary client-side heuristic with native signal polling.
  - Adds `_native_goal_signal_seen` latch to avoid missing transient state.

## v0.0.1

- Establish tag-driven draft GitHub release publishing for `kirbyam.apworld`.
- Align the world manifest version to `0.0.1`.
- Document maintainer release steps and validation checklist.
