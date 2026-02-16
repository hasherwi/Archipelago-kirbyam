from typing import List

from Options import Accessibility, OptionGroup, ProgressionBalancing

from .Options import (
                      Campaign,
                      CoinSanity,
                      CoinSanityRange,
                      DeathLink,
                      DoubleJumpGlitch,
                      EndingChoice,
                      ItemShuffle,
                      PermanentCoins,
                      TimeIsMoney,
)

dlcq_option_groups: List[OptionGroup] = [
    OptionGroup("General", [
        Campaign,
        ItemShuffle,
        CoinSanity,
    ]),
    OptionGroup("Customization", [
        EndingChoice,
        PermanentCoins,
        CoinSanityRange,
    ]),
    OptionGroup("Tedious and Grind", [
        TimeIsMoney,
        DoubleJumpGlitch,
    ]),
    OptionGroup("Advanced Options", [
        DeathLink,
        ProgressionBalancing,
        Accessibility,
    ]),
]
