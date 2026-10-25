# Kirby workflow executable inputs

Partial #981 coverage, restricted to `.github/workflows/kirby*.yml`.
The committed action-pins.json records exact commits resolved from upstream v6
(checkout/setup-python) and v4 (upload/download-artifact) on 2026-10-25.
Their action.yml entrypoints use bundled JavaScript (node24 for checkout/setup-python,
node20 for upload/download-artifact), with no composite nested `uses` entries.
The committed dist bundles are therefore covered by the Git commit identity;
this audit is not proof that those bundles are free of vulnerabilities.

Run `python worlds/kirbyam/tools/check_action_pins.py` before proposing changes.
Unknown actions, local actions, containers, mutable tags and changed commits require
an explicit inventory review; the checker rejects them by default. Refresh a pin
only in a reviewed PR after inspecting upstream changes, action.yml and transitive
network/executable inputs. Never auto-resolve a tag during the workflow.

Remaining executable inputs: setup-python selects downloadable interpreter builds
from its release manifest; ubuntu-latest and self-hosted Windows are not immutable
images; apt installs ARM gcc/binutils/make; generation/flaky/BizHawk install Python
requirements. Pinning actions does not pin these inputs. The smoke runner's installed
BizHawk/runtime is owner-managed and its isolation has not been established here.
The vendored generation fuzzer's existing checksum remains unchanged.

Global LLVM, GoogleTest helper, Enemizer/SNI/VC redistributable, AppImage controls,
full-app container images and workflows are outside the owner's Kirby-only boundary.
No global checksum controls were relaxed. No claim of full #981 completion is made.
