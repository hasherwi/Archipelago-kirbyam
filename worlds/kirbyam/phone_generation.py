"""Canonical per-seed Phone patch intent, separate from route admission.

Encoding an enabled intent is not permission to generate it: the world must
first admit the complete progression profile. The base ROM remains disabled.
"""
from .phone_protocol import PHONE_ENABLED_CONFIG, PHONE_MARKER

PHONE_CONFIG_FILE = "phone_config.bin"
PHONE_DISABLED_CONFIG = PHONE_MARKER + bytes(4)


def phone_patch_config(enabled: bool) -> bytes:
    if type(enabled) is not bool:
        raise ValueError("Phone generation intent must be a boolean")
    return PHONE_ENABLED_CONFIG if enabled else PHONE_DISABLED_CONFIG


def validate_phone_patch_intent(raw: bytes) -> bytes:
    if type(raw) is not bytes or raw not in (PHONE_DISABLED_CONFIG, PHONE_ENABLED_CONFIG):
        raise ValueError("invalid Phone patch intent; regenerate the seed")
    return raw
