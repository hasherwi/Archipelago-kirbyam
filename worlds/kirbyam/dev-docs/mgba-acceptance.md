# Standalone mGBA acceptance — issue #941

Status: **draft / runtime unrun**. Do not mark support complete from a boot screen,
host mocks, syntax checks or the historical #876 report. Do not enable dormant
Carrot Music Sheet 6 as part of emulator support.

Record exact repository commit, adapter SHA-256, AP/APWorld version, mGBA version,
platform/architecture, scripting build features, options and test seed identity.
Use the supported USA base ROM privately; publish no ROM, save or auth-token data.

## Isolation

Create a fresh directory per seed/team/slot and a uniquely named patched ROM;
point mGBA's save/state paths to that directory before starting. Verify the chosen
save path in mGBA, and record it only in private evidence. Do not copy an old save
or load a state from a different ROM. Native SRAM has no AP seed identity: changing
a filename alone does not make an existing save safe. Close the connector before
changing ROMs, and restart client/emulator for another seed/team/slot.

## Automated checks

- Python: `python -m pytest worlds/kirbyam/test/test_mgba_launch.py worlds/kirbyam/test/test_bizhawk_patch_preflight.py worlds/kirbyam/test/test_client.py worlds/kirbyam/test/test_start_inventory_protocol.py`.
  Covers launch selection, ROM rejection, existing delivery/check/reconnect and
  Dark Mind 9999/10000 goal handling with mocked BizHawk memory.
- Syntax: `luac -p data/lua/connector_bizhawkclient_mgba.lua`.
- After approval to execute the reviewed adapter, from repo root:
  `lua worlds/kirbyam/tools/test_mgba_connector.lua`.
  Exercises fragmented/coalesced input, partial/would-block output, version,
  system/hash, ROM offsets, bus reads/writes, guard rejection, display, malformed
  traffic, disconnect/reconnect, lock release, idle timeout and port exhaustion.
  No ROM or real socket is used. Passing does not establish native timing.

Current implementation check: **238 Python tests passed** in the four-file command
above; adapter and host-harness Lua syntax checks passed. After execution approval,
the bounded host harness **passed under Lua 5.1.5**, using mocked memory, sockets
and time only. Its notification assertion verifies a text-print call, not real
mGBA GUI rendering or in-game OSD.
No additional emulator build was installed or launched for this change.

## Real runtime matrix

Keep every row UNRUN until observed; use PASS/FAIL/BLOCKED with evidence references.
Do not substitute injected emulator RAM values for physical gameplay.

| Case | Observation required | Status |
| --- | --- | --- |
| Fresh setup | Patched USA ROM opens, connector version 1 connects, Kirby handler validates, correct AP slot authenticates | UNRUN |
| Wrong/unpatched ROM | Clear rejection without AP authentication or item writes | UNRUN |
| Missing modules/build feature | Clear setup error; no false connected/supported claim | UNRUN |
| Incompatible connector | Version mismatch disconnect; missing domain/command reported | UNRUN |
| Notification display | With the Archipelago Connector scripting panel visible, verify plain-text notices and the separate AP client log; no item colors/icons/position/timed fade or game-image OSD parity is implemented by this adapter | UNRUN |
| Native item receipt | Representative consumable, trap, shard, map, paint, sheet, unique Vitality apply once with mailbox ACK | UNRUN |
| Safe deferral | Item queued during title/menu/death applies only in supported gameplay state | UNRUN |
| Physical checks | Small chest, map/tutorial, Vitality, Sound Player reach server and become acknowledged | UNRUN |
| AP reconnect | Disconnect room server during collection/delivery; recover saved checks and reconcile full history without duplicate effects | UNRUN |
| Emulator reconnect | Close/reload connector with incomplete traffic and pending ACK; reconnect cleanly and preserve intended receipt accounting | UNRUN |
| Reset/save reload | In each native save slot, allow guarded native save, cold restart and replay; ownership/physical checks recover | UNRUN |
| Cross-session isolation | A fresh second seed/team/slot uses an empty independent save and correct ROM auth; no prior checks/deliveries | UNRUN |
| Dark Mind/credits | Goal and remaining checks reach server; verify post-credits/reconnect handling from historical #876 scenario | UNRUN |
| BizHawk comparison | Repeat representative item/check/reconnect/goal cases with existing connector | UNRUN |

Immediate power loss before native save and arbitrary process loss between a
consumable effect and durable receipt remain outside the proven guarantee. See
`chest-native-save-acceptance.md` for actual guarded native save timing. A connector
must not compensate by writing guessed SRAM/checksum offsets.
