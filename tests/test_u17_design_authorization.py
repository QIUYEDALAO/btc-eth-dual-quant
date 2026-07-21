import copy
import json
import unittest

from scripts.u17_design_authorization_check import AUDIT, DECISION, PRIOR, RUN, validate


class U17AuthorizationTests(unittest.TestCase):
    def setUp(self):
        load = lambda path: json.loads(path.read_text())
        self.decision, self.run, self.prior, self.audit = map(load, (DECISION, RUN, PRIOR, AUDIT))

    def test_exact(self):
        self.assertEqual(validate(self.decision, self.run, self.prior, self.audit), [])

    def test_generated_time_excluded(self):
        decision = copy.deepcopy(self.decision)
        decision["generated_utc"] = "2030-01-01T00:00:00Z"
        self.assertEqual(validate(decision, self.run, self.prior, self.audit), [])

    def test_result_or_authority_tamper(self):
        run = copy.deepcopy(self.run)
        run["run_content_hash"] = "0" * 64
        self.assertTrue(validate(self.decision, run, self.prior, self.audit))
        audit = copy.deepcopy(self.audit)
        audit["audit_summary_hash"] = "0" * 64
        self.assertTrue(validate(self.decision, self.run, self.prior, audit))

    def test_retry_or_escalation_tamper(self):
        decision = copy.deepcopy(self.decision)
        decision["decision"]["u16_failed_gate_repair_relaxation_inversion_or_repackaging_prohibited"] = False
        self.assertTrue(validate(decision, self.run, self.prior, self.audit))
        decision = copy.deepcopy(self.decision)
        decision["authorizations"]["event_scan"] = True
        self.assertTrue(validate(decision, self.run, self.prior, self.audit))


if __name__ == "__main__":
    unittest.main()
