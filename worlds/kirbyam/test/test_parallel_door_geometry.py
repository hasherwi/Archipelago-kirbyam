"""Check conservative static geometry semantics independently of the retail image."""
import pytest

from ..tools.review_parallel_door_geometry import decode_rl, reachable_cells


def test_native_rl_literal_run_and_strict_size():
    # Two literal bytes and a three-cell repeated run.
    stream = bytes([0x30, 5, 0, 0, 1, 0, 0xF5, 0x80, 0x0D])
    assert decode_rl(stream, 0, 5) == bytes([0, 0xF5, 0x0D, 0x0D, 0x0D])
    with pytest.raises(ValueError, match="dimensions"):
        decode_rl(stream, 0, 4)


def test_static_model_never_enters_plain_wall_or_treats_breakables_as_clear():
    data = bytes([0, 0xF5, 0, 0x0D, 0])
    assert reachable_cells(data, 5, 1, (0, 0), optimistic=False) == {(0, 0)}
    assert reachable_cells(data, 5, 1, (0, 0), optimistic=True) == {(0, 0), (1, 0), (2, 0)}
    assert not reachable_cells(data, 5, 1, (3, 0), optimistic=True)
