from __future__ import annotations

import copy
import json
import unittest

from scripts.u11_design_authorization_check import AUDIT, CORRECTION, DECISION, EXPECTED_HASH, PRIOR_RESULTS, U10_RESULT, validate


class U11DesignAuthorizationTests(unittest.TestCase):
    def setUp(self):
        load = lambda path: json.loads(path.read_text())
        self.decision = load(DECISION)
        self.u10 = load(U10_RESULT)
        self.correction = load(CORRECTION)
        self.prior = [load(path) for path in PRIOR_RESULTS]
        self.audit = load(AUDIT)

    def test_exact_narrow_decision(self):
        self.assertEqual(self.decision["content_hash"], EXPECTED_HASH)
        self.assertEqual(validate(self.decision, self.u10, self.correction, self.prior, self.audit), [])

    def test_prior_result_tamper_fails(self):
        changed = copy.deepcopy(self.u10)
        changed["oos_opened"] = True
        self.assertTrue(validate(self.decision, changed, self.correction, self.prior, self.audit))

    def test_only_design_is_authorized(self):
        self.assertEqual([key for key, value in self.decision["authorizations"].items() if value], ["u11_hypothesis_design"])

    def test_escalation_fails(self):
        for key in ("event_scan", "returns", "strategy_rule_selection", "backtesting", "oos", "api_trading", "execution_live", "m2"):
            changed = copy.deepcopy(self.decision)
            changed["authorizations"][key] = True
            self.assertTrue(validate(changed, self.u10, self.correction, self.prior, self.audit), key)

    def test_generated_time_excluded(self):
        changed = copy.deepcopy(self.decision)
        changed["generated_utc"] = "2030"
        self.assertEqual(validate(changed, self.u10, self.correction, self.prior, self.audit), [])


if __name__ == "__main__":
    unittest.main()
