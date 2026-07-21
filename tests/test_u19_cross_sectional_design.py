from __future__ import annotations

import copy
import json
import unittest

from scripts.u19_cross_sectional_design_check import CONTENT_HASH, SCOPE, validate_scope


class U19DesignTests(unittest.TestCase):
    def setUp(self):
        self.scope = json.loads(SCOPE.read_text())

    def test_exact(self):
        self.assertEqual(self.scope["content_hash"], CONTENT_HASH)
        self.assertEqual(validate_scope(self.scope), [])

    def test_generated_time_excluded(self):
        changed = copy.deepcopy(self.scope)
        changed["generated_utc"] = "2030-01-01T00:00:00Z"
        self.assertEqual(validate_scope(changed), [])

    def test_escalation_or_parameter_fails(self):
        changed = copy.deepcopy(self.scope)
        changed["authorizations"]["event_scan"] = True
        self.assertTrue(validate_scope(changed))
        changed = copy.deepcopy(self.scope)
        changed["unresolved_until_separate_protocol"].pop()
        self.assertTrue(validate_scope(changed))

    def test_failure_or_nonduplication_removal_fails(self):
        changed = copy.deepcopy(self.scope)
        changed["economic_hypothesis"]["failure_regimes"].pop()
        self.assertTrue(validate_scope(changed))
        changed = copy.deepcopy(self.scope)
        changed["non_duplication"]["u18_downside_tail_risk_premium_prohibited"] = False
        self.assertTrue(validate_scope(changed))


if __name__ == "__main__":
    unittest.main()
