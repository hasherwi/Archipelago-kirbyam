"""CI case202: preserve the policy stream while allowing the rare Room16 conjunction."""
from pathlib import Path

import pytest
from .. import check_accessibility
from ..peg_traversal import KirbyAmRoom16SourceError
from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive
from .support.check_accessibility import audit_local_checks


def _emulate_legacy_room_statues(monkeypatch):
    from ..traversal import SourcePolicy

    grant = SourcePolicy.grant

    def historical_grant(self, key, permitted, native_grants=(), *, native_room=None):
        return grant(self, key, permitted, native_grants)

    monkeypatch.setattr(SourcePolicy, 'grant', historical_grant)


@pytest.mark.parametrize(
    'historical_statues,cap,attempts,winning_seed',
    [
        pytest.param(True, 8192, 8192, None, id='historical-cap-exhaustion'),
        pytest.param(False, 3353, 3353, None, id='fixed-statues-before-first-witness'),
        pytest.param(False, None, 3354, 9372867150608014686, id='fixed-statues-full-archive'),
    ],
)
def test_exact_ci_seed_exhaustion_and_full_archive(monkeypatch, tmp_path, historical_statues, cap,
                                                  attempts, winning_seed):
    import worlds.kirbyam as kirby
    if historical_statues:
        # Replay the former grant rules only for the historical failure control.
        _emulate_legacy_room_statues(monkeypatch)

    original = kirby.validate_peg_assignment
    validate = check_accessibility.validate_all_checks
    draws = 0
    last = None
    audited = []

    def select(initial, factory, statues, **kwargs):
        nonlocal draws, last
        assert initial['seed'] == 2450128862376293350
        assert kwargs['max_attempts'] == 16384
        assert kwargs['require_room16'] and not kwargs['advanced']
        draws, last = 1, initial

        def counted():
            nonlocal draws, last
            last = factory()
            draws += 1
            return last

        if cap is not None:
            kwargs['max_attempts'] = cap
            kwargs['allow_room16_shuffle_repair'] = False
        kwargs["logic_aware_shuffle"] = False
        return original(initial, counted, statues, **kwargs)

    def audit(world, players):
        audited.append(world)
        return validate(world, players)

    monkeypatch.setattr(kirby, 'validate_peg_assignment', select)
    monkeypatch.setattr(check_accessibility, 'validate_all_checks', audit)
    fixture = Path(__file__).parent / 'data/fuzz_room16_source_budget_202.yaml'
    if winning_seed is None:
        with pytest.raises(KirbyAmRoom16SourceError, match=f'after {cap} attempts'):
            generate_archive_from_fixture(fixture, tmp_path, seed=587276755)
        assert draws == attempts and not audited
        assert not list(tmp_path.glob('*.zip'))
    else:
        archive = generate_archive_from_fixture(fixture, tmp_path, seed=587276755)
        assert draws == attempts
        assert last is not None and last['seed'] == winning_seed
        world, = audited
        actual = audit_local_checks(world, 1)
        assert actual.unfilled == actual.inventory_unreachable == actual.progression_unreachable == ()
        selected = load_multidata_from_archive(archive)['slot_data'][1]['enemy_copy_ability_policy']
        assert {**selected, 'allowed_abilities': list(selected['allowed_abilities'])} == last
        assert selected['mode'] == 1 and selected['ability_randomization_no_ability_weight'] == 71
        assert 'room16_switch_timer_frames' not in selected
        assert len(list(tmp_path.glob('*.zip'))) == 1


def test_room16_prerequisite_short_circuits_without_reordering_candidates(monkeypatch):
    from types import SimpleNamespace
    from .. import peg_traversal as peg, traversal_rules as rules, wheel_traversal as wheel
    policies = [{'mode': 1, 'seed': index} for index in range(3)]
    monkeypatch.setattr(peg, 'SourcePolicy', lambda raw, statues: SimpleNamespace(mode=1, policy=raw))
    checked = []
    monkeypatch.setattr(rules, 'static_room16_witness', lambda p, **kwargs: p.policy['seed'] > 0)
    def wheel_check(p):
        checked.append(p.policy['seed'])
        return p.policy['seed'] == 2
    monkeypatch.setattr(wheel, 'static_wheel_witness', wheel_check)
    monkeypatch.setattr(peg, '_assignment_has_witness', lambda *args: True)
    monkeypatch.setattr(rules, 'static_extra_witness', lambda *args, **kwargs: True)
    stream = iter(policies[1:])
    result = peg.validate_peg_assignment(policies[0], lambda: next(stream), False,
                                       max_attempts=3, require_room16=True)
    assert result is policies[2]
    assert checked == [1, 2]



@pytest.mark.parametrize("historical_statues", [False, True], ids=["fixed-statues", "legacy-statues"])
@pytest.mark.parametrize(
    ("fixture", "seed", "initial_policy_seed", "weight", "completion", "natural_policy_seed"),
    [
        ("369", 89287592, 6697895001130690181, 83, False, 39282560134454757),
        ("497", 353521934, 16414413953470095692, 96, True, 5719372416106836257),
    ],
    ids=["CI-369-room-sanity", "CI-497-full-completion"],
)
def test_exact_high_weight_room16_seed_uses_reviewed_source(
    monkeypatch, tmp_path, fixture, seed, initial_policy_seed, weight, completion,
    natural_policy_seed, historical_statues,
):
    from collections import Counter
    from io import BytesIO
    from zipfile import ZipFile

    import worlds.kirbyam as kirby
    from ..enemy_ability_data import ABILITY_NAME_TO_ID, ABILITY_SOURCES
    from ..enemy_ability_runtime_patch import (
        ROOM16_FOLEY_SWAP, build_enemy_copy_spoiler_rows,
    )
    from ..rom import KirbyAmPatchExtension, KirbyAmProcedurePatch
    from ..room16_timer import ROM_OFFSET
    from ..traversal import SourcePolicy
    from ..traversal_rules import static_room16_witness

    if historical_statues:
        # Retain the exact CI repair regressions under the grant semantics
        # that exhausted the natural stream. Production fixed statues are
        # separately required to use their first natural qualifying policy.
        _emulate_legacy_room_statues(monkeypatch)
    select = kirby.validate_peg_assignment
    validate = check_accessibility.validate_all_checks
    audited = []

    def capture(initial, *args, **kwargs):
        assert initial['seed'] == initial_policy_seed
        assert kwargs['require_room16'] == (not completion)
        assert kwargs['room16_for_completion'] == completion
        assert kwargs['allow_room16_shuffle_repair']
        kwargs['logic_aware_shuffle'] = False  # Replay the historical retry stream.
        return select(initial, *args, **kwargs)

    def audit(world, players):
        audited.append(world)
        return validate(world, players)

    monkeypatch.setattr(kirby, 'validate_peg_assignment', capture)
    monkeypatch.setattr(check_accessibility, 'validate_all_checks', audit)
    archive = generate_archive_from_fixture(
        Path(__file__).parent / f'data/fuzz_room16_source_budget_{fixture}.yaml', tmp_path, seed=seed,
    )
    world, = audited
    actual = audit_local_checks(world, 1)
    assert actual.unfilled == actual.inventory_unreachable == actual.progression_unreachable == ()
    if fixture == "369":
        from BaseClasses import CollectionState
        from Options import Accessibility

        if historical_statues:
            stone, = (loc for loc in world.get_filled_locations()
                      if loc.item is not None and loc.item.name == "Stone Ability")
            assert stone.locked and stone.can_reach(CollectionState(world))
        assert world.worlds[1].options.accessibility.value == Accessibility.option_minimal
        assert "Room 4-16" in {loc.name for loc in world.get_filled_locations()}
    policy = load_multidata_from_archive(archive)['slot_data'][1]['enemy_copy_ability_policy']
    assert policy['mode'] == 1 and policy['ability_randomization_no_ability_weight'] == weight
    assert 'room16_switch_timer_frames' not in policy
    assert static_room16_witness(SourcePolicy(policy, True))
    if not historical_statues:
        assert ROOM16_FOLEY_SWAP not in policy
        assert policy['seed'] == natural_policy_seed
        assert world.early_items[1].get("Stone Ability", 0) == 0
        return

    donor = policy[ROOM16_FOLEY_SWAP]
    base = {key: value for key, value in policy.items() if key != ROOM16_FOLEY_SWAP}
    old = {(kind, key): ability for kind, key, ability in build_enemy_copy_spoiler_rows(base, True)}
    new = {(kind, key): ability for kind, key, ability in build_enemy_copy_spoiler_rows(policy, True)}
    assert Counter(old.values()) == Counter(new.values())
    changed = {key for key in old if old[key] != new[key]}
    assert {key for _, key in changed} == {'FOLEY', donor}
    assert all(kind != 'statue' for kind, _ in changed)
    foley, = (key for key in changed if key[1] == 'FOLEY')
    other, = (key for key in changed if key[1] == donor)
    assert (new[foley], new[other]) == (old[other], old[foley])
    assert not static_room16_witness(SourcePolicy(base, True))
    with ZipFile(archive) as generated:
        patch_name, = (name for name in generated.namelist() if name.endswith('.apkirbyam'))
        patch = KirbyAmProcedurePatch()
        patch.read(BytesIO(generated.read(patch_name)))
    untouched = b'\xff' * 0x1010000
    patched = KirbyAmPatchExtension.apply_tokens(patch, untouched, 'token_data.bin')
    for _, source_key in changed:
        source, = (row for row in ABILITY_SOURCES if row.key == source_key)
        patched_id = ABILITY_NAME_TO_ID[new[source.kind, source_key]]
        assert all(patched[address] == patched_id for address in source.addresses)
    assert patched[ROM_OFFSET:ROM_OFFSET + 2] == b'\x00\x00'


@pytest.mark.parametrize("existing", ["none", "local request", "global request", "precollected", "planned", "not needed"])
def test_repaired_minimal_stone_hint_is_local_to_affected_slot(monkeypatch, existing):
    from types import SimpleNamespace
    from BaseClasses import Item, ItemClassification
    from Options import Accessibility
    from test.general import setup_multiworld
    from worlds.AutoWorld import AutoWorldRegister
    from .. import KirbyAmWorld
    from ..enemy_ability_runtime_patch import ROOM16_FOLEY_SWAP

    foreign = AutoWorldRegister.world_types["APQuest"]
    mw = setup_multiworld([KirbyAmWorld, KirbyAmWorld, foreign], steps=(), seed=17)
    stone = "Stone Ability"
    for player in mw.player_ids:
        mw.worlds[player].options.accessibility = Accessibility(Accessibility.option_minimal)
        item = Item(stone, ItemClassification.progression, 3860109, player)
        mw.itempool.append(item)
    mw.worlds[1]._enemy_copy_ability_policy = {ROOM16_FOLEY_SWAP: "BOXIN"}
    original = tuple(world.options.accessibility for world in mw.worlds.values())
    first, *_ = mw.itempool
    if existing == "local request":
        mw.local_early_items[1][stone] = 2
    elif existing == "global request":
        mw.early_items[1][stone] = 2
    elif existing == "precollected":
        mw.precollected_items[1].append(first)
    elif existing == "planned":
        # Even deliberately locked plando not represented by a pool removal
        # must not be replaced, including an unreachable forced placement.
        locked = SimpleNamespace(item=first, locked=True, can_reach=lambda _: False)
        monkeypatch.setattr(mw, "get_filled_locations", lambda: [locked])

    class Permissions:
        def __init__(self, has_stone=True):
            self.has_stone = has_stone

        def copy(self):
            return Permissions(self.has_stone)

        def remove(self, item):
            assert item is first
            self.has_stone = False

        def sweep_for_advancements(self):
            pass

    check = SimpleNamespace(address=1, can_reach=lambda state: existing == "not needed" or state.has_stone)
    monkeypatch.setattr(mw, "get_all_state", lambda *, perform_sweep: Permissions())
    monkeypatch.setattr(mw, "get_locations", lambda player=None: [check] if player == 1 else [])
    KirbyAmWorld.stage_pre_fill(mw)
    assert [mw.early_items[p].get(stone, 0) for p in mw.player_ids] == [
        {"none": 1, "global request": 2}.get(existing, 0), 0, 0,
    ]
    assert mw.local_early_items[1].get(stone, 0) == (2 if existing == "local request" else 0)
    assert tuple(world.options.accessibility for world in mw.worlds.values()) == original
    assert mw.itempool[0] is first


def test_early_hint_leaves_stone_in_pool_when_no_legal_early_placement():
    from BaseClasses import CollectionState
    from Fill import distribute_early_items
    from test.general import setup_multiworld
    from .. import KirbyAmWorld

    mw = setup_multiworld([KirbyAmWorld], seed=21, options={"ability_gating": 1},
                          steps=("generate_early", "create_regions", "create_items", "set_rules"))
    stone = next(item for item in mw.itempool if item.name == "Stone Ability")
    assert stone.advancement
    locations = mw.get_unfilled_locations()
    assert any(loc.can_reach(CollectionState(mw)) for loc in locations)
    for location in locations:
        old_rule = location.item_rule
        location.item_rule = lambda item, old_rule=old_rule: item is not stone and old_rule(item)
    mw.early_items[1][stone.name] = 1
    _, remaining = distribute_early_items(mw, locations, list(mw.itempool))
    assert stone in remaining and stone.location is None
