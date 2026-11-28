"""
Archipelago World definition for Kirby & The Amazing Mirror
"""
import base64
import os
import pkgutil
import time
from collections import Counter
from typing import TYPE_CHECKING, Any, ClassVar, TextIO

import settings
from Options import Accessibility
from BaseClasses import CollectionState, Item, ItemClassification, LocationProgressType, MultiWorld, Tutorial
from worlds.AutoWorld import WebWorld, World
from worlds.LauncherComponents import Component, Type, components, launch as launch_component

from .client import KirbyAmClient  # noqa: F401  # Required to register BizHawk client
from .ability_randomization import (
    build_enemy_copy_ability_policy,
)
from .area_keys import (
    EARLY_REACHABLE_CHECK_THRESHOLD,
    FALLBACK_STARTING_AREA_KEY_LABEL,
    RAINBOW_ROUTE_AREA_KEY_LABEL,
    area_key_bitfield_from_items,
)
from .colors import COLOR_CATALOG_VERSION, STARTING_KIRBY_COLOR_RANDOM_PER_ROOM_OPTION, resolve_kirby_color
from .data import (
    LocationCategory,
    data as kirby_data,
    format_room_region_label,
    load_json_data,
    normalize_region_exits,
)
from .enemy_ability_data import GATEABLE_ENEMY_COPY_ABILITIES
from .mini_traversal import validate_mini_sources
from .peg_traversal import peg_logic_enabled, validate_peg_assignment
from .enemy_ability_runtime_patch import build_enemy_copy_spoiler_rows
from .generation_logging import (
    generation_stage,
    log_generation_complete,
    log_generation_error,
    log_generation_start,
    log_items_created,
    log_regions_created,
    logger,
)
from .groups import ITEM_GROUPS, LOCATION_GROUPS, resolve_item_group
from .health import HealthRange, MAXIMUM_HEALTH_DEFAULT, MINIMUM_HEALTH_DEFAULT, resolve_health_range
from .item_pool_policy import ITEM_POOL_POLICY
from .items import KirbyAmItem, create_item_label_to_code_map, get_item_classification
from .locations import KirbyAmLocation, create_location_label_to_id_map
from .options import (
    Goal,
    OPTION_GROUPS,
    RANDOM_AREA_BOSS_SLOT_KEY,
    AbilityRandomizationMode,
    ConfiguredAreaBoss,
    KirbyAmOptions,
    RandomizeShards,
    TrapFillPercentage,
    validate_generation_options,
)
from .rom import KirbyAmProcedurePatch, write_tokens

if TYPE_CHECKING:
    from NetUtils import MultiData


def launch_mgba_client(*args: str) -> None:
    from .mgba_launcher import main
    launch_component(main, name="KirbyAMmGBAClient", args=args)


# Opt-in component: do not take over .apkirbyam's existing BizHawk association.
components.append(Component("KirbyAM mGBA Client", func=launch_mgba_client,
                            component_type=Type.CLIENT,
                            description="Connect KirbyAM through standalone mGBA (candidate integration)."))


class KirbyAmWebWorld(WebWorld):
    """
    Webhost info for Kirby & The Amazing Mirror
    """
    theme = "ocean"

    setup_en = Tutorial(
        "Multiworld Setup Guide",
        "A guide to playing Kirby & The Amazing Mirror with Archipelago.",
        "English",
        "setup_en.md",
        "setup/en",
        ["Harrison Sherwin, BlameMateo"],
    )

    tutorials = [setup_en]
    option_groups = OPTION_GROUPS


class KirbyAmSettings(settings.Group):
    class KirbyAmRomFile(settings.UserFilePath):
        """File name of your USA Kirby & The Amazing Mirror ROM"""
        description = "Kirby & The Amazing Mirror ROM File"
        copy_to = "Kirby & The Amazing Mirror (USA).gba"

        # Validate the ROM hash
        hash_obj = KirbyAmProcedurePatch.hash
        if hash_obj is None:
            raise RuntimeError("KirbyAmProcedurePatch.hash is missing")
        md5s = [hash_obj]

    rom_file: KirbyAmRomFile = KirbyAmRomFile(KirbyAmRomFile.copy_to)


class KirbyAmWorld(World):
    """
    Kirby & The Amazing Mirror is a classic Kirby adventure that emphasizes exploration and nonlinear progression.
    Guide Kirby through a vast, interconnected world within the Mirror Land,
    copy enemy abilities, uncover hidden paths, defeat powerful bosses,
    and restore peace by reuniting the shattered Dimension Mirror.
    """
    game = "Kirby & The Amazing Mirror"
    web = KirbyAmWebWorld()
    topology_present = True
    ut_can_gen_without_yaml = True

    # IMPORTANT: must match the name your settings system expects for this world.
    settings_key = "kirby_am_settings"
    settings: ClassVar[KirbyAmSettings]

    options_dataclass = KirbyAmOptions
    options: KirbyAmOptions

    item_name_to_id = create_item_label_to_code_map()
    location_name_to_id = create_location_label_to_id_map()

    item_name_groups = ITEM_GROUPS
    location_name_groups = LOCATION_GROUPS

    required_client_version = (0, 4, 6)

    # Per-seed auth token used by BizHawk client connection
    auth: bytes

    # Track generation timing
    _generation_start_time: float
    _enemy_copy_ability_policy: dict[str, Any]
    _candy912_linked_west_fuse: bool = False
    _resolved_starting_kirby_color_id: int
    _resolved_starting_kirby_color_name: str
    _resolved_configured_area_boss_goal_key: str | None
    _flag_location_id: int | None = None

    # Generation stages
    # Keep the historical public test-facing views derived from the policy.
    ACTIVE_FILLER_POOL: ClassVar[tuple[str, ...]] = ITEM_POOL_POLICY.filler_labels
    ACTIVE_FILLER_WEIGHTS: ClassVar[dict[str, int]] = dict(ITEM_POOL_POLICY.filler_weights_by_label)
    _SHARD_ITEM_LABEL_ORDER: ClassVar[tuple[str, ...]] = ITEM_POOL_POLICY.shard_labels
    # Activate the verified exact-source minor chest rollout. The older
    # collection-name placeholder rows remain dormant until they have unique
    # physical chest mappings.
    ENABLE_MINOR_CHESTS: ClassVar[bool] = True

    @classmethod
    def stage_assert_generate(cls, multiworld: MultiWorld) -> None:
        # If you don't have sanity_check.py yet, comment these out for now.
        from .sanity_check import validate_group_maps, validate_regions
        assert validate_regions()
        assert validate_group_maps()

    @classmethod
    def stage_pre_fill(cls, multiworld: MultiWorld) -> None:
        from .enemy_ability_runtime_patch import ROOM16_FOLEY_SWAP, SHUFFLE_SOURCE_SWAPS, SHUFFLE_STATUE_RESERVATIONS

        stone = "Stone Ability"
        stone_by_owner = {item.player: item for item in multiworld.itempool if item.name == stone and item.advancement}
        for player in multiworld.player_ids:
            world = multiworld.worlds[player]
            if (not isinstance(world, cls) or player not in stone_by_owner
                    or world.options.accessibility != Accessibility.option_minimal
                    or not world._ability_gating_enabled()
                    or not {ROOM16_FOLEY_SWAP, SHUFFLE_SOURCE_SWAPS, SHUFFLE_STATUE_RESERVATIONS}.intersection(
                        getattr(world, "_enemy_copy_ability_policy", {}))):
                continue
            if any(item.name == stone for item in multiworld.precollected_items[player]) or any(
                location.item is not None and location.item.player == player and location.item.name == stone
                for location in multiworld.get_filled_locations()
            ):
                continue  # The player already owns or deliberately placed this permission.
            early = multiworld.early_items[player]
            if early.get(stone, 0) or multiworld.local_early_items[player].get(stone, 0):
                continue
            # Prove the repaired profile has a check that needs this Stone
            # permission. Sweep each state separately so an event behind Stone
            # cannot be carried into the counterfactual without it.
            full = multiworld.get_all_state(perform_sweep=False)
            without_stone = full.copy()
            without_stone.remove(stone_by_owner[player])
            full.sweep_for_advancements()
            without_stone.sweep_for_advancements()
            if not any(loc.address is not None and loc.can_reach(full) and not loc.can_reach(without_stone)
                       for loc in multiworld.get_locations(player)):
                continue
            # Minimal may put progression behind itself once the chosen boss
            # is beatable. Use AP's ordinary early fill for this permission;
            # don't change accessibility, locality, or locked/planned items.
            early[stone] = 1

    @classmethod
    def stage_pre_output(cls, multiworld: MultiWorld) -> None:
        # Main calls this after all worlds finalize placements and after
        # progression balancing, including skip-output generation.
        from .check_accessibility import validate_all_checks
        players = (player for player in multiworld.player_ids if isinstance(multiworld.worlds[player], cls))
        from .yellow_cupid import validate_profile as validate_yellow_cupid_profile
        players = tuple(players)
        for player in players:
            validate_yellow_cupid_profile(multiworld.worlds[player])
        validate_all_checks(multiworld, players)

    def _no_extra_lives_enabled(self) -> bool:
        option = getattr(getattr(self, "options", None), "no_extra_lives", None)
        value = getattr(option, "value", option)
        return bool(value)

    def _one_hit_mode_value(self) -> int:
        option = getattr(getattr(self, "options", None), "one_hit_mode", None)
        value = getattr(option, "value", option)
        if value is None:
            return 0
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def _health_range(self) -> HealthRange:
        options = getattr(self, "options", None)
        minimum = getattr(options, "minimum_health", MINIMUM_HEALTH_DEFAULT)
        maximum = getattr(options, "maximum_health", MAXIMUM_HEALTH_DEFAULT)
        return resolve_health_range(
            getattr(minimum, "value", minimum),
            getattr(maximum, "value", maximum),
            self._one_hit_mode_value(),
        )

    def _traps_enabled(self) -> bool:
        option = getattr(getattr(self, "options", None), "enable_traps", None)
        value = getattr(option, "value", option)
        return bool(value)

    def _area_keys_enabled(self) -> bool:
        option = getattr(getattr(self, "options", None), "area_keys", None)
        value = getattr(option, "value", option)
        return True if value is None else bool(value)

    def _ability_gating_enabled(self) -> bool:
        option = getattr(getattr(self, "options", None), "ability_gating", None)
        value = getattr(option, "value", option)
        if value is None:
            return True
        return bool(value)

    def _trap_fill_percentage(self) -> int:
        option = getattr(getattr(self, "options", None), "trap_fill_percentage", None)
        value = getattr(option, "value", option)
        if value is None:
            percentage = TrapFillPercentage.default
            return max(TrapFillPercentage.range_start, min(TrapFillPercentage.range_end, percentage))
        try:
            percentage = int(value)
        except (TypeError, ValueError):
            percentage = TrapFillPercentage.default
        return max(TrapFillPercentage.range_start, min(TrapFillPercentage.range_end, percentage))

    def _start_with_all_maps_enabled(self) -> bool:
        option = getattr(getattr(self, "options", None), "start_with_all_maps", None)
        value = getattr(option, "value", option)
        return bool(value)

    def _starting_kirby_color_randomize_on_room_transition_enabled(self) -> bool:
        option = getattr(getattr(self, "options", None), "starting_kirby_color", None)
        option_value = getattr(option, "value", option)
        if option_value is None:
            return False
        try:
            return int(option_value) == STARTING_KIRBY_COLOR_RANDOM_PER_ROOM_OPTION
        except (TypeError, ValueError):
            return False

    def _get_resolved_starting_kirby_color(self) -> tuple[int, str]:
        """Return the concrete color selected by Archipelago option parsing.

        `StartingKirbyColor` is a normal Choice option. Therefore the framework's
        built-in literal `random` is resolved before world generation and this
        helper never needs a second world-local random draw or sentinel value.
        """
        resolved_id = getattr(self, "_resolved_starting_kirby_color_id", None)
        resolved_name = getattr(self, "_resolved_starting_kirby_color_name", None)
        if isinstance(resolved_id, int) and isinstance(resolved_name, str) and resolved_name:
            return resolved_id, resolved_name

        option = getattr(getattr(self, "options", None), "starting_kirby_color", None)
        option_value = getattr(option, "value", option)
        try:
            choice_value = int(option_value) if option_value is not None else 0
        except (TypeError, ValueError):
            choice_value = 0

        rng = self.random if choice_value == STARTING_KIRBY_COLOR_RANDOM_PER_ROOM_OPTION else None
        color = resolve_kirby_color(choice_value, rng)
        self._resolved_starting_kirby_color_id = color.color_id
        self._resolved_starting_kirby_color_name = color.display_name
        return self._resolved_starting_kirby_color_id, self._resolved_starting_kirby_color_name

    def _get_resolved_configured_area_boss_goal_key(self) -> str | None:
        """Map the concrete configured boss choice to its native boss-defeat key.

        Archipelago's built-in Choice value `random` is resolved to one concrete
        ConfiguredAreaBoss value before this helper runs. Keep this mapping aligned
        with the actual KatAM area/boss layout, not option declaration order.
        """
        resolved_key = getattr(self, "_resolved_configured_area_boss_goal_key", None)
        if isinstance(resolved_key, str) and resolved_key:
            return resolved_key

        option = getattr(getattr(self, "options", None), "configured_area_boss", None)
        value = getattr(option, "value", option)
        if value is None:
            raise RuntimeError(
                "KirbyAM area-boss goal could not be resolved from the selected option value. "
                "Expected one of the defined ConfiguredAreaBoss choices."
            )
        try:
            choice_value = int(value)
        except (TypeError, ValueError):
            raise RuntimeError(
                "KirbyAM area-boss goal could not be resolved from the selected option value. "
                "Expected one of the defined ConfiguredAreaBoss choices."
            ) from None

        # Verified KatAM boss layout:
        #   Moonlight=King Golem, Cabbage=Moley, Mustard=Kracko,
        #   Carrot=Mega Titan, Olive=Gobbler, Peppermint=Wiz,
        #   Radish=Dark Meta Knight, Candy=Master Hand + Crazy Hand.
        configured_area_boss_key_by_value = {
            ConfiguredAreaBoss.option_king_golem: "BOSS_DEFEAT_2",
            ConfiguredAreaBoss.option_moley: "BOSS_DEFEAT_6",
            ConfiguredAreaBoss.option_kracko: "BOSS_DEFEAT_1",
            ConfiguredAreaBoss.option_mega_titan: "BOSS_DEFEAT_7",
            ConfiguredAreaBoss.option_gobbler: "BOSS_DEFEAT_4",
            ConfiguredAreaBoss.option_wiz: "BOSS_DEFEAT_5",
            ConfiguredAreaBoss.option_dark_meta_knight: "BOSS_DEFEAT_8",
            ConfiguredAreaBoss.option_master_hand_crazy_hand_pair: "BOSS_DEFEAT_3",
        }

        resolved = configured_area_boss_key_by_value.get(choice_value)
        if resolved is None:
            raise RuntimeError(
                f"KirbyAM area-boss goal resolved an unsupported option value: {choice_value}"
            )

        self._resolved_configured_area_boss_goal_key = resolved
        return resolved

    def _active_filler_pool(self) -> tuple[str, ...]:
        return self._active_filler_weighted_pool()[0]

    def _active_filler_weighted_pool(self) -> tuple[tuple[str, ...], tuple[int, ...]]:
        return ITEM_POOL_POLICY.filler_for(
            maximum_health_is_one=self._health_range().maximum == 1,
            no_extra_lives=self._no_extra_lives_enabled(),
        )

    # Filler item name
    def get_filler_item_name(self) -> str:
        filler_labels, filler_weights = self._active_filler_weighted_pool()
        return self.random.choices(filler_labels, weights=filler_weights, k=1)[0]

    def get_trap_item_name(self) -> str:
        trap_labels = self._active_trap_pool()
        if not trap_labels:
            raise ValueError(
                "KirbyAM trap pool is empty after player and automatic exclusions"
            )
        return self.random.choice(trap_labels)

    def _active_trap_pool(self) -> tuple[str, ...]:
        from .random_teleport import TRAP_CATALOG_VERSION

        option = getattr(getattr(self, "options", None), "exclude_trap_types", None)
        return ITEM_POOL_POLICY.traps_for(
            minimum_health_is_one=self._health_range().minimum == 1,
            no_extra_lives=self._no_extra_lives_enabled(),
            catalog_version=getattr(self, "_tracker_trap_catalog_version", TRAP_CATALOG_VERSION),
            player_excluded_labels=set(getattr(option, "value", ())),
        )

    @staticmethod
    def interpret_slot_data(slot_data: dict[str, Any]) -> dict[str, Any]:
        # UT regenerates with this payload before constructing regions and rules.
        from .tracker import validate_tracker_data
        validate_tracker_data(slot_data)
        return slot_data

    # Pre-generation adjustments
    def generate_early(self) -> None:
        from .phone_traversal import validate_phone_profile
        passthrough = getattr(self.multiworld, "re_gen_passthrough", {})
        if self.game in passthrough:
            from .tracker import restore_tracker_data
            restore_tracker_data(self, passthrough[self.game])
            validate_phone_profile(self, require_policy=True)
            self._generation_start_time = time.time()
            return
        validate_generation_options(self.options, self.player_name)
        validate_phone_profile(self)
        # Reject unsupported health pairs before producing regions/items or a patch.
        health_range = self._health_range()
        if self._one_hit_mode_value():
            logger.warning(
                "[P%s] one_hit_mode is deprecated; using minimum_health=%s and maximum_health=%s. "
                "Replace one_hit_mode in your YAML with these health values.",
                self.player, health_range.minimum, health_range.maximum,
            )
            self.options.minimum_health.value = health_range.minimum
            self.options.maximum_health.value = health_range.maximum
            self.options.one_hit_mode.value = 0

        # Track generation start
        self._generation_start_time = time.time()
        log_generation_start(
            self.player,
            self.player_name,
            self.options.as_dict("goal", "configured_area_boss", "shards", "death_link"),
        )

        with generation_stage("generate_early", self.player, self.player_name):
            logger.info(f"[P{self.player}] Shards mode: {self.options.shards.current_key}")
            starting_color_option = self.options.starting_kirby_color
            chosen_color_key = getattr(starting_color_option, "current_key", "unknown")
            resolved_color_id, resolved_color_name = self._get_resolved_starting_kirby_color()
            configured_area_boss_key = self._get_resolved_configured_area_boss_goal_key()
            logger.info(
                "[P%s] Starting Kirby color option: %s -> %s (%s)",
                self.player,
                chosen_color_key,
                resolved_color_name,
                resolved_color_id,
            )
            logger.info(
                "[P%s] Configured area boss option: %s -> %s",
                self.player,
                getattr(self.options.configured_area_boss, "current_key", "unknown"),
                configured_area_boss_key,
            )

            mode = int(self.options.ability_randomization_mode.value)
            randomize_boss_spawned = bool(self.options.ability_randomization_boss_spawns.value)
            randomize_miniboss = bool(self.options.ability_randomization_minibosses.value)
            randomize_minny = False  # Minny is no longer a configurable randomized source.
            randomize_non_ability = bool(self.options.ability_randomization_passive_enemies.value)
            randomize_statues = bool(self.options.ability_randomization_statues.value)
            no_ability_weight = int(self.options.ability_randomization_no_ability_weight.value)
            self._enemy_copy_ability_policy = build_enemy_copy_ability_policy(
                self.random,
                mode,
                randomize_boss_spawned,
                randomize_miniboss,
                include_minny=randomize_minny,
                include_passive_enemies=randomize_non_ability,
                no_ability_weight=no_ability_weight,
            )
            from .room16_timer import configure_policy
            self._enemy_copy_ability_policy = configure_policy(self._enemy_copy_ability_policy)
            # Standard Shuffled repairs the initial assignment without drawing a
            # new seed. Other modes and Advanced retain their existing policy.
            self._enemy_copy_ability_policy = validate_peg_assignment(
                self._enemy_copy_ability_policy,
                lambda: build_enemy_copy_ability_policy(
                    self.random, mode, randomize_boss_spawned, randomize_miniboss,
                    include_minny=False, include_passive_enemies=randomize_non_ability,
                    no_ability_weight=no_ability_weight,
                ), randomize_statues, require_all_witnesses=True,
                # Room16 adds a rare joint source constraint. Keep the existing
                # deterministic policy stream, with a bounded larger search.
                max_attempts=16384 if mode == 1 and (
                    self.options.room_sanity.value or self.options.goal.value == Goal.option_full_completion
                ) else 8192,
                advanced=self.options.advanced_logic.value == 1,
                require_room16=bool(self.options.room_sanity.value),
                room16_for_completion=self.options.goal.value == Goal.option_full_completion,
                allow_room16_shuffle_repair=True,
                logic_aware_shuffle=(mode == AbilityRandomizationMode.option_shuffled
                                     and not self.options.advanced_logic.value),
                area_keys=self._area_keys_enabled(),
            )
            from .conditional_routes import CANDY_FUSE
            self._candy912_linked_west_fuse = CANDY_FUSE.needs_linked_fuse(
                self._enemy_copy_ability_policy, minor_chests=self.ENABLE_MINOR_CHESTS,
            )
            validate_phone_profile(self)
            validate_mini_sources(self._enemy_copy_ability_policy, randomize_statues)
            if not peg_logic_enabled(self._enemy_copy_ability_policy):
                logger.warning(
                    "[P%s] Live-random traversal uses only reviewed repeatable sources with positive ability support; "
                    "eventual eligible draws are conditional, not bounded guarantees.", self.player,
                )
            allowed_abilities = tuple(
                self._enemy_copy_ability_policy.get("allowed_abilities", ())
            )
            if mode == AbilityRandomizationMode.option_off:
                logger.info(
                    "[P%s] Enemy copy-ability randomization: off "
                    "(%s whitelist entries, minny=%s, statues=%s, no_ability_weight=%s)",
                    self.player,
                    len(allowed_abilities),
                    randomize_minny,
                    randomize_statues,
                    no_ability_weight,
                )
            elif mode == AbilityRandomizationMode.option_shuffled:
                logger.info(
                    "[P%s] Enemy copy-ability randomization: shuffled "
                    "(%s whitelist entries, minny=%s, passive_enemies=%s, statues=%s, no_ability_weight=%s)",
                    self.player,
                    len(allowed_abilities),
                    randomize_minny,
                    randomize_non_ability,
                    randomize_statues,
                    no_ability_weight,
                )
                spoiler_rows = build_enemy_copy_spoiler_rows(
                    self._enemy_copy_ability_policy,
                    include_statues=randomize_statues,
                )
                if spoiler_rows:
                    spoiler_header = "Enemy copy-ability shuffled assignments"
                    if randomize_statues:
                        spoiler_header = "Enemy and world statue copy-ability shuffled assignments (Copy Ability Room excluded)"
                    logger.info("[P%s] %s (kind | source -> ability):", self.player, spoiler_header)
                    for source_kind, source_key, ability_name in spoiler_rows:
                        logger.info(
                            "[P%s]   %s | %s -> %s",
                            self.player,
                            source_kind,
                            source_key,
                            ability_name,
                        )
            else:
                logger.info(
                    "[P%s] Enemy copy-ability randomization: completely_random "
                    "(%s whitelist entries, minny=%s, passive_enemies=%s, statues=%s, no_ability_weight=%s)",
                    self.player,
                    len(allowed_abilities),
                    randomize_minny,
                    randomize_non_ability,
                    randomize_statues,
                    no_ability_weight,
                )
                logger.debug(
                    "[P%s] Enemy copy-ability policy: %s",
                    self.player,
                    self._enemy_copy_ability_policy,
                )

            if randomize_statues and mode != AbilityRandomizationMode.option_off:
                logger.info(
                    "[P%s] Statue copy-ability randomization enabled "
                    "(inherits mode=%s; always grants ability; ignores "
                    "passive/no-ability enemy toggles; respects Minny toggle)",
                    self.player,
                    self.options.ability_randomization_mode.current_key,
                )
            elif randomize_statues:
                logger.info(
                    "[P%s] Statue copy-ability toggle enabled, but Ability "
                    "Randomization Mode is off so statue randomization is "
                    "inactive.",
                    self.player,
                )

            if self._area_keys_enabled():
                explicit_starting = getattr(getattr(self.options, "start_inventory", None), "value", {})
                # Rainbow Route is a guaranteed start, not a random placement.
                # Treat explicit "from pool" copies as the same guaranteed start.
                from_pool = getattr(getattr(self.options, "start_inventory_from_pool", None), "value", {})
                from_pool.pop(RAINBOW_ROUTE_AREA_KEY_LABEL, None)
                if explicit_starting.get(RAINBOW_ROUTE_AREA_KEY_LABEL, 0) <= 0:
                    self.push_precollected(self.create_item(RAINBOW_ROUTE_AREA_KEY_LABEL))

            if self._start_with_all_maps_enabled():
                map_items = [
                    item for item in kirby_data.items.values()
                    if "Maps" in item.tags
                ]
                for map_item in map_items:
                    self.push_precollected(self.create_item(map_item.label))
                logger.info(
                    "[P%s] start_with_all_maps: precollected %s map item(s)",
                    self.player,
                    len(map_items),
                )

    # Create world regions
    def create_regions(self) -> None:
        with generation_stage("create_regions", self.player, self.player_name):
            from .regions import create_regions as create_regions_impl

            regions_by_name = create_regions_impl(self)

            # Most create_regions implementations already append to multiworld.regions.
            # To avoid double-adding, only add missing ones here.
            existing = {(r.name, r.player) for r in self.multiworld.regions}
            for r in regions_by_name.values():
                if (r.name, r.player) not in existing:
                    self.multiworld.regions.append(r)

            # Main creates start_inventory before regions. Reclassify only the
            # conditional permissions whose actual target could not exist yet.
            # Useful items promoted here must now be collected.
            for item in self.multiworld.precollected_items[self.player]:
                if item.name in {"Ice Ability", "Crash Ability", "Missile Ability",
                                 "Parasol Ability", "Magic Ability", "Spark Ability"} \
                        and not item.advancement:
                    classification = self.create_item(item.name).classification
                    if classification & ItemClassification.progression:
                        item.classification = classification
                        self.multiworld.state.collect(item, prevent_sweep=True)

            # Log region creation
            fillable_locations = len([
                loc for loc in self.multiworld.get_locations(self.player)
                if isinstance(loc, KirbyAmLocation) and loc.address is not None
            ])
            log_regions_created(self.player, len(regions_by_name), fillable_locations)

    def _place_tutorial_hub_connection(self, locations_by_key: dict[str, KirbyAmLocation]) -> int | None:
        from .starting_mirror import (
            TUTORIAL_WORLD_MAP_KEY, random_starting_mirror_enabled, starting_mirror_candidates,
        )
        if not random_starting_mirror_enabled(self):
            return None

        location = locations_by_key.get(TUTORIAL_WORLD_MAP_KEY)
        if location is None:
            raise ValueError("Random Starting Mirror requires the tutorial World Map chest.")

        candidates = starting_mirror_candidates(self._area_keys_enabled())
        restored = getattr(self, "_starting_mirror_tutorial_item", None)
        if restored is None:
            if any(block.from_pool and candidates.keys() & block.items
                   for block in self.options.plando_items.value):
                # Keep this location out of AP's plando targets without taking
                # any of its possible rewards out of the real owner's pool.
                # Upstream resolves and executes its plans before pre_fill.
                placeholder = KirbyAmItem(
                    "Reserved tutorial Hub Connection", ItemClassification.filler, None, self.player,
                )
                self._starting_mirror_placeholder: KirbyAmItem | None = placeholder
                location.place_locked_item(placeholder)
                location.progress_type = LocationProgressType.DEFAULT
                return None
            configured_from_pool = getattr(getattr(self.options, "start_inventory_from_pool", None), "value", {})
            draw = [name for name in candidates if not configured_from_pool.get(name, 0)]
            if not draw:
                raise ValueError("Random Starting Mirror needs a Central Circle connection outside start_inventory_from_pool.")
            restored = self.random.choice(draw)
            self._starting_mirror_tutorial_item = restored
        if restored not in candidates:
            raise ValueError("Invalid Random Starting Mirror tutorial Hub Connection.")
        item = self.create_item(restored)
        location.place_locked_item(item)
        location.progress_type = LocationProgressType.DEFAULT
        return self.item_name_to_id[restored]

    def pre_fill(self) -> None:
        placeholder = getattr(self, "_starting_mirror_placeholder", None)
        if placeholder is None:
            return
        from .starting_mirror import starting_mirror_candidates

        chest = placeholder.location
        assert chest is not None and chest.item is placeholder
        candidates = starting_mirror_candidates(self._area_keys_enabled())
        owned = {
            item.name: (index, item)
            for index, item in enumerate(self.multiworld.itempool)
            if item.player == self.player and item.name in candidates
        }
        draw = [name for name in candidates if name in owned]
        if not draw:
            raise ValueError(
                f"[P{self.player}] Random Starting Mirror has no eligible Central Circle Hub Connection "
                "left in this player's pool after item plando and starting inventory. "
                "Leave at least one eligible connection unreserved."
            )
        reward = self.random.choice(draw)
        index, item = owned[reward]
        self.multiworld.itempool.pop(index)
        placeholder.location = None
        chest.item = None
        chest.place_locked_item(item)
        self._starting_mirror_placeholder = None
        self._starting_mirror_tutorial_item = reward
        self._verify_tutorial_hub_connection(after_plando=True)

    def _verify_tutorial_hub_connection(self, *, after_plando: bool = False) -> None:
        from .starting_mirror import (
            TUTORIAL_WORLD_MAP_NAME, random_starting_mirror_enabled, starting_mirror_candidates,
        )
        if not random_starting_mirror_enabled(self):
            return
        if getattr(self, "_starting_mirror_placeholder", None) is not None:
            return
        chest = self.multiworld.get_location(TUTORIAL_WORLD_MAP_NAME, self.player)
        item = chest.item
        state = CollectionState(self.multiworld)
        if item is None or not chest.can_reach(state):
            raise ValueError("Random Starting Mirror tutorial reward is not reachable.")
        edge = self.multiworld.get_entrance(starting_mirror_candidates(self._area_keys_enabled())[item.name], self.player)
        state.collect(item, True, chest)
        if not edge.can_reach(state):
            raise ValueError(f"Random Starting Mirror tutorial reward {item.name!r} does not open its entrance.")
        if not any(
            loc is not chest and loc.address is not None and (after_plando or loc.item is None)
            and loc.can_reach(state) for loc in self.multiworld.get_locations(self.player)
        ):
            raise ValueError(f"Random Starting Mirror tutorial reward {item.name!r} leaves no reachable randomized check.")

    def create_items(self) -> None:  # noqa: C901
        with generation_stage("create_items", self.player, self.player_name):
            # Create items for all fillable locations (address != None).
            fill_locations: list[KirbyAmLocation] = [
                loc for loc in self.multiworld.get_locations(self.player)
                if isinstance(loc, KirbyAmLocation) and loc.address is not None
            ]

            # Resolve fillable physical locations by category.
            boss_locations: list[KirbyAmLocation] = []
            map_chest_locations: list[KirbyAmLocation] = []
            vitality_chest_locations: list[KirbyAmLocation] = []
            sound_player_chest_locations: list[KirbyAmLocation] = []
            hub_switch_locations: list[KirbyAmLocation] = []
            lever_locations: list[KirbyAmLocation] = []
            minor_chest_locations: list[KirbyAmLocation] = []
            room_sanity_locations: list[KirbyAmLocation] = []
            area_visit_locations: list[KirbyAmLocation] = []
            goal_game_locations: list[KirbyAmLocation] = []
            location_by_key: dict[str, KirbyAmLocation] = {}
            for loc in fill_locations:
                if loc.key is None:
                    continue
                location_by_key[loc.key] = loc
                loc_meta = kirby_data.locations.get(loc.key)
                if loc_meta is None:
                    continue
                if loc_meta.category == LocationCategory.BOSS_DEFEAT:
                    boss_locations.append(loc)
                elif loc_meta.category == LocationCategory.MAP_CHEST:
                    map_chest_locations.append(loc)
                elif loc_meta.category == LocationCategory.VITALITY_CHEST:
                    vitality_chest_locations.append(loc)
                elif loc_meta.category == LocationCategory.SOUND_PLAYER_CHEST:
                    sound_player_chest_locations.append(loc)
                elif loc_meta.category == LocationCategory.HUB_SWITCH:
                    hub_switch_locations.append(loc)
                elif loc_meta.category == LocationCategory.LEVER:
                    lever_locations.append(loc)
                elif loc_meta.category == LocationCategory.MINOR_CHEST:
                    minor_chest_locations.append(loc)
                elif loc_meta.category == LocationCategory.ROOM_SANITY:
                    room_sanity_locations.append(loc)
                elif loc_meta.category == LocationCategory.GOAL_GAME:
                    goal_game_locations.append(loc)
                elif loc_meta.category == LocationCategory.AREA_VISIT:
                    area_visit_locations.append(loc)

            boss_locations.sort(key=lambda loc: loc.key or "")
            map_chest_locations.sort(key=lambda loc: loc.key or "")
            vitality_chest_locations.sort(key=lambda loc: loc.key or "")
            sound_player_chest_locations.sort(key=lambda loc: loc.key or "")
            hub_switch_locations.sort(key=lambda loc: loc.key or "")
            lever_locations.sort(key=lambda loc: loc.key or "")
            minor_chest_locations.sort(key=lambda loc: loc.key or "")
            room_sanity_locations.sort(key=lambda loc: loc.key or "")
            area_visit_locations.sort(key=lambda loc: loc.key or "")
            goal_game_locations.sort(key=lambda loc: loc.key or "")

            tutorial_hub_code = self._place_tutorial_hub_connection(location_by_key)
            locked_shard_count = 0
            randomized_item_codes: list[int] = []
            if (
                boss_locations
                or map_chest_locations
                or vitality_chest_locations
                or sound_player_chest_locations
                or hub_switch_locations
                or lever_locations
                or minor_chest_locations
                or room_sanity_locations
                or area_visit_locations
                or goal_game_locations
            ):
                shard_item_codes = ITEM_POOL_POLICY.shard_codes

                expected_boss_defeat_count = sum(
                    1 for m in kirby_data.locations.values()
                    if m.category == LocationCategory.BOSS_DEFEAT
                )
                if len(boss_locations) != expected_boss_defeat_count:
                    raise ValueError(
                        f"KirbyAM expected {expected_boss_defeat_count} boss-defeat locations,"
                        f" found {len(boss_locations)}"
                    )

                # In vanilla shard mode, each area's boss defeat location awards
                # that area's matching shard (fixed AP placement).
                if self.options.shards.value == RandomizeShards.option_vanilla:
                    boss_by_key = {loc.key: loc for loc in boss_locations}
                    for boss_key, shard_code in ITEM_POOL_POLICY.vanilla_boss_shards:
                        boss_loc = boss_by_key.get(boss_key)
                        if boss_loc is None:
                            raise ValueError(f"KirbyAM boss-defeat location missing from region graph: {boss_key}")
                        boss_loc.place_locked_item(self.create_item_by_code(shard_code))
                        boss_loc.progress_type = LocationProgressType.DEFAULT
                        locked_shard_count += 1

                    logger.info(
                        "[P%s] Locked %s shard items onto boss-defeat locations (mode=%s)",
                        self.player,
                        locked_shard_count,
                        self.options.shards.current_key,
                    )

                open_physical_locations = [
                    loc
                    for loc in (
                        boss_locations
                        + map_chest_locations
                        + vitality_chest_locations
                        + sound_player_chest_locations
                        + hub_switch_locations
                        + lever_locations
                        + minor_chest_locations
                        + room_sanity_locations
                        + area_visit_locations
                        + goal_game_locations
                    )
                    if loc.item is None
                ]
                # An unresolved tutorial lock removes a location but does not
                # remove its eventual reward from AP's pool until pre_fill.
                needed_pool_size = len(open_physical_locations) + int(
                    getattr(self, "_starting_mirror_placeholder", None) is not None
                )

                # Generate collection items only for active, source-backed checks.
                # Two known sources still need compartment attribution; their
                # native rewards and historical dormant location IDs are retained.
                active_collection_item_codes = {
                    kirby_data.locations[loc.key].default_item
                    for loc in minor_chest_locations if loc.key is not None
                }
                # Weighted-slot eligibility is independent of AP classification.
                weighted_item_codes = ITEM_POOL_POLICY.weighted_item_codes
                non_filler_item_codes = [
                    item.item_id
                    for item in kirby_data.items.values()
                    if item.item_id not in weighted_item_codes
                    and (
                        not item.tags.intersection({"SprayPaint", "MusicSheet"})
                        or item.item_id in active_collection_item_codes
                    )
                ]
                from .starting_mirror import random_starting_mirror_enabled

                excluded_mirror = (
                    frozenset() if random_starting_mirror_enabled(self)
                    else ITEM_POOL_POLICY.pool_exclusions["random_starting_mirror_off"]
                )
                non_filler_item_codes = [
                    code for code in non_filler_item_codes
                    if code != tutorial_hub_code and code not in excluded_mirror
                ]
                vitality_item_codes = getattr(self, "_vitality_item_codes", None)
                if vitality_item_codes is None:
                    vitality_item_codes = {
                        item.item_id
                        for item in kirby_data.items.values()
                        if "Vitality" in item.tags
                    }
                    self._vitality_item_codes = vitality_item_codes
                map_item_codes = ITEM_POOL_POLICY.pool_exclusions["start_with_all_maps"]
                if self.options.shards.value == RandomizeShards.option_vanilla:
                    shard_code_set = set(shard_item_codes)
                    non_filler_item_codes = [
                        code for code in non_filler_item_codes if code not in shard_code_set
                    ]

                health_range = self._health_range()
                from .vitality import VITALITY_ITEM_IDS
                active_vitality_codes = set(VITALITY_ITEM_IDS[:health_range.vitality_count])
                non_filler_item_codes = [
                    code for code in non_filler_item_codes
                    if code not in vitality_item_codes or code in active_vitality_codes
                ]
                logger.info(
                    "[P%s] Health range: %s..%s HP; %s unique Vitality Counter item(s)",
                    self.player,
                    health_range.minimum,
                    health_range.maximum,
                    health_range.vitality_count,
                )

                if self._start_with_all_maps_enabled():
                    excluded_map_count = sum(
                        1 for code in non_filler_item_codes if code in map_item_codes
                    )
                    non_filler_item_codes = [
                        code for code in non_filler_item_codes if code not in map_item_codes
                    ]
                    logger.info(
                        "[P%s] start_with_all_maps: removed %s map item(s) from non-filler pool",
                        self.player,
                        excluded_map_count,
                    )

                non_filler_item_codes = [
                    code for code in non_filler_item_codes if code not in ITEM_POOL_POLICY.pool_exclusions["always"]
                ]
                # A reconstructed seed retains its original gate catalog.
                if (seed_gateable := getattr(self, "_seed_gateable_abilities", None)) is not None:
                    seed_unlocks = {f"{name} Ability" for name in seed_gateable}
                    non_filler_item_codes = [
                        code for code in non_filler_item_codes
                        if "Abilities" not in kirby_data.items[code].tags or self.item_id_to_name[code] in seed_unlocks
                    ]
                if not self._area_keys_enabled():
                    excluded_key_codes = ITEM_POOL_POLICY.pool_exclusions["area_keys_off"]
                    non_filler_item_codes = [code for code in non_filler_item_codes if code not in excluded_key_codes]

                if not self._ability_gating_enabled():
                    excluded_ability_codes = ITEM_POOL_POLICY.pool_exclusions["ability_gating_off"]
                    excluded_ability_count = sum(
                        1 for code in non_filler_item_codes if code in excluded_ability_codes
                    )
                    non_filler_item_codes = [
                        code for code in non_filler_item_codes if code not in excluded_ability_codes
                    ]
                    logger.info(
                        "[P%s] ability_gating: removed %s ability unlock item(s) from non-filler pool",
                        self.player,
                        excluded_ability_count,
                    )

                if len(non_filler_item_codes) > needed_pool_size:
                    raise ValueError(
                        "KirbyAM item pool mismatch: non-filler item count %d exceeds open physical locations %d"
                        % (len(non_filler_item_codes), needed_pool_size)
                    )

                eligible_filler_slots = needed_pool_size - len(non_filler_item_codes)
                active_trap_labels = self._active_trap_pool()
                trap_count = 0
                if self._traps_enabled() and active_trap_labels and eligible_filler_slots > 0:
                    trap_count = (eligible_filler_slots * self._trap_fill_percentage()) // 100
                filler_needed = eligible_filler_slots - trap_count
                active_filler_labels, active_filler_weights = self._active_filler_weighted_pool()
                randomized_item_codes.extend(non_filler_item_codes)
                randomized_item_codes.extend(
                    self.item_name_to_id[self.random.choice(active_trap_labels)]
                    for _ in range(trap_count)
                )
                randomized_item_codes.extend(
                    self.item_name_to_id[self.get_filler_item_name()]
                    for _ in range(filler_needed)
                )
                self.random.shuffle(randomized_item_codes)

                non_filler_pool_codes = [
                    code
                    for code in randomized_item_codes
                    if code not in weighted_item_codes
                ]
                if sorted(non_filler_pool_codes) != sorted(non_filler_item_codes):
                    raise ValueError(
                        "KirbyAM item pool invariant failed: randomized non-filler item set does not match expected set"
                    )

                if len(randomized_item_codes) != needed_pool_size:
                    raise ValueError(
                        "KirbyAM item pool mismatch: open physical locations=%s randomized item count=%s"
                        % (needed_pool_size, len(randomized_item_codes))
                    )

                vitality_code_counts = Counter(
                    code for code in randomized_item_codes if code in vitality_item_codes
                )
                expected_vitality_counts = Counter({code: 1 for code in active_vitality_codes})
                if vitality_code_counts != expected_vitality_counts:
                    raise ValueError(
                        "KirbyAM vitality pool invariant failed: active counters must appear exactly once. "
                        f"expected={dict(expected_vitality_counts)} actual={dict(vitality_code_counts)}"
                    )
                logger.info(
                    "[P%s] Vitality counter pool multiplicity: %s",
                    self.player,
                    dict(sorted(vitality_code_counts.items())),
                )
                logger.info(
                    "[P%s] Trap pool summary: enabled=%s percentage=%s "
                    "eligible_filler_slots=%s selected_traps=%s filler_remaining=%s",
                    self.player,
                    self._traps_enabled(),
                    self._trap_fill_percentage(),
                    eligible_filler_slots,
                    trap_count,
                    filler_needed,
                )
                if self._traps_enabled() and self._no_extra_lives_enabled():
                    logger.info(
                        "[P%s] no_extra_lives: removed life-based traps from the active trap pool",
                        self.player,
                    )
                logger.info(
                    "[P%s] Filler weights (active pool): %s",
                    self.player,
                    {
                        label: weight
                        for label, weight in zip(active_filler_labels, active_filler_weights)
                    },
                )
                logger.info(
                    "[P%s] Trap labels (active pool): %s",
                    self.player,
                    active_trap_labels,
                )

                if self._start_with_all_maps_enabled():
                    map_code_counts = Counter(
                        code for code in randomized_item_codes if code in map_item_codes
                    )
                    if map_code_counts:
                        raise ValueError(
                            "KirbyAM map pool invariant failed in start_with_all_maps mode: "
                            f"expected zero map items in pool, got counts={dict(map_code_counts)}"
                        )
                    logger.info(
                        "[P%s] start_with_all_maps: confirmed no map items in randomized pool",
                        self.player,
                    )

            if (
                (
                    boss_locations
                    or map_chest_locations
                    or vitality_chest_locations
                    or sound_player_chest_locations
                    or hub_switch_locations
                    or minor_chest_locations
                    or room_sanity_locations
                    or area_visit_locations
                    or goal_game_locations
                )
                and not randomized_item_codes
            ):
                raise ValueError(
                    "KirbyAM item pool build failed: no randomized items were produced. "
                    "This likely indicates a problem with boss/major/vitality/"
                    "sound-player/hub-switch/minor-chest locations, "
                    "room-sanity/area-visit locations, or region/location data."
                )

            itempool: list[KirbyAmItem] = [
                self.create_item_by_code(code) for code in randomized_item_codes
            ]

            # Add to AP pool
            self.multiworld.itempool += itempool

            useful_count = sum(1 for item in itempool if item.useful)
            filler_count = sum(1 for item in itempool if item.filler)
            progression_count = sum(1 for item in itempool if item.advancement)
            trap_count = sum(1 for item in itempool if item.trap)
            shard_group = resolve_item_group(
                self.item_name_groups,
                "Shards",
                default=self._SHARD_ITEM_LABEL_ORDER,
            )
            pool_shard_count = sum(1 for item in itempool if item.name in shard_group)
            logger.info(
                "[P%s] Item pool classification summary: useful=%s filler=%s progression=%s trap=%s",
                self.player,
                useful_count,
                filler_count,
                progression_count,
                trap_count,
            )

            # Log item creation (randomized pool + fixed shard placements)
            log_items_created(
                self.player,
                len(itempool),
                locked_shard_count + pool_shard_count,
                len(itempool) - pool_shard_count,
            )

    @classmethod
    def stage_create_items(cls, multiworld: MultiWorld) -> None:
        # All Kirby regions and locked events now exist. Finalize the starting
        # key before AP snapshots the item pool or applies item-link handling.
        worlds = list(multiworld.get_game_worlds(cls.game))
        for world in worlds:
            world.set_rules()
        for world in worlds:
            world._ensure_starting_area_key()
            world._verify_tutorial_hub_connection()

    # Rules are needed during item creation to evaluate real starting access.
    # The normal set_rules stage must not stack the same entrance predicates.
    def set_rules(self) -> None:
        if getattr(self, "_rules_applied", False):
            return
        from .rules import set_rules as set_rules_impl
        set_rules_impl(self)
        self._rules_applied = True

    # Helper methods for generation and output
    def generate_basic(self) -> None:
        # Create auth for client connection; the item pool is already final.
        self.auth = self.random.randbytes(16)

    def _ensure_starting_area_key(self) -> None:
        if not self._area_keys_enabled():
            return

        # Rules and user-provided starting inventory are available. Measure the
        # real AP graph before finalizing the item pool, not a second JSON graph.
        state = CollectionState(self.multiworld)
        # Addressless locked events (area visits, switches, and other native
        # progression state) are part of the same graph used by fill.  Sweep
        # them before counting checks so the fallback decision cannot drift
        # from Archipelago's actual CollectionState semantics.
        state.sweep_for_advancements(locations=self.multiworld.get_locations(self.player))
        early_reachable_checks = [
            location
            for location in self.multiworld.get_locations(self.player)
            if location.address is not None and location.can_reach(state)
        ]
        early_reachable_check_count = len(early_reachable_checks)
        self._early_reachable_check_count = early_reachable_check_count

        if early_reachable_check_count >= EARLY_REACHABLE_CHECK_THRESHOLD:
            logger.info(
                "[P%s] Early reachable checks: %s (threshold=%s); no fallback Area Key needed",
                self.player,
                early_reachable_check_count,
                EARLY_REACHABLE_CHECK_THRESHOLD,
            )
            return

        player_precollected_items = self.multiworld.precollected_items[self.player]
        if any(item.name == FALLBACK_STARTING_AREA_KEY_LABEL for item in player_precollected_items):
            logger.info(
                "[P%s] Early reachable checks: %s (threshold=%s); %s is already precollected",
                self.player,
                early_reachable_check_count,
                EARLY_REACHABLE_CHECK_THRESHOLD,
                FALLBACK_STARTING_AREA_KEY_LABEL,
            )
            return

        fallback_pool_index = next(
            (
                index
                for index, item in enumerate(self.multiworld.itempool)
                if item.player == self.player and item.name == FALLBACK_STARTING_AREA_KEY_LABEL
            ),
            None,
        )
        if fallback_pool_index is None:
            raise ValueError(
                f"[P{self.player}] Cannot precollect fallback Area Key "
                f"{FALLBACK_STARTING_AREA_KEY_LABEL!r}: no owned copy exists in the item pool"
            )

        fallback_item = self.multiworld.itempool.pop(fallback_pool_index)
        self.multiworld.itempool.append(self.create_filler())
        self.push_precollected(fallback_item)
        logger.info(
            "[P%s] Early reachable checks: %s (threshold=%s); precollected %s and replaced its pool slot with filler",
            self.player,
            early_reachable_check_count,
            EARLY_REACHABLE_CHECK_THRESHOLD,
            FALLBACK_STARTING_AREA_KEY_LABEL,
        )

    def generate_output(self, output_directory: str) -> None:
        try:
            # Load base patch data from package resources
            patch_data = pkgutil.get_data(__name__, "data/base_patch.bsdiff4")
            if patch_data is None:
                raise FileNotFoundError(
                    "Missing resource 'data/base_patch.bsdiff4' in the kirbyam package/apworld. "
                    "Ensure it is included when packaging."
                )

            # Create procedure patch
            patch = KirbyAmProcedurePatch(player=self.player, player_name=self.player_name)
            patch.write_file("base_patch.bsdiff4", patch_data)
            write_tokens(self, patch, filled_locations=self.multiworld.get_locations(self.player))

            # Write the patch file
            out_file_name = self.multiworld.get_out_file_name_base(self.player)
            patch.write(os.path.join(output_directory, f"{out_file_name}{patch.patch_file_ending}"))

            if hasattr(self, "_generation_start_time"):
                elapsed = time.time() - self._generation_start_time
                log_generation_complete(self.player, self.player_name, elapsed)
        except Exception as exc:
            log_generation_error(self.player, self.player_name, str(exc))
            raise

    def modify_multidata(self, multidata: "MultiData") -> None:
        # Register auth token using the same (team, slot) tuple shape as player names.
        key = base64.b64encode(self.auth).decode("ascii")
        connect_names = multidata["connect_names"]
        connect_names[key] = connect_names[self.player_name]

    def finalize_multiworld(self) -> None:
        if self.options.goal.value == Goal.option_capture_the_flag and self._flag_location_id is None:
            from .capture_the_flag import resolve_flag
            self._flag_location_id = resolve_flag(self)

    def write_spoiler(self, spoiler_handle: TextIO) -> None:
        mode = int(self.options.ability_randomization_mode.value)
        if mode != AbilityRandomizationMode.option_shuffled:
            return

        policy = getattr(self, "_enemy_copy_ability_policy", None)
        if not isinstance(policy, dict):
            return

        randomize_statues = bool(self.options.ability_randomization_statues.value)
        spoiler_rows = build_enemy_copy_spoiler_rows(policy, include_statues=randomize_statues)
        if not spoiler_rows:
            return

        spoiler_title = "Enemy Copy Ability Shuffle"
        if randomize_statues:
            spoiler_title = "Enemy and World Statue Copy Ability Shuffle (Copy Ability Room excluded)"
        spoiler_handle.write(f"\n\n{self.player_name}'s {spoiler_title}:\n\n")
        for source_kind, source_key, ability_name in spoiler_rows:
            spoiler_handle.write(f"{source_kind:12s} | {source_key:28s} -> {ability_name}\n")

    # Helper method to fill slot data
    def fill_slot_data(self) -> dict[str, Any]:
        from .phone_traversal import validate_phone_profile
        validate_phone_profile(self, require_policy=True)
        from .yellow_cupid import validate_profile as validate_yellow_cupid_profile
        validate_yellow_cupid_profile(self)
        # Slot data needed by client.
        # Pre-v0.1.0 policy: emit only canonical ability_randomization_* keys.
        # Legacy key aliases are intentionally not emitted before first public release.
        slot_data = self.options.as_dict(
            "goal",
            "configured_area_boss",
            "required_area_bosses",
            "shards",
            "start_with_all_maps",
            "random_starting_mirror",
            "starting_kirby_color",
            "no_extra_lives",
            "ability_gating",
            "advanced_logic",
            "enable_traps",
            "trap_fill_percentage",
            "enemy_health_multiplier",
            "minimum_health",
            "maximum_health",
            "death_link",
            "ability_randomization_mode",
            "ability_randomization_boss_spawns",
            "ability_randomization_minibosses",
            "ability_randomization_passive_enemies",
            "ability_randomization_no_ability_weight",
            "ability_randomization_statues",
            "room_sanity",
            toggles_as_bools=True,
        )
        if self.options.goal.value == Goal.option_full_completion:
            slot_data["full_completion_version"] = 1
        slot_data["world_version"] = self.world_version.as_simple_string()
        from .completion import PHYSICAL_CHECK_SAVE_VERSION
        slot_data["physical_check_save_version"] = PHYSICAL_CHECK_SAVE_VERSION
        slot_data["goal_game_protocol_version"] = 3
        slot_data["health_protocol_version"] = 2
        slot_data["hub_connection_protocol_version"] = 2
        slot_data["copy_ability_room_protocol_version"] = 2
        resolved_color_id, resolved_color_name = self._get_resolved_starting_kirby_color()
        slot_data["kirby_color_catalog_version"] = COLOR_CATALOG_VERSION
        slot_data["starting_kirby_color"] = resolved_color_id
        slot_data["starting_kirby_color_name"] = resolved_color_name
        slot_data["starting_kirby_color_randomize_on_room_transition"] = (
            self._starting_kirby_color_randomize_on_room_transition_enabled()
        )
        slot_data["goal_configured_area_boss_key"] = self._get_resolved_configured_area_boss_goal_key()
        if (self.options.goal.value == Goal.option_defeat_area_boss
                and getattr(self.options.configured_area_boss, "was_random", False) is True):
            slot_data[RANDOM_AREA_BOSS_SLOT_KEY] = True
        if self.options.goal.value == Goal.option_capture_the_flag:
            from .capture_the_flag import FLAG_SLOT_KEY
            if self._flag_location_id is None:
                raise ValueError("KirbyAM: Capture the Flag target was not resolved.")
            slot_data[FLAG_SLOT_KEY] = self._flag_location_id
        multiworld = getattr(self, "multiworld", None)
        precollected_items: tuple[Item, ...] | list[Item] = ()
        if multiworld is not None:
            precollected_by_player = getattr(multiworld, "precollected_items", {})
            precollected_items = precollected_by_player.get(getattr(self, "player", 1), ())
        slot_data["starting_copy_ability_room_access"] = any(
            item.name == "Copy Ability Room Access" for item in precollected_items
        )
        slot_data["phone_protocol_version"] = 1
        slot_data["starting_phone_access"] = any(
            item.name == "Phone a Friend" for item in precollected_items
        )
        slot_data["area_keys"] = self._area_keys_enabled()
        slot_data["starting_area_key_bitfield"] = (
            area_key_bitfield_from_items(precollected_items) if slot_data["area_keys"] else 0
        )
        slot_data["core_landmark_location_ids"] = sorted(
            location.location_id
            for location in kirby_data.locations.values()
            if "CoreLandmark" in location.tags
        )
        ability_gating_enabled = self._ability_gating_enabled()
        slot_data["ability_gating"] = ability_gating_enabled
        policy = getattr(self, "_enemy_copy_ability_policy", None)
        assert policy is not None, (
            "Enemy copy ability policy must be initialized before fill_slot_data is called."
        )
        allowed_abilities = tuple(policy.get("allowed_abilities", ()))
        slot_data["enemy_copy_ability_whitelist"] = list(allowed_abilities)
        slot_data["enemy_copy_ability_policy"] = dict(policy)
        if self._candy912_linked_west_fuse:
            from .conditional_routes import CANDY_FUSE
            slot_data[CANDY_FUSE.SLOT_KEY] = True

        from .rules import get_stake_breaking_abilities, get_stake_gated_transition_entrance_names

        slot_data["stake_breaking_abilities"] = list(get_stake_breaking_abilities())
        slot_data["stake_gated_transitions"] = list(get_stake_gated_transition_entrance_names())

        ability_unlock_items: dict[str, str] = {}
        for item_data in kirby_data.items.values():
            if "Abilities" not in item_data.tags:
                continue
            if not item_data.label.endswith(" Ability"):
                continue
            ability_name = item_data.label.removesuffix(" Ability")
            ability_unlock_items[ability_name] = item_data.label

        if ability_gating_enabled:
            slot_data["ability_gateable_abilities"] = list(getattr(self, "_seed_gateable_abilities", GATEABLE_ENEMY_COPY_ABILITIES))
        else:
            slot_data["ability_gateable_abilities"] = []
        # Ownership is represented even when gates are disabled; it never equips.
        slot_data["ability_unlock_items"] = {
            ability_name: ability_unlock_items[ability_name]
            for ability_name in sorted(ability_unlock_items)
        }

        # Tracker surface integration (Issue #114)
        # Expose all locations and rooms for tracker display
        slot_data["locations"] = {
            loc_key: {
                "label": loc_data.label,
                "location_id": loc_data.location_id,
                "category": loc_data.category.name,
                "tags": sorted(loc_data.tags),
            }
            for loc_key, loc_data in kirby_data.locations.items()
            if loc_key != "GOAL_HIDDEN_AREA_BOSS"
            and (
                loc_data.category != LocationCategory.MINOR_CHEST
                or loc_data.source_rom_offset is not None
            )
        }

        # All rooms (visited and unvisited), including those not in Room Sanity
        rooms_payload = load_json_data("regions/rooms.json")
        rooms = rooms_payload if isinstance(rooms_payload, dict) else {}
        normalized_rooms: dict[str, dict[str, Any]] = {}
        for room_key, room_data in rooms.items():
            if not isinstance(room_key, str) or not isinstance(room_data, dict):
                continue
            exits, _requirements = normalize_region_exits(room_key, room_data)
            room_sanity = room_data.get("room_sanity")
            locations_payload = room_data.get("locations")
            if not isinstance(room_sanity, dict) and isinstance(locations_payload, dict):
                room_sanity = locations_payload.get("room_sanity")
            normalized_rooms[room_key] = {
                "label": room_data.get("label") or format_room_region_label(room_key),
                "exits": exits,
                "parent_region": room_key.split("/")[0] if "/" in room_key else "",
                "room_sanity_location_id": (
                    room_sanity.get("location_id") if isinstance(room_sanity, dict) else None
                ),
            }
        slot_data["rooms"] = normalized_rooms

        # Unique items for tracker display (items tagged as "Unique").
        # Emit in stable deduplicated order for tracker/cache determinism.
        slot_data["unique_items"] = sorted(
            {
                item_data.label
                for item_data in kirby_data.items.values()
                if "Unique" in item_data.tags
            }
        )

        from .tracker import export_tracker_data
        slot_data["tracker"] = export_tracker_data(self, precollected_items)

        return slot_data

    # Helper methods to create items and events
    def create_item(self, name: str) -> KirbyAmItem:
        return self.create_item_by_code(self.item_name_to_id[name])

    # Helper method to create item by item code
    def create_item_by_code(self, item_code: int) -> KirbyAmItem:
        from .traversal_rules import permission_is_progression

        classification = get_item_classification(item_code)
        if permission_is_progression(self, item_code):
            classification = ItemClassification.progression
        return KirbyAmItem(
            self.item_id_to_name[item_code],
            classification,
            item_code,
            self.player,
        )

    # Helper method to create event item
    def create_event(self, name: str) -> KirbyAmItem:
        return KirbyAmItem(
            name,
            ItemClassification.progression,
            None,
            self.player,
        )
