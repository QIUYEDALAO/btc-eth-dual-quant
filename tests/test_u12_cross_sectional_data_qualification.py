from __future__ import annotations

import copy
import unittest

from scripts.u04_cross_sectional_data_qualification import load_json
from scripts.u12_cross_sectional_data_qualification import CONFIG
from scripts.u12_cross_sectional_data_qualification_check import EXPECTED_CONTRACT, EXPECTED_RESULT, RESULT, validate


class U12QualificationTests(unittest.TestCase):
    def setUp(self):
        self.config = load_json(CONFIG)
        self.result = load_json(RESULT)

    def test_exact_contract_result_and_ceiling(self):
        self.assertEqual(self.config["content_hash"], EXPECTED_CONTRACT)
        self.assertEqual(self.result["qualification_content_hash"], EXPECTED_RESULT)
        self.assertEqual(validate(self.config, self.result), [])

    def test_ceiling_or_reader_identity_tamper_fails(self):
        changed = copy.deepcopy(self.result)
        changed["counts"]["maximum_independent_theoretical_24h_episodes"] = 299
        self.assertTrue(validate(self.config, changed))
        changed = copy.deepcopy(self.result)
        changed["same_reader_orders"][1]["content_identity_hash"] = "0" * 64
        self.assertTrue(validate(self.config, changed))

    def test_isolation_or_permission_escalation_fails(self):
        changed = copy.deepcopy(self.result)
        changed["isolation"]["event_rows_generated"] = 1
        self.assertTrue(validate(self.config, changed))
        changed = copy.deepcopy(self.result)
        changed["authorizations"]["backtesting"] = True
        self.assertTrue(validate(self.config, changed))

    def test_generated_time_excluded(self):
        changed = copy.deepcopy(self.config)
        changed["generated_utc"] = "2030-01-01T00:00:00Z"
        self.assertEqual(validate(changed, self.result), [])


if __name__ == "__main__":
    unittest.main()
