from __future__ import annotations

import hashlib
from typing import Dict, Iterable, Tuple


def _stable_hash32(text: str) -> int:
    # Deterministic across runs and machines (unlike Python's built-in hash()).
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], byteorder="big", signed=False)


def build_id_map(keys: Iterable[str], base_id: int, namespace: str) -> Dict[str, int]:
    """
    Allocate deterministic numeric IDs for a set of keys.

    - Uses a stable hash of (namespace + ":" + key)
    - Produces values in a wide range above base_id
    - Detects collisions and raises if they occur

    You MUST keep base_id stable once published.
    
    IDs are derived from canonical YAML keys (not names).
    Keys must remain stable once published.
    
    """
    mapping: Dict[str, int] = {}
    used: Dict[int, str] = {}

    for key in sorted(keys):
        h = _stable_hash32(f"{namespace}:{key}")
        # Spread IDs in a large space while keeping them positive.
        assigned = base_id + (h % 1_000_000_000)

        if assigned in used and used[assigned] != key:
            other = used[assigned]
            raise ValueError(
                f"ID collision for namespace '{namespace}': '{key}' and '{other}' -> {assigned}. "
                f"Change base_id or adjust key(s)."
            )

        used[assigned] = key
        mapping[key] = assigned

    return mapping
