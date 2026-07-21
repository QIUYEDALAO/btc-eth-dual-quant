from __future__ import annotations

import copy
import unittest

from scripts.u04_cross_sectional_paper_protocol_check import (
    EXPECTED_HASH,
    PROTOCOL_PATH,
    load,
    validate,
    validate_report,
)


class U04CrossSectionalPaperProtocolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.protocol = load(PROTOCOL_PATH)

    def test_repository_protocol_is_exact_and_outcome_blind(self) -> None:
        self.assertEqual(self.protocol["content_hash"], EXPECTED_HASH)
        self.assertEqual(validate(self.protocol), [])
        self.assertEqual(validate_report(), [])

    def test_generated_time_does_not_change_content_identity(self) -> None:
        changed = copy.deepcopy(self.protocol)
        changed["generated_utc"] = "2030-01-01T00:00:00Z"
        self.assertEqual(validate(changed), [])

    def test_every_authority_binding_is_hash_bound(self) -> None:
        for key in self.protocol["authority_bindings"]:
            changed = copy.deepcopy(self.protocol)
            changed["authority_bindings"][key] = "0" * 64
            with self.subTest(key=key):
                self.assertTrue(validate(changed))

    def test_range_timeframe_and_oos_cannot_change(self) -> None:
        for key, value in (("is_start", "2021-01-01T00:00:00Z"), ("signal_timeframe", "4h"), ("oos_opened", True)):
            changed = copy.deepcopy(self.protocol)
            changed["scope"][key] = value
            with self.subTest(key=key):
                self.assertTrue(validate(changed))

    def test_membership_or_lifecycle_shortcut_fails(self) -> None:
        for key, value in (
            ("minimum_active_members", 9), ("all_active_members_required", False),
            ("replacement_member_allowed", True), ("current_membership_backfill_allowed", True),
            ("lifecycle_crossing_assumption_allowed", True),
        ):
            changed = copy.deepcopy(self.protocol)
            changed["point_in_time_universe"][key] = value
            with self.subTest(key=key):
                self.assertTrue(validate(changed))

    def test_estimator_threshold_cluster_or_horizon_change_fails(self) -> None:
        mutations = [
            ("residual_event", "common_component", "mean"),
            ("residual_event", "standardized_residual_maximum", "-2.9"),
            ("residual_event", "relative_simple_return_maximum", "-0.0179"),
            ("episode_clustering", "connected_window_hours", 23),
            ("observation_contract", "horizon_hours", [1, 4, 24]),
        ]
        for section, key, value in mutations:
            changed = copy.deepcopy(self.protocol)
            changed[section][key] = value
            with self.subTest(section=section, key=key):
                self.assertTrue(validate(changed))

    def test_gate_or_cost_reduction_fails(self) -> None:
        changed = copy.deepcopy(self.protocol)
        changed["paper_gates"]["complete_is_independent_episodes_minimum"] = 89
        self.assertTrue(validate(changed))
        changed = copy.deepcopy(self.protocol)
        changed["cost_reference_roundtrip"]["cost_x2"] = "0.0059"
        self.assertTrue(validate(changed))

    def test_no_execution_or_outcome_authorization_can_be_enabled(self) -> None:
        allowed_true = {"paper_protocol_frozen", "exact_head_independent_review"}
        self.assertEqual({key for key, value in self.protocol["authorizations"].items() if value}, allowed_true)
        for key in set(self.protocol["authorizations"]) - allowed_true:
            changed = copy.deepcopy(self.protocol)
            changed["authorizations"][key] = True
            with self.subTest(key=key):
                self.assertTrue(validate(changed))

    def test_extra_rule_or_result_field_fails(self) -> None:
        for key in ("target", "stop", "position", "returns", "event_count", "outcome"):
            changed = copy.deepcopy(self.protocol)
            changed[key] = "forbidden"
            with self.subTest(key=key):
                self.assertTrue(validate(changed))


if __name__ == "__main__":
    unittest.main()
