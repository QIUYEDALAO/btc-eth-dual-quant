from __future__ import annotations
import copy
import unittest
from scripts.u07_cross_sectional_paper_protocol_check import EXPECTED_HASH, PROTOCOL_PATH, load, validate, validate_report


class U07CrossSectionalPaperProtocolTests(unittest.TestCase):
    def setUp(self): self.protocol = load(PROTOCOL_PATH)
    def test_repository_protocol_is_exact_and_outcome_blind(self):
        self.assertEqual(self.protocol["content_hash"], EXPECTED_HASH); self.assertEqual(validate(self.protocol), []); self.assertEqual(validate_report(), [])
    def test_generated_time_does_not_change_identity(self):
        changed = copy.deepcopy(self.protocol); changed["generated_utc"] = "2030-01-01T00:00:00Z"; self.assertEqual(validate(changed), [])
    def test_every_authority_binding_is_hash_bound(self):
        for key in self.protocol["authority_bindings"]:
            changed = copy.deepcopy(self.protocol); changed["authority_bindings"][key] = "0" * 64; self.assertTrue(validate(changed), key)
    def test_range_alignment_and_oos_cannot_change(self):
        for key, value in (("is_start", "2021-01-01T00:00:00Z"), ("signal_timeframe", "1h"), ("signal_alignment", "rolling"), ("oos_opened", True)):
            changed = copy.deepcopy(self.protocol); changed["scope"][key] = value; self.assertTrue(validate(changed), key)
    def test_stress_resilience_cluster_or_horizon_change_fails(self):
        mutations = [
            ("point_in_time_universe", "minimum_active_members", 9),
            ("market_stress_event", "common_move_maximum", "-0.0249"),
            ("market_stress_event", "negative_breadth_fraction_minimum", "0.79"),
            ("relative_resilience_candidate", "relative_residual_minimum", "0.0199"),
            ("relative_resilience_candidate", "candidate_simple_return_minimum", "-0.0051"),
            ("episode_clustering", "connected_window_hours", 47),
            ("observation_contract", "horizon_hours", [1, 4, 24]),
        ]
        for section, key, value in mutations:
            changed = copy.deepcopy(self.protocol); changed[section][key] = value; self.assertTrue(validate(changed), f"{section}.{key}")
    def test_membership_lifecycle_or_later_search_shortcut_fails(self):
        for key in ("replacement_member_allowed", "current_membership_backfill_allowed", "lifecycle_crossing_assumption_allowed"):
            changed = copy.deepcopy(self.protocol); changed["point_in_time_universe"][key] = True; self.assertTrue(validate(changed), key)
        changed = copy.deepcopy(self.protocol); changed["observation_contract"]["search_later_if_reference_missing"] = True; self.assertTrue(validate(changed))
    def test_gate_or_cost_reduction_fails(self):
        changed = copy.deepcopy(self.protocol); changed["paper_gates"]["complete_is_independent_episodes_minimum"] = 59; self.assertTrue(validate(changed))
        changed = copy.deepcopy(self.protocol); changed["cost_reference_roundtrip"]["cost_x2"] = "0.0059"; self.assertTrue(validate(changed))
    def test_outcome_or_execution_authorization_fails(self):
        allowed = {"paper_protocol_frozen", "exact_head_independent_review"}
        self.assertEqual({key for key, value in self.protocol["authorizations"].items() if value}, allowed)
        for key in set(self.protocol["authorizations"]) - allowed:
            changed = copy.deepcopy(self.protocol); changed["authorizations"][key] = True; self.assertTrue(validate(changed), key)
    def test_extra_result_or_fixed_rule_field_fails(self):
        for key in ("target", "stop", "position", "returns", "event_count", "outcome"):
            changed = copy.deepcopy(self.protocol); changed[key] = "forbidden"; self.assertTrue(validate(changed), key)


if __name__ == "__main__": unittest.main()
