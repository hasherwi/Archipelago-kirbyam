from __future__ import annotations

from .bases import KirbyAMTestBase


class TestKirbyAMLoggingSmoke(KirbyAMTestBase):
    def test_generation_with_logging(self) -> None:
        self.world_setup()
        # If logging caused exceptions during generation, world_setup would have failed.
        assert True
