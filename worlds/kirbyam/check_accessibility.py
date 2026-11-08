"""Reject generated Kirby seeds that strand any enabled physical check."""

from __future__ import annotations

from collections.abc import Iterable

from BaseClasses import CollectionState, MultiWorld
from Fill import FillError


class KirbyAmCheckAccessibilityError(FillError):
    """The selected goal may be beatable, but some Kirby checks are stranded."""


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
        messages.append(f"Player {player} ({multiworld.get_player_name(player)}): "
                        f"unfilled={unfilled}; unavailable even with all inventory={infeasible}; "
                        f"unreachable from placed progression={fill_locked}")
    raise KirbyAmCheckAccessibilityError(
        "KirbyAM all-check validation failed. Every enabled Kirby check must be reachable, "
        "including with minimal accessibility. Generation stopped before the normal output/archive stage. "
        "Try full accessibility or another seed; source/route restrictions may still require review.\n"
        + "\n".join(messages)
    )
