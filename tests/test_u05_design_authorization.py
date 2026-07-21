from __future__ import annotations

import copy
import json
import unittest

from scripts.u05_design_authorization_check import AUDIT, DECISION, EXPECTED_HASH, U04_RESULT, validate


class U05DesignAuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.document = json.loads(DECISION.read_text())
        self.u04 = json.loads(U04_RESULT.read_text())
        self.audit = json.loads(AUDIT.read_text())

    def test_repository_decision_is_exact_and_narrow(self):
        self.assertEqual(self.document["content_hash"], EXPECTED_HASH)
        self.assertEqual(validate(self.document, self.u04, self.audit), [])

    def test_u04_result_or_oos_tamper_fails(self):
        changed = copy.deepcopy(self.u04); changed["oos_opened"] = True
        self.assertTrue(validate(self.document, changed, self.audit))
        changed = copy.deepcopy(self.u04); changed["run_content_hash"] = "0" * 64
        self.assertTrue(validate(self.document, changed, self.audit))

    def test_only_one_design_hypothesis_is_authorized(self):
        self.assertEqual(self.document["decision"]["maximum_hypotheses"], 1)
        enabled = [key for key, value in self.document["authorizations"].items() if value]
        self.assertEqual(enabled, ["u05_hypothesis_design"])

    def test_outcome_derived_rule_or_permission_escalation_fails(self):
        changed = copy.deepcopy(self.document)
        changed["decision"]["u04_outcome_derived_direction_or_rule_prohibited"] = False
        self.assertTrue(validate(changed, self.u04, self.audit))
        for key in ("event_scan", "returns", "strategy_rule_selection", "oos", "api_trading", "m2"):
            changed = copy.deepcopy(self.document); changed["authorizations"][key] = True
            self.assertTrue(validate(changed, self.u04, self.audit), key)

    def test_generated_time_does_not_change_content_identity(self):
        changed = copy.deepcopy(self.document); changed["generated_utc"] = "2030-01-01T00:00:00Z"
        self.assertEqual(validate(changed, self.u04, self.audit), [])


if __name__ == "__main__":
    unittest.main()
