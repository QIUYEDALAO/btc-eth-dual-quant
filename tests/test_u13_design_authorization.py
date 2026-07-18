from __future__ import annotations

import copy
import json
import unittest

from scripts.u13_design_authorization_check import AUDIT, DECISION, EXPECTED_HASH, PRIOR_RESULTS, U09_CORRECTION, U10_RESULT, U11_RESULT, U12_RESULT, validate


class U13DesignAuthorizationTests(unittest.TestCase):
    def setUp(self):
        load = lambda path: json.loads(path.read_text())
        self.decision = load(DECISION); self.u12 = load(U12_RESULT); self.u11 = load(U11_RESULT); self.u10 = load(U10_RESULT); self.u09 = load(U09_CORRECTION); self.prior = [load(path) for path in PRIOR_RESULTS]; self.audit = load(AUDIT)

    def check(self, decision=None, u12=None):
        return validate(decision or self.decision, u12 or self.u12, self.u11, self.u10, self.u09, self.prior, self.audit)

    def test_exact_narrow_decision(self):
        self.assertEqual(self.decision["content_hash"], EXPECTED_HASH)
        self.assertEqual(self.check(), [])

    def test_prior_result_or_isolation_tamper_fails(self):
        changed = copy.deepcopy(self.u12); changed["second_run_executed"] = True
        self.assertTrue(self.check(u12=changed))
        changed = copy.deepcopy(self.decision); changed["bindings"]["u12_run_content_hash"] = "0" * 64
        self.assertTrue(self.check(changed))

    def test_only_design_is_authorized(self):
        self.assertEqual([key for key, value in self.decision["authorizations"].items() if value], ["u13_hypothesis_design"])

    def test_escalation_fails(self):
        for key in ("public_data_read", "event_scan", "returns", "strategy_rule_selection", "backtesting", "oos", "api_trading", "execution_live", "m2"):
            changed = copy.deepcopy(self.decision); changed["authorizations"][key] = True
            self.assertTrue(self.check(changed), key)

    def test_generated_time_excluded(self):
        changed = copy.deepcopy(self.decision); changed["generated_utc"] = "2030"
        self.assertEqual(self.check(changed), [])


if __name__ == "__main__":
    unittest.main()
