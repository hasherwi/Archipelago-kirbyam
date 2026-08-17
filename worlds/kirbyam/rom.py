"""ROM patch support for Kirby & The Amazing Mirror.

The world emits AP procedure patches that apply:
- the shipped KirbyAM base bsdiff patch artifact
- per-seed enemy-health table scaling
- per-seed token writes (auth token and selected runtime feature writes)

Issue #338 adds deterministic enemy copy-ability remap token writes for
non-off enemy randomization modes.
Issue #880 scales native enemy/miniboss/boss HP tables after the shared base
patch is applied, so all native table consumers see the same per-seed values.
"""

from typing import TYPE_CHECKING

from settings import get_settings
from worlds.Files import APPatchExtension, APProcedurePatch, APTokenMixin, APTokenTypes

from .data import data
from .enemy_ability_data import ABILITY_NAME_TO_ID, GATEABLE_ENEMY_COPY_ABILITIES
from .enemy_ability_runtime_patch import (
    build_enemy_copy_runtime_patch_writes,
    build_statue_runtime_allowed_mask,
)
from .enemy_health_scaling import (
    ENEMY_HEALTH_MULTIPLIER_MAX,
    ENEMY_HEALTH_MULTIPLIER_MIN,
    scale_enemy_health_tables,
)
from .options import AbilityRandomizationMode

if TYPE_CHECKING:
    from . import KirbyAmWorld


# Fixed per-seed words reserved by kirby_ap_payload/linker.ld. Starting color
# is consumed before CreateKirby so the first gameplay palette is correct. The
# gate and statue masks retain their existing offsets for patch compatibility.
STARTING_KIRBY_COLOR_INITIAL_ROM_OFFSET = 0x0015F694
ABILITY_GATE_MASK_INITIAL_ROM_OFFSET = 0x0015F698
ABILITY_RANDOMIZATION_STATUE_ALLOWED_MASK_ROM_OFFSET = 0x0015F69C
ENEMY_HEALTH_MULTIPLIER_FILE = "enemy_health_multiplier.bin"


def _initial_ability_gate_mask(world: "KirbyAmWorld") -> int:
    """Return the seed's gateable ability-ID mask, or zero when gating is off."""
    if not bool(world.options.ability_gating.value):
        return 0

    mask = 0
    for ability_name in GATEABLE_ENEMY_COPY_ABILITIES:
        ability_id = ABILITY_NAME_TO_ID.get(ability_name)
        if ability_id is None or not 0 < ability_id <= 31:
            raise ValueError(
                f"gateable ability must have a runtime ID within 1..31: {ability_name}"
            )
        mask |= 1 << ability_id
    return mask & 0xFFFFFFFF


class KirbyAmPatchExtension(APPatchExtension):
    """KirbyAM-specific AP procedure steps used while applying `.apkirbyam`."""

    game = "Kirby & The Amazing Mirror"

    @staticmethod
    def apply_enemy_health_scaling(
        caller: APProcedurePatch,
        rom: bytes,
        multiplier_file: str,
    ) -> bytes:
        """Scale native enemy HP tables using the seed-resolved percentage."""
        multiplier_data = caller.get_file(multiplier_file)
        if len(multiplier_data) != 2:
            raise ValueError(
                "KirbyAM enemy-health multiplier metadata must contain exactly "
                f"2 bytes, got {len(multiplier_data)}"
            )

        percent = int.from_bytes(multiplier_data, "little")
        return scale_enemy_health_tables(rom, percent)


class KirbyAmProcedurePatch(APProcedurePatch, APTokenMixin):
    game = "Kirby & The Amazing Mirror"
    # Calculated with PowerShell Command:
    # Get-FileHash "D:\\...\\Kirby & The Amazing Mirror (USA).gba" -Algorithm MD5
    hash = "DF5EFE075B35859529EBF82A4D824458"  # md5 hash of base USA rom
    patch_file_ending = ".apkirbyam"
    result_file_ending = ".gba"

    procedure = [
        ("apply_bsdiff4", ["base_patch.bsdiff4"]),
        ("apply_enemy_health_scaling", [ENEMY_HEALTH_MULTIPLIER_FILE]),
        ("apply_tokens", ["token_data.bin"]),
    ]

    @classmethod
    def get_source_data(cls) -> bytes:
        with open(get_settings().kirby_am_settings.rom_file, "rb") as infile:
            base_rom_bytes = bytes(infile.read())

        return base_rom_bytes


def write_tokens(world: "KirbyAmWorld", patch: KirbyAmProcedurePatch) -> None:
    health_multiplier = int(world.options.enemy_health_multiplier.value)
    if not ENEMY_HEALTH_MULTIPLIER_MIN <= health_multiplier <= ENEMY_HEALTH_MULTIPLIER_MAX:
        raise ValueError(
            "enemy health multiplier must be within "
            f"{ENEMY_HEALTH_MULTIPLIER_MIN}..{ENEMY_HEALTH_MULTIPLIER_MAX}: "
            f"{health_multiplier}"
        )
    # The custom procedure consumes this after applying the shared base patch
    # and before per-seed token writes. Two bytes cover the full supported range.
    patch.write_file(
        ENEMY_HEALTH_MULTIPLIER_FILE,
        health_multiplier.to_bytes(2, "little"),
    )

    # Only write the auth token if a ROM address has been configured.
    # The injected base patch is expected to reserve 16 bytes for this.
    auth_addr = data.rom_addresses.get("auth_token") or data.rom_addresses.get("gArchipelagoInfo")
    if auth_addr is not None:
        patch.write_token(APTokenTypes.WRITE, auth_addr, world.auth)

    resolved_color_id, _ = world._get_resolved_starting_kirby_color()
    if not 0 <= int(resolved_color_id) <= 13:
        raise ValueError(
            f"resolved starting Kirby color must be within 0..13: {resolved_color_id}"
        )
    patch.write_token(
        APTokenTypes.WRITE,
        STARTING_KIRBY_COLOR_INITIAL_ROM_OFFSET,
        int(resolved_color_id).to_bytes(4, "little"),
    )

    mode = int(world.options.ability_randomization_mode.value)
    include_statues = bool(world.options.ability_randomization_statues.value)

    policy = getattr(world, "_enemy_copy_ability_policy", None)
    if mode != AbilityRandomizationMode.option_off and not isinstance(policy, dict):
        raise ValueError(
            "enemy_copy_ability_policy must be initialized before writing enemy "
            "copy-ability runtime patch tokens when ability randomization is enabled"
        )

    # Seed the gating mask in ROM as a deny-by-default fallback before the
    # BizHawk client can synchronize live gate/unlock state. The client remains
    # authoritative after connection and may add unlock bits at runtime.
    patch.write_token(
        APTokenTypes.WRITE,
        ABILITY_GATE_MASK_INITIAL_ROM_OFFSET,
        _initial_ability_gate_mask(world).to_bytes(4, "little"),
    )

    # Always overwrite the reserved statue word so a reused base patch cannot
    # retain another seed's policy. Off mode has no policy requirement and
    # therefore writes the explicit disabled mask directly.
    statue_allowed_mask = (
        build_statue_runtime_allowed_mask(policy, include_statues=include_statues)
        if isinstance(policy, dict)
        else 0
    )
    patch.write_token(
        APTokenTypes.WRITE,
        ABILITY_RANDOMIZATION_STATUE_ALLOWED_MASK_ROM_OFFSET,
        statue_allowed_mask.to_bytes(4, "little"),
    )

    if isinstance(policy, dict):
        ability_writes = build_enemy_copy_runtime_patch_writes(
            policy,
            include_statues=include_statues,
        )
        for rom_offset, ability_id in sorted(ability_writes.items()):
            patch.write_token(APTokenTypes.WRITE, rom_offset, bytes([ability_id]))

    patch.write_file("token_data.bin", patch.get_token_binary())
