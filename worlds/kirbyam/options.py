"""
Option definitions for Kirby & The Amazing Mirror
"""
from dataclasses import dataclass

from Options import (
    Choice,
    DeathLink,
    OptionGroup,
    PerGameCommonOptions,
    Range,
    Toggle,
)

from .colors import (
    STARTING_KIRBY_COLOR_RANDOM_PER_ROOM_OPTION,
    kirby_color_names_for_docs,
    load_kirby_colors,
)
from .enemy_health_scaling import (
    ENEMY_HEALTH_MULTIPLIER_DEFAULT,
    ENEMY_HEALTH_MULTIPLIER_MAX,
    ENEMY_HEALTH_MULTIPLIER_MIN,
)


class Goal(Choice):
    """
    Determines what your goal is to consider the game beaten.

    - Dark Mind: Defeat Dark Mind and beat the game.
    - Defeat Any Area Boss: Defeat any one eligible area boss.
    - Defeat Area Boss: Defeat the area boss selected by `configured_area_boss`.
      Set `configured_area_boss` to `random` to choose one boss at generation.
    """
    display_name = "Goal"
    default = 0
    option_dark_mind = 0
    option_defeat_any_area_boss = 1
    option_defeat_area_boss = 2

    # Issue #872 rename compatibility: the old configured-goal name had the
    # same semantics, so accepting it as an alias is safe. The old hidden-random
    # goal is deliberately not aliased because doing so would silently change an
    # old YAML to the default configured boss; use configured_area_boss: random.
    alias_defeat_configured_area_boss = option_defeat_area_boss


class ConfiguredAreaBoss(Choice):
    """
    Selects which area boss is used when the goal is set to Defeat Area Boss.

    The default target is the Master Hand + Crazy Hand pair.
    Set the entire option to `random` to let Archipelago choose one of the eight
    area bosses during option parsing. In a YAML, the shorthand is:
      `configured_area_boss: random`
    If you start from the generated weighted template, replace the entire
    `configured_area_boss` weight mapping with that one line. This option is
    ignored unless `goal` is set to `defeat_area_boss`.
    """
    display_name = "Configured Area Boss"
    default = 7
    option_king_golem = 0
    option_moley = 1
    option_kracko = 2
    option_mega_titan = 3
    option_gobbler = 4
    option_wiz = 5
    option_dark_meta_knight = 6
    option_master_hand_crazy_hand_pair = 7


class RandomizeShards(Choice):
    """
    Controls where Mirror Shards can appear.

    - Vanilla: Each area's boss defeat location contains its matching shard.
    - Completely Random: Shards can appear from any location. Default.
    """
    display_name = "Randomize Shards"
    default = 2
    option_vanilla = 0
    option_completely_random = 2


class AbilityRandomizationMode(Choice):
    """
    Controls randomization of enemy-granted copy abilities.
    If statue randomization is enabled, statues inherit this same mode.

    - Off: Enemy copy abilities stay at native defaults. Default.
    - Shuffled: Enemy types are remapped deterministically so all enemies of the
        same type grant the same ability.
    - Completely Random: Eligible enemy ability grants are remapped independently
        (deterministic per grant event).
    """
    display_name = "Ability Randomization Mode"
    default = 0
    option_off = 0
    option_shuffled = 1
    option_completely_random = 2
    template_excluded_choices = frozenset({"completely_random"})


# The following three options only apply when Ability Randomization Mode is not Off.
# Regular enemy sources (kind: enemy) with a non-zero native copy ability are always included
# regardless of these settings; miniboss and boss-spawn ability sources are controlled by the
# toggles below.

class AbilityRandomizationBossSpawns(Toggle):
    """
    Include boss-spawned ability grants in randomization.
      Only applies when Ability Randomization Mode is not Off.
      On by Default, but ability_randomization_mode is Off by Default.
    """
    display_name = "Ability Randomization: Boss Spawns"
    default = 1


class AbilityRandomizationMinibosses(Toggle):
    """
    Include mini-boss ability grants in randomization.
      Only applies when Ability Randomization Mode is not Off.
      On by Default, but ability_randomization_mode is Off by Default.
    """
    display_name = "Ability Randomization: Minibosses"
    default = 1


class AbilityRandomizationMinny(Toggle):
    """
    Include Minny in copy-ability randomization.
            Only applies when Ability Randomization Mode is not Off.
            If ability statue randomization is enabled, statues also respect this toggle.
            Off by Default.
    """
    display_name = "Ability Randomization: Minny"
    default = 0


class AbilityRandomizationPassiveEnemies(Toggle):
    """
    When enabled, enemies that normally do not grant a copy ability can receive a
    randomized ability.
      Only applies when Ability Randomization Mode is not Off.
      Enemy sources only. Ability statues are not affected by this toggle.

      On by Default, but ability_randomization_mode is Off by Default.
    """
    display_name = "Ability Randomization: Passive Enemies"
    default = 1


class AbilityRandomizationNoAbilityWeight(Range):
    """
    Sets the percentage chance that an included randomized enemy grant resolves to
    no ability instead of a copy ability.

    - 0: Included randomized enemies always grant a copy ability.
    - 55: 55% of included randomized enemies grant no ability, 45% grant a copy ability.
            Default. This matches the in-game percentage when enemies that normally
            grant no ability are included in the randomization pool.
    - 100: Included randomized enemies always grant no ability.

    This only affects enemies already included by the ability randomization mode and
    the boss/miniboss/passive-enemy toggles.
    Ability statues are not affected; randomized statues always grant an ability.

        You can set a custom percentage by adding a custom number as the subkey,
        then supply the "percentage" chance for generation to roll that value.
      For example:
        25: 50
    The above says you want 25% of ability granting enemies to provide no ability
    instead of a copy ability, and 75% to provide a copy ability. Further,
        25: 10
        50: 10
        75: 10
            The above says you want generation to have equal chances of creating
            worlds where 25%, 50%, and 75% of ability granting enemies provide no
            ability instead of a copy ability.
    """
    display_name = "Ability Randomization: No Ability Weight"
    range_start = 0
    range_end = 100
    # 55% is rounded from 827 / 1510 = 54.77% vanilla no-ability regular-enemy placements
    # in the USA ROM across the current randomized-enemy dataset.
    default = 55


class AbilityRandomizationStatues(Toggle):
    """
    Include ability statues (sometimes called ability trophies or ability stands)
    in copy-ability randomization.

    This toggle only controls whether statues participate at all.
    Only applies when Ability Randomization Mode is not Off.
    Participating statues use the currently selected Ability Randomization Mode
    (Off, Shuffled, or Completely Random).
    Randomized statues always grant an ability and do not use
    `ability_randomization_no_ability_weight` or
    `ability_randomization_passive_enemies`.
    Randomized statues do respect `ability_randomization_minny`.

    Off by default.
    """
    display_name = "Ability Randomization: Statues"
    default = 0


class NoExtraLives(Toggle):
    """
    Start with zero lives and clamp all extra-life gains to zero during gameplay.
      Starts after the tutorial. Off by default.

      Yes, you can combine this with One-Hit Mode for an extra challenge.
    """
    display_name = "No Extra Lives"
    default = 0


class AbilityGating(Toggle):
    """
    Enable gating for abilities. Gated abilities are turned on by receiving an AP item.
    On by default.
    """
    display_name = "Ability Gating"
    default = 1


class EnableTraps(Toggle):
    """
    Allow negative trap items to appear in the randomized item pool.
    Off by default.
    When disabled, no KirbyAM traps are placed.
    """
    display_name = "Enable Traps"
    default = 0


class TrapFillPercentage(Range):
    """
    Sets what percentage of eligible filler slots become traps when `Enable Traps` is on.

    Eligible filler slots are the locations left after all progression/useful items are placed.
    Trap items are sampled with replacement, so duplicate traps are allowed when the pool is large enough.

    - 0: No filler slots become traps.
    - 25: One quarter of eligible filler slots become traps. Default.
    - 100: Every eligible filler slot becomes a trap.
    """
    display_name = "Trap Fill Percentage"
    range_start = 0
    range_end = 100
    default = 25


class EnemyHealthMultiplier(Range):
    """
    Scale regular-enemy, miniboss, and boss health as a percentage of native HP.

    - 50: Half native HP.
    - 100: Native HP. Default.
    - 200: Double native HP.
    - 500: Five times native HP.

    The value is baked into each generated game patch, so it changes enemy HP
    in the player's ROM rather than only changing logic or client metadata.
    Normal Archipelago Range weighting is supported in player YAML files.
    """
    display_name = "Enemy Health Multiplier"
    range_start = ENEMY_HEALTH_MULTIPLIER_MIN
    range_end = ENEMY_HEALTH_MULTIPLIER_MAX
    default = ENEMY_HEALTH_MULTIPLIER_DEFAULT


class OneHitMode(Choice):
    """
    Controls whether Kirby's maximum health is reduced to 1 HP at the start (one-hit mode).
      Starts after the tutorial. Off by default.
      Yes, you can combine this with No Extra Lives for an extra challenge.

    - Off: Kirby's maximum health is unmodified (native 6 HP base, plus 1 per
        Vitality Counter found).
    - Exclude Vitality Counters: Kirby starts with a maximum of 1 HP. All four Vitality Counter items are
        removed from the item pool and replaced with filler. Kirby's HP cap stays at 1 for the entire run.
    - Include Vitality Counters: Kirby starts with a maximum of 1 HP. Vitality Counter items remain in the
        pool; each one received increases Kirby's HP cap by 1 (up to 5 with all four). This is known to
        cause a visual artifact on the screen when a vitality counter is received, but it is functional.
    """
    display_name = "One-Hit Mode"
    default = 0
    option_off = 0
    option_exclude_vitality_counters = 1
    option_include_vitality_counters = 2


class StartWithAllMaps(Toggle):
    """
    Start the game with all nine area maps already acquired.
      Off by default. Intended for new players who find exploring unmapped areas daunting.
      All map items are removed from the item pool and replaced with filler.
    """
    display_name = "Start With All Maps"
    default = 0


def _build_starting_kirby_color_option() -> type[Choice]:
    doc = (
        """
    Choose Kirby's default starting color palette.
      Pink is the in-game default. The resolved color is embedded in the
    generated patch and applied before Kirby's first gameplay palette loads.

    Supported color names (as listed on Kirby Wiki Spray Paint):
      %s

    Set the entire option to `random` to let Archipelago choose one supported
    color during option parsing. In a YAML, the shorthand is:
      `starting_kirby_color: random`
    If you start from the generated weighted template, replace the entire
    `starting_kirby_color` weight mapping with that one line.

    Set to `random_color_per_room` to choose an initial color at generation,
    then change to a different supported color whenever the connected BizHawk
    client observes Kirby enter a different room.
    """
        % kirby_color_names_for_docs()
    )

    attrs: dict[str, object] = {
        "__doc__": doc,
        "display_name": "Starting Kirby Color",
        "default": 0,
        "option_random_color_per_room": STARTING_KIRBY_COLOR_RANDOM_PER_ROOM_OPTION,
    }
    for color in load_kirby_colors():
        attrs[f"option_{color.key}"] = color.color_id

    return type("StartingKirbyColor", (Choice,), attrs)


StartingKirbyColor = _build_starting_kirby_color_option()


class RoomSanity(Toggle):
    """Adds room-visit checks (for example, `Room X-*`). Off by default because it adds 263 locations."""
    display_name = "Room Sanity"
    default = 0


class KirbyAmDeathLink(DeathLink):
    __doc__ = DeathLink.__doc__


@dataclass
class KirbyAmOptions(PerGameCommonOptions):
    goal: Goal

    configured_area_boss: ConfiguredAreaBoss

    shards: RandomizeShards

    start_with_all_maps: StartWithAllMaps

    starting_kirby_color: StartingKirbyColor  # type: ignore[valid-type]

    no_extra_lives: NoExtraLives

    ability_gating: AbilityGating

    enable_traps: EnableTraps

    trap_fill_percentage: TrapFillPercentage

    enemy_health_multiplier: EnemyHealthMultiplier

    one_hit_mode: OneHitMode

    ability_randomization_mode: AbilityRandomizationMode

    ability_randomization_boss_spawns: AbilityRandomizationBossSpawns

    ability_randomization_minibosses: AbilityRandomizationMinibosses

    ability_randomization_minny: AbilityRandomizationMinny

    ability_randomization_passive_enemies: AbilityRandomizationPassiveEnemies

    ability_randomization_no_ability_weight: AbilityRandomizationNoAbilityWeight

    ability_randomization_statues: AbilityRandomizationStatues

    room_sanity: RoomSanity

    death_link: KirbyAmDeathLink


OPTION_GROUPS = [
    OptionGroup("Make the game shorter", [
        Goal,
        ConfiguredAreaBoss,
    ]),
    OptionGroup("Make the game easier", [
        StartWithAllMaps,
    ]),
    OptionGroup("Make the game last longer", [
        RoomSanity,
    ]),
    OptionGroup("Make the game harder", [
        AbilityGating,
        EnableTraps,
        TrapFillPercentage,
        NoExtraLives,
        OneHitMode,
        EnemyHealthMultiplier,
        KirbyAmDeathLink,
    ]),
    OptionGroup("Ability Randomization", [
        AbilityRandomizationMode,
        AbilityRandomizationStatues,
        AbilityRandomizationPassiveEnemies,
        AbilityRandomizationNoAbilityWeight,
        AbilityRandomizationBossSpawns,
        AbilityRandomizationMinibosses,
        AbilityRandomizationMinny,
    ]),
    OptionGroup("Cosmetics", [
        StartingKirbyColor,
    ]),
]
