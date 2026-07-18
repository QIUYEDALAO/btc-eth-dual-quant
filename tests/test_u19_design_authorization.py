import copy
import json
import unittest

from scripts.u19_design_authorization_check import AUDIT, DECISION, FAILURE, PRIOR, validate


class U19AuthorizationTests(unittest.TestCase):
    def setUp(self):
        load = lambda path: json.loads(path.read_text())
        self.decision, self.failure, self.prior, self.audit = map(load, (DECISION, FAILURE, PRIOR, AUDIT))

    def test_exact(self):
        self.assertEqual(validate(self.decision, self.failure, self.prior, self.audit), [])

    def test_generated_time_excluded(self):
        changed = copy.deepcopy(self.decision)
        changed["generated_utc"] = "2030-01-01T00:00:00Z"
        self.assertEqual(validate(changed, self.failure, self.prior, self.audit), [])

    def test_result_or_authority_tamper(self):
        failure = copy.deepcopy(self.failure)
        failure["run_content_hash"] = "0" * 64
        self.assertTrue(validate(self.decision, failure, self.prior, self.audit))
        audit = copy.deepcopy(self.audit)
        audit["audit_summary_hash"] = "0" * 64
        self.assertTrue(validate(self.decision, self.failure, self.prior, audit))

    def test_inversion_or_escalation_tamper(self):
        decision = copy.deepcopy(self.decision)
        decision["decision"]["u18_negative_result_inversion_repair_relabeling_or_repackaging_prohibited"] = False
        self.assertTrue(validate(decision, self.failure, self.prior, self.audit))
        decision = copy.deepcopy(self.decision)
        decision["authorizations"]["event_scan"] = True
        self.assertTrue(validate(decision, self.failure, self.prior, self.audit))


if __name__ == "__main__":
    unittest.main()
