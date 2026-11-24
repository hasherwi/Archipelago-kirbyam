"""Random Teleport's delivery identity and versioned receipt lottery word."""

from hashlib import sha256

RANDOM_TELEPORT_ITEM_ID = 3860302
RANDOM_TELEPORT_ITEM_NAME = "Random Teleport Trap"
RANDOM_TELEPORT_ROM_MARKER_OFFSET = 0x0100FFC4
RANDOM_TELEPORT_ROM_MARKER = b"APR1"
RANDOM_TELEPORT_NONCE_ADDR = 0x0203B1C0
TRAP_CATALOG_VERSION = 2


# Priority mirrors are chosen only from items preceding this receipt.
RANDOM_TELEPORT_CONNECTION_BITS = {3860401: 29, 3860403: 30, 3860405: 31}


def teleport_nonce(scope: str, key: str) -> int:
    """Independently sample each receipt; retrying its identity keeps this word."""
    identity = f"kirbyam-random-teleport-v1:{scope}:{key}".encode()
    return (int.from_bytes(sha256(identity).digest()[:4], "little") & 0x1FFFFFFF) or 1
