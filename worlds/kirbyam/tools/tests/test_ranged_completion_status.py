"""Keep explicit partial-coverage declarations honest against the real installer.

These isolated rules are not generated seeds or native route replays. Repair a
coverage gap by changing implementation and declaration together, not by keeping
the old permissive outcome as a permanent requirement.
"""
from __future__ import annotations

import hashlib
import unittest
from types import SimpleNamespace
from typing import Any, ClassVar
from unittest.mock import patch

from test.param import classvar_matrix

from Options import Accessibility
from worlds.kirbyam import traversal_rules
from worlds.kirbyam.tools import build_ranged_completion_status as status_tool
from worlds.kirbyam.tools.build_ranged_target_coverage import ROOT
from worlds.kirbyam.traversal import SourcePolicy
from worlds.kirbyam.traversal_data import _room_catalog

CONTRACT = status_tool.load_contract()
TARGETS = {row["id"]: row for row in _room_catalog()[0]}
PUBLIC = status_tool.policy_profiles()
SYNTHETIC = status_tool.policy_profiles(synthetic=True)
REPORT = status_tool.build_status()


def installer_probe(row: dict[str, Any], policy: SourcePolicy, *,
                    gating: bool = True, area_keys: bool = False) -> tuple[bool, bool]:
    """Actual graph installation; base false/true, no items or independent access."""
    target = SimpleNamespace(access_rule=lambda state: state.base)
    original_rule = target.access_rule
    world = SimpleNamespace(
        player=1, _enemy_copy_ability_policy=policy.policy,
        _ability_gating_enabled=lambda: gating, _area_keys_enabled=lambda: area_keys,
        options=SimpleNamespace(ability_randomization_statues=SimpleNamespace(value=False),
                                accessibility=Accessibility(Accessibility.option_minimal)),
        multiworld=SimpleNamespace(get_entrance=lambda name, player: target,
                                   get_location=lambda name, player: target,
                                   get_region=lambda name, player: name,
                                   register_indirect_condition=lambda region, entrance: None),
    )
    state = SimpleNamespace(base=False, has=lambda name, player: False,
                            can_reach_region=lambda name, player: False)
    with patch.object(traversal_rules, "extra_traversal_targets", return_value=(row,)):
        traversal_rules.install_extra_traversal_rules(world)
    assert target.access_rule(state) is False, "Installer relaxed an existing closed base rule"
    state.base = True
    return target.access_rule is not original_rule, target.access_rule(state)


class TestRangedCompletionContract(unittest.TestCase):
    def test_declaration_matches_current_sources_and_stays_partial(self) -> None:
        self.assertEqual(REPORT["declaration_errors"], [])
        self.assertEqual(REPORT["completion"], CONTRACT["completion_claim"])
        self.assertEqual(REPORT["completion"], "partial")
        self.assertTrue(REPORT["limits"])
        self.assertEqual({row["id"] for row in REPORT["targets"]}, set(CONTRACT["bounded_targets"]))

    def test_profiles_retain_real_public_pool_and_explicit_synthetic_boundary(self) -> None:
        self.assertTrue(all(len(policy.policy["allowed_abilities"]) == 25 for policy in PUBLIC.values()))
        self.assertEqual({policy.mode for policy in PUBLIC.values()}, {0, 1, 2})
        self.assertEqual({PUBLIC[name].policy["ability_randomization_no_ability_weight"]
                          for name in ("full_live_normal0", "full_live_normal99", "full_live_normal100")}, {0, 99, 100})
        self.assertIn("no public custom-whitelist option", REPORT["synthetic_boundary"])
        self.assertIn("not generation acceptance", REPORT["profile_boundary"])

    def test_fingerprints_include_runtime_policy_and_declaration_sources(self) -> None:
        for name in ("traversal_rules.py", "traversal.py", "traversal_data.py", "ability_randomization.py",
                     "enemy_ability_runtime_patch.py", "rules.py", "data.py", "data/regions/rooms.json",
                     "dev-docs/ranged-completion-scope.json"):
            self.assertEqual(REPORT["input_sha256"][name], hashlib.sha256((ROOT / name).read_bytes()).hexdigest())
        self.assertTrue(all(not name.startswith("/") and "\\" not in name for name in REPORT["input_sha256"]))
        self.assertEqual(len(REPORT["input_fingerprint_sha256"]), 64)

    def test_missing_declaration_cannot_hide_new_fallback(self) -> None:
        declaration = status_tool.load_contract()
        declaration["policy_fallback_targets"] = []
        declaration["public_profile_fallbacks"] = {}
        with patch.object(status_tool, "load_contract", return_value=declaration):
            report = status_tool.build_status()
        self.assertEqual(len(report["declaration_errors"]), 2)
        self.assertEqual(report["completion"], "partial")

    def test_clear_inventory_is_not_automatic_gameplay_certification(self) -> None:
        declaration = status_tool.load_contract()
        declaration["completion_claim"] = "complete"
        declaration["unresolved_evidence"] = []
        with patch.object(status_tool, "load_contract", return_value=declaration):
            report = status_tool.build_status()
        self.assertIn("cannot certify completion", report["declaration_errors"][0])
        self.assertEqual(report["completion"], "partial")

    def test_chocolate_and_sound_effects_remain_separate_or_witnesses(self) -> None:
        rows = {row["id"]: row for row in REPORT["targets"]}
        self.assertEqual(len(rows["bomb_517_chocolate"]["witnesses"]), 10)
        sound = rows["frozen_825_sound_effects"]
        self.assertEqual(len(sound["witnesses"]), 4)
        self.assertEqual(sound["target_source_conditions"], [])
        self.assertEqual(sound["public_fallback_profiles"], [])
        self.assertEqual(rows["bomb_538_beam_left_exit"]["public_fallback_profiles"], [])

    def test_summary_is_bounded_and_deterministic(self) -> None:
        summary = status_tool.format_summary(REPORT)
        self.assertEqual(summary, status_tool.format_summary(status_tool.build_status()))
        self.assertIn("PARTIAL", summary)
        self.assertIn("not counts of missing gates", summary)
        self.assertIn("does not prove a physical softlock", summary)
        self.assertLess(len(summary.splitlines()), 30)


@classvar_matrix(target_id=CONTRACT["bounded_targets"], profile=PUBLIC, area_keys=(False, True))
class TestPublicProfileInstaller(unittest.TestCase):
    target_id: ClassVar[str]
    profile: ClassVar[str]
    area_keys: ClassVar[bool]

    def test_declaration_matches_installed_rule(self) -> None:
        expected_fallback = self.target_id in CONTRACT["public_profile_fallbacks"][self.profile]
        row = next(row for row in REPORT["targets"] if row["id"] == self.target_id)
        self.assertEqual(self.profile in row["public_fallback_profiles"], expected_fallback)
        installed, base_true_result = installer_probe(
            TARGETS[self.target_id], PUBLIC[self.profile], area_keys=self.area_keys,
        )
        self.assertIs(installed, not expected_fallback)
        self.assertIs(base_true_result, expected_fallback)


@classvar_matrix(target_id=CONTRACT["bounded_targets"], profile=SYNTHETIC)
class TestSyntheticProfileInstaller(unittest.TestCase):
    target_id: ClassVar[str]
    profile: ClassVar[str]

    def test_diagnostics_not_public_options(self) -> None:
        row = TARGETS[self.target_id]
        conditions = status_tool.source_conditions(row)
        resolver = SYNTHETIC[self.profile]
        # Independent reading of the declared raw-source condition, not accepting
        # arbitrary installer outcomes or treating a permission filter as equipment.
        expected = not conditions or any(
            len(grant := resolver.grant(entry["source_key"], lambda _: True).guaranteed) == 1
            and grant <= set(entry.get("abilities", [entry.get("ability")])) for entry in conditions
        )
        recorded = next(row for row in REPORT["targets"] if row["id"] == self.target_id)
        self.assertEqual(self.profile in recorded["synthetic_applicable_profiles"], expected)
        installed, base_true_result = installer_probe(row, resolver)
        self.assertIs(installed, expected)
        self.assertIs(base_true_result, not expected)
        self.assertNotIn(self.profile, REPORT["public_profiles"])
