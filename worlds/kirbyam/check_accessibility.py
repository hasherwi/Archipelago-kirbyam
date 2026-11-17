"""Reject generated Kirby seeds that strand any enabled physical check."""

from __future__ import annotations

from collections.abc import Iterable
import json
import logging
from typing import Any

from BaseClasses import CollectionState, MultiWorld
from Fill import FillError


class KirbyAmCheckAccessibilityError(FillError):
    """The selected goal may be beatable, but some Kirby checks are stranded."""


def _room16_source_rejection_evidence(
    multiworld: MultiWorld, player: int, unfilled: list[str],
    infeasible: list[str], fill_locked: list[str],
) -> dict[str, Any] | None:
    """Diagnostic evidence only; never change acceptance or suppress an error.

    Restrict this to an intentional source/option exclusion, not any failure to
    reach Room16. The fuzzer independently reconstructs the actual raw policy.
    """
    from .traversal import SourcePolicy
    from .traversal_rules import extra_traversal_targets

    if multiworld.players != 1 or player != 1 or unfilled or infeasible != ['Room 4-16']:
        return None
    world = multiworld.worlds[player]
    options = world.options
    if (options.room_sanity.value != 1 or options.accessibility.value not in (0, 2)
            or (options.accessibility.value == 0 and fill_locked)):
        return None
    raw = getattr(world, '_enemy_copy_ability_policy', None)
    if not isinstance(raw, dict) or not raw or raw.get('mode') != options.ability_randomization_mode.value:
        return None
    row = next((row for row in extra_traversal_targets() if row['id'] == 'switch_533_room16'), None)
    if (row is None or row.get('fail_closed') is not True
            or row.get('required_for_generation') is not False
            or row.get('native_room') != 533
            or row.get('region') != 'REGION_MUSTARD_MOUNTAIN/ROOM_4_15'
            or row.get('exit') != 'REGION_MUSTARD_MOUNTAIN/ROOM_4_16'
            or row.get('advanced_graphs') != ['hub4_crash_entry', 'hub4_magic_entry']):
        return None
    advanced = options.advanced_logic.value
    if type(advanced) is not int or advanced not in (0, 1):
        return None
    try:
        guaranteed = SourcePolicy(raw).grant('FOLEY', lambda _: True).guaranteed
    except (KeyError, TypeError, ValueError):
        return None
    supported = {'Bomb', 'UFO', 'Ice'} | ({'Crash', 'Magic'} if advanced else set())
    if len(guaranteed) == 1 and guaranteed <= supported:
        return None  # Qualified source: access/graph failures must remain red.
    return {'schema': 1, 'player': player, 'seed': multiworld.seed,
            'room_sanity': 1, 'advanced_logic': advanced, 'source_policy': raw}


def validate_all_checks(multiworld: MultiWorld, players: Iterable[int]) -> None:
    """Audit final placements once, without importing the pool into progression.

    Call only after every world's finalizer and progression balancing. A fresh
    state includes precollected items; the ordinary AP sweep credits reachable
    remote deliveries and events while refusing self-locked and cross-player
    cycles. Disabled checks are absent from the instantiated world. Excluded
    physical checks still count: exclusion restricts fill, not player access.
    """
    checks = {player: tuple(location for location in multiworld.get_locations(player)
                            if location.address is not None) for player in players}
    if not checks:
        return
    progression = CollectionState(multiworld)
    progression.sweep_for_advancements()
    stranded = {player: tuple(location for location in locations
                              if location.item is None or not location.can_reach(progression))
                for player, locations in checks.items()}
    stranded = {player: locations for player, locations in stranded.items() if locations}
    if not stranded:
        return

    # Diagnostic only. This state must never decide whether a placed seed passes:
    # it grants permissions from locations that the player may be unable to reach.
    inventory = multiworld.get_all_state()
    messages = []
    for player, locations in sorted(stranded.items()):
        unfilled = sorted(location.name for location in locations if location.item is None)
        infeasible = sorted(location.name for location in locations if not location.can_reach(inventory))
        fill_locked = sorted(location.name for location in locations
                             if location.item is not None and location.can_reach(inventory))
        evidence = _room16_source_rejection_evidence(multiworld, player, unfilled, infeasible, fill_locked)
        if evidence is not None:
            logging.info("KirbyAM Room16 rejection evidence: %s",
                         json.dumps(evidence, sort_keys=True, separators=(",", ":")))
        messages.append(f"Player {player} ({multiworld.get_player_name(player)}): "
                        f"unfilled={unfilled}; unavailable even with all inventory={infeasible}; "
                        f"unreachable from placed progression={fill_locked}")
    raise KirbyAmCheckAccessibilityError(
        "KirbyAM all-check validation failed. Every enabled Kirby check must be reachable, "
        "including with minimal accessibility. Generation stopped before the normal output/archive stage. "
        "Try full accessibility or another seed; source/route restrictions may still require review.\n"
        + "\n".join(messages)
    )
