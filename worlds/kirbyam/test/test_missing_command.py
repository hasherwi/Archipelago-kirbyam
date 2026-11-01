"""Exercise Kirby's multiword missing filter through the actual shlex dispatcher."""
from types import SimpleNamespace
from typing import Any

import pytest
from CommonClient import ClientCommandProcessor

from ..client import KirbyAmClient, _build_kirbyam_command_processor, _patch_kirbyam_command_processor


def processor(base: type = ClientCommandProcessor, game: str = KirbyAmClient.game) -> tuple[Any, list[str]]:
    cls = _build_kirbyam_command_processor(base)
    ctx = SimpleNamespace(
        game=game,
        location_names={game: {1: 'Room 5-01', 2: 'Room 5-02', 3: 'Room 6-01', 4: 'Room 5-03'}},
        locations_checked={4}, missing_locations={1, 3, 4}, checked_locations={2},
    )
    command = cls(ctx)
    output: list[str] = []
    command.output = output.append
    return command, output


@pytest.mark.parametrize('raw,expected', [
    ('/missing Room 5', ['Missing: Room 5-01', 'Checked: Room 5-02']),
    ('/missing "Room 5"', ['Missing: Room 5-01', 'Checked: Room 5-02']),
    ("/missing 'Room 5'", ['Missing: Room 5-01', 'Checked: Room 5-02']),
    ('/missing   Room    5', ['Missing: Room 5-01', 'Checked: Room 5-02']),
    ('/missing 6-01', ['Missing: Room 6-01']),
    ('/missing', ['Missing: Room 5-01', 'Checked: Room 5-02', 'Missing: Room 6-01']),
    ('/missing ""', ['Missing: Room 5-01', 'Checked: Room 5-02', 'Missing: Room 6-01']),
    ('/missing nowhere', []),
])
def test_missing_filter_actual_dispatch(raw: str, expected: list[str]) -> None:
    command, output = processor()
    assert command(raw) is True
    assert [line for line in output if line.startswith(('Missing:', 'Checked:'))] == expected
    assert not any('Traceback' in line or 'TypeError' in line for line in output)
    if not expected:
        assert output == ['No missing location checks found.']


@pytest.mark.parametrize('raw', ['/missing', '/missing 6-01', '/missing "Room 5"', '/missing Room 5'])
def test_other_game_keeps_original_dispatch_semantics(raw: str) -> None:
    wrapped, wrapped_output = processor(game='Other Game')
    base = ClientCommandProcessor(wrapped.ctx)
    base_output: list[str] = []
    setattr(base, "output", base_output.append)
    assert wrapped(raw) == base(raw)
    # Traceback frame locations differ; the original argument error must remain.
    if raw == '/missing Room 5':
        assert 'TypeError' in '\n'.join(wrapped_output)
        assert 'TypeError' in '\n'.join(base_output)
    else:
        assert wrapped_output == base_output


def test_already_patched_base_preserves_original_missing_without_recursion() -> None:
    class IsolatedCommands(ClientCommandProcessor):
        pass

    original = IsolatedCommands._cmd_missing
    patched = _patch_kirbyam_command_processor(IsolatedCommands)
    assert _patch_kirbyam_command_processor(patched) is patched
    assert getattr(patched, "_kirbyam_original__cmd_missing") is original
    command, output = processor(patched)
    assert command('/missing Room 5') is True
    assert output[:2] == ['Missing: Room 5-01', 'Checked: Room 5-02']
    assert getattr(type(command), "_kirbyam_original__cmd_missing") is original
