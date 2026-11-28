"""Optional starting unlocks use the real generation and tracker paths."""
from collections import Counter
from copy import deepcopy
from pathlib import Path

import pytest

from NetUtils import decode, encode
from Options import OptionError
from test.general import setup_multiworld

from .. import KirbyAmWorld
from ..enemy_ability_data import GATEABLE_ENEMY_COPY_ABILITIES
from ..options import RandomStartingAbilities
from ..tracker import validate_tracker_data
from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive
from .test_universal_tracker import reconstruct

GATEABLE = {f"{name} Ability" for name in GATEABLE_ENEMY_COPY_ABILITIES}
CODES = {KirbyAmWorld.item_name_to_id[name]: name for name in GATEABLE}


def _archive(tmp_path: Path, *, mode: str, number: int, explicit: bool = False, attempt: int = 0):
    fixture = tmp_path / "player.yaml"
    fixture.write_text(
        "name: Ability Starts\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n"
        f"  ability_randomization_mode: {mode}\n  random_starting_abilities: {number}\n"
        + ("  start_inventory:\n    Beam Ability: 2\n" if explicit else ""),
        encoding="utf-8",
    )
    return load_multidata_from_archive(generate_archive_from_fixture(fixture, tmp_path / str(attempt), seed=773))


@pytest.mark.parametrize("mode,number,explicit", [
    ("off", 3, True),
    ("shuffled", 5, False),
    ("completely_random", len(GATEABLE), False),
])
def test_generated_unlocks_move_from_pool_without_changing_check_count(tmp_path, mode, number, explicit):
    data = _archive(tmp_path, mode=mode, number=number, explicit=explicit)
    slot = decode(encode(data["slot_data"][1]))
    tracker = validate_tracker_data(slot)
    selected = tracker["random_starting_ability_items"]
    assert tracker["options"]["random_starting_abilities"] == number
    assert len(selected) == len(set(selected)) == number and set(selected) <= GATEABLE
    if explicit:
        assert "Beam Ability" not in selected
    held = Counter(CODES[code] for code in data["precollected_items"][1] if code in CODES)
    assert held == Counter(selected) + (Counter({"Beam Ability": 2}) if explicit else Counter())
    locations = data["locations"][1]
    assert len(locations) == 140
    placed = Counter(CODES[v[0]] for v in locations.values() if v[0] in CODES)
    assert placed == Counter({name: 1 for name in GATEABLE - set(selected)})
    # Unlocks move inventory; the gate catalog and native source policy remain intact.
    assert set(slot["ability_gateable_abilities"]) == set(GATEABLE_ENEMY_COPY_ABILITIES)
    assert "Beam" in slot["enemy_copy_ability_whitelist"] and "Ice" in slot["enemy_copy_ability_whitelist"]


def test_repeat_seed_and_tracker_restore_the_same_unlocks_without_an_extra_grant(tmp_path):
    archive = _archive(tmp_path, mode="off", number=3, explicit=True)
    repeat = _archive(tmp_path, mode="off", number=3, explicit=True, attempt=1)
    slot = decode(encode(archive["slot_data"][1]))
    assert slot == decode(encode(repeat["slot_data"][1]))
    assert archive["locations"] == repeat["locations"]
    rebuilt = reconstruct(slot)
    tracker = slot["tracker"]
    assert Counter(i.name for i in rebuilt.precollected_items[1]) == Counter(tracker["precollected_items"])
    assert not set(tracker["random_starting_ability_items"]) & {i.name for i in rebuilt.itempool}
    assert rebuilt.worlds[1].fill_slot_data()["tracker"]["random_starting_ability_items"] == (
        tracker["random_starting_ability_items"])
    invalid = deepcopy(slot)
    invalid["tracker"]["random_starting_ability_items"][0] = "Beam Ability"
    with pytest.raises(ValueError, match="do not match the seed"):
        validate_tracker_data(invalid)


@pytest.mark.parametrize("options,message", [
    ({"ability_gating": 0, "random_starting_abilities": 1}, "requires ability_gating"),
    ({"start_inventory": {"Beam Ability": 2},
      "random_starting_abilities": RandomStartingAbilities.range_end}, "distinct unlocks remain"),
])
def test_incompatible_options_fail_clearly(options, message):
    with pytest.raises(OptionError, match=message):
        setup_multiworld(KirbyAmWorld, seed=773, steps=("generate_early",), options=options)
