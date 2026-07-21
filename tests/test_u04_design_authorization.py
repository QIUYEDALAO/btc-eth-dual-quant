from __future__ import annotations

import copy
import json
import unittest

from scripts.u04_design_authorization_check import AUDIT, DECISION, EXPECTED_HASH, validate


class U04DesignAuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.document = json.loads(DECISION.read_text())
        self.audit = json.loads(AUDIT.read_text())

    def test_repository_decision_is_exact_and_narrow(self):
        self.assertEqual(self.document["content_hash"], EXPECTED_HASH)
        self.assertEqual(validate(self.document, self.audit), [])

    def test_audit_hash_or_verdict_tamper_fails(self):
        changed = copy.deepcopy(self.audit); changed["verdict"] = "failed_audit"
        self.assertTrue(validate(self.document, changed))

    def test_only_one_design_hypothesis_is_authorized(self):
        self.assertEqual(self.document["decision"]["maximum_hypotheses"], 1)
        enabled = [key for key, value in self.document["authorizations"].items() if value]
        self.assertEqual(enabled, ["u04_hypothesis_design"])

    def test_event_scan_strategy_oos_or_trading_escalation_fails(self):
        for key in ("event_scan", "strategy_rule_selection", "oos", "api_trading", "m2"):
            changed = copy.deepcopy(self.document); changed["authorizations"][key] = True
            self.assertTrue(validate(changed, self.audit), key)

    def test_generated_time_does_not_change_content_identity(self):
        changed = copy.deepcopy(self.document); changed["generated_utc"] = "2030-01-01T00:00:00Z"
        self.assertEqual(validate(changed, self.audit), [])


if __name__ == "__main__":
    unittest.main()
