"""Standard shuffle repairs the assignment, not the world seed or grant counts."""
from collections import Counter
import json
from pathlib import Path
import random

import pytest

from .. import KirbyAmWorld
from ..ability_randomization import build_enemy_copy_ability_policy
from ..enemy_ability_data import ABILITY_SOURCES, ABILITY_NAME_TO_ID
from ..enemy_ability_runtime_patch import (
    SHUFFLE_SOURCE_SWAPS, build_enemy_copy_runtime_patch_writes, build_enemy_copy_spoiler_rows,
    shuffled_source_grants,
)
from ..logic_aware_shuffle import constrain_shuffled_abilities
from ..peg_traversal import validate_peg_assignment
from ..traversal import SourcePolicy
from ..traversal_rules import static_room16_witness
from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive


def base_policy(seed=2, mode=1, weight=0):
    return build_enemy_copy_ability_policy(random.Random(seed), mode, False, False, no_ability_weight=weight)


def counts_by_pool(policy, statues):
    grants = shuffled_source_grants(policy, statues)
    return tuple(Counter(v for k, v in grants.items() if k.startswith("STATUE:") is pool)
                 for pool in (False, True))


@pytest.mark.parametrize(("weight", "room16"), [(0, True), (100, False)])
def test_repair_preserves_each_pool_and_reconstructs_exact_outputs(weight, room16):
    raw = base_policy(weight=weight)
    plan = constrain_shuffled_abilities(
        raw, include_statues=True, require_all=True, room16=room16, area_keys=False)
    assert plan["seed"] == raw["seed"] and plan[SHUFFLE_SOURCE_SWAPS]
    assert plan == constrain_shuffled_abilities(
        raw, include_statues=True, require_all=True, room16=room16, area_keys=False)
    decoded = json.loads(json.dumps(plan))
    assert counts_by_pool(decoded, True) == counts_by_pool(raw, True)
    assert build_enemy_copy_spoiler_rows(plan, True) == build_enemy_copy_spoiler_rows(decoded, True)
    writes = build_enemy_copy_runtime_patch_writes(decoded, True)
    assert writes == build_enemy_copy_runtime_patch_writes(plan, True)
    for source in ABILITY_SOURCES:
        name = shuffled_source_grants(decoded, True).get(source.key)
        if name is not None:
            assert all(writes[address] == ABILITY_NAME_TO_ID[name] for address in source.addresses)
    if room16:
        assert not static_room16_witness(SourcePolicy(raw, True))
        assert static_room16_witness(SourcePolicy(decoded, True))


def test_no_policy_redraw_even_with_room16_and_whole_catalog():
    raw = base_policy()
    def draw():
        pytest.fail("logic-aware shuffle must not draw a replacement policy seed")
    selected = validate_peg_assignment(raw, draw, True, require_room16=True, logic_aware_shuffle=True)
    assert selected[SHUFFLE_SOURCE_SWAPS]
    assert selected["seed"] == raw["seed"]


@pytest.mark.parametrize(("mode", "advanced"), [(0, False), (2, False), (1, True)])
def test_new_shuffle_not_run_in_other_modes_or_advanced(monkeypatch, mode, advanced):
    from .. import logic_aware_shuffle

    def forbidden(*args, **kwargs):
        pytest.fail("constraint shuffle used outside Standard Shuffled")
    monkeypatch.setattr(logic_aware_shuffle, "constrain_shuffled_abilities", forbidden)
    raw = base_policy(seed=1, mode=mode)
    selected = validate_peg_assignment(
        raw, lambda: raw, False, logic_aware_shuffle=True, advanced=advanced, max_attempts=1,
    )
    assert selected is raw
    assert SHUFFLE_SOURCE_SWAPS not in selected


@pytest.mark.parametrize("swaps", [
    [["FOLEY", "NOT_A_SOURCE"]], [["FOLEY", "FOLEY"]],
    [["FOLEY", "STATUE:353900"]], [["STATUE:353900", "STATUE:3538FC"]],
])
def test_invalid_or_disabled_swaps_fail_closed(swaps):
    raw = {**base_policy(), SHUFFLE_SOURCE_SWAPS: swaps}
    with pytest.raises(ValueError, match="shuffle|swap"):
        shuffled_source_grants(raw, include_statues=False)


def test_real_room16_archive_keeps_first_policy_seed(monkeypatch, tmp_path):
    from .. import check_accessibility
    from .support.check_accessibility import audit_local_checks
    import worlds.kirbyam as kirby

    early = kirby.validate_peg_assignment
    finalize = check_accessibility.validate_all_checks
    base = []
    audited = []

    def choose(initial, factory, include_statues, **options):
        assert options["logic_aware_shuffle"] and not options["advanced"]
        base.append(initial)
        def fail():
            pytest.fail("production attempted to redraw a whole source policy")
        return early(initial, fail, include_statues, **options)

    def verify(world, players):
        audited.append(world)
        return finalize(world, players)

    monkeypatch.setattr(kirby, "validate_peg_assignment", choose)
    monkeypatch.setattr(check_accessibility, "validate_all_checks", verify)
    fixture = Path(__file__).parent / "data" / "fuzz_room16_source_budget_202.yaml"
    archive = generate_archive_from_fixture(fixture, tmp_path, seed=587276755)
    slot_policy = load_multidata_from_archive(archive)["slot_data"][1]["enemy_copy_ability_policy"]
    assert slot_policy["seed"] == base[0]["seed"]
    assert slot_policy[SHUFFLE_SOURCE_SWAPS]
    assert counts_by_pool(slot_policy, True) == counts_by_pool(base[0], True)
    check = audit_local_checks(audited[0], 1)
    assert check.unfilled == check.inventory_unreachable == check.progression_unreachable == ()
    assert audited[0].worlds[1].game == KirbyAmWorld.game


def test_missing_burning_can_be_reserved_only_in_exact_statue_profile():
    from ..enemy_ability_runtime_patch import SHUFFLE_STATUE_RESERVATIONS

    raw = {**base_policy(weight=100), "seed": 907056349273356545}
    before = shuffled_source_grants(raw, True)
    assert "Burning" not in {grant for key, grant in before.items() if key.startswith("STATUE:")}
    selected = constrain_shuffled_abilities(
        raw, include_statues=True, require_all=True, room16=False, area_keys=True)
    reserves = selected[SHUFFLE_STATUE_RESERVATIONS]
    assert "Burning" in reserves.values()
    assert selected["seed"] == raw["seed"]
    roster_with_reserved_grants = {**raw, SHUFFLE_STATUE_RESERVATIONS: reserves}
    assert counts_by_pool(selected, True) == counts_by_pool(roster_with_reserved_grants, True)
    assert counts_by_pool(selected, True)[0] == counts_by_pool(raw, True)[0]
    assert len(shuffled_source_grants(selected, True)) == len(before)
    with pytest.raises(ValueError, match="reservation"):
        build_enemy_copy_runtime_patch_writes(
            {**selected, "ability_randomization_no_ability_weight": 99}, include_statues=True)


def test_advanced_high_weight_shuffle_never_sets_statue_reservations():
    from ..enemy_ability_runtime_patch import SHUFFLE_STATUE_RESERVATIONS
    from .test_mini_traversal import make_world

    world = make_world(1, False, advanced_logic=1, ability_randomization_statues=1,
                       ability_randomization_no_ability_weight=100)
    assert SHUFFLE_STATUE_RESERVATIONS not in world._enemy_copy_ability_policy
    assert SHUFFLE_SOURCE_SWAPS not in world._enemy_copy_ability_policy


@pytest.mark.parametrize("seed,weight,passive,keys", [
    (4142342124837059238, 29, True, True),
    (4794201909486144105, 50, False, False),
])
def test_short_cabbage_sources_repair_earlier_hosted_peg_rosters(
    seed: int, weight: int, passive: bool, keys: bool,
) -> None:
    from ..logic_aware_shuffle import _constraints, proven_roster_shortage

    raw = build_enemy_copy_ability_policy(random.Random(0), 1, False, False,
                                         include_passive_enemies=passive, no_ability_weight=weight)
    raw["seed"] = seed
    initial = SourcePolicy(raw, include_statues=True)
    settings = dict(include_statues=True, require_all=True, room16=True, area_keys=keys)
    assert proven_roster_shortage(raw, **settings) is None
    repaired = SourcePolicy(constrain_shuffled_abilities(raw, **settings), include_statues=True)
    assert all(rule.accepts(repaired) for rule in _constraints(initial, True, True, keys))


@pytest.mark.parametrize("second_key,capacity,bypass,conflict", [
    ("BATAFIRE", 1, False, True),
    ("BATAFIRE", 2, False, False),
    ("FLAMER", 1, False, False),
    ("BATAFIRE", 1, True, False),
])
def test_capacity_certificate_needs_disjoint_families_and_no_alternative(
    second_key: str, capacity: int, bypass: bool, conflict: bool,
) -> None:
    from ..logic_aware_shuffle import _graph_constraint, _shared_roster_cut
    from ..traversal import Node, Placement, Position, Route, TraversalGraph

    def graph(key: str, bypass: bool = False) -> TraversalGraph:
        required = Route("start", "end", capability="metal",
                         allowed_abilities=frozenset({"Burning"}))
        return TraversalGraph(
            (Node("start", 141), Node("end", 141)),
            (required, Route("start", "end")) if bypass else (required,),
            (Placement(node="start", source_key=key, identity=key),),
            (Position("start"),), frozenset({"end"}),
        )

    movable = {"FLAMER": "Burning", "BATAFIRE": "Burning" if capacity == 2 else "Sword"}
    pools = {False: set(movable.values()), True: set()}
    constraints = (_graph_constraint("a", (graph("FLAMER"),)),
                   _graph_constraint("b", (graph(second_key, bypass),)))
    got = _shared_roster_cut(constraints, SourcePolicy({"mode": 0}), movable, pools)
    if conflict:
        assert got == {"ability": "Burning", "pool": "enemy", "available": 1,
                       "targets": {"a": ["FLAMER"], "b": ["BATAFIRE"]}}
    else:
        assert got is None
