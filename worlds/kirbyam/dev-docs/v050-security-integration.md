# v0.5.0 security and reconnect integration plan

The owner abandoned the unpublished v0.4.2 release on October 26, 2026. Its security content belongs in upcoming v0.5.0. This document is planning and source integration, not release acceptance. Removal of draft release 422918553 and tag `kirbyam-v0.4.2` is a separate operation; do not infer deletion from this document. Preserve v0.4.1 and all source branches and commits. Do not merge the obsolete v0.4.2 version-only PR #984; select v0.5.0 metadata at the final integration stage.

## Source mapping

| Source | Content to retain | Boundary and pending work |
| --- | --- | --- |
| [#979](https://github.com/hasherwi/Archipelago-kirbyam/pull/979), `f1e6c60913f213e8ccd2a607adde0b502de84c7e` | SHA-256-pinned pip 26.2.2 / certifi 2026.10.19 bootstrap in four Kirby build/test workflows; optional dedicated-venv bootstrap and [trust guidance](../docs/python-trust-update.md). | Retained in this branch. Move notes to Unreleased; discard the abandoned version bump, not security source. #978 remains open: advisory/API and host remediation are broader than this patch. |
| Reconnect commit `214ba2db57413b4895980a7587b0f658dc2ac088` | mGBA transport reset and launcher wiring, protocol guidance and regression tests; one Unreleased reconnect note. | Integrated source from the preserved local `fix/kirbyam-mgba-reconnect` branch. Original handoff records 281 tests and actual stock Qt same-process reconnect after emulator restart/script reload. This is limited acceptance, not the complete runtime matrix. |
| [#989](https://github.com/hasherwi/Archipelago-kirbyam/pull/989), `e713cdd4ebe7e534b55c47e89633e3157a5fb803` | Verify exact bsdiff4 wheel inventory and SHA-256 before offline CPython 3.12/Linux x86_64 ROM-smoke installation. | Integrated in the local candidate; partial #980 coverage. Other Python/platform matrices, generation/flaky/BizHawk dependencies, hooks, interpreter inputs and apt/compiler remain unlocked. Preserve its reuse of #979 bootstrap. |
| [#990](https://github.com/hasherwi/Archipelago-kirbyam/pull/990), `e9a96981d2e0441f2158d7412628708ea10e50ba` | Exact action identities across five Kirby workflows, YAML policy checker and executable-input inventory, including #994 nested provenance actions. | Integrated in the local candidate; partial #981 coverage. Runner images, interpreters, apt, Python downloads and online OIDC/attestation services remain outside the action-pin contract. Preserve changes from #989 and #993/#994 when resolving workflows/changelog. |
| [#993](https://github.com/hasherwi/Archipelago-kirbyam/pull/993), `278f8e8a03d91f96f07c0996e9bf30f689d853c4` | Trusted-main authorization/source policy, protected tag and release environment, restricted publisher and self-hosted smoke boundary. | Integrated in the local candidate; partial #982 coverage. **Never enable standalone:** legacy prune/delete/`--clobber` requires replacement by #994. Tag/environment protections and runner isolation/ephemerality need owner verification. |
| [#994](https://github.com/hasherwi/Archipelago-kirbyam/pull/994), `ac63a2c17d3a3a06e6fe050d36a9f693b906e55b` | Stack on #993: source/run receipts, hashes, identity-constrained provenance verification, no-replacement draft staging and download readback. | Integrated in the local candidate; partial #983 coverage. Requires combined #993 + #994 and owner-verified protections plus server-side immutable-release enforcement. Source checks are not atomic; live signing, post-publication checks and concurrent publication enforcement remain unverified. |

Global AP requirements, Docker, general CI, frozen-app builders and host/OS trust remediation remain outside this Kirby-only work. Installing an APWorld updates neither host Python nor standalone/vendored certifi, pip or the OS trust store. Historical artifacts are not retroactively remediated or attested. Python 3.11 support is retained; the reported 3.13.16 launcher deadlock and a 3.13.17 embedded-pip security update must not be conflated.

## Local integration candidate

The isolated `integration/kirby-v050-hardening-20261026` branch starts at #979 head `e50e8e005b64382350706c6b6487d00d7f904af5` and merges the four reviewed heads above, with #993 preceding its #994 descendant. This preserves the reconnect fixes without applying them twice. The workflow resolution retains the verified wheelhouse install, pinned action identities, disabled checkout credentials, trusted-main authorization and #994 no-replacement staging. All four broad hardening issues remain open; integration is not release acceptance. The v0.4.2 release and tag were separately removed and verified; do not recreate them.

The candidate is local only. Update the existing drafts after reviewing its verification evidence; do not create duplicate PRs. Keep #994 based on #993, and deliver their publisher changes together. Owner protections, live signing, immutable release enforcement and the remaining runtime/platform matrix still require separate acceptance.

## Inherited limitations

Carry every v0.4.1 limitation into the final notes unless separately changed and validated:

- Progression remains broadly two spheres: almost the whole game is completable without received items except opening the Dimension Mirror and defeating Dark Mind. Planned progression work does not itself establish that this is fixed.
- Only the North American ROM is supported; AP notifications are English.
- Chest item sprites and collection animations remain original; statues retain their original ability appearance.
- mGBA notifications are plain text in the visible Archipelago Connector scripting panel, not game-image overlays.

Retain the uncertain-consumable-delivery and native-save-timing caveats. No exactly-once effects guarantee applies across arbitrary interruption or unsaved power loss. The reconnect evidence does not validate every item class, minor/Vitality/Sound Player chest, all native slots, offline checks, pending-ACK disconnect, goal completion or BizHawk parity. Earlier custom-health patches require regeneration; authoritative ownership still requires client reconciliation. Older cosmetic/lever limitations may be marked resolved only with their existing documented fixes and required regenerated patches, not by the version change.

## Integration and acceptance gates

1. Keep #979 bootstrap bytes, reconnect code/tests and the single reconnect changelog entry. Review the existing gameplay/progression PRs separately; do not duplicate their source or infer acceptance.
2. Integrate #989/#990 without losing either workflow change. Integrate #993 and #994 together, preserving no-replacement staging and #990's provenance-action inventory. Retain each PR's security limitations; #978 and #980–#983 remain open.
3. Re-run policy negative fixtures, release/package/source checks, focused reconnect tests and supported platform CI on the final combined commit. Prior uncommitted combination testing is evidence only for that tree.
4. Record remaining red gates accurately. Historical #979 CI had Ubuntu 3.11.2 setup, Windows 3.11 Kivy/EOF and Windows 3.13 OC2 fill failures; #990 also recorded a KH2 Valor-level assertion. #989/#993/#994 retained the two general setup failures. #994 lacked exact-head CodeQL. These results do not establish the status of a future combined head. Global repair #985 remains separate from this authorized scope.
5. Obtain missing runtime acceptance and verify final v0.5.0 version metadata/snapshots and generated notes. Do not reuse the abandoned candidate's “gameplay unchanged from v0.4.1” claim for v0.5.0.
6. Before any separately authorized publication, verify tag/environment protection, runner isolation, immutable releases, exact source identity, asset hashes and provenance. Skipped publisher jobs are not live signing/publication acceptance. No merge, public release, settings change, full ROM or secrets upload is authorized by this plan.
