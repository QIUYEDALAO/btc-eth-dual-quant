from __future__ import annotations

import copy
import json
import unittest

from scripts.u17_cross_sectional_design_check import CONTENT_HASH, SCOPE, validate_scope


class U17DesignTests(unittest.TestCase):
    def setUp(self):
        self.scope = json.loads(SCOPE.read_text())

    def test_exact(self):
        self.assertEqual(self.scope["content_hash"], CONTENT_HASH)
        self.assertEqual(validate_scope(self.scope), [])

    def test_generated_time_excluded(self):
        scope = copy.deepcopy(self.scope)
        scope["generated_utc"] = "2030-01-01T00:00:00Z"
        self.assertEqual(validate_scope(scope), [])

    def test_escalation_or_parameter_fails(self):
        scope = copy.deepcopy(self.scope)
        scope["authorizations"]["event_scan"] = True
        self.assertTrue(validate_scope(scope))
        scope = copy.deepcopy(self.scope)
        scope["unresolved_until_separate_protocol"].pop()
        self.assertTrue(validate_scope(scope))

    def test_failure_or_nonduplication_removal_fails(self):
        scope = copy.deepcopy(self.scope)
        scope["economic_hypothesis"]["failure_regimes"].pop()
        self.assertTrue(validate_scope(scope))
        scope = copy.deepcopy(self.scope)
        scope["non_duplication"]["u16_correlation_breakdown_information_persistence_prohibited"] = False
        self.assertTrue(validate_scope(scope))


if __name__ == "__main__":
    unittest.main()
