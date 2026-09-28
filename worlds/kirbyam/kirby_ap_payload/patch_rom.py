from __future__ import annotations

import os
import sys

import argparse
import hashlib
import importlib.util
import json
import multiprocessing as mp
from multiprocessing.queues import Queue as MultiprocessingQueue
import re
import shutil
import struct
import subprocess
import tempfile
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any, TextIO, TYPE_CHECKING, cast

_SCRIPT_DIR = os.path.realpath(os.path.dirname(__file__))
_WORLD_DIR = os.path.realpath(os.path.dirname(_SCRIPT_DIR))

if TYPE_CHECKING:
    shared_is_thumb_bl_instruction: Callable[[bytes], bool]
    shared_thumb_bl_bytes: Callable[[int, int], bytes]

# When patch_rom.py is executed from worlds/kirbyam/kirby_ap_payload, Python can
# still see the parent world directory early enough for worlds/kirbyam/types.py
# to shadow stdlib types during stdlib imports. Remove that parent world path.
for path_entry in list(sys.path):
    resolved = os.path.realpath(path_entry or os.getcwd())
    if resolved == _WORLD_DIR:
        sys.path.remove(path_entry)

try:
    from .thumb_branch import is_thumb_bl_instruction as shared_is_thumb_bl_instruction
    from .thumb_branch import thumb_bl_bytes as shared_thumb_bl_bytes
except ImportError:
    _thumb_spec = importlib.util.spec_from_file_location(
        "kirbyam_thumb_branch",
        Path(__file__).resolve().with_name("thumb_branch.py"),
    )
    if _thumb_spec is None or _thumb_spec.loader is None:
        raise SystemExit("Error: unable to load thumb_branch.py helper module")
    _thumb_module = importlib.util.module_from_spec(_thumb_spec)
    _thumb_spec.loader.exec_module(_thumb_module)
    shared_is_thumb_bl_instruction = _thumb_module.is_thumb_bl_instruction
    shared_thumb_bl_bytes = _thumb_module.thumb_bl_bytes

PAYLOAD_OFFSET = 0x0015E000
MAIN_HOOK_OFFSET = 0x00152696
BOSS_COLLECT_SHARD_CALL_OFFSET = 0x001D952
MINOR_CHEST_COLLECT_CALL_OFFSET = 0x0000AFEC
BIG_CHEST_COLLECT_CALL_OFFSET = 0x0000B144
VITALITY_CHEST_COLLECT_CALL_OFFSET = 0x0000B0CC
SPRAY_PAINT_CHEST_COLLECT_CALL_OFFSET = 0x0000B1D0
# This native callsite handles reward-index 0 (Sound Player unlock) and
# reward-index > 0 (Music Sheet collection rewards).
SOUND_PLAYER_CHEST_COLLECT_CALL_OFFSET = 0x0000B264
BIG_SWITCH_UNLOCK_CALL_OFFSET = 0x00039EEE
# sub_08119B3C: BL _call_via_r0 after resolving the small-switch effect function.
# Hook receives that function pointer in r0 and can suppress only the four AP levers.
SMALL_SWITCH_EFFECT_CALL_OFFSET = 0x00119B98
ORIGINAL_SPECIAL_DOOR_STATE_FN_ADDR = 0x08002BA8
EXPECTED_SPECIAL_DOOR_STATE_CALLSITES = 5
ORIGINAL_BUTTON_SPECIAL_TRANSITION_FN_ADDR = 0x0805BC78
EXPECTED_BUTTON_SPECIAL_TRANSITION_CALLSITES = 28
ORIGINAL_EXPLICIT_ROOM_TRANSITION_FN_ADDR = 0x080551FC
EXPECTED_EXPLICIT_ROOM_TRANSITION_CALLSITES = 8
ROOM_PROPS_TABLE_OFFSET = 0x009331AC
ROOM_PROPS_STRIDE = 0x28
ROOM_PROPS_DOORS_IDX_OFFSET = 0x24
ROOM_AREA_INFO_TABLE_OFFSET = 0x00D6CD0C
ROOM_AREA_INFO_AREA_OFFSET = 0x46
ROOM_AREA_INFO_COUNT = 1000
# In sub_0803FBB4, replace the retail collision-mask comparison and unk58 OR
# before any transition state is written. The following store at 0x0803FE20
# consumes the value returned by ap_prepare_automatic_transition.
AUTOMATIC_TRANSITION_GUARD_OFFSET = 0x0003FE10
AUTOMATIC_TRANSITION_GUARD_RETURN_ROM_ADDR = 0x0803FE5A
AUTOMATIC_TRANSITION_GUARD_ORIGINAL = bytes.fromhex(
    "82 20 40 03 86 42 20 D1 A8 6D 80 21 C9 01 08 43"
)
ORIGINAL_ABILITY_TRANSITION_FN_ADDR = 0x080547C4
# sub_08054C0C consumes Kirby::transitioningAbility after statues write it directly.
ORIGINAL_ABILITY_TRANSITION_START_FN_ADDR = 0x08054C0C
ORIGINAL_BOSS_ALREADY_OWNED_REWARD_FN_ADDR = 0x08088A38
EXPECTED_BOSS_ALREADY_OWNED_REWARD_CALLSITES = 8
# Two single-player gameplay-start calls in code_08123950.c. Both originally
# target sub_080332BC and must run the seed-color wrapper before CreateKirby.
ORIGINAL_START_GAME_FN_ADDR = 0x080332BC
STARTING_COLOR_START_GAME_CALL_OFFSETS = (0x00123EF2, 0x00124022)


ROM_PATH_TMP = "rom_path.tmp"
INTERMEDIARY_ROM = "baseline_patched.tmp.gba"
EXPECTED_BASE_ROM_SIZE = 0x1000000
BSDIFF_TIMEOUT_SECONDS = int(os.environ.get("KIRBYAM_BSDIFF_TIMEOUT_SECONDS", "0"))
BSDIFF_HEARTBEAT_SECONDS = int(os.environ.get("KIRBYAM_BSDIFF_HEARTBEAT_SECONDS", "30"))


# ----------------------------
# Logging (tee stdout/stderr)
# ----------------------------
class Tee:
    def __init__(self, *streams: Any) -> None:
        self.streams = streams

    def write(self, data: str) -> None:
        for s in self.streams:
            s.write(data)
            s.flush()

    def flush(self) -> None:
        for s in self.streams:
            s.flush()


def get_fixed_patch_out() -> Path:
    # patch_rom.py is in .../worlds/kirbyam/kirby_ap_payload/
    # world root is .../worlds/kirbyam
    world_root = Path(__file__).resolve().parent.parent
    return world_root / "data" / "base_patch.bsdiff4"


def get_log_path() -> Path:
    # Create the log file next to this script (same directory)
    script_dir = Path(__file__).resolve().parent
    return script_dir / "patch_rom.log"


def setup_logging() -> Path:
    log_path = get_log_path()
    # Append to preserve prior runs
    log_f = log_path.open("a", encoding="utf-8", newline="\n")
    header = (
        "\n"
        "============================================================\n"
        f"patch_rom.py run: {datetime.now().isoformat(timespec='seconds')}\n"
        f"Working dir: {Path.cwd()}\n"
        f"Args: {sys.argv}\n"
        "============================================================\n"
    )
    log_f.write(header)
    log_f.flush()

    # Tee both stdout and stderr to the same log file
    sys.stdout = cast(TextIO, Tee(sys.__stdout__, log_f))
    sys.stderr = cast(TextIO, Tee(sys.__stderr__, log_f))

    # Store handle so it stays open for duration
    return log_path


def run_make() -> None:
    """Run `make clean` then `make` in the current working directory."""
    for cmd in (["make", "clean"], ["make"]):
        print("Running:", " ".join(cmd))
        try:
            result = subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            if result.stdout:
                print(result.stdout.rstrip())
        except FileNotFoundError as e:
            raise SystemExit(
                "Error: 'make' was not found on PATH.\n"
                "Install build tools (e.g., GNU Make) or run this script in an environment where `make` is available."
            ) from e
        except subprocess.CalledProcessError as e:
            output = (e.stdout or "").rstrip()
            # Some Windows make setups do not provide `rm`, causing only the
            # clean target to fail. Continue to `make` in that case.
            if cmd == ["make", "clean"] and (
                "rm -f" in output
                or "CreateProcess(NULL, rm -f" in output
                or "cannot find the file specified" in output.lower()
            ):
                print(
                    "Warning: `make clean` failed because `rm` is unavailable "
                    "in this environment; continuing with `make`."
                )
                if output:
                    print(output)
                continue
            raise SystemExit(
                f"Error: command failed: {' '.join(cmd)}\n"
                f"{output}"
            ) from e


def _find_arm_binutil(tool_name: str) -> str:
    direct = shutil.which(tool_name)
    if direct:
        return direct
    exe = shutil.which(f"{tool_name}.exe")
    if exe:
        return exe

    # Check devkitPro environment variables before falling back to a hardcoded path.
    attempted: list[str] = []
    for env_var in ("DEVKITARM", "DEVKITPRO"):
        env_val = os.environ.get(env_var)
        if not env_val:
            continue

        # DEVKITARM points directly at the devkitARM prefix; its binaries live in <DEVKITARM>/bin.
        # DEVKITPRO is the devkitPro root; the standard layout is <DEVKITPRO>/devkitARM/bin.
        # Also check <DEVKITPRO>/bin in case of a non-standard installation.
        if env_var == "DEVKITARM":
            base_paths = [Path(env_val) / "bin"]
        else:
            base_paths = [
                Path(env_val) / "devkitARM" / "bin",
                Path(env_val) / "bin",
            ]

        for base in base_paths:
            candidate = base / f"{tool_name}.exe"
            attempted.append(str(candidate))
            if candidate.exists():
                return str(candidate)
            candidate_no_ext = base / tool_name
            attempted.append(str(candidate_no_ext))
            if candidate_no_ext.exists():
                return str(candidate_no_ext)

    if os.name == "nt":
        fallback = Path("C:/devkitPro/devkitARM/bin") / f"{tool_name}.exe"
        attempted.append(str(fallback))
        if fallback.exists():
            return str(fallback)

    raise SystemExit(
        f"Error: required tool '{tool_name}' was not found on PATH or at any of the following locations:\n"
        + "\n".join(f"  {p}" for p in attempted)
        + "\nEnsure devkitARM is installed and DEVKITARM or DEVKITPRO is set, or add the bin directory to PATH."
    )


def thumb_bl_bytes(src_rom_addr: int, dst_rom_addr: int) -> bytes:
    return shared_thumb_bl_bytes(src_rom_addr, dst_rom_addr)


def is_thumb_bl_instruction(opcode: bytes) -> bool:
    """Return True when <opcode> encodes a 32-bit Thumb BL instruction."""
    return shared_is_thumb_bl_instruction(opcode)


def decode_thumb_bl_target(src_rom_addr: int, opcode: bytes) -> int:
    """Decode absolute target address from a 32-bit Thumb-1 BL instruction."""
    if len(opcode) != 4 or not is_thumb_bl_instruction(opcode):
        raise ValueError("opcode is not a 32-bit Thumb BL instruction")

    first = int.from_bytes(opcode[:2], "little")
    second = int.from_bytes(opcode[2:], "little")

    # Thumb-1 BL as encoded by thumb_branch.thumb_bl_bytes():
    #   first halfword:  11110 <imm11_hi>
    #   second halfword: 11111 <imm11_lo>
    # signed immediate is 22 bits, byte offset is (imm22 << 1).
    imm22 = ((first & 0x07FF) << 11) | (second & 0x07FF)
    if imm22 & (1 << 21):
        imm22 -= 1 << 22

    next_addr = src_rom_addr + 4
    return (next_addr + (imm22 << 1)) & 0xFFFFFFFF


def validate_thumb_bl_callsite(rom: bytes | bytearray, offset: int, label: str) -> bytes:
    """Ensure the target callsite is a Thumb BL before overwriting it."""
    if offset < 0 or offset + 4 > len(rom):
        raise SystemExit(
            f"Error: {label} callsite offset {offset:#x} is out of ROM bounds "
            f"(size={len(rom):#x})."
        )
    if offset % 2 != 0:
        raise SystemExit(
            f"Error: {label} callsite offset {offset:#x} is not halfword aligned for Thumb "
            "(must be 2-byte aligned)."
        )
    original = bytes(rom[offset:offset + 4])
    if not is_thumb_bl_instruction(original):
        raise SystemExit(
            f"Error: {label} callsite at {offset:#x} is not a Thumb BL instruction. "
            f"Found bytes: {original.hex(' ')}. Refusing to patch unknown site."
        )
    return original


def validate_thumb_bl_callsite_target(
    rom: bytes | bytearray,
    offset: int,
    label: str,
    expected_target: int,
    *,
    rom_base: int = 0x08000000,
) -> bytes:
    """Validate both the Thumb-BL shape and its decoded retail target."""
    original = validate_thumb_bl_callsite(rom, offset, label)
    actual_target = decode_thumb_bl_target(rom_base + offset, original)
    if actual_target != expected_target:
        raise SystemExit(
            f"Error: {label} callsite at {offset:#x} targets "
            f"0x{actual_target:08X}, expected 0x{expected_target:08X}. "
            "Refusing to patch an unknown ROM revision."
        )
    return original


def validate_exact_rom_bytes(
    rom: bytes | bytearray,
    offset: int,
    expected: bytes,
    label: str,
) -> bytes:
    """Require an exact verified retail instruction sequence before overwriting it."""
    if offset < 0 or offset + len(expected) > len(rom):
        raise SystemExit(
            f"Error: {label} sequence at {offset:#x} is out of ROM bounds "
            f"(size={len(rom):#x})."
        )
    original = bytes(rom[offset:offset + len(expected)])
    if original != expected:
        raise SystemExit(
            f"Error: {label} sequence at {offset:#x} does not match the verified retail bytes. "
            f"Found {original.hex(' ')}, expected {expected.hex(' ')}. "
            "Refusing to patch an unknown ROM revision."
        )
    return original


_NATIVE_AREA_BY_REGION_TOKEN = {
    "RAINBOW_ROUTE": 0,
    "MOONLIGHT_MANSION": 1,
    "CABBAGE_CAVERN": 2,
    "MUSTARD_MOUNTAIN": 3,
    "CARROT_CASTLE": 4,
    "OLIVE_OCEAN": 5,
    "PEPPERMINT_PALACE": 6,
    "RADISH_RUINS": 7,
    "CANDY_CONSTELLATION": 8,
    "TUTORIAL": 9,
    "DIMENSION_MIRROR": 10,
}
_ROOM_REGION_AREA_PATTERN = re.compile(r"^REGION_([A-Z_]+)/ROOM_")


def load_expected_native_area_by_doors_idx() -> dict[int, int]:
    """Build the AP room-data side of the native Area Key mapping contract."""
    rooms_path = Path(__file__).resolve().parent.parent / "data" / "regions" / "rooms.json"
    with rooms_path.open("r", encoding="utf-8") as rooms_file:
        rooms = json.load(rooms_file)

    expected: dict[int, int] = {}
    for region_name, room_data in rooms.items():
        match = _ROOM_REGION_AREA_PATTERN.match(region_name)
        room_sanity = room_data.get("room_sanity") if isinstance(room_data, dict) else None
        if not isinstance(room_sanity, dict) and isinstance(room_data, dict):
            locations = room_data.get("locations")
            if isinstance(locations, dict):
                room_sanity = locations.get("room_sanity")
        if match is None or not isinstance(room_sanity, dict):
            continue
        doors_idx = room_sanity.get("bit_index")
        if not isinstance(doors_idx, int):
            continue

        native_area = _NATIVE_AREA_BY_REGION_TOKEN.get(match.group(1))
        if native_area is None:
            raise SystemExit(
                f"Error: no native Area Key area mapping for room region {region_name!r}."
            )
        previous_area = expected.setdefault(doors_idx, native_area)
        if previous_area != native_area:
            raise SystemExit(
                f"Error: rooms.json assigns doorsIdx {doors_idx} to native areas "
                f"{previous_area} and {native_area}."
            )

    if not expected:
        raise SystemExit("Error: rooms.json produced an empty native Area Key area contract.")
    return expected


def validate_area_key_native_area_contract(rom: bytes | bytearray) -> None:
    """Require rooms.json area names to agree with the retail native room metadata."""
    expected = load_expected_native_area_by_doors_idx()
    observed_doors_idx: set[int] = set()

    for room_id in range(ROOM_AREA_INFO_COUNT):
        info_table_entry = ROOM_AREA_INFO_TABLE_OFFSET + (room_id * 4)
        room_props_entry = (
            ROOM_PROPS_TABLE_OFFSET
            + (room_id * ROOM_PROPS_STRIDE)
            + ROOM_PROPS_DOORS_IDX_OFFSET
        )
        if info_table_entry + 4 > len(rom) or room_props_entry + 2 > len(rom):
            raise SystemExit("Error: native Area Key room metadata is outside the selected ROM.")

        info_address = struct.unpack_from("<I", rom, info_table_entry)[0]
        if not (0x08000000 <= info_address < 0x0A000000):
            continue
        area_offset = (info_address - 0x08000000) + ROOM_AREA_INFO_AREA_OFFSET
        if area_offset >= len(rom):
            continue

        doors_idx = struct.unpack_from("<H", rom, room_props_entry)[0]
        expected_area = expected.get(doors_idx)
        if expected_area is None:
            continue

        native_area = rom[area_offset]
        if native_area != expected_area:
            raise SystemExit(
                "Error: Area Key native/AP room mapping drift: "
                f"roomId={room_id}, doorsIdx={doors_idx}, nativeArea={native_area}, "
                f"rooms.jsonArea={expected_area}. Refusing to build a mismatched patch."
            )
        observed_doors_idx.add(doors_idx)

    missing = sorted(set(expected) - observed_doors_idx)
    if missing:
        raise SystemExit(
            "Error: Area Key native/AP room mapping is incomplete; rooms.json doorsIdx values "
            f"were not found in retail room metadata: {missing}."
        )

    print(
        "Validated Area Key native/AP room-area mapping:",
        len(observed_doors_idx),
        "doorsIdx entries",
    )


def thumb_beq_bytes(src_rom_addr: int, dst_rom_addr: int) -> bytes:
    """Encode a Thumb-1 16-bit BEQ from <src_rom_addr> to <dst_rom_addr>."""
    displacement = dst_rom_addr - (src_rom_addr + 4)
    if displacement % 2 != 0 or not (-256 <= displacement <= 254):
        raise ValueError(
            f"Thumb BEQ target out of range/alignment: src={src_rom_addr:#x}, dst={dst_rom_addr:#x}"
        )
    return (0xD000 | ((displacement >> 1) & 0xFF)).to_bytes(2, "little")


def build_automatic_transition_guard_bytes(
    hook_target: int,
    *,
    rom_base: int = 0x08000000,
) -> bytes:
    """Build the 16-byte pre-mutation guard installed inside sub_0803FBB4."""
    start_addr = rom_base + AUTOMATIC_TRANSITION_GUARD_OFFSET
    guard = (
        bytes.fromhex("28 46 31 46")  # mov r0, r5; mov r1, r6
        + thumb_bl_bytes(start_addr + 4, hook_target)
        + bytes.fromhex("00 28")  # cmp r0, #0
        + thumb_beq_bytes(start_addr + 10, AUTOMATIC_TRANSITION_GUARD_RETURN_ROM_ADDR)
        + bytes.fromhex("C0 46 C0 46")  # two Thumb-1 NOPs
    )
    if len(guard) != len(AUTOMATIC_TRANSITION_GUARD_ORIGINAL):
        raise AssertionError("automatic transition guard must preserve the 16-byte patch window")
    return guard


def discover_thumb_bl_callsites_to_targets(
    rom: bytes | bytearray,
    target_addrs: set[int],
    *,
    rom_base: int,
    scan_start: int,
    scan_end: int,
) -> list[int]:
    """Find Thumb BL callsites in [scan_start, scan_end) whose decoded target is in target_addrs."""
    callsites: list[int] = []
    bounded_end = min(scan_end, len(rom) - 3)
    for offset in range(scan_start, bounded_end, 2):
        opcode = bytes(rom[offset:offset + 4])
        if not is_thumb_bl_instruction(opcode):
            continue
        src_addr = rom_base + offset
        try:
            dst_addr = decode_thumb_bl_target(src_addr, opcode)
        except ValueError:
            continue
        if dst_addr in target_addrs:
            callsites.append(offset)
    return callsites


def resolve_elf_symbol_address(elf_path: str | Path, symbol_name: str) -> int:
    nm = _find_arm_binutil("arm-none-eabi-nm")
    try:
        result = subprocess.run(
            [nm, str(elf_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
    except FileNotFoundError as e:
        raise SystemExit(f"Error: failed to execute {nm}") from e
    except subprocess.CalledProcessError as e:
        raise SystemExit(
            f"Error: failed to inspect ELF symbols in {elf_path}:\n{(e.stdout or '').rstrip()}"
        ) from e

    for line in result.stdout.splitlines():
        parts = line.strip().split()
        if len(parts) >= 3 and parts[-1] == symbol_name:
            try:
                return int(parts[0], 16)
            except ValueError:
                break

    raise SystemExit(f"Error: symbol '{symbol_name}' not found in ELF {elf_path}")


def require_bsdiff4() -> Any:
    try:
        import bsdiff4  # type: ignore[import-untyped]
        return bsdiff4
    except ModuleNotFoundError as e:
        raise SystemExit(
            "Error: Python package 'bsdiff4' is not installed.\n"
            "Install it in the SAME environment you run this script with:\n"
            "  python -m pip install bsdiff4\n"
        ) from e


def read_rom_path_from_tmp(tmp_path: str) -> str:
    try:
        with open(tmp_path, "r", encoding="utf-8") as f:
            for line in f:
                candidate = line.strip()
                if candidate:
                    candidate = candidate.strip('"').strip("'").strip()
                    return candidate
    except FileNotFoundError as e:
        raise SystemExit(
            f"Error: '{tmp_path}' not found.\n"
            f"Create '{tmp_path}' with a single line pointing to your clean base ROM."
        ) from e

    raise SystemExit(
        f"Error: '{tmp_path}' exists but contains no usable ROM path.\n"
        "Put the full path to the ROM on the first line."
    )


def safe_unlink(path: str) -> None:
    try:
        os.remove(path)
        print("Deleted intermediary ROM:", path)
    except FileNotFoundError:
        return
    except Exception as e:
        print(f"Warning: failed to delete intermediary ROM '{path}': {e}")


def _lock_pid_from_file(lock_path: Path) -> int | None:
    try:
        text = lock_path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return None
    except Exception:
        return None

    for line in text.splitlines():
        if line.startswith("pid="):
            raw = line.split("=", 1)[1].strip()
            if raw.isdigit():
                return int(raw)
    return None


def _pid_is_running(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def acquire_run_lock(lock_path: Path) -> None:
    try:
        # O_EXCL guarantees only one patch_rom.py run can hold the lock at a time.
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(f"pid={os.getpid()}\n")
            f.write(f"started={datetime.now().isoformat(timespec='seconds')}\n")
        return
    except FileExistsError:
        existing_pid = _lock_pid_from_file(lock_path)
        if existing_pid is not None and not _pid_is_running(existing_pid):
            print(f"Stale lock detected for exited pid={existing_pid}; reclaiming lock.")
            try:
                lock_path.unlink()
            except Exception as e:
                raise SystemExit(
                    f"Error: found stale lock but failed to remove it: {lock_path}\n{e}"
                ) from e
            return acquire_run_lock(lock_path)

        raise SystemExit(
            f"Error: another patch generation appears to be running (lock file exists): {lock_path}\n"
            "If no patch job is active, delete the lock file and retry."
        )


def release_run_lock(lock_path: Path) -> None:
    try:
        lock_path.unlink()
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"Warning: failed to remove lock file '{lock_path}': {e}")


def _bsdiff_worker(
    in_path: str,
    intermediary_rom: str,
    tmp_patch_path: str,
    result_queue: MultiprocessingQueue[str],
) -> None:
    try:
        bsdiff4 = require_bsdiff4()
        bsdiff4.file_diff(in_path, intermediary_rom, tmp_patch_path)
        result_queue.put("")
    except Exception as e:  # pragma: no cover - exercised only on worker failure
        result_queue.put(str(e))


def generate_bsdiff_with_timeout(in_path: str, intermediary_rom: str, patch_path: str) -> None:
    with tempfile.TemporaryDirectory(prefix="kirbyam-bsdiff-") as tmpdir:
        tmpdir_path = Path(tmpdir)
        local_in = tmpdir_path / "clean_base.gba"
        local_out = tmpdir_path / "patched_base.gba"
        local_patch = tmpdir_path / "base_patch.bsdiff4"

        print(f"Preparing local temp workspace for bsdiff: {tmpdir_path}")
        shutil.copy2(in_path, local_in)
        shutil.copy2(intermediary_rom, local_out)

        result_queue: MultiprocessingQueue[str] = mp.Queue()
        proc = mp.Process(
            target=_bsdiff_worker,
            args=(str(local_in), str(local_out), str(local_patch), result_queue),
            daemon=True,
        )
        proc.start()

        start = time.monotonic()
        last_heartbeat = start

        while proc.is_alive():
            now = time.monotonic()
            elapsed = int(now - start)
            if BSDIFF_TIMEOUT_SECONDS > 0 and elapsed >= BSDIFF_TIMEOUT_SECONDS:
                proc.terminate()
                proc.join(timeout=5)
                raise SystemExit(
                    "Error: bsdiff generation timed out.\n"
                    f"Elapsed: {elapsed}s, timeout: {BSDIFF_TIMEOUT_SECONDS}s\n"
                    "You can raise the timeout with KIRBYAM_BSDIFF_TIMEOUT_SECONDS, "
                    "or investigate system load/IO contention."
                )

            if BSDIFF_HEARTBEAT_SECONDS > 0 and now - last_heartbeat >= BSDIFF_HEARTBEAT_SECONDS:
                print(f"BSdiff still running... {elapsed}s elapsed")
                last_heartbeat = now

            proc.join(timeout=1)

        proc.join(timeout=5)

        worker_error = ""
        if not result_queue.empty():
            worker_error = result_queue.get_nowait()

        if proc.exitcode not in (0, None) or worker_error:
            msg = worker_error or f"worker exited with code {proc.exitcode}"
            raise SystemExit(f"Error generating bsdiff patch '{patch_path}': {msg}")

        shutil.move(local_patch, patch_path)


def md5_file(path: str, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk_size)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def get_rom_size_warning(rom_size: int, expected_size: int = EXPECTED_BASE_ROM_SIZE) -> str | None:
    if rom_size == expected_size:
        return None
    return f"Warning: ROM size is {rom_size:#x}, expected {expected_size:#x}. Proceeding anyway."


def load_expected_rom_md5_from_rom_py() -> str:
    """
    Load expected base ROM MD5 from worlds/kirbyam/rom.py as a package import so
    relative imports inside rom.py work.

    Assumptions:
      - patch_rom.py is at .../worlds/kirbyam/kirby_ap_payload/patch_rom.py
      - repo root is 3 parents up from this script (contains 'worlds/')
      - expected hash lives at KirbyAmProcedurePatch.hash
    """
    script_path = Path(__file__).resolve()
    repo_root = script_path.parents[3]  # repo root containing 'worlds/'

    repo_root_str = str(repo_root)
    added = False
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)
        added = True

    try:
        # Import as a proper package module so rom.py's relative imports work.
        import importlib

        mod = importlib.import_module("worlds.kirbyam.rom")

        if not hasattr(mod, "KirbyAmProcedurePatch"):
            raise SystemExit("--hash-debug: worlds.kirbyam.rom does not define KirbyAmProcedurePatch")

        cls = getattr(mod, "KirbyAmProcedurePatch")
        if not hasattr(cls, "hash"):
            raise SystemExit("--hash-debug: KirbyAmProcedurePatch has no attribute 'hash'")

        expected = getattr(cls, "hash")
        if not isinstance(expected, str) or not expected:
            raise SystemExit("--hash-debug: KirbyAmProcedurePatch.hash is not a non-empty string")

        expected = expected.strip().lower()
        if any(c not in "0123456789abcdef" for c in expected) or len(expected) != 32:
            raise SystemExit(
                "--hash-debug: KirbyAmProcedurePatch.hash does not look like an MD5 hex digest.\n"
                f"Value: {expected!r}"
            )

        return expected
    except ModuleNotFoundError as e:
        raise SystemExit(
            "--hash-debug: Failed to import worlds.kirbyam.rom.\n"
            f"Repo root used: {repo_root_str}\n"
            f"Original error: {e}"
        ) from e
    finally:
        # Optional rollback to keep environment clean
        if added:
            try:
                sys.path.remove(repo_root_str)
            except ValueError:
                pass


def hash_debug_report(in_path: str, source_type: str) -> None:
    print("")
    print("=== HASH DEBUG (BASE ROM) ===")
    print("Source type:", source_type)
    print("Base ROM path:", in_path)

    if source_type == "file":
        tmp = Path(ROM_PATH_TMP).resolve()
        print("rom_path.tmp:", str(tmp))
        if tmp.exists():
            try:
                line0 = tmp.read_text(encoding="utf-8", errors="replace").splitlines()[:1]
                if line0:
                    print("rom_path.tmp first line:", line0[0])
            except Exception as e:
                print(f"Warning: could not read rom_path.tmp for display: {e}")
        else:
            print("rom_path.tmp exists: False")

    p = Path(in_path)
    print("Exists:", p.exists())
    if not p.exists():
        print("=== HASH DEBUG END (ROM MISSING) ===")
        print("")
        return

    try:
        size = p.stat().st_size
        print("Size (bytes):", size)
    except Exception as e:
        print(f"Warning: could not stat ROM file: {e}")

    # Compute MD5 of base ROM
    actual = md5_file(in_path)

    # Load expected MD5 from rom.py
    expected = load_expected_rom_md5_from_rom_py()

    # Adjacent lines, explicitly labeled
    print(f"Expected MD5 (rom.py KirbyAmProcedurePatch.hash): {expected}")
    print(f"Computed MD5 (selected base ROM):               {actual}")

    if actual.lower() == expected.lower():
        print("Result: MATCH (base ROM MD5 matches expected).")
    else:
        print("Result: MISMATCH (base ROM MD5 does NOT match expected).")
        print("Action: verify you're using the correct (clean, unmodified) USA ROM file.")

    print("=== HASH DEBUG END ===")
    print("")


def parse_args(argv: list[str]) -> dict[str, Any]:
    fixed_patch = str(get_fixed_patch_out())

    # Legacy mode: <in> <out> [patch] and no flags
    if len(argv) in (3, 4) and not any(a.startswith("-") for a in argv[1:]):
        in_path = argv[1]
        ignored_out = argv[2]
        if len(argv) == 4:
            print(f"Warning: ignoring user-supplied patch output path '{argv[3]}'")
            print(f"         Patch will always be written to: {fixed_patch}")
        return {
            "source_type": "arg",
            "in_path": in_path,
            "patch_path": fixed_patch,
            "legacy_ignored_out": ignored_out,
            "hash_debug": False,
        }

    parser = argparse.ArgumentParser(
        prog=os.path.basename(argv[0]),
        description="Build payload, patch ROM, and generate a bsdiff4 patch.",
    )
    parser.add_argument(
        "--source-type",
        choices=("file", "arg"),
        default="file",
        help="Where to get the base ROM path: 'file' reads rom_path.tmp, 'arg' uses positional IN_ROM.",
    )
    parser.add_argument(
        "--hash-debug",
        action="store_true",
        help="Compute and print MD5 of selected base ROM and compare to KirbyAmProcedurePatch.hash from rom.py.",
    )
    # Keep accepting optional PATH args for backwards compatibility, but they are ignored for patch output.
    parser.add_argument(
        "paths",
        nargs="*",
        help="Legacy/compat only. Any provided patch output path will be ignored.",
    )

    ns = parser.parse_args(argv[1:])

    legacy_ignored_out = None

    if ns.source_type == "file":
        # Accept 0 or 1 positional for backward compatibility, but ignore it.
        if len(ns.paths) > 1:
            raise SystemExit(
                "Usage:\n"
                "  python patch_rom.py [ignored_patch_path]\n"
                "  python patch_rom.py --source-type file [ignored_patch_path]\n"
                f"Patch will always be written to: {fixed_patch}"
            )
        if len(ns.paths) == 1:
            print(f"Warning: ignoring user-supplied patch output path '{ns.paths[0]}'")
            print(f"         Patch will always be written to: {fixed_patch}")
        in_path = read_rom_path_from_tmp(ROM_PATH_TMP)

    else:
        # Expect: IN_ROM [ignored_patch_path]
        if len(ns.paths) not in (1, 2):
            raise SystemExit(
                "Usage with --source-type arg:\n"
                "  python patch_rom.py --source-type arg <in.gba> [ignored_patch_path]\n"
                f"Patch will always be written to: {fixed_patch}"
            )
        in_path = ns.paths[0]
        if len(ns.paths) == 2:
            print(f"Warning: ignoring user-supplied patch output path '{ns.paths[1]}'")
            print(f"         Patch will always be written to: {fixed_patch}")

    return {
        "source_type": ns.source_type,
        "in_path": in_path,
        "patch_path": fixed_patch,
        "legacy_ignored_out": legacy_ignored_out,
        "hash_debug": bool(ns.hash_debug),
    }


def ensure_patch_output_dir_exists(patch_path: str) -> None:
    patch_out_dir = Path(patch_path).resolve().parent
    if not patch_out_dir.exists():
        raise SystemExit(
            f"Error: patch output directory does not exist: {patch_out_dir}\n"
            "Create it (worlds/kirbyam/data/) and re-run. patch_rom.py will not create folders."
        )


def load_payload_and_validate() -> tuple[bytes, Path]:
    try:
        with open("payload.bin", "rb") as f:
            payload = f.read()
    except FileNotFoundError as e:
        raise SystemExit(
            "Error: payload.bin not found. Ensure your build produces payload.bin in the current directory."
        ) from e

    if len(payload) > 0x16A0:
        raise SystemExit(f"payload.bin too large: {len(payload)} bytes (max 0x16A0)")

    payload_elf_path = Path("payload.elf")
    if not payload_elf_path.exists():
        raise SystemExit(
            "Error: payload.elf not found after build; cannot resolve payload hook symbols."
        )

    return payload, payload_elf_path


def resolve_payload_hook_targets(payload_elf_path: Path) -> dict[str, int]:
    targets = {
        "main_hook_target": resolve_elf_symbol_address(
            payload_elf_path, "ap_hook_entry"),
        "boss_hook_target": resolve_elf_symbol_address(
            payload_elf_path, "ap_on_boss_defeat_collect_shard"),
        "boss_already_owned_hook_target": resolve_elf_symbol_address(
            payload_elf_path, "ap_on_boss_defeat_already_owned_reward"),
        "minor_chest_hook_target": resolve_elf_symbol_address(
            payload_elf_path, "ap_on_collect_small_chest"),
        "big_chest_hook_target": resolve_elf_symbol_address(
            payload_elf_path, "ap_on_collect_big_chest"),
        "vitality_chest_hook_target": resolve_elf_symbol_address(
            payload_elf_path, "ap_on_collect_vitality_chest"),
        "spray_paint_chest_hook_target": resolve_elf_symbol_address(
            payload_elf_path, "ap_on_collect_spray_paint_chest"),
        "sound_player_chest_hook_target": resolve_elf_symbol_address(
            payload_elf_path, "ap_on_collect_sound_player_chest"),
        "hub_switch_hook_target": resolve_elf_symbol_address(
            payload_elf_path, "ap_on_world_map_unlock_call"),
        "small_switch_effect_hook_target": resolve_elf_symbol_address(
            payload_elf_path, "ap_on_small_switch_effect"),
        "special_door_state_hook_target": resolve_elf_symbol_address(
            payload_elf_path, "ap_on_query_special_door_state"),
        "automatic_transition_guard_target": resolve_elf_symbol_address(
            payload_elf_path, "ap_prepare_automatic_transition"),
        "button_special_transition_hook_target": resolve_elf_symbol_address(
            payload_elf_path, "ap_on_button_special_transition"),
        "explicit_room_transition_hook_target": resolve_elf_symbol_address(
            payload_elf_path, "ap_on_explicit_room_transition"),
        "ability_transition_hook_target": resolve_elf_symbol_address(
            payload_elf_path, "ap_on_request_copy_ability_transition"),
        "ability_transition_start_hook_target": resolve_elf_symbol_address(
            payload_elf_path, "ap_on_start_copy_ability_transition"),
        "starting_color_start_game_hook_target": resolve_elf_symbol_address(
            payload_elf_path, "ap_on_start_single_player_game"),
    }
    return {name: target & ~1 for name, target in targets.items()}


_PAYLOAD_TARGET_LABELS = {
    "main_hook_target": "main hook",
    "boss_hook_target": "boss shard hook",
    "boss_already_owned_hook_target": "boss already-owned reward hook",
    "minor_chest_hook_target": "minor chest hook",
    "big_chest_hook_target": "big chest hook",
    "vitality_chest_hook_target": "vitality chest hook",
    "spray_paint_chest_hook_target": "spray paint chest hook",
    "sound_player_chest_hook_target": "sound player/music-sheet chest hook",
    "hub_switch_hook_target": "hub switch hook",
    "small_switch_effect_hook_target": "lever small-switch effect hook",
    "special_door_state_hook_target": "Area Key mirror visual-state hook",
    "automatic_transition_guard_target": "Area Key automatic-transition guard",
    "button_special_transition_hook_target": "Area Key button-transition hook",
    "explicit_room_transition_hook_target": "Area Key explicit-room-transition hook",
    "ability_transition_hook_target": "ability transition hook",
    "ability_transition_start_hook_target": "ability transition-start hook",
    "starting_color_start_game_hook_target": "starting-color game-start hook",
}


def validate_payload_targets(
    hook_targets: dict[str, int],
    payload_rom_start: int,
    payload_rom_end: int,
) -> None:
    for name, target in hook_targets.items():
        if not (payload_rom_start <= target < payload_rom_end):
            raise SystemExit(
                "Error: "
                f"{_PAYLOAD_TARGET_LABELS[name]} target address out of expected payload range.\n"
                f"Resolved address: 0x{target:08X}, expected within "
                f"[0x{payload_rom_start:08X}, 0x{payload_rom_end:08X}). "
                "Check your payload.elf link address and PAYLOAD_OFFSET."
            )


def build_payload_hook_bl_bytes(
    hook_targets: dict[str, int], rom_base: int
) -> dict[str, bytes]:
    return {
        "main_hook_bl_bytes": thumb_bl_bytes(
            rom_base + MAIN_HOOK_OFFSET, hook_targets["main_hook_target"]
        ),
        "boss_hook_bl_bytes": thumb_bl_bytes(
            rom_base + BOSS_COLLECT_SHARD_CALL_OFFSET,
            hook_targets["boss_hook_target"],
        ),
        "minor_chest_hook_bl_bytes": thumb_bl_bytes(
            rom_base + MINOR_CHEST_COLLECT_CALL_OFFSET,
            hook_targets["minor_chest_hook_target"],
        ),
        "big_chest_hook_bl_bytes": thumb_bl_bytes(
            rom_base + BIG_CHEST_COLLECT_CALL_OFFSET,
            hook_targets["big_chest_hook_target"],
        ),
        "vitality_chest_hook_bl_bytes": thumb_bl_bytes(
            rom_base + VITALITY_CHEST_COLLECT_CALL_OFFSET,
            hook_targets["vitality_chest_hook_target"],
        ),
        "spray_paint_chest_hook_bl_bytes": thumb_bl_bytes(
            rom_base + SPRAY_PAINT_CHEST_COLLECT_CALL_OFFSET,
            hook_targets["spray_paint_chest_hook_target"],
        ),
        "sound_player_chest_hook_bl_bytes": thumb_bl_bytes(
            rom_base + SOUND_PLAYER_CHEST_COLLECT_CALL_OFFSET,
            hook_targets["sound_player_chest_hook_target"],
        ),
        "hub_switch_hook_bl_bytes": thumb_bl_bytes(
            rom_base + BIG_SWITCH_UNLOCK_CALL_OFFSET,
            hook_targets["hub_switch_hook_target"],
        ),
        "small_switch_effect_hook_bl_bytes": thumb_bl_bytes(
            rom_base + SMALL_SWITCH_EFFECT_CALL_OFFSET,
            hook_targets["small_switch_effect_hook_target"],
        ),
        "automatic_transition_guard_bytes": build_automatic_transition_guard_bytes(
            hook_targets["automatic_transition_guard_target"],
            rom_base=rom_base,
        ),
    }


def load_rom_and_validate(in_path: str) -> tuple[bytearray, bool]:
    try:
        with open(in_path, "rb") as f:
            rom = bytearray(f.read())
    except FileNotFoundError as e:
        raise SystemExit(f"Error: input ROM not found: {in_path}") from e

    warning = get_rom_size_warning(len(rom))
    if warning is not None:
        print(warning)
    return rom, warning is None


def validate_rom_callsite_instructions(rom: bytes | bytearray) -> dict[str, bytes]:
    original_boss_hook = validate_thumb_bl_callsite(
        rom, BOSS_COLLECT_SHARD_CALL_OFFSET, "boss shard"
    )
    original_minor_chest_hook = validate_thumb_bl_callsite(
        rom, MINOR_CHEST_COLLECT_CALL_OFFSET, "minor chest"
    )
    original_big_chest_hook = validate_thumb_bl_callsite(
        rom, BIG_CHEST_COLLECT_CALL_OFFSET, "big chest"
    )
    original_vitality_hook = validate_thumb_bl_callsite(
        rom, VITALITY_CHEST_COLLECT_CALL_OFFSET, "vitality chest"
    )
    original_spray_paint_hook = validate_thumb_bl_callsite(
        rom, SPRAY_PAINT_CHEST_COLLECT_CALL_OFFSET, "spray paint chest"
    )
    original_sound_player_hook = validate_thumb_bl_callsite(
        rom,
        SOUND_PLAYER_CHEST_COLLECT_CALL_OFFSET,
        "sound player/music-sheet chest",
    )
    original_hub_switch_hook = validate_thumb_bl_callsite(
        rom, BIG_SWITCH_UNLOCK_CALL_OFFSET, "hub switch unlock"
    )
    original_small_switch_effect_hook = validate_thumb_bl_callsite(
        rom, SMALL_SWITCH_EFFECT_CALL_OFFSET, "lever small-switch effect dispatch"
    )
    original_automatic_transition_guard = validate_exact_rom_bytes(
        rom,
        AUTOMATIC_TRANSITION_GUARD_OFFSET,
        AUTOMATIC_TRANSITION_GUARD_ORIGINAL,
        "Area Key automatic-transition guard",
    )
    original_starting_color_hooks = [
        validate_thumb_bl_callsite_target(
            rom,
            offset,
            "single-player game start",
            ORIGINAL_START_GAME_FN_ADDR,
        )
        for offset in STARTING_COLOR_START_GAME_CALL_OFFSETS
    ]

    print("Validated hook callsite instruction shape (Thumb BL):")
    print(f"  boss shard @ {BOSS_COLLECT_SHARD_CALL_OFFSET:#x}: {original_boss_hook.hex(' ')}")
    print(f"  minor chest @ {MINOR_CHEST_COLLECT_CALL_OFFSET:#x}: {original_minor_chest_hook.hex(' ')}")
    print(f"  big chest @ {BIG_CHEST_COLLECT_CALL_OFFSET:#x}: {original_big_chest_hook.hex(' ')}")
    print(f"  vitality chest @ {VITALITY_CHEST_COLLECT_CALL_OFFSET:#x}: {original_vitality_hook.hex(' ')}")
    print(f"  spray paint chest @ {SPRAY_PAINT_CHEST_COLLECT_CALL_OFFSET:#x}: {original_spray_paint_hook.hex(' ')}")
    print(
        f"  sound player/music-sheet chest @ {SOUND_PLAYER_CHEST_COLLECT_CALL_OFFSET:#x}: "
        f"{original_sound_player_hook.hex(' ')}"
    )
    print(f"  hub switch unlock @ {BIG_SWITCH_UNLOCK_CALL_OFFSET:#x}: {original_hub_switch_hook.hex(' ')}")
    print(
        f"  lever small-switch effect @ {SMALL_SWITCH_EFFECT_CALL_OFFSET:#x}: "
        f"{original_small_switch_effect_hook.hex(' ')}"
    )
    print(
        f"  Area Key automatic-transition guard @ {AUTOMATIC_TRANSITION_GUARD_OFFSET:#x}: "
        f"{original_automatic_transition_guard.hex(' ')}"
    )
    for offset, opcode in zip(STARTING_COLOR_START_GAME_CALL_OFFSETS, original_starting_color_hooks):
        print(f"  single-player game start @ {offset:#x}: {opcode.hex(' ')}")

    return {
        "original_boss_hook": original_boss_hook,
        "original_minor_chest_hook": original_minor_chest_hook,
        "original_big_chest_hook": original_big_chest_hook,
        "original_vitality_hook": original_vitality_hook,
        "original_spray_paint_hook": original_spray_paint_hook,
        "original_sound_player_hook": original_sound_player_hook,
        "original_hub_switch_hook": original_hub_switch_hook,
        "original_small_switch_effect_hook": original_small_switch_effect_hook,
        "original_automatic_transition_guard": original_automatic_transition_guard,
        "original_starting_color_hook_intro": original_starting_color_hooks[0],
        "original_starting_color_hook_load": original_starting_color_hooks[1],
    }


def discover_required_callsites(
    rom: bytes | bytearray,
    rom_base: int,
    target_addr: int,
    expected_count: int,
    label: str,
) -> list[int]:
    """Discover one retail call family and fail closed on missing/extra hooks."""
    callsites = discover_thumb_bl_callsites_to_targets(
        rom,
        {target_addr, target_addr | 1},
        rom_base=rom_base,
        scan_start=0xC0,
        scan_end=min(PAYLOAD_OFFSET, len(rom) - 3),
    )
    if len(callsites) != expected_count:
        raise SystemExit(
            f"Error: expected exactly {expected_count} {label} callsites to "
            f"0x{target_addr:08X}, found {len(callsites)} at "
            f"{', '.join(hex(offset) for offset in callsites) or '<none>'}. "
            "Refusing to build an Area Key patch with incomplete runtime coverage."
        )
    return callsites


def discover_area_key_callsites(
    rom: bytes | bytearray,
    rom_base: int,
) -> tuple[list[int], list[int], list[int]]:
    special_door_state_callsites = discover_required_callsites(
        rom,
        rom_base,
        ORIGINAL_SPECIAL_DOOR_STATE_FN_ADDR,
        EXPECTED_SPECIAL_DOOR_STATE_CALLSITES,
        "special-door visual-state",
    )
    button_transition_callsites = discover_required_callsites(
        rom,
        rom_base,
        ORIGINAL_BUTTON_SPECIAL_TRANSITION_FN_ADDR,
        EXPECTED_BUTTON_SPECIAL_TRANSITION_CALLSITES,
        "button special-transition",
    )
    explicit_transition_callsites = discover_required_callsites(
        rom,
        rom_base,
        ORIGINAL_EXPLICIT_ROOM_TRANSITION_FN_ADDR,
        EXPECTED_EXPLICIT_ROOM_TRANSITION_CALLSITES,
        "explicit room-transition",
    )
    return (
        special_door_state_callsites,
        button_transition_callsites,
        explicit_transition_callsites,
    )


def discover_runtime_callsites(
    rom: bytes | bytearray, rom_base: int, hook_targets: dict[str, int]
) -> tuple[dict[int, bytes], list[int], list[int]]:
    _GBA_ROM_CODE_START = 0xC0
    scan_end = min(PAYLOAD_OFFSET, len(rom) - 3)

    boss_already_owned_target_candidates = {
        ORIGINAL_BOSS_ALREADY_OWNED_REWARD_FN_ADDR,
        ORIGINAL_BOSS_ALREADY_OWNED_REWARD_FN_ADDR | 1,
    }
    boss_already_owned_callsites = discover_thumb_bl_callsites_to_targets(
        rom,
        boss_already_owned_target_candidates,
        rom_base=rom_base,
        scan_start=_GBA_ROM_CODE_START,
        scan_end=scan_end,
    )
    if len(boss_already_owned_callsites) != EXPECTED_BOSS_ALREADY_OWNED_REWARD_CALLSITES:
        if scan_end == PAYLOAD_OFFSET:
            raise SystemExit(
                "Error: expected exactly "
                f"{EXPECTED_BOSS_ALREADY_OWNED_REWARD_CALLSITES} callsites to "
                f"0x{ORIGINAL_BOSS_ALREADY_OWNED_REWARD_FN_ADDR:08X}, "
                f"found {len(boss_already_owned_callsites)} at "
                f"{', '.join(hex(x) for x in boss_already_owned_callsites)}."
            )

        print(
            "Warning: expected exactly "
            f"{EXPECTED_BOSS_ALREADY_OWNED_REWARD_CALLSITES} callsites to "
            f"0x{ORIGINAL_BOSS_ALREADY_OWNED_REWARD_FN_ADDR:08X}, "
            f"found {len(boss_already_owned_callsites)} at "
            f"{', '.join(hex(x) for x in boss_already_owned_callsites) or '<none>'}. "
            "Continuing because ROM size is non-standard; already-owned reward hook patching may be incomplete."
        )

    boss_already_owned_hook_bl_by_offset = {
        offset: thumb_bl_bytes(
            rom_base + offset,
            hook_targets["boss_already_owned_hook_target"],
        )
        for offset in boss_already_owned_callsites
    }

    ability_transition_target_candidates = {
        ORIGINAL_ABILITY_TRANSITION_FN_ADDR,
        ORIGINAL_ABILITY_TRANSITION_FN_ADDR | 1,
    }
    ability_transition_callsites = discover_thumb_bl_callsites_to_targets(
        rom,
        ability_transition_target_candidates,
        rom_base=rom_base,
        scan_start=_GBA_ROM_CODE_START,
        scan_end=scan_end,
    )
    if not ability_transition_callsites:
        raise SystemExit(
            f"Error: no callsites found for ability transition function "
            f"0x{ORIGINAL_ABILITY_TRANSITION_FN_ADDR:08X}. "
            "Refusing to continue without a validated runtime reroll hook site."
        )

    ability_transition_start_target_candidates = {
        ORIGINAL_ABILITY_TRANSITION_START_FN_ADDR,
        ORIGINAL_ABILITY_TRANSITION_START_FN_ADDR | 1,
    }
    ability_transition_start_callsites = discover_thumb_bl_callsites_to_targets(
        rom,
        ability_transition_start_target_candidates,
        rom_base=rom_base,
        scan_start=_GBA_ROM_CODE_START,
        scan_end=scan_end,
    )
    if not ability_transition_start_callsites:
        raise SystemExit(
            f"Error: no callsites found for ability transition starter "
            f"0x{ORIGINAL_ABILITY_TRANSITION_START_FN_ADDR:08X}. "
            "Without this hook, ability statues can bypass ability locking."
        )

    return (
        boss_already_owned_hook_bl_by_offset,
        ability_transition_callsites,
        ability_transition_start_callsites,
    )


def patch_rom_with_payload(
    rom: bytearray,
    payload: bytes,
    hook_bl_bytes: dict[str, bytes],
    boss_already_owned_hook_bl_by_offset: dict[int, bytes],
    ability_transition_callsites: list[int],
    ability_transition_start_callsites: list[int],
    special_door_state_callsites: list[int],
    button_transition_callsites: list[int],
    explicit_transition_callsites: list[int],
    hook_targets: dict[str, int],
    rom_base: int,
) -> None:
    rom[PAYLOAD_OFFSET:PAYLOAD_OFFSET + len(payload)] = payload

    rom[MAIN_HOOK_OFFSET:MAIN_HOOK_OFFSET + 4] = hook_bl_bytes["main_hook_bl_bytes"]
    rom[BOSS_COLLECT_SHARD_CALL_OFFSET:BOSS_COLLECT_SHARD_CALL_OFFSET + 4] = hook_bl_bytes["boss_hook_bl_bytes"]
    rom[MINOR_CHEST_COLLECT_CALL_OFFSET:MINOR_CHEST_COLLECT_CALL_OFFSET + 4] = (
        hook_bl_bytes["minor_chest_hook_bl_bytes"]
    )
    rom[BIG_CHEST_COLLECT_CALL_OFFSET:BIG_CHEST_COLLECT_CALL_OFFSET + 4] = (
        hook_bl_bytes["big_chest_hook_bl_bytes"]
    )
    rom[VITALITY_CHEST_COLLECT_CALL_OFFSET:VITALITY_CHEST_COLLECT_CALL_OFFSET + 4] = (
        hook_bl_bytes["vitality_chest_hook_bl_bytes"]
    )
    rom[SPRAY_PAINT_CHEST_COLLECT_CALL_OFFSET:SPRAY_PAINT_CHEST_COLLECT_CALL_OFFSET + 4] = (
        hook_bl_bytes["spray_paint_chest_hook_bl_bytes"]
    )
    rom[SOUND_PLAYER_CHEST_COLLECT_CALL_OFFSET:SOUND_PLAYER_CHEST_COLLECT_CALL_OFFSET + 4] = (
        hook_bl_bytes["sound_player_chest_hook_bl_bytes"]
    )
    rom[BIG_SWITCH_UNLOCK_CALL_OFFSET:BIG_SWITCH_UNLOCK_CALL_OFFSET + 4] = hook_bl_bytes["hub_switch_hook_bl_bytes"]
    rom[SMALL_SWITCH_EFFECT_CALL_OFFSET:SMALL_SWITCH_EFFECT_CALL_OFFSET + 4] = (
        hook_bl_bytes["small_switch_effect_hook_bl_bytes"]
    )
    rom[
        AUTOMATIC_TRANSITION_GUARD_OFFSET:
        AUTOMATIC_TRANSITION_GUARD_OFFSET + len(AUTOMATIC_TRANSITION_GUARD_ORIGINAL)
    ] = hook_bl_bytes["automatic_transition_guard_bytes"]

    for offset, hook_bl in boss_already_owned_hook_bl_by_offset.items():
        rom[offset:offset + 4] = hook_bl
    for offset in ability_transition_callsites:
        rom[offset:offset + 4] = thumb_bl_bytes(
            rom_base + offset, hook_targets["ability_transition_hook_target"]
        )
    for offset in ability_transition_start_callsites:
        rom[offset:offset + 4] = thumb_bl_bytes(
            rom_base + offset, hook_targets["ability_transition_start_hook_target"]
        )
    for offset in special_door_state_callsites:
        rom[offset:offset + 4] = thumb_bl_bytes(
            rom_base + offset, hook_targets["special_door_state_hook_target"]
        )
    for offset in button_transition_callsites:
        rom[offset:offset + 4] = thumb_bl_bytes(
            rom_base + offset, hook_targets["button_special_transition_hook_target"]
        )
    for offset in explicit_transition_callsites:
        rom[offset:offset + 4] = thumb_bl_bytes(
            rom_base + offset, hook_targets["explicit_room_transition_hook_target"]
        )
    for offset in STARTING_COLOR_START_GAME_CALL_OFFSETS:
        rom[offset:offset + 4] = thumb_bl_bytes(
            rom_base + offset, hook_targets["starting_color_start_game_hook_target"]
        )


def print_patch_summary(
    hook_targets: dict[str, int],
    hook_bl_bytes: dict[str, bytes],
    boss_already_owned_callsites: list[int],
    ability_transition_callsites: list[int],
    ability_transition_start_callsites: list[int],
    special_door_state_callsites: list[int],
    button_transition_callsites: list[int],
    explicit_transition_callsites: list[int],
) -> None:
    print("Intermediary patched ROM written:", INTERMEDIARY_ROM)
    print("Payload inserted at file offset:", hex(PAYLOAD_OFFSET))
    print(
        "Main hook patched at file offset:",
        hex(MAIN_HOOK_OFFSET),
        "with bytes:",
        hook_bl_bytes["main_hook_bl_bytes"].hex(" "),
        "target=",
        hex(hook_targets["main_hook_target"]),
    )
    print(
        "Boss shard call patched at file offset:",
        hex(BOSS_COLLECT_SHARD_CALL_OFFSET),
        "with bytes:",
        hook_bl_bytes["boss_hook_bl_bytes"].hex(" "),
        "target=",
        hex(hook_targets["boss_hook_target"]),
    )
    print(
        "Boss already-owned reward callsites patched:",
        ", ".join(hex(x) for x in boss_already_owned_callsites),
        "target=",
        hex(hook_targets["boss_already_owned_hook_target"]),
    )
    print(
        "Minor chest call patched at file offset:",
        hex(MINOR_CHEST_COLLECT_CALL_OFFSET),
        "with bytes:",
        hook_bl_bytes["minor_chest_hook_bl_bytes"].hex(" "),
        "target=",
        hex(hook_targets["minor_chest_hook_target"]),
    )
    print(
        "Big chest call patched at file offset:",
        hex(BIG_CHEST_COLLECT_CALL_OFFSET),
        "with bytes:",
        hook_bl_bytes["big_chest_hook_bl_bytes"].hex(" "),
        "target=",
        hex(hook_targets["big_chest_hook_target"]),
    )
    print(
        "Vitality chest call patched at file offset:",
        hex(VITALITY_CHEST_COLLECT_CALL_OFFSET),
        "with bytes:",
        hook_bl_bytes["vitality_chest_hook_bl_bytes"].hex(" "),
        "target=",
        hex(hook_targets["vitality_chest_hook_target"]),
    )
    print(
        "Spray paint chest call patched at file offset:",
        hex(SPRAY_PAINT_CHEST_COLLECT_CALL_OFFSET),
        "with bytes:",
        hook_bl_bytes["spray_paint_chest_hook_bl_bytes"].hex(" "),
        "target=",
        hex(hook_targets["spray_paint_chest_hook_target"]),
    )
    print(
        "Sound Player/Music Sheet chest call patched at file offset:",
        hex(SOUND_PLAYER_CHEST_COLLECT_CALL_OFFSET),
        "with bytes:",
        hook_bl_bytes["sound_player_chest_hook_bl_bytes"].hex(" "),
        "target=",
        hex(hook_targets["sound_player_chest_hook_target"]),
    )
    print(
        "Hub switch unlock call patched at file offset:",
        hex(BIG_SWITCH_UNLOCK_CALL_OFFSET),
        "with bytes:",
        hook_bl_bytes["hub_switch_hook_bl_bytes"].hex(" "),
        "target=",
        hex(hook_targets["hub_switch_hook_target"]),
    )
    print(
        "Lever small-switch effect call patched at file offset:",
        hex(SMALL_SWITCH_EFFECT_CALL_OFFSET),
        "with bytes:",
        hook_bl_bytes["small_switch_effect_hook_bl_bytes"].hex(" "),
        "target=",
        hex(hook_targets["small_switch_effect_hook_target"]),
    )
    print(
        "Area Key automatic-transition guard patched at file offset:",
        hex(AUTOMATIC_TRANSITION_GUARD_OFFSET),
        "target=",
        hex(hook_targets["automatic_transition_guard_target"]),
    )
    print(
        "Area Key mirror visual-state callsites patched:",
        len(special_door_state_callsites),
        "target=",
        hex(hook_targets["special_door_state_hook_target"]),
    )
    print(
        "Area Key button-transition callsites patched:",
        len(button_transition_callsites),
        "target=",
        hex(hook_targets["button_special_transition_hook_target"]),
    )
    print(
        "Area Key explicit-room-transition callsites patched:",
        len(explicit_transition_callsites),
        "target=",
        hex(hook_targets["explicit_room_transition_hook_target"]),
    )
    print(
        "Ability request callsites patched:",
        len(ability_transition_callsites),
        "target=",
        hex(hook_targets["ability_transition_hook_target"]),
    )
    print(
        "Ability transition-start callsites patched:",
        len(ability_transition_start_callsites),
        "target=",
        hex(hook_targets["ability_transition_start_hook_target"]),
    )
    print(
        "Single-player game-start callsites patched:",
        ", ".join(hex(offset) for offset in STARTING_COLOR_START_GAME_CALL_OFFSETS),
        "target=",
        hex(hook_targets["starting_color_start_game_hook_target"]),
    )


def main() -> None:
    log_path = setup_logging()
    print(f"Logging to: {log_path}")

    args = parse_args(sys.argv)

    in_path = args["in_path"]
    patch_path = args["patch_path"]

    ensure_patch_output_dir_exists(patch_path)

    lock_path = Path(patch_path).with_suffix(Path(patch_path).suffix + ".lock")
    acquire_run_lock(lock_path)

    source_type = args["source_type"]
    legacy_ignored_out = args.get("legacy_ignored_out")
    hash_debug = bool(args.get("hash_debug"))

    if legacy_ignored_out is not None:
        print("Warning: legacy invocation detected (<in> <out> [patch]).")
        print(f"         Ignoring provided out ROM name: {legacy_ignored_out}")
        print(f"         Using intermediary ROM name: {INTERMEDIARY_ROM}")

    if source_type == "file":
        print(f"Source type: file (reading base ROM from '{ROM_PATH_TMP}')")
    else:
        print("Source type: arg")

    print("Base ROM path:", in_path)

    if hash_debug:
        hash_debug_report(in_path, source_type)

    if os.path.basename(in_path).lower() != "kirby.gba":
        print(f"Note: You specified input ROM '{in_path}'.")
        print("      Your canonical clean ROM is 'kirby.gba'.")
        print("      For consistency, consider using a file named 'kirby.gba' as the clean base.")

    try:
        run_make()

        payload, payload_elf_path = load_payload_and_validate()
        hook_targets = resolve_payload_hook_targets(payload_elf_path)

        rom_base = 0x08000000
        payload_rom_start = rom_base + PAYLOAD_OFFSET
        payload_rom_end = payload_rom_start + len(payload)
        validate_payload_targets(hook_targets, payload_rom_start, payload_rom_end)

        hook_bl_bytes = build_payload_hook_bl_bytes(hook_targets, rom_base)

        rom, _ = load_rom_and_validate(in_path)
        validate_rom_callsite_instructions(rom)
        validate_area_key_native_area_contract(rom)

        (
            special_door_state_callsites,
            button_transition_callsites,
            explicit_transition_callsites,
        ) = discover_area_key_callsites(rom, rom_base)

        (
            boss_already_owned_hook_bl_by_offset,
            ability_transition_callsites,
            ability_transition_start_callsites,
        ) = discover_runtime_callsites(
            rom,
            rom_base,
            hook_targets,
        )

        patch_rom_with_payload(
            rom,
            payload,
            hook_bl_bytes,
            boss_already_owned_hook_bl_by_offset,
            ability_transition_callsites,
            ability_transition_start_callsites,
            special_door_state_callsites,
            button_transition_callsites,
            explicit_transition_callsites,
            hook_targets,
            rom_base,
        )

        with open(INTERMEDIARY_ROM, "wb") as f:
            f.write(rom)

        if hash_debug:
            try:
                patched_md5 = md5_file(INTERMEDIARY_ROM)
                print("")
                print("=== HASH DEBUG (PATCHED ROM OUTPUT) ===")
                print(f"Computed MD5 (expected base ROM):               {load_expected_rom_md5_from_rom_py()}")
                print(f"Computed MD5 (intermediary patched ROM output): {patched_md5}")
                print("Note: These are expected to differ (patched ROM is modified).")
                print("=== HASH DEBUG END ===")
                print("")
            except Exception as e:
                print(f"Warning: failed to compute intermediary patched ROM MD5: {e}")

        print_patch_summary(
            hook_targets,
            hook_bl_bytes,
            list(boss_already_owned_hook_bl_by_offset.keys()),
            ability_transition_callsites,
            ability_transition_start_callsites,
            special_door_state_callsites,
            button_transition_callsites,
            explicit_transition_callsites,
        )

        print("Starting bsdiff generation...")
        generate_bsdiff_with_timeout(in_path, INTERMEDIARY_ROM, patch_path)

        print("BSdiff patch generated:", patch_path)
        print("Patch source (clean):", in_path)
        print("Patch target (baseline):", INTERMEDIARY_ROM)

        safe_unlink(INTERMEDIARY_ROM)
    finally:
        release_run_lock(lock_path)


if __name__ == "__main__":
    main()
