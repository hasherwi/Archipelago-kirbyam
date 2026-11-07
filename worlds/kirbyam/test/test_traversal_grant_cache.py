"""Grant memoization is local to one search and never caches physical consumption."""

from collections import Counter

import pytest

from ..traversal import Grant, Node, Placement, Position, Route, SourcePolicy, TraversalGraph


def graph(keys=("WHEELIE", "WHEELIE"), renewable=True):
    return TraversalGraph(
        (Node("a", 108), Node("b", 108), Node("target", 108)),
        (Route("a", "b"), Route("b", "a"), Route("b", "target", "wheel_race")),
        tuple(Placement(node, key, identity=f"physical-{node}", renewable=renewable,
                        retry_evidence="reviewed repeat loop" if renewable else None)
              for node, key in zip(("a", "b"), keys)),
        (Position("a"),), frozenset({"target"}),
    )


def test_repeated_source_key_resolved_once_per_evaluation(monkeypatch):
    policy = SourcePolicy({"mode": 0})
    original = policy.grant
    calls = Counter()

    def counted(key, permitted):
        calls[key] += 1
        return original(key, permitted)

    monkeypatch.setattr(policy, "grant", counted)
    for expected in (1, 2):
        result = graph().evaluate(policy, frozenset({"Wheel Ability"}), True)
        assert result.reaches("target")
        assert calls == {"WHEELIE": expected}
        assert not result.retry_assumptions


@pytest.mark.parametrize("renewable", [False, True])
@pytest.mark.parametrize("retries", [False, True])
@pytest.mark.parametrize("randomized", [False, True])
def test_shared_key_preserves_complete_results_and_physical_identities(renewable, retries, randomized):
    class Policy:
        def grant(self, key, permitted):
            possibilities = {"Wheel", "Stone"} if randomized else {"Wheel"}
            return Grant(frozenset(a for a in possibilities if permitted(a)), randomized, randomized)

    # Different policy keys with identical grants provide an independent reference
    # for the shared-key case. Physical identities and search topology stay equal.
    shared = graph(renewable=renewable).evaluate(Policy(), frozenset(), False, retries)
    separate = graph(("SOURCE_A", "SOURCE_B"), renewable).evaluate(Policy(), frozenset(), False, retries)
    assert shared == separate
    if not renewable and shared.reaches("target"):
        assert all(p.consumed for p in shared.positions if p.node == "target")


def test_owned_gating_and_monkeypatched_grants_are_fresh_between_evaluations(monkeypatch):
    policy = SourcePolicy({"mode": 0})
    route = graph()
    assert not route.evaluate(policy, frozenset(), True).reaches("target")
    assert route.evaluate(policy, frozenset({"Wheel Ability"}), True).reaches("target")
    assert route.evaluate(policy, frozenset(), False).reaches("target")
    with monkeypatch.context() as context:
        context.setattr(policy, "grant", lambda *_: Grant(frozenset()))
        assert not route.evaluate(policy, frozenset({"Wheel Ability"}), True).reaches("target")
    assert route.evaluate(policy, frozenset({"Wheel Ability"}), True).reaches("target")
