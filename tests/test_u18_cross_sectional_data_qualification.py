from __future__ import annotations

import copy
import unittest

from btc_eth_dual_quant.data.u18_downside_tail_risk import evaluate_stream, tail_statistics
from scripts.u04_cross_sectional_data_qualification import load_json
from scripts.u18_cross_sectional_data_qualification import CONFIG, EVENT_HALF, NON_EVENT_HALF, synthetic_rows
from scripts.u18_cross_sectional_data_qualification_check import RESULT, validate


class U18QualificationTests(unittest.TestCase):
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

    def test_tail_fixture_contract(self) -> None:
        admitted = tail_statistics(EVENT_HALF)
        self.assertIsNotNone(admitted)
        self.assertEqual(admitted["tail_count"], 2)
        self.assertGreaterEqual(admitted["tail_energy_share"], 0.25)
        self.assertLessEqual(admitted["tail_dominance"], 0.65)
        self.assertIsNone(tail_statistics(NON_EVENT_HALF))

    def test_synthetic_core_deterministic(self) -> None:
        self.assertEqual(evaluate_stream(synthetic_rows(1500)), evaluate_stream(synthetic_rows(1500)))


if __name__ == "__main__":
    unittest.main()
