from __future__ import annotations

import copy
import json
import unittest

from scripts.u22_cross_sectional_paper_protocol_check import FEASIBILITY, PROTOCOL, validate_feasibility, validate_protocol


class U22ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.protocol = json.loads(PROTOCOL.read_text())
        self.feasibility = json.loads(FEASIBILITY.read_text())

    def test_exact(self):
        self.assertEqual(validate_feasibility(self.feasibility), [])
        self.assertEqual(validate_protocol(self.protocol), [])

    def test_generated_time_excluded(self):
        changed = copy.deepcopy(self.protocol)
        changed["generated_utc"] = "2030-01-01T00:00:00Z"
        self.assertEqual(validate_protocol(changed), [])

    def test_parameter_or_gate_tamper(self):
        changed = copy.deepcopy(self.protocol)
        changed["dispersion_contract"]["minimum_recent_over_baseline_dispersion_ratio"] = "1.40"
        self.assertTrue(validate_protocol(changed))
        changed = copy.deepcopy(self.protocol)
        changed["paper_gates"]["combined_median_24h_relative_leader_continuation_minimum"] = "0.0100"
        self.assertTrue(validate_protocol(changed))

    def test_feasibility_or_authorization_tamper(self):
        changed = copy.deepcopy(self.feasibility)
        changed["passes"][0]["event_digest"] = "0" * 64
        self.assertTrue(validate_feasibility(changed))
        changed = copy.deepcopy(self.protocol)
        changed["authorizations"]["event_scan"] = True
        self.assertTrue(validate_protocol(changed))


if __name__ == "__main__":
    unittest.main()
