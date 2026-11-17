"""Mutation controls for feature integration, separate from native evidence."""
from copy import deepcopy
from pathlib import Path

import pytest

from ..tools.build_ranged_target_coverage import build_coverage
from .support import main_sync_history as history

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('name', sorted(history.record()['files']))
@pytest.mark.parametrize('ending', [b'\n', b'\r\n'])
def test_exact_feature_projection_accepts_checkout_endings(name: str, ending: bytes) -> None:
    raw = (ROOT / name).read_bytes().replace(b'\r\n', b'\n').replace(b'\n', ending)
    result = history.main_text(name, raw)
    assert history._sha(result) == history.record()['files'][name]['main_sha256']


@pytest.mark.parametrize('name', sorted(history.record()['files']))
@pytest.mark.parametrize('mutation', ['extra', 'missing', 'feature'])
def test_projection_rejects_changed_current_source(name: str, mutation: str) -> None:
    raw = (ROOT / name).read_bytes().replace(b'\r\n', b'\n')
    if mutation == 'extra':
        changed = raw + b'\n'
    elif mutation == 'missing':
        changed = raw[:-1]
    else:
        entry = history.record()['files'][name]
        token = next(line for change in entry['reverse_slices'] for line in change['current'] if line.strip())
        changed = raw.replace(token.encode(), (token.rstrip('\n') + ' \n').encode(), 1)
    assert changed != raw
    with pytest.raises(AssertionError):
        history.main_text(name, changed)


@pytest.mark.parametrize('mutation', ['owner', 'requirement', 'extra', 'delete', 'order'])
def test_surface_projection_rejects_undeclared_changes(mutation: str) -> None:
    rows = deepcopy(build_coverage()['surfaces'])
    history.main_surfaces(rows)
    if mutation == 'owner':
        rows[0]['owner'] += '_MUTATED'
    elif mutation == 'requirement':
        rows[0]['requirement'] = 'can_swim'
    elif mutation == 'extra':
        rows.append(deepcopy(rows[0]))
    elif mutation == 'delete':
        rows.pop()
    else:
        rows[0], rows[1] = rows[1], rows[0]
    with pytest.raises(AssertionError):
        history.main_surfaces(rows)


def test_projection_record_cannot_change_restored_main(monkeypatch: pytest.MonkeyPatch) -> None:
    record = history.record()
    change = record['files']['client.py']['reverse_slices'][0]
    change['main'] = ['# unreviewed historical replacement\n']
    monkeypatch.setattr(history, 'record', lambda: record)
    with pytest.raises(AssertionError, match='Invalid main projection'):
        history.main_text('client.py', (ROOT / 'client.py').read_bytes())


@pytest.mark.parametrize('mutation', ['lever_requirement', 'same_owner_order'])
def test_composed_lever_projection_rejects_mutations(mutation: str) -> None:
    rows = deepcopy(build_coverage()['surfaces'])
    history.main_surfaces(rows)
    if mutation == 'lever_requirement':
        row = next(row for row in rows if 'ROOM_5_05__LOGIC__CHUTE_SIDE' in row['owner'])
        row['requirement'] = 'can_swim'
    else:
        index = next(i for i in range(len(rows) - 1)
                     if rows[i]['owner'] == rows[i + 1]['owner'] and rows[i] != rows[i + 1])
        rows[index], rows[index + 1] = rows[index + 1], rows[index]
    with pytest.raises(AssertionError):
        history.main_surfaces(rows)
