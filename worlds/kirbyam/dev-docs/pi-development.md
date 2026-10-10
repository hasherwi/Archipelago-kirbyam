# ARM64 development on Raspberry Pi

The v0.4.0 Python tests and ARM7TDMI payload can be built on an ARM64 Linux
host. Host architecture and payload architecture are different: a native
`gcc` builds test helpers and `_speedups`, while `arm-none-eabi-gcc` builds
the GBA payload.

## Isolate the tools

Use a Python 3.11–3.13 virtual environment. Install the repository's Python
requirements and `ci-requirements.txt` there. On Python 3.13, keep
`setuptools>=75,<81` available for the existing `_speedups.pyxbld` distutils
import, and honor the repository's `cython>=3.2.4,<3.3` constraint.

On Debian ARM64, the official `gcc-arm-none-eabi` and
`binutils-arm-none-eabi` packages provide the cross-compiler. If system
package changes are being coordinated elsewhere, download and extract them
under a private workspace instead:

```sh
mkdir -p toolchain-debs toolchain
(cd toolchain-debs && apt-get download gcc-arm-none-eabi binutils-arm-none-eabi)
for package in toolchain-debs/*.deb; do
    dpkg-deb -x "$package" toolchain
done
export PATH="$PWD/toolchain/usr/bin:$PATH"
arm-none-eabi-gcc --version
```

This extraction does not resolve or install host-library dependencies.
Check that the compiler executes successfully on the host. Debian Trixie's
ARM64 GCC 14.2.1 and binutils 2.44 packages were exercised on harrison-pi.
Record package versions and SHA-256 hashes when preparing a new workspace.

## Validate from the repository root

With the virtual environment activated and compiler directory on `PATH`:

```sh
cythonize -b -i _speedups.pyx
python -c 'import _speedups; print(_speedups.__file__)'
SKIP_REQUIREMENTS_UPDATE=1 python -m pytest worlds/kirbyam/test -q
make -C worlds/kirbyam/kirby_ap_payload
python worlds/kirbyam/build.py --skip-patch --skip-install --non-interactive
```

Use the normal `python -m pytest` entry point. Launching pytest from Python
standard input breaks the hosting test's multiprocessing `spawn` entry
point. The fake BizHawk connector tests require ephemeral loopback sockets;
the hosting test starts a local MultiServer on port 38281. Run them with
local socket access and an unused port. A sandbox-denied socket is an
environment failure, not successful runtime acceptance.

`--skip-patch` verifies packaging with the checked-in base patch; it does
not rebuild that patch for new payload code. Run the workflow's deterministic
dummy-image smoke only in a disposable copy, because it replaces the base
patch. Its generated ROM, patch and APWorld are synthetic test artifacts
and must not be distributed as playable release outputs.

## v0.4.0 acceptance boundary

Preserve each PR head before combining feature changes for local validation.
The combined test overlay must include the ordinary chest room-counter fix
alongside reward suppression, and retain both fixed-collection and lever
headers/hooks when reconciling overlaps. Keep v0.5.0 area keys, hub connection
items and expanded room logic outside this overlay.

A successful Pi build or simulated connector test does not validate BizHawk
gameplay. The lawful USA-ROM rebuild, collection menus, levers, health,
ability gating, save/reload and reconnect acceptance remain required before
release. Music Sheet #6 stays dormant until native rooms 719, 720, 730 and
734 are reconciled against lawful ROM evidence. Follow
`v040-runtime-acceptance.md` from the runtime-regressions PR when testing
the combined tree.
