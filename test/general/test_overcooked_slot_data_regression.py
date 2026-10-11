"""Narrow quarantine for the stable 0.6.8 OC2 fill failure exposed by PR #960."""

import pytest

from Fill import FillError, distribute_items_restrictive
from NetUtils import convert_to_base_types
from worlds.AutoWorld import AutoWorldRegister, call_all
from . import setup_solo_multiworld


class KnownOvercookedFillError(FillError):
    """Only the exact default-option failure reproduced in upstream 54803be0."""


@pytest.mark.world
@pytest.mark.xfail(
    strict=True,
    raises=KnownOvercookedFillError,
    reason="Upstream 0.6.8 OC2 seed 51633506502411458318 cannot place 25 items; PR #960",
)
def test_overcooked_slot_data_upstream_seed():
    world_type = AutoWorldRegister.testable_worlds.get("Overcooked! 2")
    if world_type is None:
        pytest.skip("Overcooked! 2 is outside the selected test worlds")
    multiworld = setup_solo_multiworld(world_type, seed=51633506502411458318)
    try:
        distribute_items_restrictive(multiworld)
    except FillError as error:
        if str(error).splitlines()[0] != (
            "No more spots to place 25 items. Remaining locations are invalid."
        ):
            raise
        raise KnownOvercookedFillError(str(error)) from error
    # If fill is repaired, still exercise the original serialization assertions.
    # A complete pass becomes strict XPASS so the quarantine must be removed.
    for step in ("post_fill", "finalize_multiworld", "pre_output"):
        call_all(multiworld, step)
    for key, value in multiworld.worlds[1].fill_slot_data().items():
        assert isinstance(key, str), "keys in slot data must be a string"
        convert_to_base_types(value)
