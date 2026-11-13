"""Inject a policy for isolated rule/lifecycle tests, not generation acceptance."""
from typing import Any, Callable

import pytest

from ... import KirbyAmWorld


def set_rule_test_policy(monkeypatch: pytest.MonkeyPatch, provider: Callable[..., dict[str, Any]]) -> None:
    """Keep real early feasibility; install the synthetic fixture afterward.

    A fixed/narrow historical policy may not satisfy the combined full catalog.
    Feeding it into the retry builder would repeat that same rejected policy
    thousands of times. These tests exercise installed rules and classification,
    while full-generation tests continue using the real builder and safeguards.
    """
    original = KirbyAmWorld.generate_early

    def generate_early(world: KirbyAmWorld) -> None:
        original(world)
        world._enemy_copy_ability_policy = provider()

    monkeypatch.setattr(KirbyAmWorld, 'generate_early', generate_early)
