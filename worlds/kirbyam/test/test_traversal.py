"""Traversal contracts: equipment, source policy and room-instance state."""

import random

import pytest

from ..ability_randomization import build_enemy_copy_ability_policy
from ..enemy_ability_data import ABILITY_NAME_TO_ID, ABILITY_SOURCES, STARTING_COPY_ABILITIES
from ..enemy_ability_runtime_patch import build_enemy_copy_runtime_patch_writes
from ..traversal import (
    Node, Placement, Position, Route, SourcePolicy, compile_traversal_graph,
    reachable_positions, validated_assignment,
)


def policy(mode=0, minny=True, minibosses=True, statues=False, weight=0, pool=None):
    kwargs = {} if pool is None else {"whitelist": pool}
    raw = build_enemy_copy_ability_policy(
        random.Random(427), mode, True, minibosses, minny,
        include_passive_enemies=True, no_ability_weight=weight, **kwargs,
    )
    return SourcePolicy(raw, statues)


def run(routes, sources=(), starts=(Position("pre"),), owned=frozenset(), gating=True,
        source_policy=None, retry=False):
    return reachable_positions(
        [Node("pre", 1), Node("post", 1), Node("other", 2)], routes, sources, starts,
        source_policy or policy(), owned, gating, retry,
    )


PEG = Route("pre", "post", "peg", "peg_1")


@pytest.mark.parametrize("mode", [0, 1])
@pytest.mark.parametrize("minny", [False, True])
@pytest.mark.parametrize("minibosses", [False, True])
def test_sources_match_actual_rom_writes(mode, minny, minibosses):
    resolver = policy(mode, minny, minibosses)
    writes = build_enemy_copy_runtime_patch_writes(resolver.policy)
    for source in ABILITY_SOURCES:
        if not source.can_be_swallowed:
            continue
        actual = resolver.grant(source.key, lambda _: True)
        expected = writes.get(source.addresses[0], source.default_ability_id)
        assert actual.guaranteed == frozenset(
            name for name, ability_id in ABILITY_NAME_TO_ID.items() if ability_id == expected and name != "Normal"
        )


@pytest.mark.parametrize("mode", [0, 1, 2])
def test_excluded_minny_retains_native_mini(mode):
    assert policy(mode, minny=False).grant("MINNY", lambda _: True).guaranteed == {"Mini"}


def test_unlock_is_not_equipment_or_a_source():
    assert not run([PEG], owned=frozenset({"Hammer Ability"})).reaches("post")


def test_source_behind_peg_cannot_bootstrap_itself():
    assert not run([PEG], [Placement("post", "ROCKY")]).reaches("post")


def test_source_before_peg_and_carried_source_work():
    assert run([PEG], [Placement("pre", "ROCKY")]).reaches("post")
    assert run([PEG], starts=[Position("pre", "Stone")]).reaches("post")


@pytest.mark.parametrize("gating", [False, True])
def test_hammer_permission_applies_at_acquisition(gating):
    sources = [Placement("pre", "BONKERS")]
    assert run([PEG], sources, gating=gating).reaches("post") == (not gating)
    assert run([PEG], sources, owned=frozenset({"Hammer Ability"}), gating=gating).reaches("post")


def test_acquisition_requirements_not_just_object_presence():
    sources = [Placement("pre", "BONKERS", frozenset({"Defeat local miniboss"}))]
    assert not run([PEG], sources, gating=False).reaches("post")
    assert run([PEG], sources, owned=frozenset({"Defeat local miniboss"}), gating=False).reaches("post")


def test_reverse_bypass_and_unaffected_exit():
    routes = [PEG, Route("post", "pre"), Route("pre", "other")]
    result = run(routes)
    assert result.reaches("other") and not result.reaches("post")
    assert run(routes, starts=[Position("post")]).reaches("pre")


def test_mini_clears_on_native_room_transition_not_compartment_change():
    routes = [Route("pre", "post", "mini_corridor"), Route("post", "other")]
    result = run(routes, [Placement("pre", "MINNY")], owned=frozenset({"Mini Ability"}))
    assert any(p.node == "post" and p.equipped == "Mini" for p in result.positions)
    assert Position("other", "Mini") not in result.positions
    assert any(p.node == "other" and p.equipped == "Normal" for p in result.positions)


def test_one_equipped_ability_and_open_peg_persists_only_in_room():
    routes = [PEG, Route("post", "pre", "peg", "peg_1"), Route("post", "other")]
    result = run(routes, [Placement("post", "WHEELIE")], starts=[Position("pre", "Stone")])
    assert any(p.node == "pre" and p.equipped == "Wheel" and p.opened == {"peg_1"} for p in result.positions)
    assert any(p.node == "other" and p.equipped == "Wheel" for p in result.positions)
    assert all(not p.opened for p in result.positions if p.node == "other")
    # A fresh room instance has no inherited peg event.
    assert not run([PEG], starts=[Position("pre", "Wheel")]).reaches("post")


def test_random_pool_is_not_a_deterministic_grant():
    resolver = policy(2, pool=["Hammer", "Stone"])
    grant = resolver.grant("ROCKY", lambda _: True)
    assert grant.abilities == {"Hammer", "Stone"}
    assert grant.randomized and not grant.guaranteed
    result = run([PEG], [Placement("pre", "ROCKY")], source_policy=resolver, gating=False)
    assert result.reaches("post")  # Every outcome solves this capability.
    assert not any(p.node == "pre" and p.equipped == "Hammer" for p in result.positions)
    assert not any(p.node == "pre" and p.equipped == "Stone" for p in result.positions)


def test_uncertain_equipment_is_not_simultaneous_or_chosen_equipment():
    resolver = policy(2, pool=["Hammer", "Stone"])
    routes = [PEG, Route("post", "other", "peg", allowed_abilities=frozenset({"Hammer"}))]
    result = run(routes, [Placement("pre", "ROCKY")], source_policy=resolver, gating=False)
    assert result.reaches("post")
    assert not result.reaches("other")


def test_mixed_peg_and_wheel_outputs_cannot_be_union_planned():
    resolver = policy(2, pool=["Stone", "Wheel"])
    routes = [PEG, Route("post", "other", "wheel_race")]
    result = run(routes, [Placement("pre", "ROCKY")], source_policy=resolver, gating=False)
    assert not result.reaches("post")
    assert not result.reaches("other")


def test_gate_filter_turns_random_peg_pool_into_guaranteed_stone():
    result = run([PEG], [Placement("pre", "ROCKY")], source_policy=policy(2, pool=["Hammer", "Stone"]))
    assert any(p.node == "pre" and p.equipped == "Stone" for p in result.positions)
    assert result.reaches("post")


def test_cannon_selftransition_clears_mini_and_room_local_state():
    result = run([Route("pre", "post", room_transition=True)],
                 starts=[Position("pre", "Mini", frozenset({"peg_1"}))])
    assert Position("post", "Normal") in result.positions
    assert not any(p.equipped == "Mini" or p.opened for p in result.positions if p.node == "post")


def test_retry_requires_both_opt_in_and_placement_evidence():
    resolver = policy(2, pool=["Stone", "Wheel"])
    source = Placement("pre", "ROCKY", renewable=True,
                       retry_evidence="Fixture: safe renewable source, conditional eventual roll")
    assert not run([PEG], [source], source_policy=resolver).reaches("post")
    assert not run([PEG], [Placement("pre", "ROCKY")], source_policy=resolver, retry=True).reaches("post")
    result = run([PEG], [source], source_policy=resolver, retry=True)
    assert result.reaches("post")
    assert result.retry_assumptions == {source.retry_evidence}


def test_weight_100_cannot_acquire_an_initial_ability_even_with_retries():
    resolver = policy(2, weight=100, pool=["Stone"])
    assert not run([PEG], [Placement("pre", "ROCKY", retry_evidence="Repeatable")],
                   source_policy=resolver, retry=True).reaches("post")


def test_random_statue_ignores_enemy_weight_and_filters_locked_pool():
    resolver = policy(2, statues=True, weight=100, pool=["Stone", "Hammer"])
    assert resolver.grant("STATUE:353900", lambda ability: ability == "Stone").guaranteed == {"Stone"}
    assert not resolver.grant("STATUE:353900", lambda _: False).guaranteed


def test_statue_toggle_off_is_vanilla_even_in_random_mode():
    assert policy(2, statues=False).grant("STATUE:353900", lambda _: True).guaranteed == {"Stone"}


def test_stone_starting_permission_is_preserved():
    assert "Stone" in STARTING_COPY_ABILITIES


def test_invalid_cross_room_peg_event_is_rejected():
    with pytest.raises(ValueError, match="room-local"):
        run([Route("pre", "other", "peg", "peg_1")])


@pytest.mark.parametrize("mode", [0, 1, 2])
def test_olive_drop_inhale_recover_sequence(mode):
    route = Route("pre", "post", "mini_corridor", recover_dropped_ability=True)
    result = run([route], [Placement("pre", "MINNY")], source_policy=policy(mode, minny=False),
                 owned=frozenset({"Mini Ability"}))
    assert result.reaches("post")


def test_only_raw_mini_star_ignores_weight_100_and_is_not_an_initial_source():
    resolver = policy(2, minny=False, weight=100, pool=["Mini"])
    assert not resolver.dropped_star_grant("Normal", lambda _: True).abilities
    assert not resolver.dropped_star_grant("Stone", lambda _: True).guaranteed
    assert resolver.dropped_star_grant("Mini", lambda _: True).guaranteed == {"Mini"}
    assert not resolver.dropped_star_grant("Mini", lambda _: False).guaranteed


def mini_fixture():
    return {
        "version": 1, "status": "reviewed",
        "nodes": [{"id": "local", "native_room": 321}, {"id": "lower", "native_room": 321}],
        "routes": [{"from": "local", "to": "lower", "capability": "mini_corridor",
                    "evidence": "Fixture based on native 0x59 corridor: 321 (12,26)-(13,26)"}],
        "sources": [{"node": "local", "source_key": "MINNY",
                     "acquisition_evidence": "Fixture: local canonical Minny approach"}],
        "starts": ["local"], "required_targets": ["lower"],
    }


def test_compiler_rejects_unreviewed_research():
    payload = mini_fixture()
    payload["status"] = "unresolved"
    with pytest.raises(ValueError, match="reviewed"):
        compile_traversal_graph(payload)


def test_compiler_requires_acquisition_evidence():
    payload = mini_fixture()
    del payload["sources"][0]["acquisition_evidence"]
    with pytest.raises(ValueError, match="acquisition evidence"):
        compile_traversal_graph(payload)


def test_assignment_retries_use_factory_without_forcing_source_outputs():
    graph = compile_traversal_graph(mini_fixture())
    rng = random.Random(713)
    produced = []

    def candidate():
        resolver = SourcePolicy(build_enemy_copy_ability_policy(
            rng, 1, True, True, True, whitelist=["Mini", "Stone"], no_ability_weight=0,
        ))
        produced.append(resolver)
        return resolver

    resolver, attempts = validated_assignment(graph, candidate, frozenset({"Mini Ability"}), True)
    assert resolver is produced[-1] and attempts == len(produced)
    assert resolver.grant("MINNY", lambda _: True).guaranteed == {"Mini"}
    assert resolver.writes == build_enemy_copy_runtime_patch_writes(resolver.policy)


def test_live_random_is_not_retried_using_fallback_assignments():
    payload = mini_fixture()
    payload["sources"][0]["source_key"] = "ROCKY"
    graph = compile_traversal_graph(payload)
    calls = []

    def candidate():
        calls.append(1)
        return policy(2)

    with pytest.raises(ValueError, match="source-backed"):
        validated_assignment(graph, candidate, frozenset({"Mini Ability"}), True)
    assert len(calls) == 1


def test_spent_source_cannot_be_reused_while_peg_stays_open():
    nodes = [Node(key, 1) for key in ("a", "b", "c", "d")]
    routes = [Route("a", "b", "peg", "first"), Route("b", "c", "wheel_race"),
              Route("c", "d", "peg", "second")]
    sources = [Placement("a", "ROCKY", identity="physical_rocky"), Placement("b", "WHEELIE"),
               Placement("c", "ROCKY", identity="physical_rocky")]
    result = reachable_positions(nodes, routes, sources, [Position("a")], policy())
    assert result.reaches("c") and not result.reaches("d")


def test_transition_does_not_renew_sources_without_reset_evidence():
    initial = Position("pre", "Mini", frozenset({"peg_1"}), frozenset({"physical_rocky"}))
    for route, opened, consumed in [
        (Route("pre", "post", room_transition=True, preserves_room_instance=True),
         {"peg_1"}, {"physical_rocky"}),
        (Route("pre", "post", room_transition=True), set(), {"physical_rocky"}),
        (Route("pre", "post", room_transition=True, resets_room_instance=True), set(), set()),
    ]:
        result = run([route], starts=[initial])
        assert Position("post", "Normal", frozenset(opened), frozenset(consumed)) in result.positions


def test_compiler_requires_renewable_evidence():
    payload = mini_fixture()
    payload["sources"][0]["renewable"] = True
    with pytest.raises(ValueError, match="repeatability"):
        compile_traversal_graph(payload)
