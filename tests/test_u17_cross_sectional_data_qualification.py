from __future__ import annotations

import copy
import unittest

from btc_eth_dual_quant.data.u17_liquidity_risk import evaluate_stream
from scripts.u04_cross_sectional_data_qualification import load_json
from scripts.u17_cross_sectional_data_qualification import CONFIG, synthetic_rows
from scripts.u17_cross_sectional_data_qualification_check import RESULT, validate


class U17QualificationTests(unittest.TestCase):
    def setUp(self):
        self.config = load_json(CONFIG)
        self.result = load_json(RESULT)

    def test_exact(self):
        self.assertEqual(validate(self.config, self.result), [])

    def test_generated_time_excluded(self):
        config = copy.deepcopy(self.config)
        config["generated_utc"] = "2030-01-01T00:00:00Z"
        self.assertEqual(validate(config, self.result), [])

    def test_ceiling_or_authorization_tamper(self):
        result = copy.deepcopy(self.result)
        result["counts"]["maximum_independent_theoretical_28d_episodes"] = 50
        self.assertTrue(validate(self.config, result))
        result = copy.deepcopy(self.result)
        result["authorizations"]["one_sealed_is_paper_observation"] = True
        self.assertTrue(validate(self.config, result))

    def test_isolation_or_complexity_tamper(self):
        result = copy.deepcopy(self.result)
        result["isolation"]["liquidity_rank_rows_generated"] = 1
        self.assertTrue(validate(self.config, result))
        result = copy.deepcopy(self.result)
        result["complexity_benchmark"]["passes"][0]["elapsed_seconds"] = "30.1"
        self.assertTrue(validate(self.config, result))

    def test_synthetic_core_deterministic(self):
        self.assertEqual(evaluate_stream(synthetic_rows(100000)), evaluate_stream(synthetic_rows(100000)))


if __name__ == "__main__":
    unittest.main()
