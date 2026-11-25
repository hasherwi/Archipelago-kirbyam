"""ROM-free production artifact rejection, including real AP archive dispatch.

All base bytes are sparse synthetic data, not a ROM or the shipped base patch.
BSDIFFs use an empty source to avoid suffix-sorting a large nonempty buffer.
Only the source-data provider is substituted during APProcedurePatch.patch.
"""
import json
from pathlib import Path
from zipfile import ZipFile

import bsdiff4  # type: ignore[import-untyped]
import pytest

from worlds.Files import APTokenTypes
from ..enemy_ability_runtime_patch import ENEMY_SOURCE_CONFIG_LEGACY, ENEMY_SOURCE_CONFIG_ROM_OFFSET
from ..enemy_health_scaling import BOSS_HEALTH_TABLE_OFFSET
from ..phone_generation import PHONE_CONFIG_FILE
from ..phone_protocol import PHONE_CONFIG_OFFSET, PHONE_ENABLED_CONFIG, PHONE_MARKER, validate_phone_pairing
from ..reward_art_config import REWARD_ART_CONFIG_EMPTY, REWARD_ART_CONFIG_ROM_OFFSET
from ..rom import (
    AREA_KEYS_CONFIG_ON, AREA_KEYS_CONFIG_ROM_OFFSET, ENEMY_HEALTH_MULTIPLIER_FILE,
    HEALTH_INITIAL_ROM_OFFSET, KirbyAmPatchExtension, KirbyAmProcedurePatch,
    ROOM_VISIT_ART_CONFIG_ROM_OFFSET, ROOM_VISIT_ART_CORE_ONLY,
)
from ..statue_seed import STATUE_CONFIG_EMPTY, STATUE_CONFIG_ROM_OFFSET
from ..vitality import HEALTH_CONFIG_MAGIC, HEALTH_ROM_TITLE


DISABLED_PHONE_CONFIG = PHONE_MARKER + bytes(4)
PHONE_GUARD_ERROR = "production Phone must remain disabled.*rebuild.*regenerate"
HEALTH_CONFIG = (HEALTH_CONFIG_MAGIC | (10 << 8) | 6).to_bytes(4, "little")
HISTORICAL_PROCEDURE = [
    ("apply_bsdiff4", ["base_patch.bsdiff4"]),
    ("validate_area_keys_base", []),
    ("validate_enemy_source_base", []),
    ("apply_enemy_health_scaling", [ENEMY_HEALTH_MULTIPLIER_FILE]),
    ("apply_tokens", ["token_data.bin"]),
    ("finalize_health_header", []),
]


@pytest.fixture(scope="module")
def synthetic_post_base() -> bytes:
    """Enough synthetic bytes for all real procedure steps and their guards."""
    buffer = bytearray(max(ENEMY_SOURCE_CONFIG_ROM_OFFSET + 36, 0x008C270A))
    buffer[PHONE_CONFIG_OFFSET:PHONE_CONFIG_OFFSET + 12] = DISABLED_PHONE_CONFIG
    buffer[STATUE_CONFIG_ROM_OFFSET:STATUE_CONFIG_ROM_OFFSET + len(STATUE_CONFIG_EMPTY)] = STATUE_CONFIG_EMPTY
    buffer[ROOM_VISIT_ART_CONFIG_ROM_OFFSET:ROOM_VISIT_ART_CONFIG_ROM_OFFSET + 4] = ROOM_VISIT_ART_CORE_ONLY
    reward_art_offset = REWARD_ART_CONFIG_ROM_OFFSET
    buffer[reward_art_offset:reward_art_offset + len(REWARD_ART_CONFIG_EMPTY)] = REWARD_ART_CONFIG_EMPTY
    buffer[AREA_KEYS_CONFIG_ROM_OFFSET:AREA_KEYS_CONFIG_ROM_OFFSET + 4] = AREA_KEYS_CONFIG_ON.to_bytes(4, "little")
    buffer[ENEMY_SOURCE_CONFIG_ROM_OFFSET:ENEMY_SOURCE_CONFIG_ROM_OFFSET + 4] = (
        ENEMY_SOURCE_CONFIG_LEGACY.to_bytes(4, "little"))
    buffer[BOSS_HEALTH_TABLE_OFFSET:BOSS_HEALTH_TABLE_OFFSET + 2] = (8).to_bytes(2, "little")
    return bytes(buffer)


@pytest.fixture(scope="module")
def synthetic_bsdiffs(synthetic_post_base: bytes) -> dict[str, bytes]:
    """Compress one sparse target at a time; keep only the tiny diffs."""
    buffer = bytearray(synthetic_post_base)
    patches = {}
    for name, config in (
        ("disabled", DISABLED_PHONE_CONFIG),
        ("enabled", PHONE_ENABLED_CONFIG),
        ("corrupt", b"X" + DISABLED_PHONE_CONFIG[1:]),
        ("marker-free", bytes(12)),
    ):
        buffer[PHONE_CONFIG_OFFSET:PHONE_CONFIG_OFFSET + 12] = config
        patches[name] = bsdiff4.diff(b"", bytes(buffer))
    return patches


@pytest.fixture
def synthetic_source(monkeypatch: pytest.MonkeyPatch) -> None:
    # Do not read a configured user ROM or reuse any cached source bytes.
    monkeypatch.setattr(KirbyAmProcedurePatch, "get_source_data_with_cache", classmethod(lambda cls: b""))


def _synthetic_patch(base_diff: bytes) -> KirbyAmProcedurePatch:
    patch = KirbyAmProcedurePatch(player=1, player_name="ROM-free Phone guard")
    patch.write_file("base_patch.bsdiff4", base_diff)
    patch.write_file(PHONE_CONFIG_FILE, DISABLED_PHONE_CONFIG)
    patch.write_file(ENEMY_HEALTH_MULTIPLIER_FILE, (150).to_bytes(2, "little"))
    patch.write_token(APTokenTypes.WRITE, HEALTH_INITIAL_ROM_OFFSET, HEALTH_CONFIG)
    patch.write_token(APTokenTypes.WRITE, 0x100, b"synthetic token")
    return patch


def test_room_visit_art_base_guard_rejects_stale_or_seed_written_config(
        synthetic_post_base: bytes) -> None:
    offset = ROOM_VISIT_ART_CONFIG_ROM_OFFSET
    assert KirbyAmPatchExtension.validate_room_visit_art_base(None, synthetic_post_base) is synthetic_post_base
    assert (KirbyAmProcedurePatch.procedure.index(("validate_room_visit_art_base", []))
            < KirbyAmProcedurePatch.procedure.index(("apply_tokens", ["token_data.bin"])))
    for version in (b"\0" * 4, b"APR1", b"APR9"):
        bad = bytearray(synthetic_post_base)
        bad[offset:offset + 4] = version
        with pytest.raises(ValueError, match="RoomSanity reward sprite config missing"):
            KirbyAmPatchExtension.validate_room_visit_art_base(None, bytes(bad))


def test_reward_art_base_guard_rejects_absent_and_prepopulated_table(synthetic_post_base: bytes) -> None:
    offset = REWARD_ART_CONFIG_ROM_OFFSET
    assert KirbyAmPatchExtension.validate_reward_art_base(None, synthetic_post_base) is synthetic_post_base
    steps = KirbyAmProcedurePatch.procedure
    assert steps.index(("validate_reward_art_base", [])) < steps.index(("apply_tokens", ["token_data.bin"]))
    for relative_offset in (0, 4, len(REWARD_ART_CONFIG_EMPTY) - 1):
        malformed = bytearray(synthetic_post_base)
        malformed[offset + relative_offset] ^= 1
        with pytest.raises(ValueError, match="Location reward art config missing"):
            KirbyAmPatchExtension.validate_reward_art_base(None, bytes(malformed))


def _write_archive(patch: KirbyAmProcedurePatch, tmp_path: Path) -> Path:
    patch.write_file("token_data.bin", patch.get_token_binary())
    archive = tmp_path / "synthetic.apkirbyam"
    patch.write(str(archive))
    return archive


def test_phone_validator_returns_valid_bytes_unchanged(synthetic_post_base: bytes) -> None:
    assert KirbyAmPatchExtension.validate_production_phone_disabled(
        KirbyAmProcedurePatch(), synthetic_post_base) is synthetic_post_base


@pytest.mark.parametrize("config", [
    PHONE_MARKER + word.to_bytes(4, "little") for word in (1, 2, 0x100, 0x10000, 0x1000000, 0xFFFFFFFF)
] + [
    b"X" + DISABLED_PHONE_CONFIG[1:], b"APPHN02\0" + bytes(4), b"APPHN01X" + bytes(4), bytes(12),
], ids=["enabled", "word-2", "byte-1", "byte-2", "byte-3", "all-bits",
        "corrupt-marker", "unknown-version", "marker-terminator", "absent-marker"])
def test_phone_validator_rejects_noncanonical_config(config: bytes, synthetic_post_base: bytes) -> None:
    buffer = bytearray(synthetic_post_base)
    buffer[PHONE_CONFIG_OFFSET:PHONE_CONFIG_OFFSET + 12] = config
    with pytest.raises(ValueError, match=PHONE_GUARD_ERROR):
        KirbyAmPatchExtension.validate_production_phone_disabled(KirbyAmProcedurePatch(), bytes(buffer))
    assert buffer[PHONE_CONFIG_OFFSET:PHONE_CONFIG_OFFSET + 12] == config


@pytest.mark.parametrize("length", [0, PHONE_CONFIG_OFFSET - 1, PHONE_CONFIG_OFFSET,
                                    PHONE_CONFIG_OFFSET + 7, PHONE_CONFIG_OFFSET + 8, PHONE_CONFIG_OFFSET + 11])
def test_phone_validator_rejects_missing_or_truncated_buffers(length: int, synthetic_post_base: bytes) -> None:
    with pytest.raises(ValueError, match=PHONE_GUARD_ERROR):
        KirbyAmPatchExtension.validate_production_phone_disabled(KirbyAmProcedurePatch(), synthetic_post_base[:length])


def test_phone_guard_procedure_order_is_serialized(tmp_path: Path, synthetic_bsdiffs: dict[str, bytes]) -> None:
    expected = [HISTORICAL_PROCEDURE[0], ("validate_production_phone_disabled", []),
                *HISTORICAL_PROCEDURE[1:3], ("validate_room16_timer_base", []),
                ("validate_room_visit_art_base", []), ("validate_reward_art_base", []), ("validate_statue_seed_base", []),
                *HISTORICAL_PROCEDURE[3:], ("validate_phone_seed_config", [])]
    assert KirbyAmProcedurePatch.procedure == expected
    archive = _write_archive(_synthetic_patch(synthetic_bsdiffs["disabled"]), tmp_path)
    with ZipFile(archive) as opened:
        manifest = json.loads(opened.read("archipelago.json"))
    assert manifest["procedure"] == [[name, args] for name, args in expected]
    loaded = KirbyAmProcedurePatch(str(archive))
    loaded.read()
    assert loaded.procedure == manifest["procedure"]


def test_archive_patch_dispatch_produces_valid_synthetic_output(
        tmp_path: Path, synthetic_source: None, synthetic_post_base: bytes,
        synthetic_bsdiffs: dict[str, bytes]) -> None:
    archive = _write_archive(_synthetic_patch(synthetic_bsdiffs["disabled"]), tmp_path)
    output = tmp_path / "synthetic.gba"
    KirbyAmProcedurePatch(str(archive)).patch(str(output))

    expected = bytearray(synthetic_post_base)
    expected[HEALTH_INITIAL_ROM_OFFSET:HEALTH_INITIAL_ROM_OFFSET + 4] = HEALTH_CONFIG
    expected[0x100:0x10F] = b"synthetic token"
    expected[BOSS_HEALTH_TABLE_OFFSET:BOSS_HEALTH_TABLE_OFFSET + 2] = (12).to_bytes(2, "little")
    expected[0xA0:0xAC] = HEALTH_ROM_TITLE.ljust(12, b"\0")
    expected[0xBD] = (-sum(expected[0xA0:0xBD]) - 0x19) & 0xFF
    assert output.read_bytes() == expected


@pytest.mark.parametrize("existing_output", [False, True], ids=["absent-output", "existing-output"])
@pytest.mark.parametrize("base,relative_offset,payload", [
    ("disabled", 8, b"\1\0\0\0"),
    ("disabled", 8, b"\0\1\0\0"),
    ("disabled", 0, b"X"),
    ("disabled", 6, b"2"),
    ("enabled", 0, DISABLED_PHONE_CONFIG),
    ("corrupt", 0, DISABLED_PHONE_CONFIG),
    ("marker-free", 0, DISABLED_PHONE_CONFIG),
], ids=["enable-token", "invalid-word-token", "corrupt-marker-token", "unknown-version-token",
        "enabled-base-with-repair", "corrupt-base-with-repair", "missing-marker-base-with-repair"])
def test_archive_rejects_invalid_phone_without_creating_or_overwriting_output(
        tmp_path: Path, synthetic_source: None, synthetic_bsdiffs: dict[str, bytes],
        existing_output: bool, base: str, relative_offset: int, payload: bytes) -> None:
    patch = _synthetic_patch(synthetic_bsdiffs[base])
    patch.write_token(APTokenTypes.WRITE, PHONE_CONFIG_OFFSET + relative_offset, payload)
    archive = _write_archive(patch, tmp_path)
    output = tmp_path / "synthetic.gba"
    sentinel = b"existing output must not be opened or overwritten"
    if existing_output:
        output.write_bytes(sentinel)

    with pytest.raises(ValueError, match=(PHONE_GUARD_ERROR + "|Phone ROM differs from seed intent")):
        KirbyAmProcedurePatch(str(archive)).patch(str(output))

    if existing_output:
        assert output.read_bytes() == sentinel
    else:
        assert not output.exists()


def test_historical_manifest_and_legacy_client_do_not_gain_new_guard(
        tmp_path: Path, synthetic_source: None, synthetic_bsdiffs: dict[str, bytes]) -> None:
    """Old archives execute their saved procedure; this guard is not retroactive."""
    patch = _synthetic_patch(synthetic_bsdiffs["marker-free"])
    patch.procedure = HISTORICAL_PROCEDURE
    archive = _write_archive(patch, tmp_path)
    output = tmp_path / "synthetic-legacy.gba"
    loaded = KirbyAmProcedurePatch(str(archive))
    loaded.patch(str(output))
    assert [(name, args) for name, args in loaded.procedure] == HISTORICAL_PROCEDURE
    config = output.read_bytes()[PHONE_CONFIG_OFFSET:PHONE_CONFIG_OFFSET + 12]
    assert config == bytes(12)
    assert validate_phone_pairing({}, config) == 0


@pytest.mark.parametrize("existing_output", [False, True])
def test_enabled_archive_intent_roundtrip_and_late_corruption(
        tmp_path: Path, synthetic_source: None, synthetic_bsdiffs: dict[str, bytes],
        existing_output: bool) -> None:
    patch = _synthetic_patch(synthetic_bsdiffs["disabled"])
    patch.write_file(PHONE_CONFIG_FILE, PHONE_ENABLED_CONFIG)
    patch.write_token(APTokenTypes.WRITE, PHONE_CONFIG_OFFSET + 8, bytes([1, 0, 0, 0]))
    archive = _write_archive(patch, tmp_path)
    output = tmp_path / "enabled.gba"
    KirbyAmProcedurePatch(str(archive)).patch(str(output))
    assert output.read_bytes()[PHONE_CONFIG_OFFSET:PHONE_CONFIG_OFFSET + 12] == PHONE_ENABLED_CONFIG
    # Later tokens must not undo or corrupt the intended configuration.
    patch.write_token(APTokenTypes.WRITE, PHONE_CONFIG_OFFSET + 8, bytes(4))
    archive = _write_archive(patch, tmp_path)
    rejected = tmp_path / "rejected.gba"
    if existing_output:
        rejected.write_bytes(b"keep me")
    with pytest.raises(ValueError, match="differs from seed intent"):
        KirbyAmProcedurePatch(str(archive)).patch(str(rejected))
    assert rejected.read_bytes() == b"keep me" if existing_output else not rejected.exists()
