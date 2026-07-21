import copy
import json
import unittest

from scripts.u25_design_authorization_check import AUDIT, DECISION, FAILURE, PRIOR, validate


class U25AuthorizationTests(unittest.TestCase):
    def setUp(self) -> None:
        load = lambda path: json.loads(path.read_text())
        self.decision, self.failure, self.prior, self.audit = map(load, (DECISION, FAILURE, PRIOR, AUDIT))

    def test_exact(self) -> None:
        self.assertEqual(validate(self.decision, self.failure, self.prior, self.audit), [])

    def test_generated_time_excluded(self) -> None:
        changed = copy.deepcopy(self.decision)
        changed["generated_utc"] = "2030-01-01T00:00:00Z"
        self.assertEqual(validate(changed, self.failure, self.prior, self.audit), [])

    def test_result_or_authority_tamper(self) -> None:
        changed = copy.deepcopy(self.failure)
        changed["run_content_hash"] = "0" * 64
        self.assertTrue(validate(self.decision, changed, self.prior, self.audit))
        changed = copy.deepcopy(self.audit)
        changed["audit_summary_hash"] = "0" * 64
        self.assertTrue(validate(self.decision, self.failure, self.prior, changed))

    def test_inversion_or_escalation_tamper(self) -> None:
        changed = copy.deepcopy(self.decision)
        changed["decision"]["u24_negative_result_inversion_repair_relabeling_or_repackaging_prohibited"] = False
        self.assertTrue(validate(changed, self.failure, self.prior, self.audit))
        changed = copy.deepcopy(self.decision)
        changed["authorizations"]["event_scan"] = True
        self.assertTrue(validate(changed, self.failure, self.prior, self.audit))


if __name__ == "__main__":
    unittest.main()
