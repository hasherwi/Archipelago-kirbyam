"""Inject a policy for isolated rule/lifecycle tests, not generation acceptance."""
from typing import Any, Callable

import pytest

from ... import KirbyAmWorld


def keep_historical_room16_assignment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replay pre-#1124 policies while leaving traversal, fill, and the final audit intact."""
    import worlds.kirbyam as kirby

    from ... import room16_timer

    # Historical fixtures predate the explicit native-room timer patch.
    monkeypatch.setattr(room16_timer, "configure_policy", lambda raw: raw)
    validate = kirby.validate_peg_assignment

    def validate_historical(*args: Any, **kwargs: Any) -> dict[str, Any]:
        kwargs.update(require_room16=False, room16_for_completion=False)
        return validate(*args, **kwargs)

    monkeypatch.setattr(kirby, "validate_peg_assignment", validate_historical)


def set_rule_test_policy(monkeypatch: pytest.MonkeyPatch, provider: Callable[..., dict[str, Any]]) -> None:
    """Keep real early feasibility; install the synthetic fixture afterward.

    A fixed/narrow historical policy may not satisfy the combined full catalog.
    Feeding it into the retry builder would repeat that same rejected policy
    thousands of times. These tests exercise installed rules and classification,
    while full-generation tests continue using the real builder and safeguards.
    """
    original = KirbyAmWorld.generate_early

    def generate_early(world: KirbyAmWorld) -> None:
        # Room16 preflight must not select or reject the unrelated setup policy:
        # the fixture immediately substitutes its own policy for installed rules.
        with monkeypatch.context() as scoped:
            keep_historical_room16_assignment(scoped)
            original(world)
        world._enemy_copy_ability_policy = provider()

    monkeypatch.setattr(KirbyAmWorld, 'generate_early', generate_early)
