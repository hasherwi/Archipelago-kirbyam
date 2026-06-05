# KirbyAM Dev Docs - Start Here

This folder is the entry point for KirbyAM world and client internals.

## Quick map

- Runtime check flow by location type: see runtime-location-checks.md
- Runtime item injection and native reward interception: see runtime-item-delivery-and-native-intercepts.md
- Full protocol contract (mailbox fields, ACK behavior, transport registers): see ../../PROTOCOL.md
- Deeper architecture context and historical notes: see kirbyam-world-architecture-notes.md

## Read order for new contributors

1. runtime-location-checks.md
2. runtime-item-delivery-and-native-intercepts.md
3. ../../PROTOCOL.md
4. kirbyam-world-architecture-notes.md (only if you need background/legacy rationale)

## Scope of this mini-set

The two runtime reference docs above intentionally stay short and operational:

- What exact signal is read.
- Where the signal is written (native hook or AP transport register).
- Which client poll/delivery method consumes it.
- What behavior is intentionally suppressed from native game rewards in AP mode.
