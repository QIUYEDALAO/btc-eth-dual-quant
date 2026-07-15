import json
import unittest

from btc_eth_dual_quant.data.lifecycle_availability import evaluate_fault_case
from tests.v4_lifecycle_fixtures import ROOT


class V4FaultInjectionTests(unittest.TestCase):
    def test_every_reviewed_fault_case_has_unique_executable_mapping(self):
        matrix = json.loads((ROOT / "docs/decisions/proposals/adr0014_lifecycle_fault_matrix.json").read_text())
        cases = matrix["fault_cases"]
        self.assertEqual(len(cases), 37)
        self.assertEqual(len({item["test_id"] for item in cases}), 37)
        for item in cases:
            outcome = evaluate_fault_case(item["test_id"], item["precondition"], item["mutation_or_fault"])
            self.assertEqual(outcome.result, item["expected_result"], item["test_id"])
            self.assertEqual(outcome.state, item["expected_state"], item["test_id"])
            self.assertEqual(outcome.blocking, item["blocking_status"], item["test_id"])

    def test_execution_interpretations_and_policy_overlap_fail_closed(self):
        for test_id in ("ADR0014-FI-023", "ADR0014-FI-034", "ADR0014-FI-035", "ADR0014-FI-036", "ADR0014-FI-037"):
            outcome = evaluate_fault_case(test_id, "fixture", "fixture")
            self.assertEqual(outcome.state, "unresolved_blocked")


if __name__ == "__main__":
    unittest.main()
