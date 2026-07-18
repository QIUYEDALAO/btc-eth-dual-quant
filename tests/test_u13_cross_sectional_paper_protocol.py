from __future__ import annotations

import copy
import json
import unittest

from scripts.u13_cross_sectional_paper_protocol_check import EXPECTED_HASH, PROTOCOL, REPORT, validate


class U13PaperProtocolTests(unittest.TestCase):
    def setUp(self):
        self.document = json.loads(PROTOCOL.read_text()); self.report = REPORT.read_text()

    def test_exact_protocol(self):
        self.assertEqual(self.document["content_hash"], EXPECTED_HASH)
        self.assertEqual(validate(self.document, self.report), [])

    def test_generated_time_excluded(self):
        changed = copy.deepcopy(self.document); changed["generated_utc"] = "2030"
        self.assertEqual(validate(changed, self.report), [])

    def test_shock_lag_or_weakness_tamper_fails(self):
        for section, key in (("common_shock_contract", "current_event_common_log_return_minimum"), ("lag_estimator_contract", "lookback_completed_1h_observations"), ("event_identity", "candidate_current_residual_maximum")):
            changed = copy.deepcopy(self.document); changed[section][key] = 0
            self.assertTrue(validate(changed, self.report), key)

    def test_gate_or_permission_escalation_fails(self):
        changed = copy.deepcopy(self.document); changed["paper_gates"]["complete_is_independent_episodes_minimum"] = 89
        self.assertTrue(validate(changed, self.report))
        for key in ("data_qualification_and_preflight", "event_scan", "formal_returns", "backtesting", "oos", "api_trading", "execution_live", "m2"):
            changed = copy.deepcopy(self.document); changed["authorizations"][key] = True
            self.assertTrue(validate(changed, self.report), key)


if __name__ == "__main__":
    unittest.main()
