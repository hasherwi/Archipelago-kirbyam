"""Strict, reversible main-sync projections; never a native acceptance claim."""
import hashlib
import json
from pathlib import Path
from typing import Any

PIN = Path(__file__).with_name('main_sync_projection.json')


def record() -> dict[str, Any]:
    result: dict[str, Any] = json.loads(PIN.read_text(encoding='utf-8'))
    return result


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _reverse(current: list[str], entry: dict[str, Any]) -> list[str]:
    result = list(current)
    for change in reversed(entry['reverse_slices']):
        start, stop = change['start'], change['stop']
        assert result[start:stop] == change['current'], 'Altered integration slice'
        result[start:stop] = change['main']
    return result


def main_text(name: str, raw: bytes) -> bytes:
    """Reject any unpinned byte, then reverse only the explicitly recorded feature delta."""
    raw = raw.replace(b'\r\n', b'\n')
    entry = record()['files'][name]
    assert _sha(raw) == entry['integrated_sha256'], 'Unreviewed integrated source change'
    result = ''.join(_reverse(raw.decode('utf-8').splitlines(keepends=True), entry)).encode('utf-8')
    assert _sha(result) == entry['main_sha256'], 'Invalid main projection'
    return result


def main_surfaces(surfaces: list[dict[str, Any]]) -> list[dict[str, Any]]:
    entry = record()['surfaces']
    rows = [json.dumps(row, sort_keys=True, separators=(',', ':')) for row in surfaces]
    raw = json.dumps(surfaces, sort_keys=True, separators=(',', ':')).encode()
    assert _sha(raw) == entry['integrated_sha256'], 'Unreviewed integrated surface change'
    result = [json.loads(row) for row in _reverse(rows, entry)]
    raw = json.dumps(result, sort_keys=True, separators=(',', ':')).encode()
    assert _sha(raw) == entry['main_sha256'], 'Invalid main surface projection'
    return result
