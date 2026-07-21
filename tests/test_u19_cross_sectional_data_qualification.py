from __future__ import annotations

import copy
import unittest

from btc_eth_dual_quant.data.u19_volatility_of_volatility import evaluate_decision, evaluate_stream, half_statistics
from scripts.u04_cross_sectional_data_qualification import load_json
from scripts.u19_cross_sectional_data_qualification import CONFIG, HIGH_HALF, LOW_HALF, synthetic_rows
from scripts.u19_cross_sectional_data_qualification_check import RESULT, validate


class U19QualificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = load_json(CONFIG)
        self.result = load_json(RESULT)

    def test_exact(self) -> None:
        self.assertEqual(validate(self.config, self.result), [])

    def test_generated_time_excluded(self) -> None:
        changed = copy.deepcopy(self.config)
        changed["generated_utc"] = "2030-01-01T00:00:00Z"
        self.assertEqual(validate(changed, self.result), [])

    def test_ceiling_and_permission_tamper_fail(self) -> None:
        changed = copy.deepcopy(self.result)
        changed["counts"]["maximum_independent_theoretical_24h_episodes"] = 399
        self.assertTrue(validate(self.config, changed))
        changed = copy.deepcopy(self.result)
        changed["authorizations"]["strategy"] = True
        self.assertTrue(validate(self.config, changed))

    def test_isolation_and_complexity_tamper_fail(self) -> None:
        changed = copy.deepcopy(self.result)
        changed["isolation"]["residual_rows_generated"] = 1
        self.assertTrue(validate(self.config, changed))
        changed = copy.deepcopy(self.result)
        changed["complexity_benchmark"]["passes"][0]["elapsed_seconds"] = "30.1"
        self.assertTrue(validate(self.config, changed))

    def test_volatility_of_volatility_fixture_contract(self) -> None:
        high = half_statistics(HIGH_HALF)
        low = half_statistics(LOW_HALF)
        self.assertIsNotNone(high)
        self.assertIsNotNone(low)
        self.assertGreaterEqual(high["normalized_volatility_of_volatility"], 0.25)
        self.assertLess(low["normalized_volatility_of_volatility"], 0.25)

    def test_cross_sectional_rank_and_tie_break(self) -> None:
        rows = list(synthetic_rows(15))
        event = evaluate_decision(rows)
        self.assertIsNotNone(event)
        self.assertEqual(event["symbol"], "S00USDT")

    def test_connected_clustering_uses_prior_event(self) -> None:
        rows = list(synthetic_rows(15 * 8))
        result = evaluate_stream(rows)
        self.assertEqual(result["candidate_events"], 8)
        self.assertEqual(result["independent_episodes"], 1)

    def test_synthetic_core_deterministic(self) -> None:
        self.assertEqual(evaluate_stream(synthetic_rows(1500)), evaluate_stream(synthetic_rows(1500)))


if __name__ == "__main__":
    unittest.main()
