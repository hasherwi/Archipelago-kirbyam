# Hub Teleport Trap (#697)

Hub Teleport Trap (item `3860041`) participates in the existing trap pool when traps are enabled. It returns the local single-player Kirby to Rainbow Route's central hub (native room `0x321`) using the native default spawn. Receiving it while safely in that room consumes it without another transition. Regenerate the ROM patch and use the matching client; older payloads do not implement this item.

The mailbox keeps the receipt pending during scripts, death, pause, demos, multiplayer, missing gameplay HUD, or an existing room transition. Subsequent items wait behind it. The client does not clear/reoffer this deliberately deferred receipt on its ordinary ACK timeout. Once native transition initiation succeeds, the counter advances once and the flag clears last. This acknowledges accepted initiation, not arrival. A reset after acceptance follows the existing transient receipt policy; an ambiguous process-loss receipt still requires the existing explicit recovery flow.

## Native evidence and implementation

The baseline is main `99c63e3a505131d5ab16db60350a4c9c9daae54d`. Existing trap implementation and receipt policy were reused. The local decompilation source (`kirby.c`, `code_080023A4.c`, `code_0800ECAC_2.c`, `main.c`, `task.c`, and layout headers) and the existing legally supplied USA ROM (MD5 `df5efe075b35859529ebf82a4d824458`) establish these contracts:

- `GetInput` begins at `0x08152694`; the existing mailbox hook at `0x08152696` runs before gameplay tasks. It deliberately leaves this new item unacknowledged.
- The one `GameLoop` call to `TasksExec` at `0x08151CF4` targets `0x08152CF4`. The wrapper calls the original scheduler once before attempting the pending trap. It does not hook other scheduler callers or mutate the scheduler's task list.
- `sub_080551FC` is the native guarded request: it rejects native freeze bits, dead Kirby, animation 39 or above 122, a non-null script pointer at Kirby `+0x110`, transition flags `0x3800B00`, same room, or missing eligibility bit `0x1000`. On success it sets the destination/spawn and enters `sub_0805545C`. These existing native routines own cleanup and transition sequencing.
- `sub_08002D40` retrieves the default room spawn from `gUnk_0893CB44`. The trap uses this lookup for `0x321`; it does not guess tile coordinates. Existing native AI return code also uses `sub_080551FC` with the same hub destination.
- The wrapper additionally requires ordinary AI state 300, one local human player, no demo/multiplayer flags, an active gameplay HUD and unpaused task execution. It applies the native readiness guards to the already-hub no-op too.

The patch builder validates the exact scheduler BL and SHA256 digests of the native request function, spawn lookup, and hub spawn entry before mutation. The dispatch body resides after the existing color code in the append-only ROM extension; a small main-window wrapper uses an ARM long call. The color marker and existing per-seed configuration addresses remain unchanged. No additional mailbox register, SRAM write, save format, progression grant, native door-unlock write, or full ROM is distributed.

## Validation and acceptance still needed

Host tests compile the actual payload C, substituting only native platform calls/register bindings. They cover pending-before-tasks behavior, active script after task execution, each readiness gate, native rejection/retry, already-hub handling, ordered duplicate traps, unknown IDs, and all five previous trap effects. Client tests cover prolonged deferral without clearing the flag, ordered following deliveries, and the existing cold-restart transient-receipt matrix. Item-pool tests retain existing IDs and challenge-mode exclusions while adding this trap.

The ARM payload and distributable BSDIFF patch are rebuilt against the local USA ROM. Local validation applies the patch back to that ROM, checks the hook target and payload bytes, and independently corrupts five guarded inputs to confirm rejection without mutation. These checks do not establish emulator gameplay stability.

Before closing #697, test the generated candidate ROM in an emulator: ordinary ground/air/water states and copy abilities; door, mirror and warp-star transitions; chest/lever scripts; boss defeat and shard cutscenes; pause/death/respawn; receipt during the hub; consecutive traps with following progression items; and save/reload/reconnect before and after acknowledgement. Verify arrival at the intended hub spawn, no lost collection events or ability/health changes, no duplicate receipt effects, and normal native save behavior. Multiplayer is intentionally deferred and is not claimed as supported trap execution.
