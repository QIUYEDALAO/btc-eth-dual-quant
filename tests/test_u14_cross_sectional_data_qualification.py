from __future__ import annotations

import copy
import unittest

from btc_eth_dual_quant.data.u14_downside_rejection import AuctionPathRow, evaluate_decision, evaluate_stream
from scripts.u04_cross_sectional_data_qualification import load_json
from scripts.u14_cross_sectional_data_qualification import CONFIG, synthetic_rows
from scripts.u14_cross_sectional_data_qualification_check import RESULT, validate


class U14QualificationTests(unittest.TestCase):
    def setUp(self):
        self.config = load_json(CONFIG)
        self.result = load_json(RESULT)

    def test_exact_contract_result_and_gates(self):
        self.assertEqual(validate(self.config, self.result), [])

    def test_generated_time_excluded(self):
        changed = copy.deepcopy(self.config)
        changed["generated_utc"] = "2030"
        self.assertEqual(validate(changed, self.result), [])

    def test_result_or_permission_tamper_fails(self):
        changed = copy.deepcopy(self.result)
        changed["counts"]["maximum_independent_theoretical_24h_episodes"] = 399
        self.assertTrue(validate(self.config, changed))
        changed = copy.deepcopy(self.result)
        changed["authorizations"]["strategy"] = True
        self.assertTrue(validate(self.config, changed))

    def test_complexity_gate_tamper_fails(self):
        changed = copy.deepcopy(self.result)
        changed["complexity_benchmark"]["passes"][0]["elapsed_seconds"] = "30.1"
        self.assertTrue(validate(self.config, changed))
        changed = copy.deepcopy(self.result)
        changed["complexity_benchmark"]["passes"][0]["output_hash"] = "0" * 64
        self.assertTrue(validate(self.config, changed))

    def test_same_event_path_core_is_deterministic(self):
        first = evaluate_stream(synthetic_rows(1500, 15), 15)
        second = evaluate_stream(synthetic_rows(1500, 15), 15)
        self.assertEqual(first, second)
        self.assertEqual(first["input_rows"], 1500)
        self.assertGreater(first["candidate_events"], 0)

    def test_incomplete_and_malformed_groups_fail_closed(self):
        rows = list(synthetic_rows(15, 15))
        self.assertIsNone(evaluate_decision(rows[:9]))
        malformed = list(rows)
        malformed[0] = AuctionPathRow(malformed[0].decision_ms, malformed[0].symbol, 100.0, 99.0, 101.0, 100.0, 100.0, malformed[0].path_closes)
        self.assertIsNone(evaluate_decision(malformed))

    def test_rank_gate_uses_all_active_members(self):
        rows = list(synthetic_rows(15, 15))
        candidate = rows[0]
        rows[0] = AuctionPathRow(candidate.decision_ms, candidate.symbol, 100.0, 100.2, 98.0, 99.9, 100.0, candidate.path_closes)
        for index in range(1, 5):
            row = rows[index]
            rows[index] = AuctionPathRow(row.decision_ms, row.symbol, 100.0, 100.0, 98.8, 99.9, 100.0, row.path_closes)
        self.assertIsNone(evaluate_decision(rows))


if __name__ == "__main__":
    unittest.main()
