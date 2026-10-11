# mGBA connector candidate for KirbyAM v0.4.0

This adapter lets standalone mGBA speak protocol 1 to Archipelago's existing
BizHawk Client. It is a draft integration for [#941](https://github.com/hasherwi/Archipelago-kirbyam/issues/941).
Full current-version runtime acceptance is outstanding. Keep using the established
BizHawk workflow if you need the existing support boundary.

## Provenance and license

Adapted from [Zunawe/bhc-substitutes](https://github.com/Zunawe/bhc-substitutes/blob/8954261f63f8032893b3a9a28a049a718ee480fc/mgba/connector_bizhawkclient_mgba.lua),
commit `8954261f63f8032893b3a9a28a049a718ee480fc`, source Git blob
`c384bdba030e9f0074741713133650a9a396bfaa`. Its in-file MIT copyright notice
(2023–2024 Zunawe) is retained; repository-level MIT notice (2026 Zunawe) is
included in `LICENSE.bhc-substitutes`. The existing AP `base64.lua` and `json.lua`
remain separate dependencies with their existing notices.

Local changes retain incomplete newline-delimited requests between callbacks,
queue partial/would-block sends, discard incomplete traffic and release locks on
disconnect/timeout, reject malformed streams, bound queued data to 1 MiB, and
restrict the port scan to the client's actual five ports. Bind/listen failures
close the candidate socket. Memory mapping and item semantics are unchanged.

The socket return conventions were checked against official mGBA 0.10.5
[`src/script/engines/lua.c`](https://github.com/mgba-emu/mgba/blob/0.10.5/src/script/engines/lua.c)
and [`src/script/socket.c`](https://github.com/mgba-emu/mgba/blob/0.10.5/src/script/socket.c).

## Required features and limitations

- Upstream minimum: mGBA 0.10.0+, with the scripting UI, Lua and built-in socket API.
  A standalone core library or a build without Tools > Scripting is insufficient.
- Use the **KirbyAM mGBA Client** Launcher component, or
  `python -m worlds.kirbyam.mgba_launcher` from source. It exports this APWorld
  resource, its notices and AP's existing `base64.lua`/`json.lua` into the directory
  printed in the client log. Load that exported script. `--connector-dir` selects
  a fresh destination; differing existing files are preserved rather than replaced.
  The standard BizHawk client and patch association remain unchanged.
- One mGBA connector instance at a time. The upstream cross-instance binding
  limitation is not solved by this adaptation. Close competing BizHawk connectors too.
- `ROM` is mGBA `cart0` with ROM-relative offsets; `System Bus` uses full GBA
  addresses. These are the only memory domains Kirby's client currently uses.
- Guards and their following operations are processed together in one callback;
  a failed guard suppresses the rest of that batch.
- Known notification limitation in this v0.4.0 integration: display messages are
  plain text in the **Archipelago Connector** scripting panel, not an overlay on
  the game image. Keep that panel visible to see notices. There are no item colors,
  icons, configurable screen position or timed fade; this does not match BizHawk
  in-game OSD behavior. Normal AP server messages remain separately in the AP
  client/log, without guaranteed replay of a missing delivery notice. This scopes
  the limitation to this adapter, not to all mGBA versions or possible overlays.
  `SET_MESSAGE_INTERVAL` and unmapped domains are unsupported; Kirby does not
  currently require them. Unsupported commands return an error.
- ROM change detection returns a CRC32 token instead of BizHawk's hash. Kirby
  still independently checks USA header fields, patch metadata and hook bytes.
- This is an unauthenticated local memory-control interface. It binds only to
  `127.0.0.1:43055–43059`; do not expose or forward it to other machines. The
  adapter itself makes no outbound connections and performs no file/save writes.
  Its two `require` calls load the adjacent AP modules. mGBA owns normal saving;
  the AP client separately connects to the room server.

## Validation status

Python launch/client regression tests and Lua syntax checks cover source changes.
The host harness `worlds/kirbyam/tools/test_mgba_connector.lua` exercises the actual
adapter with mocked memory, sockets and time. After execution approval it passed
under Lua 5.1.5, including the notification text-print call. It did not test the
real scripting GUI, notification appearance, emulator, native saves or gameplay.
No mGBA version/platform combination is yet certified for this v0.4.0 integration.

The [historical #876 closing report](https://github.com/hasherwi/Archipelago-kirbyam/issues/876#issuecomment-5138157837)
was posted July 31, 2026 and describes a June 24 adapter with APWorld 0.3.0-rc2:
goal completion and remaining checks worked there. It does not validate this
candidate. See `worlds/kirbyam/dev-docs/mgba-acceptance.md` for current acceptance.


## Repository scope

All source, resources, tests and documentation for this integration live under
`worlds/kirbyam`. The world registers an opt-in component through AP's existing
`LauncherComponents` hook and reuses the existing `BizHawkClientContext` and game
watcher without editing or monkeypatching shared modules. Shared transport log
messages retain the BizHawk name. ROM preflight is world-local.

The five exported runtime files are materialized because mGBA needs ordinary Lua
files outside the APWorld ZIP. Their user-selected/default output directory is
runtime data, not a source-tree modification. AP's standard Lua helper files are
read and copied without altering their originals.
