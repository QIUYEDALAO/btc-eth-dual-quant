from __future__ import annotations

import copy
import unittest

from btc_eth_dual_quant.data.u20_negative_coskewness import evaluate_decision, evaluate_stream, half_coskewness
from scripts.u04_cross_sectional_data_qualification import load_json
from scripts.u20_cross_sectional_data_qualification import COMMON_HALF, CONFIG, NEGATIVE_HISTORY, NEUTRAL_HISTORY, synthetic_rows
from scripts.u20_cross_sectional_data_qualification_check import RESULT, validate


class U20QualificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = load_json(CONFIG)
        self.result = load_json(RESULT)

    def test_exact(self) -> None:
        self.assertEqual(validate(self.config, self.result), [])

    def test_generated_time_excluded(self) -> None:
        changed = copy.deepcopy(self.config)
        changed["generated_utc"] = "2030-01-01T00:00:00Z"
        self.assertEqual(validate(changed, self.result), [])

    def test_ceiling_permission_isolation_and_complexity_tamper_fail(self) -> None:
        changed = copy.deepcopy(self.result)
        changed["counts"]["maximum_independent_theoretical_24h_episodes"] = 399
        self.assertTrue(validate(self.config, changed))
        changed = copy.deepcopy(self.result)
        changed["authorizations"]["strategy"] = True
        self.assertTrue(validate(self.config, changed))
        changed = copy.deepcopy(self.result)
        changed["isolation"]["coskewness_statistic_rows_generated"] = 1
        self.assertTrue(validate(self.config, changed))
        changed = copy.deepcopy(self.result)
        changed["complexity_benchmark"]["passes"][0]["elapsed_seconds"] = "30.1"
        self.assertTrue(validate(self.config, changed))

    def test_coskewness_fixture_contract(self) -> None:
        negative = half_coskewness(NEGATIVE_HISTORY[:168], COMMON_HALF)
        neutral = half_coskewness(NEUTRAL_HISTORY[:168], COMMON_HALF)
        self.assertIsNotNone(negative)
        self.assertLessEqual(negative, -0.20)
        self.assertEqual(neutral, 0.0)
        self.assertIsNone(half_coskewness((0.0,) * 168, (0.0,) * 168))

    def test_cross_sectional_rank_tie_break_and_clustering(self) -> None:
        event = evaluate_decision(list(synthetic_rows(15)))
        self.assertIsNotNone(event)
        self.assertEqual(event["symbol"], "S00USDT")
        result = evaluate_stream(synthetic_rows(15 * 8))
        self.assertEqual(result["candidate_events"], 8)
        self.assertEqual(result["independent_episodes"], 1)

    def test_synthetic_core_deterministic(self) -> None:
        self.assertEqual(evaluate_stream(synthetic_rows(1500)), evaluate_stream(synthetic_rows(1500)))


if __name__ == "__main__":
    unittest.main()
