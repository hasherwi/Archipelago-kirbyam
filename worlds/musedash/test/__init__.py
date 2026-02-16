from typing import cast

from test.bases import WorldTestBase

from .. import MuseDashWorld


class MuseDashTestBase(WorldTestBase):
    game = "Muse Dash"

    def get_world(self) -> MuseDashWorld:
        return cast(MuseDashWorld, self.multiworld.worlds[1])

