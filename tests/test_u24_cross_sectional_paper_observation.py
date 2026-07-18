from __future__ import annotations
import copy
import unittest

from scripts.u04_cross_sectional_data_qualification import load_json
from scripts.u24_cross_sectional_paper_observation_check import RUN, validate


class U24ObservationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.run = load_json(RUN)

    def test_exact_failed_result(self) -> None:
        self.assertEqual(validate(self.run), [])

    def test_metric_or_second_run_tamper_fails(self) -> None:
        changed = copy.deepcopy(self.run)
        changed["metrics"]["complete_is_independent_episodes"] = 79
        self.assertTrue(validate(changed))
        changed = copy.deepcopy(self.run)
        changed["second_run_executed"] = True
        self.assertTrue(validate(changed))

    def test_oos_or_authorization_tamper_fails(self) -> None:
        changed = copy.deepcopy(self.run)
        changed["oos_opened"] = True
        self.assertTrue(validate(changed))
        changed = copy.deepcopy(self.run)
        changed["authorizations"]["strategy"] = True
        self.assertTrue(validate(changed))

    def test_gate_or_order_tamper_fails(self) -> None:
        changed = copy.deepcopy(self.run)
        changed["paper_gate_checks"]["complete_is_independent_episodes"] = True
        self.assertTrue(validate(changed))
        changed = copy.deepcopy(self.run)
        changed["orders"][2]["content_identity_hash"] = "0" * 64
        self.assertTrue(validate(changed))


if __name__ == "__main__":
    unittest.main()
