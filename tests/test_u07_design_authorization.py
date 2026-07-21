from __future__ import annotations

import copy
import json
import unittest

from scripts.u07_design_authorization_check import AUDIT, DECISION, EXPECTED_HASH, U04_RESULT, U05_RESULT, U06_RESULT, validate


class U07DesignAuthorizationTests(unittest.TestCase):
    def setUp(self):
        load = lambda path: json.loads(path.read_text())
        self.document = load(DECISION); self.u06 = load(U06_RESULT); self.u05 = load(U05_RESULT); self.u04 = load(U04_RESULT); self.audit = load(AUDIT)

    def test_repository_decision_is_exact_and_narrow(self):
        self.assertEqual(self.document["content_hash"], EXPECTED_HASH)
        self.assertEqual(validate(self.document, self.u06, self.u05, self.u04, self.audit), [])

    def test_every_prior_result_binding_and_oos_seal_is_enforced(self):
        for index, prior in enumerate((self.u06, self.u05, self.u04)):
            changed = copy.deepcopy(prior); changed["oos_opened"] = True
            args = [self.document, self.u06, self.u05, self.u04, self.audit]; args[index + 1] = changed
            self.assertTrue(validate(*args))
            changed = copy.deepcopy(prior); changed["run_content_hash"] = "0" * 64
            args = [self.document, self.u06, self.u05, self.u04, self.audit]; args[index + 1] = changed
            self.assertTrue(validate(*args))

    def test_only_one_design_hypothesis_is_authorized(self):
        self.assertEqual(self.document["decision"]["maximum_hypotheses"], 1)
        enabled = [key for key, value in self.document["authorizations"].items() if value]
        self.assertEqual(enabled, ["u07_hypothesis_design"])

    def test_outcome_derived_rule_or_permission_escalation_fails(self):
        changed = copy.deepcopy(self.document)
        changed["decision"]["u04_u05_u06_outcome_derived_direction_or_rule_prohibited"] = False
        self.assertTrue(validate(changed, self.u06, self.u05, self.u04, self.audit))
        for key in ("event_scan", "returns", "strategy_rule_selection", "freqtrade_strategy_code", "backtesting", "oos", "api_trading", "execution_live", "m2"):
            changed = copy.deepcopy(self.document); changed["authorizations"][key] = True
            self.assertTrue(validate(changed, self.u06, self.u05, self.u04, self.audit), key)

    def test_generated_time_does_not_change_content_identity(self):
        changed = copy.deepcopy(self.document); changed["generated_utc"] = "2030-01-01T00:00:00Z"
        self.assertEqual(validate(changed, self.u06, self.u05, self.u04, self.audit), [])


if __name__ == "__main__":
    unittest.main()
